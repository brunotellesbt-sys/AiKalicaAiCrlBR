"""Real v2 controller saves -> v3 Continue/SAVE -> second cold Continue.

The old ROM uses the published533 IDs/rectangles plus earlier local repairs.
Its three initial positions/version/party are declared fixtures, not travel
proofs. Each battery is then written by the game's SAVE menu. Continue and
the second SAVE use no game-memory writes. This complements, rather than
relabels, the separately tested original public TESTE battery.
"""
import argparse
import ctypes
import gzip
import hashlib
import json
from pathlib import Path

from atlas_surf_candidate_ids import load_history
from atlas_surf_candidate_migration import resolve
from atlas_surf_source import Source
from candidate_layer import Layer
from prepare_generated_area_review import PRIOR,LAYER
from validate_coast_scenery_objects import bootstrap
from validate_cold_boot import validate as cold_boot

CASES=[('unchanged','JourneyAtlasSea000',4,3,True),
       ('retired','JourneyAtlasSea004',4,3,True),
       ('moved-land','JourneyAtlasScene002',12,9,False)]


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_menu(ns,path):
    lib,s=ns['lib'],ns['s'];step=ns['step'];press=ns['press']
    press(8);step(90)
    actions=[lib.read8(s['sCurrentStartMenuActions']+i) for i in range(lib.read8(s['sNumStartMenuActions']))]
    assert actions.count(5)==1,('SAVE missing',actions);target=actions.index(5)
    for _ in range(12):
        if lib.read8(s['sStartMenuCursorPos'])==target:break
        press(128)
    assert lib.read8(s['sStartMenuCursorPos'])==target
    press(1);seen=set();callbacks={value:name for name,value in s.items()}
    for _ in range(120):
        callback=lib.read32(s['sSaveDialogCallback'])&~1;seen.add(callbacks.get(callback,hex(callback)))
        if callback==s['SaveOverwriteInputCallback']:press(64)
        if 'SaveReturnSuccessCallback' in seen and not lib.read8(s['sLockFieldControls']):break
        press(1)
    else:raise AssertionError(('Native save did not finish',seen))
    assert 'SaveReturnSuccessCallback' in seen
    lib.export_save.argtypes=[ctypes.c_char_p];lib.export_save.restype=ctypes.c_int
    assert lib.export_save(str(path.resolve()).encode()) and path.stat().st_size==131072
    return sorted(seen)


def run(old_source,new_source,library,tables_path,output):
    old_source,new_source,library,tables_path,output=map(lambda p:Path(p).resolve(),
        (old_source,new_source,library,tables_path,output));output.mkdir(parents=True,exist_ok=True)
    tables=json.loads(gzip.decompress(tables_path.read_bytes()))
    old_meta=json.loads((old_source/'.journey-atlas-surf-layout').read_bytes())
    new_meta=json.loads((new_source/'.journey-atlas-surf-layout').read_bytes())
    assert new_meta['candidate533_migration']['table_sha256']==tables['table_sha256']
    signature=lambda p:{r['name']:(r['group_index'],r['number'],r['origin'],r['width'],r['height']) for r in p['chunks']}
    assert signature(old_meta['geometry_plan'])==signature(load_history()['geometry_plan'])
    expected={};binaries={}
    for label,source,meta in [('old',old_source,old_meta),('new',new_source,new_meta)]:
        expected[label]=Layer(source,'atlas-surf-layout',PRIOR+[LAYER]).expected
        expected[label].update(meta['prepared_sha256'])
        binaries[label]={n:sha(source/n) for n in ('pokeemerald.gba','pokeemerald.elf','.journey-atlas-surf-layout')}
    def unchanged():
        for label,source in [('old',old_source),('new',new_source)]:
            for n,h in expected[label].items():assert sha(source/n)==h,(label,n)
            assert binaries[label]=={n:sha(source/n) for n in binaries[label]}
    unchanged();old=Source(old_source);cases=[]
    for case,name,x,y,surf in CASES:
        folder=output/case;folder.mkdir(exist_ok=True)
        word=old.word(name,x,y);assert not word&0xc00
        assert old.water(name,x,y)==surf and word>>12==(1 if surf else 3)
        packed=old.identities[name];destination=resolve(tables,packed,x,y,surf)
        assert destination is not None
        ns=bootstrap(old_source,library,folder,[name]);original={k:ns[k] for k in ('native','warp','script','step')}
        fixture=True;depth=0;controls=[]
        def step(count,key=0):
            if not fixture and not depth:controls.append(dict(frames=count,key=key))
            original['step'](count,key)
        def native(function,*args,**kwargs):
            nonlocal depth
            if not fixture:
                assert function.startswith(('MapGridGet','MetatileBehavior_Is')) or function in {
                    'PlayerGetElevation','GetPlayerFacingDirection','GetPlayerFacingMovementDirection'},function
            depth+=1
            try:return original['native'](function,*args,**kwargs)
            finally:depth-=1
        def script(*args,**kwargs):
            assert fixture or depth,'Script injected after initial fixture'
            return original['script'](*args,**kwargs)
        def warp(*args,**kwargs):
            assert fixture,'Warp after initial fixture'
            return original['warp'](*args,**kwargs)
        ns.update(native=native,step=step,script=script,warp=warp)
        try:
            native('VarSet',0x40dc,2);warp(name,x,y)
            native('SetPlayerAvatarTransitionFlags',8 if surf else 1);native('DisableWildEncounters',1);step(90)
            assert ns['position']()==(x,y) and bool(ns['player_state']()['surfing'])==surf
            fixture=False;battery=folder/'old-v2-controller-save.sav'
            callbacks=save_menu(ns,battery);ns['picture']('old-v2-saved-through-menu')
        finally:ns['lib'].stop()
        old_boot=cold_boot(old_source,library,folder/'old-cold-continue',battery,expected_geometry_version=2)
        migrated=folder/'migrated-v3-controller-save.sav'
        first=cold_boot(new_source,library,folder/'new-first-continue',battery,migrated,expected_geometry_version=3)
        second=cold_boot(new_source,library,folder/'new-second-continue',migrated,expected_geometry_version=3)
        check=lambda r:(r['field_map'][0]<<8|r['field_map'][1],*r['player_tile'],
                        2 if r['player_surfing'] else 1,r['player_elevation'])
        assert check(old_boot['runs'][-1])==(packed,x,y,2 if surf else 1,word>>12)
        assert check(first['runs'][-1])==destination,(case,check(first['runs'][-1]),destination)
        assert check(second['runs'][-1])==destination,(case,'Migration repeated on second Continue')
        cases.append(dict(case=case,old_point=[name,x,y],old_mode='surf' if surf else 'walk',
            old_word=word,old_battery_sha256=sha(battery),migrated_battery_sha256=sha(migrated),
            expected_new_map_and_position_mode_elevation=list(destination),
            old_saved_by_controllers=True,old_save_callbacks=callbacks,old_save_controls=controls,
            native_old_v2_continue_passed=True,new_v3_continue_menu_save_continue_passed=True,
            second_continue_position_and_mode_unchanged=True))
        print('Battery migration passed:',case,flush=True)
    unchanged()
    report=dict(kind='candidate533-native-battery-roundtrips',passed=True,old_and_new_binaries=binaries,
        old_source_files_checked=len(expected['old']),new_source_files_checked=len(expected['new']),
        old533_geometry_matches_published_compiled_rectangles=True,
        old_ROM_has_local_repairs_and_is_not_relabelled_as_original_public_ROM=True,
        initial_old_position_version_party_and_progress_are_per_case_fixtures=True,
        old_battery_written_by_real_SAVE_menu=True,new_boot_and_SAVE_controllers_only=True,
        new_boot_no_game_memory_writes=True,table_sha256=tables['table_sha256'],cases=cases,
        all_possible_native_old_batteries_tested=False,final_release_validated=False)
    (output/'battery-roundtrips.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('old-source','new-source','library','tables','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();r=run(a.old_source,a.new_source,a.library,a.tables,a.output)
    print(json.dumps(dict(passed=r['passed'],cases=len(r['cases']),final_release_validated=False)))
