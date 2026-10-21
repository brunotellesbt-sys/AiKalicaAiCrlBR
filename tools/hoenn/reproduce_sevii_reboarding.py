"""Reproduce the seven blocked Surf returns on the immutable layer-161 ROM.

The initial water placement and Surf mode of each independent case are
fixtures. Approaching the adjacent dry boardwalk uses only the D-pad.
This intentionally emits passed:false and cannot seal a current release.
"""
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
bootstrap = (ROOT / 'tools/hoenn/validate_trainer_levels.py').read_text().split('\nchecks=[]')[0]
exec(compile(bootstrap, __file__, 'exec'))
assert not (source / '.journey-sevii-integrated-piers').exists(), 'Use the immutable defective baseline'
initial_sha = hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest()
piers = json.loads((source / '.journey-dewford-coast-safety').read_text())['piers']
names = sorted({segment['map'] for row in piers['town_bridges']
                for segment in row['deck_segments']})
allowed = set()
walk_surf_under_bridges = True
native('RtcInitLocalTimeOffset', 12, 0)
native('VarSet', 0x40FE, 7)
for flag_value in hoenn_flags + kanto_flags:
    rawflag(flag_value, True)
constants = (source / 'include/constants/vars.h').read_text()
for variable, value in [('VAR_MAP_SCENE_ONE_ISLAND_HARBOR', 3),
                         ('VAR_MAP_SCENE_FOUR_ISLAND', 1)]:
    native('VarSet', int(re.search(r'^#define\s+' + variable + r'\s+(0x\w+)',
                                 constants, re.M)[1], 16), value)
exec(compile((ROOT / 'tools/hoenn/native_water_walk.py').read_text(),
             'blocked-reboarding-native-walker', 'exec'))
checks = []
for row in piers['town_bridges']:
    candidates = []
    for segment in row['deck_segments']:
        name = segment['map']
        left, top, width, height = segment['footprint']
        map_width, map_height, tiles = blocks[name]
        for y in range(top, top + height):
            for x in range(left, left + width):
                if tiles[y * map_width + x] >> 12 != 3 or tiles[y * map_width + x] & 0xC00:
                    continue
                for dx, dy, key in keys:
                    sx, sy = x - dx, y - dy
                    if not (0 <= sx < map_width and 0 <= sy < map_height):
                        continue
                    value = tiles[sy * map_width + sx]
                    if (value >> 12 == 1 and not value & 0xC00
                            and water_behaviors[behaviors[name][sy * map_width + sx]]):
                        candidates.append(((name, sx, sy), (name, x, y), key))
    assert candidates, (row['island'], 'No native water-to-dry-deck approach')
    water, dry, direction = candidates[len(candidates) // 2]
    warp(*water)
    native('SetPlayerAvatarTransitionFlags', 8)
    step(90)
    before = (location(), position())
    assert lib.read8(s['gPlayerAvatar']) & 8
    assert native('PlayerGetElevation') == 1
    step(90, direction)
    step(45)
    assert (location(), position()) == before, (row['island'], 'Baseline did not reproduce blocked return')
    assert lib.read8(s['gPlayerAvatar']) & 8
    assert native('PlayerGetElevation') == 1
    picture(row['island'].lower() + '-blocked-surf-return')
    checks.append(dict(island=row['island'], water=list(water), dry_pier=list(dry),
                       inward_key=direction, surfing_before_and_after=True,
                       controller_return_blocked=True,
                       no_coordinates_or_elevation_writes_during_approach=True))
    print('Layer-161 blocked Surf return reproduced:', row['island'], flush=True)
assert len(checks) == 7
assert hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest() == initial_sha
lib.stop()
(args.output / 'blocked-surf-return-reproduced.json').write_text(json.dumps(dict(
    passed=False, expected_broken_baseline=True, bug_reproduced=True,
    rom_sha256=initial_sha, all_seven_town_pier_returns_blocked=True, ports=checks,
    water_placements_and_initial_surf_mode_are_fixtures=True,
    no_midapproach_warps_or_coordinate_or_elevation_writes=True), indent=2) + '\n')
