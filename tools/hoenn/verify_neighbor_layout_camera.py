"""Verify current neighbor-camera evidence without changing source or ROMs."""
import hashlib
import gzip
import json
from pathlib import Path
from PIL import Image
from validate_neighbor_layout_camera_native import CASES
from verify_sevii_route_boundaries_native import verify_pixels

def verify_reference(root,frozen):
    root=Path(root);base=root/'docs/design/neighbor-layout-camera-review'
    ref=json.loads((root/'docs/design/atlas-surf-layout/neighbor-camera-checkpoint.json').read_bytes())
    for key in ('summary','evidence_manifest'):
        row=ref[key];p=(root/row['file']).resolve();assert p.is_relative_to(base.resolve())
        assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
    seen=set()
    for line in (base/'SHA256SUMS').read_text().splitlines():
        h,name=line.split('  ',1);p=(base/name).resolve()
        assert p.is_relative_to(base.resolve()) and name not in seen;seen.add(name)
        assert hashlib.sha256(p.read_bytes()).hexdigest()==h,('Changed neighbor evidence',name)
    summary=json.loads((base/'summary.json').read_bytes())
    assert summary['ROM_sha256']==frozen['rom_sha256'] and summary['confirmed_seams_fixed']==2
    assert summary['final_release_validated'] is ref['final_release_validated'] is False
    saves=json.loads((base/'old-cache-roundtrips-v7/old-cache-roundtrips.json').read_bytes())
    assert saves['passed'] is True and len(saves['cases'])==2
    for row in saves['cases']:
        old,new,second=[row[k] for k in ('old','new','second')]
        assert new['rom_sha256']==second['rom_sha256']==frozen['rom_sha256']
        assert old['rom_sha256']=='5b5b1ace4c9b681c22540168d0d142abd30b57628d26da9264d508a82bed929c'
        for report in (old,new,second):
            assert report['passed'] is report['controllers_only'] is report['no_game_memory_writes'] is True
            assert report['backup_grid_layout_proof']['actual_ARM_APCS_struct_compiled'] is True
        a,b,c=[r['runs'][-1] for r in (old,new,second)]
        assert a['geometry_version']==6 and b['geometry_version']==c['geometry_version']==7
        for key in ('field_map','player_tile','player_surfing','player_elevation'):assert a[key]==b[key]==c[key]
        assert b['saved_after_continue_with_controllers'] is True
        assert b['saved_battery_sha256']==second['bundled_save_sha256']
        assert all(p['word']==0x1170 for p in a['continued_native_map_grid_cells'])
        assert [p['word'] for p in b['continued_native_map_grid_cells']]==[0x550,0x551,0x558,0x559]
        assert b['continued_native_map_grid_cells']==c['continued_native_map_grid_cells']
    return summary

def verify(frozen,folder):
    folder=Path(folder);path=folder/'neighbor-camera-native.json'
    if not path.exists():path=path.with_suffix('.json.gz')
    raw=path.read_bytes();r=json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)
    assert r['passed'] is r['fixed'] is True
    assert r['artifact_sha256']=={'pokeemerald.gba':frozen['rom_sha256'],'pokeemerald.elf':frozen['elf_sha256'],
        '.journey-atlas-surf-layout':frozen['marker_sha256']},'Neighbor proof belongs to another ROM'
    assert r['fixtures_declared'] is r['after_placement_controllers_and_readonly_getters_only'] is True
    assert len(r['cases'])==2
    captures={};images={}
    for row in r['captures']:
        name=row['file'];assert Path(name).name==name and name not in captures
        path=folder/name;assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
        captures[name]=row['sha256'];images[name]=Image.open(path).convert('RGB')
    for case,expected in zip(r['cases'],CASES):
        assert case['case']==expected and case['defect_reproduced'] is False
        for key in ('before','after','returned'):
            observation=case[key];shift=0 if key=='after' else expected['shift']
            assert observation['state']['map']==('Route131' if key=='after' else expected['origin'])
            assert observation['state']['tile']==(expected['target'] if key=='after' else expected['start'])
            assert observation['state']['surfing'] is True and observation['state']['elevation']==1
            cells=observation['cells'];assert len(cells)==4
            for row,(x,y,mid) in zip(cells,expected['cells']):
                assert row['tile']==[x+shift,y] and row['metatile']==mid and row['collision']==1 and row['elevation']==0
            phases=observation['animation_observations'];assert [p['frame'] for p in phases]==[0,24,48]
            for phase in phases:
                obs=phase['pixels'];assert len(obs['cells'])==4
                for row,cell in zip(obs['cells'],cells):
                    assert row['cell']==cell['tile']
                    verify_pixels(dict(obs,cells=[row]),phase['capture'],captures,images,row['cell'],cell['metatile'])
        bump=case['native_boundary_rock_bump'];assert bump and bump['before']==bump['after']
        assert case['battery']['geometry_version']==frozen.get('migration_version',7)
        p=folder/case['battery']['file'];assert p.stat().st_size==131072 and hashlib.sha256(p.read_bytes()).hexdigest()==case['battery']['sha256']
    assert all(q['function'].startswith(('MapGridGet','MetatileBehavior_Is')) or q['function']=='PlayerGetElevation' for q in r['queries'])
    return dict(cases=2,captures=len(captures),three_animation_phases=True,collision_and_native_save=True)
