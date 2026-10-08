"""Native ferry and six-on-six PWT evidence after integration."""
import json
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[2]
VALIDATION = ROOT / 'mods/hoenn/frontier-travel-validation'

def report(path): return json.loads((VALIDATION / path).read_text())

class FrontierTravelRequirements(unittest.TestCase):
    def native(self, path):
        r = report(path)
        self.assertTrue(r['passed'])
        self.assertEqual(r['rom_sha256'], report('reproduction.json')['rom_sha256'])
        return r

    def test_replay_changes_only_native_port_ticket_guards(self):
        r = report('reproduction.json'); self.assertTrue(r['passed'])
        self.assertTrue(r['deterministic_replay']); self.assertTrue(r['idempotent'])
        self.assertEqual(r['files'], 2)
        self.assertEqual(r['baseline_rom_sha256'], json.loads((ROOT / 'mods/hoenn/pwt-validation/reproduction.json').read_text())['rom_sha256'])
        p = report('preparation.json')
        self.assertEqual(set(p['prepared_sha256']), {'data/maps/SlateportCity_Harbor/scripts.inc', 'data/maps/LilycoveCity_Harbor/scripts.inc'})
        for key in ['native_scott_invitation_retained', 'hoenn_champion_requirement_retained', 'ss_ticket_required_at_both_ports', 'ticket_not_consumed', 'save_layout_unchanged']:
            self.assertTrue(p[key])

    def test_native_ports_reject_missing_ticket_and_kanto_only_champion(self):
        baseline = report('baseline/frontier-travel-baseline.json')
        self.assertTrue(baseline['passed']); self.assertTrue(baseline['allows_boarding_without_ticket'])
        self.assertEqual(baseline['rom_sha256'], report('reproduction.json')['baseline_rom_sha256'])
        r = self.native('native/frontier-travel.json')
        self.assertEqual(len(r['guards']), 8)
        for g in r['guards']:
            self.assertEqual(g['destination_menu'], g['hoenn_champion'] and g['ticket'])
        self.assertEqual({g['port'] for g in r['guards']}, {'Slateport', 'Lilycove'})

    def test_first_cruise_cabin_and_frontier_round_trips(self):
        r = self.native('native/frontier-travel.json')
        self.assertTrue(r['first_native_cruise_scott_invitation'])
        self.assertTrue(r['physical_cabin_bed_and_arrival'])
        self.assertTrue(r['ticket_not_consumed']); self.assertTrue(r['native_flash_save_reload'])
        self.assertTrue(r['native_continue_rebuilds_map'])
        self.assertEqual([(t['origin'], t['destination']) for t in r['native_ferry_trips']], [('Lilycove', 'Slateport'), ('Slateport', 'Lilycove')])
        self.assertTrue(all(t['via'] == 'BattleFrontier' and t['ticket_quantity'] == 1 for t in r['native_ferry_trips']))
        self.assertTrue(r['initial_port_warps_and_champion_visibility_are_fixtures'])
        self.assertFalse(r['full_campaign_playthrough'])

    def test_pwt_round_remains_six_on_six_on_ferry_candidate(self):
        r = self.native('pwt/frontier-pwt.json')
        self.assertEqual(r['team_size'], 6)
        self.assertEqual(r['native_win']['outcome'], 1)
        self.assertGreater(r['native_win']['attacks'], 0)
        self.assertTrue(r['native_win']['bag_blocked'])
        for key in ['after_win_retirement', 'original_party_byte_identical', 'flags_money_and_bp_unchanged', 'native_flash_save_reload']:
            self.assertTrue(r[key])
        self.assertFalse(r['balance_validated'])

if __name__ == '__main__': unittest.main()
