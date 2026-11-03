"""Keep the new west passage inside its visible reef boundary.

The completed cliff otherwise exposes a one-tile water strip to the old
northern map cut. A full native rock closes the reef row without deleting
the cliff face underneath. Its unused graphics slot avoids renumbering saved
graphics IDs and cannot be mistaken for an interactive Rock Smash boulder.
"""
import hashlib
import json
import re
import struct

from badge_story_layer import read
from integrated_ocean_seams import _header, _field

GRAPHICS = 'OBJ_EVENT_GFX_JOURNEY_COAST_BOUNDARY_ROCK'
UNUSED = 'OBJ_EVENT_GFX_UNUSED_NATU_DOLL'


def repair(layer):
    layouts = json.loads(read(layer, 'data/layouts/layouts.json'))
    by_id = {r['id']: r for r in layouts['layouts']}
    mapping = json.loads(read(layer, 'data/maps/OneIsland_Frlg/map.json'))
    layout = by_id[mapping['layout']]
    raw = read(layer, layout['blockdata_filepath'])
    words = list(struct.unpack('<'+'H'*(len(raw)//2),raw))
    assert words[7*24] == 0x1274
    assert words[7*24+1] == 0x0473
    existing = json.loads(json.dumps(mapping))
    assert not any(e['x']==0 and e['y']==7 for kind in ('object_events','warp_events','coord_events','bg_events')
                   for e in mapping.get(kind,[]))
    barrier = dict(type='object',graphics_id=GRAPHICS,x=0,y=7,elevation=1,
        movement_type='MOVEMENT_TYPE_FACE_DOWN',movement_range_x=0,movement_range_y=0,
        trainer_type='TRAINER_TYPE_NONE',trainer_sight_or_berry_tree_id='0',script='0',flag='0')
    mapping['object_events'].append(barrier)
    assert mapping['object_events'][:-1] == existing['object_events']
    assert {k:v for k,v in mapping.items() if k!='object_events'} == {k:v for k,v in existing.items() if k!='object_events'}
    layer.stage('data/maps/OneIsland_Frlg/map.json',json.dumps(mapping,indent=2)+'\n')
    # The matching collision also keeps batteries from the old map safe while
    # their newly added object templates are being restored into the camera.
    words[7*24] = 0x1674
    layer.stage(layout['blockdata_filepath'],struct.pack('<'+'H'*len(words),*words))

    constants_path='include/constants/event_objects.h'
    before=read(layer,constants_path).decode()
    anchor='    NUM_OBJ_EVENT_GFX,\n};\n'
    assert before.count(anchor)==1 and GRAPHICS not in before
    declaration='\n// Permanent scenery; reuse a verified unreferenced slot without shifting IDs.\n#define '+GRAPHICS+' '+UNUSED+'\n'
    after=before.replace(anchor,anchor+declaration)
    assert after.replace(declaration,'')==before
    layer.stage(constants_path,after)
    pointers_path='src/data/object_events/object_event_graphics_info_pointers.h'
    before_pointers=read(layer,pointers_path).decode()
    entry=re.search(r'\['+UNUSED+r'\]\s*=\s*&gObjectEventGraphicsInfo_UnusedNatuDoll,',before_pointers)
    assert entry is not None
    replacement='['+GRAPHICS+'] = &gObjectEventGraphicsInfo_BreakableRockFrlg,'
    layer.stage(pointers_path,before_pointers[:entry.start()]+replacement+before_pointers[entry.end():])
    # An unused enum member is not sufficient: prove no existing source or map
    # consumes it, and keep every pre-existing enum/dynamic graphics ID intact.
    references=[]
    for name in layer.expected:
        path=layer.source/name
        if not name.startswith(('src/','data/','include/')) or path.suffix not in ('.h','.c','.inc','.json','.s'):continue
        if name in (constants_path,pointers_path):continue
        if UNUSED.encode() in path.read_bytes():references.append(name)
    assert not references,('Scenery slot is already used',references)

    link=json.loads(read(layer,'data/maps/JourneySurfLink05000/map.json'))
    linked=by_id[link['layout']]
    linked_raw=read(layer,linked['blockdata_filepath'])
    linked_words=struct.unpack('<'+'H'*(len(linked_raw)//2),linked_raw)
    assert all(word==0x1643 for word in linked_words[:linked['width']])
    assert all((word&1023)<640 for word in linked_words)
    old_banks=[linked['primary_tileset'],linked['secondary_tileset']]
    assert old_banks == ['gTileset_General_Frlg','gTileset_SeviiIslands123']
    linked['primary_tileset']=layout['primary_tileset']
    assert linked['primary_tileset']=='gTileset_JourneySeviiSea'
    # The adjacent camera can show only the first seven columns of One/Beach
    # before crossing. All those cells use the shared primary, so retain the
    # route's native secondary graphics/palettes instead of swapping port art.
    for name in ('OneIsland_Frlg','OneIsland_TreasureBeach_Frlg'):
        other=json.loads(read(layer,f'data/maps/{name}/map.json'))
        other_layout=by_id[other['layout']]
        other_words=struct.unpack('<'+'H'*(other_layout['width']*other_layout['height']),read(layer,other_layout['blockdata_filepath']))
        visible_rows=other_layout['height'] if name=='OneIsland_Frlg' else 7
        assert all((other_words[y*other_layout['width']+x]&1023)<640
                   for y in range(visible_rows) for x in range(7))
    headers=read(layer,'src/data/tilesets/headers.h').decode()
    for old_bank,new_bank in zip(old_banks,[linked['primary_tileset'],linked['secondary_tileset']]):
        old_body,new_body=_header(headers,old_bank),_header(headers,new_bank)
        for field in ('metatiles','metatileAttributes'):
            new_body=new_body.replace(_field(new_body,field),_field(old_body,field))
        assert old_body==new_body, ('Adjacent camera changes graphics/palette/animation',old_bank,new_bank)
    layer.stage('data/layouts/layouts.json',json.dumps(layouts,indent=2)+'\n')
    return dict(kind='arrival-coast-passage-limit',map='OneIsland_Frlg',cell=[0,7],
        background_before=0x1274,background_after=0x1674,cliff_graphics_unchanged=True,
        visible_rock=barrier,local_id=len(mapping['object_events']),existing_events_unchanged=True,
        reused_unused_graphics_slot=UNUSED,unused_slot_source_references=references,
        all_existing_graphics_and_dynamic_variable_ids_unchanged=True,
        native_rock_graphics_info='gObjectEventGraphicsInfo_BreakableRockFrlg',
        new_graphics_pixels_and_palettes=False,rock_smash_and_strength_graphics_ids_not_used=True,
        aligned_reef_boundary=dict(map='JourneySurfLink05000',row=0,block=0x1643),
        adjacent_camera_banks=dict(map='JourneySurfLink05000',before=old_banks,
            after=[linked['primary_tileset'],linked['secondary_tileset']],
            original_map_used_only_primary_metatiles=True,neighbor_camera_first_seven_columns_use_only_primary=True),
        native_object_pixels_blocked_north_passage_and_both_camera_banks_required=True)
