"""Independently check exported diagnostic timing, pixels and artifact bindings.

The three-map diagnostic cannot certify final-network geography/performance.
With --source, also compare the actual frozen ROM, ELF, marker and inputs.
"""
import argparse
import hashlib
import json
from pathlib import Path

from verify_sevii_integrated_piers_update import verify_captures, verify_native_avatar_pixels
from verify_sevii_route_boundaries_native import verify_pixels


CASES = {'east-out-of-four-tile-map':(16,[1,0]),
         'south-across-second-seam':(128,[0,1]),
         'north-return':(64,[0,-1]),
         'west-return-to-four-tile-map':(32,[-1,0])}


def verify(report, directory, source=None):
    directory=Path(directory)
    assert report['kind']=='atlas-physical-three-map-native-diagnostic'
    for key in ('passed','diagnostic_build','after_placement_movement_controllers_only',
                'initial_party_progress_placement_surf_and_encounter_suppression_are_fixtures',
                'private_read_only_query_trampoline_declared','frozen_source_marker_rom_and_elf_unchanged'):
        assert report[key] is True,key
    for key in ('final_release_validated','real_atlas_route_classification_proven','full_network_performance_proven'):
        assert report[key] is False,key
    artifacts=report['artifact_sha256']
    assert set(artifacts)=={'pokeemerald.gba','pokeemerald.elf','.journey-atlas-stage-smoke'}
    inputs=report['prepared_source_sha256']
    assert inputs and 'src/fieldmap.c' in inputs and 'src/data/journey_atlas_physical.h' in inputs
    for name,value in {**inputs,**artifacts}.items():
        path=Path(name)
        assert not path.is_absolute() and '..' not in path.parts
        assert len(value)==64 and set(value)<=set('0123456789abcdef')
        if source is not None:
            assert hashlib.sha256((Path(source)/path).read_bytes()).hexdigest()==value,name
    if source is not None:
        marker=json.loads((Path(source)/'.journey-atlas-stage-smoke').read_text())
        assert marker['prepared_sha256']==inputs
        assert marker['diagnostic_only'] is True and marker['release_eligible'] is False
    expected={name+'.png' for name in CASES}|{'reef-blocks-surf.png','diagonal-real-terrain.png'}
    images=verify_captures(report['captures'],directory,expected)
    captures={row['file']:row['sha256'] for row in report['captures']}
    rows=report['seams']
    assert len(rows)==4 and {row['case'] for row in rows}==set(CASES)
    for row in rows:
        key,delta=CASES[row['case']]
        assert row['key']==key and row['global_tile_delta']==delta
        assert row['no_native_queries_during_timing'] is True
        assert row['end_frame']-row['start_frame']==row['total_frames']
        assert not any(row['start_frame']<=q['frame']<row['end_frame'] for q in report['queries'])
        assert 1<=row['map_published_frame']<=row['consistent_coordinates_frame']<=row['total_frames']<=120
        assert row['inconsistent_coordinate_frames']==row['consistent_coordinates_frame']-row['map_published_frame']<=30
        samples=row['frame_samples']
        assert [s['frame'] for s in samples]==list(range(1,row['total_frames']+1))
        before,after=row['before'],row['after']
        assert before['map']!=after['map'] and after['tile']==after['saved_tile']
        assert all(s['idle'] and s['object_active'] and s['surfing'] and s['map']==after['map']
                   and s['tile']==s['saved_tile']==after['tile'] for s in samples[-20:])
        first=next(s['frame'] for s in samples if s['map']!=before['map'])
        consistent=next(s['frame'] for s in samples if s['map']==after['map'] and s['tile']==s['saved_tile']==after['tile'])
        assert first==row['map_published_frame'] and consistent==row['consistent_coordinates_frame']
        assert row['capture']['file']==row['case']+'.png'
        assert captures[row['capture']['file']]==row['capture']['sha256']
    assert all(c['key'] in (0,1,2,16,32,64,128) and c['frames']>0 for c in report['controls'])
    observations={row['case']:row for row in report['observations']}
    assert len(observations)==4
    terrain=observations['west-strip-from-narrow-source']['terrain']
    assert terrain==dict(cell=[-1,3],loaded_word=0x112B,height=1,collision=0)
    north=observations['north-eight-tiles']
    start,end=north['start'],north['end']
    assert end['global_tile']==[start['global_tile'][0],start['global_tile'][1]-8]
    assert end['atlas']==[start['atlas'][0],start['atlas'][1]-1]
    moves=[row for row in report['route'] if row['phase']=='north-eight-tiles']
    assert len(moves)==8
    for row in moves:
        assert row['global_after']==[row['global_before'][0],row['global_before'][1]-1]
    reef=observations['reef-blocks-surf']
    assert reef['terrain']==dict(cell=[12,2],loaded_word=0x1643,height=1,collision=1)
    assert reef['player']['surfing'] is True and reef['player']['tile']==[13,2]
    verify_native_avatar_pixels(reef['player']['native_avatar_pixels'],images[reef['capture']['file']])
    diagonal=observations['diagonal-real-terrain-without-direct-connection']
    assert diagonal['terrain']==dict(cell=[4,8],loaded_word=0x1643,height=1,collision=1)
    assert diagonal['border_invalid'] is True
    verify_pixels(diagonal['pixels'],diagonal['capture'],captures,images,[4,8],0x243)
    return dict(kind='verified-atlas-physical-native-diagnostic',passed=True,
                current_source_bound=source is not None,seams=4,captures=len(images),final_release_validated=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--source',type=Path)
    args=parser.parse_args()
    print(json.dumps(verify(json.loads(args.report.read_text()),args.report.parent,args.source),indent=2))
