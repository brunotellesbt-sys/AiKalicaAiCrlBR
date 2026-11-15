"""Prove five native Dive/portal/Emerge trips by controllers on a frozen ROM.

Each site gets an explicit initial placement/party/progress/Surf fixture.
No gameplay setters, warps, effects or coordinate writes run after departure.
Only declared read-only native getters use the private query trampoline.
The isolated probes do not certify the final ocean network or five editions.
"""
import argparse
import hashlib
import json
from pathlib import Path

from validate_coast_scenery_objects import bootstrap


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(source,library,output):
    source,library,output=[Path(p).resolve() for p in (source,library,output)]
    output.mkdir(parents=True,exist_ok=True)
    marker=source/'.journey-atlas-stage-smoke';metadata=json.loads(marker.read_text())
    assert metadata['diagnostic_role']=='five-isolated-dives'
    assert metadata['diagnostic_only'] is True and metadata['release_eligible'] is False
    prepared=metadata['prepared_sha256']
    artifacts={name:digest(source/name) for name in ('pokeemerald.gba','pokeemerald.elf','.journey-atlas-stage-smoke')}
    def unchanged():
        assert artifacts=={name:digest(source/name) for name in artifacts}
        assert all(digest(source/name)==expected for name,expected in prepared.items())
    unchanged()
    sites=metadata['dives']['sites'];plan=metadata['geometry_plan']
    names=[r['name'] for r in plan['chunks']]
    names+=[name for site in sites for name in (site['depth'],site['sanctuary'])]
    ns=bootstrap(source,library,output,names)
    lib,s=ns['lib'],ns['s'];original={k:ns[k] for k in ('step','native','script','warp','picture')}
    fixture,depth,phase,frames=True,0,'setup',0
    controls,queries,captures,route,cases=[],[],[],[],[]

    def step(count,key=0):
        nonlocal frames
        if not fixture and not depth:
            if controls and controls[-1]['phase']==phase and controls[-1]['key']==key:
                controls[-1]['frames']+=count
            else:controls.append(dict(phase=phase,frames=count,key=key))
        original['step'](count,key);frames+=count

    def native(name,*values,**kwargs):
        nonlocal depth
        if not fixture:
            assert name.startswith(('MapGridGet','MetatileBehavior_Is')) or name in {
                'PlayerGetElevation','JourneyWorldMapPosition','GetPlayerFacingDirection',
                'IsPlayerFacingSurfableFishableWater'},('Mutable native query after departure',name)
            queries.append(dict(phase=phase,function=name,arguments=list(values),frame=frames))
        depth+=1
        try:return original['native'](name,*values,**kwargs)
        finally:depth-=1

    def script(*args,**kwargs):
        assert fixture or depth,'Gameplay script injection after initial placement'
        return original['script'](*args,**kwargs)

    def warp(*args,**kwargs):
        assert fixture,'Travel fixture used during controller trip'
        return original['warp'](*args,**kwargs)

    def picture(label):
        original['picture'](label)
        row=dict(file=label+'.png',sha256=digest(output/(label+'.png')))
        captures.append(row);return row

    def observe(before,after):
        route.append(dict(phase=phase,before=list(before),after=list(after)))

    ns.update(step=step,native=native,script=script,warp=warp,picture=picture,
              walk_observer=observe,walk_transition_pictures=False,walk_max_ticks=500)

    def raw():
        save=ns['save']()
        return dict(map=ns['by_location'][ns['location']()],tile=list(ns['position']()),
                    saved_tile=[lib.read16(save),lib.read16(save+2)],
                    mode=lib.read8(s['gPlayerAvatar']),idle=bool(ns['idle']()))

    def state(label):
        value=raw();x,y=value['tile']
        value.update(elevation=native('PlayerGetElevation'),tile_elevation=native('MapGridGetElevationAt',x+7,y+7),
                     tile_collision=native('MapGridGetCollisionAt',x+7,y+7),
                     behavior=native('MapGridGetMetatileBehaviorAt',x+7,y+7))
        position=native('JourneyWorldMapPosition');value['atlas']=[position&255,(position>>8)&255]
        value['capture']=picture(label)
        return value

    def effect(button,goal,label):
        nonlocal phase
        phase=label;before=raw();start=frames;stable=0
        step(1,button);step(30)
        for tick in range(50):
            value=raw()
            if [value['map'],*value['tile']]==list(goal) and value['tile']==value['saved_tile'] and value['idle']:
                stable+=1
                if stable==2:break
                step(20)
            else:
                stable=0
                # Yes/no and text are advanced through A, including the
                # native field-effect sequence. No setters start the effect.
                step(1,1);step(20)
        else:raise AssertionError(('Native Dive/Emerge controls did not reach goal',label,goal,raw()))
        after=state(label)
        return dict(before=before,after=after,frames=frames-start,button=button,
                    native_field_effect_started_by_controllers=True)

    try:
        native('ScriptSetMonMoveSlot',0,291,2)
        for site in sites:
            theme=site['name'];surface='JourneyAtlasDiveProbe'+theme
            depth_map,sanctuary=site['depth'],site['sanctuary'];px,py=site['portal']
            fixture=True;phase=theme+'-placement'
            warp(surface,4,6);native('SetPlayerAvatarTransitionFlags',8);native('DisableWildEncounters',1);step(120)
            assert raw()['map']==surface and raw()['tile']==[4,6] and raw()['mode']&8
            fixture=False
            case=dict(site=theme,initial_fixture=dict(surface=surface,tile=[4,6],surf=True,
                                                     party_has_surf_and_dive=True,encounters_suppressed=True))
            phase=theme+'-surface-reef'
            step(90,16);step(30)
            assert raw()['tile']==[6,6] and raw()['map']==surface
            assert native('MapGridGetCollisionAt',14,13)==1
            case['surface_reef_blocked']=state(theme+'-surface-reef')
            ns['walk']((surface,4,6))
            start=state(theme+'-before-dive')
            case['descent']=effect(1,(depth_map,px,py+2),theme+'-native-dive')
            entered=case['descent']['after']
            assert entered['mode']&16 and entered['tile_elevation']==3 and entered['tile_collision']==0
            assert entered['atlas']==start['atlas']==site['atlas']
            phase=theme+'-blocked-emerge-reef'
            ns['walk']((depth_map,px+3,py+2))
            assert not native('MetatileBehavior_IsUnableToEmerge',native('MapGridGetMetatileBehaviorAt',px+10,py+9))
            before=raw();step(1,2);step(120)
            assert raw()['map']==before['map'] and raw()['tile']==before['tile'] and raw()['mode']&16
            case['blocked_emerge_reef']=state(theme+'-blocked-emerge-reef')
            phase=theme+'-blocked-emerge-no-owner'
            ns['walk']((depth_map,px+4,py+2));before=raw();step(1,2);step(120)
            assert raw()['map']==before['map'] and raw()['tile']==before['tile'] and raw()['mode']&16
            case['blocked_emerge_no_owner']=state(theme+'-blocked-emerge-no-owner')
            phase=theme+'-real-portal-entry'
            ns['walk']((depth_map,px,py+2));ns['walk']((sanctuary,14,17))
            inside=state(theme+'-sanctuary')
            assert not inside['mode']&(8|16) and inside['tile_collision']==0
            # Native sanctuary floor0x0364 has height0. Do not demand3.
            assert inside['tile_elevation']==0
            inside['avatar_pixels']=ns['visible_avatar_pixels']()
            case['sanctuary']=inside
            phase=theme+'-portal-return'
            ns['walk']((depth_map,px,py+2));case['depth_return']=state(theme+'-depth-return')
            assert case['depth_return']['mode']&16
            case['emerge']=effect(2,(surface,4,6),theme+'-native-emerge')
            returned=case['emerge']['after']
            assert returned['mode']&8 and not returned['mode']&16
            assert returned['tile_elevation']==1 and returned['atlas']==start['atlas']
            case['completed_by_controllers']=True;cases.append(case)
        unchanged()
        report=dict(kind='atlas-five-dive-native-diagnostic',passed=True,diagnostic_build=True,
                    final_release_validated=False,full_network_reachability_proven=False,
                    artifact_sha256=artifacts,prepared_source_sha256=prepared,
                    initial_party_progress_placement_and_surf_are_per_case_fixtures=True,
                    after_departure_controllers_only=True,private_read_only_query_trampoline_declared=True,
                    no_try_set_dive_warp_or_effect_setters_used_as_queries=True,
                    frozen_source_marker_rom_and_elf_unchanged=True,
                    cases=cases,controls=controls,queries=queries,route=route,captures=captures)
        (output/'dives-native.json').write_text(json.dumps(report,indent=2)+'\n')
        return report
    except BaseException:
        picture('dive-native-failure')
        (output/'dives-native-failure.json').write_text(json.dumps(dict(passed=False,phase=phase,
             artifact_sha256=artifacts,cases=cases,controls=controls,queries=queries,route=route,captures=captures),indent=2)+'\n')
        raise
    finally:lib.stop()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--library',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();report=run(args.source,args.library,args.output)
    print(json.dumps(dict(passed=report['passed'],sites=len(report['cases']),captures=len(report['captures']),final_release_validated=False),indent=2))
