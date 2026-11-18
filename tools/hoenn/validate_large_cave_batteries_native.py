"""Real version7 SAVE -> version8 Continue/SAVE/Continue for expanded islands.

Party, progress and the initial old position are declared fixtures. Both old
and migrated batteries are written through SAVE. Cold Continue never writes
game RAM. Capture flags, native actor templates and terrain are read directly.
"""
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
import struct

from validate_atlas_candidate_batteries_native import save_menu
from validate_coast_scenery_objects import bootstrap
from validate_cold_boot import validate as cold_boot

ROOT=Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(old_source,new_source,library,output,limit=None,offset=0):
    old_source,new_source,library,output=(Path(p).resolve() for p in (old_source,new_source,library,output))
    output.mkdir(parents=True,exist_ok=True)
    fixture=json.loads(gzip.decompress((ROOT/'tools/hoenn/data/large-cave-save-source-fixture.json.gz').read_bytes()))
    metadata=json.loads((new_source/'.journey-atlas-surf-layout').read_bytes())
    old_captures=json.loads((old_source/'.journey-sanctuaries').read_bytes())['captures']
    flags={r['flag_id']:bool(i%2) for i,r in enumerate(old_captures)}
    artifacts={label:{n:sha(src/n) for n in ('pokeemerald.gba','pokeemerald.elf','.journey-atlas-surf-layout')}
               for label,src in [('old',old_source),('new',new_source)]}
    cases=[]
    for row in metadata['large_cave_exteriors']['maps']:
        name=row['map'];mapping=fixture['maps'][name]
        old=struct.unpack('<1089H',base64.b64decode(mapping['old']))
        for surfing in (False,True):
            candidates=[r for r in fixture['rescues'] if fixture['map_ids'][r['map']]==mapping['id'] and r['surfing']==surfing]
            rescue=min(candidates,key=lambda r:abs(r['from_tile'][0]-16)+abs(r['from_tile'][1]-11))
            x,y=rescue['from_tile'];xx,yy=rescue['to_tile']
            new=struct.unpack('<1089H',base64.b64decode(mapping['new']))
            cases.append(dict(name=name,label=name+('-surf' if surfing else '-foot'),
                old=[x,y],target=[xx,yy],surfing=surfing,old_word=old[y*33+x],new_word=new[yy*33+xx],map_id=mapping['id']))
    results=[]
    for case in cases[offset:offset+limit if limit else None]:
        folder=output/case['label'];folder.mkdir(exist_ok=True)
        name=case['name'];x,y=case['old'];surfing=case['surfing']
        ns=bootstrap(old_source,library,folder,[name])
        original={key:ns[key] for key in ('native','script','warp','step')}
        fixture_active=True;depth=0;controls=[]
        def step(frames,key=0):
            if not fixture_active and not depth:
                controls.append(dict(frames=frames,key=key))
            original['step'](frames,key)
        def native(function,*args,**kwargs):
            nonlocal depth
            assert fixture_active,'Native call after initial save fixture'
            depth+=1
            try:
                return original['native'](function,*args,**kwargs)
            finally:
                depth-=1
        def script(*args,**kwargs):
            assert fixture_active or depth,'Script after initial save fixture'
            return original['script'](*args,**kwargs)
        def warp(*args,**kwargs):
            assert fixture_active,'Warp after initial save fixture'
            return original['warp'](*args,**kwargs)
        ns.update(step=step,native=native,script=script,warp=warp)
        battery=folder/'old-v7-controller-save.sav'
        try:
            native('VarSet',0x40DC,7)
            for flag,value in flags.items():
                ns['rawflag'](flag,value)
            warp(name,x,y);native('SetPlayerAvatarTransitionFlags',8 if surfing else 1)
            native('DisableWildEncounters',1);step(240)
            assert ns['position']()==(x,y)
            assert bool(ns['lib'].read8(ns['s']['gPlayerAvatar'])&8)==surfing
            fixture_active=False
            callbacks=save_menu(ns,battery);ns['picture']('old-saved-through-menu')
        finally:
            ns['lib'].stop();ns['emulator_workspace'].cleanup()
        old=cold_boot(old_source,library,folder/'old-continue',battery,expected_geometry_version=7,
            expected_map_cells=[(*case['old'],case['old_word'])],expected_flags=flags,verify_current_map_objects=True)
        migrated=folder/'new-v8-controller-save.sav'
        options=dict(expected_geometry_version=8,expected_map_cells=[(*case['target'],case['new_word'])],
            expected_flags=flags,verify_current_map_objects=True,require_cleared_template_tail=True)
        first=cold_boot(new_source,library,folder/'new-continue',battery,migrated,**options)
        second=cold_boot(new_source,library,folder/'second-continue',migrated,**options)
        def state(report):
            r=report['runs'][-1]
            return dict(map_id=r['field_map'][0]*256+r['field_map'][1],tile=r['player_tile'],
                        surfing=r['player_surfing'],elevation=r['player_elevation'])
        assert state(old)==dict(map_id=case['map_id'],tile=case['old'],surfing=surfing,elevation=case['old_word']>>12)
        wanted=dict(map_id=case['map_id'],tile=case['target'],surfing=surfing,elevation=case['new_word']>>12)
        assert state(first)==state(second)==wanted,(case,state(first),state(second),wanted)
        results.append(dict(**case,old_battery_sha256=sha(battery),new_battery_sha256=sha(migrated),
            old_save_controls=controls,old_save_callbacks=callbacks,
            old_save_and_both_new_continues_passed=True,capture_flags_checked=len(flags),
            native_actor_templates_match_current_compiled_map=True,second_continue_did_not_repeat_migration=True))
        print(case['label'],'old SAVE/Continue -> new Continue/SAVE/Continue PASS',flush=True)
        (output/'partial-cases.json').write_text(json.dumps(results,indent=2)+'\n')
    for label,src in [('old',old_source),('new',new_source)]:
        assert artifacts[label]=={n:sha(src/n) for n in artifacts[label]}
    report=dict(kind='large-cave-native-save-migrations',passed=True,artifacts=artifacts,cases=results,
        initial_old_party_progress_position_and_version_are_fixtures=True,
        real_menu_batteries_and_cold_controllers_only=True,all_nine_maps_and_both_modes=len(results)==18,
        final_release_validated=False)
    (output/'large-cave-native-save-migrations.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('old-source','new-source','library','output'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--limit',type=int);p.add_argument('--offset',type=int,default=0)
    a=p.parse_args();run(a.old_source,a.new_source,a.library,a.output,a.limit,a.offset)
