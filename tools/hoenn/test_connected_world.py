"""Offline checks for the integration candidate; do not certify its campaigns."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
VALIDATION = ROOT / 'mods/hoenn/integration-validation'


class ConnectedWorldTests(unittest.TestCase):
    def test_sixteen_native_starting_homes_match_the_candidate(self):
        prep = json.loads((VALIDATION / 'family-preparation.json').read_text())
        runtime = json.loads((VALIDATION / 'family.json').read_text())
        world = json.loads((VALIDATION / 'connected-world.json').read_text())
        self.assertTrue(runtime['passed'])
        self.assertEqual(runtime['rom_sha256'], world['rom_sha256'])
        self.assertEqual(len(runtime['cities'][:16]), 16)
        self.assertEqual(len(prep['homes']), 16)
        self.assertTrue(runtime['hoenn_origin_control']['passed'])
        self.assertTrue(runtime['hoenn_origin_control']['no_late_city_chooser'])
        self.assertEqual({c['starter_species'] for c in runtime['cities'][1:16]}, {1, 4, 7})
        for home, check in zip(prep['homes'], runtime['cities']):
            self.assertEqual(check['house'], home['house'])
            self.assertEqual(check['people'], home['people'])
            self.assertTrue(check['real_city_menu'])
            self.assertTrue(check['fixed_house_alias_only'])
            self.assertTrue(check['actual_stairs_and_door'])
            self.assertTrue(check['family_gifts_once'])
            self.assertFalse(check['full_story_validated'])
            if home['index'] > 1:
                self.assertTrue(check['original_mother_heal'])
                self.assertTrue(check['native_save_roundtrip'])
                self.assertEqual(check['starter_level'], 5)
        self.assertTrue(runtime['cities'][3]['full_bag_and_partial_retry'])
        self.assertTrue(prep['one_fixed_house_per_city'])
        self.assertFalse(prep['additional_hoenn_starts'])
        self.assert_final_layer_hashes(prep, ['travel-rules', 'birth', 'wild', 'habitats', 'sanctuaries', 'ecology'])

    def test_thirty_one_birth_choices_and_native_travel_rules(self):
        prep = json.loads((VALIDATION / 'birth-preparation.json').read_text())
        runtime = json.loads((VALIDATION / 'family.json').read_text())
        rules = json.loads((VALIDATION / 'birth-rules.json').read_text())
        world = json.loads((VALIDATION / 'connected-world.json').read_text())
        self.assertEqual(len(prep['homes']), 31)
        self.assertEqual(len(runtime['cities']), 30)
        self.assertEqual(runtime['rom_sha256'], rules['rom_sha256'])
        self.assertEqual(rules['rom_sha256'], world['rom_sha256'])
        self.assertTrue(rules['passed'])
        self.assertEqual(len(rules['checks']), 5)
        for home, check in zip(prep['homes'][17:], runtime['cities'][16:]):
            self.assertEqual(home['house'], check['house'])
            for name in ['real_city_menu', 'selection_before_motion', 'fixed_house_alias_only',
                         'actual_stairs_and_door', 'family_gifts_once', 'native_save_roundtrip', 'original_mother_heal']:
                self.assertTrue(check[name])
            self.assertIn(check['starter_species'], [252, 255, 258])
            self.assertEqual(check['starter_level'], 5)
        boats = {a['city'] for a in prep['arrivals'] if a['vehicle'] == 'boat'}
        self.assertTrue({'Pacifidlog', 'Dewford', 'Mossdeep', 'Sootopolis'} <= boats)
        self.assertTrue(all(a['vehicle'] == 'boat' for a in prep['arrivals'][9:16]))
        self.assertFalse(any(p.endswith('map.bin') for p in prep['prepared_sha256']))
        self.assert_final_layer_hashes(prep, ['wild', 'habitats', 'sanctuaries', 'ecology'])
        travel = json.loads((VALIDATION / 'travel-rules-preparation.json').read_text())
        self.assertFalse(travel['following_pokemon_enabled'])
        self.assert_final_layer_hashes(travel, ['birth', 'wild', 'habitats', 'sanctuaries', 'ecology'])

    def assert_final_layer_hashes(self, prep, later_names):
        expected = dict(prep['prepared_sha256'])
        for name in later_names:
            later = json.loads((VALIDATION / (name + '-preparation.json')).read_text())
            for path in expected.keys() & later['prepared_sha256'].keys():
                self.assertEqual(later['original_sha256'][path], expected[path])
                expected[path] = later['prepared_sha256'][path]
        reproduction = json.loads((VALIDATION / 'world-reproduction.json').read_text())
        for path, digest in expected.items():
            self.assertEqual(reproduction['prepared_sha256'][path], digest)

    def test_opposite_sex_rival_keeps_blue_and_other_trainers(self):
        prep = json.loads((VALIDATION / 'rival-preparation.json').read_text())
        runtime = json.loads((VALIDATION / 'connected-world.json').read_text())
        check = next(c for c in runtime['checks'] if c['check'] == 'opposite_sex_kanto_rival')
        self.assertEqual(check['player_genders'], [0, 1])
        self.assertEqual(check['rival_teams'], len(prep['rival_trainer_ids']))
        self.assertEqual(check['trainer_portraits_checked'], 3102)
        self.assertEqual(check['male_player_rival'], 'Leaf')
        self.assertEqual(check['female_player_rival'], 'Red')
        for invariant in ['real_lab_battle_starts', 'blue_leader_preserved',
                          'non_rival_portraits_preserved', 'overworld_graphics_resolved',
                          'dynamic_graphics_resolved', 'native_intro_assets_checked']:
            self.assertTrue(check[invariant])
        self.assertFalse(check['victories_simulated'])
        self.assertFalse(check['full_intro_and_naming_flow_validated'])
        self.assertTrue(prep['parties_and_event_scripts_unchanged'])
        self.assertTrue(prep['hoenn_rival_preserved'])
        self.assert_final_layer_hashes(prep, ['family', 'travel-rules', 'birth', 'wild', 'habitats', 'sanctuaries', 'ecology'])

    def test_early_ferry_preserves_regional_progress_and_ticket(self):
        prep = json.loads((VALIDATION / 'ferry-preparation.json').read_text())
        runtime = json.loads((VALIDATION / 'connected-world.json').read_text())
        check = next(c for c in runtime['checks'] if c['check'] == 'early_ticketed_interregional_ferry')
        self.assertEqual(check['ports_tested'], len(prep['ports']))
        self.assertEqual(len(check['trips']), 16)
        self.assertEqual({tuple(trip) for trip in check['trips']},
                         {(0, i) for i in range(1, 9)} | {(i, 0) for i in range(1, 9)})
        for invariant in ['real_npc_interactions', 'actual_menu_inputs', 'zero_badges',
                          'ticket_reusable', 'full_key_pocket_retry', 'cancel_and_back',
                          'duplicate_ticket_prevented', 'on_foot_arrivals',
                          'regional_format_switches', 'mission_flags_unchanged',
                          'native_flash_save_roundtrip']:
            self.assertTrue(check[invariant])
        self.assertTrue(prep['native_port_scripts_unchanged'])
        self.assertFalse(prep['boat_interior_or_sailing_animation'])
        self.assertFalse(prep['full_story_validated'])
        self.assert_final_layer_hashes(prep, ['rival', 'family', 'travel-rules', 'birth', 'wild', 'habitats', 'sanctuaries', 'ecology'])

    def test_three_water_hms_and_terrestrial_tm_conversion(self):
        prep = json.loads((VALIDATION / 'water-hms-preparation.json').read_text())
        runtime = json.loads((VALIDATION / 'connected-world.json').read_text())
        check = next(c for c in runtime['checks'] if c['check'] == 'three_water_hms_and_family_package')
        self.assertEqual(prep['hms'], ['SURF', 'DIVE', 'WATERFALL'])
        self.assertEqual(check['water_hms'], prep['hms'])
        self.assertEqual(check['terrestrial_tms'], {'CUT': 51, 'FLY': 52, 'STRENGTH': 53, 'FLASH': 54, 'ROCK_SMASH': 55})
        self.assertEqual(check['native_move_types'], {'CUT': 'GRASS', 'STRENGTH': 'ROCK'})
        for invariant in ['native_machine_table_checked', 'native_hm_classification',
                          'squirtle_can_learn_all_three', 'mothers_in_both_regions', 'zero_badges',
                          'dive_without_badges', 'native_zero_badge_dive_roundtrip', 'shared_gift_no_duplicates',
                          'full_pocket_and_partial_delivery_retry', 'whirlpool_is_not_hm']:
            self.assertTrue(check[invariant])
        self.assertTrue(prep['requires_new_save'])
        self.assertFalse(prep['full_story_validated'])

    def test_space_center_completion_survives_native_rival_call(self):
        prep = json.loads((VALIDATION / 'story-completion-preparation.json').read_text())
        runtime = json.loads((VALIDATION / 'connected-world.json').read_text())
        check = next(c for c in runtime['checks'] if c['check'] == 'space_center_completion_survives_rival_call')
        self.assertEqual(check['state_combinations'], 72)
        for invariant in ['native_rival_call_executed', 'call_does_not_repeat', 'native_steven_dive_gift',
                          'dive_without_tate_liza_badge', 'archie_permission_preserved',
                          'physical_eighth_gym_entry', 'native_flash_save_roundtrip']:
            self.assertTrue(check[invariant])
        self.assertTrue(check['battle_victory_simulated'])
        self.assertTrue(prep['native_rayquaza_call_unchanged'])
        self.assertFalse(prep['new_flags_allocated'])
        reproduction = json.loads((VALIDATION / 'world-reproduction.json').read_text())
        self.assertEqual(reproduction['prepared_sha256']['src/journey_campaign_gates.c'],
                         prep['prepared_sha256']['src/journey_campaign_gates.c'])
        self.assertFalse(prep['full_story_validated'])

    def test_first_badge_reward_survives_region_change_and_full_bag(self):
        prep = json.loads((VALIDATION / 'story-access-preparation.json').read_text())
        runtime = json.loads((VALIDATION / 'connected-world.json').read_text())
        check = next(c for c in runtime['checks'] if c['check'] == 'first_badge_flute_native_rewards')
        self.assertEqual(set(check['gyms']), {g['map'] for g in prep['gyms']})
        self.assertEqual(len(check['gyms']), 16)
        self.assertEqual(sum(g['kanto'] for g in prep['gyms']), 8)
        for invariant in ['no_reward_before_badges', 'repeated_reward_no_duplicate',
                          'full_bag_retry', 'hoenn_reward_recognized_by_fuji', 'other_region_badges_unchanged']:
            self.assertTrue(check[invariant])
        self.assertTrue(check['battle_victory_simulated'])
        self.assertTrue(prep['snorlax_encounters_unchanged'])
        self.assertTrue(prep['mr_fuji_rescue_preserved'])
        self.assertTrue(prep['magma_emblem_quest_preserved'])
        self.assertFalse(prep['full_story_validated'])

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
        self.assertTrue(access['dive_without_badges'])
        self.assertFalse(access['dive_rule_preserved'])
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

    def test_cycling_gates_still_require_a_bicycle_quest(self):
        runtime=json.loads((VALIDATION/'connected-world.json').read_text())
        bike=next(c for c in runtime['checks']if c['check']=='bike_quests_and_acro_replacements')
        self.assertEqual(bike['bike_gate_cases'],8)
        self.assertTrue(bike['cycling_locked_without_bike'])
        self.assertTrue(bike['cycling_open_after_bike'])
        self.assertTrue(bike['only_mach_awarded'])
        self.assertTrue(bike['registered_bike_preserved'])
        self.assertEqual(set(bike['reward_scripts']),{'MauvilleCity_BikeShop','CeruleanCity_BikeShop_Frlg'})
        self.assertFalse(bike['full_bicycle_quests_validated'])

    def test_acro_replacements_and_aqua_passages_preserve_missions(self):
        prep=json.loads((VALIDATION/'mach-bike-preparation.json').read_text())
        self.assertEqual(len(prep['replacements']),81)
        self.assertEqual({c['kind']for c in prep['replacements']},{'stairs','wood_bridge'})
        self.assertEqual(len(prep['completed_bridge_gaps']),1)
        self.assertEqual(len(prep['decorative_under_bridge_tiles_preserved']),4)
        self.assertEqual(prep['only_obtainable_bike'],'ITEM_MACH_BIKE')
        self.assertTrue(prep['stairs_draw_below_player'])
        jagged=[c for c in prep['replacements']if c['layout']=='LAYOUT_JAGGED_PASS']
        landings=[c for c in jagged if c['surface']=='landing']
        self.assertEqual(len(landings),5)
        self.assertTrue(all(c['after']==0x3271 for c in landings))
        self.assertTrue(all(c['after']==0x02AF for c in jagged if c['surface']=='yellow_stair'))
        road=json.loads((VALIDATION/'road-access-preparation.json').read_text())
        self.assertEqual(len(road['relocations']),7)
        self.assertTrue(road['mission_flags_unchanged'])
        self.assertEqual({e['path'][-1]for e in road['event_changes']},{'x','y'})
        runtime=json.loads((VALIDATION/'connected-world.json').read_text())
        bike=next(c for c in runtime['checks']if c['check']=='bike_quests_and_acro_replacements')
        self.assertEqual(bike['converted_tiles'],81)
        self.assertEqual(bike['physical_replacement_walks'],5)
        self.assertTrue(bike['stairs_draw_below_player'])
        self.assertTrue(bike['yellow_stair_matches_native_lateral'])
        self.assertTrue(bike['upper_landings_have_no_stair'])
        self.assertEqual(bike['physical_aqua_passages'],2)
        self.assertTrue(bike['aqua_missions_unchanged'])

    def test_all_acro_cliff_passages_have_native_yellow_stairs(self):
        prep=json.loads((VALIDATION/'yellow-stairs-preparation.json').read_text())
        self.assertTrue(prep['foreground_pixels_identical'])
        self.assertTrue(prep['foreground_palette_identical'])
        self.assertTrue(prep['original_lilycove_pixels_preserved'])
        self.assertTrue(prep['palette_12_previously_unused'])
        self.assertFalse(prep['requires_bicycle'])
        self.assertEqual(len(prep['replacements']),3)
        middle=next(c for c in prep['replacements']if c['surface']=='landing')
        self.assertEqual((middle['x'],middle['y'],middle['after']),(22,22,0x5001))
        runtime=json.loads((VALIDATION/'connected-world.json').read_text())
        check=next(c for c in runtime['checks']if c['check']=='all_acro_cliff_passages_yellow')
        self.assertEqual(check['passages'],6)
        self.assertEqual(check['on_foot_traversals'],12)
        self.assertEqual(check['yellow_stair_cells'],11)
        self.assertEqual(check['clear_landings'],6)

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
