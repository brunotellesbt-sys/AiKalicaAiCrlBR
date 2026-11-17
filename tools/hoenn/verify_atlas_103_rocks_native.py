"""Recheck exported native pixels, collision records and the exact frozen ROM.

This checks the recorded local cases; it does not certify a campaign or any
of the release obligations outside the General boulder repair.
"""
import gzip
import hashlib
import json
from pathlib import Path

from PIL import Image
from atlas_surf_rock_repairs import PLAN
from verify_sevii_route_boundaries_native import verify_pixels


def verify(frozen,directory):
    directory=Path(directory)
    report=json.loads(gzip.decompress((directory/'rocks103-native.json.gz').read_bytes()))
    assert report['kind']=='103-General-rock-fragments-native' and report['passed'] is True
    assert report['final_release_validated'] is False
    assert report['artifact_sha256']=={
        'pokeemerald.gba':frozen['rom_sha256'],'pokeemerald.elf':frozen['elf_sha256'],
        '.journey-atlas-surf-layout':frozen['marker_sha256']},'Native proof belongs to another ROM'
    assert report['prepared_source_sha256']==frozen['prepared_sha256']
    assert report['source_inputs_checked']==frozen['complete_source_files_checked']
    for key in ('all_four_quadrants_BG_VRAM_palette_and_PNG_samples_checked',
                'compiled_metatile_words_match_actual_source','old_collision_elevation_preserved_in_native_engine',
                'fixture_per_case_party_progress_initial_position_and_movement_mode',
                'after_placement_controllers_and_read_only_native_getters_only','native_getter_trampoline_declared'):
        assert report[key] is True,key
    assert report['original_reviewed_cells']==103 and report['additional_runtime_fragment_cells']==6
    assert len(report['cases'])==54 and report['checked_task_cells']==109
    plan=json.loads(PLAN.read_bytes());expected={(r['map'],*r['tile']):r for r in plan['repairs']+plan['scripted_alternate_repairs']}
    assert len(expected)==109
    captures={};images={}
    for row in report['captures']:
        name=row['file'];assert Path(name).name==name and name not in captures
        path=directory/name;assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
        captures[name]=row['sha256'];images[name]=Image.open(path).convert('RGB')
    seen=set();witnesses=0;bumps=0
    for case in report['cases']:
        name=case['map'];loaded=case['loaded_cells'];cells={tuple(r['tile']):r for r in loaded}
        assert len(cells)==len(loaded)
        for point,row in cells.items():
            if row['preserved_object_witness']:
                assert name=='Route131' and point in ((2,8),(3,8));witnesses+=1;continue
            key=(name,*point);assert key in expected and key not in seen;seen.add(key);repair=expected[key]
            if name=='Route131' and point in ((2,7),(3,7)):
                assert row['metatile']==(0x15a if point[0]==2 else 0x15b)
                assert row['primary_layout_after']==repair['after'] and row['resolution'].startswith('complete native boulder preserved')
            else:assert row['metatile']==repair['after']&1023
            assert row['collision']==(repair['before']>>10)&3 and row['elevation']==repair['before']>>12
        phases=case['animation_observations'];assert [r['frame'] for r in phases]==[0,24,48]
        for phase in phases:
            observation=phase['pixels'];assert {tuple(r['cell']) for r in observation['cells']}==set(cells)
            for row in observation['cells']:
                point=tuple(row['cell']);assert row['native_metatile']==cells[point]['metatile']
                verify_pixels(dict(observation,cells=[row]),phase['capture'],captures,images,row['cell'],row['native_metatile'])
        bump=case['native_collision_bump']
        if bump:
            assert bump['controller_frames']>=60
            for key in ('map','tile','mode','elevation'):assert bump['before'][key]==bump['after'][key]
            assert captures[bump['capture']['file']]==bump['capture']['sha256'];bumps+=1
    assert seen==set(expected) and witnesses==report['preserved_native_variant_boulder_witness_cells']==2
    assert bumps>0
    assert all(r['function'].startswith(('MapGridGet','MetatileBehavior_Is')) or r['function'] in {
        'GetPlayerFacingDirection','GetPlayerFacingMovementDirection','PlayerGetElevation','IsPlayerFacingSurfableFishableWater'} for r in report['queries'])
    return dict(original_cells=103,additional_cells=6,cases=54,captures=len(captures),native_collision_cases=bumps,
                native_pixels_and_artifact_identity=True,final_release_validated=False)
