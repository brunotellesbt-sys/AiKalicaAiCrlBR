"""Verify exact layer-165 resource proofs and preserve layer-164 evidence."""
import hashlib
import json
from pathlib import Path

from generated_world_contract import BASELINE_SHA256, PREPARED_SHA256, SCOPE
from package_review_rom import verify as verify_review
from publish_coastal_closures import report_dependencies
from verify_coastal_closures_update import verify_cold_boot, verify_review_mode, verify_shore_animation
from verify_fuchsia_update import ROOT, previous_release
from verify_sevii_integrated_piers_update import require_true


COMMON_KINDS = frozenset({
    'generated-world-source', 'generated-navigation', 'generated-cave-routes',
    'generated-shore-animation-source-census', 'generated-shore-animation-native-banks',
    'generated-gym-native-walk', 'generated-ever-grande', 'surf-repairs',
    'integrated-piers', 'dewford-movement', 'shore-animation',
})
EDITION_KINDS = frozenset({'review-mode', 'cold-boot'})
OPTIONAL_COMMON_KINDS = frozenset({'qualifier-event', 'badge-gates', 'generated-pwt-access',
                                  'coastal-cave-access'})


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def baseline(name, raw):
    assert hashlib.sha256(raw).hexdigest() == BASELINE_SHA256[name], ('Layer 164 baseline changed', name)
    if name == 'versions.json':
        old = json.loads(raw)
        assert old['validated'] is True and old['validation_scope'] == 'badge-story'
        assert len(old['integration_layers']) == 164 and len(old['proofs']) == 26
        return old
    if name == 'test.sav':
        assert len(raw) == 131072


def verify_proof(report, directory, kind, is_test, save, info, old):
    if kind != 'generated-shore-animation-source-census':
        assert report['passed'] is True, kind
    if 'kind' in report:
        assert report['kind'] == kind
    if kind in {'review-mode', 'cold-boot', 'generated-gym-native-walk'}:
        assert report.get('review_mode', is_test) is is_test
    if kind == 'generated-world-source':
        assert report['layers'] == info['integration_layers']
        assert report['parent_rom_sha256'] == old['parent_rom_sha256']
        assert report['prepared_sha256'] == PREPARED_SHA256
        assert set(report['changed_files']) == set(PREPARED_SHA256)
        assert len(report['changed_files']) == len(PREPARED_SHA256)
        assert report['source_hashes_checked'] >= 32240
        assert report['compiled_rom'] is True and report['preflight'] is False
        require_true(report, ['independent_replay', 'idempotent', 'unrelated_source_files_unchanged',
                              'atlas_graphics_unchanged', 'campaign_and_save_abi_source_unchanged'])
        blocks = report['compiled_blockdata']
        assert {r['file'] for r in blocks} == {name for name in PREPARED_SHA256 if name.endswith('.bin')}
        assert all(r['sha256'] == PREPARED_SHA256[r['file']] and r['bytes'] > 0 for r in blocks)
    elif kind == 'generated-navigation':
        require_true(report, ['graph_passed', 'native_passed', 'native_all_planned_cases_executed',
                              'compiled_behavior_and_collision_graph', 'forced_ocean_currents_respected',
                              'native_directional_input', 'initial_placements_party_and_defeated_trainer_flags_are_fixtures'])
        assert report['surface_maps'] == 417 and report['reviewed_edge_count'] == 470
        assert report['nonreciprocal_edges'] == report['disconnected_generated_ocean_maps'] == []
        cases, planned = report['native_cases'], report['planned_native_cases']
        assert len(cases) == len(planned) == report['native_case_count'] == report['planned_native_case_count'] == 990
        assert [c['index'] for c in cases] == list(range(len(cases)))
        for index, row in enumerate(cases):
            assert row['passed'] is True
            assert all(row[key] == value for key, value in planned[index].items())
            assert row['mode'] in {'surf', 'walk'}
            assert row['observed']['position'] == row['end']
            assert row['observed']['surf'] is (row['mode'] == 'surf')
            assert row['observed']['loaded_block'] == row['observed']['expected_block']
        for mode in ('surf', 'walk'):
            assert report['native_'+mode+'_case_count'] == sum(row['mode'] == mode for row in cases) == \
                   sum(row['mode'] == mode for row in planned) > 0
    elif kind == 'generated-cave-routes':
        require_true(report, ['retired_lodge_exits_fixed_in_selected_source',
                              'no_coordinate_writes_or_internal_warps_during_routes', 'wild_encounters_disabled'])
        caves = report['caves']
        assert len(caves) == len({r['map'] for r in caves}) == 26
        assert all(r['controller_entry_and_return'] is True and r['walked_tiles'] > 0 for r in caves)
        assert report['npc_approaches'] == sum(len(r['npc_approaches']) for r in caves) > 0
        exits = report['retired_lodge_save_continue']
        assert len(exits) == len({r['map'] for r in exits}) == 7
        assert all(r['native_save_continue'] is r['controller_exit'] is True for r in exits)
        # Dive/emerge proof is deliberately independent from a fixture that
        # merely begins already underwater. Its schema is bound below once
        # the controller runner has completed all five native roundtrips.
        dives = report['dive_roundtrips']
        assert report['all_cases_executed'] is True
        assert len(dives) == len({r['depth'] for r in dives}) == 5
        assert all(r['native_dive_and_emerge_prompts'] is r['controller_cave_entry_and_return'] is
                   r['native_underwater_surf_and_walking_modes'] is True for r in dives)
        assert all(r['initial_position'] == r['returned_position'] and r['walked_tiles'] > 0 for r in dives)
    elif kind == 'generated-shore-animation-source-census':
        assert report['source_only'] is True and report['native_animation_proof'] is False
        assert report['maps_inspected'] == len(report['maps']) == 901
        assert report['active_bank_pairs'] == 44
        assert report['maps_referencing_active_shore_graphics'] == 446
    elif kind == 'generated-shore-animation-native-banks':
        require_true(report, ['compiled_rom', 'native_validation_performed',
                              'hardware_matched_native_shore_pixels_verified',
                              'no_animation_clock_callback_palette_or_vram_writes'])
        assert report['source_maps_inspected'] == 901 and report['source_active_bank_pairs'] == 44
        observations = report['observations']
        assert report['native_bank_pairs'] == len({tuple(r['bank_pair']) for r in observations}) == 43
        assert report['native_maps_sampled'] == len(observations)
        coasts = {'OneIsland_Frlg', 'TwoIsland_Frlg', 'ThreeIsland_Port_Frlg',
                  'FourIsland_Frlg', 'FiveIsland_Frlg', 'SixIsland_Frlg', 'SevenIsland_Frlg'}
        assert coasts <= {r['map'] for r in observations}
        assert report['captures']
        for row in observations:
            require_true(row, ['all_eight_ocean_phases_observed', 'no_animation_clock_callback_palette_or_vram_writes'])
            assert row['hardware_matched_changing_shore_pixels']
            channels = row['native_animation_channels']
            assert set(channels) == {'water', 'foam'}
            assert all(channel['every_source_phase_seen'] is True and
                       len(channel['observed_frame_sha256']) == channel['unique_source_frames'] >= 2
                       for channel in channels.values())
    elif kind == 'generated-gym-native-walk':
        require_true(report, ['native_validation_performed', 'compiled_rom',
                              'doors_and_movement_use_controller',
                              'battle_outcomes_and_post_victory_flags_not_written'])
        gyms = report['gyms']
        assert len(gyms) == 8 and all(len(row['students']) == 4 and row['controller_entry_and_exit'] for row in gyms)
        assert report['trainer_battles'] == 32 and report['leader_battles'] == 8
        assert report['automatic_approaches'] == (0 if is_test else 32)
        if not is_test:
            assert all(row['all_four_battled_separately_on_mandatory_walk'] for row in gyms)
            assert all(win['approach']['native_walked_to_player'] for row in gyms for win in row['students'])
    elif kind == 'generated-ever-grande':
        assert report['physical_market_access_and_native_shop'] is True
        gifts = report['gifts']
        assert len(gifts) == 2 and {r['item'] for r in gifts} == {32, 34}
        assert len({r['map'] for r in gifts}) == 2
        assert all(r['after'] == r['before'] + 1 and r['physical_door_entry_and_exit'] and
                   r['native_gift_once'] and r['repeat_conversation_does_not_duplicate'] for r in gifts)
    elif kind == 'surf-repairs':
        assert report['links'] == len(report['checks']) == 55 and report['crossings'] == 110
        require_true(report, ['all_repaired_links_walked_bidirectionally', 'no_midtrip_warps_or_coordinate_writes',
                              'surf_and_current_bank_checked_at_each_step', 'actual_controller_movement'])
        assert report['atlas_graphics_changed'] is False
        assert all(r['returned_to_departure'] and r['all_segments_walked'] and r['surf_continuous'] and
                   r['loaded_tiles_match_current_bank'] and r['ocean_colors_identical'] for r in report['checks'])
        assert report['solrock_loadout_checks'] and all(394 not in r['moves'] for r in report['solrock_loadout_checks'])
    elif kind == 'integrated-piers':
        require_true(report, ['native_controller_terminal_roundtrip', 'native_surf_departure_and_reboard',
                              'native_avatar_pixels_checked', 'exact_current_vram_frame_compared',
                              'no_midtrip_coordinate_or_elevation_writes'])
        assert len(report['ports']) == 7 and report['captures']
        from verify_sevii_integrated_piers_update import verify_integrated_piers
        verify_integrated_piers(report, directory)
    elif kind == 'dewford-movement':
        from verify_coastal_closures_update import verify_dewford_movement
        verify_dewford_movement(report, directory)
    elif kind == 'shore-animation':
        verify_shore_animation(report, directory)
    elif kind == 'review-mode':
        verify_review_mode(report, is_test, save)
    elif kind == 'cold-boot':
        verify_cold_boot(report, is_test, save)
    elif kind in {'qualifier-event', 'badge-gates'}:
        from verify_badge_story_update import NATIVE_VERIFIERS
        NATIVE_VERIFIERS[kind](report, directory)
    elif kind == 'generated-pwt-access':
        require_true(report, ['compiled_rom', 'native_validation_performed', 'native_guide_interaction',
                              'physical_counter_walk', 'native_selection_cancel', 'physical_exit_door_returns_to_dome'])
    elif kind == 'coastal-cave-access':
        require_true(report, ['native_controller_entries_and_returns', 'no_internal_warps_or_coordinate_writes',
                              'initial_surface_positions_and_party_are_fixtures', 'legendary_capture_rules_preserved'])
        caves = report['caves']
        assert len(caves) == len({r['map'] for r in caves}) == 15
        assert all(r['controller_entry_and_return'] for r in caves)
        assert sum(r['access']=='dive' for r in caves) == 5
        assert all(r['native_surf_and_dive_prompts'] and r['walked_tiles'] > 0
                   for r in caves if r['map'] != 'SeafoamIslands_1F_Frlg')
    else:
        raise AssertionError(('Unknown current generated-world proof', kind))


def required_keys(info):
    targets = {'test', *[row['file'] for row in info['variants']]}
    return ({('common', kind) for kind in COMMON_KINDS} |
            {(target, kind) for target in targets for kind in EDITION_KINDS} |
            {('test', 'generated-gym-native-walk')})


def verify_update(directory, info):
    directory = Path(directory)
    old = previous_release(info)
    reference = info['previous_port_validation']
    assert baseline('versions.json', (ROOT/reference['manifest']).read_bytes()) == old
    assert reference['manifest_sha256'] == BASELINE_SHA256['versions.json']
    assert reference['retested_on_current_rom'] is False
    assert info['integration_layers'] == old['integration_layers'] + [SCOPE]
    assert len(info['integration_layers']) == 165
    assert info['historical_validation'] == old['historical_validation']
    assert info['previous_validation'] == old['previous_validation']
    assert info['full_campaign_playthrough'] is False and info['previous_features_retested_on_current_rom'] is False
    references = {}
    for key, name in [('previous_review_validation','review.json'),('previous_review_save_validation','test.sav')]:
        ref = info[key]
        path = ROOT/ref['file']
        assert digest(path) == ref['sha256'] == BASELINE_SHA256[name]
        baseline(name, path.read_bytes())
        references[name] = path
    test = verify_review(ROOT/'roms/rom-de-teste', directory/'Pokemon-Journey-Gen1-9-Normal.gba')
    expected = {'common':info['parent_rom_sha256'], 'test':test['sha256'],
                **{row['file']:row['sha256'] for row in info['variants']}}
    covered = set()
    for proof in info['proofs']:
        key = proof['target'], proof['kind']
        assert key not in covered
        assert key in required_keys(info) or (key[0] == 'common' and key[1] in OPTIONAL_COMMON_KINDS)
        covered.add(key)
        relative = Path(proof['file'])
        assert not relative.is_absolute() and '..' not in relative.parts
        path = directory/relative
        report_dependencies(path, expected_sha=proof['sha256'])
        report = json.loads(path.read_bytes())
        assert report['rom_sha256'] == expected[proof['target']], ('Stale proof', key)
        verify_proof(report, path.parent, proof['kind'], proof['target']=='test',
                     ROOT/'roms/rom-de-teste/Pokemon-Journey-TESTE.sav', info, old)
    assert required_keys(info) <= covered
    previous_review = json.loads(references['review.json'].read_bytes())
    assert info['historical_release'] == dict(scope='badge-story',parent_rom_sha256=old['parent_rom_sha256'],
        variants={r['file']:r['sha256'] for r in old['variants']},test_rom_sha256=previous_review['sha256'],
        proof_count=26,retested_on_current_rom=False)
    from verify_badge_story_update import verify_update as verify_previous
    verify_previous(directory, old, historical_review=previous_review, historical_save=references['test.sav'])
    return info
