"""Controller-only Three Island Surf circuit in a frozen compiled candidate.

Party/progress and one dry starting placement are explicit fixtures. After
that placement no warp, script entry, avatar setter or world-memory fix is
allowed. Native getters use the declared private read-only trampoline.
"""
import argparse
import hashlib
import json
from pathlib import Path

from validate_coast_scenery_objects import bootstrap
from candidate_layer import Layer
from prepare_generated_area_review import PRIOR,LAYER

PORT='ThreeIsland_Port_Frlg'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(source,library,output):
    source,library,output=map(lambda p:Path(p).resolve(),(source,library,output))
    output.mkdir(parents=True,exist_ok=True)
    marker=source/'.journey-atlas-surf-layout';metadata=json.loads(marker.read_bytes());prepared=metadata['prepared_sha256']
    bindings=[b for b in metadata['adapter_plan']['bindings'] if (b['native_map'],b['component'])==(PORT,1)]
    assert len(bindings)==1,'Three needs its actual unique compiled coast binding'
    coast=bindings[0]['adapter']
    expected=Layer(source,'atlas-surf-layout',PRIOR+[LAYER]).expected;expected.update(prepared)
    frozen={n:sha(source/n) for n in ('pokeemerald.gba','pokeemerald.elf','.journey-atlas-surf-layout')}
    def verify():
        assert frozen=={n:sha(source/n) for n in frozen}
        for name,wanted in expected.items():assert sha(source/name)==wanted,name
    verify();ns=bootstrap(source,library,output,[PORT,coast])
    original={key:ns[key] for key in ('step','native','script','warp','picture')}
    fixture=True;depth=0;phase='fixture';controls=[];queries=[];route=[];states=[];captures=[]
    def step(count,key=0):
        if not fixture and not depth:controls.append(dict(phase=phase,frames=count,key=key))
        original['step'](count,key)
    def native(name,*args,**kwargs):
        nonlocal depth
        if not fixture:
            assert name.startswith(('MapGridGet','MetatileBehavior_Is')) or name in {
                'GetPlayerFacingDirection','GetPlayerFacingMovementDirection','IsPlayerFacingSurfableFishableWater','PlayerGetElevation'},name
            queries.append(dict(phase=phase,function=name,arguments=list(args)))
        depth+=1
        try:return original['native'](name,*args,**kwargs)
        finally:depth-=1
    def script(*args,**kwargs):
        assert fixture or depth,'Injected gameplay script after initial placement'
        return original['script'](*args,**kwargs)
    def warp(*args,**kwargs):
        assert fixture,'Warp after initial placement'
        return original['warp'](*args,**kwargs)
    def picture(label):
        original['picture'](label);captures.append(dict(file=label+'.png',sha256=sha(output/(label+'.png'))))
    def observe(before,after):route.append(dict(phase=phase,before=list(before),after=list(after)))
    ns.update(step=step,native=native,script=script,warp=warp,picture=picture,
              walk_observer=observe,walk_transition_pictures=False,walk_max_ticks=600)
    def state(label,foot=False):
        value=ns['assert_foot'](label) if foot else ns['assert_surf']()
        if not foot:picture(label)
        states.append(dict(label=label,**value));return value
    try:
        warp(PORT,13,17);native('SetPlayerAvatarTransitionFlags',1);native('DisableWildEncounters',1);step(90)
        assert ns['position']()==(13,17)
        fixture=False;phase='pedestrian-water-barrier'
        step(90,16);step(30)
        assert state('three-pedestrian-blocked',True)['tile']==[13,17]
        phase='native-surf-departure';ns['walk']((PORT,14,17));state('three-east-boarding-water')
        ns['set_passability'](water_only=True)
        phase='southern-ocean-to-west'
        for point in [(15,20),(3,20),(2,17)]:ns['walk']((PORT,*point))
        state('three-west-water-reached')
        phase='terminal-body-barrier';ns['walk']((PORT,3,17));step(90,16);step(30)
        assert state('three-terminal-blocks-surf')['tile']==[3,17]
        width,height,_=ns['blocks'][coast]
        choices=[(x,y) for y in range(height) for x in range(width)
            if y*width+x in ns['passable'][coast] and ns['water_behaviors'][ns['behaviors'][coast][y*width+x]]]
        target=min(choices,key=lambda p:abs(p[0]-width//2)+abs(p[1]-height//2))
        phase='ocean-coast-roundtrip';ns['walk']((coast,*target));state('three-real-coast-crossed')
        ns['walk']((PORT,2,17));state('three-coast-returned')
        phase='southern-perimeter-barrier';ns['walk']((PORT,3,25));step(90,128);step(30)
        assert state('three-southern-reef-blocked')['tile']==[3,25]
        phase='west-to-east-return'
        for point in [(15,23),(15,18),(14,17)]:ns['walk']((PORT,*point))
        state('three-returned-east-water')
        ns['set_passability']();phase='native-reboarding';ns['walk']((PORT,13,17))
        state('three-reboarded-dry-terminal',True)
        phase='native-menu-save'
        ns['press'](8);step(90)
        lib,s=ns['lib'],ns['s']
        actions=[lib.read8(s['sCurrentStartMenuActions']+i) for i in range(lib.read8(s['sNumStartMenuActions']))]
        assert actions.count(5)==1,('SAVE missing from native menu',actions)
        target=actions.index(5)
        for _ in range(12):
            if lib.read8(s['sStartMenuCursorPos'])==target:break
            ns['press'](128)
        assert lib.read8(s['sStartMenuCursorPos'])==target
        ns['press'](1);seen=set()
        callbacks={value:name for name,value in s.items()}
        for _ in range(120):
            callback=lib.read32(s['sSaveDialogCallback'])&~1
            seen.add(callbacks.get(callback,hex(callback)))
            if callback==s['SaveOverwriteInputCallback']:ns['press'](64)
            if 'SaveReturnSuccessCallback' in seen and not lib.read8(s['sLockFieldControls']):break
            ns['press'](1)
        else:raise AssertionError(('Native SAVE did not finish',seen))
        assert 'SaveReturnSuccessCallback' in seen
        import ctypes
        lib.export_save.argtypes=[ctypes.c_char_p];lib.export_save.restype=ctypes.c_int
        battery=output/'three-after-controller-save.sav'
        assert lib.export_save(str(battery).encode()) and battery.stat().st_size==131072
        picture('three-saved-through-native-menu')
        verify()
        result=dict(kind='atlas-three-port-native-component',passed=True,
            rom_sha256=frozen['pokeemerald.gba'],elf_sha256=frozen['pokeemerald.elf'],marker_sha256=frozen['.journey-atlas-surf-layout'],
            prepared_source_sha256=prepared,source_files_checked=len(expected),actual_coast_adapter=coast,
            initial_party_progress_and_dry_placement_are_fixtures=True,encounter_suppression_is_fixture=True,
            after_placement_movement_controllers_only=True,private_read_only_query_trampoline_declared=True,
            southern_ocean_both_directions=True,real_coast_connection_both_directions=True,
            surf_departure_and_reboarding=True,pedestrian_and_reef_and_terminal_barriers=True,
            saved_through_native_menu=True,battery=dict(file=battery.name,sha256=sha(battery)),
            save_menu_callbacks=sorted(seen),
            controls=controls,queries=queries,route=route,states=states,captures=captures,
            final_release_validated=False,global_network_validated=False)
        (output/'three-native.json').write_text(json.dumps(result,indent=2)+'\n')
        return result
    except BaseException:
        picture('three-native-failure');raise
    finally:ns['lib'].stop()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','library','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();r=run(a.source,a.library,a.output)
    print(json.dumps(dict(passed=r['passed'],captures=len(r['captures']),final_release_validated=False)))
