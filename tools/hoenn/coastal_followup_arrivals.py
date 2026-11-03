"""Retarget initial boat arrivals after harbor exteriors became sea routes.

Only the arrival table changes. Both the dynamic truck destination and the
Seagallop intro already read this table; the temporary mother stands one tile
north of a boat landing. Keep both actors on reviewed, unoccupied dry ground.
"""
import hashlib
import json
from pathlib import Path
import re
import struct

from badge_story_layer import read


PATH = 'include/journey_birth_arrivals.h'
# index: (old map, new map, old landing, new landing). Vehicle coordinates and
# boat flags stay unchanged; the seven retired exterior maps are never reused.
REPAIRS = {
    10: ('MAP_ONE_ISLAND_HARBOR', 'MAP_ONE_ISLAND_TREASURE_BEACH', (7, 5), (12, 4)),
    11: ('MAP_TWO_ISLAND_HARBOR', 'MAP_TWO_ISLAND', (7, 5), (10, 12)),
    12: ('MAP_THREE_ISLAND_HARBOR', 'MAP_THREE_ISLAND_PORT', (7, 5), (12, 17)),
    13: ('MAP_FOUR_ISLAND_HARBOR', 'MAP_FOUR_ISLAND', (7, 5), (10, 32)),
    14: ('MAP_FIVE_ISLAND_HARBOR', 'MAP_FIVE_ISLAND', (7, 5), (12, 17)),
    15: ('MAP_SIX_ISLAND_HARBOR', 'MAP_SIX_ISLAND', (7, 5), (11, 27)),
    16: ('MAP_SEVEN_ISLAND_HARBOR', 'MAP_SEVEN_ISLAND', (7, 5), (15, 17)),
    21: ('MAP_DEWFORD_TOWN', 'MAP_DEWFORD_TOWN', (14, 11), (14, 12)),
    29: ('MAP_MOSSDEEP_CITY', 'MAP_MOSSDEEP_CITY', (4, 32), (6, 25)),
    31: ('MAP_PACIFIDLOG_TOWN', 'MAP_PACIFIDLOG_TOWN', (10, 27), (8, 24)),
}
ROW = re.compile(r'^\{(MAP_\w+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(TRUE|FALSE)\}', re.M)


def rows(text):
    result = []
    for index, match in enumerate(ROW.finditer(text), 1):
        map_id, tx, ty, lx, ly, boat = match.groups()
        result.append(dict(index=index, map_id=map_id, truck=[int(tx), int(ty)],
            landing=[int(lx), int(ly)], boat=boat == 'TRUE', text=match[0]))
    assert len(result) == 31, 'Starting-city table changed; review every destination'
    return result


class Terrain:
    """Read the actual layout bank attributes, including FRLG's 640 split."""
    def __init__(self, layer):
        self.layer = layer
        self.layouts = {r['id']: r for r in json.loads(read(layer, 'data/layouts/layouts.json'))['layouts']}
        self.maps = {}
        for path in (layer.source/'data/maps').glob('*/map.json'):
            mapping = json.loads(read(layer, path.relative_to(layer.source).as_posix()))
            self.maps[mapping['id']] = (path.parent.name, mapping)
        self.headers = read(layer, 'src/data/tilesets/headers.h').decode()
        self.definitions = read(layer, 'src/data/tilesets/metatiles.h').decode()
        self.cache = {}

    def cell(self, map_id, xy):
        name, mapping = self.maps[map_id]
        layout = self.layouts[mapping['layout']]
        x, y = xy
        assert 0 <= x < layout['width'] and 0 <= y < layout['height'], (map_id, xy)
        path = layout['blockdata_filepath']
        raw = read(self.layer, path)
        block = struct.unpack_from('<H', raw, (y*layout['width']+x)*2)[0]
        frlg = layout['layout_version'] == 'frlg'
        cutoff, size, mask = (640, 4, 511) if frlg else (512, 2, 255)
        mid = block & 1023
        bank = layout['primary_tileset' if mid < cutoff else 'secondary_tileset']
        if bank not in self.cache:
            body = re.search(r'const struct Tileset '+re.escape(bank)+r'\s*=\s*\{(.*?)\};', self.headers, re.S)[1]
            symbol = re.search(r'\.metatileAttributes\s*=\s*(\w+)', body)[1]
            attr_path = re.search(r'\b'+re.escape(symbol)+r'\[\].*?"([^"]+)"', self.definitions)[1]
            self.cache[bank] = read(self.layer, attr_path)
        index = mid if mid < cutoff else mid-cutoff
        behavior = int.from_bytes(self.cache[bank][index*size:(index+1)*size], 'little') & mask
        occupied = [kind for kind in ('object_events', 'warp_events', 'coord_events', 'bg_events')
                    if any([event['x'], event['y']] == list(xy) for event in mapping.get(kind, []))]
        return dict(map=name, map_id=map_id, position=list(xy), block=block,
            elevation=block >> 12, collision=(block >> 10) & 3, behavior=behavior,
            static_events=occupied, layout=mapping['layout'], file=path,
            blockdata_sha256=hashlib.sha256(raw).hexdigest())


def census(layer, text, require_dry=True):
    terrain = Terrain(layer)
    result = []
    # These are the reviewed common floor, short grass, sand and native wooden
    # bridge behaviors used by these 31 starts. Water, directional movement,
    # doors and unknown behaviors require a new review rather than a loose pass.
    safe = {0, 7, 33, *range(112, 120)}
    for row in rows(text):
        lx, ly = row['landing']; tx, ty = row['truck']
        mother = [lx, ly-1] if row['boat'] else [tx+2, ty-1]
        actors = [dict(actor='player', **terrain.cell(row['map_id'], [lx, ly])),
                  dict(actor='mother', **terrain.cell(row['map_id'], mother))]
        for actor in actors:
            actor['dry_walkable'] = (actor['elevation'] in (3, 4, 5) and
                actor['collision'] == 0 and actor['behavior'] in safe)
            if require_dry:
                assert actor['dry_walkable'], ('Arrival actor is not on reviewed dry ground', row['index'], actor)
                if row['index'] in REPAIRS:
                    assert not actor['static_events'], ('Arrival actor overlaps an event', row['index'], actor)
        assert actors[0]['position'] != actors[1]['position']
        result.append(dict(index=row['index'], map_id=row['map_id'], boat=row['boat'], actors=actors))
    return result


def repair(layer):
    before = read(layer, PATH).decode()
    parsed = rows(before)
    before_census = census(layer, before, require_dry=False)
    after = before
    changed = []
    for row in parsed:
        if row['index'] not in REPAIRS:
            continue
        old_map, new_map, old_landing, landing = REPAIRS[row['index']]
        assert row['boat']
        assert (row['map_id'], tuple(row['landing'])) in ((old_map, old_landing), (new_map, landing)), row
        replacement = '{'+', '.join([new_map, *map(str, row['truck']), *map(str, landing), 'TRUE'])+'}'
        if row['text'] != replacement:
            assert after.count(row['text']) == 1
            after = after.replace(row['text'], replacement)
            changed.append(dict(index=row['index'], before=row['text'], after=replacement))
    final_census = census(layer, after)
    updated = rows(after)
    for old, new in zip(parsed, updated):
        assert old['truck'] == new['truck'] and old['boat'] == new['boat']
        if old['index'] not in REPAIRS:
            assert old == new, ('Unrelated city changed', old['index'])
    if changed:
        assert len(changed) == 10
        layer.stage(PATH, after)
    return dict(kind='coastal-followup-initial-arrivals', path=PATH,
        before_sha256=hashlib.sha256(before.encode()).hexdigest(),
        after_sha256=hashlib.sha256(after.encode()).hexdigest(), changed_rows=changed,
        all_31_destinations=final_census, previous_destinations=before_census,
        all_player_and_mother_cells_dry=True, changed_cells_have_no_static_event=True,
        truck_coordinates_boat_flags_and_21_other_cities_unchanged=True,
        same_table_used_by_dynamic_warp_and_intro_voyage=True,
        map_graphics_events_connections_and_save_abi_unchanged=True,
        actual_cold_boot_through_city_choice_welcome_and_bedroom_required=True)
