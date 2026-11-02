"""Close transition-height water beside the integrated Sevii low boardwalks.

Water at elevation zero accepts an entering pedestrian and then drops the
actor to the sea level without enabling Surf. The enlarged One Island pier
exposed two such cells. Normalize the complete remaining open-water patch,
not merely the two observed exits; all art and collision bits stay intact.
"""
import hashlib
import json
import re
import struct

from badge_story_layer import read
from integrated_sevii_harbors import CONFIG

# These native behaviors can be traversed with Surf on the connected Sevii
# coast. This list deliberately excludes dry low-deck and multi-level bridge
# art: elevation zero there has a different meaning.
WATER_BEHAVIORS = frozenset((16, 17, 18, 20, 21, 25, 34, 42, 44, 80, 81, 82, 83))
AFFECTED_MAP = 'OneIsland_TreasureBeach_Frlg'
EXPECTED_CELLS = 65


def inventory(layer):
    layouts = {row['id']: row for row in json.loads(
        read(layer, 'data/layouts/layouts.json'))['layouts']}
    headers = read(layer, 'src/data/tilesets/headers.h').decode()
    definitions = read(layer, 'src/data/tilesets/metatiles.h').decode()
    attributes = {}
    records = []
    names = sorted({cfg['map'] for cfg in CONFIG.values()}
                   | {cfg['front_map'] for cfg in CONFIG.values() if 'front_map' in cfg})
    for name in names:
        mapping = json.loads(read(layer, f'data/maps/{name}/map.json'))
        layout = layouts[mapping['layout']]
        assert layout['layout_version'] == 'frlg', name
        tables = []
        for key in ('primary_tileset', 'secondary_tileset'):
            symbol = layout[key]
            if symbol not in attributes:
                body = re.search(r'const struct Tileset ' + re.escape(symbol)
                                 + r'\s*=\s*\{(.*?)\};', headers, re.S)[1]
                attr = re.search(r'\.metatileAttributes\s*=\s*(\w+)', body)[1]
                path = re.search(r'\b' + re.escape(attr) + r'\[\].*?"([^"]+)"',
                                 definitions)[1]
                raw = read(layer, path)
                assert len(raw) % 4 == 0
                attributes[symbol] = [value & 511 for value in struct.unpack(
                    '<' + 'I' * (len(raw)//4), raw)]
            tables.append(attributes[symbol])
        path = layout['blockdata_filepath']
        raw = read(layer, path)
        width, height = layout['width'], layout['height']
        assert len(raw) == 2 * width * height
        words = list(struct.unpack('<' + 'H' * (width * height), raw))
        aquatic = []
        for index, word in enumerate(words):
            mid = word & 1023
            behavior = tables[0 if mid < 640 else 1][mid if mid < 640 else mid-640]
            if behavior in WATER_BEHAVIORS and not word & 0xC00:
                aquatic.append((index, word, behavior))
        records.append(dict(map=name, map_id=mapping['id'], file=path,
                            width=width, height=height, raw=raw, words=words,
                            aquatic=aquatic))
    return records


def repair(layer):
    reports, touched = [], []
    for record in inventory(layer):
        words = record['words']
        changes = []
        for index, before, behavior in record['aquatic']:
            if before >> 12 != 0:
                continue
            assert record['map'] == AFFECTED_MAP, (
                'Unexpected transition-height coast needs separate review', record['map'], index)
            after = (before & 0x0FFF) | 0x1000
            words[index] = after
            changes.append(dict(position=[index % record['width'], index // record['width']],
                                before=before, after=after, behavior=behavior))
        if changes:
            assert len(changes) == EXPECTED_CELLS
            assert all((row['before'] & 0x0FFF) == (row['after'] & 0x0FFF)
                       for row in changes)
            layer.stage(record['file'], struct.pack('<'+'H'*len(words), *words))
            touched.append(record['file'])
        reports.append(dict(map=record['map'], map_id=record['map_id'],
                            file=record['file'], dimensions=[record['width'], record['height']],
                            traversable_water_cells=len(record['aquatic']),
                            transition_water_before=len(changes), transition_water_after=0,
                            changed_cells=changes,
                            before_sha256=hashlib.sha256(record['raw']).hexdigest(),
                            after_sha256=hashlib.sha256(read(layer, record['file'])).hexdigest()))
    return dict(kind='coastal-ecology-safe-pier-water', maps=reports,
                changed_paths=touched, normalized_water_cells=sum(
                    row['transition_water_before'] for row in reports),
                water_graphics_and_collision_unchanged=True,
                all_dry_deck_cells_unchanged=True,
                all_events_warps_connections_unchanged=True,
                atlas_unchanged=True, native_controller_validation_required=True)
