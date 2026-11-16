"""Explicit native chart features backed by native terrain, C and real trips.

These four isolated chart glyphs identify water already in native maps.
They are authored classifications, not recovered affine geometry. A regional
UI bin alone never admits a feature: its exact reviewed component, native
water, compiled/source word, complete frozen inputs and controller coast
roundtrip must all agree. No graph edge is created by a chart coordinate.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from atlas_surf_regional_projection import NativeProjection,NativeCOracle,project_native
from atlas_surf_source import CARDINAL
from candidate_layer import Layer
from prepare_generated_area_review import PRIOR,LAYER

FEATURES={
    'route12':dict(point=['Route12_Frlg',8,48],pixels=[[93,39],[93,40],[94,40]],
        basis='Native Route12 coastal water beside its fixed section anchor; the isolated L glyph is inside the original regional cursor cell.'),
    'treasure':dict(point=['OneIsland_TreasureBeach_Frlg',0,0],pixels=[[135,41],[135,42]],
        basis='Existing native northern Treasure Beach water between One Island and the fixed Treasure Beach section.'),
    'pacifidlog':dict(point=['PacifidlogTown',0,8],pixels=[[93,98],[94,98],[95,98]],
        basis='The isolated native Pacifidlog water glyph; the existing town and Route131/130 sea provide the physical coast return.'),
    'bond':dict(point=['ThreeIsland_BondBridge_Frlg',48,13],pixels=[[189,50],[190,50],[191,50],[192,50]],
        basis='Existing southern Bond Bridge sea and its native land connection to Three Island; native scale is not eight local tiles per chart pixel.'),
}


def _sha(raw):return hashlib.sha256(raw).hexdigest()


def _validate_component(truth,pixels):
    points=set(map(tuple,pixels))
    if not points or not points<=truth.blue_pixels:raise ValueError('Native feature must use exactly reviewed blue chart ink')
    start=min(points);seen={start};todo=[start]
    for x,y in todo:
        for dx,dy in CARDINAL.values():
            p=x+dx,y+dy
            if p in truth.blue_pixels and p not in points:
                raise ValueError('Native feature cannot remove a piece of a larger generated route')
            if p in points and p not in seen:seen.add(p);todo.append(p)
    if seen!=points:raise ValueError('Native chart feature is not one isolated reviewed glyph')


def review(inputs,truth,travel_root,travel_source):
    travel_root,travel_source=Path(travel_root).resolve(),Path(travel_source).resolve()
    marker=json.loads((travel_source/'.journey-atlas-surf-layout').read_bytes())
    expected=Layer(travel_source,'atlas-surf-layout',PRIOR+[LAYER]).expected
    expected.update(marker['prepared_sha256'])
    for p,h in expected.items():
        if _sha((travel_source/p).read_bytes())!=h:raise ValueError(('Native travel source changed',p))
    manifest=_sha(json.dumps(sorted(expected.items()),separators=(',',':')).encode())
    binary={key:_sha((travel_source/name).read_bytes()) for key,name in [
        ('rom_sha256','pokeemerald.gba'),('elf_sha256','pokeemerald.elf'),('marker_sha256','.journey-atlas-surf-layout')]}
    if marker['parent']['source_manifest_sha256']!='d3a06e90f222f83a3e7778df52895594f6bd02719a8bc925151d7d80bfa1fed7':
        raise ValueError('Native travel uses another immutable parent')
    projection=NativeProjection(inputs);oracle=NativeCOracle(projection).compare([f['point'] for f in FEATURES.values()])
    rows=[]
    for key,definition in FEATURES.items():
        _validate_component(truth,definition['pixels']);name,x,y=definition['point']
        if not inputs.water(name,x,y):raise ValueError('Reviewed native feature point is not passable Surf water')
        projected=projection.project(name,x,y)
        if not set(map(tuple,definition['pixels']))<=set(map(tuple,projected['atlas_blue_pixels'])):
            raise ValueError('Native feature differs from original engine regional projection')
        path=travel_root/key/'native-chart-trip.json';raw=path.read_bytes();proof=json.loads(raw)
        if (proof.get('kind')!='native-chart-feature-physical-trip' or proof.get('case')!=key
                or proof.get('passed') is not True or not proof.get('after_placement_movement_controllers_only')
                or not proof.get('native_water_coast_and_dry_return') or proof.get('actual_native_water_point')!=definition['point']
                or proof.get('complete_native_and_prepared_source_manifest_sha256')!=manifest
                or proof.get('source_files_checked')!=len(expected) or not proof.get('controls') or not proof.get('route')):
            raise ValueError(('Native feature lacks complete physical travel proof',key))
        if any(proof.get(k)!=v for k,v in binary.items()):raise ValueError('Native travel proof belongs to another ROM/ELF/source')
        if proof['native_point_word']!=inputs.word(name,x,y):raise ValueError('Compiled native witness word differs from actual native terrain')
        for capture in proof['captures']:
            p=Path(capture['file'])
            if p.is_absolute() or len(p.parts)!=1 or _sha((path.parent/p).read_bytes())!=capture['sha256']:
                raise ValueError('Native travel capture missing or changed')
        row=dict(key=key,**deepcopy(definition),native_word=inputs.word(name,x,y),
            native_blockdata_sha256=_sha(inputs.read(inputs.layout(name)['blockdata_filepath'])),
            native_map_sha256=_sha(inputs.read(f'data/maps/{name}/map.json')),projection=projected,
            reference_travel_proof_sha256=_sha(raw),reference_travel_ROM_sha256=binary['rom_sha256'],
            native_scale_8_assumed=False,authored_native_feature_mapping=True,
            physical_native_point_and_coast_return_proven=True,new_candidate_native_replay_required=True)
        row['reference_native_transit_maps']=sorted({p[0] for step in proof['route']
            for p in (step['before'],step['after']) if not p[0].startswith('JourneyAtlas')})
        rows.append(row)
    inputs.assert_unchanged()
    return dict(kind='reviewed-native-isolated-chart-features/v1',features=rows,
        pixels=[p for r in rows for p in r['pixels']],oracle=oracle,
        reference_travel_source_manifest_sha256=manifest,reference_travel_binary_sha256=binary,
        classification_authored_not_recovered=True,UI_bin_alone_never_sufficient=True,
        native_maps_unmodified=True,generated_graph_edges_created=False,final_release_validated=False)


def verify_requirement(inputs,row):
    key=row.get('native_chart_feature');definition=FEATURES.get(key)
    if definition is None or row.get('point')!=definition['point'] or row.get('atlas') not in definition['pixels']:
        raise ValueError('Unknown or changed authored native chart feature')
    if (not row.get('physical_native_point_and_coast_return_proven')
            or not isinstance(row.get('reference_travel_proof_sha256'),str)
            or len(row['reference_travel_proof_sha256'])!=64):
        raise ValueError('Native chart feature lacks admitted physical proof')
    name,x,y=row['point']
    if not inputs.water(name,x,y) or inputs.word(name,x,y)!=row.get('native_word'):
        raise ValueError('Native chart feature actual terrain changed')
    if row['atlas'] not in project_native(inputs,name,x,y)['atlas_blue_pixels']:
        raise ValueError('Native chart feature projection changed')


def relocate_route12_island(inputs,truth,inventory,scenery,pixels,coasts):
    """Keep the complete nine-by-seven island/trainer beside generated water.

    Its old placement sat in the native Route12 glyph. Relocate that one
    whole stamp within its original authored coastal region, preserving the
    map name, bank, words, actor IDs and every other reservation.
    """
    from atlas_surf_scenery_pack import pack_scenery
    result=deepcopy(scenery);target='JourneyRoute12OuterSea:000';name='JourneyAtlasScene002'
    old=[r for r in result['placements'] if r['name']==name]
    if len(old)!=1 or old[0]['stamp']!=target:raise ValueError('Route12 island is no longer its one complete reviewed stamp')
    stamp=next(s for s in inventory['stamps'] if s['key']==target)
    existing=[r for r in result['reservations'] if r['name']!=name]
    existing+=deepcopy(result['dive_features']['reservations']+coasts['adapter_plan']['reservations'])
    for b in coasts['adapter_plan']['native_bounds']:
        a,d,c,e=b['global_rect'];existing.append(dict(name=b['native_map'],origin=[a,d],width=c-a,height=e-d))
    packed=pack_scenery(inputs,truth,dict(inventory,stamps=[stamp]),pixels,existing=existing,radius=12,halo=9)
    if not packed['complete'] or len(packed['reservations'])!=1:raise ValueError(packed['unplaced_stamps'])
    moved=packed['reservations'][0];moved['name']=name
    result['placements']=[deepcopy(moved) if r['name']==name else r for r in result['placements']]
    result['reservations']=[deepcopy(moved) if r['name']==name else r for r in result['reservations']]
    return result,dict(kind='complete-route12-island-off-native-chart-glyph',stamp=target,map=name,
        before_origin=old[0]['origin'],after_origin=moved['origin'],
        stamp_sha256=stamp['stamp_sha256'],whole_words_events_and_numeric_actor_ids_preserved=True,
        existing_fixed_coasts_caves_dives_and_other_scenery_preserved=True,native_ROM_validated=False)
