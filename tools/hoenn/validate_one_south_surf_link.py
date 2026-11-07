"""Sail One's new vertical route, turn both ways and return by native controls.

One initial party/progress/placement fixture precedes the trip. The route,
reef bumps, disembarkation, Surf prompts and both saves use controller input.
Two exported batteries receive independent cold Continue checks.
"""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path

from one_south_surf_link import BEACH, SEA, PASSAGE
from validate_coast_scenery_objects import bootstrap
from validate_sevii_route_boundaries_native import observe_cells, cold_continue
from verify_sevii_route_boundaries_native import verify_pixels, verify_cold
from verify_sevii_integrated_piers_update import verify_captures, verify_native_avatar_pixels

ROOT = Path(__file__).resolve().parents[2]
START = [BEACH, 4, 43]
# Each turn is explicit: a graph cannot substitute the retired harbor circuit.
GOALS = [
    [BEACH, 4, 39], [BEACH, 4, 45], [PASSAGE, 4, 2],
    [PASSAGE, 4, 16], [PASSAGE, 1, 16], [PASSAGE, 2, 16],
    [PASSAGE, 6, 16], [PASSAGE, 5, 16], [PASSAGE, 4, 29],
    [SEA, 66, 2], [SEA, 66, 6], [SEA, 60, 6], [SEA, 76, 6],
    [SEA, 66, 6], [PASSAGE, 4, 29], [PASSAGE, 4, 2],
    [BEACH, 4, 45], [BEACH, 4, 43], [BEACH, 35, 43],
    [BEACH, 35, 39], [BEACH, 35, 14],
    [BEACH, 26, 20], [BEACH, 24, 21], [BEACH, 26, 20],
    [BEACH, 29, 14], [BEACH, 29, 6], [BEACH, 25, 6],
    [BEACH, 20, 6], [BEACH, 20, 7], [BEACH, 20, 6],
]
DRY_GOALS = {BEACH+':24,21', BEACH+':25,6', BEACH+':20,6'}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_report(report, directory, rom_sha256=None):
    directory = Path(directory)
    assert report['kind'] == 'one-south-surf-link-native' and report['passed'] is True
    for value in (report['rom_sha256'], report['elf_sha256']):
        assert isinstance(value, str) and len(value) == 64 and set(value) <= set('0123456789abcdef')
    if rom_sha256 is not None:
        assert report['rom_sha256'] == rom_sha256
    for key in ('native_validation_performed', 'initial_party_progress_encounter_suppression_and_placement_are_fixtures',
                'after_placement_movement_controllers_only', 'gameplay_scripts_not_injected_after_placement',
                'native_hardware_bg_oam_vram_palette_and_scanout_checked', 'old_source_and_rom_unchanged'):
        assert report[key] is True, key
    assert report['source_overlay_inputs_checked'] >= 14
    assert len(report['source_overlay_marker_sha256']) == 64
    assert report['full_campaign_playthrough'] is False
    assert report['fixtures'] == [dict(map=START[0], tile=START[1:], surfing=True)]
    images = verify_captures(report['captures'], directory)
    captures = {row['file']: row['sha256'] for row in report['captures']}
    assert len(captures) == len(report['captures'])
    assert report['goals'] == GOALS
    assert len(report['arrivals']) == len(GOALS)
    for index, (row, goal) in enumerate(zip(report['arrivals'], GOALS)):
        assert row['goal'] == goal
        state = row['player']
        assert [state['map'], *state['tile']] == goal
        expected_surf = goal[0]+':'+','.join(map(str, goal[1:])) not in DRY_GOALS
        assert state['surfing'] is expected_surf
        assert state['elevation'] == (1 if expected_surf else 3)
        assert state['active_surf_blobs'] == int(expected_surf)
        assert state['sprite_visible'] is state['object_visible'] is True
        assert row['capture']['file'] == f'route-{index:02d}.png'
        assert captures[row['capture']['file']] == row['capture']['sha256']
        if not expected_surf:
            verify_native_avatar_pixels(row['avatar_pixels'], images[row['capture']['file']])
    transitions = report['transitions']
    assert transitions == [
        dict(source=[BEACH, 4, 47], destination=[PASSAGE, 4, 0]),
        dict(source=[PASSAGE, 4, 31], destination=[SEA, 66, 0]),
        dict(source=[SEA, 66, 0], destination=[PASSAGE, 4, 31]),
        dict(source=[PASSAGE, 4, 0], destination=[BEACH, 4, 47])]
    gps = report['gps_samples']
    # Bind distance to this route rather than an estimated arbitrary count.
    # Each physical crossing costs one step; local legs need at least their
    # Manhattan distance. Actual obstacles may require a longer walk.
    previous = START
    minimum_steps = 0
    crossings = iter(transitions)
    for goal in GOALS:
        if previous[0] != goal[0]:
            crossing = next(crossings)
            assert crossing['source'][0] == previous[0]
            assert crossing['destination'][0] == goal[0]
            minimum_steps += sum(abs(a-b) for a, b in zip(previous[1:], crossing['source'][1:]))+1
            previous = crossing['destination']
        minimum_steps += sum(abs(a-b) for a, b in zip(previous[1:], goal[1:]))
        previous = goal
    assert report['walked_tiles'] >= minimum_steps
    assert len(gps) == report['walked_tiles']+1
    assert gps[0]['map'] == BEACH and gps[0]['tile'] == START[1:]
    # Every required turn must also occur in the continuous GPS trajectory;
    # screenshots of separately placed waypoints cannot satisfy this proof.
    pending = iter(GOALS)
    goal = next(pending, None)
    for row in gps:
        if goal == [row['map'], *row['tile']]:
            goal = next(pending, None)
    assert goal is None, ('Missing ordered route waypoint', goal)
    assert sum(row['seam'] for row in gps) == 4
    observed_seams = []
    for previous, row in zip(gps, gps[1:]):
        delta = max(abs(a-b) for a, b in zip(previous['marker'], row['marker']))
        assert row['delta'] == delta <= 2
        assert row['seam'] is (row['map'] != previous['map'])
        if row['seam']:
            assert delta == 0
            observed_seams.append(dict(source=[previous['map'], *previous['tile']],
                                       destination=[row['map'], *row['tile']]))
        else:
            assert sum(abs(a-b) for a, b in zip(previous['tile'], row['tile'])) == 1
    assert observed_seams == transitions
    assert report['maximum_gps_step'] == max(row.get('delta', 0) for row in gps)
    assert report['maximum_seam_delta'] == 0
    assert len(report['surf_prompts']) >= 2
    assert [BEACH, 20, 6] in report['surf_prompts']
    assert len(report['boundary_bumps']) == 2
    for row, x, direction in zip(report['boundary_bumps'], (0, 7), (32, 16)):
        assert row['reef_cell'] == [x, 16] and row['direction_key'] == direction
        assert row['before'] == row['after']
        assert row['before']['map'] == PASSAGE and row['before']['surfing'] is True
        assert row['before']['tile'] == [1 if x == 0 else 6, 16]
        assert row['observation_player']['map'] == PASSAGE
        assert row['observation_player']['tile'] == [2 if x == 0 else 5, 16]
        assert row['collision'] == 1 and row['held_input_frames'] == 120
        assert row['native_directional_input_blocked'] is True
        verify_pixels(row['pixels'], row['capture'], captures, images, [x, 16], 0x243)
    views = report['terrain_views']
    expected_views = {
        'west-cliff': [(7, 37, 0x117), (6, 38, 0x128), (7, 38, 0x73), (7, 40, 0x7B)],
        'east-cliff': [(32, 37, 0x11F), (33, 38, 0x129), (32, 38, 0x75), (32, 40, 0x7D)],
        'top-from-beach': [(0, 48, 0x243), (3, 48, 0x12B), (7, 48, 0x243)],
        'top-from-passage': [(0, 0, 0x243), (3, 0, 0x12B), (7, 0, 0x243)],
        'bottom-from-passage': [(0, 32, 0x243), (4, 32, 0x12B), (7, 32, 0x243)],
        'bottom-from-sea': [(62, 0, 0x243), (66, 0, 0x12B), (69, 0, 0x243), (64, 1, 0x12B)],
    }
    view_points = {'west-cliff': [BEACH, 4, 39], 'east-cliff': [BEACH, 35, 39],
                   'top-from-beach': [BEACH, 4, 45], 'top-from-passage': [PASSAGE, 4, 2],
                   'bottom-from-passage': [PASSAGE, 4, 29], 'bottom-from-sea': [SEA, 66, 2]}
    assert len(views) == len(expected_views)
    assert {row['label'] for row in views} == set(expected_views)
    for view in views:
        assert [view['player']['map'], *view['player']['tile']] == view_points[view['label']]
        assert view['player']['surfing'] is True and view['player']['elevation'] == 1
        assert view['pixels']['map'] == view['player']['map']
        requested = expected_views[view['label']]
        assert len(view['pixels']['cells']) == len(requested)
        for cell, (x, y, mid) in zip(view['pixels']['cells'], requested):
            single = dict(view['pixels'], cells=[cell])
            verify_pixels(single, view['capture'], captures, images, [x, y], mid)
    animation = report['water_animation']
    assert animation['phases_observed'] == list(range(8))
    assert len(animation['source_frames_sha256']) == 8 and len(animation['samples']) == 16
    for row in animation['samples']:
        assert row['matches'] and set(row['matches']) <= set(range(8))
        assert row['vram_sha256'] in [animation['source_frames_sha256'][i] for i in row['matches']]
        assert captures[row['capture']['file']] == row['capture']['sha256']
    assert report['inputs'] and {1, 8, 16, 32, 64, 128} <= {row['key'] for row in report['inputs']}
    for row in report['inputs']:
        assert type(row['frames']) is int and row['frames'] > 0
        assert row['key'] in (0, 1, 2, 8, 16, 32, 64, 128)
    assert report['queries']
    for row in report['queries']:
        assert row['function'].startswith(('MapGridGet', 'MetatileBehavior_Is')) or row['function'] in {
            'GetPlayerFacingDirection', 'IsPlayerFacingSurfableFishableWater', 'PlayerGetElevation', 'JourneyWorldMapPosition'}
    assert len(report['saves']) == 2
    for row, goal in zip(report['saves'], ([PASSAGE, 4, 16], [BEACH, 20, 6])):
        assert row['saved_with_controllers'] is True
        assert 'SaveReturnSuccessCallback' in row['save_menu_callbacks']
        assert [row['player']['map'], *row['player']['tile']] == goal
        battery = directory/row['file']
        assert battery.stat().st_size == row['bytes'] == 131072
        assert digest(battery) == row['sha256']
        expected = dict(map_id=row['map_id'], tile=goal[1:], surfing=goal[0] == PASSAGE,
                        elevation=1 if goal[0] == PASSAGE else 3)
        verify_cold(row['cold_continue'], directory/row['cold_directory'], battery,
                    report['rom_sha256'], expected, avatar=goal[0] == BEACH)
        component = directory/row['cold_directory']/'cold-boot.json'
        assert digest(component) == row['cold_report_sha256']
    assert report['components'] == [dict(file=row['cold_directory']+'/cold-boot.json',
                                        sha256=row['cold_report_sha256']) for row in report['saves']]
    assert report['battery_saves'] == [{k: row[k] for k in ('file', 'bytes', 'sha256')}
                                      for row in report['saves']]
    expected_images = {row['capture']['file'] for row in report['arrivals']+views+report['boundary_bumps']}
    expected_images.update(row['capture']['file'] for row in animation['samples'])
    expected_images.update(row['capture']['file'] for row in report['saves'])
    assert set(images) == expected_images
    return True


def run(source, library, output, parent_source=None):
    source, library, output = map(lambda p: Path(p).resolve(), (source, library, output))
    output.mkdir(parents=True, exist_ok=True)
    rom_sha, elf_sha = digest(source/'pokeemerald.gba'), digest(source/'pokeemerald.elf')
    marker_path = source/'.journey-generated-area-review'
    marker_sha = digest(marker_path)
    source_hashes = json.loads(marker_path.read_bytes())['prepared_sha256']
    assert all(digest(source/name) == expected for name, expected in source_hashes.items())
    ns = bootstrap(source, library, output, {BEACH, SEA, PASSAGE})
    lib, symbols = ns['lib'], ns['s']
    original_step, original_native, original_warp, original_script = (
        ns[k] for k in ('step', 'native', 'warp', 'script'))
    inputs, queries, captures, arrivals, views, bumps, gps, saves = [], [], [], [], [], [], [], []
    active, depth, phase = True, 0, 'bootstrap'

    def step(count, key=0):
        if not active:
            if inputs and inputs[-1]['key'] == key and inputs[-1]['phase'] == phase:
                inputs[-1]['frames'] += count
            else:
                inputs.append(dict(phase=phase, frames=count, key=key))
        original_step(count, key)

    def native(name, *values, **kwargs):
        nonlocal depth
        if not active:
            assert name.startswith(('MapGridGet', 'MetatileBehavior_Is')) or name in {
                'GetPlayerFacingDirection', 'IsPlayerFacingSurfableFishableWater',
                'PlayerGetElevation', 'JourneyWorldMapPosition'}, ('Forbidden midtrip native call', name)
            queries.append(dict(phase=phase, function=name, arguments=list(values)))
        depth += 1
        try:
            return original_native(name, *values, **kwargs)
        finally:
            depth -= 1

    def script(*values, **kwargs):
        assert active or depth, 'Gameplay script injected after initial placement'
        return original_script(*values, **kwargs)

    def warp(*values, **kwargs):
        assert active, 'Midtrip travel fixture attempted'
        return original_warp(*values, **kwargs)

    ns.update(step=step, native=native, script=script, warp=warp,
              walk_transition_pictures=False, walk_max_ticks=4000)

    def capture(label):
        ns['picture'](label)
        row = dict(file=label+'.png', sha256=digest(output/(label+'.png')))
        captures.append(row)
        return row

    def state():
        row = ns['player_state']()
        assert row['sprite_visible'] is row['object_visible'] is True
        assert row['elevation'] == (1 if row['surfing'] else 3)
        player_id = lib.read8(symbols['gPlayerAvatar']+5)
        row['active_surf_blobs'] = sum(bool(lib.read8(symbols['gSprites']+68*i+0x3E)&1)
            and (lib.read32(symbols['gSprites']+68*i+0x1C)&~1) == symbols['UpdateSurfBlobFieldEffect']
            and lib.read16(symbols['gSprites']+68*i+0x32) == player_id for i in range(64))
        assert row['active_surf_blobs'] == int(row['surfing'])
        return row

    def gps_sample(point, seam=False):
        packed = native('JourneyWorldMapPosition')
        row = dict(map=point[0], tile=list(point[1:]), marker=[packed&255, packed >> 8], seam=seam)
        if gps:
            row['delta'] = max(abs(a-b) for a, b in zip(row['marker'], gps[-1]['marker']))
            assert row['delta'] <= 2, ('GPS jumped', gps[-1], row)
            if seam:
                assert row['delta'] == 0, ('GPS seam changed', gps[-1], row)
        gps.append(row)

    def view(label, requested):
        player = state()
        pixels = observe_cells(ns, requested)
        views.append(dict(label=label, player=player, pixels=pixels, capture=capture(label)))

    def save(label):
        before = state()
        ns['press'](8)
        step(90)
        count = lib.read8(symbols['sNumStartMenuActions'])
        actions = [lib.read8(symbols['sCurrentStartMenuActions']+i) for i in range(count)]
        assert actions.count(5) == 1, ('SAVE absent from native start menu', actions)
        target = actions.index(5)
        for _ in range(12):
            if lib.read8(symbols['sStartMenuCursorPos']) == target:
                break
            ns['press'](128)
        assert lib.read8(symbols['sStartMenuCursorPos']) == target
        ns['press'](1)
        seen = set()
        by_address = {value: name for name, value in symbols.items() if name.startswith('Save')}
        for _ in range(120):
            callback = lib.read32(symbols['sSaveDialogCallback'])&~1
            seen.add(by_address.get(callback, hex(callback)))
            if callback == symbols['SaveOverwriteInputCallback']:
                ns['press'](64)
            if 'SaveReturnSuccessCallback' in seen and not lib.read8(symbols['sLockFieldControls']):
                break
            ns['press'](1)
        else:
            raise AssertionError(('Native controller save did not finish', seen))
        step(90)
        assert state() == before
        battery = output/(label+'.sav')
        lib.export_save.argtypes = [ctypes.c_char_p]
        lib.export_save.restype = ctypes.c_int
        assert lib.export_save(str(battery).encode()) and battery.stat().st_size == 131072
        saves.append(dict(file=battery.name, bytes=131072, sha256=digest(battery), player=before,
                          map_id=list(ns['map_id'](before['map'])), saved_with_controllers=True,
                          save_menu_callbacks=sorted(seen), capture=capture(label)))

    animation = None
    try:
        original_native('DisableWildEncounters', 1)
        for n in ns['maps']:
            width = ns['blocks'][n][0]
            for event in ns['maps'][n]['warp_events']:
                ns['full_passable'][n].discard(event['y']*width+event['x'])
        ns['warps'] = {n: {} for n in ns['maps']}
        ns['set_passability']()
        original_warp(*START)
        step(90)
        if not lib.read8(symbols['gPlayerAvatar'])&8:
            original_native('SetPlayerAvatarTransitionFlags', 8)
            step(90)
        active = False
        assert [state()['map'], *state()['tile']] == START
        assert state()['surfing'] is True
        gps_sample(START)
        ns['walk_observer'] = lambda before, after: gps_sample(after, before[0] != after[0])
        for index, goal in enumerate(GOALS):
            phase = 'route-'+str(index)
            ns['walk'](tuple(goal))
            step(60)
            player = state()
            assert [player['map'], *player['tile']] == goal
            arrival = dict(goal=goal, player=player)
            if not player['surfing']:
                arrival['avatar_pixels'] = ns['visible_avatar_pixels']()
            arrival['capture'] = capture(f'route-{index:02d}')
            arrivals.append(arrival)
            if index == 0:
                view('west-cliff', [(7, 37, 0x117), (6, 38, 0x128), (7, 38, 0x73), (7, 40, 0x7B)])
            elif index == 1:
                view('top-from-beach', [(0, 48, 0x243), (3, 48, 0x12B), (7, 48, 0x243)])
            elif index == 2:
                view('top-from-passage', [(0, 0, 0x243), (3, 0, 0x12B), (7, 0, 0x243)])
            elif index == 3:
                save('vertical-route-saved')
                from integrated_ocean_seams import _animation_frames
                frames = _animation_frames(source)
                samples, seen = [], set()
                for sample in range(16):
                    step(8)
                    raw = b''.join(bytes(lib.read8(0x06000000+slot*32+i) for i in range(32)) for slot in (454, 455))
                    matches = [i for i, frame in enumerate(frames) if frame == raw]
                    assert matches, ('New route lost native water animation', sample)
                    seen.update(matches)
                    samples.append(dict(matches=matches, vram_sha256=hashlib.sha256(raw).hexdigest(),
                                        capture=capture(f'new-sea-phase-{sample:02d}')))
                assert seen == set(range(8))
                animation = dict(samples=samples, phases_observed=sorted(seen),
                                 source_frames_sha256=[hashlib.sha256(frame).hexdigest() for frame in frames])
            elif index in (4, 6):
                x, direction = (0, 32) if index == 4 else (7, 16)
                before = state()
                collision = native('MapGridGetCollisionAt', x+7, 16+7)
                assert collision == 1
                step(120, direction)
                step(60)
                after = state()
                assert before == after, ('Native reef bump moved player', before, after)
                bumps.append(dict(reef_cell=[x, 16], direction_key=direction, collision=collision,
                                  before=before, after=after, held_input_frames=120,
                                  native_directional_input_blocked=True))
            elif index in (5, 7):
                row = bumps[-1]
                row.update(observation_player=state(), pixels=observe_cells(ns, [(*row['reef_cell'], 0x243)]),
                           capture=capture('new-route-reef-'+str(len(bumps))))
            elif index == 8:
                view('bottom-from-passage', [(0, 32, 0x243), (4, 32, 0x12B), (7, 32, 0x243)])
            elif index == 9:
                view('bottom-from-sea', [(62, 0, 0x243), (66, 0, 0x12B), (69, 0, 0x243), (64, 1, 0x12B)])
            elif index == 19:
                view('east-cliff', [(32, 37, 0x11F), (33, 38, 0x129), (32, 38, 0x75), (32, 40, 0x7D)])
            print('One south native route:', index, goal, 'Surf' if player['surfing'] else 'land', flush=True)
        assert state()['surfing'] is False
        save('pier-return-saved')
        walked, transitions, prompts = ns['walked'], ns['transitions'], ns['surf_prompts']
    finally:
        lib.stop()
    components = []
    for index, row in enumerate(saves):
        expected = dict(map_id=row['map_id'], tile=row['player']['tile'],
                        surfing=row['player']['surfing'], elevation=row['player']['elevation'])
        folder = 'cold-continue-'+str(index)
        row['cold_directory'] = folder
        row['cold_continue'] = cold_continue(source, library, output/folder, output/row['file'], expected)
        row['cold_report_sha256'] = digest(output/folder/'cold-boot.json')
        components.append(dict(file=folder+'/cold-boot.json', sha256=row['cold_report_sha256']))
    assert digest(source/'pokeemerald.gba') == rom_sha and digest(source/'pokeemerald.elf') == elf_sha
    assert digest(marker_path) == marker_sha
    assert all(digest(source/name) == expected for name, expected in source_hashes.items())
    report = dict(kind='one-south-surf-link-native', passed=True, rom_sha256=rom_sha, elf_sha256=elf_sha,
                  native_validation_performed=True, full_campaign_playthrough=False,
                  fixtures=[dict(map=START[0], tile=START[1:], surfing=True)],
                  goals=GOALS, arrivals=arrivals, transitions=transitions, walked_tiles=walked,
                  gps_samples=gps, maximum_gps_step=max(row.get('delta', 0) for row in gps),
                  maximum_seam_delta=max(row['delta'] for row in gps if row['seam']),
                  surf_prompts=prompts, boundary_bumps=bumps, terrain_views=views,
                  water_animation=animation, saves=saves, captures=captures, inputs=inputs,
                  queries=queries, components=components,
                  source_overlay_inputs_checked=len(source_hashes), source_overlay_marker_sha256=marker_sha,
                  battery_saves=[{k: row[k] for k in ('file', 'bytes', 'sha256')} for row in saves],
                  initial_party_progress_encounter_suppression_and_placement_are_fixtures=True,
                  after_placement_movement_controllers_only=True,
                  gameplay_scripts_not_injected_after_placement=True,
                  native_hardware_bg_oam_vram_palette_and_scanout_checked=True,
                  old_source_and_rom_unchanged=True)
    verify_report(report, output, rom_sha)
    (output/'one-south-surf-link-native.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--library', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.source, args.library, args.output)
