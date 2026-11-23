"""Walk the seven restored sand habitats into actual wild battles and SAVE.

Only initial party/progress/map placement is a fixture. Encounter rolls,
enemy creation, battle escape, the SAVE menu and cold Continue run natively.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from atlas_sand_habitats import SCENES
from atlas_surf_source import Source
from validate_coast_scenery_objects import bootstrap
from validate_atlas_candidate_batteries_native import save_menu
from validate_cold_boot import validate as cold_boot


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(source,library,output,census):
    source,library,output,census=(Path(p).resolve() for p in (source,library,output,census))
    output.mkdir(parents=True,exist_ok=True)
    raw=census.read_bytes();ecology=json.loads(gzip.decompress(raw) if census.suffix=='.gz' else raw)
    terrain=Source(source);names=['JourneyAtlasScene%03d' % i for i in SCENES]
    ns=bootstrap(source,library,output,names);lib,s,abi=(ns[k] for k in ('lib','s','abi'))
    artifacts={n:sha(source/n) for n in ('pokeemerald.gba','pokeemerald.elf','.journey-atlas-surf-layout')}
    controls=[];fixture=True;phase='fixture';cases=[];captures=[]
    original={k:ns[k] for k in ('step','native','script','warp')};depth=0
    def step(frames,key=0):
        if not fixture and not depth:controls.append(dict(phase=phase,frames=frames,key=key))
        original['step'](frames,key)
    def native(function,*args,**kwargs):
        nonlocal depth
        assert fixture,'Unexpected native call after land walk departure: '+function
        depth+=1
        try:return original['native'](function,*args,**kwargs)
        finally:depth-=1
    def script(*args,**kwargs):
        assert fixture or depth,'Injected land encounter script';return original['script'](*args,**kwargs)
    def warp(*args,**kwargs):
        assert fixture,'Warp during land encounter';return original['warp'](*args,**kwargs)
    ns.update(step=step,native=native,script=script,warp=warp)
    def callback():return lib.read32(s['gMain']+4)&~1
    def picture(label):
        ns['picture'](label);captures.append(dict(file=label+'.png',sha256=sha(output/(label+'.png'))))
    try:
        assert not lib.read8(s['gJourneyReviewMode'])
        cap=lib.read16(s['gJourneyBuildRules'])
        for name in names:
            row=next(r for r in ecology['map_areas'] if r['map']==name and r['area']==0)
            allowed=set(row['species'][str(cap)]);assert allowed
            points={tuple(p) for p in row['trigger_sample']}
            # The source census truncates samples. Find a complete dry pair
            # independently, preserving full tile words and native behavior.
            pairs=[]
            layout=terrain.layout(name)
            for y in range(layout['height']):
                for x in range(layout['width']-1):
                    words=[terrain.word(name,xx,y) for xx in (x,x+1)]
                    if all(w>>12==3 and not w&0xC00 and terrain.behavior(name,w)==33 for w in words):
                        pairs.append((x,y))
            occupied={(o['x'],o['y']) for o in terrain.maps[name]['object_events']}
            x,y=next(p for p in pairs if p not in occupied and (p[0]+1,p[1]) not in occupied)
            fixture=True;native('VarSet',0x40DC,8);ns['team']([80])
            native('DisableWildEncounters',0)
            # Map-review bootstrap enables both native Repel counters.
            # Clear them before testing ordinary encounters.
            native('VarSet',0x4021,0);native('VarSet',0x4120,0)
            for bank in (ns['kanto_flags'],ns['hoenn_flags']):
                for f in bank:ns['rawflag'](f,False)
            warp(name,x,y);native('SetPlayerAvatarTransitionFlags',1);step(120)
            fixture=False;phase=name;start=len(controls);picture(name+'-dry-departure')
            found=False
            for turn in range(600):
                step(16,16 if turn%2==0 else 32)
                if callback() in (s['CB2_InitBattle'],s['BattleMainCB2']):found=True;break
            assert found,('No ordinary sand encounter after controller steps',name,ns['position']())
            for _ in range(180):
                if callback()==s['BattleMainCB2'] and (lib.read32(s['gBattlerControllerFuncs'])&~1) in ns['actions']:break
                ns['press'](2)
            else:raise AssertionError('Wild battle did not reach native actions')
            species=lib.read16(s['gBattleMons']+abi[74]+abi[75])
            assert species in allowed,(name,species,sorted(allowed))
            assert not lib.read32(s['gBattleTypeFlags'])&abi[10],'Unexpected trainer battle'
            picture(name+'-actual-land-wild-battle')
            step(1,128);step(12);step(1,16);step(12)
            assert lib.read8(s['gActionSelectionCursor'])==3
            ns['press'](1)
            escape_retries=0
            for _ in range(180):
                if callback()==s['CB2_Overworld'] and ns['idle']():break
                if (callback()==s['BattleMainCB2']
                    and (lib.read32(s['gBattlerControllerFuncs'])&~1) in ns['actions']):
                    # A legitimate failed escape returns to the action menu.
                    # Retry Run through controls, retaining native battle RNG.
                    assert lib.read8(s['gActionSelectionCursor'])==3
                    ns['press'](1);escape_retries+=1
                else:ns['press'](2)
            else:raise AssertionError('Wild escape failed to return to the field')
            step(120);picture(name+'-returned-on-foot')
            assert ns['by_location'][ns['location']()]==name and ns['position']()[1]==y
            cases.append(dict(map=name,owner=row['owner'],species=species,allowed_species=sorted(allowed),
                              native_battle_started_by_walking=True,returned_to_same_island_on_foot=True,
                              failed_escape_retries=escape_retries,controls=[start,len(controls)]))
            print(name,'native sand walk / actual species / return PASS',flush=True)
        battery=output/'actual-land-walk-controller-save.sav';callbacks=save_menu(ns,battery)
    except BaseException:picture('land-habitat-failure');raise
    finally:lib.stop();ns['emulator_workspace'].cleanup()
    cold=cold_boot(source,library,output/'cold-continue',battery,expected_geometry_version=8,verify_current_map_objects=True)
    assert artifacts=={n:sha(source/n) for n in artifacts}
    report=dict(kind='atlas-land-habitats-native',passed=True,artifact_sha256=artifacts,
                max_national=cap,cases=cases,controls=controls,captures=captures,
                initial_party_map_progress_are_fixtures=True,no_gameplay_writes_after_departure=True,
                battery=dict(file=battery.name,sha256=sha(battery)),save_callbacks=callbacks,
                cold_continue=dict(file='cold-continue/cold-boot.json',passed=cold['passed']))
    (output/'land-habitats-native.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','library','output','census'):p.add_argument('--'+name,type=Path,required=True)
    run(**vars(p.parse_args()))
