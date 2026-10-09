"""Native puzzle crossings and retained sixteen-badge capture requirements."""
import json
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / 'mods/hoenn/story-puzzles-validation'
def read(path): return json.loads((DIR / path).read_text())

class StoryPuzzleDoors(unittest.TestCase):
    def test_strict_replay_changes_only_three_doors_and_shared_text(self):
        r = read('reproduction.json'); p = read('preparation.json')
        self.assertTrue(r['passed']); self.assertTrue(r['deterministic_replay']); self.assertTrue(r['idempotent'])
        self.assertEqual(r['files'], 4)
        self.assertEqual(r['baseline_rom_sha256'], json.loads((ROOT / 'mods/hoenn/frontier-travel-validation/reproduction.json').read_text())['rom_sha256'])
        self.assertEqual(set(p['prepared_sha256']), {'data/maps/DesertRuins/scripts.inc', 'data/maps/AncientTomb/scripts.inc', 'data/maps/SealedChamber_OuterRoom/scripts.inc', 'data/scripts/journey_campaign_gates.inc'})
        for key in ['dive_access_retained', 'inner_party_riddle_retained', 'regice_walking_puzzle_retained', 'sixteen_badges_capture_gate_retained', 'save_layout_unchanged']:
            self.assertTrue(p[key], key)
        self.assertFalse(p['new_flags_allocated']); self.assertFalse(p['full_campaign_validated'])

    def test_closed_baseline_and_native_inscription_crossings_survive_continue(self):
        old = read('baseline/story-puzzles.json'); new = read('native/story-puzzles.json')
        self.assertTrue(old['passed']); self.assertTrue(new['passed'])
        self.assertEqual(old['rom_sha256'], read('reproduction.json')['baseline_rom_sha256'])
        self.assertEqual(new['rom_sha256'], read('reproduction.json')['rom_sha256'])
        self.assertEqual(len(old['doors']), 3); self.assertEqual(len(new['doors']), 3)
        for door in old['doors']:
            self.assertFalse(door['opened_by_inscription']); self.assertFalse(door['physical_crossing'])
        for door in new['doors']:
            for key in ['opened_by_inscription', 'physical_crossing', 'no_moves_or_badges', 'native_save_reload_continue_and_recross']:
                self.assertTrue(door[key], key)
        self.assertTrue(new['original_inner_party_riddle_not_awarded']); self.assertTrue(new['badges_not_awarded'])
        self.assertFalse(new['full_campaign_playthrough'])

    def test_capture_permission_still_requires_eight_badges_in_both_regions(self):
        for r in [read('native/story-puzzles.json'), json.loads((ROOT / 'mods/hoenn/aqua-episodes-validation/puzzles/story-puzzles.json').read_text())]:
            self.assertTrue(r['passed'])
            self.assertEqual([(g['kanto_badges'], g['hoenn_badges'], g['capture_permission']) for g in r['capture_guard_combinations']], [(0, 0, False), (8, 0, False), (0, 8, False), (8, 8, True)])
            self.assertEqual(len(r['doors']), 3)
            self.assertTrue(all(d['physical_crossing'] and d['native_save_reload_continue_and_recross'] for d in r['doors']))
        final = json.loads((ROOT / 'mods/hoenn/aqua-episodes-validation/puzzles/story-puzzles.json').read_text())
        self.assertEqual(final['rom_sha256'], json.loads((ROOT / 'mods/hoenn/aqua-episodes-validation/reproduction.json').read_text())['rom_sha256'])

if __name__ == '__main__': unittest.main()
