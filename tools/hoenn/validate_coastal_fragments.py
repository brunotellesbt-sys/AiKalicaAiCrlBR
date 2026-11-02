"""Surf beside every finished cliff-foot fragment in the final compiled ROM.

Party, progress, encounter suppression and initial travel are explicit fixtures.
After initial travel each local roundtrip uses directional input. The two
intact native cliff/rock variants receive an independent compiled-grid check.
"""
import hashlib
import json
from pathlib import Path

from coastal_ecology_cliff_rocks import ANCHORS, COMPLETE, DONOR_MAP, FINISHED
from coastal_ecology_kindle_cliff import CHANGES as KINDLE_CHANGES, ROAD, TOWN, TREASURE
from validate_generated_surface_navigation import place_fixture


ROOT = Path(__file__).resolve().parents[2]
bootstrap = (ROOT / 'tools/hoenn/validate_trainer_levels.py').read_text().split('\nchecks=[]')[0]
exec(compile(bootstrap, __file__, 'exec'))
initial_rom_sha = hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest()
marker = json.loads((source / '.journey-coastal-ecology').read_text())
metadata = marker['cliffs']
kindle_metadata = marker['kindle_cliff']
assert kindle_metadata['changed_cells'] == 26
assert metadata['replaced_top_cells'] == 32
assert len(metadata['fragments']) == 16 and len(metadata['maps']) == 9
assert {(row['map'], *row['anchor']) for row in metadata['fragments']} == {
    (name, x, y) for name, anchors in ANCHORS.items() for x, y in anchors}
layouts = {row['id']: row for row in json.loads((source / 'data/layouts/layouts.json').read_text())['layouts']}
maps = {name: json.loads((source / f'data/maps/{name}/map.json').read_text())
        for name in (*ANCHORS, DONOR_MAP, ROAD, TREASURE)}
captures = []


def capture(label):
    picture(label)
    path = args.output / (label + '.png')
    captures.append(dict(file=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest()))


def state():
    return dict(location=list(location()), tile=list(position()),
                surfing=bool(lib.read8(s['gPlayerAvatar']) & 8),
                elevation=native('PlayerGetElevation'))


def check_grid(name, x, y, words):
    layout = layouts[maps[name]['layout']]
    loaded = lib.read32(s['gMapHeader'])
    assert lib.read32(loaded + 16) == s[layout['primary_tileset']]
    assert lib.read32(loaded + 20) == s[layout['secondary_tileset']]
    loaded_width = lib.read32(s['gBackupMapLayout'])
    loaded_blocks = lib.read32(s['gBackupMapLayout'] + 8)
    for i, expected in enumerate(words):
        xx, yy = x + i % 2, y + i // 2
        actual = lib.read16(loaded_blocks + 2 * (xx + 7 + (yy + 7) * loaded_width))
        assert actual == expected, (name, xx, yy, actual, expected)
        assert native('MapGridGetMetatileIdAt', xx + 7, yy + 7) == expected & 1023
        assert native('MapGridGetElevationAt', xx + 7, yy + 7) == expected >> 12
        assert native('MapGridGetCollisionAt', xx + 7, yy + 7) == (expected >> 10) & 3


def move(goal, key, target_map=None):
    start = position()
    source_location = location()
    target_location = map_id(target_map) if target_map else source_location
    for frames in range(96):
        if position() == goal and location() == target_location:
            step(60 if source_location != target_location else 24)
            assert position() == goal and location() == target_location
            assert lib.read8(s['gPlayerAvatar']) & 8
            return dict(start=list(start), end=list(goal), direction_key=key,
                        source_location=list(source_location), destination_location=list(target_location),
                        held_input_frames=frames, controller_input_only=True,
                        surfing_preserved=True)
        step(1, key)
    capture('coastal-fragments-controller-failure')
    raise AssertionError(('Local Surf roundtrip failed', start, goal, state()))


native('RtcInitLocalTimeOffset', 12, 0)
native('DisableWildEncounters', 1)
team([40, 40, 40])
native('ScriptSetMonMoveSlot', 0, 57, 1)
for badge in hoenn_flags + kanto_flags:
    rawflag(badge, True)
for trainer_id in range(1, 1589):
    rawflag(0x500 + trainer_id, True)
native('VarSet', 0x40FE, 7)
native('VarSet', 0x40FF, 4095)
native('VarSet', 0x4021, 65535)
native('VarSet', 0x4120, 65535)

sites = []
for row in metadata['fragments']:
    name, (x, y) = row['map'], row['anchor']
    assert tuple(word & 1023 for word in row['after']) == FINISHED
    high_fixture = place_fixture(globals(), name, x, y + 1)
    native('SetPlayerAvatarTransitionFlags', 8)
    step(90)
    assert location() == map_id(name) and position() == (x, y + 1), (name, state())
    assert lib.read8(s['gPlayerAvatar']) & 8
    check_grid(name, x, y, row['after'])
    before = state()
    label = f'cliff-foot-{name}-{x}-{y}'
    capture(label + '-before')
    movements = [move((x + 1, y + 1), 16), move((x, y + 1), 32)]
    assert location() == map_id(name)
    check_grid(name, x, y, row['after'])
    capture(label + '-return')
    sites.append(dict(map=name, anchor=[x, y], compiled_words=row['after'],
                      physical_bits_preserved=all(a & ~1023 == b & ~1023
                          for a, b in zip(row['before'], row['after'])),
                      initial_fixture=before, return_state=state(), movements=movements,
                      restored_private_16bit_initial_warp_fixture=high_fixture,
                      native_grid_and_loaded_banks_checked=True))
    print('Native finished cliff foot and Surf roundtrip:', name, x, y, flush=True)

complete = []
for row in metadata['preserved_complete_native_rocks']:
    name, (x, y) = row['map'], row['anchor']
    assert tuple(word & 1023 for word in row['words']) == COMPLETE
    place_fixture(globals(), name, x, y + 2)
    native('SetPlayerAvatarTransitionFlags', 8)
    step(90)
    assert location() == map_id(name)
    check_grid(name, x, y, row['words'])
    capture(f'preserved-cliff-rock-{x}-{y}')
    complete.append(dict(map=name, anchor=[x, y], compiled_words=row['words'],
                         complete_native_variant_preserved=True))


def blocked_probe(key):
    before = state()
    step(48, key)
    step(24)
    after = state()
    assert after == before, (key, before, after)
    return dict(before=before, after=after, direction_key=key,
                held_input_frames=48, blocked=True, controller_input_only=True)


# The cliff continues into One Island through the native left connection.
# Inspect both halves in the actual Kindle Road connection buffer, then Surf
# around its toe and across that seam in both directions using controls.
high_fixture = place_fixture(globals(), ROAD, 7, 137)
assert high_fixture
native('SetPlayerAvatarTransitionFlags', 8)
step(90)
assert location() == map_id(ROAD) and position() == (7, 137)
assert lib.read8(s['gPlayerAvatar']) & 8
kindle_start = state()


def observe_kindle_cells(loaded_map, source_maps):
    assert location() == map_id(loaded_map)
    layout = layouts[maps[loaded_map]['layout']]
    loaded = lib.read32(s['gMapHeader'])
    assert lib.read32(loaded + 16) == s[layout['primary_tileset']]
    assert lib.read32(loaded + 20) == s[layout['secondary_tileset']]
    loaded_width = lib.read32(s['gBackupMapLayout'])
    loaded_blocks = lib.read32(s['gBackupMapLayout'] + 8)
    records = []
    for name in source_maps:
        for x, y, previous, expected in KINDLE_CHANGES[name]:
            xx, yy = (x - 24, y + 120) if name == TOWN and loaded_map == ROAD else (x, y)
            actual = lib.read16(loaded_blocks + 2 * (xx + 7 + (yy + 7) * loaded_width))
            assert actual == expected, (name, x, y, actual, expected)
            assert native('MapGridGetMetatileIdAt', xx + 7, yy + 7) == expected & 1023
            assert native('MapGridGetElevationAt', xx + 7, yy + 7) == expected >> 12
            assert native('MapGridGetCollisionAt', xx + 7, yy + 7) == (expected >> 10) & 3
            records.append(dict(source_map=name, source_tile=[x, y], loaded_map=loaded_map,
                                loaded_tile=[xx, yy], expected=expected, observed=actual,
                                native_grid_checked=True, native_banks_checked=True))
    return records


loaded_cells = observe_kindle_cells(ROAD, (TOWN, ROAD))
assert len(loaded_cells) == 20
kindle_movements = [move((7, 138), 128)]
capture('kindle-cliff-face-native')
west_probe = blocked_probe(32)
kindle_movements.append(move((7, 139), 128))
capture('kindle-cliff-toe-native')
south_probe = blocked_probe(128)
for x in range(6, -1, -1):
    kindle_movements.append(move((x, 139), 32))
kindle_movements.append(move((23, 19), 32, TOWN))
capture('kindle-cliff-town-return-native')
# Visit every cell of the obsolete two-column west foot in Treasure Beach.
# It must load as open sea after traversing the actual town/beach connection.
kindle_movements.append(move((23, 0), 128, TREASURE))
kindle_movements += [move((23, 1), 128), move((23, 2), 128)]
loaded_cells += observe_kindle_cells(TREASURE, (TREASURE,))
capture('kindle-cliff-retired-foot-treasure-native')
kindle_movements += [move((22, 2), 32), move((22, 1), 64),
                     move((22, 0), 64), move((23, 0), 16)]
kindle_movements.append(move((23, 19), 64, TOWN))
kindle_movements.append(move((0, 139), 16, ROAD))
for x in range(1, 8):
    kindle_movements.append(move((x, 139), 16))
kindle_movements += [move((7, 138), 64), move((7, 137), 64)]
assert len(kindle_movements) == 28 and len(loaded_cells) == 26
assert state() == kindle_start
kindle_proof = dict(map=ROAD, initial_fixture=kindle_start, return_state=state(),
    native_loaded_cells=loaded_cells, all26_native_cells_checked=True,
    complete_face_and_water_toe_loaded=True,
    movements=kindle_movements, west_face_probe=west_probe,
    south_boundary_probe=south_probe, controller_steps=28,
    all_six_retired_treasure_foot_cells_surfed=True,
    town_treasure_surf_seam_roundtrip_controller=True,
    cape_surf_roundtrip_and_town_seam_controller=True,
    restored_private_16bit_initial_warp_fixture=True)
print('Native complete Kindle cliff, 26 cells, 28 Surf steps and two boundary probes passed', flush=True)

lib.stop()
assert hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest() == initial_rom_sha
result = dict(passed=True, kind='coastal-fragments', rom_sha256=initial_rom_sha,
              elf_sha256=hashlib.sha256((source / 'pokeemerald.elf').read_bytes()).hexdigest(),
              compiled_rom=True, native_validation_performed=True,
              cliff_rock_sites=sites, preserved_complete_native_rocks=complete,
              kindle_road_cliff=kindle_proof,
              cliff_rock_sites_checked=16, cliff_rock_maps_checked=9,
              all_cliff_foot_surf_roundtrips_use_controller=True,
              native_grid_and_loaded_banks_checked=True,
              no_avatar_coordinate_elevation_map_grid_palette_or_vram_writes=True,
              initial_party_progress_travel_and_encounter_suppression_are_fixtures=True,
              high_coordinate_fixture_uses_restored_private_16bit_warp_event=True,
              captures=captures)
(args.output / 'coastal-fragments.json').write_text(json.dumps(result, indent=2) + '\n')
print('All 16 finished cliff feet, two intact native rocks and the complete Kindle cape passed', flush=True)
