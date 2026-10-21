"""Replay the island port overlay and audit its exact source and save ABI scope."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import tempfile

from prepare_sevii_integrated_piers import LAYER, PRIOR, prepare
from validate_dewford_coast_source import compiled_values

PARENT_ROM_SHA256 = '5e0cecc8d2143334795a752e9bb1f70343671f34a29dbd2af3a78e3bff05ef50'
ISLANDS = ['One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven']
OWNERS = ['OneIsland_TreasureBeach_Frlg', 'TwoIsland_Frlg',
          'ThreeIsland_Port_Frlg', 'FourIsland_Frlg', 'FiveIsland_Frlg',
          'SixIsland_Frlg', 'SevenIsland_Frlg']
FRONT = 'SevenIsland_SevaultCanyon_Entrance_Frlg'
OCEAN_MAPS = set(OWNERS + [FRONT, 'OneIsland_Frlg',
    'TwoIsland_CapeBrink_Frlg', 'ThreeIsland_Frlg', 'SixIsland_WaterPath_Frlg',
    'SevenIsland_TrainerTower_Frlg', 'SevenIsland_SevaultCanyon_Frlg',
    'JourneySurfLink01000', 'JourneySurfLink05100', 'JourneySurfLink05200',
    'JourneySurfLink05301'])
ALLOWED_SOURCE_FILES = {
    'data/layouts/layouts.json',
    'src/data/tilesets/headers.h', 'src/data/tilesets/graphics.h',
    'src/data/tilesets/metatiles.h',
    'data/tilesets/secondary/journey_dewford_harbor/metatile_attributes.bin',
    'src/event_object_movement.c',
    'src/journey_sevii_surf.c', 'src/field_door.c', 'include/tilesets.h',
    'data/tilesets/primary/general_frlg/journey_sevii_sea_metatiles.bin',
}
for family in ['123', '45', '67']:
    ALLOWED_SOURCE_FILES.add(f'data/tilesets/secondary/sevii_islands_{family}_frlg/journey_sevii_sea_metatiles.bin')
    folder = 'data/tilesets/secondary/journey_sevii_integrated_' + family
    ALLOWED_SOURCE_FILES.update(folder + '/' + name for name in [
        'tiles.png', 'metatiles.bin', 'metatile_attributes.bin',
        *[f'palettes/{bank:02}.pal' for bank in range(16)]])
for island in ISLANDS:
    ALLOWED_SOURCE_FILES.update([
        f'data/maps/{island}Island_Harbor_Frlg/map.json',
        f'data/layouts/JourneySevii{island}Port/map.bin',
        f'data/maps/JourneySevii{island}Harbor/map.json'])
for name in OWNERS + [FRONT]:
    ALLOWED_SOURCE_FILES.update([f'data/maps/{name}/map.json',
                                 f'data/layouts/{name}/map.bin'])
ALLOWED_SOURCE_FILES.add('data/layouts/OneIsland_Frlg/map.bin')


def audit_ports(source, baseline, marker):
    """Check complete native facades, direct doors and preservation of other events."""
    from render_sea_maps import MapRenderer
    current_layouts = json.loads((source / 'data/layouts/layouts.json').read_text())
    old_layouts = json.loads((baseline / 'data/layouts/layouts.json').read_text())
    assert current_layouts.keys() == old_layouts.keys()
    assert len(current_layouts['layouts']) == len(old_layouts['layouts'])
    allowed_layouts = set(OWNERS + [FRONT, 'OneIsland_Frlg'])
    for old, new in zip(old_layouts['layouts'], current_layouts['layouts']):
        folder = old['blockdata_filepath'].split('/')[-2]
        expected = dict(old)
        if folder in allowed_layouts:
            assert old['secondary_tileset'].startswith('gTileset_SeviiIslands')
            expected['secondary_tileset'] = old['secondary_tileset'].replace('SeviiIslands', 'JourneySeviiIntegrated')
        if folder in OCEAN_MAPS:
            expected['primary_tileset'] = 'gTileset_JourneySeviiSea'
            if expected['secondary_tileset'].startswith('gTileset_SeviiIslands'):
                expected['secondary_tileset'] = expected['secondary_tileset'].replace('SeviiIslands', 'JourneySeviiSea')
        assert new == expected, ('Unauthorized layout or bank change', old['id'])
    before_renderer, after_renderer = MapRenderer(baseline), MapRenderer(source)
    donor, _ = before_renderer.render('OneIsland_Harbor_Frlg', npcs=False)
    terminal = donor.crop((160, 0, 272, 96))
    layouts = {row['id']: row for row in current_layouts['layouts']}
    ports = marker['harbors']['ports']
    changed_headers = {f'data/maps/{p["map"]}/map.json' for p in ports}
    changed_headers |= {f'data/maps/{p["old_exterior"]}/map.json' for p in ports}
    changed_headers |= {f'data/maps/{p["interior"]}/map.json' for p in ports}
    changed_headers.add(f'data/maps/{FRONT}/map.json')
    for old_path in (baseline / 'data/maps').glob('*/map.json'):
        relative = old_path.relative_to(baseline).as_posix()
        old = json.loads(old_path.read_text())
        new = json.loads((source / relative).read_text())
        if relative not in changed_headers:
            assert old == new, relative
        else:
            assert old == (new | {'warp_events': old['warp_events'],
                                  'object_events': old['object_events']}), relative
    for port in ports:
        island = port['island']
        assert port['map'] == OWNERS[ISLANDS.index(island)]
        image, exterior = after_renderer.render(port['map'], npcs=False)
        x, y, width, height = port['terminal_bounds']
        assert (width, height) == (7, 6)
        assert image.crop((x * 16, y * 16, (x + width) * 16, (y + height) * 16)).tobytes() == terminal.tobytes(), (island, 'Incomplete native terminal or changed colors')
        inside = json.loads((source / f'data/maps/{port["interior"]}/map.json').read_text())
        door = exterior['warp_events'][port['door_warp_id']]
        assert (door['x'], door['y'], door['elevation']) == (x + 3, y + 5, 3)
        assert door['dest_map'] == inside['id'] and door['dest_warp_id'] == '0'
        assert inside['warp_events']
        for warp in inside['warp_events']:
            assert warp['dest_map'] == exterior['id'] and warp['dest_warp_id'] == str(port['door_warp_id'])
        old_header = json.loads((source / f'data/maps/{port["old_exterior"]}/map.json').read_text())
        assert not old_header['warp_events'] and not old_header['object_events']
        old_layout = layouts[old_header['layout']]
        old_blocks = struct.unpack('<' + 'H' * (old_layout['width'] * old_layout['height']),
                                   (source / old_layout['blockdata_filepath']).read_bytes())
        for row in range(6):
            for column in range(7):
                value = old_blocks[row * old_layout['width'] + column + 10]
                assert value >> 12 == 1 and not value & 0xC00, (island, 'Detached terminal remains')
        for name, xx, yy in port['deck_cells']:
            data = json.loads((source / f'data/maps/{name}/map.json').read_text())
            layout = layouts[data['layout']]
            value = struct.unpack_from('<H', (source / layout['blockdata_filepath']).read_bytes(),
                                       2 * (yy * layout['width'] + xx))[0]
            assert value >> 12 == 3 and not value & 0xC00, (island, name, xx, yy)
    return ports


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate(source, baseline, output, preflight=False):
    source, baseline, output = map(Path, (source, baseline, output))
    assert source.resolve() != baseline.resolve()
    parent_sha = digest(baseline / 'pokeemerald.gba')
    assert parent_sha == PARENT_ROM_SHA256
    rom_sha = None if preflight else digest(source / 'pokeemerald.gba')
    if not preflight:
        assert rom_sha != parent_sha, 'Compile the integrated port source first'
    marker = json.loads((source / ('.journey-' + LAYER)).read_text())
    assert marker['layer'] == LAYER and len(PRIOR) == 161
    expected = dict(json.loads((baseline / '.source-acquired.json').read_text())['sha256'])
    for name in PRIOR:
        expected.update(json.loads((baseline / ('.journey-' + name)).read_text())['prepared_sha256'])
    outputs = marker['prepared_sha256']
    changed = sorted(name for name, sha in outputs.items() if sha != expected.get(name))
    assert ALLOWED_SOURCE_FILES, 'The overlay scope needs independent review'
    assert set(changed) == ALLOWED_SOURCE_FILES
    assert len(expected) > 30000
    for name, sha in expected.items():
        assert digest(baseline / name) == sha, ('Modified baseline', name)
    for name, sha in (expected | outputs).items():
        assert digest(source / name) == sha, ('Unexpected source modification', name)
    history = ['.source-acquired.json', *['.journey-' + name for name in PRIOR]]
    for name in history:
        assert (source / name).read_bytes() == (baseline / name).read_bytes(), name
    with tempfile.TemporaryDirectory(prefix='sevii-integrated-replay-', dir='/tmp') as temporary:
        replay = Path(temporary)
        for name in [*expected, *history]:
            destination = replay / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            try:
                os.link(baseline / name, destination)
            except OSError:
                shutil.copyfile(baseline / name, destination)
        fresh = json.loads(json.dumps(prepare(replay)))
        assert fresh == marker, 'Independent replay disagrees with the prepared overlay'
        assert prepare(replay) == fresh, 'The overlay is not idempotent'
        for name, sha in outputs.items():
            assert digest(replay / name) == sha, name
        for name in outputs.keys() & expected.keys():
            assert digest(baseline / name) == expected[name], ('Replay altered baseline', name)

    ports = audit_ports(source, baseline, marker)
    from integrated_ocean_seams import audit_source as audit_ocean
    from validate_six_landscape import inspect_source
    ocean_audit = audit_ocean(source, baseline, marker['ocean_seams'])
    six_audit = inspect_source(source, baseline)
    preserved = ['data/maps/map_groups.json',
                 'src/journey_campaign_gates.c', 'src/journey_crossover.c',
                 'include/journey_team_missions.h', 'src/data/journey_pwt_trainers.h',
                 'include/constants/vars.h', 'include/constants/flags.h',
                 'include/constants/items.h', 'include/trainer_card.h',
                 'include/global.h', 'include/link.h', 'include/pokemon.h',
                 'src/data/journey_world_map.h', 'src/journey_world_map.c']
    for name in preserved:
        assert (source / name).read_bytes() == (baseline / name).read_bytes(), name
    gym_info = json.loads((baseline / '.journey-extra-gyms').read_text())
    layouts = {row['id']: row for row in json.loads((source / 'data/layouts/layouts.json').read_text())['layouts']}
    for gym in gym_info['gyms']:
        name = 'data/maps/' + gym['name'] + '/map.json'
        assert (source / name).read_bytes() == (baseline / name).read_bytes(), name
        layout = layouts[json.loads((source / name).read_text())['layout']]
        for name in [layout['blockdata_filepath'], layout['border_filepath']]:
            assert (source / name).read_bytes() == (baseline / name).read_bytes(), name
    assert len(gym_info['gyms']) == 8
    abi_symbols = ['sizeof(struct SaveBlock1)', 'sizeof(struct SaveBlock2)',
                   'sizeof(struct ObjectEvent)', 'sizeof(struct LinkPlayer)',
                   'sizeof(struct LinkPlayerBlock)', 'FLAGS_COUNT']
    abi_includes = ['global.h', 'constants/flags.h', 'link.h']
    current_abi = compiled_values(source, abi_symbols, abi_includes, baseline)
    assert current_abi == compiled_values(baseline, abi_symbols, abi_includes, baseline)
    moves = re.findall(r'F\((\w+)\)', (baseline / 'include/constants/tms_hms.h').read_text().split('#define FOREACH_HM')[0])
    item_symbols = ['ITEM_TM_' + move for move in moves] + [
        'ITEM_HM_SURF', 'ITEM_HM_DIVE', 'ITEM_HM_WATERFALL', 'ITEM_HM_FLY',
        'ITEM_FULL_RESTORE', 'ITEM_MAX_REVIVE', 'ITEM_POKE_BALL']
    item_values = compiled_values(source, item_symbols, ['global.h', 'constants/items.h'], baseline)
    assert item_values == compiled_values(baseline, item_symbols, ['global.h', 'constants/items.h'], baseline)
    assert len(ports) == 7 and {p['island'] for p in ports} == {'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven'}
    if not preflight:
        assert digest(source / 'pokeemerald.gba') == rom_sha, 'ROM changed during source audit'
    assert digest(baseline / 'pokeemerald.gba') == parent_sha
    result = dict(passed=True, kind='sevii-integrated-source',
                  rom_sha256=rom_sha, parent_rom_sha256=parent_sha,
                  compiled_rom=not preflight, preflight=bool(preflight),
                  layers=PRIOR + [LAYER], changed_files=changed,
                  allowed_changed_files=sorted(ALLOWED_SOURCE_FILES),
                  source_hashes_checked=len(expected | outputs),
                  independent_replay=True, idempotent=True,
                  unrelated_source_files_unchanged=True, gyms_and_campaign_unchanged=True,
                  atlas_graphics_unchanged=True, save_and_link_abi_unchanged=True,
                  original_tm_hm_and_item_numbers_preserved=True,
                  compiled_abi=dict(zip(abi_symbols, current_abi)),
                  compiled_item_constants_preserved=len(item_symbols),
                  extra_gyms_preserved=8, ports=ports,
                  six_landscape=six_audit, ocean=ocean_audit,
                  authorized_port_warp_changes_only=True,
                  all_seven_terminals_at_town_bridge_ends=True,
                  all_seven_separate_terminals_removed=True,
                  surf_reboarding_uses_native_state_transition=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--preflight', action='store_true')
    args = parser.parse_args()
    report = validate(args.source, args.baseline, args.output, args.preflight)
    print(json.dumps({key: report[key] for key in ['passed', 'rom_sha256', 'preflight', 'changed_files']}, indent=2))
