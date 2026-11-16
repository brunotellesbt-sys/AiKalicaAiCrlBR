"""Observe both finished cliff faces and their native collision in mGBA."""
import argparse
import hashlib
import json
from pathlib import Path

from validate_coast_scenery_objects import bootstrap

NAME='SlateportCity'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(source,library,output):
    source,library,output=map(lambda p:Path(p).resolve(),(source,library,output));output.mkdir(parents=True,exist_ok=True)
    prepared=json.loads((source/'.journey-atlas-surf-layout').read_bytes())['prepared_sha256']
    frozen={n:sha(source/n) for n in ('pokeemerald.gba','pokeemerald.elf','.journey-atlas-surf-layout')}
    def verify():
        assert frozen=={n:sha(source/n) for n in frozen}
        for p,h in prepared.items():assert sha(source/p)==h,p
    verify();ns=bootstrap(source,library,output,[NAME,'Route109'])
    original={k:ns[k] for k in ('step','native','script','warp','picture')}
    fixture=True;depth=0;phase='fixture';controls=[];queries=[];route=[];captures=[];checks=[]
    def step(frames,key=0):
        if not fixture and not depth:controls.append(dict(phase=phase,frames=frames,key=key))
        original['step'](frames,key)
    def native(name,*args,**kwargs):
        nonlocal depth
        if not fixture:
            assert name.startswith(('MapGridGet','MetatileBehavior_Is')) or name in {
                'GetPlayerFacingDirection','GetPlayerFacingMovementDirection','PlayerGetElevation','IsPlayerFacingSurfableFishableWater'},name
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
              walk_observer=observe,walk_transition_pictures=False)
    try:
        warp(NAME,37,6);native('SetPlayerAvatarTransitionFlags',8);native('DisableWildEncounters',1);step(90)
        ns['assert_surf']();ns['set_passability'](water_only=True);fixture=False
        for tile in [(36,6),(36,7),(38,15),(38,16)]:
            x,y=tile;phase=f'cliff-{x}-{y}';ns['walk']((NAME,x+1,y))
            before=ns['assert_surf']();step(90,32);step(30);after=ns['assert_surf']()
            assert before['tile']==after['tile']==[x+1,y],(before,after)
            loaded=dict(metatile=native('MapGridGetMetatileIdAt',x+7,y+7),
                        collision=native('MapGridGetCollisionAt',x+7,y+7),
                        elevation=native('MapGridGetElevationAt',x+7,y+7))
            assert loaded==dict(metatile=0x190,collision=1,elevation=0),loaded
            picture(phase+'-complete-native-face');checks.append(dict(tile=list(tile),loaded=loaded,before=before,after=after))
        phase='southern-whole-rock-across-native-seam';ns['set_passability']()
        ns['walk']((NAME,37,59));ns['assert_surf']();picture('slateport-south-complete-rock-from-town')
        seam=[]
        for point in [(38,59),(39,59),(38,60),(39,60)]:
            x,y=point;seam.append(native('MapGridGetMetatileIdAt',x+7,y+7))
        assert seam==[0x150,0x151,0x158,0x159],seam
        ns['walk'](('Route109',37,2));ns['assert_surf']();picture('slateport-south-complete-rock-from-route109')
        ns['walk']((NAME,37,59));ns['assert_surf']();picture('slateport-south-native-seam-return')
        verify()
        result=dict(kind='slateport-native-finished-cliff-faces',passed=True,
            rom_sha256=frozen['pokeemerald.gba'],elf_sha256=frozen['pokeemerald.elf'],marker_sha256=frozen['.journey-atlas-surf-layout'],
            prepared_source_sha256=prepared,source_files_checked=len(prepared),
            initial_party_progress_and_single_Surf_placement_are_fixtures=True,
            after_placement_movement_controllers_only=True,private_read_only_query_trampoline_declared=True,
            checks=checks,controls=controls,queries=queries,route=route,captures=captures,
            southern_native_seam_roundtrip=True,southern_rock_complete_native_quartet=seam,
            final_release_validated=False,global_network_validated=False)
        (output/'cliffs-native.json').write_text(json.dumps(result,indent=2)+'\n');return result
    except BaseException:picture('slateport-cliff-native-failure');raise
    finally:ns['lib'].stop()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','library','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();r=run(a.source,a.library,a.output)
    print(json.dumps(dict(passed=r['passed'],checks=len(r['checks']),captures=len(r['captures']),final_release_validated=False)))
