"""Verify native Dive probe exports, controllers, pixels and frozen bindings."""
import argparse
import hashlib
import json
from pathlib import Path

from verify_sevii_integrated_piers_update import verify_captures,verify_native_avatar_pixels


SITES=[('Mares',[125,68],[38,10]),('Origens',[135,87],[38,10]),
       ('Profundezas',[134,97],[38,10]),('Dimensoes',[13,89],[30,64]),('Abismo',[14,99],[30,64])]


def verify(report,directory,source=None):
    assert report['kind']=='atlas-five-dive-native-diagnostic'
    for key in ['passed','diagnostic_build','initial_party_progress_placement_and_surf_are_per_case_fixtures',
                'after_departure_controllers_only','private_read_only_query_trampoline_declared',
                'no_try_set_dive_warp_or_effect_setters_used_as_queries','frozen_source_marker_rom_and_elf_unchanged']:
        assert report[key] is True,key
    assert report['final_release_validated'] is False and report['full_network_reachability_proven'] is False
    artifacts=report['artifact_sha256'];prepared=report['prepared_source_sha256']
    assert set(artifacts)=={'pokeemerald.gba','pokeemerald.elf','.journey-atlas-stage-smoke'}
    assert prepared and 'src/data/journey_atlas_dives.h' in prepared and 'src/overworld.c' in prepared
    for name,value in {**artifacts,**prepared}.items():
        path=Path(name);assert not path.is_absolute() and '..' not in path.parts
        assert len(value)==64 and set(value)<=set('0123456789abcdef')
        if source is not None:assert hashlib.sha256((Path(source)/path).read_bytes()).hexdigest()==value,name
    if source is not None:
        marker=json.loads((Path(source)/'.journey-atlas-stage-smoke').read_text())
        assert marker['prepared_sha256']==prepared and marker['diagnostic_role']=='five-isolated-dives'
    labels=['surface-reef','before-dive','native-dive','blocked-emerge-reef',
            'blocked-emerge-no-owner','sanctuary','depth-return','native-emerge']
    expected={theme+'-'+label+'.png' for theme,_,_ in SITES for label in labels}
    images=verify_captures(report['captures'],Path(directory),expected)
    assert len(report['cases'])==5 and [case['site'] for case in report['cases']]==[s[0] for s in SITES]
    for case,(theme,atlas,portal) in zip(report['cases'],SITES):
        surface='JourneyAtlasDiveProbe'+theme;depth='JourneyDepth'+theme;chamber='JourneySanctuary'+theme
        px,py=portal
        assert case['completed_by_controllers'] is True
        assert case['initial_fixture']==dict(surface=surface,tile=[4,6],surf=True,
                                            party_has_surf_and_dive=True,encounters_suppressed=True)
        reef=case['surface_reef_blocked']
        assert reef['map']==surface and reef['tile']==[6,6] and reef['mode']&8
        down,up=case['descent'],case['emerge']
        assert down['button']==1 and up['button']==2
        for item in (down,up):
            assert item['native_field_effect_started_by_controllers'] is True and item['frames']>0
        assert down['before']['map']==surface and down['before']['tile']==[4,6]
        entered=down['after']
        assert entered['map']==depth and entered['tile']==entered['saved_tile']==[px,py+2]
        assert entered['mode']&16 and entered['tile_elevation']==3 and entered['tile_collision']==0 and entered['atlas']==atlas
        for key,dx in [('blocked_emerge_reef',3),('blocked_emerge_no_owner',4)]:
            value=case[key]
            assert value['map']==depth and value['tile']==[px+dx,py+2] and value['mode']&16
        inside=case['sanctuary']
        assert inside['map']==chamber and inside['tile']==[14,17] and not inside['mode']&(8|16)
        assert inside['tile_elevation']==0 and inside['tile_collision']==0
        verify_native_avatar_pixels(inside['avatar_pixels'],images[inside['capture']['file']])
        returned=case['depth_return']
        assert returned['map']==depth and returned['tile']==[px,py+2] and returned['mode']&16
        end=up['after']
        assert end['map']==surface and end['tile']==end['saved_tile']==[4,6]
        assert end['mode']&8 and not end['mode']&16 and end['tile_elevation']==1 and end['atlas']==atlas
        assert any(row['before'][0]==depth and row['after'][0]==chamber for row in report['route'])
        assert any(row['before'][0]==chamber and row['after'][0]==depth for row in report['route'])
        for value in [reef,entered,inside,returned,end,case['blocked_emerge_reef'],case['blocked_emerge_no_owner']]:
            assert value['capture']['file'] in images
    assert all(c['key'] in (0,1,2,16,32,64,128) and c['frames']>0 for c in report['controls'])
    for query in report['queries']:
        name=query['function']
        assert name.startswith(('MapGridGet','MetatileBehavior_Is')) or name in {
            'PlayerGetElevation','JourneyWorldMapPosition','GetPlayerFacingDirection','IsPlayerFacingSurfableFishableWater'}
    return dict(passed=True,sites=5,captures=len(images),current_source_bound=source is not None,final_release_validated=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--source',type=Path)
    args=parser.parse_args()
    print(json.dumps(verify(json.loads(args.report.read_text()),args.report.parent,args.source),indent=2))
