"""Native whole-object, collision, usable-floor and battery proof for Horizonte.

The isolated retired portals and the removed stair receive declared local
placements. The real entrance, three actor approaches, exit and return form a
separate controller trip. No claim connects the isolated upper rooms to that
entrance. Read-only native getters use the existing private-ROM trampoline.
The two batteries use the declared native TrySavingData/export_save fixture;
the cold cores boot and Continue with controllers and read-only observers.
"""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import re

from generated_cave_portals import MAP, PORTALS
from validate_coast_scenery_objects import bootstrap
from validate_sevii_route_boundaries_native import observe_cells, cold_continue
from verify_sevii_route_boundaries_native import verify_pixels, verify_cold
from verify_sevii_integrated_piers_update import verify_captures
from verify_coastal_closures_update import verify_cold_boot

ROOT = Path(__file__).resolve().parents[2]
OUTSIDE = 'JourneyHorizonteApproach'
PARENT_ROM = '6a70d43313df75d2258c5bac46d7ab8c0aa50b6e4f1a7246d540159ee726d5fc'
PARENT_ELF = 'df384a54339cbd4de07c187592208ef4999636f095856e34aa4c1a47e5303545'
PORTAL_VIEWS = [[12, 20], [33, 27], [31, 28], [37, 32]]
PORTAL_ELEVATIONS = [3, 3, 3, 5]
GOALS = [[MAP, 14, 32], [MAP, 16, 32], [MAP, 3, 27], [MAP, 10, 30],
         [OUTSIDE, 43, 11], [MAP, 14, 32]]
ACTORS = [(2, [17, 32], [16, 32]), (1, [3, 26], [3, 27]), (3, [10, 29], [10, 30])]
JUMP_ACTIONS = [*range(0xC, 0x10), *range(0x3A, 0x3E), *range(0x42, 0x4E),
                0x50, 0x51, *range(0x78, 0x7C)]
TRUE_FIELDS = ('native_validation_performed', 'initial_party_progress_and_local_placements_are_fixtures',
    'after_placement_movement_controllers_only', 'private_read_only_query_trampoline_declared',
    'native_flash_save_calls_are_declared_fixtures',
    'no_midtrip_gameplay_script_position_elevation_camera_palette_or_vram_writes',
    'whole_objects_have_native_bg_vram_palette_and_rgb_quadrant_evidence',
    'usable_floor_trip_is_separate_from_isolated_portal_fixtures', 'frozen_source_and_artifact_unchanged')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _write(path, value):
    Path(path).write_text(json.dumps(value, indent=2)+'\n')


def _manifest(path):
    return dict(file=path.name, sha256=digest(path), bytes=path.stat().st_size)


def _point(state):
    return [state['map'], *state['tile']]


def _field(source, library, output, *, legacy=False):
    output.mkdir(parents=True, exist_ok=True)
    ns = bootstrap(source, library, output, [MAP, OUTSIDE])
    lib, symbols = ns['lib'], ns['s']
    originals = {key: ns[key] for key in ('step', 'native', 'warp', 'script', 'picture')}
    fixture, depth, phase = True, 0, 'bootstrap'
    fixtures, controls, queries, captures, route, portals, arrivals, actors = [], [], [], [], [], [], [], []

    def state():
        obj = symbols['gObjectEvents']+36*lib.read8(symbols['gPlayerAvatar']+5)
        sprite = symbols['gSprites']+68*lib.read8(obj+35)
        return dict(map=ns['by_location'][ns['location']()], tile=list(ns['position']()),
            surfing=bool(lib.read8(symbols['gPlayerAvatar'])&8), elevation=lib.read8(obj+11)&15,
            sprite_visible=not bool(lib.read16(sprite+0x3E)&4),
            object_visible=not bool(lib.read8(obj+1)&32))

    def step(count, key=0):
        if not fixture and not depth:
            if controls and controls[-1]['phase'] == phase and controls[-1]['key'] == key:
                controls[-1]['frames'] += count
            else:
                controls.append(dict(phase=phase, key=key, frames=count))
        originals['step'](count, key)

    def native(name, *values, **kwargs):
        nonlocal depth
        if not fixture:
            assert name.startswith(('MapGridGet', 'MetatileBehavior_Is')) or name in {
                'GetPlayerFacingDirection', 'IsDirectionalStairWarpMetatileBehavior',
                'PlayerGetElevation', 'IsPlayerFacingSurfableFishableWater', 'TrySavingData'}, name
            queries.append(dict(phase=phase, function=name, arguments=list(values)))
        depth += 1
        try:
            return originals['native'](name, *values, **kwargs)
        finally:
            depth -= 1

    def script(*args, **kwargs):
        assert fixture or depth, 'Gameplay script injected after placement'
        return originals['script'](*args, **kwargs)

    def warp(*args, **kwargs):
        assert fixture, 'Travel fixture used during a controller trip'
        return originals['warp'](*args, **kwargs)

    def capture(label):
        originals['picture'](label)
        row = dict(file=label+'.png', sha256=digest(output/(label+'.png')))
        captures.append(row)
        return row

    def place(name, point, label):
        nonlocal fixture, phase
        fixture, phase = True, label
        warp(name, *point)
        native('SetPlayerAvatarTransitionFlags', 1)
        native('DisableWildEncounters', 1)
        step(90)
        assert _point(state()) == [name, *point] and state()['surfing'] is False, state()
        fixtures.append(dict(label=label, map=name, tile=point, surfing=False))
        fixture = False

    def observe_move(before, after):
        route.append(dict(phase=phase, source=list(before), destination=list(after)))

    def save_battery(label):
        assert native('TrySavingData', 0, max_frames=6000) == 1
        battery = output/(label+'.sav')
        lib.export_save.argtypes, lib.export_save.restype = [ctypes.c_char_p], ctypes.c_int
        assert lib.export_save(str(battery).encode()) and battery.stat().st_size == 131072
        return _manifest(battery)

    ns.update(step=step, native=native, script=script, warp=warp, walk_observer=observe_move,
              walk_max_ticks=2400, walk_transition_pictures=False)
    try:
        # Keep all three sanctuary actors visible and present; these are
        # progress fixtures, set before any placement/controller trip.
        constants = (source/'include/constants/flags.h').read_text()
        for number in (716, 717, 718):
            value = int(re.search(r'^#define\s+FLAG_JOURNEY_SPECIAL_'+str(number)+r'\s+(0x\w+)', constants, re.M)[1], 16)
            native('FlagClear', value)
        if legacy:
            place(MAP, [15, 20], 'legacy-passable-north-door')
            before = state()
            step(120, 64)
            step(60)
            entered = state()
            assert entered['tile'] == [15, 19] and entered['elevation'] == 3
            cell = dict(metatile=native('MapGridGetMetatileIdAt', 22, 26),
                        collision=native('MapGridGetCollisionAt', 22, 26),
                        elevation=native('MapGridGetElevationAt', 22, 26))
            battery = save_battery('layer170-retired-door')
            save_address = lib.read32(symbols['gSaveBlock1Ptr'])
            saved_origin = [lib.read16(save_address), lib.read16(save_address+2)]
            assert saved_origin == [15, 19] and state()['tile'] == saved_origin
            result = dict(kind='generated-cave-portals-legacy-save-fixture', passed=True,
                rom_sha256=digest(source/'pokeemerald.gba'), elf_sha256=digest(source/'pokeemerald.elf'),
                before=before, entered=entered, door_grid=cell, saved_origin=saved_origin,
                captures=[capture('layer170-retired-door')],
                fixtures=fixtures, controls=controls, queries=queries, battery_saves=[battery],
                actual_native_flash_export=True, old_passable_door_entered_with_controllers=True,
                initial_party_progress_and_local_placements_are_fixtures=True)
            _write(output/'legacy-door.json', result)
            return result
        for index, portal in enumerate(PORTALS):
            label = 'retired-portal-'+str(index+1)
            place(MAP, portal['approach'], label)
            before = state()
            x, y = portal['entry'] if portal['kind'] == 'north_arch' else [portal['entry'][0], portal['entry'][1]+1]
            target = dict(cell=[x, y], metatile=native('MapGridGetMetatileIdAt', x+7, y+7),
                collision=native('MapGridGetCollisionAt', x+7, y+7),
                elevation=native('MapGridGetElevationAt', x+7, y+7))
            key = 64 if portal['kind'] == 'north_arch' else 128
            step(120, key)
            step(60)
            after = state()
            assert after == before and target['collision'] == 1
            ns['walk']((MAP, *PORTAL_VIEWS[index]))
            step(60)
            bx, by, width, height = portal['bounds']
            cells = [(bx+dx, by+dy, 0x219 if portal['kind'] == 'north_arch' else 0x209)
                     for dy in range(height) for dx in range(width)]
            cells += [(xx, yy, 0x219) for xx, yy in portal['extra_cells']]
            pixels = observe_cells(ns, cells)
            portals.append(dict(portal=portal, before=before, after=after, target=target,
                direction_key=key, held_frames=120, blocked_with_controllers=True,
                observation_player=state(), pixels=pixels, capture=capture(label)))
        place(MAP, [19, 15], 'corrected-floor-both-directions')
        phase = 'corrected-floor-both-directions'
        floor_samples, floor_arrivals = [], []
        movement_constants = (source/'include/constants/event_object_movement.h').read_text()
        jumps = {int(value, 0) for name, value in re.findall(r'^#define\s+(MOVEMENT_ACTION_\w*JUMP\w*)\s+(0x[0-9A-Fa-f]+|\d+)', movement_constants, re.M)}
        assert jumps == set(JUMP_ACTIONS)
        for goal in ([19, 14], [19, 13], [19, 14], [19, 15]):
            key = 128 if goal[1] > state()['tile'][1] else 64
            for _ in range(80):
                step(1, key)
                obj = symbols['gObjectEvents']+36*lib.read8(symbols['gPlayerAvatar']+5)
                sample = dict(tile=state()['tile'], action=lib.read8(obj+0x1C),
                    landing_jump=bool(lib.read8(obj)&32), elevation=state()['elevation'])
                floor_samples.append(sample)
                assert sample['action'] not in jumps and not sample['landing_jump']
                if sample['tile'] == goal:
                    step(30)
                    break
            else:
                raise AssertionError(('Corrected floor blocked', goal, state()))
            floor_arrivals.append(state())
        floor_grid = dict(metatile=native('MapGridGetMetatileIdAt', 26, 21),
            collision=native('MapGridGetCollisionAt', 26, 21), elevation=native('MapGridGetElevationAt', 26, 21),
            behavior=native('MapGridGetMetatileBehaviorAt', 26, 21))
        ns['walk']((MAP, 18, 15))
        step(60)
        floor_pixels = observe_cells(ns, [(19, 14, 0x211)])
        floor = dict(arrivals=floor_arrivals, samples=floor_samples, jump_actions=sorted(jumps),
            grid=floor_grid, observation_player=state(), pixels=floor_pixels,
            capture=capture('corrected-floor-both-directions'))
        place(OUTSIDE, [43, 11], 'real-entry-actors-exit-return')
        for index, goal in enumerate(GOALS):
            phase = 'usable-floor-'+str(index)
            ns['walk'](tuple(goal))
            step(60)
            player = state()
            assert _point(player) == goal
            arrivals.append(dict(goal=goal, player=player, capture=capture(phase)))
            if 1 <= index <= 3:
                local_id, point, approach = ACTORS[index-1]
                objects = []
                for slot in range(16):
                    at = symbols['gObjectEvents']+36*slot
                    if lib.read8(at)&1 and lib.read8(at+8) == local_id:
                        objects.append(dict(local_id=local_id,
                            tile=[lib.read16(at+16)-7, lib.read16(at+18)-7],
                            map_id=[lib.read8(at+10), lib.read8(at+9)],
                            elevation=lib.read8(at+11)&15))
                assert len(objects) == 1 and objects[0]['tile'] == point
                assert objects[0]['map_id'] == list(ns['map_id'](MAP))
                actors.append(dict(approach=approach, object=objects[0]))
        phase = 'usable-floor-save'
        battery = save_battery('usable-cave-floor')
        return dict(kind='generated-cave-portals-native', passed=True,
            rom_sha256=digest(source/'pokeemerald.gba'), elf_sha256=digest(source/'pokeemerald.elf'),
            map_id=list(ns['map_id'](MAP)), portals=portals, corrected_floor=floor,
            goals=GOALS, arrivals=arrivals, actor_approaches=actors, route=route,
            fixtures=fixtures, controls=controls, queries=queries, captures=captures,
            battery_saves=[battery], full_campaign_playthrough=False,
            **{key: True for key in TRUE_FIELDS})
    finally:
        lib.stop()
        ns['emulator_workspace'].cleanup()


def _legacy_continue(source, library, output, battery, map_id):
    """Load an actual old battery, observe height zero, and escape with DOWN."""
    path = ROOT/'tools/hoenn/validate_cold_boot.py'
    code = path.read_text()
    anchor = "                    result = dict(bundled_save_continue_to_field=True, field_map=[lib.read8(save+4), lib.read8(save+5)])"
    assert code.count(anchor) == 1
    observer = '''
                    obj=symbols['gObjectEvents']+36*lib.read8(symbols['gPlayerAvatar']+5)
                    def player():
                        return dict(map_id=[lib.read8(save+4),lib.read8(save+5)],
                            tile=[(lib.read16(obj+16)&65535)-7,(lib.read16(obj+18)&65535)-7],
                            elevation=lib.read8(obj+11)&15,
                            surfing=bool(lib.read8(symbols['gPlayerAvatar'])&8))
                    before=player()
                    assert before==dict(map_id=MAP_ID,tile=[15,19],elevation=0,surfing=False),before
                    layout=symbols['gBackupMapLayout']
                    width=lib.read32(layout)
                    grid=lib.read32(layout+8)
                    block=lib.read16(grid+2*((19+7)*width+15+7))&65535
                    assert block==0x619,hex(block)
                    picture('battery-retired-door-before-escape')
                    moves=[]
                    for tick in range(100):
                        step(1,128)
                        moves.append(player())
                        if moves[-1]['tile']==[15,20]:break
                    else:raise AssertionError(('Old door save cannot escape',moves))
                    step(60)
                    after=player()
                    assert after==dict(map_id=MAP_ID,tile=[15,20],elevation=3,surfing=False),after
                    picture('battery-retired-door-escaped')
                    result.update(before_escape=before,after_escape=after,loaded_grid_block=block,
                        escape_input=dict(key=128,frames=tick+1),escape_samples=moves,
                        old_save_escaped_with_controllers=True,no_callback_script_or_native_call_injection=True)
'''
    ns = {'__file__': str(path), '__name__': 'generated_cave_legacy_cold_continue', 'MAP_ID': map_id}
    exec(compile(code.replace(anchor, anchor+observer), str(path), 'exec'), ns)
    result = ns['validate'](source, library, output, battery)
    result['captures'] = [dict(file=p.name, sha256=digest(p)) for p in sorted(output.glob('*.png'))]
    _write(output/'cold-boot.json', result)
    return result


def run(source, library, output, parent_source=None):
    source, library, output = [Path(p).resolve() for p in (source, library, output)]
    before = [digest(source/name) for name in ('pokeemerald.gba', 'pokeemerald.elf')]
    report = _field(source, library, output)
    battery = output/report['battery_saves'][0]['file']
    report['floor_cold_continue'] = cold_continue(source, library, output/'floor-cold', battery,
        dict(map_id=report['map_id'], tile=[14, 32], surfing=False, elevation=5))
    report['components'] = [dict(file='floor-cold/cold-boot.json', sha256=digest(output/'floor-cold/cold-boot.json'))]
    if parent_source is not None:
        parent_source = Path(parent_source).resolve()
        assert [digest(parent_source/name) for name in ('pokeemerald.gba', 'pokeemerald.elf')] == [PARENT_ROM, PARENT_ELF]
        old = _field(parent_source, library, output/'parent170', legacy=True)
        report['parent_legacy_fixture'] = old
        report['legacy_cold_continue'] = _legacy_continue(source, library, output/'legacy-cold',
            output/'parent170'/old['battery_saves'][0]['file'], report['map_id'])
        report['components'] += [dict(file=name, sha256=digest(output/name))
            for name in ('parent170/legacy-door.json', 'legacy-cold/cold-boot.json')]
        assert [digest(parent_source/name) for name in ('pokeemerald.gba', 'pokeemerald.elf')] == [PARENT_ROM, PARENT_ELF]
        for name in (MAP, OUTSIDE):
            assert (source/f'data/maps/{name}/map.json').read_bytes() == (parent_source/f'data/maps/{name}/map.json').read_bytes()
    assert before == [digest(source/name) for name in ('pokeemerald.gba', 'pokeemerald.elf')]
    verify_report(report, output, before[0])
    _write(output/'caves.json', report)
    return report


def _player(state, point=None, elevation=None):
    assert state['surfing'] is False and state['sprite_visible'] is state['object_visible'] is True
    if point is not None:
        assert _point(state) == point
    if elevation is not None:
        assert state['elevation'] == elevation


def _sha(value):
    assert isinstance(value, str) and len(value) == 64 and set(value) <= set('0123456789abcdef')


def _child(report, name, directory, child):
    row = next(row for row in report['components'] if row['file'] == name)
    path = directory/name
    assert digest(path) == row['sha256'] and json.loads(path.read_bytes()) == child


def verify_report(report, directory, romsha):
    directory = Path(directory)
    assert report['kind'] == 'generated-cave-portals-native' and report['passed'] is True
    assert report['rom_sha256'] == romsha
    _sha(romsha)
    _sha(report['elf_sha256'])
    assert all(report[key] is True for key in TRUE_FIELDS)
    assert report['full_campaign_playthrough'] is False
    assert report['goals'] == GOALS
    assert len(report['map_id']) == 2 and all(type(v) is int for v in report['map_id'])
    images = verify_captures(report['captures'], directory)
    captures = {row['file']: row['sha256'] for row in report['captures']}
    assert len(captures) == len(report['captures'])
    used = set()
    assert len(report['portals']) == 4
    for index, (row, portal) in enumerate(zip(report['portals'], PORTALS)):
        assert row['portal'] == portal
        _player(row['before'], [MAP, *portal['approach']], PORTAL_ELEVATIONS[index])
        assert row['before'] == row['after']
        assert row['blocked_with_controllers'] is True and row['held_frames'] == 120
        assert row['direction_key'] == (64 if index < 2 else 128)
        expected_cell = portal['entry'] if index < 2 else [portal['entry'][0], portal['entry'][1]+1]
        assert row['target'] == dict(cell=expected_cell, metatile=0x219 if index < 2 else 0x209,
                                    collision=1, elevation=0)
        _player(row['observation_player'], [MAP, *PORTAL_VIEWS[index]])
        x, y, width, height = portal['bounds']
        cells = [[x+dx, y+dy] for dy in range(height) for dx in range(width)]+portal['extra_cells']
        assert [item['cell'] for item in row['pixels']['cells']] == cells
        assert row['pixels']['map'] == MAP
        assert row['capture']['file'] == 'retired-portal-'+str(index+1)+'.png'
        for cell, pixels in zip(cells, row['pixels']['cells']):
            verify_pixels(dict(row['pixels'], cells=[pixels]), row['capture'], captures, images,
                          cell, 0x219 if index < 2 else 0x209)
        used.add(row['capture']['file'])
    floor = report['corrected_floor']
    assert floor['grid'] == dict(metatile=0x211, collision=0, elevation=4, behavior=8)
    assert len(floor['arrivals']) == 4
    for state, tile in zip(floor['arrivals'], ([19, 14], [19, 13], [19, 14], [19, 15])):
        _player(state, [MAP, *tile], 4)
    assert floor['samples'] and {row['tile'][1] for row in floor['samples']} == {13, 14, 15}
    assert floor['jump_actions'] == JUMP_ACTIONS
    assert all(row['action'] not in floor['jump_actions'] and row['landing_jump'] is False
               and row['elevation'] == 4 and row['tile'][0] == 19 for row in floor['samples'])
    _player(floor['observation_player'], [MAP, 18, 15], 4)
    assert floor['capture']['file'] == 'corrected-floor-both-directions.png'
    assert captures[floor['capture']['file']] == floor['capture']['sha256']
    verify_pixels(floor['pixels'], floor['capture'], captures, images, [19, 14], 0x211)
    used.add(floor['capture']['file'])
    assert len(report['arrivals']) == len(GOALS)
    for index, (row, goal) in enumerate(zip(report['arrivals'], GOALS)):
        assert row['goal'] == goal
        _player(row['player'], goal, [5, 5, 5, 3, 3, 5][index])
        assert row['capture']['file'] == 'usable-floor-'+str(index)+'.png'
        assert captures[row['capture']['file']] == row['capture']['sha256']
        used.add(row['capture']['file'])
    assert used == set(captures)
    assert len(report['actor_approaches']) == 3
    for row, (local_id, tile, approach) in zip(report['actor_approaches'], ACTORS):
        assert row['approach'] == approach
        assert row['object'] == dict(local_id=local_id, tile=tile, map_id=report['map_id'],
                                     elevation=3 if local_id == 3 else 5)
    expected_fixtures = [dict(label='retired-portal-'+str(i+1), map=MAP, tile=p['approach'], surfing=False)
                         for i, p in enumerate(PORTALS)]
    expected_fixtures += [dict(label='corrected-floor-both-directions', map=MAP, tile=[19, 15], surfing=False),
                         dict(label='real-entry-actors-exit-return', map=OUTSIDE, tile=[43, 11], surfing=False)]
    assert report['fixtures'] == expected_fixtures
    route = [row for row in report['route'] if row['phase'].startswith('usable-floor-')]
    assert len(route) >= 60
    previous = [OUTSIDE, 43, 11]
    seams = []
    expected_phase = 0
    for index, row in enumerate(route):
        assert row['phase'] == 'usable-floor-'+str(expected_phase)
        assert row['source'] == previous
        now = row['destination']
        assert now != previous
        if now[0] == previous[0]:
            assert sum(abs(a-b) for a, b in zip(now[1:], previous[1:])) == 1
        else:
            seams.append([previous[0], now[0]])
            assert {previous[0], now[0]} == {MAP, OUTSIDE}
        previous = now
        if index+1 == len(route) or route[index+1]['phase'] != row['phase']:
            assert now == GOALS[expected_phase], ('Controller phase did not reach its declared goal', row)
            expected_phase += 1
    assert expected_phase == len(GOALS)
    assert previous == GOALS[-1]
    assert seams == [[OUTSIDE, MAP], [MAP, OUTSIDE], [OUTSIDE, MAP]]
    assert report['controls'] and {16, 32, 64, 128} <= {r['key'] for r in report['controls']}
    for row in report['controls']:
        assert type(row['frames']) is int and row['frames'] > 0 and row['key'] in (0, 1, 2, 16, 32, 64, 128)
    for index, portal in enumerate(report['portals']):
        case_inputs = [row for row in report['controls'] if row['phase'] == 'retired-portal-'+str(index+1)]
        assert case_inputs
        assert case_inputs[0] == dict(phase='retired-portal-'+str(index+1),
                                      key=portal['direction_key'], frames=120)
    for index in range(len(GOALS)):
        assert any(row['phase'] == 'usable-floor-'+str(index) and row['key'] in (16, 32, 64, 128)
                   for row in report['controls'])
    for row in report['queries']:
        assert row['function'].startswith(('MapGridGet', 'MetatileBehavior_Is')) or row['function'] in {
            'GetPlayerFacingDirection', 'IsDirectionalStairWarpMetatileBehavior', 'PlayerGetElevation',
            'IsPlayerFacingSurfableFishableWater', 'TrySavingData'}
    assert len(report['battery_saves']) == 1
    battery = report['battery_saves'][0]
    assert battery['file'] == 'usable-cave-floor.sav' and battery['bytes'] == 131072
    assert (directory/battery['file']).stat().st_size == 131072 and digest(directory/battery['file']) == battery['sha256']
    verify_cold(report['floor_cold_continue'], directory/'floor-cold', directory/battery['file'], romsha,
                dict(map_id=report['map_id'], tile=[14, 32], surfing=False, elevation=5), avatar=True)
    expected_components = ['floor-cold/cold-boot.json']
    _child(report, expected_components[0], directory, report['floor_cold_continue'])
    if 'parent_legacy_fixture' in report:
        expected_components += ['parent170/legacy-door.json', 'legacy-cold/cold-boot.json']
        old = report['parent_legacy_fixture']
        assert old['kind'] == 'generated-cave-portals-legacy-save-fixture' and old['passed'] is True
        assert old['rom_sha256'] == PARENT_ROM and old['elf_sha256'] == PARENT_ELF
        assert old['actual_native_flash_export'] is old['old_passable_door_entered_with_controllers'] is True
        assert old['initial_party_progress_and_local_placements_are_fixtures'] is True
        _player(old['before'], [MAP, 15, 20], 3)
        _player(old['entered'], [MAP, 15, 19], 3)
        assert old['door_grid'] == dict(metatile=0x214, collision=0, elevation=3)
        assert old['saved_origin'] == [15, 19]
        assert old['fixtures'] == [dict(label='legacy-passable-north-door', map=MAP, tile=[15, 20], surfing=False)]
        assert any(r['key'] == 64 and r['frames'] >= 120 for r in old['controls'])
        for row in old['queries']:
            assert row['function'].startswith('MapGridGet') or row['function'] == 'TrySavingData'
        assert len(old['battery_saves']) == 1
        old_battery = old['battery_saves'][0]
        assert old_battery['file'] == 'layer170-retired-door.sav' and old_battery['bytes'] == 131072
        assert (directory/'parent170'/old_battery['file']).stat().st_size == 131072
        assert digest(directory/'parent170'/old_battery['file']) == old_battery['sha256']
        assert set(verify_captures(old['captures'], directory/'parent170')) == {'layer170-retired-door.png'}
        cold = report['legacy_cold_continue']
        verify_cold_boot(cold, True, directory/'parent170'/old_battery['file'])
        assert cold['passed'] is cold['controllers_only'] is cold['no_game_memory_writes'] is True
        assert cold['rom_sha256'] == romsha and cold['bundled_save_sha256'] == old_battery['sha256']
        assert [r['battery'] for r in cold['runs']] == [False, True]
        assert all(r['frames'] >= 2000 and r['samples'] for r in cold['runs'])
        continued = cold['runs'][1]
        assert continued['bundled_save_continue_to_field'] is True
        assert continued['old_save_escaped_with_controllers'] is continued['no_callback_script_or_native_call_injection'] is True
        assert continued['before_escape'] == dict(map_id=report['map_id'], tile=[15, 19], elevation=0, surfing=False)
        assert continued['after_escape'] == dict(map_id=report['map_id'], tile=[15, 20], elevation=3, surfing=False)
        assert continued['loaded_grid_block'] == 0x619
        assert continued['escape_input']['key'] == 128 and 1 <= continued['escape_input']['frames'] <= 100
        assert len(continued['escape_samples']) == continued['escape_input']['frames']
        assert continued['escape_samples'][-1]['tile'] == continued['after_escape']['tile']
        assert all(r['map_id'] == report['map_id'] and r['tile'] in ([15, 19], [15, 20])
                   and r['surfing'] is False for r in continued['escape_samples'])
        assert set(verify_captures(cold['captures'], directory/'legacy-cold')) == {
            'fresh-title.png', 'fresh-main-menu.png', 'fresh-new-game.png', 'battery-title.png',
            'battery-main-menu.png', 'battery-continued-to-field.png',
            'battery-retired-door-before-escape.png', 'battery-retired-door-escaped.png'}
        _child(report, expected_components[1], directory, old)
        _child(report, expected_components[2], directory, cold)
    assert [r['file'] for r in report['components']] == expected_components
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--library', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--parent-source', type=Path)
    args = parser.parse_args()
    run(args.source, args.library, args.output, args.parent_source)
