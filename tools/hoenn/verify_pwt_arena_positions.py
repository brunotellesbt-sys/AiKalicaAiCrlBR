"""Verify both stadium entrances and rebuild the five tested PWT editions."""
import gzip
import json
import struct
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image, ImageChops

from prepare_pwt_arena_positions import ENTRANCE, LAYER, SCRIPT
from pwt_catalog import eligible, load
from verify_atlas_route_pruning import ROOT, apply, sha
from verify_battle_interactions import verify_report as verify_battle
from verify_crossover_badges import DIRECTORY as PARENT, verify as verify_parent, verify_continues
from verify_pwt_balance import verify_report as verify_unboosted
from verify_pwt_complete_rosters import DIRECTORY as ROSTERS
from verify_pwt_official_review import checked
from verify_versions import VARIANTS

DIRECTORY = ROOT / 'mods/hoenn' / LAYER
POOLS = {'Gen1-4-Normal': 1, 'Gen1-4-Hard': 4, 'Gen1-9-Normal': 9, 'Gen1-9-Hard': 0, 'TESTE': 3}


def presentation(folder, run, expected_rom, elf, regression):
    assert run['passed'] and run['rom_sha256'] == expected_rom and run['elf_sha256'] == elf
    assert run['draw_seed'] == 101 and run['offset_regression_observed'] is regression
    assert run['declined_round_with_controller'] and run['original_party_restored_byte_exact']
    assert run['no_bp_reward_for_retirement'] and run['travel_and_registration_are_fixtures']
    entrance = run['entrance']
    assert entrance['player'] == [9, 6] and entrance['opponent_start'] == ([10, -1] if regression else [17, 6])
    assert entrance['opponent'] == ([6, -1] if regression else [13, 6])
    checked(folder / 'ready.png', run['capture_sha256'])
    picture = checked(folder / 'presentation.png', run['presentation_sha256'])
    with Image.open(BytesIO(picture)) as image:
        assert image.size == (240, 160) and image.format == 'PNG'
        return image.convert('RGB')


def verify_cup(proof, sha256, cap, hard, pool, rows):
    assert proof['rom_sha256'] == sha256 and proof['version_generation_cap'] == cap
    assert proof['difficulty'] == ('Hard' if hard else 'Normal') and proof['cup_generation'] == pool
    assert proof['passed'] and proof['complete_tournament_playthrough'] and proof['champion']
    assert proof['returned_to_lobby'] and proof['party_restored_byte_exact']
    assert proof['player_battle_stats_boosted_for_flow_test'] and proof['helper_and_travel_fixtures']
    assert proof['bp_reward'] == (10 if pool else 25)
    entrants = {row['id']: row['name'] for row in eligible(rows, cap, pool)}
    assert proof['entrants'] == len(entrants) + 1
    battles = proof['actual_battles']
    assert {battle['stage'] for battle in battles} == {0, 1}
    for battle in battles:
        actor = battle['entrance']
        assert actor['opponent_start'] == [17, 6] and actor['opponent'] == [13, 6] and actor['player'] == [9, 6]
        assert battle['opponent_name'] == entrants[actor['catalog_id']]
        assert actor['catalog_id'] == battle['opponent_catalog_id']
        assert battle['level'] == 50 and battle['player_team_size'] == battle['enemy_team_size'] == 6
        assert battle['outcome'] == 1 and battle['attacks'] > 0


def verify(directory=DIRECTORY, *, output=None, base_directory=None):
    directory = Path(directory)
    if base_directory is None:
        with TemporaryDirectory(prefix='pwt-arena-parent-') as temp:
            verify_parent(output=temp)
            return verify(directory, output=output, base_directory=temp)

    info = json.loads((directory / 'validation.json').read_bytes())
    parent = json.loads(checked(PARENT / 'validation.json', info['parent_manifest_sha256']))
    assert info['layer'] == LAYER and info['editions'].keys() == parent['editions'].keys()
    marker = json.loads(checked(directory / 'source-marker.json', info['source_marker_sha256']))
    assert marker['layer'] == LAYER and set(marker['prepared_sha256']) == {ENTRANCE, SCRIPT}
    assert marker['opponent_start'] == [17, 6] and marker['opponent_ready'] == [13, 6]
    previous = json.loads((ROSTERS / 'validation.json').read_bytes())
    rows = load()
    if output is not None:
        Path(output).mkdir(parents=True, exist_ok=True)
    for name, entry in info['editions'].items():
        stem = Path(name).stem
        edition = stem.removeprefix('Pokemon-Journey-')
        base = checked(Path(base_directory) / name, parent['editions'][name]['rom_sha256'])
        patch = checked(directory / (stem + '.bps'), entry['patch_sha256'])
        rom = apply(patch, base)
        assert len(rom) == len(base) == 33554432 and sha(rom) == entry['rom_sha256']
        # These ranges are the compiled coordinate immediate and NextRound script.
        # Restoring them must reproduce the complete parent, including its edition header.
        restored = bytearray(rom)
        assert base[0x1780e8] == 6 and rom[0x1780e8] == 13
        restored[0x1780e8] = 6
        assert rom[0x3e8ccb:0x3e8cfb] != base[0x3e8ccb:0x3e8cfb]
        restored[0x3e8ccb:0x3e8cfb] = base[0x3e8ccb:0x3e8cfb]
        assert restored == base
        del restored
        # The five profiles differ from the same compiled ROM only in the
        # already-verified header, build rules and TESTE switch.
        normalized = bytearray(rom)
        normalized[0xa0:0xbe] = bytes.fromhex(parent['parent_header_hex'])
        offset = parent['build_rules_offset']
        normalized[offset:offset + 4] = struct.pack('<HBB', 1025, 1, 0)
        if name == 'Pokemon-Journey-TESTE.gba':
            normalized[parent['test_mode']['review_mode_offset']] = 0
        assert sha(normalized) == info['compiled_rom_sha256']
        national, hard = VARIANTS.get(name, (1025, False))
        cap = 4 if national == 493 else 9
        folder = directory / stem
        proof = json.loads(gzip.decompress(checked(folder / 'native.json.gz', entry['native_sha256'])))
        digest = entry['rom_sha256']
        old, new = proof['before'], proof['after']
        before = presentation(folder / 'before', old, parent['editions'][name]['rom_sha256'], parent['elf_sha256'], True)
        after = presentation(folder / 'after', new, digest, info['elf_sha256'], False)
        for key in ('catalog_id', 'walking_graphics'):
            assert old['entrance'][key] == new['entrance'][key]
        left, top, right, bottom = ImageChops.difference(before, after).getbbox()
        assert (left, right, bottom) == (176, 192, 88) and 55 <= top <= 72
        reference = json.loads(gzip.decompress(checked(ROSTERS / (stem + '-evidence.json.gz'),
                                                       previous['editions'][name]['evidence_sha256'])))
        for key in ('catalog', 'mega'):
            assert proof[key] == {**reference[key], 'rom_sha256': entry['rom_sha256']}
        checked(folder / 'mega-raichu.png', entry['mega_capture_sha256'])
        verify_cup(proof['cup'], digest, cap, hard, POOLS[edition], rows)
        verify_unboosted(proof['unboosted'], digest, cap, hard, POOLS[edition])
        verify_battle(proof['battle'], digest, national, hard)
        register = proof['registration']
        org = ROOT / 'docs/design/revisao-integral-2026-11-26' / (stem + '-mecanicas.json.gz')
        assert register == {**json.loads(gzip.decompress(org.read_bytes()))['registration'], 'rom_sha256': digest}
        verify_continues(directory, name, {**entry, 'base_sha256': parent['editions'][name]['base_sha256']}, info['elf_sha256'])
        if output is not None:
            (Path(output) / name).write_bytes(rom)
    return info


if __name__ == '__main__':
    verify()
    print('Verified the stadium entrances, cups, return to lobby and five ROMs.')
