"""Bind the campaign milestones to their exact layer-164 ROMs and history.

The literal source scope and strict observation contracts were reviewed
against all 26 executed proofs from the frozen five-edition build.
"""
import hashlib
import io
import json
from pathlib import Path

from PIL import Image

from package_review_rom import verify as verify_review
from verify_coastal_closures_update import verify_cold_boot, verify_review_mode
from verify_dewford_coast_update import pinned_file
from verify_fuchsia_update import ROOT, previous_release
from verify_sevii_integrated_piers_update import current_report, require_true
from validate_badge_story_source import ALLOWED_SOURCE_FILES
from story_rival_contract import MAPS as RIVAL_MAPS, NATIVE_TRAINERS as RIVAL_TRAINERS


SCOPE = 'badge-story'
COMMON_KINDS = {'badge-story-source'}
EDITION_KINDS = {'qualifier-event', 'rival-identities', 'badge-gates',
                 'review-mode', 'cold-boot'}
# Finalized only after all 26 exact-ROM reports and 53 release rejection tests
# passed, including visible command-menu frames and actual party switching.
CONTRACT_FINALIZED = True
NATIVE_SCHEMAS_FINALIZED = True
PARENT_ROM_SHA256 = 'cd5187f43d33b80e5ba2130c9e4e31a4d5a9a0e2504d8b71517da7d13814d9c6'
BASELINE_SHA256 = {
    'versions.json': '23f5603eb385e8f34816c82f84fa22c8c632fa3dae9738c2a3cf7fe39b33bcd8',
    'review.json': '82b6129993a7e4769dad5be7b3e5a99fe77a5338f2e6d0ea4cb47edd022b92ed',
    'test.sav': '33b8e45a444a5d84684b907ef2c90fffc785f6c54514bb5b934172f7e557bf37',
}

# Independent public roles: local opposite sex, away opposite sex, away same sex.
# Sevii keeps Kanto's birth affinity. Do not import the game's selection table.
RIVAL_ROLES = {
    0: {1: (4, 2, 3), 2: (3, 1, 4), 3: (4, 2, 1), 4: (3, 1, 2)},
    1: {1: (2, 4, 3), 2: (1, 3, 4), 3: (2, 4, 1), 4: (1, 3, 2)},
    2: {1: (2, 4, 3), 2: (1, 3, 4), 3: (2, 4, 1), 4: (1, 3, 2)},
}


def verify_group_ledger(core, *, player_hero, start_region, scenario):
    """Recalculate group standings from six observed native match records."""
    expected_heroes = [0, *RIVAL_ROLES[start_region][player_hero], 5, 6]
    assert core['hero'] == expected_heroes, ('Qualifier roster', core['hero'], expected_heroes)
    groups = core['groups']
    assert len(groups) == 2 and all(len(group) == 3 for group in groups)
    assert sorted(value for group in groups for value in group) == list(range(6))
    assert groups[0][0] == 0, 'The human belongs to group A'
    assert sorted(core['tie_order']) == list(range(6)), 'Registration tiebreak must be a unique draw'
    ledger = core['ledger']
    assert len(ledger) == core['cursor'] == 6
    expected_pairs = {frozenset((group[a], group[b]))
                      for group in groups for a, b in [(0, 1), (0, 2), (1, 2)]}
    seen, wins, balance, survivors = set(), [0] * 6, [0] * 6, [0] * 6
    for row in ledger:
        a, b, left_a, left_b = (row[key] for key in ['a', 'b', 'left_a', 'left_b'])
        assert all(type(value) is int for value in [a, b, left_a, left_b])
        assert 0 <= a < 6 and 0 <= b < 6 and a != b
        pair = frozenset((a, b))
        assert pair in expected_pairs and pair not in seen, ('Repeated or cross-group match', row)
        assert row['resolved'] is True
        assert 0 <= left_a <= 6 and 0 <= left_b <= 6
        assert (left_a > 0) != (left_b > 0), ('Group match needs one winner', row)
        seen.add(pair)
        wins[a if left_a else b] += 1
        balance[a] += left_a - left_b
        balance[b] += left_b - left_a
        survivors[a] += left_a
        survivors[b] += left_b
    assert seen == expected_pairs
    assert core['wins'] == wins and core['balance'] == balance and core['survivors'] == survivors
    ranked = [sorted(group, key=lambda index: (
        wins[index], balance[index], survivors[index], core['tie_order'][index]), reverse=True)
        for group in groups]
    finalists = [ranked[0][0], ranked[1][0]]
    assert core['finalists'] == finalists, ('Wrong group winner advanced', core['finalists'], finalists)
    if scenario == 'championship':
        assert finalists[0] == 0 and core['stage'] == 2
        assert core['final_played'] is True and core['final_winner'] == 0
    elif scenario == 'final_defeat':
        assert finalists[0] == 0 and core['stage'] == 3
        assert core['final_played'] is True and core['final_winner'] == finalists[1]
    elif scenario == 'group_elimination':
        assert finalists[0] != 0 and core['stage'] == 3
        assert core['final_played'] is False and core['final_winner'] == 255
    else:
        raise AssertionError(('Unknown required tournament scenario', scenario))
    return ranked


def require_final_contract():
    assert CONTRACT_FINALIZED is True, 'Badge-story native contracts are not finalized'
    assert NATIVE_SCHEMAS_FINALIZED is True, 'Badge-story native schemas are not finalized'
    assert ALLOWED_SOURCE_FILES, 'The source scope needs an independent literal allowlist'


def verify_baseline_bytes(name, raw):
    assert hashlib.sha256(raw).hexdigest() == BASELINE_SHA256[name], ('Layer 163 baseline changed', name)
    if name == 'versions.json':
        old = json.loads(raw)
        assert old['validated'] is True and old['validation_scope'] == 'coastal-closures'
        assert old['parent_rom_sha256'] == PARENT_ROM_SHA256
        assert len(old['integration_layers']) == 163 and len(old['proofs']) == 31
        return old
    if name == 'test.sav':
        assert len(raw) == 131072


def verify_source(report, info, old):
    assert ALLOWED_SOURCE_FILES, 'The source scope needs an independent literal allowlist'
    assert report['kind'] == 'badge-story-source'
    assert report['layers'] == info['integration_layers']
    assert report['parent_rom_sha256'] == old['parent_rom_sha256']
    assert report['compiled_rom'] is True and report['preflight'] is False
    assert len(report['changed_files']) == len(set(report['changed_files'])) == len(ALLOWED_SOURCE_FILES)
    assert set(report['changed_files']) == set(report['allowed_changed_files']) == ALLOWED_SOURCE_FILES
    assert set(report['prepared_sha256']) == ALLOWED_SOURCE_FILES
    assert all(len(sha) == 64 and set(sha) <= set('0123456789abcdef')
               for sha in report['prepared_sha256'].values())
    assert report['source_hashes_checked'] == 32240
    require_true(report, ['independent_replay', 'idempotent',
                          'unrelated_source_files_unchanged', 'save_and_link_abi_unchanged',
                          'atlas_graphics_unchanged', 'coastlines_and_gym_geometry_unchanged',
                          'native_trainer_parties_unchanged'])
    assert report['full_campaign_playthrough'] is False
    assert report['compiled_abi'] == {
        'sizeof(struct SaveBlock1)': 19620, 'sizeof(struct SaveBlock2)': 3892,
        'sizeof(struct ObjectEvent)': 36, 'sizeof(struct LinkPlayer)': 28,
        'sizeof(struct LinkPlayerBlock)': 60, 'FLAGS_COUNT': 6976, 'VARS_COUNT': 396}
    field = report['field_event']
    assert field['original_outdoor_npcs_preserved'] == 25 and field['added_outdoor_actors'] == 5
    require_true(field, ['original_events_warps_and_connections_unchanged',
                         'native_pwt_implementation_unchanged', 'native_trainer_parties_unchanged'])
    avatars = report['avatars']
    assert avatars['reference_rivals'] == [dict(name=name, visible_height=height)
        for name, height in [('red', 19), ('leaf', 19), ('brendan', 21), ('may', 20)]]
    assert avatars['all_frames_whole_and_same_native_scale'] is True
    assert len(avatars['avatars']) == 4
    observed = set()
    for avatar in avatars['avatars']:
        name = avatar['path'].removeprefix('graphics/object_events/pics/people/journey_').removesuffix('.png')
        assert name in {'eren', 'luffy', 'pwt_eren', 'pwt_luffy'} and name not in observed
        observed.add(name)
        assert avatar['palette_unchanged'] is True
        assert avatar['frames'] == [dict(frame=index, bounds=[1, 11 if index < 3 else 12,
                                                            15, 31 if index < 3 else 32],
                                         visible_height=20) for index in range(9)]
        compiled = avatar['compiled']
        assert compiled['bytes'] == 2304 and 0x08000000 <= compiled['address'] < 0x0A000000 - 2304
        assert compiled['sha256'] == ('93e58771b7c5a0a9121081b0020291cb33717831f41802d431880eb80207b2e2'
                                      if name.endswith('eren') else
                                      'ae30bb48d7f463d66f49b2febd62bcf86049fa527a2f80466a624606a119ffcd')


def verify_qualifier_event(report, directory):
    assert report['full_campaign_playthrough'] is False
    assert report['native_mon_decoder_checked_against_GetMonData'] is True
    fixture = report['fixtures']
    assert [fixture[key] for key in ['player_hero', 'start_region', 'family_home', 'qualifying_badges']] == [1, 0, 17, 18]
    require_true(fixture, ['random_encounters_disabled', 'initial_map_placement', 'birth_identity',
                           'player_battle_stats_boosted', 'player_hp_status_for_berry_test',
                           'native_flash_negative_control_after_actual_victory',
                           'continuation_callback_is_fixture',
                           'actual_battle_outcomes_and_qualifier_flag_not_written'])
    cap, hard = report['max_national'], report['perfect_trainer_ivs']
    assert cap in [493, 1025] and type(hard) is bool
    attempts = report['attempts']
    assert [attempt['scenario'] for attempt in attempts] == ['group_elimination', 'final_defeat', 'championship']
    expected_outcomes = {'group_elimination': [2, 2], 'final_defeat': [1, 1, 2], 'championship': [1, 1, 1]}
    captures = {'qualifier-outdoor-six-participants', 'qualifier-normal-bag-ui',
                'qualifier-champion-save-continue', 'qualifier-interrupted-arena-recovery'}

    def identity(mon):
        return mon['personality'], mon['ot_id']

    def party(rows, originals=None):
        assert 1 <= len(rows) <= 6
        assert len({identity(row) for row in rows}) == len(rows)
        for row in rows:
            assert row['hp'] == row['max_hp'] and row['hp'] > 0 and row['status'] == 0
            assert row['pp'] == row['max_pp'] and len(row['pp']) == len(row['moves']) == 4
            assert row['level'] > 50 and row['experience'] >= 0
        if originals is not None:
            assert {identity(row) for row in rows} == originals.keys()
            for row in rows:
                original = originals[identity(row)]
                assert row['item'] == original['item'] and row['moves'] == original['moves']
                assert row['level'] >= original['level'] and row['experience'] >= original['experience']

    for attempt in attempts:
        scenario = attempt['scenario']
        won = scenario == 'championship'
        core = attempt['final_core']
        verify_group_ledger(core, player_hero=fixture['player_hero'],
                            start_region=fixture['start_region'], scenario=scenario)
        initial = attempt['initial_draw']
        assert all(initial[key] == core[key] for key in ['hero', 'groups', 'tie_order'])
        assert core['prepared'] is False and core['immediate_group_loss'] is False
        starting = attempt['initial_party']
        assert len(starting) == (1 if scenario == 'group_elimination' else 3)
        party(starting)
        originals = {identity(row): row for row in starting}
        battles = attempt['player_battles']
        assert [battle['outcome'] for battle in battles] == expected_outcomes[scenario]
        assert [battle['stage'] for battle in battles] == ([0, 0] if scenario == 'group_elimination' else [0, 0, 1])
        human_group = next(group for group in core['groups'] if 0 in group)
        assert {battle['hero'] for battle in battles[:2]} == {core['hero'][i] for i in human_group if i != 0}
        if len(battles) == 3:
            assert battles[2]['hero'] == core['hero'][core['finalists'][1]]
        for index, battle in enumerate(battles, 1):
            assert battle['trainer'] == 1800 + battle['hero']
            # BattleMainCB2 adds IS_MASTER to every native non-link trainer
            # battle; facility, PWT and level-normalization flags stay absent.
            assert battle['battle_flags'] == 12 and battle['actions'] > 0
            assert battle['command_menu_capture'] is True
            active = battle['active_party_indices']
            assert active and len(set(active)) == len(active)
            assert all(type(slot) is int and 0 <= slot < len(starting) for slot in active)
            party(battle['entry_party'], originals)
            enemy = battle['enemy_party']
            assert len(enemy) == 6 and all(0 < mon['national_dex'] <= cap for mon in enemy)
            assert all(sum(mon['evs']) == 510 and len(mon['evs']) == 6 for mon in enemy)
            if hard:
                assert all(mon['ivs'] == 0x3FFFFFFF for mon in enemy)
            else:
                assert any(mon['ivs'] != 0x3FFFFFFF for mon in enemy)
            captures.add(f'{scenario}-battle-{index}')
        assert battles[0]['berry_consumed_natively'] is won
        if won:
            assert len(battles[0]['active_party_indices']) > 1
        after = attempt['after']
        assert after['map'] == ('BattleFrontier_OutsideWest' if won else 'BattleFrontier_PokemonCenter_1F')
        assert after['state'] == (3 if won else 0) and after['won'] is won
        assert all(type(after[key]) is int and 0 <= after[key] < 2**32
                   for key in ['money_before', 'money_after'])
        if won:
            assert after['money_after'] >= after['money_before']
        assert after['battle_points'] == report['pwt_isolation']['battle_points']
        party(after['party'], originals)
        gain = sum(mon['experience'] - originals[identity(mon)]['experience'] for mon in after['party'])
        assert after['total_experience_gain'] == gain
        assert gain > 0 if any(outcome == 1 for outcome in expected_outcomes[scenario]) else gain >= 0
        assert after['x_attack_before'] == 5 and after['x_attack_after'] == (4 if won else 5)
        assert after['bag_ui_opened'] is after['bag_item_consumed_natively'] is won
        assert after['native_party_switch'] is won
        orders = after['post_battle_party_orders']
        assert len(orders) == len(battles)
        expected_personalities = sorted(row['personality'] for row in starting)
        assert all(sorted(order) == expected_personalities for order in orders)
        captures.add(scenario + '-finished')

    intro = attempts[0]['outdoor_intro']
    assert intro['map'] == 'BattleFrontier_OutsideWest'
    assert intro['player'] == [26, 67]
    assert intro['native_source_frames_compared_with_scanout'] is True
    assert len(intro['objects']) == 6
    objects = intro['objects']
    assert len({obj['object_index'] for obj in objects}) == len({obj['sprite_id'] for obj in objects}) == 6
    assert {obj['local_id'] for obj in objects if 26 <= obj['local_id'] <= 30} == set(range(26, 31))
    assert len({obj['native_obj_pixels']['hardware_oam_index'] for obj in objects}) == 6
    expected_actors = {255: ([26, 67], 243), 26: ([22, 66], 89), 27: ([24, 66], 251),
                       28: ([28, 66], 0), 29: ([21, 67], 391), 30: ([29, 67], 390)}
    assert {obj['local_id'] for obj in objects} == expected_actors.keys()
    rivals = [obj['native_obj_pixels']['opaque_bbox'][3] for obj in objects if obj['local_id'] not in (29, 30)]
    for obj in objects:
        assert (obj['position'], obj['graphics_id']) == expected_actors[obj['local_id']]
        pixels = obj['native_obj_pixels']
        assert pixels['frame'] == [16, 32] and pixels['exact_vram_obj_palette_and_current_frame'] is True
        assert min(rivals) - 2 <= pixels['opaque_bbox'][3] <= max(rivals) + 2
        assert pixels['opaque_pixels'] >= 100
        assert pixels['matching_scanout_pixels'] >= pixels['opaque_pixels'] * 0.8
        x, y, width, height = pixels['screen_rectangle']
        assert 0 <= x <= 240 - width and 0 <= y <= 160 - height
    for local in [29, 30]:
        assert next(obj for obj in objects if obj['local_id'] == local)['native_obj_pixels']['opaque_bbox'][3] == 20
    greetings = report['celebrations']
    assert len(greetings) == 5 and {row['slot'] for row in greetings} == set(range(5))
    phrases = {'LEAF': 'You kept reading our next move.', 'BRENDAN': 'Every journey made us stronger.',
               'MAY': 'You trusted every POKeMON.', 'Luffy': 'You never gave up on your crew!',
               'Eren': 'You chose your path and held on.'}
    assert {row['speaker'] for row in greetings} == set(phrases)
    for row in greetings:
        assert row['map'] == 'BattleFrontier_OutsideWest'
        assert row['text'].startswith(row['speaker'] + ':') and phrases[row['speaker']] in row['text']
        assert row['printer_accelerated_with_held_b'] is True
        assert 0x08000000 <= row['native_script_pointer'] < 0x0A000000
        captures.add('qualifier-congratulations-' + str(row['slot']))
    saved = report['saved_win']
    require_true(saved, ['native_flash_roundtrip', 'qualifier_won', 'celebrated',
                         'temporary_clear_is_negative_control', 'continuation_callback_is_fixture'])
    assert saved['state'] == 3
    recovery = report['interrupted_arena']
    assert recovery['inactive_volatile_controller_and_arena_state_are_fixtures'] is True
    assert recovery['recovered_map'] == 'BattleFrontier_PokemonCenter_1F'
    assert recovery['state'] == 0 and recovery['qualifier_won'] is False
    isolation = report['pwt_isolation']
    assert isolation['state_bytes'] > 0 and len(isolation['state_sha256']) == 64
    assert isolation['state_sha256'] == isolation['initial_state_sha256']
    assert isolation['battle_points'] == isolation['initial_battle_points']
    verify_captures(report, directory, captures)


def verify_rival_identities(report, directory):
    assert report['full_campaign_playthrough'] is False and report['api_maps_are_unloaded_fixtures'] is True
    require_true(report['fixtures'], ['avatar_and_birthplace', 'unloaded_api_map_contexts',
        'initial_party_and_progress', 'initial_map_placement', 'encounters_disabled',
        'player_battle_stats_boosted', 'enemy_stats_and_outcomes_not_written',
        'event_progression_not_written_after_trigger'])
    contexts = {(hero, region) for hero in range(1, 5) for region in range(3)}
    names = {1: 'RED', 2: 'LEAF', 3: 'BRENDAN', 4: 'MAY'}
    portraits = {1: 3, 2: 4, 3: 1, 4: 2}
    graphics = {1: 243, 2: 251, 3: 0, 4: 89}

    def expected(hero, region, kanto, away_slot):
        return RIVAL_ROLES[region][hero][0 if kanto == (region != 0) else away_slot]

    def context_rows(rows, expected_keys, key):
        observed = set()
        assert len(rows) == len(expected_keys)
        for row in rows:
            value = key(row)
            assert value in expected_keys and value not in observed
            observed.add(value)
        assert observed == expected_keys

    rows = report['identity_contexts']
    context_rows(rows, contexts, lambda row: (row['player_hero'], row['start_region']))
    for row in rows:
        assert row['roles'] == list(RIVAL_ROLES[row['start_region']][row['player_hero']])
    trainers = {name: (kanto, slot) for name, kanto, slot in RIVAL_TRAINERS}
    rows = report['trainer_observations']
    context_rows(rows, {(hero, region, name) for hero, region in contexts for name in trainers},
                 lambda row: (row['player_hero'], row['start_region'], row['trainer']))
    trainer_ids = {}
    # Stable IDs read independently from the pinned native parent, in the
    # curated chronology order above. A self-consistent relabel is insufficient.
    expected_trainer_ids = dict(zip([name for name, _, _ in RIVAL_TRAINERS], [
        1080, 1081, 1082, 1083, 1084, 1085, 1086, 1087, 1088,
        1180, 1181, 1182, 1183, 1184, 1185, 1186, 1187, 1188,
        1189, 1190, 1191, 1192, 1193, 1194, 1474, 1475, 1476,
        523, 526, 520, 532, 535, 529, 592, 599, 593, 768, 769, 600,
        524, 527, 521, 533, 536, 530, 525, 528, 522, 534, 537, 531,
        662, 663, 661, 665, 666, 664]))
    for row in rows:
        rival = expected(row['player_hero'], row['start_region'], *trainers[row['trainer']])
        assert row['expected_hero'] == row['observed_hero'] == rival
        assert row['name'] == names[rival] and row['trainer_pic'] == row['compatibility_pic'] == portraits[rival]
        assert row['trainer_id'] == expected_trainer_ids[row['trainer']]
        assert trainer_ids.setdefault(row['trainer'], row['trainer_id']) == row['trainer_id']
    assert len(trainer_ids) == len(set(trainer_ids.values())) == 57
    maps = {name: (kanto, slot) for name, _, kanto, slot in RIVAL_MAPS}
    rows = report['map_observations']
    context_rows(rows, {(hero, region, name) for hero, region in contexts for name in maps},
                 lambda row: (row['player_hero'], row['start_region'], row['map']))
    native_info = {}
    for row in rows:
        rival = expected(row['player_hero'], row['start_region'], *maps[row['map']])
        assert row['expected_hero'] == row['observed_hero'] == rival
        assert row['placeholder'] == names[rival] and row['graphics'] == graphics[rival]
        assert 0x08000000 <= row['native_graphics_info'] < 0x0A000000
        assert native_info.setdefault(rival, row['native_graphics_info']) == row['native_graphics_info']
    assert len(native_info) == len(set(native_info.values())) == 4
    rows = report['route22_late_observations']
    context_rows(rows, contexts, lambda row: (row['player_hero'], row['start_region']))
    for row in rows:
        rival = expected(row['player_hero'], row['start_region'], True, 1)
        assert row['expected_hero'] == row['observed_hero'] == rival
    controls = {'TRAINER_WALLY_VR_1', 'TRAINER_JOURNEY_BLUE'}
    rows = report['negative_controls']
    context_rows(rows, {(hero, region, name) for hero, region in contexts for name in controls},
                 lambda row: (row['player_hero'], row['start_region'], row['trainer']))
    native_controls = {}
    for row in rows:
        assert row['observed_hero'] == 0 and row['name'] == row['raw_name'] and row['trainer_pic'] == row['raw_pic']
        native = row['trainer_id'], row['raw_name'], row['raw_pic']
        assert native == ((519, 'WALLY', 7) if row['trainer'] == 'TRAINER_WALLY_VR_1' else (1550, 'BLUE', 149))
        assert native_controls.setdefault(row['trainer'], native) == native
    assert len(report['fixed_graphics_controls']) == 6
    assert set(report['fixed_graphics_controls']) == {
        'OBJ_EVENT_GFX_RED_NORMAL', 'OBJ_EVENT_GFX_GREEN_NORMAL', 'OBJ_EVENT_GFX_BRENDAN_NORMAL',
        'OBJ_EVENT_GFX_MAY_NORMAL', 'OBJ_EVENT_GFX_WALLY', 'OBJ_EVENT_GFX_JOURNEY_GYM_BLUE'}
    actual = {
        'red-hoenn-kanto-brendan': (1, 0, 'Route22_Frlg', 3, 'TRAINER_RIVAL_ROUTE22_EARLY_'),
        'red-hoenn-kanto-leaf': (1, 0, 'CeruleanCity_Frlg', 2, 'TRAINER_RIVAL_CERULEAN_'),
        'red-hoenn-home-may': (1, 0, 'Route103', 4, 'TRAINER_MAY_ROUTE_103_'),
        'leaf-kanto-home-red': (2, 1, 'Route22_Frlg', 1, 'TRAINER_RIVAL_ROUTE22_EARLY_')}
    rows = report['actual_encounters']
    context_rows(rows, set(actual), lambda row: row['label'])
    captures = set()
    images = set()
    for row in rows:
        hero, region, mapping, rival, prefix = actual[row['label']]
        assert (row['player_hero'], row['start_region'], row['map'], row['expected_hero']) == (hero, region, mapping, rival)
        assert row['observed_name'] == names[rival]
        assert names[rival] + ':' in row['field_dialogue'] and names[rival] in row['battle_name']
        assert row['opponent_id'] in {value for name, value in trainer_ids.items() if name.startswith(prefix)}
        assert row['portrait']['trainer_pic'] == portraits[rival]
        assert row['actual_attacks'] > 0 and row['battle_outcome'] == 1
        assert row['controller_triggered'] is row['native_scene_completed'] is True
        actor = row['field_actor']
        assert actor['local_id'] == (2 if mapping == 'Route103' else 8 if mapping == 'CeruleanCity_Frlg' else 1)
        assert 0 <= actor['sprite_id'] < 64 and 0 <= row['portrait']['sprite_id'] < 64
        assert 0x08000000 <= actor['images'] < 0x0A000000
        images.add(actor['images'])
        captures |= {row['label'] + '-field-dialogue', row['label'] + '-battle-portrait'}
    assert len(images) == 4
    verify_captures(report, directory, captures)


def verify_captures(report, directory, required):
    """Require the observed steps' own hashed PNGs, not a report-only claim."""
    seen = set()
    for row in report['captures']:
        path = Path(row['file'])
        assert not path.is_absolute() and '..' not in path.parts
        assert path.suffix == '.png' and row['file'] not in seen
        seen.add(row['file'])
        raw = (Path(directory) / path).read_bytes()
        assert raw.startswith(b'\x89PNG\r\n\x1a\n'), path
        assert hashlib.sha256(raw).hexdigest() == row['sha256'], path
        with Image.open(io.BytesIO(raw)) as capture:
            assert capture.format == 'PNG' and capture.size == (240, 160), path
            pixels = capture.convert('RGB').getcolors(240 * 160)
        assert max(count for count, _ in pixels) < 0.95 * 240 * 160, ('Uniform native capture', path)
        assert sum(count for count, color in pixels if max(color) < 8) < 0.95 * 240 * 160, ('Black native capture', path)
    assert {name + '.png' for name in required} <= seen, ('Missing native captures', required, seen)


def verify_badge_gates(report, directory):
    require_true(report, [
        'source_gate_contract_checked', 'physical_gate_event_locations_and_warps_unchanged',
        'galactic_crossover_and_capture_requirements_preserved',
        'native_qualification_save_roundtrip', 'qualifier_victory_flag_is_initial_fixture',
        'initial_badges_quests_party_surf_and_travel_are_fixtures',
        'no_qualification_victory_or_galactic_battle_claimed',
        'controller_input_drives_all_crossings_and_interactions',
        'high_coordinate_initial_travel_uses_restored_private_emulator_warp_fixture',
        'prior_missions_and_crossover_are_not_league_prerequisites'])
    assert report['full_campaign_playthrough'] is False
    assert report['baseline_rom_sha256'] == PARENT_ROM_SHA256
    distributions = {(0, 0, 0), (8, 8, 0), (8, 8, 1), (8, 8, 2), (7, 3, 8),
                     (3, 8, 7), (8, 5, 8), (8, 6, 8), (6, 8, 8), (8, 8, 8)}
    expected = {(*bank, won, state) for bank in distributions
                for won in [False, True] for state in [0, 7]}
    seen = set()
    assert len(report['permission_cases']) == 40
    for row in report['permission_cases']:
        bank = tuple(row[key] for key in ['kanto', 'hoenn', 'extras'])
        key = (*bank, row['qualifier_won'], row['galactic_state'])
        assert type(row['qualifier_won']) is bool and key in expected and key not in seen
        seen.add(key)
        total = sum(bank)
        assert row['total'] == total
        assert row['league_permissions'] == [int(total >= 18 and row['qualifier_won'])] * 3
        assert row['galactic_available'] == int(total >= 22)
    assert seen == expected
    expected = {(f'GALACTIC_GRUNT_{i}', total, state)
                for i in range(18) for total in [21, 22] for state in [0, 7]}
    seen = set()
    assert len(report['grunt_visibility_cases']) == 72
    for row in report['grunt_visibility_cases']:
        key = row['key'], row['total'], row['galactic_state']
        assert key in expected and key not in seen
        seen.add(key)
        assert row['visible'] is (row['total'] >= 22 and row['galactic_state'] < 7)
    assert seen == expected
    loaded = report['loaded_grunt_visibility']
    assert len(loaded) == 2 and {row['total'] for row in loaded} == {21, 22}
    for row in loaded:
        assert row['map'] == 'AbandonedShip_CaptainsOffice' and row['local_id'] > 0
        assert row['object_loaded'] is (row['total'] == 22)

    checkpoints = [(7, 2, False), (13, 149, False), (7, 140, False),
                   (12, 123, False), (14, 112, True), (9, 94, True),
                   (12, 61, False), (5, 35, False)]
    assert len(report['physical_checkpoints']) == 8
    for index, (row, (x, y, surfing)) in enumerate(zip(report['physical_checkpoints'], checkpoints)):
        assert row['checkpoint'] == index + 1
        assert row['map'] == ('Route23_Frlg' if index else 'Route22_NorthEntrance_Frlg')
        assert row['trigger'] == [x, y] and row['fixture_start'] == [x, y + 1]
        assert row['initial_surf_fixture'] is surfing
        assert row['recognition_state'] == 8 and row['controller_crossing'] is True
        assert row['after_map'] == [37, 42]
        if index:
            assert row['after_position'] == [x, y - 1]
    blocked = report['physical_checkpoint_denials']
    assert len(blocked) == 2
    assert {(row['total'], row['qualifier_won']) for row in blocked} == {(17, True), (18, False)}
    for row in blocked:
        assert row['pushed_back'] is True and row['recognition_state'] == 7
        assert row['after_position'][0] == 5 and row['after_position'][1] >= 36

    expected = {(region, total, won, entered)
                for region in ['Kanto', 'Hoenn']
                for total, won, entered in [(17, True, False), (18, False, False),
                                             (18, False, True), (18, True, False)]}
    seen = set()
    assert len(report['physical_leagues']) == 8
    for row in report['physical_leagues']:
        key = row['region'], row['total'], row['qualifier_won'], row['prior_elite_entry']
        assert key in expected and key not in seen
        seen.add(key)
        assert all(type(row[name]) is bool for name in ['qualifier_won', 'prior_elite_entry'])
        region, total, won, _ = key
        assert row['fixture_start_map'] == ('IndigoPlateau_PokemonCenter_1F_Frlg'
                                          if region == 'Kanto' else 'EverGrandeCity_PokemonLeague_1F')
        assert [row['kanto_badges'], row['hoenn_badges'], row['extras']] == ([8, 8, 1] if total == 17 else [6, 4, 8])
        assert row['galactic_state'] == row['crossover_visits'] == 0
        allowed = total >= 18 and won
        assert row['allowed'] is allowed and row['physical_controller_entry'] is allowed
        assert row['physical_controller_denial'] is (not allowed)
        assert row['after_map'] == (([35, 75] if region == 'Kanto' else [16, 9]) if allowed
                                   else ([47, 0] if region == 'Kanto' else [16, 10]))
        if not allowed:
            assert row['after_position'][1] >= 3
    assert seen == expected
    chapter = report['physical_galactic_entry']
    assert len(chapter) == 3
    assert {(row['total'], row['crossover_visits']) for row in chapter} == {(21, 4095), (22, 0), (22, 4095)}
    for row in chapter:
        assert [row['kanto'], row['hoenn'], row['extras']] == ([8, 5, 8] if row['total'] == 21 else [8, 6, 8])
        assert row['bulkhead_previously_defeated_fixture'] is row['physical_interaction'] is True
        admitted = row['total'] == 22 and row['crossover_visits'] == 4095
        assert row['admitted'] is admitted
        assert row['after_map'] == ([83, 21] if admitted else [24, 66])
    captures = {f'badge-gates-galactic-{n}-badges' for n in [21, 22]}
    captures |= {f'badge-gates-checkpoint-{i}' for i in range(1, 9)}
    captures |= {f'badge-gates-checkpoint-denied-{n}' for n in [17, 18]}
    captures |= {f'badge-gates-{region}-{suffix}' for region in ['kanto', 'hoenn']
                 for suffix in ['admitted', 'denied-17-0', 'denied-18-0', 'denied-18-1']}
    captures |= {f'badge-gates-galactic-entry-{n}-{visits}' for n, visits in [(21, 4095), (22, 0), (22, 4095)]}
    captures |= {'badge-gates-galactic-22-entry-prompt', 'badge-gates-native-save-qualification'}
    verify_captures(report, directory, captures)


NATIVE_VERIFIERS = {'qualifier-event': verify_qualifier_event,
                    'rival-identities': verify_rival_identities,
                    'badge-gates': verify_badge_gates}


def verify_proof(report, directory, kind, is_test, save, info, old):
    if kind in EDITION_KINDS and kind != 'cold-boot':
        assert report['review_mode'] is is_test
    if kind == 'badge-story-source':
        verify_source(report, info, old)
    elif kind in NATIVE_VERIFIERS:
        require_true(report, ['compiled_rom', 'native_validation_performed'])
        assert report['preflight'] is False
        if kind in {'qualifier-event', 'rival-identities'}:
            if is_test:
                expected_rules = 1025, False
            else:
                edition = next(row for row in info['variants'] if row['sha256'] == report['rom_sha256'])
                expected_rules = edition['max_national'], edition['perfect_trainer_ivs']
            assert (report['max_national'], report['perfect_trainer_ivs']) == expected_rules
        NATIVE_VERIFIERS[kind](report, directory)
    elif kind == 'review-mode':
        verify_review_mode(report, is_test, save)
    elif kind == 'cold-boot':
        verify_cold_boot(report, is_test, save)
    else:
        raise AssertionError(('Unsupported current proof', kind))


def verify_update(directory, info, *, historical_review=None, historical_save=None):
    require_final_contract()
    directory = Path(directory)
    old = previous_release(info)
    reference = info['previous_port_validation']
    assert reference['manifest_sha256'] == BASELINE_SHA256['versions.json']
    assert reference['retested_on_current_rom'] is False
    assert verify_baseline_bytes('versions.json', (ROOT / reference['manifest']).read_bytes()) == old
    assert info['integration_layers'] == old['integration_layers'] + [SCOPE]
    assert len(info['integration_layers']) == 164
    assert info['historical_validation'] == old['historical_validation']
    assert info['previous_validation'] == old['previous_validation']
    assert info['full_campaign_playthrough'] is False
    assert info['previous_features_retested_on_current_rom'] is False
    _, previous_review_raw = pinned_file(info['previous_review_validation'])
    previous_save, previous_save_raw = pinned_file(info['previous_review_save_validation'])
    verify_baseline_bytes('review.json', previous_review_raw)
    verify_baseline_bytes('test.sav', previous_save_raw)
    previous_review = json.loads(previous_review_raw)
    assert info['historical_release'] == dict(
        scope=old['validation_scope'], parent_rom_sha256=old['parent_rom_sha256'],
        variants={row['file']: row['sha256'] for row in old['variants']},
        test_rom_sha256=previous_review['sha256'], proof_count=31,
        retested_on_current_rom=False)
    if historical_review is None:
        assert historical_save is None
        test = verify_review(ROOT / 'roms/rom-de-teste', directory / 'Pokemon-Journey-Gen1-9-Normal.gba')
    else:
        test = historical_review
        assert historical_save is not None, 'Historical TESTE evidence requires its pinned save'
        normal = next(row for row in info['variants'] if row['file'] == test['base_normal_file'])
        assert test['base_normal_sha256'] == normal['sha256'] and test['bytes'] == 33554432
        assert test['file'] == 'Pokemon-Journey-TESTE.gba' and test['separate_save_identity'] is True
        assert test['random_wild_encounters'] is False and test['automatic_trainer_approaches'] is False
    expected = {'common': info['parent_rom_sha256'], 'test': test['sha256'],
                **{row['file']: row['sha256'] for row in info['variants']}}
    required = {('common', kind) for kind in COMMON_KINDS}
    required |= {(target, kind) for target in expected if target != 'common'
                 for kind in EDITION_KINDS}
    assert len(required) == len(info['proofs']) == 26
    covered = set()
    source_elf, observed_elf = None, set()
    save = (ROOT / 'roms/rom-de-teste/Pokemon-Journey-TESTE.sav'
            if historical_review is None else Path(historical_save))
    from publish_coastal_closures import report_dependencies
    for proof in info['proofs']:
        key = proof['target'], proof['kind']
        assert key in required and key not in covered, key
        covered.add(key)
        path = Path(proof['file'])
        assert not path.is_absolute() and '..' not in path.parts
        file = directory / path
        report_dependencies(file, expected_sha=proof['sha256'])
        report = current_report(file.read_bytes(), expected[proof['target']], key)
        verify_proof(report, file.parent, proof['kind'], proof['target'] == 'test', save, info, old)
        if proof['kind'] == 'badge-story-source':
            source_elf = report['elf_sha256']
        elif proof['kind'] in {'qualifier-event', 'rival-identities'}:
            observed_elf.add(report['elf_sha256'])
    assert covered == required
    assert observed_elf == {source_elf}, 'Native reports used an ELF outside the audited source build'
    if historical_review is None:
        assert all((directory / row['file']).read_bytes()[test['review_mode_offset']] == 0
                   for row in info['variants'])
    from verify_coastal_closures_update import verify_update as verify_previous
    verify_previous(directory, old, historical_review=previous_review, historical_save=previous_save)
