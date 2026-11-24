"""Verify the four Galar/PWT trial patches and their matching native evidence."""
import gzip
import hashlib
import json

from prepare_pwt_galar_za_megas import LAYER, REFERENCE, load_review
from pwt_catalog import eligible, load
from verify_atlas_route_pruning import DIRECTORY as ATLAS, ROOT, apply
from verify_pwt_official_review import DIRECTORY as PREVIOUS, checked
from verify_versions import VARIANTS

DIRECTORY = ROOT / 'mods/hoenn/pwt-galar-za-megas'


def verify(directory=DIRECTORY):
    manifest = json.loads((directory / 'validation.json').read_bytes())
    assert manifest['layer'] == LAYER and manifest['final_release_validated'] is False
    checked(REFERENCE, manifest['reference_sha256'])
    galar = load_review()
    rows = load()
    species = json.loads((ROOT / 'tools/hoenn/catalog_metadata.json').read_bytes())['species']
    previous = json.loads((PREVIOUS / 'validation.json').read_bytes())
    baseline = json.loads((ATLAS / 'validation.json').read_bytes())
    atlas_editions = {entry['edition']: entry for entry in baseline['editions']}
    assert manifest['editions'].keys() == VARIANTS.keys()

    for name, entry in manifest['editions'].items():
        cap = 4 if VARIANTS[name][0] == 493 else 9
        atlas = atlas_editions[name]
        base = apply(checked(ATLAS / atlas['patch'], atlas['patch_sha256']),
                     checked(ROOT / atlas['base'], atlas['base_sha256']))
        assert hashlib.sha256(base).hexdigest() == atlas['rom_sha256'] == entry['base_sha256'], name
        prefix = name.removesuffix('.gba')
        raw = apply(checked(directory / (prefix + '-pwt-galar-za.bps'), entry['patch_sha256']), base)
        assert len(raw) == 33554432 and hashlib.sha256(raw).hexdigest() == entry['rom_sha256'], name
        assert raw[0xbd] == (-sum(raw[0xa0:0xbd]) - 0x19) & 255, name
        proof = json.loads(gzip.decompress(checked(directory / (prefix + '-evidence.json.gz'), entry['evidence_sha256'])))
        roster, mega = proof['catalog'], proof['mega']
        for result in (roster, mega):
            assert result['passed'] and result['rom_sha256'] == entry['rom_sha256'], name
        assert mega['generation_cap'] == cap and mega['hard'] is VARIANTS[name][1], name
        assert mega['compiled_za_forms'] == 49 and mega['stones_in_ever_grande'] == 45, name
        assert len(set(mega['eligible_forms'])) == (17 if cap == 4 else 49), name
        assert mega['opponent'] == 'Lt. Surge' and mega['one_opponent_mega_stone'], name
        assert mega['native_ai_mega'] == 'SPECIES_RAICHU_MEGA_X', name
        assert mega['player_start_button_mega'] == 'SPECIES_RAICHU_MEGA_Y', name
        image = checked(directory / (prefix + '-mega.png'), entry['screenshot_sha256'])
        assert image[16:24] == bytes.fromhex('000000f0000000a0'), name
        cup_generation = {'Pokemon-Journey-Gen1-4-Normal.gba': 1, 'Pokemon-Journey-Gen1-9-Hard.gba': 8}.get(name)
        if cup_generation is not None:
            cup = proof['cup']
            assert cup['passed'] and cup['rom_sha256'] == entry['rom_sha256'], name
            assert cup['cup_generation'] == cup_generation and cup['complete_tournament_playthrough'], name
            assert cup['champion'] and cup['bp_reward'] == 10 and cup['party_restored_byte_exact'], name
        if name.endswith('Normal.gba'):
            ordinary = proof['ordinary']
            assert ordinary['passed'] and ordinary['rom_sha256'] == entry['rom_sha256'], name
            assert ordinary['case'] == ('garchomp-z' if cap == 4 else 'greninja'), name
            assert ordinary['native_start_button'] and ordinary['transformed'] and ordinary['restored_base_species'], name
        if cup_generation == 8:
            unboosted = proof['unboosted']
            assert unboosted['passed'] and unboosted['rom_sha256'] == entry['rom_sha256'], name
            assert unboosted['pool'] == 8 and not unboosted['battle_stat_hp_pp_or_outcome_writes'], name
            assert unboosted['returned_to_lobby'] and unboosted['original_party_restored_byte_exact'], name

        names = {record['name']: record['key'] for record in eligible(rows, cap)}
        assert roster['catalog_identities'] == len(rows) == 162
        assert roster['reviewed_galar_teams'] == (len(galar) if cap == 9 else 0), name
        assert {team['name'] for team in roster['catalog_teams']} == names.keys()
        old = previous['editions'][name]
        old_teams = json.loads(gzip.decompress(checked(PREVIOUS / (prefix + '-evidence.json.gz'),
                                                      old['evidence_sha256'])))['catalog']['catalog_teams']
        for prior, candidate in zip(old_teams, roster['catalog_teams'], strict=True):
            assert (candidate['name'], candidate['trainer_id'], candidate['portrait_id']) == (
                prior['name'], prior['trainer_id'], prior['portrait_id']), name
            key = names[candidate['name']]
            expected = (galar[key]['reference'] if key in galar else
                        [species[str(mon['species'])]['name'].removeprefix('SPECIES_') for mon in prior['team']])
            actual = [species[str(mon['species'])]['name'].removeprefix('SPECIES_') for mon in candidate['team']]
            assert actual == expected, (name, key)
    return manifest


if __name__ == '__main__':
    verify()
    print('Verified all four PWT Galar and Z-A Mega trial patches')
