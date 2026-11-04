"""Independent forest footprint, neighbor, shore and preservation checks.

This validates source data. The native control/animation proof is separate.
--staged validates the helper without changing the frozen layer166 source.
"""
import argparse
import hashlib
import json
from pathlib import Path

from arrival_coast_forest import MAPS, repair, unpack
from audit_added_forest_seams import audit
from candidate_layer import Layer
from coastal_followup_arrivals import Terrain
from prepare_arrival_coast_review import LAYER,PRIOR


def validate(source,baseline,original,output,staged=False):
    source,baseline,original,output=map(Path,(source,baseline,original,output))
    output.mkdir(parents=True,exist_ok=True)
    expected=Layer(baseline,LAYER,PRIOR);metadata=repair(expected)
    if staged:
        assert source.resolve()==baseline.resolve()
        actual=expected
    else:
        assert source.resolve()!=baseline.resolve()
        actual=Layer(baseline,LAYER,PRIOR)
        for path,blob in expected.outputs.items():
            observed=(source/path).read_bytes()
            # Another reviewed helper also aligns the One Island camera bank.
            # Compare every layout row below rather than rejecting composition
            # merely because the shared JSON has one additional scoped edit.
            if path!='data/layouts/layouts.json':
                assert observed==blob, ('Final forest bytes differ from independent staging',path)
            actual.outputs[path]=observed
    terrain=Terrain(actual)
    parsed={}
    for row in metadata['maps']:
        name=row['map'];mapping=json.loads((baseline/f'data/maps/{name}/map.json').read_bytes())
        layout=terrain.layouts[mapping['layout']];path=layout['blockdata_filepath']
        old=unpack((baseline/path).read_bytes());new=unpack(actual.outputs[path]);width=layout['width']
        allowed={tuple(c['cell']) for c in row['changed_cells']}
        observed={(i%width,i//width) for i,(a,b) in enumerate(zip(old,new)) if a!=b}
        assert observed==allowed
        if not staged:
            for path in (f'data/maps/{name}/map.json',layout['border_filepath']):
                assert (source/path).read_bytes()==(baseline/path).read_bytes(), ('Events or border changed',path)
        parsed[name]=(layout,new,mapping)
    old_doc=json.loads((baseline/'data/layouts/layouts.json').read_bytes())
    new_doc=json.loads(actual.outputs['data/layouts/layouts.json'])
    changed_layouts={r['layout'] for r in metadata['shore_aliases']['layout_assignments']}
    assert len(changed_layouts)==5
    passage_layout=None
    if not staged:
        marker=json.loads((source/('.journey-'+LAYER)).read_bytes())
        if 'limits' in marker:
            reviewed=marker['limits']['adjacent_camera_banks']
            assert reviewed['map']=='JourneySurfLink05000'
            assert reviewed['before']==['gTileset_General_Frlg','gTileset_SeviiIslands123']
            assert reviewed['after']==['gTileset_JourneySeviiSea','gTileset_SeviiIslands123']
            passage_layout=json.loads((baseline/'data/maps/JourneySurfLink05000/map.json').read_bytes())['layout']
    assert len(old_doc['layouts'])==len(new_doc['layouts'])
    for old,new in zip(old_doc['layouts'],new_doc['layouts']):
        expected_row=dict(old)
        if old['id'] in changed_layouts:
            expected_row['primary_tileset']='gTileset_JourneySeviiSea'
            if old['secondary_tileset']=='gTileset_LavenderTown':expected_row['secondary_tileset']='gTileset_JourneyKantoSeaLavenderTown'
        if old['id']==passage_layout:
            expected_row['primary_tileset']='gTileset_JourneySeviiSea'
            expected_row['secondary_tileset']='gTileset_SeviiIslands123'
        assert expected_row==new, ('Unrelated layout field changed',old['id'])
    def word(name,x,y):
        layout,values,_=parsed[name];return values[y*layout['width']+x]
    # Dense crowns/middles retain their matching complete bases, including
    # the offset neighbor on the second half of the 72-cell native coastline.
    for x in range(72):
        if x<6:assert word('Route15_Frlg',x,19)==0x0424+x%2
        else:
            assert word('Route15_Frlg',x,19)==0x041C+x%2
            target,xx=('JourneyFuchsiaInlet',x) if x<36 else ('JourneyKantoSouthSea',x-36)
            assert word(target,xx,0)==0x0424+x%2
    for x in range(22):
        assert word('Route14_Frlg',x,59)==(0x041F if x==21 else 0x041C+x%2)
        assert word('JourneyKantoSouthSea',36+x,0)==(0x0427 if x==21 else 0x0424+x%2)
    assert [word('Route14_Frlg',23,y) for y in (20,21,22)]==[0x0417,0x041F,0x0427]
    assert [word('FuchsiaCity_Frlg',x,39) for x in range(36,48)]==[0x0426+x%2 for x in range(36,48)]
    # Preserved complete shrubs, foreground fences and the standing tree's
    # entire physical footprint; no new land is given water elevation.
    for y in range(25,37):assert word('FuchsiaCity_Frlg',45,y)==0x0405
    semantic=[]
    for name,positions,kind in [('JourneyFuchsiaInlet',[(x,0) for x in range(6)],'dry'),
            ('JourneyFuchsiaInlet',[(x,1) for x in range(36)]+[(0,y) for y in range(2,10)],'water'),
            ('JourneyKantoSouthSea',[(x,1) for x in range(58)]+[(58,0),(58,1)],'water'),
            ('JourneyRoute13Coast',[(0,y) for y in range(4)],'water')]:
        mapping=parsed[name][2]
        for xy in positions:
            cell=terrain.cell(mapping['id'],xy)
            assert cell['collision']==0
            if kind=='dry':assert cell['elevation']==3 and cell['behavior']==0
            else:assert cell['elevation']==1 and cell['behavior']==21
        semantic.append(dict(map=name,kind=kind,checked_cells=len(positions)))
    # Retain both whole-width horizontal Surf lanes and the west approach;
    # these invariants can fail if a future island/reef seals the route.
    assert all(word('JourneyFuchsiaInlet',x,y)==0x112B for y in (2,3) for x in range(1,36))
    assert all(word('JourneyKantoSouthSea',x,2)==0x112B for x in range(60))
    before=audit(baseline,original,output/'census-before',False)
    after=audit(baseline,original,output/'census-after',False,actual)
    assert before['inspected_added_native_to_generated_ocean_connections']==after['inspected_added_native_to_generated_ocean_connections']
    assert len(before['inspected_added_native_to_generated_ocean_connections'])==56
    assert len(before['suspect_connections'])==5 and before['suspect_cell_count']==105
    assert not after['suspect_connections'] and after['suspect_cell_count']==0
    result=dict(passed=True,compiled_rom=False,staged=staged,kind='arrival-coast-forest-source',
        changed_paths=metadata['changed_paths'],changed_cells=metadata['changed_cell_count'],
        prepared_sha256={p:hashlib.sha256(b).hexdigest() for p,b in actual.outputs.items()},
        composed_one_island_camera_layout_checked=passage_layout is not None,
        unchanged_56_connection_census_before_105_after_zero=True,
        source_whole_objects_and_neighbor_continuation_checked=True,
        native_donor_complete_bases_and_outer_variants_checked=True,
        grass_elevation3_water_elevation1_behavior21_checked=semantic,
        events_shrubs_borders_dimensions_and_all_other_layout_fields_preserved=True,
        sea_corridor_and_small_islands_preserved=True,
        loaded_bank_pointers_sprite_pixels_animation_and_controller_proof_are_separate=True)
    (output/'forest-source.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True)
    p.add_argument('--baseline',type=Path,required=True);p.add_argument('--original',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--staged',action='store_true')
    a=p.parse_args();r=validate(a.source,a.baseline,a.original,a.output,a.staged)
    print(json.dumps({k:r[k] for k in ('passed','compiled_rom','staged','changed_cells','changed_paths')},indent=2))
