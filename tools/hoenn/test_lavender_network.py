"""Native evidence for the world ferry network, animation and preserved quests."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / 'mods/hoenn/lavender-network-validation'

def read(name):
    return json.loads((DIR / name).read_text())

class LavenderNetwork(unittest.TestCase):
    def test_every_port_has_actual_roundtrip_and_animation_evidence(self):
        r = read('native/lavender-network.json')
        self.assertTrue(r['passed'] and r['all_ports_visited'])
        self.assertTrue(r['actual_captain_interactions'] and r['actual_menu_choices'])
        self.assertTrue(r['no_midtrip_fixture_warps'] and r['save_continue'])
        self.assertTrue(r['all_arrivals_on_walkable_dry_tiles'])
        self.assertTrue(r['all_world_voyages_animated'])
        self.assertEqual([(t['origin'],t['destination']) for t in r['trips']], [(i,(i+1)%18) for i in range(18)])
        self.assertTrue(all(t['scene_observations'] >= 5 for t in r['trips']))
        self.assertTrue(all((DIR/f'native/port-{i}-voyage.png').is_file() for i in range(18)))
        self.assertFalse(r['full_campaign_playthrough'])
        self.assertEqual(r['rom_sha256'],read('preparation/reproduction.json')['rom_sha256'])

    def test_native_seagallop_destination_branch_still_works_both_ways(self):
        r = read('native/lavender-network.json')
        self.assertEqual([(t['origin'],t['destination']) for t in r['legacy_seagallop_trips']],[(0,1),(1,0)])
        self.assertTrue(all(t['scene_observations']>=5 for t in r['legacy_seagallop_trips']))
        self.assertEqual(r['legacy_seagallop_trips'][0]['position'],[8,5])
        self.assertEqual(r['legacy_seagallop_trips'][1]['position'],[23,32])

    def test_native_menus_exclude_the_current_port(self):
        r = read('native/lavender-network.json')
        self.assertEqual({a['origin'] for a in r['self_audits']},set(range(18)))
        for a in r['self_audits']:
            self.assertNotIn(a['current'],a['native_labels'])
        p = read('preparation/preparation.json')
        for m in p['menus']:
            self.assertNotIn(m['origin'],m['destinations'])
            self.assertLessEqual(len(m['destinations'])+1,8)

    def test_frontier_needs_all_three_native_prerequisites(self):
        r = read('native/lavender-network.json')
        self.assertEqual([(g['champion'],g['ticket'],g['scott']) for g in r['frontier_guards']],[(False,False,False),(False,True,True),(True,False,True),(True,True,False)])
        self.assertTrue(all(g['blocked'] for g in r['frontier_guards']))
        self.assertIn({'origin':14,'destination':15,'scene_observations':r['trips'][14]['scene_observations']},r['trips'])

    def test_overlay_replays_without_changing_shipyard_or_campaign_code(self):
        p = read('preparation/preparation.json')
        r = read('preparation/reproduction.json')
        self.assertTrue(r['passed'] and r['deterministic_replay'] and r['idempotent'])
        self.assertEqual(r['files'],len(p['prepared_sha256']))
        self.assertTrue(p['shipyard_terrain_preserved'])
        self.assertTrue(p['lavender_port_name'])
        self.assertTrue(read('native/lavender-network.json')['lavender_region_map_is_kanto'])
        for path in ['data/layouts/JourneyRoute12Shipyard/map.bin','src/journey_campaign_gates.c','src/journey_gym_scaling.c','src/journey_pwt.c','data/maps/SSTidalCorridor/scripts.inc','data/maps/SSAnne_CaptainsOffice_Frlg/scripts.inc']:
            self.assertIn(path,p['preserved_native_sha256'])
            self.assertNotIn(path,p['prepared_sha256'])
        self.assertIn('src/seagallop.c',p['prepared_sha256'])

if __name__ == '__main__':
    unittest.main()
