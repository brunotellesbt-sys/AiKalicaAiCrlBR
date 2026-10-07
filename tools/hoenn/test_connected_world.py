"""Offline checks for the integration candidate; do not certify its campaigns."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
VALIDATION = ROOT / 'mods/hoenn/integration-validation'


class ConnectedWorldTests(unittest.TestCase):
    def test_square_cartography_and_provenance(self):
        data = json.loads((ROOT / 'web/world-layout.json').read_text())
        self.assertEqual(data['width'], data['height'])
        self.assertEqual(data['cinnabar_south_endpoint'], 'MAPSEC_ROUTE_114')
        self.assertFalse(data['full_story_validated'])
        for path, key in [('web/world-layout.svg', 'svg_sha256'), ('tools/hoenn/world_layout.py', 'generator_sha256'),
                          ('web/world-map.json', 'atlas_sha256')]:
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), data[key])

    def test_eastern_rows_and_route131(self):
        east = json.loads((VALIDATION / 'eastern-ocean-preparation.json').read_text())
        self.assertEqual(east['cells'][:4], [[0, 0], [1, 0], [2, 0], [3, 0]])
        self.assertEqual(east['cells'][4:8], [[1, 1], [2, 1], [1, 2], [2, 2]])
        self.assertTrue(any(c['map'] == 'MAP_JOURNEYPACIFIDLOGSEA' and c['direction'] == 'down'
                            for c in east['connections']['Route131']))
        self.assertTrue(any(c['map'] == 'MAP_JOURNEYWORLDSEA06' and c['direction'] == 'right'
                            for c in east['connections']['JourneyPacifidlogSea']))

    def test_western_river_preserves_special_events(self):
        west = json.loads((VALIDATION / 'western-ocean-preparation.json').read_text())
        self.assertEqual(west['channels']['Route114'], [0, 12, 10, 24])
        self.assertTrue(west['superseded_crossing_disconnected'])
        # Both native Route114–Route115 land entrance and the new lake
        # entrance exist in distinct spans; all event hashes are retained.
        links = west['connections']['Route114']
        self.assertTrue(any(c['map'] == 'MAP_ROUTE115' and c['offset'] == 40 for c in links))
        self.assertTrue(any(c['map'] == 'MAP_JOURNEYWESTRIVER' and c['offset'] == 10 for c in links))
        self.assertEqual(set(west['preserved_event_sha256']['Route114']),
                         {'object_events', 'warp_events', 'coord_events', 'bg_events'})

    def test_story_and_badge_banks_have_no_id_collision(self):
        state = json.loads((VALIDATION / 'regional-state-preparation.json').read_text())
        allocated = [f['allocated'] for f in state['frlg_flags'].values()]
        self.assertEqual(len(allocated), 763)
        self.assertEqual(len(set(allocated)), len(allocated))
        self.assertTrue(all(3160 <= f < state['flags_count'] for f in allocated))
        self.assertTrue(set(allocated).isdisjoint(state['kanto_badges']))
        self.assertNotIn(state['kanto_champion'], allocated)
        self.assertTrue(state['requires_new_save'])

    def test_reproduction_and_runtime_checks_are_recorded(self):
        reproduction = json.loads((VALIDATION / 'world-reproduction.json').read_text())
        runtime = json.loads((VALIDATION / 'connected-world.json').read_text())
        self.assertTrue(reproduction['passed']); self.assertTrue(reproduction['idempotence'])
        self.assertEqual(reproduction['prepared_files'], len(reproduction['prepared_sha256']))
        self.assertTrue(reproduction['entire_eastern_sea_connected'])
        seams = [r for r in runtime['checks'] if r['check'] == 'physical_surf_seam']
        self.assertEqual(len(seams), 96)
        self.assertTrue(all(r['passed'] for r in runtime['checks']))
        self.assertTrue(any(r['check'] == 'regional_flags_and_native_save_roundtrip' for r in runtime['checks']))
        self.assertFalse(runtime['full_story_validated'])

    def test_three_eastern_entrances_and_fuchsia(self):
        coast=json.loads((VALIDATION/'east-coast-preparation.json').read_text())
        self.assertEqual(set(coast['channels']),{'Route125','Route127','Route129','Route19_Frlg'})
        self.assertTrue(coast['ever_grande_entrance_preserved'])
        self.assertEqual(coast['channels']['Route19_Frlg'],[20,24,40,54])
        links=coast['connections']['JourneyWorldSea00']
        left=[c for c in links if c['direction']=='left']
        self.assertEqual({c['offset'] for c in left},{0,24})

    def test_gym_levels_cover_both_regions_and_all_floors(self):
        scaling=json.loads((VALIDATION/'gym-scaling-preparation.json').read_text())
        self.assertEqual(len(scaling['gyms']),18)
        self.assertEqual(sum(g['kanto'] for g in scaling['gyms']),8)
        self.assertEqual(scaling['ace_levels'],[14,21,28,35,42,48,54,60])
        runtime=json.loads((VALIDATION/'connected-world.json').read_text())
        check=next(r for r in runtime['checks'] if r['check']=='native_gym_party_levels')
        self.assertTrue(check['passed'])
        self.assertEqual(check['parties'],840)
        self.assertFalse(check['access_or_free_order_validated'])

    def test_regional_story_checkpoints_and_native_door_guides(self):
        gates=json.loads((VALIDATION/'campaign-gates-preparation.json').read_text())
        self.assertEqual(gates['before_gym_ordinals'], {'kanto':[3,4],'hoenn':[3,6,7,7]})
        self.assertEqual(len(gates['cities']),16)
        state=json.loads((VALIDATION/'regional-state-preparation.json').read_text())
        used={f['allocated'] for f in state['frlg_flags'].values()} | set(state['kanto_badges']) | {state['kanto_champion']}
        self.assertTrue(used.isdisjoint(gates['guide_flags']))
        runtime=json.loads((VALIDATION/'connected-world.json').read_text())
        check=next(r for r in runtime['checks'] if r['check']=='regional_campaign_checkpoints_and_guides')
        self.assertTrue(check['passed']); self.assertEqual(check['city_guides'],16)
        self.assertEqual(check['state_combinations'],180)
        self.assertTrue(check['completion_hides_guides'])
        self.assertTrue(check['all_guide_dialogues_triggered'])
        self.assertTrue(check['dive_after_space_center_without_seventh_badge'])
        self.assertEqual(check['representative_completed_door_warps'],2)
        self.assertFalse(check['full_story_or_free_order_access_validated'])
        for path,template in [('src/journey_campaign_gates.c','campaign_gates.c'),
                              ('include/journey_campaign_gates.h','campaign_gates.h')]:
            self.assertEqual(gates['prepared_sha256'][path],
                hashlib.sha256((ROOT/'tools/hoenn'/template).read_bytes()).hexdigest())

    def test_team_stories_are_required_in_their_own_region(self):
        stories=json.loads((VALIDATION/'team-stories-preparation.json').read_text())
        self.assertEqual(stories['before_gym_ordinals'],{'kanto':[3,5,7],'hoenn':[3,5,6,8,8]})
        self.assertEqual(len(stories['new_maps']),2)
        self.assertEqual(len(stories['ocean_design']),27)
        ids=[t['id']for t in stories['trainers']]
        self.assertEqual(len(ids),72);self.assertEqual(len(set(ids)),72)
        self.assertLessEqual(max(ids),1622)
        self.assertTrue(all(m['badge_count']==4 for m in stories['missions']))
        rocket=next(m for m in stories['missions']if m['key']=='hoenn_rocket')
        self.assertFalse(rocket['kanto']);self.assertEqual(len(rocket['trainers']),9)
        self.assertTrue(all(m['kanto']for m in stories['missions']if m['key']!='hoenn_rocket'))
        runtime=json.loads((VALIDATION/'connected-world.json').read_text())
        check=next(c for c in runtime['checks']if c['check']=='regional_incursions_and_casino')
        self.assertEqual(check['individually_required_trainers'],28)
        self.assertTrue(check['regions_independent']);self.assertEqual(check['physical_stair_warps'],4)
        self.assertTrue(check['silph_after_six']);self.assertTrue(check['alliance_after_seven'])

    def test_giovanni_alliance_uses_native_multi_battle(self):
        runtime=json.loads((VALIDATION/'connected-world.json').read_text())
        battle=next(c for c in runtime['checks']if c['check']=='real_giovanni_tag_battle_start')
        self.assertTrue(battle['passed']);self.assertEqual(battle['opponents'],['ARCHIE','SHELLY'])
        self.assertEqual(battle['partner_id'],2)
        self.assertTrue(battle['battle_type_flags']&0x8000)
        self.assertTrue(battle['battle_type_flags']&0x40)
        self.assertEqual(battle['rendered_battlers'],4)
        self.assertTrue(battle['native_battle_screen_rendered'])
        self.assertFalse(battle['victory_aftermath_validated'])
        self.assertTrue((VALIDATION/'Giovanni-Archie-Shelly-tag-battle.png').exists())

    def test_native_free_order_access_preserves_missions_and_water(self):
        runtime=json.loads((VALIDATION/'connected-world.json').read_text())
        access=next(c for c in runtime['checks']if c['check']=='free_gym_doors_and_land_hms')
        self.assertEqual(access['physical_gym_entries'],16)
        self.assertEqual(access['norman_old_badge_states'],4)
        self.assertEqual(access['opened_boulder_barrier_tiles'],8)
        self.assertEqual(access['all_obstacles_catalogued'],336)
        self.assertEqual(len(access['obstacle_samples']),6)
        self.assertTrue(access['real_surf_prompt_without_badges'])
        self.assertTrue(access['dive_rule_preserved'])
        self.assertFalse(access['full_campaign_validated'])
        # Mission-door tests must still pass on the same ROM as free entries.
        gates=next(c for c in runtime['checks']if c['check']=='regional_campaign_checkpoints_and_guides')
        self.assertTrue(gates['blocked_door_movement']);self.assertEqual(gates['city_guides'],16)

    def test_blue_is_a_regular_scaled_gym_and_not_a_rocket_victory(self):
        prep=json.loads((VALIDATION/'blue-gym-preparation.json').read_text())
        self.assertEqual(prep['leader'],'Blue');self.assertFalse(prep['team_rocket_event'])
        self.assertLessEqual(prep['trainer_id'],1622)
        runtime=json.loads((VALIDATION/'connected-world.json').read_text())
        blue=next(c for c in runtime['checks']if c['check']=='blue_regular_gym_reward')
        self.assertTrue(blue['rocket_flags_unchanged']);self.assertTrue(blue['regional_badge_only'])
        self.assertTrue(blue['route22_after_all_eight'])
        self.assertTrue(blue['completed_final_rival_not_restarted'])
        self.assertTrue(blue['battle_victory_simulated'])
        parties=next(c for c in runtime['checks']if c['check']=='native_gym_party_levels')
        self.assertEqual(parties['parties'],840)

    def test_only_explicit_access_event_edits_are_recorded(self):
        prep=json.loads((VALIDATION/'free-access-preparation.json').read_text())
        self.assertEqual(len(prep['obstacles']),336)
        self.assertEqual(len({o['map']for o in prep['obstacles']}),77)
        self.assertEqual(prep['water_moves']['dive'],'unchanged')
        self.assertTrue(prep['norman_tutorial_preserved']);self.assertTrue(prep['requires_new_save'])
        self.assertFalse(prep['full_story_validated'])
        # Every source map is inspected, so this catalogue covers both regions.
        maps=[p for p in prep['input_sha256']if p.endswith('/map.json')]
        self.assertEqual(len(maps),939)


if __name__ == '__main__': unittest.main()
