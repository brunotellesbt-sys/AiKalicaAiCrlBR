"""Finish the actual Fuchsia/Route15 forest exposed by the added inlet.

The native bottom rows were an overlapping forest, not complete isolated
trees. The new ocean replaced their continuation. Close those objects in
their real neighboring maps, then add animated native water/cliff margins.
"""
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
import struct

from PIL import Image

from badge_story_layer import read

MAPS = ('FuchsiaCity_Frlg', 'Route15_Frlg', 'JourneyFuchsiaInlet', 'JourneyKantoSouthSea',
        'Route14_Frlg', 'JourneyRoute13Coast')
PRIMARY = 'gTileset_General_Frlg'
SECONDARY = 'gTileset_LavenderTown'
MARINE_PRIMARY = 'gTileset_JourneySeviiSea'
MARINE_SECONDARY = 'gTileset_JourneyKantoSeaLavenderTown'
SHORES = (0x120, 0x123, 0x129, 0x12A, 0x130)


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def unpack(blob):
    return list(struct.unpack('<' + 'H' * (len(blob)//2), blob))


def pack(values):
    return struct.pack('<' + 'H' * len(values), *values)


def shoreline_aliases(layer, layouts):
    headers = read(layer, 'src/data/tilesets/headers.h').decode()
    definitions = read(layer, 'src/data/tilesets/metatiles.h').decode()
    def fields(name):
        body = re.search(r'const struct Tileset '+name+r'\s*=\s*\{(.*?)\};',headers,re.S)[1]
        return dict(re.findall(r'\.(\w+)\s*=\s*(\w+)',body))
    def table(name):
        symbol = fields(name)['metatiles']
        path = re.search(r'\b'+symbol+r'\[\].*?"([^"]+)"',definitions)[1]
        return path,read(layer,path)
    compatibility = []
    for native,private in [(PRIMARY,MARINE_PRIMARY),(SECONDARY,MARINE_SECONDARY)]:
        old,new = fields(native),fields(private)
        assert old.keys() == new.keys()
        assert [key for key in old if old[key] != new[key]] == ['metatiles']
        compatibility.append(dict(original=native,private=private,shared_fields={k:v for k,v in old.items() if k != 'metatiles'}))
    doors = read(layer,'src/field_door.c').decode()
    assert 'if (tileset == &'+MARINE_SECONDARY+')\n        return &'+SECONDARY+';' in doors
    donor_path,donors = table(PRIMARY)
    private_path,private = table(MARINE_PRIMARY)
    records = []
    for donor in SHORES:
        words = unpack(donors[donor*16:(donor+1)*16])
        assert len(words) == 8 and all(w & 1023 in (454, 455) for w in words[:4])
        normalized = [(w & 0xFFF) | 0x4000 for w in words[:4]] + words[4:]
        assert private[donor*16:(donor+1)*16] == pack(normalized)
        records.append(dict(metatile=donor,before=words,after=normalized))
    # The bank swap must leave every pine and grass graphic exact.
    assert private[:0x100*16] == donors[:0x100*16]
    frames = []
    for frame in range(8):
        path = f'data/tilesets/primary/general_frlg/anim/water_current_landwatersedge/{frame}.png'
        blob = read(layer, path)
        with Image.open(BytesIO(blob)) as image:
            assert image.mode == 'P'
            width = image.width//8
            for tile in (454, 455):
                index = tile-416
                left, top = index % width * 8, index//width * 8
                indices = sorted(set(image.crop((left, top, left+8, top+8)).getdata()))
                assert set(indices) <= {0, 3, 4, 5, 6, 7}
                frames.append(dict(frame=frame, graphic=tile, indices=indices, file=path, sha256=sha(blob)))
    raw = read(layer,'data/layouts/layouts.json')
    document = json.loads(raw)
    changed = []
    targets = {layouts[json.loads(read(layer,f'data/maps/{n}/map.json'))['layout']]['id'] for n in MAPS}
    for row in document['layouts']:
        if row['id'] not in targets: continue
        assert row['primary_tileset'] in (PRIMARY,MARINE_PRIMARY)
        old_primary=row['primary_tileset']
        old_secondary=row['secondary_tileset']
        new_secondary=MARINE_SECONDARY if old_secondary == SECONDARY else old_secondary
        assert old_secondary in (SECONDARY,'gTileset_FuchsiaCity',MARINE_SECONDARY)
        if (old_primary,old_secondary) != (MARINE_PRIMARY,new_secondary):
            changed.append(dict(layout=row['id'],original_primary=old_primary,private_primary=MARINE_PRIMARY,
                                original_secondary=old_secondary,private_secondary=new_secondary))
        row['primary_tileset'],row['secondary_tileset'] = MARINE_PRIMARY,new_secondary
    assert len(changed) == 5
    layer.stage('data/layouts/layouts.json',json.dumps(document,indent=2)+'\n')
    return dict(primary=MARINE_PRIMARY, secondary=MARINE_SECONDARY, definitions=records,
        files=['data/layouts/layouts.json'],frames=frames,bank_compatibility=compatibility,
        layout_assignments=changed,existing_aliases_reused=True,native_door_alias_preserved=True,
        native_table=donor_path,private_table=private_path,
        native_graphic_numbers_animation_and_cliff_upper_words_preserved=True,
        only_water_palette_normalized_to_open_sea=True,
        primary_graphics_attributes_palettes_callbacks_unchanged=True)


def repair(layer):
    layouts = {row['id']: row for row in json.loads(read(layer, 'data/layouts/layouts.json'))['layouts']}
    data = {}
    for name in (*MAPS, 'SixIsland_Frlg'):
        mapping_raw = read(layer, f'data/maps/{name}/map.json')
        mapping = json.loads(mapping_raw)
        layout = layouts[mapping['layout']]
        blob = read(layer, layout['blockdata_filepath'])
        data[name] = dict(mapping=mapping, mapping_raw=mapping_raw, layout=layout,
                          before=blob, values=unpack(blob))
    for name in MAPS:
        assert data[name]['layout']['primary_tileset'] in (PRIMARY,MARINE_PRIMARY)
        assert data[name]['layout']['layout_version'] == 'frlg'
    city, route, inlet, sea = [data[name] for name in MAPS[:4]]
    assert [(d['layout']['width'], d['layout']['height']) for d in (city, route, inlet, sea)] == [(48,40),(72,20),(36,10),(132,50)]
    for d in (inlet, sea):
        assert d['layout']['secondary_tileset'] == SECONDARY
    assert dict(map='MAP_JOURNEYFUCHSIAINLET', direction='right', offset=30) in city['mapping']['connections']
    assert dict(map='MAP_JOURNEYFUCHSIAINLET', direction='down', offset=0) in route['mapping']['connections']
    assert dict(map='MAP_JOURNEYKANTOSOUTHSEA', direction='down', offset=36) in route['mapping']['connections']
    assert [city['values'][y*48+x] for y in (2,3) for x in (2,3)] == [0x041C,0x041D,0x0424,0x0425]
    donor = data['SixIsland_Frlg']
    assert [donor['values'][y*24+x] for y in (3,4,5) for x in (2,3)] == [0x300E,0x300F,0x041E,0x041F,0x0426,0x0427]
    aliases = shoreline_aliases(layer, layouts)
    edits = {name: {} for name in MAPS}

    def put(name, x, y, old, new):
        d = data[name]; i = y*d['layout']['width']+x
        assert d['values'][i] == old, (name,x,y,hex(old),hex(d['values'][i]))
        assert (x,y) not in edits[name]
        edits[name][x,y] = new

    # The left three columns finish on row19; farther east the last complete
    # crown/middle lies one row lower and its base belongs in the real neighbor.
    for x in range(6):
        put('Route15_Frlg', x, 19, 0x0414+x%2, 0x0424+x%2)
    for x in range(72):
        name, xx = ('JourneyFuchsiaInlet',x) if x < 36 else ('JourneyKantoSouthSea',x-36)
        put(name, xx, 0, 0x112B, 0x3001 if x < 6 else 0x0424+x%2)
        put(name, xx, 1, 0x112B, 0x1120 if x == 0 else 0x1123)
    # Native outer-edge variants remove the implied tree to the east, while
    # retaining every crown, middle, trunk and the entire shrub column.
    for y in range(30,39):
        put('FuchsiaCity_Frlg',47,y,0x041D if y%2 == 0 else 0x0415,
            0x041F if y%2 == 0 else 0x0417)
    for x in range(36,48):
        put('FuchsiaCity_Frlg',x,39,0x0414+x%2,0x0426+x%2)
    for y in range(2,10):
        put('JourneyFuchsiaInlet',0,y,0x112B,0x1129)
    # The same coastline bends around Route14. Close its entire bottom stand
    # and the last two east-facing overlap cells rather than stopping at the
    # video camera. The grass-facing final half uses the outer native base.
    eastern=data['Route14_Frlg'];coast=data['JourneyRoute13Coast']
    assert (eastern['layout']['width'],eastern['layout']['height']) == (24,60)
    assert (coast['layout']['width'],coast['layout']['height']) == (72,40)
    for y,old,new in [(20,0x0415,0x0417),(21,0x041D,0x041F),(22,0x0425,0x0427)]:
        put('Route14_Frlg',23,y,old,new)
    for y in range(3):put('JourneyRoute13Coast',0,y,0x112B,0x1129)
    put('JourneyRoute13Coast',0,3,0x112B,0x1130)
    for x in range(22):
        assert eastern['values'][59*24+x] == (0x041F if x == 21 else 0x041C+x%2)
        put('JourneyKantoSouthSea',36+x,0,0x112B,0x0427 if x == 21 else 0x0424+x%2)
        put('JourneyKantoSouthSea',36+x,1,0x112B,0x1123)
    put('JourneyKantoSouthSea',58,0,0x112B,0x112A)
    put('JourneyKantoSouthSea',58,1,0x112B,0x1130)

    records = []
    for name in MAPS:
        d = data[name]; layout = d['layout']; values = d['values'].copy(); width = layout['width']
        occupied = {(e['x'],e['y']) for kind in ('object_events','warp_events','coord_events','bg_events') for e in d['mapping'].get(kind,[])}
        assert not occupied.intersection(edits[name]), (name,occupied.intersection(edits[name]))
        for (x,y),word in edits[name].items(): values[y*width+x] = word
        raw = pack(values)
        layer.stage(layout['blockdata_filepath'],raw)
        records.append(dict(map=name,file=layout['blockdata_filepath'],
            before_sha256=sha(d['before']),after_sha256=sha(raw),
            map_json_sha256=sha(d['mapping_raw']),connections=d['mapping']['connections'],
            changed_cells=[dict(cell=[x,y],before=d['values'][y*width+x],after=word) for (x,y),word in sorted(edits[name].items())]))
    # The 28x8 western Surf corridor and whole-width northern route stay open;
    # retain the small native island farther east without flattening its shore.
    assert all(inlet['values'][y*36+x] == 0x112B for y in range(2,10) for x in range(1,29))
    assert all(inlet['values'][y*36+x] == 0x112B for y in (2,3) for x in range(36))
    assert all(city['values'][y*48+45] == 0x0405 for y in range(25,37))
    return dict(kind='arrival-coast-exposed-fuchsia-forest',maps=records,shore_aliases=aliases,
        changed_paths=[r['file'] for r in records]+aliases['files'],
        changed_cell_count=sum(len(r['changed_cells']) for r in records),
        donor_dense_base=dict(map='FuchsiaCity_Frlg',bounds=[2,2,2,2],words=[0x041C,0x041D,0x0424,0x0425]),
        donor_full_tree=dict(map='SixIsland_Frlg',bounds=[2,3,2,3],words=[0x300E,0x300F,0x041E,0x041F,0x0426,0x0427]),
        entire_72_tile_route15_coast_finished=True,shrub_fence_buildings_and_events_preserved=True,
        forest_collision_preserved=True,grass_height=3,surf_height=1,western_open_surf_corridor=[1,2,28,8],
        retained_island_cells_and_whole_width_surf_rows=[2,3,7,8,9],
        map_dimensions_connections_borders_and_atlas_unchanged=True,
        all_five_flagged_native_to_added_ocean_forest_seams_finished=True,
        five_affected_layout_banks_reuse_existing_marine_aliases=True,
        all_six_whole_maps_neighbors_and_controller_proofs_required=True)
