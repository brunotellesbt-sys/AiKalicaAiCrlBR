"""Reproduce the five completed PWT editions and verify their native evidence."""
import gzip
import hashlib
import json
from pathlib import Path
import struct

from package_review_rom import NAME as TEST_EDITION
from prepare_pwt_complete_rosters import LAYER, REFERENCE, load_review
from prepare_pwt_galar_za_megas import load_review as load_galar
from prepare_pwt_official_parties import validate_review
from pwt_catalog import eligible, load
from review_pwt_official_parties import OUTPUT
from verify_atlas_route_pruning import DIRECTORY as ATLAS, ROOT, apply
from verify_battle_interactions import verify_report as verify_interactions
from verify_pwt_galar_za_megas import DIRECTORY as GALAR
from verify_pwt_official_review import checked
from verify_versions import VARIANTS

DIRECTORY = ROOT / 'mods/hoenn/pwt-complete-rosters'
PREFIX = 'Pokemon-Journey-'
PARENT_MERGE = '2c38d692538d48e1b028a969aa5d3ade66437675'
REQUIRED_CUPS = {
    PREFIX + 'Gen1-4-Normal.gba': {0, 1, 3}, PREFIX + 'Gen1-4-Hard.gba': {2, 4},
    PREFIX + 'Gen1-9-Normal.gba': {5, 6, 7}, PREFIX + 'Gen1-9-Hard.gba': {0, 8, 9},
    TEST_EDITION: set(),
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify(directory=DIRECTORY, *, output=None, base_directory=None):
    directory = Path(directory)
    manifest = json.loads((directory / 'validation.json').read_bytes())
    assert manifest['layer'] == LAYER and manifest['catalog_complete'] is True
    assert manifest['parent_commit'] == PARENT_MERGE
    assert manifest['editions'].keys() == REQUIRED_CUPS.keys()
    checked(REFERENCE, manifest['reference_sha256'])
    marker = json.loads(checked(directory / 'source-marker.json', manifest['source_marker_sha256']))
    assert marker['layer'] == LAYER and marker['catalog_complete'] and marker['entrant_ids_preserved']
    assert marker['reviewed_teams'] == 73 and marker['gen1_4_teams'] == 5
    final = load_review()
    canonical = validate_review(json.loads(OUTPUT.read_bytes())) | load_galar() | final
    rows = load()
    species = json.loads((ROOT / 'tools/hoenn/catalog_metadata.json').read_bytes())['species']
    atlas = {row['edition']: row for row in json.loads((ATLAS / 'validation.json').read_bytes())['editions']}
    prior = json.loads((GALAR / 'validation.json').read_bytes())['editions']

    for name, entry in manifest['editions'].items():
        national_cap, hard = VARIANTS.get(name, (1025, False))
        cap = 4 if national_cap == 493 else 9
        baseline = atlas[name]
        if base_directory is None:
            raw = apply(checked(ATLAS / baseline['patch'], baseline['patch_sha256']),
                        checked(ROOT / baseline['base'], baseline['base_sha256']))
        else:
            raw = (Path(base_directory) / name).read_bytes()
        assert sha(raw) == entry['base_sha256'] == baseline['rom_sha256'], name
        prefix = name.removesuffix('.gba')
        rom = apply(checked(directory / (prefix + '-pwt-complete.bps'), entry['patch_sha256']), raw)
        assert len(rom) == 33554432 and sha(rom) == entry['rom_sha256'], name
        assert rom[0xbd] == (-sum(rom[0xa0:0xbd]) - 0x19) & 255, name
        rules = manifest['build_rules_offset']
        assert 192 <= rules < len(rom) - 4 and rom[rules:rules + 4] == struct.pack('<HBB', national_cap, hard, 0), name
        proof = json.loads(gzip.decompress(checked(directory / (prefix + '-evidence.json.gz'), entry['evidence_sha256'])))
        catalog, mega = proof['catalog'], proof['mega']
        assert all(check['passed'] and check['rom_sha256'] == entry['rom_sha256'] for check in (catalog, mega)), name
        assert catalog['version_generation_cap'] == mega['generation_cap'] == cap, name
        assert catalog['perfect_ivs'] is mega['hard'] is hard, name
        assert catalog['catalog_identities'] == len(rows) == 162
        assert catalog['reviewed_final_teams'] == (5 if cap == 4 else 73), name
        assert catalog['water_silvally_memory_verified'] is (cap == 9), name
        assert mega['compiled_za_forms'] == 49 and mega['stones_in_ever_grande'] == 45, name
        assert len(set(mega['eligible_forms'])) == (17 if cap == 4 else 49), name
        assert mega['opponent'] == 'Lt. Surge' and mega['one_opponent_mega_stone'], name
        assert mega['native_ai_mega'] == 'SPECIES_RAICHU_MEGA_X', name
        assert mega['player_start_button_mega'] == 'SPECIES_RAICHU_MEGA_Y', name
        capture = checked(directory / (prefix + '-mega.png'), entry['screenshot_sha256'])
        assert capture[:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack_from('>II', capture, 16) == (240, 160), name

        previous_name = PREFIX + 'Gen1-9-Normal.gba' if name == TEST_EDITION else name
        previous_prefix = previous_name.removesuffix('.gba')
        archive = checked(GALAR / (previous_prefix + '-evidence.json.gz'), prior[previous_name]['evidence_sha256'])
        previous = json.loads(gzip.decompress(archive))['catalog']['catalog_teams']
        for entrant, team, old in zip(eligible(rows, cap), catalog['catalog_teams'], previous, strict=True):
            assert entrant['name'] == team['name'] == old['name']
            assert (team['trainer_id'], team['portrait_id']) == (old['trainer_id'], old['portrait_id'])
            actual = [species[str(mon['species'])]['name'].removeprefix('SPECIES_') for mon in team['team']]
            if entrant['key'] in canonical:
                expected = canonical[entrant['key']]['gen1_4' if cap == 4 else 'reference']
            else:
                expected = [species[str(mon['species'])]['name'].removeprefix('SPECIES_') for mon in old['team']]
            assert actual == expected, (name, entrant['key'])
            assert all(mon['level'] == 50 and sum(mon['evs']) == 510 for mon in team['team']), entrant['key']

        cups = proof['cups']
        assert {row['cup_generation'] for row in cups} == REQUIRED_CUPS[name] and len(cups) == len(REQUIRED_CUPS[name]), name
        for cup in cups:
            generation = cup['cup_generation']
            assert cup['passed'] and cup['rom_sha256'] == entry['rom_sha256'] and cup['complete_tournament_playthrough']
            assert cup['version_generation_cap'] == cap and cup['difficulty'] == ('Hard' if hard else 'Normal')
            assert cup['champion'] and cup['bp_reward'] == (10 if generation else 25)
            assert cup['party_restored_byte_exact'] and cup['returned_to_lobby']
            pool = {row['id'] for row in eligible(rows, cap, generation)}
            assert cup['entrants'] == 1 + len(pool), generation
            assert {battle['stage'] for battle in cup['actual_battles']} == {0, 1}
            for battle in cup['actual_battles']:
                assert battle['opponent_catalog_id'] in pool and battle['outcome'] == 1
                assert battle['level'] == 50 and battle['player_team_size'] == battle['enemy_team_size'] == 6
        if name != TEST_EDITION:
            verify_interactions(proof['interactions'], entry['rom_sha256'], national_cap, hard)
            if name == PREFIX + 'Gen1-9-Hard.gba':
                unboosted = proof['unboosted']
                assert unboosted['passed'] and unboosted['rom_sha256'] == entry['rom_sha256']
                assert unboosted['pool'] == 9 and unboosted['full_cup_participation']
                assert unboosted['battles'] and unboosted['opponent_ai_unchanged']
                assert unboosted['battle_stat_hp_pp_or_outcome_writes'] is False
                assert unboosted['returned_to_lobby'] and unboosted['original_party_restored_byte_exact']
            parent = bytearray(rom)
            parent[0xa0:0xbe] = bytes.fromhex(manifest['parent_header_hex'])
            parent[rules:rules + 4] = struct.pack('<HBB', 1025, 1, 0)
            assert sha(parent) == manifest['compiled_rom_sha256'], name
        else:
            fields = manifest['test_mode']
            at = fields['review_mode_offset']
            assert 192 <= at < len(rom) and rom[at] == 1
            assert rom[0xa0:0xb0] == b'JOURNEY TESTJRTE' and fields['sha256'] == entry['rom_sha256']
            restored = bytearray(rom)
            restored[at] = 0
            restored[0xa0:0xbe] = bytes.fromhex(fields['base_header_hex'])
            assert sha(restored) == fields['base_normal_sha256'] == manifest['editions'][previous_name]['rom_sha256']
            boot = proof['cold_boot']
            assert boot['passed'] and boot['rom_sha256'] == entry['rom_sha256']
            assert boot['fresh_rom_title_to_new_game'] and boot['bundled_save_continue_to_field']
            assert boot['controllers_only'] and boot['no_game_memory_writes']
            checked(ROOT / 'roms/rom-de-teste' / name.replace('.gba', '.sav'), boot['bundled_save_sha256'])
            saved, = [run for run in boot['runs'] if run['battery']]
            assert saved['geometry_version'] == 9 and saved['field_map'] == [0, 6]
            assert saved['player_tile'] == [28, 18] and not saved['player_surfing']
        if output is not None:
            (Path(output) / name).write_bytes(rom)
    return manifest


if __name__ == '__main__':
    verify()
    print('Verified 162 documented PWT entrants, five editions and all cup proofs')
