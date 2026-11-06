"""Add a Surf circuit around Treasure Beach without cutting its old terrain.

The old twenty-four-column map ended inside the southern mountain. Preserve
every original block and event, translate them eight tiles east, and finish
the newly exposed mountain with native face, toe and corner pieces.
"""
import hashlib
import json
import struct

from badge_story_layer import read


BEACH = 'OneIsland_TreasureBeach_Frlg'
TOWN = 'OneIsland_Frlg'
LINK = 'JourneySurfLink05000'
SHIFT = 8


def repair(layer):
    layouts = json.loads(read(layer, 'data/layouts/layouts.json'))
    by_layout = {row['id']:row for row in layouts['layouts']}
    maps = {name:json.loads(read(layer, f'data/maps/{name}/map.json'))
            for name in (BEACH, TOWN, LINK)}
    layout = by_layout[maps[BEACH]['layout']]
    assert (layout['width'],layout['height']) == (24,40)
    assert layout['primary_tileset'] == 'gTileset_JourneySeviiSea'
    original = read(layer,layout['blockdata_filepath'])
    old = list(struct.unpack('<960H',original))
    assert old[-24:] == [0x0471]*24, 'Unreviewed southern mountain edge'
    water = old[13*24+3]
    assert water == 0x112B
    donors = []
    for name,x,y,expected in (
            (TOWN,23,6,0x051F),(BEACH,2,29,0x0517),
            (TOWN,18,16,0x0473),(BEACH,21,30,0x0475),
            (TOWN,18,17,0x047B),(TOWN,19,17,0x047C),
            ('OneIsland_KindleRoad_Frlg',6,138,0x047D),
            (TOWN,17,17,0x112C),(TOWN,19,18,0x1123),
            ('OneIsland_KindleRoad_Frlg',7,137,0x112A),
            ('OneIsland_KindleRoad_Frlg',7,138,0x1120),
            ('OneIsland_KindleRoad_Frlg',7,139,0x1131)):
        mapping = maps.get(name) or json.loads(read(layer,f'data/maps/{name}/map.json'))
        donor_layout = by_layout[mapping['layout']]
        assert donor_layout['primary_tileset']==layout['primary_tileset']
        raw = read(layer,donor_layout['blockdata_filepath'])
        actual = struct.unpack_from('<H',raw,2*(y*donor_layout['width']+x))[0]
        assert actual==expected, ('Unreviewed native mountain donor',name,x,y,hex(actual))
        donors.append(dict(map=name,position=[x,y],block=actual,
                           primary_tileset=layout['primary_tileset']))
    width,height = 40,48
    words = [water]*(width*height)
    for y in range(40):
        words[y*width+SHIFT:y*width+SHIFT+24] = old[y*24:(y+1)*24]

    # Native One Island southwest face and its matching southeast family.
    # Face 0x07C and corners 0x07B/0x07D are complete metatiles, with their
    # native 0x123 water toe.  The two side columns are outside the old map.
    # Their upper cap is the native blocked sea-cliff diagonal 0x11F/0x117.
    closure = []
    def place(x,y,value):
        assert not (SHIFT<=x<SHIFT+24 and y<40), ('Old terrain changed',x,y)
        words[y*width+x] = value
        closure.append(dict(position=[x,y],after=value))
    place(7,37,0x051F)
    place(32,37,0x0517)
    for y in (38,39):
        place(7,y,0x0473)
        place(6,y,0x112C)
        place(32,y,0x0475)
        place(33,y,0x112A)
    for x in range(7,33):
        place(x,40,0x047B if x==7 else 0x047D if x==32 else 0x047C)
        place(x,41,0x1123)
    place(6,40,0x112C)
    place(33,40,0x1120)
    place(33,41,0x1131)
    # Every original geology, building, dock and encounter-floor word remains.
    assert all(words[y*width+SHIFT:y*width+SHIFT+24] == old[y*24:(y+1)*24]
               for y in range(40))
    layout.update(width=width,height=height)
    layer.stage(layout['blockdata_filepath'],struct.pack('<1920H',*words))
    event_counts = {}
    for key in ('object_events','warp_events','coord_events','bg_events'):
        event_counts[key] = len(maps[BEACH].get(key,[]))
        for event in maps[BEACH].get(key,[]):
            event['x'] += SHIFT
    assert maps[BEACH]['connections'] == [dict(map='MAP_ONE_ISLAND',offset=0,direction='up')]
    maps[BEACH]['connections'] = [
        dict(map='MAP_ONE_ISLAND',offset=SHIFT,direction='up'),
        dict(map='MAP_JOURNEYSURFLINK05000',offset=-SHIFT,direction='up')]
    town_connection = [c for c in maps[TOWN]['connections']
                       if c['map']=='MAP_ONE_ISLAND_TREASURE_BEACH']
    assert len(town_connection)==1 and town_connection[0]['direction']=='down'
    assert town_connection[0]['offset']==0
    town_connection[0]['offset'] = -SHIFT
    assert not any(c['direction']=='down' for c in maps[LINK]['connections'])
    maps[LINK]['connections'].append(
        dict(map='MAP_ONE_ISLAND_TREASURE_BEACH',offset=SHIFT,direction='down'))
    link_layout = by_layout[maps[LINK]['layout']]
    assert (link_layout['width'],link_layout['height'])==(16,13)
    link_raw = read(layer,link_layout['blockdata_filepath'])
    link_words = list(struct.unpack('<208H',link_raw))
    opening=[]
    for x in range(8,16):
        at=12*16+x
        before=link_words[at]
        assert before&1023==0x243 and before&0xC00, (LINK,x,hex(before))
        link_words[at]=water
        opening.append(dict(position=[x,12],before=before,after=water))
    layer.stage(link_layout['blockdata_filepath'],struct.pack('<208H',*link_words))
    for name,mapping in maps.items():
        layer.stage(f'data/maps/{name}/map.json',json.dumps(mapping,indent=2)+'\n')
    layer.stage('data/layouts/layouts.json',json.dumps(layouts,indent=2)+'\n')
    replacements = {
        'include/journey_birth_arrivals.h':
            ('{MAP_ONE_ISLAND_TREASURE_BEACH, 10, 6, 12, 4, TRUE}',
             '{MAP_ONE_ISLAND_TREASURE_BEACH, 18, 6, 20, 4, TRUE}'),
        'include/journey_coastal_piers.h':
            ('{MAP_GROUP(MAP_ONE_ISLAND_TREASURE_BEACH), MAP_NUM(MAP_ONE_ISLAND_TREASURE_BEACH), 11, 0, 13, 3}',
             '{MAP_GROUP(MAP_ONE_ISLAND_TREASURE_BEACH), MAP_NUM(MAP_ONE_ISLAND_TREASURE_BEACH), 19, 0, 21, 3}')}
    for path,(before,after) in replacements.items():
        text=read(layer,path).decode()
        assert text.count(before)==1, ('Unreviewed absolute Treasure coordinate',path)
        layer.stage(path,text.replace(before,after))
    return dict(kind='treasure-beach-south-surf-approach',map=BEACH,
        before_dimensions=[24,40],after_dimensions=[40,48],original_terrain_offset=[8,0],
        original_blockdata_sha256=hashlib.sha256(original).hexdigest(),
        all_original_blocks_preserved=True,all_event_order_and_warp_ids_preserved=True,
        translated_event_counts=event_counts,connections={n:m['connections'] for n,m in maps.items()},
        exterior_rail_opening=opening,added_mountain_closure=closure,native_mountain_donors=donors,
        absolute_coordinate_files=list(replacements),atlas_art_unchanged=True,
        gps_reprojection_required=dict(path='src/data/journey_world_position.h',
            preserve_old_grid_at=[8,0],dimensions=[40,48]),
        native_controller_waypoints=[
            [LINK,12,11],[BEACH,4,1],[BEACH,4,43],[BEACH,35,43],
            [BEACH,35,14],[BEACH,29,14],[BEACH,29,6],[BEACH,25,6]],
        native_return_reverses_same_waypoints=True)
