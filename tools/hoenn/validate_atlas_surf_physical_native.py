"""Controller proof for the identified three-map diagnostic; never a release.

Initial party/progress/placement/Surf and encounter suppression are fixtures.
After placement only controllers move the player. Declared getter trampolines
inspect terrain/GPS; seam timing uses frame steps and direct memory reads only.
"""
import argparse
import hashlib
import json
from pathlib import Path

from validate_coast_scenery_objects import bootstrap
from validate_sevii_route_boundaries_native import observe_cells


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(source, library, output):
    source, library, output = [Path(p).resolve() for p in (source,library,output)]
    output.mkdir(parents=True,exist_ok=True)
    marker=source/'.journey-atlas-stage-smoke'
    metadata=json.loads(marker.read_text())
    plan=metadata['geometry_plan']
    assert metadata['diagnostic_only'] and not metadata['release_eligible']
    assert len(plan['chunks'])==3 and plan['chunks'][0]['width']==4
    prepared=metadata['prepared_sha256']
    frozen={name:digest(source/name) for name in ('pokeemerald.gba','pokeemerald.elf','.journey-atlas-stage-smoke')}

    def unchanged():
        assert frozen=={name:digest(source/name) for name in frozen}
        assert all(digest(source/name)==expected for name,expected in prepared.items())

    unchanged()
    names=[row['name'] for row in plan['chunks']]
    chunks={row['name']:row for row in plan['chunks']}
    a,b,c=names
    ns=bootstrap(source,library,output,names)
    lib,s=ns['lib'],ns['s']
    original={name:ns[name] for name in ('native','step','script','warp','picture')}
    fixture,depth,phase,frames=True,0,'placement',0
    controls,queries,route,seams,captures,observations=[],[],[],[],[],[]

    def step(count,key=0):
        nonlocal frames
        if not fixture and not depth:
            if controls and controls[-1]['phase']==phase and controls[-1]['key']==key:
                controls[-1]['frames']+=count
            else:
                controls.append(dict(phase=phase,frames=count,key=key))
        original['step'](count,key); frames+=count

    def native(name,*values,**kwargs):
        nonlocal depth
        if not fixture:
            assert name.startswith(('MapGridGet','MetatileBehavior_Is')) or name in {
                'PlayerGetElevation','JourneyWorldMapPosition','GetMapBorderIdAt',
                'GetPlayerFacingDirection','IsPlayerFacingSurfableFishableWater'},name
            queries.append(dict(phase=phase,function=name,arguments=list(values),frame=frames))
        depth+=1
        try:return original['native'](name,*values,**kwargs)
        finally:depth-=1

    def script(*args,**kwargs):
        assert fixture or depth,'Mutable gameplay script during controller proof'
        return original['script'](*args,**kwargs)

    def warp(*args,**kwargs):
        assert fixture,'Placement fixture after departure'
        return original['warp'](*args,**kwargs)

    def picture(label):
        original['picture'](label)
        record=dict(file=label+'.png',sha256=digest(output/(label+'.png')))
        captures.append(record);return record

    def world(point):
        name,x,y=point;origin=chunks[name]['origin']
        return origin[0]+x,origin[1]+y

    def observe(before,after):
        row=dict(phase=phase,before=list(before),after=list(after),
                 global_before=list(world(before)),global_after=list(world(after)))
        if phase=='north-eight-tiles':
            assert row['global_after'][0]==row['global_before'][0]
            assert row['global_after'][1]==row['global_before'][1]-1
        route.append(row)

    ns.update(native=native,step=step,script=script,warp=warp,picture=picture,
              walk_observer=observe,walk_transition_pictures=False,walk_max_ticks=200)

    def raw_state():
        name=ns['by_location'][ns['location']()]
        obj=s['gObjectEvents']+lib.read8(s['gPlayerAvatar']+5)*36
        save=ns['save']()
        return dict(map=name,tile=list(ns['position']()),
                    saved_tile=[lib.read16(save),lib.read16(save+2)],
                    idle=bool(ns['idle']()),surfing=bool(lib.read8(s['gPlayerAvatar'])&8),
                    object_active=bool(lib.read8(obj)&1))

    def seam(key,goal,label):
        nonlocal phase
        phase=label
        before=raw_state(); initial=frames; samples=[]
        published=consistent=None;stable=0;released=False
        for i in range(120):
            step(1,0 if released else key)
            value=raw_state(); value['frame']=i+1;samples.append(value)
            if value['map']!=before['map'] and published is None:published=i+1
            if [value['map'],*value['tile']]==list(goal) and value['tile']==value['saved_tile']:
                if consistent is None:consistent=i+1
                released=True
                stable=stable+1 if value['idle'] and value['surfing'] and value['object_active'] else 0
                if stable>=20:break
            else:stable=0
        else:raise AssertionError(('Seam did not settle within120frames',label,samples))
        assert published is not None and consistent is not None
        assert consistent-published<=30,('Synchronous loading pause',label,published,consistent)
        after=raw_state()
        source_point=(before['map'],*before['tile'])
        observe(source_point,goal)
        delta=[v-u for u,v in zip(world(source_point),world(goal))]
        expected={16:[1,0],32:[-1,0],64:[0,-1],128:[0,1]}[key]
        assert delta==expected,(label,delta,expected)
        seams.append(dict(case=label,before=before,after=after,key=key,
                          start_frame=initial,end_frame=frames,
                          total_frames=frames-initial,map_published_frame=published,
                          consistent_coordinates_frame=consistent,
                          inconsistent_coordinate_frames=consistent-published,
                          frame_samples=samples,no_native_queries_during_timing=True,
                          global_tile_delta=delta,capture=picture(label)))

    def gps():
        point=(ns['by_location'][ns['location']()],*ns['position']())
        value=native('JourneyWorldMapPosition')
        actual=[value&255,(value>>8)&255]
        expected=[v//8 for v in world(point)]
        assert actual==expected,(point,actual,expected)
        return dict(point=list(point),global_tile=list(world(point)),atlas=actual)

    def cell(x,y,word):
        at=s['gBackupMapLayout']; width=lib.read32(at);height=lib.read32(at+4)
        xx,yy=x+7,y+7
        assert 0<=xx<width and 0<=yy<height
        loaded=lib.read16(lib.read32(at+8)+2*(yy*width+xx))
        assert loaded==word,(x,y,loaded,word)
        assert native('MapGridGetCollisionAt',xx,yy)==((word>>10)&3)
        assert native('MapGridGetElevationAt',xx,yy)==word>>12
        return dict(cell=[x,y],loaded_word=loaded,height=word>>12,collision=(word>>10)&3)

    try:
        warp(a,3,3);native('SetPlayerAvatarTransitionFlags',8);native('DisableWildEncounters',1);step(120)
        assert raw_state()['tile']==[3,3] and raw_state()['surfing']
        fixture=False
        seam(16,(b,0,3),'east-out-of-four-tile-map')
        observations.append(dict(case='west-strip-from-narrow-source',terrain=cell(-1,3,0x112B)))
        phase='approach-south-seam';ns['walk']((b,13,7))
        seam(128,(c,13,0),'south-across-second-seam')
        phase='south-to-north-start';ns['walk']((c,13,10))
        start=gps();phase='north-eight-tiles';ns['walk']((c,13,2));end=gps()
        assert end['global_tile']==[start['global_tile'][0],start['global_tile'][1]-8]
        assert end['atlas']==[start['atlas'][0],start['atlas'][1]-1]
        observations.append(dict(case='north-eight-tiles',start=start,end=end))
        phase='reef-blocks-surf';before=raw_state();step(90,32);step(30)
        assert raw_state()['map']==before['map'] and raw_state()['tile']==before['tile']
        terrain=cell(12,2,0x1643)
        avatar=ns['assert_surf']()
        avatar['native_avatar_pixels']=ns['visible_avatar_pixels']()
        observations.append(dict(case='reef-blocks-surf',terrain=terrain,
                                 player=avatar,capture=picture('reef-blocks-surf')))
        phase='approach-north-seam';ns['walk']((c,13,0))
        seam(64,(b,13,7),'north-return')
        phase='approach-west-seam';ns['walk']((b,0,3))
        seam(32,(a,3,3),'west-return-to-four-tile-map')
        phase='diagonal-before-entering';ns['walk']((a,3,6))
        diagonal=cell(4,8,0x1643)
        assert native('GetMapBorderIdAt',11,15)&0xFFFFFFFF==0xFFFFFFFF
        pixels=observe_cells(ns,[(4,8,0x243)])
        observations.append(dict(case='diagonal-real-terrain-without-direct-connection',
                                 terrain=diagonal,border_invalid=True,pixels=pixels,
                                 capture=picture('diagonal-real-terrain')))
        unchanged()
        report=dict(kind='atlas-physical-three-map-native-diagnostic',passed=True,
                    diagnostic_build=True,final_release_validated=False,
                    artifact_sha256=frozen,prepared_source_sha256=prepared,
                    initial_party_progress_placement_surf_and_encounter_suppression_are_fixtures=True,
                    after_placement_movement_controllers_only=True,
                    private_read_only_query_trampoline_declared=True,
                    frozen_source_marker_rom_and_elf_unchanged=True,
                    real_atlas_route_classification_proven=False,
                    full_network_performance_proven=False,
                    seams=seams,observations=observations,route=route,
                    controls=controls,queries=queries,captures=captures)
        (output/'physical-native.json').write_text(json.dumps(report,indent=2)+'\n')
        return report
    except BaseException:
        picture('physical-native-failure')
        (output/'physical-native-failure.json').write_text(json.dumps(dict(
            passed=False,artifact_sha256=frozen,phase=phase,route=route,seams=seams,
            controls=controls,queries=queries,captures=captures),indent=2)+'\n')
        raise
    finally:lib.stop()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--library',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    report=run(args.source,args.library,args.output)
    print(json.dumps(dict(passed=report['passed'],seams=[dict(case=row['case'],total_frames=row['total_frames'],
          inconsistent_coordinate_frames=row['inconsistent_coordinate_frames']) for row in report['seams']],
          final_release_validated=False),indent=2))
