"""Walk the freed bridge, enter House3 and sail with its relocated captain.

One dry starting placement, party and progress are explicit fixtures. After
that placement only controllers and declared private native getter queries
are allowed. The final battery is saved through the actual game menu.
"""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path

from validate_coast_scenery_objects import bootstrap

TOWN='PacifidlogTown';HOUSE='PacifidlogTown_House3';DEST='JourneyMossdeepHarbor'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(source,library,output):
    source,library,output=map(lambda p:Path(p).resolve(),(source,library,output));output.mkdir(parents=True,exist_ok=True)
    prepared=json.loads((source/'.journey-atlas-surf-layout').read_bytes())['prepared_sha256']
    frozen={n:sha(source/n) for n in ('pokeemerald.gba','pokeemerald.elf','.journey-atlas-surf-layout')}
    def verify():
        assert frozen=={n:sha(source/n) for n in frozen}
        for n,h in prepared.items():assert sha(source/n)==h,n
    verify();ns=bootstrap(source,library,output,[TOWN,HOUSE,DEST])
    old={k:ns[k] for k in ('step','native','script','warp','picture')}
    fixture=True;depth=0;phase='fixture';controls=[];queries=[];route=[];states=[];captures=[]
    def step(frames,key=0):
        if not fixture and not depth:controls.append(dict(phase=phase,frames=frames,key=key))
        old['step'](frames,key)
    def native(name,*args,**kwargs):
        nonlocal depth
        if not fixture:
            assert name.startswith(('MapGridGet','MetatileBehavior_Is')) or name in {
                'GetPlayerFacingDirection','GetPlayerFacingMovementDirection','PlayerGetElevation',
                'IsPlayerFacingSurfableFishableWater'},name
            queries.append(dict(phase=phase,function=name,arguments=list(args)))
        depth+=1
        try:return old['native'](name,*args,**kwargs)
        finally:depth-=1
    def script(*args,**kwargs):
        assert fixture or depth,'Injected gameplay script after initial placement'
        return old['script'](*args,**kwargs)
    def warp(*args,**kwargs):
        assert fixture,'Warp after initial placement'
        return old['warp'](*args,**kwargs)
    def picture(label):
        old['picture'](label);captures.append(dict(file=label+'.png',sha256=sha(output/(label+'.png'))))
    def observe(before,after):route.append(dict(phase=phase,before=list(before),after=list(after)))
    ns.update(step=step,native=native,script=script,warp=warp,picture=picture,
              walk_observer=observe,walk_transition_pictures=False)
    lib,s=ns['lib'],ns['s']
    def actors():
        player=lib.read8(s['gPlayerAvatar']+5)
        return [dict(slot=i,local_id=lib.read8(s['gObjectEvents']+i*36+8)) for i in range(16)
                if i!=player and lib.read8(s['gObjectEvents']+i*36)&1]
    def state(label):
        value=ns['assert_foot'](label);states.append(dict(label=label,actors=actors(),**value));return value
    try:
        warp(TOWN,10,27);native('SetPlayerAvatarTransitionFlags',1);native('DisableWildEncounters',1);step(90)
        fixture=False;phase='freed-bridge'
        for point in [(11,27),(14,27),(9,27)]:ns['walk']((TOWN,*point))
        state('pacifidlog-freed-bridge')
        assert 4 not in [r['local_id'] for r in actors()]
        assert 5 in [r['local_id'] for r in actors()],'Original boat numeric ID changed or boat disappeared'
        phase='house-door-and-captain';ns['walk']((HOUSE,7,7))
        state('pacifidlog-captain-inside-nearest-house')
        assert {1,2,4}<={r['local_id'] for r in actors()},actors()
        ns['talk_captain']();assert lib.read16(s['gSpecialVar_0x8008'])==11
        picture('pacifidlog-indoor-captain-native-network-menu')
        phase='native-ferry-from-house'
        for index in (1,1,1):ns['choose'](index)
        outward=ns['voyage'](DEST,(16,13));state('pacifidlog-arrived-mossdeep-by-ferry')
        phase='native-ferry-return'
        ns['talk_captain']();assert lib.read16(s['gSpecialVar_0x8008'])==16
        for index in (1,1,1):ns['choose'](index)
        returned=ns['voyage'](TOWN,(10,27));state('pacifidlog-returned-to-freed-bridge')
        ns['walk']((TOWN,11,27));state('pacifidlog-bridge-free-after-return')
        phase='house-return-and-native-save';ns['walk']((HOUSE,7,7));state('pacifidlog-house-reentered')
        assert 4 in [r['local_id'] for r in actors()]
        ns['press'](8);step(90)
        actions=[lib.read8(s['sCurrentStartMenuActions']+i) for i in range(lib.read8(s['sNumStartMenuActions']))]
        assert actions.count(5)==1,actions;target=actions.index(5)
        for _ in range(12):
            if lib.read8(s['sStartMenuCursorPos'])==target:break
            ns['press'](128)
        assert lib.read8(s['sStartMenuCursorPos'])==target
        ns['press'](1);seen=set();callbacks={value:name for name,value in s.items()}
        for _ in range(120):
            callback=lib.read32(s['sSaveDialogCallback'])&~1;seen.add(callbacks.get(callback,hex(callback)))
            if callback==s['SaveOverwriteInputCallback']:ns['press'](64)
            if 'SaveReturnSuccessCallback' in seen and not lib.read8(s['sLockFieldControls']):break
            ns['press'](1)
        else:raise AssertionError(('Native SAVE did not finish',seen))
        assert 'SaveReturnSuccessCallback' in seen
        lib.export_save.argtypes=[ctypes.c_char_p];lib.export_save.restype=ctypes.c_int
        battery=output/'captain-house-after-native-save.sav'
        assert lib.export_save(str(battery).encode()) and battery.stat().st_size==131072
        picture('pacifidlog-house-saved-through-native-menu');verify()
        result=dict(kind='pacifidlog-relocated-captain-native-proof',passed=True,
            rom_sha256=frozen['pokeemerald.gba'],elf_sha256=frozen['pokeemerald.elf'],marker_sha256=frozen['.journey-atlas-surf-layout'],
            prepared_source_sha256=prepared,source_files_checked=len(prepared),
            initial_party_progress_and_single_dry_placement_are_fixtures=True,encounter_suppression_is_fixture=True,
            after_placement_movement_controllers_only=True,private_read_only_query_trampoline_declared=True,
            bridge_both_directions=True,nearest_house_native_door_roundtrip=True,captain_service_preserved=True,
            original_boat_numeric_local_id_preserved=True,house_residents_preserved=True,
            voyages=[outward,returned],saved_through_native_menu=True,
            battery=dict(file=battery.name,sha256=sha(battery)),save_menu_callbacks=sorted(seen),
            controls=controls,queries=queries,route=route,states=states,captures=captures,
            final_release_validated=False,global_network_validated=False)
        (output/'captain-native.json').write_text(json.dumps(result,indent=2)+'\n');return result
    except BaseException:picture('pacifidlog-captain-native-failure');raise
    finally:lib.stop()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','library','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();r=run(a.source,a.library,a.output)
    print(json.dumps(dict(passed=r['passed'],voyages=len(r['voyages']),captures=len(r['captures']),final_release_validated=False)))
