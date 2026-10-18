"""Require exact-ROM native proofs for the extra circuit and marine repairs."""
import hashlib,json
from pathlib import Path
from package_review_rom import verify as verify_review
from verify_fuchsia_update import ROOT,previous_release

def verify_update(directory,info):
    directory=Path(directory);old=previous_release(info)
    assert old['validated'] and old['validation_scope']=='ever-grande-market'
    assert old['integration_layers']+['extra-gyms']==info['integration_layers']
    test=verify_review(ROOT/'roms/rom-de-teste',directory/'Pokemon-Journey-Gen1-9-Normal.gba')
    expected={'common':info['parent_rom_sha256'],'test':test['sha256'],**{r['file']:r['sha256'] for r in info['variants']}}
    covered=set()
    for p in info['proofs']:
        path=Path(p['file']);assert not path.is_absolute() and '..' not in path.parts
        raw=(directory/path).read_bytes();assert hashlib.sha256(raw).hexdigest()==p['sha256']
        r=json.loads(raw);assert r['passed'] and r['rom_sha256']==expected[p['target']]
        kind=p['kind'];covered.add((p['target'],kind))
        if kind=='extra-gym-source':
            assert p['target']=='common' and r['layers']==info['integration_layers']
            for k in ['independent_replay','idempotent','allocated_flags_disjoint','save_and_link_abi_unchanged','original_tm_hm_numbers_preserved','old_campaign_and_pwt_preserved','all_legendary_encounters_and_cave_doors_preserved','atlas_graphics_unchanged']:assert r[k],k
            assert r['source_hashes_checked']>30000 and len(r['gyms'])==8 and r['total_badges']==24
            assert len(r['room_checks'])==8 and len(r['gym_leader_sprites'])==8
            assert r['interior_themes_distinct'] and r['all_room_floors_connected'] and r['long_clear_trainer_sightlines'] and r['non_puzzle_rooms']
            assert all(room['three_wide_clear_trainer_approaches'] for room in r['room_checks'])
            assert all(room['guide_at_entrance'] and room['marked_path_crossed_by_each_trainer'] and room['thematic_entrance_display'] for room in r['room_checks'])
            assert len({tuple(tuple(d) for d in room['route_directions']) for room in r['room_checks']})==8
            assert all({c['facing'] for c in room['mandatory_checkpoints']}=={'UP','DOWN','LEFT','RIGHT'} for room in r['room_checks'])
            assert all(len(room['mandatory_checkpoints'])==4 and all(c['removing_sightline_disconnects_leader'] for c in room['mandatory_checkpoints']) for room in r['room_checks'])
            assert r['pending_story_milestones']==[18,22] and not r['pending_story_events_implemented']
        elif kind=='extra-gyms':
            assert r['roster_cases']==40 and len(r['gyms'])==8
            assert len({g['leader'] for g in r['gyms']})==8
            for g in r['gyms']:
                assert g['leader_win']['outcome']==1 and len(g['students'])==4
                for k in ['controller_entry_and_exit','guide_talked_near_entrance','badge_once','tm_once','tm_move_matches']:assert g[k],k
                for student in g['students']:
                    if p['target']=='test':assert student['automatic_approach_disabled'] and student['manual_battle']
                    else:assert student['approach']['native_walked_to_player'] and student['approach']['controller_entered_sightline_at_distance']>=2 and student['approach']['sight_range']==6 and student['approach']['mandatory_route_from_city']
                if p['target']!='test':assert g['all_four_battled_separately_on_mandatory_walk']
            for k in ['all_24_badges_saved_and_continued','actual_three_page_trainer_card','enemy_party_and_native_battle_outcome_not_written','reward_flags_not_written_during_battles']:assert r[k],k
            assert r['league']['both_leagues_require_24'] and len(r['league']['missing_badge_cases'])==24
            assert r['league']['old_story_and_galactic_completion_still_required']
        elif kind=='all-surf-links':
            assert r['all_usable_outdoor_surf_connections_covered'] and r['no_midcrossing_warps_or_coordinate_writes']
            assert len(r['links'])==r['usable_reciprocal_water_links']>150
            assert r['crossings']==2*len(r['links'])+len(r['native_current_links'])
            assert all(c['outbound_and_return'] and c['surf_preserved'] for c in r['links'])
            assert r['visible_outer_rock_checks'] and all(c['visible_rock_blocks_controller'] for c in r['visible_outer_rock_checks'])
            assert all(c['native_one_way_current_preserved'] and c['surf_preserved'] for c in r['native_current_links'])
        elif kind=='surf-repairs':
            assert r['links']==55 and r['crossings']==110 and len(r['checks'])==55 and r['apron_samples']>10000
            for k in ['all_repaired_links_walked_bidirectionally','no_midtrip_warps_or_coordinate_writes','surf_and_current_bank_checked_at_each_step','actual_controller_movement']:assert r[k],k
            assert not r['atlas_graphics_changed'] and r['solrock_loadout_checks']
            for c in r['checks']:
                for k in ['returned_to_departure','all_segments_walked','surf_continuous','loaded_tiles_match_current_bank','ocean_colors_identical']:assert c[k],k
        elif kind=='map-finishing':
            assert len(r['ports'])==7
            assert r['restored_center_wall_blocks_controller'] and r['center_door_roundtrip'] and r['native_save_continue_on_pier']
            assert r['six_obsolete_roof_removed'] and r['six_ramp_main_terminal_controller_roundtrip']
            assert r['all_seven_obsolete_roofs_removed'] and r['all_seven_ramp_main_terminal_controller_roundtrips'] and len(r['ramp_roundtrips'])==7
            assert r['one_treasure_beach_obsolete_terminal_completely_removed'] and r['one_treasure_beach_surf_controller_roundtrip']
            assert r['two_ramp_coast_finished'] and r['two_center_terminal_controller_roundtrip'] and r['two_ramp_coast_blocks_foot_and_surf'] and r['two_western_surf_preserved']
            assert all(c['obsolete_roof_absent'] and c['local_ocean_texture_preserved'] and c['native_ramp_tiles_and_warp_ids_preserved'] and c['native_north_arrow_return'] and c['controller_outbound_to_main_terminal'] and c['controller_return_to_town'] and c['foot_state_preserved'] for c in r['ramp_roundtrips'])
            assert all(row['controller_door_roundtrip'] and row['foot_blocks_at_pier_end'] and row['foot_state_on_dry_terminal'] and row['foot_drawn_above_bridge'] and row['surf_drawn_below_bridge'] and row['under_pier_surf_roundtrip'] for row in r['ports'])
        elif kind=='coastal-landings':
            assert r['beaches'] and r['decorative_collision_attempts']
            for k in ['all_repaired_beach_components_tested','input_only_landing_and_reembarkation','surf_ends_on_land','foot_cannot_enter_ocean_without_surf']:assert r[k],k
            expected_maps={row['map'] for row in json.loads((directory/'evidence/extra-gyms/common/extra-gym-source.json').read_text())['coastal_fixes']['geography']['beach_land_elevations']}
            assert expected_maps=={row['map'] for row in r['beaches']}
        elif kind=='luffy-approach':
            assert r['hero']=='Luffy' and r['standard_directional_frames']
            for k in ['spawn_entirely_outside_camera','actual_native_movement','lateral_facing_preserved','controller_dialogue_and_battle_entry','actor_coordinates_not_written']:assert r[k],k
            assert len(r['movement_actions'])>=6
        elif kind=='review-mode':
            assert r['review_mode']==(p['target']=='test') and not r['fixture_wild_encounters_disabled']
            assert bool(r['checks']['trainer_approach_result'])==(p['target']!='test')
            if p['target']=='test':
                c=r['checks'];assert c['random_wild_attempts']>=200 and c['native_flash_save_exported']
                for k in ['no_random_encounters','no_fishing_encounters','no_sweet_scent_encounters','no_rock_smash_encounters','no_automatic_approach_after_600_frames']:assert c[k],k
                assert hashlib.sha256((ROOT/'roms/rom-de-teste/Pokemon-Journey-TESTE.sav').read_bytes()).hexdigest()==c['save_sha256']
        elif kind in ['ever-grande-market','dewford-competitive-shop','fallarbor-physics','coastal-details','marine-network']:
            # These reports have feature-specific invariants checked below by
            # their source validators and exact current binary identities here.
            if kind=='ever-grande-market':
                assert r['market_actual_purchase'] and r['insufficient_money_rejected'] and r['market_price']==200000
                assert len(r['gifts'])==2 and all(g['bag_full_preserves_gift'] and g['repeat_talk_no_duplicate'] and g['controller_entry_and_exit'] for g in r['gifts'])
                assert r['save_continue_preserves_gifts_and_purchase'] and r['sootopolis_city_red']
            if kind=='dewford-competitive-shop':
                assert r['dewford_second_seller_restored'] and r['frontier_single_seller'] and r['two_attendants_interacted']
                assert r['single_cap_only_one_stat'] and r['gold_cap_all_six_stats'] and r['original_genetic_ivs_preserved']
                assert r['legendary_caves']['total_species']==105 and len(r['legendary_caves']['groups'])==48
                assert len(r['purchases'])==3 and r['prices_checked']==71
            if kind=='fallarbor-physics':
                for k in ['beach_walkable_on_foot','native_surf_prompt','native_disembark_before_city','city_reachable_on_foot','rock_limit_blocks_controller','complete_tree_overhang_blocks_surf','northern_southern_and_river_connections_bidirectional','surfing_observed_only_on_water','native_save_continue_preserves_land_and_foot_state','no_midroute_warps_or_coordinate_writes']:assert r[k],k
            if kind=='coastal-details':
                assert {c['map'] for c in r['dewford_shores']}=={'DewfordTown','Route107'}
                assert all(c['native_disembark'] and c['native_surf_prompt'] and c['native_southern_terrain_restored'] and c['original_south_art_and_elevations_match_compiled_rom'] and c['original_border_retained'] for c in r['dewford_shores'])
                for k in ['two_dewford_vendors_interacted','dewford_purchase','luffy_native_directional_frames','full_cave_crowns']:assert r[k],k
            if kind=='marine-network':
                assert r['all_seven_islands_reached_from_mossdeep'] and r['kanto_to_one_island_and_back'] and r['returned_to_mossdeep']
                assert r['controller_movement_only'] and r['no_midtrip_warps_or_coordinate_writes'] and r['all_surf_samples_on_water']
                assert len(r['towns'])==7 and hashlib.sha256((ROOT/'docs/videos/surf-connections-repaired.mp4').read_bytes()).hexdigest()==r['video_sha256']
        else:raise AssertionError(kind)
    required={('common','extra-gym-source'),('common','all-surf-links'),('common','surf-repairs'),('common','coastal-details'),('common','marine-network'),('common','luffy-approach'),('common','coastal-landings'),('common','map-finishing')}
    required|={(t,k) for t in expected if t!='common' for k in ['extra-gyms','review-mode','ever-grande-market','dewford-competitive-shop','fallarbor-physics']}
    assert required<=covered,required-covered
    assert all((directory/r['file']).read_bytes()[test['review_mode_offset']]==0 for r in info['variants'])
    ref=info['previous_review_validation'];p=Path(ref['file']);assert not p.is_absolute() and '..' not in p.parts
    raw=(ROOT/p).read_bytes();assert hashlib.sha256(raw).hexdigest()==ref['sha256']
    from verify_ever_grande_update import verify_update as verify_previous
    verify_previous(directory,old,historical_review=json.loads(raw))
