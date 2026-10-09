"""All sanctuary routes and locked altar interactions in the current candidate."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / 'mods/hoenn/sanctuary-routes-validation'
def read(path): return json.loads((DIR / path).read_text())

class SanctuaryRoutes(unittest.TestCase):
    def native(self, path):
        r = read(path); self.assertTrue(r['passed'])
        expected = json.loads((ROOT / 'mods/hoenn/sky-pillar-validation/reproduction.json').read_text())
        self.assertEqual(r['rom_sha256'], expected['rom_sha256'])
        return r

    def test_all_fourteen_sites_have_reciprocal_native_walks(self):
        r = self.native('native/sanctuary-routes.json')
        prep = json.loads((ROOT / 'mods/hoenn/integration-validation/sanctuaries-preparation.json').read_text())
        self.assertEqual({s['site'] for s in r['sites']}, {s['theme'] for s in prep['sites']})
        self.assertEqual(len(r['sites']), 14)
        self.assertEqual(sum(s['access'] == 'surf' for s in r['sites']), 9)
        self.assertEqual(sum(s['access'] == 'dive' for s in r['sites']), 5)
        self.assertGreater(r['position_changes'], 1000)
        for site in r['sites']:
            self.assertEqual(site['initial_position'], site['final_position'])
            self.assertEqual(len(site['transitions']), 2)
            self.assertEqual(site['transitions'][0]['destination'][0], site['chamber'])
            expected = site['surface'] if site['access'] == 'surf' else 'JourneyDepth' + site['site']
            self.assertEqual(site['transitions'][1]['destination'][0], expected)
            if site['access'] == 'surf': self.assertTrue(site['native_surf_prompts'])
        self.assertTrue(r['native_dive_and_emerge_prompts'])
        self.assertTrue(r['no_internal_warps_or_field_effect_or_script_entries'])

    def test_every_special_altar_has_an_actual_refused_interaction(self):
        r = self.native('native/sanctuary-routes.json')
        prep = json.loads((ROOT / 'mods/hoenn/integration-validation/sanctuaries-preparation.json').read_text())
        self.assertEqual(len(r['altars']), 105)
        self.assertEqual({a['national_dex'] for a in r['altars']}, {c['national_dex'] for c in prep['captures']})
        self.assertEqual(len({a['national_dex'] for a in r['altars']}), 105)
        for altar in r['altars']:
            self.assertTrue(altar['native_interaction_refused'])
            self.assertFalse(altar['captured_flag']); self.assertFalse(altar['caught_dex'])
        for site in r['sites']:
            self.assertEqual(site['altars'], sum(a['site'] == site['site'] for a in r['altars']))

    def test_thirty_three_continues_preserve_land_surf_and_underwater_modes(self):
        r = self.native('native/sanctuary-routes.json')
        saves = r['save_continue']; self.assertEqual(len(saves), 33)
        self.assertEqual(sum(s['before']['mode'] == 1 for s in saves), 14)
        self.assertEqual(sum(s['before']['mode'] == 8 for s in saves), 14)
        self.assertEqual(sum(s['before']['mode'] == 16 for s in saves), 5)
        for saved in saves:
            self.assertEqual(saved['before'], saved['after'])
            self.assertEqual(saved['after']['kanto_badges'], 0)
            self.assertEqual(saved['after']['hoenn_badges'], 0)
            self.assertFalse(saved['after']['special_capture_unlocked'])
            self.assertTrue((DIR / 'native' / (saved['label'] + '-after-continue.png')).is_file())

    def test_emerald_sky_pillar_still_passes_after_mixed_layout_support(self):
        r = self.native('sky-pillar/sky-pillar-access.json')
        self.assertTrue(r['native_full_tower_walk_return_and_reentry'])
        self.assertTrue(r['native_early_awakening_trigger_refused'])
        self.assertEqual(len(r['save_continue']), 3)
        for saved in r['save_continue']: self.assertEqual(saved['before'], saved['after'])

    def test_evidence_does_not_claim_captures_balance_or_complete_campaigns(self):
        r = self.native('native/sanctuary-routes.json')
        self.assertTrue(r['initial_party_badges_and_fourteen_surface_positions_are_fixtures'])
        self.assertTrue(r['wild_encounters_disabled'])
        self.assertFalse(r['full_campaign_playthrough'])
        self.assertFalse(r['capture_or_balance_validated'])

if __name__ == '__main__': unittest.main()
