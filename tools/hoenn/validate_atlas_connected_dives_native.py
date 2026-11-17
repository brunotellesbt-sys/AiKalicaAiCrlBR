"""Controller Dive/portal/Emerge trips on the actual connected frozen mesh.

Unlike the isolated historical probe, surface coordinates are resolved from
the actual compiled plan. Each case declares one initial Surf/party placement;
after that only controller input changes gameplay. Queries are read-only.
"""
import argparse
import hashlib
import json
from pathlib import Path

from candidate_layer import Layer
from prepare_generated_area_review import PRIOR,LAYER
from validate_coast_scenery_objects import bootstrap


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(source,library,output):
    source,library,output=map(lambda p:Path(p).resolve(),(source,library,output));output.mkdir(parents=True,exist_ok=True)
    marker=source/'.journey-atlas-surf-layout';metadata=json.loads(marker.read_bytes());prepared=metadata['prepared_sha256']
    expected=Layer(source,'atlas-surf-layout',PRIOR+[LAYER]).expected;expected.update(prepared)
    artifacts={n:sha(source/n) for n in ('pokeemerald.gba','pokeemerald.elf','.journey-atlas-surf-layout')}
    def unchanged():
        assert artifacts=={n:sha(source/n) for n in artifacts}
        for n,h in expected.items():assert sha(source/n)==h,n
    def owner(gx,gy):
        rows=[r for r in metadata['geometry_plan']['chunks'] if r['origin'][0]<=gx<r['origin'][0]+r['width']
              and r['origin'][1]<=gy<r['origin'][1]+r['height']]
        assert len(rows)==1,('Dive arrival has no unique actual surface owner',gx,gy)
        r=rows[0];return r['name'],gx-r['origin'][0],gy-r['origin'][1]
    sites=[];names=set()
    for row in metadata['dives']['sites']:
        px,py=row['portal'];point=owner(row['depth_origin'][0]+px,row['depth_origin'][1]+py+2)
        sites.append((row,point));names.update([point[0],row['depth'],row['sanctuary']])
    unchanged();ns=bootstrap(source,library,output,names);lib,s=ns['lib'],ns['s']
    original={k:ns[k] for k in ('step','native','script','warp','picture')}
    fixture=True;depth=0;phase='fixture';controls=[];queries=[];route=[];captures=[];cases=[]
    def step(count,key=0):
        if not fixture and not depth:controls.append(dict(phase=phase,frames=count,key=key))
        original['step'](count,key)
    def native(function,*args,**kwargs):
        nonlocal depth
        if not fixture:
            assert function.startswith(('MapGridGet','MetatileBehavior_Is')) or function in {
                'PlayerGetElevation','JourneyWorldMapPosition','GetPlayerFacingDirection',
                'GetPlayerFacingMovementDirection','IsPlayerFacingSurfableFishableWater'},function
            queries.append(dict(phase=phase,function=function,args=list(args)))
        depth+=1
        try:return original['native'](function,*args,**kwargs)
        finally:depth-=1
    def script(*args,**kwargs):
        assert fixture or depth,'Injected gameplay script after placement'
        return original['script'](*args,**kwargs)
    def warp(*args,**kwargs):
        assert fixture,'Warp fixture after departure'
        return original['warp'](*args,**kwargs)
    def picture(label):
        original['picture'](label);captures.append(dict(file=label+'.png',sha256=sha(output/(label+'.png'))))
    def observe(before,after):route.append(dict(phase=phase,before=list(before),after=list(after)))
    ns.update(step=step,native=native,script=script,warp=warp,picture=picture,
        walk_observer=observe,walk_transition_pictures=False,walk_max_ticks=1500)
    def raw():
        save=ns['save']();return dict(map=ns['by_location'][ns['location']()],tile=list(ns['position']()),
            saved_tile=[lib.read16(save),lib.read16(save+2)],mode=lib.read8(s['gPlayerAvatar']),idle=bool(ns['idle']()))
    def state(label):
        r=raw();x,y=r['tile'];r.update(elevation=native('PlayerGetElevation'),
            tile_elevation=native('MapGridGetElevationAt',x+7,y+7),collision=native('MapGridGetCollisionAt',x+7,y+7))
        value=native('JourneyWorldMapPosition');r['atlas']=[value&255,value>>8&255];picture(label);return r
    def effect(button,goal,label):
        nonlocal phase
        phase=label;step(1,button);step(30);stable=0
        for _ in range(60):
            r=raw()
            if [r['map'],*r['tile']]==list(goal) and r['tile']==r['saved_tile'] and r['idle']:
                stable+=1
                if stable==2:return state(label)
                step(20)
            else:stable=0;step(1,1);step(20)
        raise AssertionError(('Native Dive/Emerge did not reach actual plan point',label,goal,raw()))
    try:
        native('ScriptSetMonMoveSlot',0,291,2)
        for site,point in sites:
            fixture=True;theme=site['name'];phase=theme+'-fixture';px,py=site['portal']
            warp(*point);native('SetPlayerAvatarTransitionFlags',8);native('DisableWildEncounters',1);step(120)
            assert raw()['map']==point[0] and raw()['tile']==list(point[1:]) and raw()['mode']&8
            fixture=False;start=state(theme+'-actual-surface')
            assert start['atlas']==site['atlas'] and start['collision']==0 and start['tile_elevation']==1
            entered=effect(1,(site['depth'],px,py+2),theme+'-native-dive')
            assert entered['mode']&16 and entered['collision']==0 and entered['tile_elevation']==3
            assert entered['atlas']==start['atlas']
            phase=theme+'-real-portal';ns['walk']((site['sanctuary'],14,17));inside=state(theme+'-sanctuary')
            assert not inside['mode']&(8|16) and inside['collision']==0 and inside['tile_elevation']==0
            inside['visible_avatar_pixels']=ns['visible_avatar_pixels']()
            phase=theme+'-portal-return';ns['walk']((site['depth'],px,py+2));returned=state(theme+'-depth-return')
            assert returned['mode']&16
            emerged=effect(2,point,theme+'-native-emerge')
            assert emerged['mode']&8 and not emerged['mode']&16 and emerged['tile_elevation']==1
            assert emerged['atlas']==start['atlas']
            cases.append(dict(site=theme,actual_surface_point=list(point),initial_placement_is_fixture=True,
                start=start,dive=entered,sanctuary=inside,depth_return=returned,emerge=emerged,
                native_field_effect_and_portal_roundtrip_passed=True))
        unchanged();report=dict(kind='atlas-connected-five-dive-native',passed=True,artifact_sha256=artifacts,
            prepared_source_sha256=prepared,complete_source_files_checked=len(expected),
            per_case_initial_party_progress_surf_and_placement_are_fixtures=True,
            after_departure_controllers_only=True,private_read_only_query_trampoline_declared=True,
            actual_surface_owners_resolved_from_frozen_plan=True,cases=cases,controls=controls,
            queries=queries,route=route,captures=captures,all_emerge_rejection_boundaries_tested=False,
            global_network_travel_proven=False,final_release_validated=False)
        (output/'dives-native.json').write_text(json.dumps(report,indent=2)+'\n');return report
    except BaseException:picture('connected-dive-failure');raise
    finally:lib.stop()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('source','library','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();r=run(a.source,a.library,a.output)
    print(json.dumps(dict(passed=r['passed'],sites=len(r['cases']),final_release_validated=False)))
