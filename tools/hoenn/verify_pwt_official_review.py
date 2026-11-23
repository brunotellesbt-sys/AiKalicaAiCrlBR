"""Verify all four trial patches against the checked-in Atlas HJK editions and reports."""
import gzip
import hashlib
import json

from prepare_pwt_official_parties import LAYER, OUTPUT, validate_review
from verify_atlas_route_pruning import DIRECTORY as ATLAS, ROOT, apply
from verify_battle_interactions import verify_report as verify_interactions
from verify_versions import VARIANTS

DIRECTORY = ROOT / 'mods/hoenn/pwt-official-review'


def checked(path, sha):
    data = path.read_bytes()
    assert hashlib.sha256(data).hexdigest() == sha, path
    return data


def verify(directory=DIRECTORY):
    report = json.loads((directory / 'validation.json').read_bytes())
    assert report['layer'] == LAYER and report['final_release_validated'] is False
    review = json.loads(checked(OUTPUT, report['reference_sha256']))
    parties = validate_review(review)
    available_cap4 = sum(team['gen1_4'] is not None for team in parties.values())
    species = json.loads((ROOT / 'tools/hoenn/catalog_metadata.json').read_bytes())['species']
    baseline = json.loads((ATLAS / 'validation.json').read_bytes())
    base_editions = {row['edition']: row for row in baseline['editions']}
    assert report['editions'].keys() == set(VARIANTS)
    for name, edition in report['editions'].items():
        row = base_editions[name]
        base = apply(checked(ATLAS / row['patch'], row['patch_sha256']), checked(ROOT / row['base'], row['base_sha256']))
        assert hashlib.sha256(base).hexdigest() == row['rom_sha256'] == edition['base_sha256'], name
        prefix = name.removesuffix('.gba')
        patch = checked(directory / (prefix + '-pwt-review.bps'), edition['patch_sha256'])
        rom = apply(patch, base)
        assert len(rom) == 33554432 and hashlib.sha256(rom).hexdigest() == edition['rom_sha256'], name
        assert rom[0xbd] == (-sum(rom[0xa0:0xbd]) - 0x19) & 255, name
        captures = json.loads(gzip.decompress(checked(directory / (prefix + '-evidence.json.gz'), edition['evidence_sha256'])))
        required = {'catalog', 'interactions', 'modern', 'cup' if name.endswith('Normal.gba') else 'unboosted'}
        gen4 = '-Gen1-4-' in name
        if not gen4:
            required.update(('dipplin', 'girafarig'))
        elif name.endswith('Normal.gba'):
            required.add('stone')
        assert captures.keys() == required, name
        for item in captures.values():
            assert item['passed'] and item['rom_sha256'] == edition['rom_sha256'], name
        catalog = captures['catalog']
        assert len(catalog['catalog_teams']) == (61 if gen4 else 162), name
        assert catalog['reviewed_official_teams'] + catalog['reviewed_league_teams'] == (
            available_cap4 if gen4 else len(parties)), name
        teams = {row['name']: row['team'] for row in catalog['catalog_teams']}
        assert len(teams) == len(catalog['catalog_teams']), name
        for party in parties.values():
            expected = party['gen1_4'] if gen4 else party['reference']
            if expected is not None:
                actual = [species[str(mon['species'])]['name'].removeprefix('SPECIES_')
                          for mon in teams[party['name']]]
                assert actual == expected, (name, party['name'])
        assert len(captures['modern']['checks']) == (9 if gen4 else 26), name
        verify_interactions(captures['interactions'], edition['rom_sha256'], 493 if gen4 else 1025,
                            name.endswith('Hard.gba'))
        if 'cup' in captures:
            cup = captures['cup']
            assert cup['complete_tournament_playthrough'] and cup['champion'] and cup['bp_reward'] == 10, name
            assert cup['party_restored_byte_exact'] and cup['returned_to_lobby'], name
        else:
            match = captures['unboosted']
            assert match['single_catalog_matchup'] and not match['battle_stat_hp_pp_or_outcome_writes'], name
            assert match['original_party_restored_byte_exact'] and match['returned_to_lobby'], name
        for evolution in required & {'dipplin', 'girafarig'}:
            menu = captures[evolution]
            assert menu['case'] == evolution and menu['level_up_without_move_did_not_evolve'], name
            assert menu['item_activation_and_confirmation_are_controller_input'], name
            assert menu['learned_move_persisted_after_evolution_and_reload'], name
        if 'stone' in captures:
            menu = captures['stone']
            assert menu['stone_consumed_once'] and menu['reusable_tm_taught_to_two_pokemon'], name
    return report


if __name__ == '__main__':
    verify()
    print('Four PWT trial patches match their Atlas HJK bases and native evidence')
