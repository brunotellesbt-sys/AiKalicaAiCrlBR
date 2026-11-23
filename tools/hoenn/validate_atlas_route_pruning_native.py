"""Verify route closures, remaining passages and old saves with native inputs."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import struct

from atlas_surf_background import cells
from atlas_surf_geometry import chunk_water
from atlas_surf_route_borders import _neighbor
from atlas_surf_source import Source
from atlas_surf_truth import ART_ARRAYS, array_values
from candidate_layer import Layer
from prepare_atlas_route_pruning import ART, H, J, K, LAYER, PRIOR, K_ISLAND, TRAINER_MAP
from validate_atlas_candidate_batteries_native import save_menu
from validate_coast_scenery_objects import bootstrap
from validate_cold_boot import validate as cold_boot
from validate_generated_area_review_source import compiled_map_bindings
from validate_sevii_route_boundaries_source import Inputs, symbols

DIRECTION_KEYS = {(1, 0): 16, (-1, 0): 32, (0, -1): 64, (0, 1): 128}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def world_points(view, plan):
    chunks = {row['name']: row for row in plan['chunks']}
    points = {}
    for name, chunk in chunks.items():
        ox, oy = chunk['origin']
        for x, y in chunk_water(chunk):
            if view.water(name, x, y):
                points[ox + x, oy + y] = (name, x, y)
    return points


def bind_chart_and_blocks(view, changes, art_sha):
    rom = (view.source / 'pokeemerald.gba').read_bytes()
    table = symbols(view.source)
    ranges = {}
    compiled_map_bindings(view.source, Inputs(view.source), sorted(changes))
    for name in changes:
        layout = view.layout(name)
        header_offset = table[layout['name']][0] - 0x08000000
        address = struct.unpack_from('<I', rom, header_offset + 12)[0] - 0x08000000
        expected = view.read(layout['blockdata_filepath'])
        assert 0 <= address < len(rom) and rom[address:address + len(expected)] == expected, name
        ranges[name] = dict(offset=address, size=len(expected), sha256=hashlib.sha256(expected).hexdigest())

    header = view.read(ART).decode()
    for name in ART_ARRAYS:
        values = array_values(header, name)
        width = 'H' if name in ('sWorldPalette', 'sWorldTilemap') else 'B'
        raw = struct.pack('<' + width * len(values), *values)
        address, size = table[name]
        offset = address - 0x08000000
        assert 0 <= offset < len(rom) and size == len(raw) and rom[offset:offset + size] == raw
        assert hashlib.sha256(raw).hexdigest() == art_sha[name]
        ranges[name] = dict(offset=offset, size=size, sha256=art_sha[name])
    return ranges


def run(before, after, library, output):
    before, after, library, output = (Path(p).resolve() for p in (before, after, library, output))
    output.mkdir(parents=True, exist_ok=True)
    parent = json.loads((before / '.journey-atlas-surf-layout').read_bytes())
    marker = json.loads((after / f'.journey-{LAYER}').read_bytes())
    old_view, view = Source(before), Source(after)
    plan = marker['geometry_plan']
    result = marker['route_pruning']
    assert set(map(tuple, result['removed_pixels'])) == H | J | K
    expected = Layer(before, LAYER, PRIOR).expected | marker['prepared_sha256']
    for path, wanted in expected.items():
        assert sha(after / path) == wanted, path
    ranges = bind_chart_and_blocks(view, result['changed_words_by_map'], marker['art_sha256'])
    old_points = world_points(old_view, parent['geometry_plan'])
    points = world_points(view, plan)
    rows = {row['name']: row for row in plan['chunks']}
    assert not points.keys() - old_points.keys()
    candidates = defaultdict(list)
    for name in result['changed_words_by_map']:
        ox, oy = rows[name]['origin']
        for y in range(rows[name]['height']):
            for x in range(rows[name]['width']):
                target = (name, x, y)
                if not old_view.water(*target) or not view.word(*target) & 0xc00:
                    continue
                pixel = ((ox + x) // 8, (oy + y) // 8)
                section = 'K' if pixel[1] < 70 else 'J' if pixel[0] <= 125 else 'H'
                for dx, dy in DIRECTION_KEYS:
                    start = _neighbor(view, *target, -dx, -dy)
                    if not start or start[0] not in rows or not view.water(*start):
                        continue
                    if _neighbor(view, *start, dx, dy) != target:
                        continue
                    if (start[1], start[2]) in cells(rows[start[0]]):
                        continue
                    candidates[section, dx, dy, *pixel].append((start, target))
    assert {r[0] for r in candidates} == {'H', 'J', 'K'}
    bumps = []
    for group, choices in sorted(candidates.items()):
        # Pick the centre of the blocked span and prove every entrance.
        choices.sort()
        start, target = choices[len(choices) // 2]
        dx, dy = group[1:3]
        case = 'reef-' + '-'.join(map(str, group))
        folder = output / case
        folder.mkdir(exist_ok=True)
        ns = bootstrap(after, library, folder, {start[0], target[0]})
        try:
            place(ns, start, 9, surfing=True)
            ns['picture']('before')
            word = view.word(*target)
            gx, gy = start[1] + dx + 7, start[2] + dy + 7
            assert ns['native']('MapGridGetMetatileIdAt', gx, gy) == word & 1023
            assert ns['native']('MapGridGetCollisionAt', gx, gy) == (word >> 10) & 3
            ns['step'](90, DIRECTION_KEYS[dx, dy])
            ns['step'](30)
            assert state(ns) == start and ns['player_state']()['surfing']
            ns['picture']('after')
        finally:
            close(ns)
        bumps.append(dict(case=case, approach=start, blocked=target, native_word=word, frames=90))
        print('Native reef blocked:', case, start, flush=True)

    trips = [
        ('K-west-east', [(94, 60), (95, 59), (105, 59)]),
        ('K-south-fork', [(102, 59), (101, 59), (101, 62)]),
        ('H-J-around-mossdeep', [(124, 84), (127, 84), (127, 86), (127, 89)]),
    ]
    travelled = []
    for label, pixels in trips:
        places = [points[8 * ax + 4, 8 * ay + 4] for ax, ay in pixels]
        left, right = min(x for x, y in pixels) - 1, max(x for x, y in pixels) + 1
        top, bottom = min(y for x, y in pixels) - 1, max(y for x, y in pixels) + 1
        scope = {n for (gx, gy), (n, x, y) in points.items()
                 if left <= gx // 8 <= right and top <= gy // 8 <= bottom}
        folder = output / label
        folder.mkdir(exist_ok=True)
        ns = bootstrap(after, library, folder, scope)
        try:
            for row in parent['surf_trainer_redesign']['trainers']:
                if row['map'] in scope:
                    ns['rawflag'](row['flag'], True)
            place(ns, places[0], 9, surfing=True)
            ns['picture']('departure')
            for goal in places[1:] + places[-2::-1]:
                ns['walk'](goal)
                assert state(ns) == goal and ns['player_state']()['surfing']
            ns['picture']('return')
            travelled.append(dict(case=label, destinations=places, transitions=ns['transitions']))
        finally:
            close(ns)
        print('Native Surf round trip:', label, flush=True)

    rescues = {tuple(row[:3]): tuple(row[3:]) for row in result['save_moves']}
    migration = []
    samples = ['JourneyAtlasSea361', TRAINER_MAP, 'JourneyAtlasSea140', 'JourneyAtlasSea142', K_ISLAND]
    for name in samples:
        surf = name != K_ISLAND
        origin = next(p for p, dest in rescues.items() if p[0] == name
                      and old_view.water(*p) == surf and not old_view.word(*p) & 0xc00
                      and p != (TRAINER_MAP, 10, 9))
        dest = rescues[origin]
        folder = output / ('save-' + name)
        folder.mkdir(exist_ok=True)
        initial = folder / 'original-v8.sav'
        new = folder / 'migrated-v9.sav'
        ns = bootstrap(before, library, folder, {name})
        try:
            place(ns, origin, 8, surfing=surf)
            save_menu(ns, initial)
        finally:
            close(ns)
        first = cold_boot(after, library, folder / 'first', initial, new, expected_geometry_version=9)
        second = cold_boot(after, library, folder / 'second', new, expected_geometry_version=9)
        packed = view.identities[dest[0]]
        for boot in (first, second):
            saved = boot['runs'][-1]
            assert saved['field_map'] == [packed >> 8, packed & 255]
            assert tuple(saved['player_tile']) == dest[1:]
            assert saved['player_surfing'] == surf and saved['player_elevation'] == (1 if surf else 3)
        migration.append(dict(from_point=origin, to_point=dest, surfing=surf,
                              old_battery_sha=sha(initial), new_battery_sha=sha(new)))
        print('Native save migration / repeated Continue:', name, origin, dest, flush=True)

    report = dict(passed=True, old_rom_sha256=sha(before / 'pokeemerald.gba'),
                  new_rom_sha256=sha(after / 'pokeemerald.gba'),
                  elf_sha256=sha(after / 'pokeemerald.elf'),
                  marker_sha256=sha(after / f'.journey-{LAYER}'),
                  source_inputs_checked=len(expected),
                  compiled_ranges=ranges,
                  reef_bumps=bumps, trips=travelled, saves=migration)
    (output / 'native.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def state(ns):
    return (ns['by_location'][ns['location']()], *ns['position']())


def place(ns, point, version, *, surfing):
    ns['native']('VarSet', 0x40dc, version)
    ns['warp'](*point)
    ns['native']('SetPlayerAvatarTransitionFlags', 8 if surfing else 1)
    ns['native']('DisableWildEncounters', 1)
    ns['step'](180)
    assert state(ns) == point and ns['player_state']()['surfing'] == surfing


def close(ns):
    ns['lib'].stop()
    ns['emulator_workspace'].cleanup()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ('before', 'after', 'library', 'output'):
        parser.add_argument('--' + arg, required=True, type=Path)
    run(**vars(parser.parse_args()))
