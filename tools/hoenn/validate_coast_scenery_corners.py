"""Controller and hardware scanout evidence for the layer 170 marine corners."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from marine_corner_coherence import REPRO_CASES, SOURCE_ONLY_CASES, Source
from validate_sevii_route_boundaries_native import observe_cells
from verify_sevii_route_boundaries_native import verify_pixels
from verify_sevii_integrated_piers_update import verify_captures

ROOT = Path(__file__).resolve().parents[2]
KEY = {'left': 32, 'right': 16, 'up': 64, 'down': 128}
OPPOSITE = {'left': 'right', 'right': 'left', 'up': 'down', 'down': 'up'}


def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(source, library, output, parent_source=None, *, baseline=False):
    source, library, output = Path(source).resolve(), Path(library).resolve(), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    hashes = [digest(source/name) for name in ('pokeemerald.gba', 'pokeemerald.elf')]
    parent = None
    if parent_source is not None:
        parent = run(parent_source, library, output/'parent169', baseline=True)
    bootstrap = ROOT/'tools/hoenn/validate_abilities.py'
    code = bootstrap.read_text().split('\nability_field,')[0]
    argv = sys.argv
    ns = {'__file__': str(bootstrap), '__name__': 'coast_scenery_corner_native'}
    try:
        sys.argv = [str(bootstrap), '--source', str(source), '--library', str(library), '--output', str(output)]
        exec(compile(code, str(bootstrap), 'exec'), ns)
    finally:
        sys.argv = argv
    lib, native, step, warp = (ns[k] for k in ('lib', 'native', 'step', 'warp'))
    maps = {p.parent.name: json.loads(p.read_bytes()) for p in (source/'data/maps').glob('*/map.json')}
    ns['maps'] = maps
    ns['by_location'] = {(g, i): n for g, label in enumerate(ns['groups']['group_order'])
                         for i, n in enumerate(ns['groups'][label])}
    captures, fixtures, controls, queries, cases, bumps = [], [], [], [], [], []
    fixture = True
    original_native = native

    def query(name, *args):
        assert name.startswith('MapGridGet') or name == 'GetMapBorderIdAt'
        if not fixture: queries.append(dict(function=name, arguments=list(args)))
        return original_native(name, *args)

    ns['native'] = query

    def state():
        return dict(map=ns['by_location'][ns['location']()], tile=list(ns['position']()),
                    surfing=bool(lib.read8(ns['s']['gPlayerAvatar']) & 8))

    def place(name, player, label):
        nonlocal fixture
        fixture = True
        warp(name, *player)
        step(60)
        if not lib.read8(ns['s']['gPlayerAvatar']) & 8:
            original_native('SetPlayerAvatarTransitionFlags', 8)
            step(60)
        assert state() == dict(map=name, tile=list(player), surfing=True), state()
        fixtures.append(dict(label=label, map=name, tile=list(player), surfing=True))
        fixture = False

    def cross(direction, neighbor, target):
        for frame in range(240):
            step(1, KEY[direction])
            if ns['location']() == ns['map_id'](neighbor): break
        else: raise AssertionError(('Controller seam blocked', state(), direction, neighbor))
        controls.append(dict(direction=direction, frames=frame+1, neighbor=neighbor, target=list(target)))
        step(30)
        assert state() == dict(map=neighbor, tile=list(target), surfing=True), state()

    def grid(cell):
        x, y = cell
        backup = ns['s']['gBackupMapLayout']
        w, h, address = [lib.read32(backup+4*i) for i in range(3)]
        gx, gy = x+7, y+7
        assert 0 <= gx < w and 0 <= gy < h
        return dict(cell=list(cell), block=lib.read16(address+2*(gy*w+gx)),
            metatile=query('MapGridGetMetatileIdAt', gx, gy),
            collision=query('MapGridGetCollisionAt', gx, gy),
            elevation=query('MapGridGetElevationAt', gx, gy), border_id=query('GetMapBorderIdAt', gx, gy))

    def picture(label):
        ns['picture'](label)
        row = dict(file=label+'.png', sha256=digest(output/(label+'.png')))
        captures.append(row)
        return row

    def view(cell, label, expected=None):
        result = grid(cell)
        if expected is not None:
            assert result['metatile'] == expected, (state(), result, expected)
        pixels = observe_cells(ns, [(*cell, result['metatile'])])
        return dict(state=state(), grid=result, pixels=pixels, capture=picture(label))

    def viewport_pixels(cell):
        # Observe the entire hardware viewport, with no sprite/UI exclusion.
        # Zero therefore proves absence even before any occlusion is removed.
        save = lib.read32(ns['s']['gSaveBlock1Ptr'])
        origin = [lib.read16(save+i) for i in (0, 2)]
        ring = [lib.read8(ns['s']['sFieldCameraOffset']+i) for i in (2, 3)]
        scroll = [lib.read16(ns['s']['sGpuRegBuffer']+i) & 511 for i in (0x14, 0x16)]
        return sum((origin[0]+(((x+scroll[0])%256//8-ring[0])%32)//2-7,
                    origin[1]+(((y+scroll[1])%256//8-ring[1])%32)//2-7) == tuple(cell)
                   for y in range(160) for x in range(240))

    try:
        original_native('DisableWildEncounters', 1)
        for case in REPRO_CASES:
            place(case['map'], case['player'], case['label'])
            expected = None if baseline else case['expected_metatile']
            before = view(case['cell'], case['label']+'-before', expected)
            cross(case['direction'], case['neighbor'], case['target'])
            after = view(case['neighbor_cell'], case['label']+'-after', expected)
            cross(OPPOSITE[case['direction']], case['map'], case['player'])
            returned = view(case['cell'], case['label']+'-returned', expected)
            cases.append(dict(case=case, before=before, after=after, returned=returned,
                outbound_and_return_with_controllers=True,
                parent_pop_observed=before['grid']['metatile'] != after['grid']['metatile']))
        case = SOURCE_ONLY_CASES[0]
        place(case['map'], case['player'], 'unviewable-03104')
        before = dict(state=state(), grid=grid(case['cell']), visible_pixels=viewport_pixels(case['cell']))
        cross(case['direction'], case['neighbor'], case['target'])
        after = dict(state=state(), grid=grid(case['neighbor_cell']), visible_pixels=viewport_pixels(case['neighbor_cell']))
        assert before['visible_pixels'] == after['visible_pixels'] == 0
        source_only = dict(case=case, before=before, after=after, source_only_not_a_visible_bug=True)
        if not baseline:
            metadata = json.loads((source/'.journey-coast-scenery-review').read_bytes())
            contract = metadata.get('corners') or metadata.get('marine_corners') or metadata.get('corner_coherence')
            assert contract, 'Layer marker must contain its marine-corner repair contract'
            inputs = Source(source)
            chosen = {}
            for row in contract['changed_cells']:
                name, x, y = row['map'], row['x'], row['y']
                approaches = chosen.setdefault(name, [])
                if len(approaches) == 2: continue
                l = inputs.layout(name)
                for dx, dy, direction in ((-1, 0, 'right'), (1, 0, 'left'), (0, -1, 'down'), (0, 1, 'up')):
                    px, py = x+dx, y+dy
                    if not (0 <= px < l['width'] and 0 <= py < l['height']): continue
                    word = inputs.word(name, px, py)
                    if word & 0xC00 or inputs.behavior(name, word) not in inputs.water: continue
                    if any(item[2] == direction for item in approaches): continue
                    approaches.append((row, [px, py], direction))
                    if len(approaches) == 2: break
            assert set(chosen) == set(contract['changed_map_counts'])
            assert all(len(rows) == 2 for rows in chosen.values())
            for name, approaches in sorted(chosen.items()):
                for row, player, direction in approaches:
                    label = 'reef-bump-'+name+'-'+direction
                    place(name, player, label)
                    before = state()
                    target = grid([row['x'], row['y']])
                    assert target['collision'] == 1 and target['elevation'] == 1
                    assert target['metatile'] == row['after'] & 1023
                    step(48, KEY[direction])
                    controls.append(dict(direction=direction, frames=48, purpose='reef-bump', map=name))
                    step(30)
                    assert state() == before, ('New reef could be crossed', name, before, state())
                    bumps.append(dict(map=name, target=target, before=before, after=state(),
                        controls_direction=direction, held_frames=48, blocked=True,
                        capture=picture(label)))
    finally:
        lib.stop()
        ns['emulator_workspace'].cleanup()
    assert hashes == [digest(source/name) for name in ('pokeemerald.gba', 'pokeemerald.elf')]
    result = dict(kind='coast-scenery-corners-native', passed=True,
        rom_sha256=hashes[0], elf_sha256=hashes[1], baseline=baseline,
        native_validation_performed=True, initial_placements_and_surf_state_are_fixtures=True,
        private_query_trampoline_declared=True, only_read_only_queries_after_placement=True,
        no_midtrip_position_collision_elevation_camera_palette_or_vram_writes=True,
        parent_source_and_rom_unchanged=True, corner_cases=cases, source_only_case=source_only,
        reef_bumps=bumps, fixtures=fixtures, controls=controls, queries=queries,
        captures=captures, full_campaign_playthrough=False)
    if parent is not None:
        result['parent_baseline'] = parent
        result['components'] = [dict(kind=parent['kind'], file='parent169/corners-native.json',
                                     sha256=digest(output/'parent169/corners-native.json'))]
    (output/'corners-native.json').write_text(json.dumps(result, indent=2)+'\n')
    verify_report(result, output, hashes[0])
    return result


def verify_report(report, directory, expected_rom_sha256=None):
    directory = Path(directory)
    assert report['kind'] == 'coast-scenery-corners-native' and report['passed'] is True
    if expected_rom_sha256 is not None: assert report['rom_sha256'] == expected_rom_sha256
    for key in ('rom_sha256', 'elf_sha256'):
        value = report[key]
        assert len(value) == 64 and set(value) <= set('0123456789abcdef')
    for key in ('native_validation_performed', 'initial_placements_and_surf_state_are_fixtures',
                'private_query_trampoline_declared', 'only_read_only_queries_after_placement',
                'no_midtrip_position_collision_elevation_camera_palette_or_vram_writes',
                'parent_source_and_rom_unchanged'):
        assert report[key] is True
    assert report['full_campaign_playthrough'] is False
    images = verify_captures(report['captures'], directory)
    captures = {row['file']: row['sha256'] for row in report['captures']}
    assert len(captures) == len(report['captures'])
    assert len(report['corner_cases']) == len(REPRO_CASES)
    used = set()
    for row, case in zip(report['corner_cases'], REPRO_CASES):
        assert row['case'] == case and row['outbound_and_return_with_controllers'] is True
        for phase, name, player, cell in (('before', case['map'], case['player'], case['cell']),
                ('after', case['neighbor'], case['target'], case['neighbor_cell']),
                ('returned', case['map'], case['player'], case['cell'])):
            record = row[phase]
            assert record['state'] == dict(map=name, tile=player, surfing=True)
            grid = record['grid']
            assert grid['cell'] == cell
            if not report['baseline']: assert grid['metatile'] == case['expected_metatile']
            if grid['block'] == 1023:
                assert (grid['collision'], grid['elevation'], grid['border_id']) == (1, 0, 0xFFFFFFFF)
            else:
                assert grid['metatile'] == grid['block'] & 1023
                assert grid['collision'] == (grid['block'] >> 10) & 3
                assert grid['elevation'] == grid['block'] >> 12
            verify_pixels(record['pixels'], record['capture'], captures, images, cell, grid['metatile'])
            used.add(record['capture']['file'])
    source_only = report['source_only_case']
    assert source_only['case'] == SOURCE_ONLY_CASES[0]
    assert source_only['source_only_not_a_visible_bug'] is True
    assert source_only['before']['visible_pixels'] == source_only['after']['visible_pixels'] == 0
    assert len(report['reef_bumps']) == (0 if report['baseline'] else 26)
    if not report['baseline']:
        assert len({row['map'] for row in report['reef_bumps']}) == 13
        for name in {row['map'] for row in report['reef_bumps']}:
            assert len({row['controls_direction'] for row in report['reef_bumps'] if row['map'] == name}) == 2
    for row in report['reef_bumps']:
        assert row['blocked'] is True and row['held_frames'] >= 48
        assert row['before'] == row['after']
        assert row['target']['collision'] == row['target']['elevation'] == 1
        used.add(row['capture']['file'])
    assert used == set(captures)
    assert all(row['function'].startswith('MapGridGet') or row['function'] == 'GetMapBorderIdAt'
               for row in report['queries'])
    assert len(report['controls']) == 2*len(REPRO_CASES)+1+len(report['reef_bumps'])
    if 'parent_baseline' in report:
        import coast_scenery_review_contract as contract
        parent = report['parent_baseline']
        assert parent['baseline'] is True and parent['rom_sha256'] == contract.PARENT_ROM_SHA256
        assert parent['elf_sha256'] == contract.PARENT_ELF_SHA256
        path = directory/'parent169/corners-native.json'
        assert report['components'] == [dict(kind=parent['kind'], file='parent169/corners-native.json', sha256=digest(path))]
        assert json.loads(path.read_bytes()) == parent
        verify_report(parent, directory/'parent169')
        assert sum(row['parent_pop_observed'] for row in parent['corner_cases']) == 7
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--library', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--parent-source', type=Path)
    parser.add_argument('--baseline', action='store_true')
    args = parser.parse_args()
    run(args.source, args.library, args.output, args.parent_source, baseline=args.baseline)
