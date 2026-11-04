"""Record the real faulty Cinnabar door exit as a legacy battery.

This diagnostic must fail on the repaired ROM. The initial dry map placement,
party/progress and encounter suppression are fixtures; entering/exiting the
terminal and reaching the invalid elevation use only controller input.
"""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--library', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    path = ROOT/'tools/hoenn/validate_integrated_piers.py'
    code = path.read_text().split('\nchecks = []\ntry:')[0].replace(
        'names = sorted(names)', "names = ['CinnabarIsland_Frlg','JourneyCinnabarHarbor']")
    sys.argv = [str(path), '--source', str(args.source), '--library',
                str(args.library), '--output', str(args.output)]
    ns = {'__file__': str(path), '__name__': 'cinnabar_door_legacy_fixture'}
    exec(compile(code, str(path), 'exec'), ns)
    lib, native, step, walk, warp = (ns[k] for k in
                                    ('lib', 'native', 'step', 'walk', 'warp'))
    try:
        native('DisableWildEncounters', 1)
        for name, valid in ns['full_passable'].items():
            words = ns['blocks'][name][2]
            ns['passable'][name] = {i for i in valid if words[i] >> 12 == 15
                or not ns['water_behaviors'][ns['behaviors'][name][i]]}
        ns['_planned_goal'], ns['_planned_keys'] = None, {}
        warp('CinnabarIsland_Frlg', 11, 14)
        native('SetPlayerAvatarTransitionFlags', 1)
        step(90)
        initial = ns['player_state']()
        assert initial['elevation'] == 3 and not initial['surfing']
        walk(('JourneyCinnabarHarbor', 11, 13))
        step(90)
        interior = ns['player_state']()
        assert interior['elevation'] == 3 and not interior['surfing']
        walk(('CinnabarIsland_Frlg', 7, 15))
        step(150)
        broken = ns['player_state']()
        assert broken['tile'] == [7, 15] and broken['elevation'] == 0 and not broken['surfing'], broken
        assert broken['tile_elevation'] == 15 and broken['priority'] == 2
        ns['picture']('faulty-door-exit-before-save')
        assert native('TrySavingData', 0, max_frames=6000) == 1
        battery = args.output/'cinnabar-door-level0.sav'
        lib.export_save.argtypes = [ctypes.c_char_p]
        lib.export_save.restype = ctypes.c_int
        assert lib.export_save(str(battery.resolve()).encode())
        assert battery.stat().st_size == 131072
        report = dict(kind='cinnabar-door-parent-regression', passed=True,
            rom_sha256=hashlib.sha256((args.source/'pokeemerald.gba').read_bytes()).hexdigest(),
            elf_sha256=hashlib.sha256((args.source/'pokeemerald.elf').read_bytes()).hexdigest(),
            initial=initial, interior=interior, broken=broken,
            actual_terminal_entry_and_exit_reproduce_level0=True,
            no_midtrip_coordinate_elevation_or_avatar_writes=True,
            initial_placement_party_and_progress_are_fixtures=True,
            movement_fixture_random_encounters_disabled=True,
            battery=battery.name, battery_sha256=hashlib.sha256(battery.read_bytes()).hexdigest(),
            map_id=list(ns['location']()), tile=list(ns['position']()),
            captures=list(ns['captures'].values()))
        (args.output/'cinnabar-door-level0.json').write_text(json.dumps(report, indent=2)+'\n')
        print('Actual faulty door exit saved:', battery, flush=True)
        # Preserve a second, distinct real battery after the faulty door level
        # has allowed the pedestrian to enter water. Do not synthesize either
        # the elevation or Surf bit: they are the result of these held keys.
        walk(('CinnabarIsland_Frlg', 11, 15))
        step(60)
        for _ in range(120):
            if ns['position']() == (12, 15):
                break
            step(1, 16)
        else:
            raise AssertionError(('Parent no longer allows walking into water', ns['player_state']()))
        step(60)
        water = ns['player_state']()
        assert water['tile'] == [12, 15] and water['tile_elevation'] == water['elevation'] == 1
        assert not water['surfing'], water
        ns['picture']('faulty-door-walking-water-before-save')
        assert native('TrySavingData', 0, max_frames=6000) == 1
        water_battery = args.output/'cinnabar-door-walking-water.sav'
        assert lib.export_save(str(water_battery.resolve()).encode())
        assert water_battery.stat().st_size == 131072
        water_report = dict(report, kind='cinnabar-door-water-parent-regression',
            broken=water, bridge_before_water=broken,
            walking_water_reproduced_by_controller=True,
            battery=water_battery.name,
            battery_sha256=hashlib.sha256(water_battery.read_bytes()).hexdigest(),
            map_id=list(ns['location']()), tile=list(ns['position']()),
            captures=list(ns['captures'].values()))
        (args.output/'cinnabar-door-walking-water.json').write_text(json.dumps(water_report, indent=2)+'\n')
        print('Actual faulty door walking-water saved:', water_battery, flush=True)
    finally:
        lib.stop()


if __name__ == '__main__':
    main()
