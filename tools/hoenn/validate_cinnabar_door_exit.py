"""Check Cinnabar's high pier after a real terminal door round trip.

The first dry placement, party/progress and encounter suppression are declared
movement fixtures. No player coordinates, elevations or avatar modes are
written after that placement. Door entry/exit, blocked water attempts, native
Surf and reboarding all use controller input.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
TOWN = 'CinnabarIsland_Frlg'
INTERIOR = 'JourneyCinnabarHarbor'
DECK = tuple([(x, 15) for x in range(6, 12)] +
             [(x, y) for y in (16, 17) for x in (9, 10)])


def legacy_continue(source, library, output, battery, manifest, pixel_namespace):
    """Cold-continue the actual pre-repair door battery without game writes."""
    expected = json.loads(Path(manifest).read_bytes())
    assert expected['actual_terminal_entry_and_exit_reproduce_level0']
    assert expected['broken']['elevation'] == 0 and expected['broken']['tile_elevation'] == 15
    assert hashlib.sha256(Path(battery).read_bytes()).hexdigest() == expected['battery_sha256']
    path = ROOT/'tools/hoenn/validate_cold_boot.py'
    code = path.read_text()
    anchor = "                    result = dict(bundled_save_continue_to_field=True, field_map=[lib.read8(save+4), lib.read8(save+5)])"
    assert code.count(anchor) == 1
    observer = '''
                    PIXEL_NAMESPACE['lib'] = lib
                    PIXEL_NAMESPACE['s'] = symbols
                    def state():
                        obj = symbols['gObjectEvents'] + 36 * lib.read8(symbols['gPlayerAvatar'] + 5)
                        sprite = symbols['gSprites'] + 68 * lib.read8(obj+35)
                        return dict(tile=[lib.read16(obj+16)-7,lib.read16(obj+18)-7],
                                    surfing=bool(lib.read8(symbols['gPlayerAvatar']) & 8),
                                    elevation=lib.read8(obj+11)&15,
                                    priority=(lib.read16(sprite+4)>>10)&3)
                    before = state()
                    assert result['field_map'] == EXPECTED['map_id'], result
                    assert before['tile'] == EXPECTED['tile'] == [7,15], before
                    assert before['elevation'] == 3 and not before['surfing'] and before['priority'] == 1, before
                    before['native_avatar_pixels'] = PIXEL_NAMESPACE['visible_avatar_pixels']()
                    picture('legacy-bridge-restored')
                    for _ in range(180):
                        if state()['tile'] == [11,15]:
                            break
                        step(1,16)
                    else:
                        raise AssertionError(('Legacy bridge controller walk failed',state()))
                    step(60)
                    step(90,16)
                    step(45)
                    blocked = state()
                    assert blocked['tile'] == [11,15] and blocked['elevation'] == 3 and not blocked['surfing'], blocked
                    assert blocked['priority'] == 1, blocked
                    blocked['native_avatar_pixels'] = PIXEL_NAMESPACE['visible_avatar_pixels']()
                    picture('legacy-bridge-water-blocked')
                    result.update(legacy_bridge_level_restored=True,
                                  legacy_water_entry_blocked_by_controller=True,
                                  legacy_initial_state=before,legacy_final_state=blocked,
                                  no_game_memory_writes=True)
'''
    namespace = {'__file__': str(path), '__name__': 'cinnabar_legacy_cold_boot',
                 'EXPECTED': expected, 'PIXEL_NAMESPACE': pixel_namespace}
    exec(compile(code.replace(anchor, anchor+observer), str(path), 'exec'), namespace)
    result = namespace['validate'](source, library, output, battery)
    result.update(legacy_parent_rom_sha256=expected['rom_sha256'],
                  legacy_actual_door_exit_battery_tested=True)
    return result


def legacy_water_continue(source, library, output, battery, manifest, pixel_namespace):
    """Continue the actual walking-water battery and reboard by controller."""
    expected = json.loads(Path(manifest).read_bytes())
    assert expected['actual_terminal_entry_and_exit_reproduce_level0']
    assert expected['walking_water_reproduced_by_controller']
    assert expected['bridge_before_water']['elevation'] == 0
    assert expected['broken']['elevation'] == expected['broken']['tile_elevation'] == 1
    assert not expected['broken']['surfing'] and expected['tile'] == [12, 15]
    assert hashlib.sha256(Path(battery).read_bytes()).hexdigest() == expected['battery_sha256']
    path = ROOT/'tools/hoenn/validate_cold_boot.py'
    code = path.read_text()
    anchor = "                    result = dict(bundled_save_continue_to_field=True, field_map=[lib.read8(save+4), lib.read8(save+5)])"
    assert code.count(anchor) == 1
    observer = '''
                    PIXEL_NAMESPACE['lib'] = lib
                    PIXEL_NAMESPACE['s'] = symbols
                    def state():
                        obj = symbols['gObjectEvents'] + 36 * lib.read8(symbols['gPlayerAvatar'] + 5)
                        sprite = symbols['gSprites'] + 68 * lib.read8(obj+35)
                        return dict(tile=[lib.read16(obj+16)-7,lib.read16(obj+18)-7],
                                    surfing=bool(lib.read8(symbols['gPlayerAvatar']) & 8),
                                    elevation=lib.read8(obj+11)&15,
                                    priority=(lib.read16(sprite+4)>>10)&3)
                    before = state()
                    assert result['field_map'] == EXPECTED['map_id'], result
                    assert before['tile'] == EXPECTED['tile'] == [12,15], before
                    assert before['elevation'] == 1 and before['surfing'] and before['priority'] == 2, before
                    picture('legacy-water-restored-native-surf')
                    movements = []
                    route = [([11,15],32),([10,15],32),([9,15],32),([8,15],32),
                             ([8,16],128),([8,17],128),([8,18],128),([9,18],16),([9,17],64)]
                    for index,(goal,key) in enumerate(route):
                        initial = state()
                        for held in range(180):
                            if state()['tile'] == goal:
                                break
                            step(1,key)
                        else:
                            raise AssertionError(('Legacy water controller return failed',goal,state()))
                        step(60)
                        after = state()
                        final = index == len(route)-1
                        assert after['tile'] == goal and after['surfing'] is not final, after
                        assert after['elevation'] == (3 if final else 1), after
                        assert after['priority'] == (1 if final else 2), after
                        movements.append(dict(initial=initial,returned=after,direction_key=key,
                                              held_input_frames=held,controller_input_only=True))
                    returned = state()
                    returned['native_avatar_pixels'] = PIXEL_NAMESPACE['visible_avatar_pixels']()
                    picture('legacy-water-reboarded-dry-pier')
                    result.update(legacy_walking_water_recovers_native_surf=True,
                                  legacy_controller_returned_to_pier=True,
                                  legacy_initial_state=before,legacy_final_state=returned,
                                  legacy_controller_movements=movements,
                                  no_game_memory_writes=True)
'''
    namespace = {'__file__': str(path), '__name__': 'cinnabar_legacy_water_cold_boot',
                 'EXPECTED': expected, 'PIXEL_NAMESPACE': pixel_namespace}
    exec(compile(code.replace(anchor, anchor+observer), str(path), 'exec'), namespace)
    result = namespace['validate'](source, library, output, battery)
    result.update(legacy_parent_rom_sha256=expected['rom_sha256'],
                  legacy_actual_door_to_walking_water_battery_tested=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--library', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--legacy-battery', type=Path)
    parser.add_argument('--legacy-manifest', type=Path)
    parser.add_argument('--coldboot-library', type=Path)
    parser.add_argument('--legacy-water-battery', type=Path)
    parser.add_argument('--legacy-water-manifest', type=Path)
    args = parser.parse_args()
    assert bool(args.legacy_battery) == bool(args.legacy_manifest) == bool(args.coldboot_library)
    assert bool(args.legacy_water_battery) == bool(args.legacy_water_manifest)
    assert not args.legacy_water_battery or args.coldboot_library
    path = ROOT/'tools/hoenn/validate_integrated_piers.py'
    code = path.read_text().split('\nchecks = []\ntry:')[0]
    assert code.count('names = sorted(names)') == 1
    code = code.replace('names = sorted(names)',
                        "names = ['CinnabarIsland_Frlg','JourneyCinnabarHarbor']")
    sys.argv = [str(path), '--source', str(args.source), '--library',
                str(args.library), '--output', str(args.output)]
    ns = {'__file__': str(path), '__name__': 'cinnabar_door_exit_native'}
    exec(compile(code, str(path), 'exec'), ns)
    lib, native, step, walk, warp = (ns[k] for k in
                                    ('lib', 'native', 'step', 'walk', 'warp'))
    rom_sha = hashlib.sha256((args.source/'pokeemerald.gba').read_bytes()).hexdigest()
    observations, perimeter, underpass = [], [], []

    def record(label, surfing=False, priority=None):
        state = ns['player_state']()
        assert state['surfing'] is surfing, (label, state)
        assert state['elevation'] == (1 if surfing else 3), (label, state)
        if priority is not None:
            assert state['priority'] == priority, (label, state)
        if not surfing:
            try:
                state['native_avatar_pixels'] = ns['visible_avatar_pixels']()
            except AssertionError:
                ns['picture'](label+'-failure')
                raise
        ns['picture'](label)
        state['capture_file'] = label+'.png'
        return state

    def dry_paths():
        for name, valid in ns['full_passable'].items():
            words = ns['blocks'][name][2]
            ns['passable'][name] = {i for i in valid if words[i] >> 12 == 15
                or not ns['water_behaviors'][ns['behaviors'][name][i]]}
        ns['_planned_goal'], ns['_planned_keys'] = None, {}

    def arrive(x, y):
        walk((TOWN, x, y))
        step(60)
        assert ns['location']() == ns['map_id'](TOWN) and ns['position']() == (x, y)

    try:
        native('DisableWildEncounters', 1)
        dry_paths()
        warp(TOWN, 11, 14)
        native('SetPlayerAvatarTransitionFlags', 1)
        step(90)
        initial = record('initial-dry-land', priority=2)
        walk((INTERIOR, 11, 13))
        step(90)
        inside = record('terminal-interior', priority=2)
        arrive(7, 15)
        after_door = record('door-exit-on-high-pier', priority=1)
        for index, (x, y) in enumerate(DECK):
            arrive(x, y)
            observations.append(record('deck-after-door-'+str(index), priority=1))

        # Enumerate all true dry/bridge-to-water edges, not one chosen front.
        width, height, words = ns['blocks'][TOWN]
        deck = set(DECK)
        cases = []
        for x, y in DECK:
            for dx, dy, key in ns['keys']:
                xx, yy = x+dx, y+dy
                if (xx, yy) in deck or not (0 <= xx < width and 0 <= yy < height):
                    continue
                word = words[yy*width+xx]
                behavior = ns['behaviors'][TOWN][yy*width+xx]
                if not word & 0xC00 and ns['water_behaviors'][behavior]:
                    assert word >> 12 == 1, (x, y, xx, yy, hex(word))
                    cases.append((x, y, xx, yy, key))
        assert len(cases) == 9, ('Cinnabar pier perimeter changed', cases)
        for index, (x, y, xx, yy, key) in enumerate(cases):
            arrive(x, y)
            before = ns['player_state']()
            assert before['elevation'] == 3 and not before['surfing']
            assert native('MapGridGetElevationAt', xx+7, yy+7) == 1
            step(90, key)
            step(45)
            after = record('blocked-water-after-door-'+str(index), priority=1)
            assert after['tile'] == [x, y], (before, after)
            perimeter.append(dict(dry=[x, y], water=[xx, yy], key=key,
                                  before=before, after=after,
                                  walking_without_surf_blocked=True))

        # The high bridge must keep its lower Surf passage and native prompt.
        arrive(9, 17)
        ns['set_passability']()
        prompts = len(ns['surf_prompts'])
        arrive(9, 18)
        departure = record('native-surf-departure', surfing=True, priority=2)
        assert len(ns['surf_prompts']) > prompts
        route = [(8, 18), (8, 17), (8, 16), (8, 15)]
        route += [(x, 15) for x in range(7, 5, -1)]
        route += [(x, 15) for x in range(7, 17)]
        route += [(16, 16), (16, 15)]
        route += [(x, 15) for x in range(15, 5, -1)]
        route += [(7, 15), (8, 15), (8, 16), (8, 17), (8, 18), (9, 18)]
        for index, (x, y) in enumerate(route):
            arrive(x, y)
            underpass.append(record('surf-underpass-'+str(index), surfing=True, priority=2))
        arrive(9, 17)
        reboarded = record('native-surf-reboarded', priority=1)
        dry_paths()
        walk((INTERIOR, 11, 13))
        step(90)
        arrive(7, 15)
        repeated_exit = record('door-exit-after-surf-roundtrip', priority=1)
        arrive(11, 15)
        before = ns['player_state']()
        step(90, 16)
        step(45)
        final = record('final-bridge-water-blocked', priority=1)
        assert final['tile'] == before['tile'] == [11, 15]
    finally:
        lib.stop()
    assert hashlib.sha256((args.source/'pokeemerald.gba').read_bytes()).hexdigest() == rom_sha
    report = dict(kind='cinnabar-door-exit', passed=True, rom_sha256=rom_sha,
        elf_sha256=hashlib.sha256((args.source/'pokeemerald.elf').read_bytes()).hexdigest(),
        compiled_rom=True, native_validation_performed=True,
        initial=initial, interior=inside, door_exit=after_door,
        all_ten_dry_pier_cells=observations, perimeter=perimeter,
        perimeter_edges=len(perimeter), departure=departure,
        native_underpass_route=[list(p) for p in route], underpass=underpass,
        reboarded=reboarded, repeated_door_exit=repeated_exit, final=final,
        captures=list(ns['captures'].values()),
        controller_terminal_entry_and_exit=True,
        dry_placement_does_not_replace_actual_door_exit=True,
        all_exposed_pier_water_edges_block_pedestrians=True,
        full_avatar_vram_pixels_after_door_exit=True,
        native_surf_departure_underpass_and_reboard=True,
        no_midtrip_coordinate_elevation_or_avatar_writes=True,
        initial_placement_party_and_progress_are_fixtures=True,
        movement_fixture_random_encounters_disabled=True,
        full_campaign_playthrough=False)
    if args.legacy_battery:
        legacy_output = args.output/'legacy-continue'
        report['legacy_continue'] = legacy_continue(args.source, args.coldboot_library,
            legacy_output, args.legacy_battery, args.legacy_manifest, ns)
        report['legacy_actual_door_exit_battery_tested'] = True
        for name in ('battery-continued-to-field.png', 'legacy-bridge-restored.png',
                     'legacy-bridge-water-blocked.png'):
            capture = legacy_output/name
            report['captures'].append(dict(file='legacy-continue/'+name,
                sha256=hashlib.sha256(capture.read_bytes()).hexdigest()))
    else:
        report['legacy_actual_door_exit_battery_tested'] = False
    if args.legacy_water_battery:
        legacy_output = args.output/'legacy-water-continue'
        report['legacy_water_continue'] = legacy_water_continue(args.source, args.coldboot_library,
            legacy_output, args.legacy_water_battery, args.legacy_water_manifest, ns)
        report['legacy_actual_walking_water_battery_tested'] = True
        for name in ('battery-continued-to-field.png', 'legacy-water-restored-native-surf.png',
                     'legacy-water-reboarded-dry-pier.png'):
            capture = legacy_output/name
            report['captures'].append(dict(file='legacy-water-continue/'+name,
                sha256=hashlib.sha256(capture.read_bytes()).hexdigest()))
    else:
        report['legacy_actual_walking_water_battery_tested'] = False
    (args.output/'cinnabar-door-exit.json').write_text(json.dumps(report, indent=2)+'\n')
    print('Cinnabar actual door exit, 10 deck cells, 9 water edges and native Surf roundtrip passed.', flush=True)


if __name__ == '__main__':
    main()
