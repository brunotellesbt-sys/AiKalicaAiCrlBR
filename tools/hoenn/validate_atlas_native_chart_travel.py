"""Prove native-map water and return through real Atlas coast connections.

These trips collect physical travel evidence for regional chart features.
They do not classify/exclude atlas pixels and cannot certify a release.
Each case declares one dry placement and progress/party fixtures; movement
afterward is controller-only, including Surf and native map/camera seams.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

from validate_coast_scenery_objects import bootstrap
from candidate_layer import Layer
from prepare_generated_area_review import PRIOR,LAYER

CASES={
    'route12':dict(native='Route12_Frlg',component=1,start=['Route12_Frlg',12,48],point=['Route12_Frlg',8,48],extra=[]),
    'treasure':dict(native='OneIsland_TreasureBeach_Frlg',component=0,start=['OneIsland_TreasureBeach_Frlg',14,20],point=['OneIsland_TreasureBeach_Frlg',0,0],extra=[]),
    'pacifidlog':dict(native='Route130',component=0,start=['PacifidlogTown',10,27],point=['PacifidlogTown',0,8],extra=['Route131','PacifidlogTown']),
    'bond':dict(native='ThreeIsland_Port_Frlg',component=1,start=['ThreeIsland_Port_Frlg',13,17],point=['ThreeIsland_BondBridge_Frlg',48,13],extra=['ThreeIsland_Frlg','ThreeIsland_BondBridge_Frlg']),
}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(source,library,output,case):
    source,library,output=map(lambda p:Path(p).resolve(),(source,library,output));output.mkdir(parents=True,exist_ok=True)
    marker=json.loads((source/'.journey-atlas-surf-layout').read_bytes());prepared=marker['prepared_sha256']
    expected=Layer(source,'atlas-surf-layout',PRIOR+[LAYER]).expected;expected.update(prepared)
    source_manifest=hashlib.sha256(json.dumps(sorted(expected.items()),separators=(',',':')).encode()).hexdigest()
    frozen={n:sha(source/n) for n in ('pokeemerald.gba','pokeemerald.elf','.journey-atlas-surf-layout')}
    def verify():
        assert frozen=={n:sha(source/n) for n in frozen}
        for p,h in expected.items():assert sha(source/p)==h,p
    row=CASES[case];binding=next(b for b in marker['adapter_plan']['bindings']
        if (b['native_map'],b['component'])==(row['native'],row['component']))
    names={row['native'],row['start'][0],row['point'][0],binding['adapter'],*row['extra']}
    verify();ns=bootstrap(source,library,output,names)
    old={k:ns[k] for k in ('step','native','script','warp','picture')}
    fixture=True;depth=0;phase='fixture';controls=[];queries=[];route=[];states=[];captures=[]
    def step(frames,key=0):
        if not fixture and not depth:controls.append(dict(phase=phase,frames=frames,key=key))
        old['step'](frames,key)
    def native(name,*args,**kwargs):
        nonlocal depth
        if not fixture:
            assert name.startswith(('MapGridGet','MetatileBehavior_Is')) or name in {
                'GetPlayerFacingDirection','GetPlayerFacingMovementDirection','PlayerGetElevation','IsPlayerFacingSurfableFishableWater'},name
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
              walk_observer=observe,walk_transition_pictures=False,walk_max_ticks=4000)
    def state(label):
        value=ns['player_state']();assert value['sprite_visible'] and value['object_visible'],value
        picture(label);states.append(dict(label=label,**value));return value
    try:
        if case=='bond':
            text=(source/'include/constants/vars.h').read_text()
            variable=int(re.search(r'^#define\s+VAR_MAP_SCENE_THREE_ISLAND\s+(0x\w+)',text,re.M)[1],16)
            native('VarSet',variable,4)
            flags=(source/'include/constants/flags.h').read_text()
            for name in ('FLAG_HIDE_THREE_ISLAND_BIKERS','FLAG_HIDE_THREE_ISLAND_LONE_BIKER','FLAG_RESCUED_LOSTELLE'):
                value=int(re.search(r'^#define\s+'+name+r'\s+(0x\w+)',flags,re.M)[1],16)
                native('FlagSet',value)
        warp(*row['start']);native('SetPlayerAvatarTransitionFlags',1);native('DisableWildEncounters',1);step(90)
        assert not ns['player_state']()['surfing'];fixture=False
        phase='native-water-approach';ns['walk'](tuple(row['point']))
        assert state(case+'-actual-native-water')['surfing']
        x,y=row['point'][1:]
        observed=dict(metatile=native('MapGridGetMetatileIdAt',x+7,y+7),
                      collision=native('MapGridGetCollisionAt',x+7,y+7),elevation=native('MapGridGetElevationAt',x+7,y+7),
                      behavior=native('MapGridGetMetatileBehaviorAt',x+7,y+7))
        native_word=observed['metatile']|(observed['collision']<<10)|(observed['elevation']<<12)
        width0,height0,words0=ns['blocks'][row['point'][0]]
        assert native_word==words0[y*width0+x]
        assert native('MetatileBehavior_IsSurfableWaterOrUnderwater',observed['behavior'])
        width,height,_=ns['blocks'][binding['adapter']]
        choices=[(x,y) for y in range(height) for x in range(width)
                 if y*width+x in ns['passable'][binding['adapter']]
                 and ns['water_behaviors'][ns['behaviors'][binding['adapter']][y*width+x]]]
        target=min(choices,key=lambda p:abs(p[0]-width//2)+abs(p[1]-height//2))
        phase='actual-coast-connection';ns['walk']((binding['adapter'],*target))
        assert state(case+'-real-atlas-coast-reached')['surfing']
        phase='return-native-water';ns['walk'](tuple(row['point']))
        assert state(case+'-native-water-returned')['surfing']
        phase='native-reboarding';ns['walk'](tuple(row['start']))
        assert not state(case+'-dry-origin-returned')['surfing']
        verify()
        r=dict(kind='native-chart-feature-physical-trip',case=case,passed=True,
            rom_sha256=frozen['pokeemerald.gba'],elf_sha256=frozen['pokeemerald.elf'],marker_sha256=frozen['.journey-atlas-surf-layout'],
            prepared_source_sha256=prepared,source_files_checked=len(expected),
            complete_native_and_prepared_source_manifest_sha256=source_manifest,
            initial_party_progress_and_single_dry_placement_are_fixtures=True,
            extra_progress_fixture='Three Island scene4, bikers departed, Lostelle rescued' if case=='bond' else None,
            after_placement_movement_controllers_only=True,private_read_only_query_trampoline_declared=True,
            actual_native_water_point=row['point'],actual_coast_adapter=binding['adapter'],
            observed_native_point=observed,native_point_word=native_word,
            native_water_coast_and_dry_return=True,controls=controls,queries=queries,route=route,states=states,captures=captures,
            atlas_pixel_ownership_certified=False,global_network_validated=False,final_release_validated=False)
        (output/'native-chart-trip.json').write_text(json.dumps(r,indent=2)+'\n');return r
    except BaseException:picture(case+'-native-chart-trip-failure');raise
    finally:ns['lib'].stop()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','library','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--case',choices=CASES,required=True)
    a=p.parse_args();r=run(a.source,a.library,a.output,a.case)
    print(json.dumps(dict(passed=r['passed'],case=a.case,captures=len(r['captures']),final_release_validated=False)))
