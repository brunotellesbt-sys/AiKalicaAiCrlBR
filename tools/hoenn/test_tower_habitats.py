"""Tower family habitats, native ghost scaling and complete catalog regression."""
import csv
import json
from pathlib import Path
import unittest
from prepare_ecology import LAND_RATES

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / 'mods/hoenn/tower-habitat-validation'

class TowerHabitats(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prep = json.loads((DIR / 'preparation/preparation.json').read_text())
        cls.old = json.loads((ROOT / 'mods/hoenn/lostelle-habitat-validation/preparation/preparation.json').read_text())
        cls.native = json.loads((DIR / 'tower-habitats.json').read_text())
        cls.wild = json.loads((DIR / 'wild.json').read_text())
        cls.replay = json.loads((DIR / 'preparation/reproduction.json').read_text())

    def test_story_and_random_marowak_share_one_habitat(self):
        for root, section in [(104, 'MAPSEC_POKEMON_TOWER'), (29, 'MAPSEC_DIGLETTS_CAVE')]:
            owned = [h['section'] for h in self.prep['locations_data'] if any(f['root'] == root for f in h['families'])]
            self.assertEqual(owned, [section])
        self.assertTrue(self.prep['original_marowak_ghost_script_preserved'])
        self.assertIn('data/maps/PokemonTower_6F_Frlg/scripts.inc', self.prep['preserved_native_sha256'])

    def test_other_families_counts_and_full_catalog_are_preserved(self):
        before = {f['root']: (h['section'], f) for h in self.old['locations_data'] for f in h['families']}
        after = {f['root']: (h['section'], f) for h in self.prep['locations_data'] for f in h['families']}
        self.assertEqual(len(after), 444); self.assertEqual(before.keys(), after.keys())
        for root in before:
            self.assertEqual(before[root][1], after[root][1])
            if root not in [104, 29]: self.assertEqual(before[root][0], after[root][0])
        self.assertEqual([h['family_count'] for h in self.old['locations_data']],
                         [h['family_count'] for h in self.prep['locations_data']])

    def test_aquatic_and_unaffected_pools_are_identical(self):
        maps = {m for h in self.prep['locations_data'] if h['section'] in ['MAPSEC_POKEMON_TOWER', 'MAPSEC_DIGLETTS_CAVE'] for m in h['maps']}
        old = {(p['map'], p['area']): p for p in self.old['pools']}
        for p in self.prep['pools']:
            if p['map'] not in maps or p['area'] in [1, 3]: self.assertEqual(p, old[p['map'], p['area']])

    def test_native_dex_membership_all_maps_and_three_evolution_phases(self):
        self.assertTrue(self.native['passed'])
        self.assertEqual(self.native['rom_sha256'], self.replay['rom_sha256'])
        expected = 2 * sum(len(h['maps']) for h in self.prep['locations_data'])
        self.assertEqual(len(self.native['dex_membership']), expected)
        target_maps = {m for h in self.prep['locations_data'] if h['section'] in ['MAPSEC_POKEMON_TOWER', 'MAPSEC_DIGLETTS_CAVE'] for m in h['maps']}
        self.assertEqual(len(self.native['phase_cases']), 3 * len(target_maps))
        for c in self.native['phase_cases']:
            root = c['root']; self.assertEqual(c['observed'], ([104] if c['phase'] == 0 else [104, 105, 973] if c['phase'] == 1 else [105, 973]) if root == 104 else ([29] if c['phase'] == 0 else [29, 30] if c['phase'] == 1 else [30, 31]))

    def test_complete_native_habitat_and_wild_level_regression(self):
        r = self.wild; self.assertTrue(r['passed'])
        self.assertEqual(r['rom_sha256'], self.replay['rom_sha256'])
        self.assertEqual(len(r['catalog_habitats']), 135)
        for h in r['catalog_habitats']:
            self.assertTrue(h['observed']); self.assertLessEqual(set(h['observed']), set(self.prep['map_species'][h['map']]))
        self.assertTrue(r['national_dex_from_initial_pokedex']); self.assertTrue(r['aquatic_branches_verified'])
        self.assertEqual(r['phase_cases'], 6); self.assertEqual(len(r['level_cases']), 5)

    def test_documented_species_match_native_habitats(self):
        with (ROOT / 'mods/hoenn/pokemon-locations.csv').open() as stream:
            rows = {int(r['internal_id']): r for r in csv.DictReader(stream)}
        for species, habitat in [(104, 'Pokemon Tower'), (105, 'Pokemon Tower'), (973, 'Pokemon Tower'), (29, 'Digletts Cave'), (30, 'Digletts Cave'), (31, 'Digletts Cave')]:
            self.assertEqual(rows[species]['habitat'], habitat)
        self.assertEqual(len([r for r in rows.values() if r['category'] == 'comum']), 920)

    def test_rarer_families_keep_lower_land_chances(self):
        for habitat in self.prep['locations_data']:
            if habitat['section'] not in ['MAPSEC_POKEMON_TOWER', 'MAPSEC_DIGLETTS_CAVE']: continue
            for pool in self.prep['pools']:
                if pool['map'] not in habitat['maps'] or pool['area'] != 0: continue
                chances = {f['root']: sum(p for r, p in zip(pool['roots'], LAND_RATES) if r == f['root']) for f in habitat['families']}
                self.assertEqual(sum(chances.values()), 100)
                for a in habitat['families']:
                    for b in habitat['families']:
                        if a['weight'] < b['weight']: self.assertLessEqual(chances[a['root']], chances[b['root']])

    def test_overlay_replay_and_english_are_verified(self):
        self.assertTrue(self.replay['passed']); self.assertTrue(self.replay['deterministic_replay']); self.assertTrue(self.replay['idempotent'])
        english = json.loads((DIR / 'english-audit.json').read_text())
        self.assertTrue(english['passed']); self.assertEqual(english['rom_sha256'], self.replay['rom_sha256'])
        self.assertEqual(set(self.prep['prepared_sha256']), {'src/data/wild_encounters.json', 'include/journey_wild_data.h', 'include/journey_habitat_data.h', 'src/battle_setup.c'})

    def test_ghost_level_regression_and_native_outcomes(self):
        r = json.loads((DIR / 'tower-ghost.json').read_text())
        self.assertTrue(r['passed']); self.assertEqual(r['rom_sha256'], self.replay['rom_sha256'])
        self.assertEqual(len(r['cases']), 5)
        for c in r['cases']:
            self.assertGreaterEqual(c['opponent_level'], max(1, c['mean'] - 5))
            self.assertLessEqual(c['opponent_level'], min(100, c['mean'] + 2))
            self.assertEqual(c['scene'], int(c['scope']))
            self.assertEqual(c['outcome'], 1 if c['scope'] else 4)
            self.assertTrue(c['ghost_battle'])
            if c['scope']:
                self.assertEqual(c['reconstructed']['gender'], 254)
                self.assertEqual(c['reconstructed']['nature'], 12)
                self.assertEqual(c['reconstructed']['ivs'], [31, 0, 0, 0, 0, 0])
        self.assertTrue(r['victory_save_continue']); self.assertTrue(r['seventh_floor_reached_by_walking'])
        self.assertTrue(r['initial_states_and_boosted_stats_are_fixtures'])
        self.assertFalse(r['full_campaign_playthrough']); self.assertFalse(r['balance_validated'])
        old = json.loads((DIR / 'baseline-regression.json').read_text())
        self.assertTrue(old['expected_failure_reproduced'])
        self.assertEqual(old['baseline_rom_sha256'], self.replay['baseline_rom_sha256'])
        self.assertEqual(old['observed_level'], 30); self.assertEqual(old['party_mean'], 5)

    def test_static_inventory_resolves_shared_events_and_preserves_limits(self):
        r = json.loads((DIR / 'fixed-encounters.json').read_text())
        self.assertEqual(r['rom_sha256'], self.replay['rom_sha256'])
        self.assertTrue(any(c['map'] == 'Route119' and c['species'] == 'SPECIES_KECLEON' for c in r['records']))
        self.assertTrue(any(c['species'] == 'SPECIES_SUDOWOODO' for c in r['records']))
        self.assertFalse(any(c['species'] in ['SPECIES_HYPNO', 'SPECIES_MAROWAK'] for c in r['ordinary_habitat_mismatches']))
        self.assertFalse(r['full_fixed_encounter_coverage']); self.assertFalse(r['conditions_and_flags_evaluated'])

if __name__ == '__main__': unittest.main()
