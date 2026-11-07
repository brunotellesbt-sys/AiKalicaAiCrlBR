"""Join Treasure Beach's west canal to the existing southern atlas sea.

Append one map and GPS grid. Existing maps, IDs, GPS cells and atlas artwork
keep their positions; only the two previously closed reef mouths open.
"""
import copy
import hashlib
import json
import re
import struct

from badge_story_layer import read
from prepare_complete_marine_atlas import point_line

BEACH = 'OneIsland_TreasureBeach_Frlg'
SEA = 'JourneyKantoSeviiTransit'
PASSAGE = 'JourneyOneSouthPassage'
WIDTH, HEIGHT, SEA_OFFSET = 8, 32, 62
WATER, REEF = 0x112B, 0x1643


def projection(top, bottom):
    """Keep both old seam rows exact and follow the drawn x=135 meridian."""
    assert top == [136 | (40 << 8)]*WIDTH
    assert bottom == [x | (53 << 8) for x in (135, 135, 135, 136, 136, 137, 138, 138)]
    cells = []
    for y in range(HEIGHT):
        gy = min(53, 40+round(13*y/27))
        for x in range(WIDTH):
            gx = 136 if gy == 40 else 135
            if y >= 27:
                gx = 135+round(((bottom[x]&255)-135)*(y-27)/4)
            cells.append(gx | (gy << 8))
    assert cells[:WIDTH] == top and cells[-WIDTH:] == bottom
    return cells


def repair(layer):
    layouts_path = 'data/layouts/layouts.json'
    layout_data = json.loads(read(layer, layouts_path))
    layouts = {row['id']: row for row in layout_data['layouts']}
    mappings = {n: json.loads(read(layer, f'data/maps/{n}/map.json')) for n in (BEACH, SEA)}
    assert not (layer.source/f'data/maps/{PASSAGE}/map.json').exists()
    beach, sea = (layouts[mappings[n]['layout']] for n in (BEACH, SEA))
    assert (beach['width'], beach['height']) == (40, 48)
    assert (sea['width'], sea['height']) == (112, 24)
    assert not any(c['direction'] == 'down' for c in mappings[BEACH]['connections'])
    assert not any(c['direction'] == 'up' for c in mappings[SEA]['connections'])

    mapping = copy.deepcopy(mappings[SEA])
    mapping.update(id='MAP_'+PASSAGE.upper(), name=PASSAGE, layout='LAYOUT_'+PASSAGE.upper(),
                   region_map_section='MAPSEC_ONE_ISLAND', object_events=[], warp_events=[],
                   coord_events=[], bg_events=[], connections=[
                       dict(map=mappings[BEACH]['id'], direction='up', offset=0),
                       dict(map=mappings[SEA]['id'], direction='down', offset=-SEA_OFFSET)])
    # A dedicated factual point label uses One Island's existing section. Adding
    # an enum before MAPSEC_NONE would change that old, save-visible sentinel.
    mappings[BEACH]['connections'].append(dict(map=mapping['id'], direction='down', offset=0))
    mappings[SEA]['connections'].append(dict(map=mapping['id'], direction='up', offset=SEA_OFFSET))
    layout = copy.deepcopy(beach)
    layout.update(id=mapping['layout'], name=PASSAGE+'_Layout', width=WIDTH, height=HEIGHT,
                  blockdata_filepath=f'data/layouts/{PASSAGE}/map.bin',
                  border_filepath=f'data/layouts/{PASSAGE}/border.bin', border_width=2, border_height=2)
    layout_data['layouts'].append(layout)
    groups_path = 'data/maps/map_groups.json'
    groups = json.loads(read(layer, groups_path))
    group = next(g for g in groups['group_order'] if SEA in groups[g])
    old_group_size = len(groups[group])
    assert old_group_size < 255
    groups[group].append(PASSAGE)

    changed = []
    grids = {}
    for n in (BEACH, SEA):
        l = layouts[mappings[n]['layout']]
        raw = read(layer, l['blockdata_filepath'])
        grids[n] = list(struct.unpack('<'+'H'*(len(raw)//2), raw))
    # Transit inherited a two-row reef apron. Open its full depth, otherwise
    # the visible seam would lead directly into the second blocked row.
    for n, y, xs in ((BEACH, 47, range(1, 7)), (SEA, 0, range(63, 69)),
                     (SEA, 1, range(63, 69))):
        width = layouts[mappings[n]['layout']]['width']
        for x in xs:
            at = y*width+x
            assert grids[n][at] == REEF, ('Old mouth is not a complete reef', n, x, y)
            changed.append(dict(map=n, cell=[x, y], before=REEF, after=WATER))
            grids[n][at] = WATER

    # The prior closure used each diagonal on the opposite side, leaving a
    # floating right-facing triangle on the west. Authenticate the complete
    # native cap/side/foam families, retaining all original mountain cells.
    donors = []
    def donor(n, x, y, expected):
        m = json.loads(read(layer, f'data/maps/{n}/map.json'))
        l = layouts[m['layout']]
        assert l['primary_tileset'] == beach['primary_tileset']
        raw = read(layer, l['blockdata_filepath'])
        word = struct.unpack_from('<H', raw, 2*(y*l['width']+x))[0]
        assert word == expected, ('Native cliff donor changed', n, x, y, word, expected)
        donors.append(dict(map=n, cell=[x, y], block=word))
        return word
    donor('SevenIsland_TrainerTower_Frlg', 39, 36, 0x0517)
    donor('SevenIsland_TrainerTower_Frlg', 39, 37, 0x0473)
    donor('SevenIsland_TrainerTower_Frlg', 38, 37, 0x0128)
    donor('SevenIsland_TrainerTower_Frlg', 38, 38, 0x012C)
    donor('OneIsland_KindleRoad_Frlg', 6, 135, 0x051F)
    donor('OneIsland_KindleRoad_Frlg', 6, 136, 0x0475)
    donor('OneIsland_KindleRoad_Frlg', 7, 136, 0x1129)
    donor('OneIsland_KindleRoad_Frlg', 7, 137, 0x112A)
    cliff = []
    for x, y, before, after in ((7, 37, 0x051F, 0x0517), (6, 38, 0x112C, 0x1128),
                                 (32, 37, 0x0517, 0x051F), (33, 38, 0x112A, 0x1129)):
        assert grids[BEACH][y*40+x] == before
        assert before & 0xFC00 == after & 0xFC00
        grids[BEACH][y*40+x] = after
        cliff.append(dict(cell=[x, y], before=before, after=after))
    for n, words in grids.items():
        l = layouts[mappings[n]['layout']]
        layer.stage(l['blockdata_filepath'], struct.pack('<'+'H'*len(words), *words))
    words = [REEF if x in (0, WIDTH-1) else WATER for y in range(HEIGHT) for x in range(WIDTH)]
    layer.stage(layout['blockdata_filepath'], struct.pack('<'+'H'*len(words), *words))
    layer.stage(layout['border_filepath'], struct.pack('<4H', *([REEF]*4)))
    layer.stage(layouts_path, json.dumps(layout_data, indent=2)+'\n')
    layer.stage(groups_path, json.dumps(groups, indent=2)+'\n')
    for n, m in {**mappings, PASSAGE: mapping}.items():
        layer.stage(f'data/maps/{n}/map.json', json.dumps(m, indent=2)+'\n')
    layer.stage(f'data/maps/{PASSAGE}/scripts.inc', PASSAGE+'_MapScripts::\n\t.byte 0\n')
    scripts_path = 'data/event_scripts.s'
    scripts = read(layer, scripts_path).decode()
    layer.stage(scripts_path, scripts+f'\n\t.include "data/maps/{PASSAGE}/scripts.inc"\n')

    gps_path = 'src/data/journey_world_position.h'
    header = read(layer, gps_path).decode()
    array = re.search(r'sWorldNavigationPixels\[\] = \{([^}]+)', header)
    values = list(map(int, array[1].split(',')))
    descriptors = {ident: (int(first), int(w), int(h)) for first, ident, w, h in re.findall(
        r'\{(\d+), \(MAP_GROUP\((\w+)\)<<8\)\|MAP_NUM\(\2\), (\d+), (\d+)\}', header)}
    first, width, height = descriptors[mappings[BEACH]['id']]
    assert (width, height) == (40, 48)
    top = values[first+47*40:first+47*40+WIDTH]
    first, width, height = descriptors[mappings[SEA]['id']]
    assert (width, height) == (112, 24)
    bottom = values[first+SEA_OFFSET:first+SEA_OFFSET+WIDTH]
    extra = projection(top, bottom)
    before_count = len(values)
    header = header[:array.end(1)]+','+','.join(map(str, extra))+header[array.end(1):]
    end = header.index('};', header.index('sWorldTileGrids'))
    line = '{'+f'{before_count}, (MAP_GROUP({mapping["id"]})<<8)|MAP_NUM({mapping["id"]}), {WIDTH}, {HEIGHT}'+'},\n'
    header = header[:end]+line+header[end:]
    layer.stage(gps_path, header)
    point_path = 'src/data/journey_world_map.h'
    points = read(layer, point_path).decode()
    end = points.index('};', points.index('sWorldPoints'))
    points = points[:end]+point_line(mapping, [135, 47], 'ONE SOUTH PASSAGE')+points[end:]
    layer.stage(point_path, points)

    wild_path = 'src/data/wild_encounters.json'
    wild = json.loads(read(layer, wild_path))
    families = [(g, row) for g in wild['wild_encounter_groups'] for row in g['encounters']
                if row.get('map') == mappings[SEA]['id']]
    assert len(families) == 1
    family, encounter = families[0]
    assert set(encounter) == {'map', 'base_label', 'water_mons', 'fishing_mons'}
    addition = copy.deepcopy(encounter)
    addition.update(map=mapping['id'], base_label='gCoastalEcology_'+PASSAGE)
    family['encounters'].append(addition)
    layer.stage(wild_path, json.dumps(wild, indent=2)+'\n')
    return dict(kind='one-south-surf-link', map=PASSAGE, dimensions=[WIDTH, HEIGHT],
                joins=[BEACH, SEA], sea_offset=SEA_OFFSET, existing_mouth_changes=changed,
                cliff_changes=cliff, authenticated_native_cliff_donors=donors,
                new_map_group=group, appended_map_number=old_group_size,
                gps_values_appended=len(extra), old_gps_values=len(values),
                gps_appended_sha256=hashlib.sha256(struct.pack('<'+'H'*len(extra), *extra)).hexdigest(),
                old_map_ids_layouts_events_gps_and_atlas_art_preserved=True,
                region_section='MAPSEC_ONE_ISLAND', world_label='ONE SOUTH PASSAGE',
                encounter_family_from=SEA, normal_water_and_fishing_encounters_preserved=True,
                test_mode_global_encounter_suppression_unchanged=True)
