"""Guard the new campaign seal and immutable layer-163 release history."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

import verify_coastal_closures_update as historical
from publish_badge_story import (
    HISTORICAL_COMMIT, archive_plan, historical_media, publish, releases,
)
from verify_badge_story_update import (
    BASELINE_SHA256, ROOT, require_final_contract, verify_baseline_bytes,
    verify_badge_gates, verify_captures, verify_group_ledger, verify_proof,
    verify_qualifier_event, verify_rival_identities, verify_source,
)


BASELINE = ROOT / 'mods/hoenn/badge-story-validation/baseline'
VERSIONS = ROOT / 'mods/hoenn/versions'


class BadgeStoryRelease(unittest.TestCase):
    def old(self):
        return json.loads((BASELINE / 'versions.json').read_bytes())

    def review(self):
        return json.loads((BASELINE / 'review.json').read_bytes())

    def test_unfinished_contract_cannot_publish_or_touch_downloads(self):
        with patch('verify_badge_story_update.CONTRACT_FINALIZED', False):
            with tempfile.TemporaryDirectory(prefix='badge-story-closed-', dir='/tmp') as temporary:
                output = Path(temporary) / 'downloads'
                with patch('publish_badge_story.package') as package:
                    with self.assertRaisesRegex(AssertionError, 'not finalized'):
                        publish(Path(temporary) / 'source', BASELINE.parent, output)
                    package.assert_not_called()
                self.assertFalse(output.exists())

    def test_source_allowlist_and_native_schema_are_required_independently(self):
        with patch('verify_badge_story_update.CONTRACT_FINALIZED', True):
            with patch('verify_badge_story_update.NATIVE_SCHEMAS_FINALIZED', False):
                with self.assertRaisesRegex(AssertionError, 'schemas are not finalized'):
                    require_final_contract()
            with patch('verify_badge_story_update.NATIVE_SCHEMAS_FINALIZED', True), \
                    patch('verify_badge_story_update.ALLOWED_SOURCE_FILES', frozenset()):
                with self.assertRaisesRegex(AssertionError, 'literal allowlist'):
                    require_final_contract()

    def test_baseline_bytes_have_independent_pinned_identities(self):
        for name, expected in BASELINE_SHA256.items():
            with self.subTest(name=name):
                raw = (BASELINE / name).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), expected)
                verify_baseline_bytes(name, raw)
                with self.assertRaisesRegex(AssertionError, 'baseline changed'):
                    verify_baseline_bytes(name, raw + b'\n')

    def test_changed_parent_rejects_publication_before_packaging(self):
        with tempfile.TemporaryDirectory(prefix='badge-story-parent-', dir='/tmp') as temporary:
            root = Path(temporary)
            baseline = root / 'validation/baseline'
            baseline.mkdir(parents=True)
            info = self.old()
            info['parent_rom_sha256'] = '0' * 64
            (baseline / 'versions.json').write_text(json.dumps(info))
            with patch('verify_badge_story_update.CONTRACT_FINALIZED', True), \
                    patch('verify_badge_story_update.NATIVE_SCHEMAS_FINALIZED', True), \
                    patch('verify_badge_story_update.ALLOWED_SOURCE_FILES', frozenset({'fixture.c'})), \
                    patch('publish_badge_story.package') as package:
                with self.assertRaisesRegex(AssertionError, 'baseline changed'):
                    publish(root / 'source', baseline.parent, root / 'downloads')
                package.assert_not_called()
            self.assertFalse((root / 'downloads').exists())

    def test_all284_historical_main_reports_keep_their_original_hashes(self):
        old = self.old()
        self.assertEqual((old['validation_scope'], len(old['integration_layers']), len(old['proofs'])),
                         ('coastal-closures', 163, 31))
        reports = [proof for release in releases(old) for proof in release['proofs']]
        self.assertEqual(len(reports), 284)
        for proof in reports:
            self.assertEqual(hashlib.sha256((VERSIONS / proof['file']).read_bytes()).hexdigest(),
                             proof['sha256'], proof['file'])

    def test_layer163_historical_verification_ignores_current_rom_and_review(self):
        with patch.object(historical, 'verify_review',
                          side_effect=AssertionError('Historical validation read the current TESTE')):
            historical.verify_update(VERSIONS, self.old(), historical_review=self.review(),
                                     historical_save=BASELINE / 'test.sav')

    def test_layer163_history_rejects_relabelled_test_rom_identity(self):
        review = self.review()
        review['base_normal_sha256'] = '0' * 64
        with self.assertRaises(AssertionError):
            historical.verify_update(VERSIONS, self.old(), historical_review=review,
                                     historical_save=BASELINE / 'test.sav')

    def test_layer163_history_requires_the_battery_save_used_by_its_boot_proof(self):
        with tempfile.TemporaryDirectory(prefix='badge-story-save-', dir='/tmp') as temporary:
            save = Path(temporary) / 'unrelated.sav'
            save.write_bytes(bytes(131072))
            with self.assertRaises(AssertionError):
                historical.verify_update(VERSIONS, self.old(), historical_review=self.review(),
                                         historical_save=save)

    def test_preflight_is_never_a_current_native_proof(self):
        for kind in ['qualifier-event', 'rival-identities', 'badge-gates']:
            with self.subTest(kind=kind):
                report = dict(review_mode=False, compiled_rom=True,
                              native_validation_performed=True, preflight=True)
                with self.assertRaises(AssertionError):
                    verify_proof(report, Path('/tmp'), kind, False, BASELINE / 'test.sav', {}, {})

    def test_archive_keeps_all_historical_reports_but_explicitly_registers_old_media(self):
        entries, media = archive_plan(self.old(), VERSIONS, include_roms=False)
        reports = {name for name in entries if name.startswith('evidence/') and name.endswith('.json')}
        self.assertEqual(len(reports), 299)  # 284 main reports and 15 layer-163 components.
        self.assertEqual(len(media), 2645)
        self.assertFalse(set(entries) & set(media))
        self.assertTrue(all(Path(name).suffix in {'.png', '.mp4', '.gif'} for name in media))
        self.assertTrue(all(row['required_by_historical_scopes'] for row in media.values()))
        catalog = {path.relative_to(ROOT).as_posix()
                   for path in (ROOT / 'assets/tiles').rglob('*') if path.is_file()}
        self.assertGreaterEqual(len(catalog), 608)
        self.assertTrue(catalog <= entries.keys())
        self.assertIn('docs/AJUSTES-GBA.txt', entries)

    def test_historical_registry_uses_real_immutable_repository_paths(self):
        _, media = archive_plan(self.old(), VERSIONS, include_roms=False)
        names = [next(name for name in media if name.startswith('evidence/coastal-closures/')),
                 'docs/videos/dewford-coast-corrected.mp4']
        registry = historical_media({name: media[name] for name in names})
        for row in registry:
            self.assertEqual(row['sha256'], media[row['file']]['sha256'])
            self.assertIn('/blob/' + HISTORICAL_COMMIT + '/' + row['repository_file'], row['url'])
        current = next(row for row in registry if row['file'].startswith('evidence/'))
        self.assertEqual(current['repository_file'], 'mods/hoenn/versions/' + current['file'])

    def test_historical_media_cannot_relabel_changed_pixels_as_an_old_capture(self):
        _, media = archive_plan(self.old(), VERSIONS, include_roms=False)
        name = next(name for name in media if name.startswith('evidence/coastal-closures/'))
        changed = copy.deepcopy(media[name])
        changed['sha256'] = '0' * 64
        with self.assertRaises(AssertionError):
            historical_media({name: changed})

    def test_historical_media_registry_rejects_paths_outside_repository(self):
        row = dict(file='native.png', repository_file='../native.png', sha256='0' * 64,
                   required_by_historical_scopes=['coastal-closures'])
        with patch('publish_badge_story.subprocess.check_output') as git:
            with self.assertRaises(AssertionError):
                historical_media({'native.png': row})
            git.assert_not_called()

    def test_archive_includes_current_capture_bytes_instead_of_historical_links(self):
        with tempfile.TemporaryDirectory(prefix='badge-story-current-', dir='/tmp') as temporary:
            root = Path(temporary)
            directory = root / 'evidence/badge-story/test/qualifier-event'
            directory.mkdir(parents=True)
            image = directory / 'actual-native.png'
            image.write_bytes(b'current native pixels')
            report = directory / 'qualifier-event.json'
            report.write_text(json.dumps(dict(captures=[dict(file=image.name,
                sha256=hashlib.sha256(image.read_bytes()).hexdigest())])))
            info = dict(validation_scope='badge-story', proofs=[dict(
                file=report.relative_to(root).as_posix(), sha256=hashlib.sha256(report.read_bytes()).hexdigest())])
            for name in ['versions.json', 'SHA256SUMS', 'START-HERE.md']:
                (root / name).write_text('{}\n')
            entries, media = archive_plan(info, root, include_roms=False)
            name = image.relative_to(root).as_posix()
            self.assertEqual(entries[name].read_bytes(), image.read_bytes())
            self.assertNotIn(name, media)
            image.write_bytes(b'corrupted current pixels')
            with self.assertRaisesRegex(AssertionError, 'attachment hash mismatch'):
                archive_plan(info, root, include_roms=False)


class QualifierLedgerContracts(unittest.TestCase):
    def ledger(self, scenario='championship', cyclic=False):
        # A report-shaped fixture exercises rejection; this is not native proof.
        pairs = [(0, 1), (3, 4), (1, 2), (3, 5), (0, 2), (4, 5)]
        wins, balance, survivors, rows = [0] * 6, [0] * 6, [0] * 6, []
        for a, b in pairs:
            winner = b if scenario == 'group_elimination' and a == 0 else a
            if cyclic and (a, b) == (0, 2): winner = b
            left_a, left_b = (1, 0) if winner == a else (0, 1)
            wins[winner] += 1
            balance[a] += left_a - left_b; balance[b] += left_b - left_a
            survivors[a] += left_a; survivors[b] += left_b
            rows.append(dict(a=a, b=b, left_a=left_a, left_b=left_b, resolved=True))
        tie = [5, 0, 1, 2, 3, 4]
        ranked = [sorted(group, key=lambda i: (wins[i], balance[i], survivors[i], tie[i]), reverse=True)
                  for group in [[0, 1, 2], [3, 4, 5]]]
        return dict(hero=[0, 4, 2, 3, 5, 6], groups=[[0, 1, 2], [3, 4, 5]],
                    wins=wins, balance=balance, survivors=survivors, tie_order=tie,
                    ledger=rows, cursor=6, finalists=[ranked[0][0], ranked[1][0]],
                    stage=2 if scenario == 'championship' else 3,
                    final_played=scenario != 'group_elimination',
                    final_winner=0 if scenario == 'championship' else 255 if scenario == 'group_elimination' else ranked[1][0])

    def verify(self, core, scenario='championship'):
        return verify_group_ledger(core, player_hero=1, start_region=0, scenario=scenario)

    def test_two_groups_have_one_winner_each_and_native_final_is_required(self):
        for scenario in ['championship', 'final_defeat', 'group_elimination']:
            with self.subTest(scenario=scenario):
                self.verify(self.ledger(scenario), scenario)
        forged = self.ledger()
        forged['final_played'] = False
        with self.assertRaises(AssertionError): self.verify(forged)

    def test_duplicate_or_cross_group_match_cannot_manufacture_a_win(self):
        for field, value in [('a', 3), ('b', 1)]:
            with self.subTest(field=field):
                forged = self.ledger()
                forged['ledger'][4][field] = value
                with self.assertRaises(AssertionError): self.verify(forged)

    def test_ledger_requires_every_group_pair_once(self):
        forged = self.ledger()
        forged['ledger'] = forged['ledger'][:-1]
        forged['cursor'] = 5
        with self.assertRaises(AssertionError): self.verify(forged)

    def test_standings_are_recomputed_instead_of_trusting_the_report(self):
        for field in ['wins', 'balance', 'survivors']:
            with self.subTest(field=field):
                forged = self.ledger()
                forged[field][0] += 1
                with self.assertRaises(AssertionError): self.verify(forged)

    def test_group_loser_cannot_advance_or_gain_a_championship_flag(self):
        forged = self.ledger('group_elimination')
        forged.update(stage=2, final_played=True, final_winner=0)
        forged['finalists'][0] = 0
        with self.assertRaises(AssertionError): self.verify(forged)

    def test_all_one_win_cycle_uses_declared_tiebreaks(self):
        core = self.ledger(cyclic=True)
        self.assertEqual(core['wins'][:3], [1, 1, 1])
        self.verify(core)
        core['finalists'][0] = 1
        with self.assertRaises(AssertionError): self.verify(core)

    def test_self_copy_or_wrong_start_region_roster_is_rejected(self):
        forged = self.ledger()
        forged['hero'][1] = 1
        with self.assertRaises(AssertionError): self.verify(forged)
        forged = self.ledger()
        with self.assertRaises(AssertionError):
            verify_group_ledger(forged, player_hero=1, start_region=1, scenario='championship')

    def test_unresolved_or_two_winner_matches_and_duplicate_draw_are_rejected(self):
        for field, value in [('resolved', False), ('left_b', 1)]:
            forged = self.ledger()
            forged['ledger'][0][field] = value
            with self.assertRaises(AssertionError): self.verify(forged)
        forged = self.ledger()
        forged['tie_order'][0] = forged['tie_order'][1]
        with self.assertRaises(AssertionError): self.verify(forged)


class CompiledBadgeStorySourceContracts(unittest.TestCase):
    def source(self):
        return json.loads((BASELINE.parent / 'source.json').read_text())

    def verify(self, report):
        old = json.loads((BASELINE / 'versions.json').read_text())
        verify_source(report, dict(integration_layers=old['integration_layers'] + ['badge-story']), old)

    def test_actual_compiled_source_report_has_reviewed_scope_and_avatar_bytes(self):
        self.verify(self.source())

    def test_source_scope_cannot_expand_or_drop_an_output(self):
        for extra in ['data/layouts/SixIsland_Frlg/map.bin', None]:
            report = self.source()
            if extra:
                report['changed_files'].append(extra)
                report['allowed_changed_files'].append(extra)
            else:
                report['changed_files'].pop()
            with self.assertRaises(AssertionError): self.verify(report)

    def test_abi_pwt_and_geometry_guarantees_are_mandatory(self):
        report = self.source()
        report['compiled_abi']['sizeof(struct SaveBlock1)'] += 4
        with self.assertRaises(AssertionError): self.verify(report)
        for key in ['atlas_graphics_unchanged', 'coastlines_and_gym_geometry_unchanged',
                    'native_trainer_parties_unchanged']:
            report = self.source(); report[key] = False
            with self.assertRaises(AssertionError): self.verify(report)
        report = self.source(); report['field_event']['native_pwt_implementation_unchanged'] = False
        with self.assertRaises(AssertionError): self.verify(report)

    def test_all_regular_and_stadium_avatar_frames_must_match_native_rival_scale(self):
        for index in range(4):
            report = self.source()
            report['avatars']['avatars'][index]['frames'][8]['visible_height'] = 12 if index % 2 else 30
            with self.assertRaises(AssertionError): self.verify(report)
        report = self.source(); report['avatars']['avatars'][2]['compiled']['sha256'] = '0' * 64
        with self.assertRaises(AssertionError): self.verify(report)

    def test_native_captures_are_complete_hashed_pngs(self):
        with tempfile.TemporaryDirectory(prefix='badge-story-pixels-', dir='/tmp') as temporary:
            directory = Path(temporary)
            path = directory / 'observation.png'
            fixture = Image.new('RGB', (240, 160))
            fixture.putdata([(40 + x % 2 * 160, 80 + y % 2 * 100, 120)
                             for y in range(160) for x in range(240)])
            fixture.save(path)
            report = dict(captures=[dict(file=path.name,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())])
            verify_captures(report, directory, {'observation'})
            with self.assertRaises(AssertionError): verify_captures(report, directory, {'missing'})
            path.write_bytes(path.read_bytes() + b'changed')
            with self.assertRaises(AssertionError): verify_captures(report, directory, {'observation'})
            Image.new('RGB', (240, 160), 'black').save(path)
            report['captures'][0]['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            with self.assertRaisesRegex(AssertionError, 'Uniform native capture'):
                verify_captures(report, directory, {'observation'})
            report['captures'][0]['file'] = '../observation.png'
            with self.assertRaises(AssertionError): verify_captures(report, directory, set())


class NativeBadgeStoryReportContracts(unittest.TestCase):
    directory = BASELINE.parent / 'Gen1-9-Normal'

    def gates(self):
        return json.loads((self.directory / 'badge-gates.json').read_text())

    def rivals(self):
        return json.loads((self.directory / 'rival-identities.json').read_text())

    def test_actual_gate_and_rival_observations_pass_their_strict_contracts(self):
        verify_badge_gates(self.gates(), self.directory)
        verify_rival_identities(self.rivals(), self.directory)

    def test_native_rules_must_match_the_edition_rom_identity(self):
        info = dict(variants=[dict(sha256=self.rivals()['rom_sha256'], max_national=1025,
                                   perfect_trainer_ivs=False)])
        for key, value in [('max_national', 493), ('perfect_trainer_ivs', True)]:
            report = self.rivals(); report[key] = value
            with self.assertRaises(AssertionError):
                verify_proof(report, self.directory, 'rival-identities', False,
                             BASELINE / 'test.sav', info, {})

    def test_missing_or_duplicate_permission_distributions_are_rejected(self):
        for replacement in [None, 0]:
            report = self.gates()
            if replacement is None:
                report['permission_cases'].pop()
            else:
                report['permission_cases'][-1] = copy.deepcopy(report['permission_cases'][replacement])
            with self.assertRaises(AssertionError): verify_badge_gates(report, self.directory)

    def test_league_qualification_cannot_require_24_or_galactic_completion(self):
        report = self.gates()
        row = next(row for row in report['permission_cases']
                   if row['total'] == 18 and row['qualifier_won'] and row['galactic_state'] == 0)
        row['league_permissions'] = [0, 0, 0]
        with self.assertRaises(AssertionError): verify_badge_gates(report, self.directory)

    def test_galactic_cannot_appear_at21_or_wait_until24(self):
        for total in [21, 22]:
            report = self.gates()
            row = next(row for row in report['grunt_visibility_cases']
                       if row['total'] == total and row['galactic_state'] == 0)
            row['visible'] = not row['visible']
            with self.assertRaises(AssertionError): verify_badge_gates(report, self.directory)

    def test_route23_proof_needs_both_surf_crossings_and_real_controller_outcomes(self):
        for key in ['initial_surf_fixture', 'controller_crossing']:
            report = self.gates()
            report['physical_checkpoints'][4][key] = False
            with self.assertRaises(AssertionError): verify_badge_gates(report, self.directory)
        report = self.gates(); report['physical_checkpoints'].pop()
        with self.assertRaises(AssertionError): verify_badge_gates(report, self.directory)

    def test_prior_elite_entry_cannot_bypass_qualifier_victory(self):
        report = self.gates()
        row = next(row for row in report['physical_leagues'] if row['prior_elite_entry'])
        row.update(allowed=True, physical_controller_entry=True, physical_controller_denial=False)
        with self.assertRaises(AssertionError): verify_badge_gates(report, self.directory)

    def test_galactic_still_needs_all_prior_crossover_visits(self):
        report = self.gates()
        row = next(row for row in report['physical_galactic_entry'] if row['crossover_visits'] == 0)
        row['admitted'] = True
        with self.assertRaises(AssertionError): verify_badge_gates(report, self.directory)

    def test_hashed_native_gate_captures_are_required(self):
        report = self.gates(); report['captures'].pop()
        with self.assertRaises(AssertionError): verify_badge_gates(report, self.directory)

    def test_rivals_cannot_copy_the_selected_hero_or_use_the_wrong_birthplace(self):
        report = self.rivals()
        row = report['identity_contexts'][0]
        row['roles'][0] = row['player_hero']
        with self.assertRaises(AssertionError): verify_rival_identities(report, self.directory)
        report = self.rivals()
        row = report['trainer_observations'][0]
        row['expected_hero'] = row['observed_hero'] = row['player_hero']
        with self.assertRaises(AssertionError): verify_rival_identities(report, self.directory)

    def test_native_trainer_ids_names_and_portraits_cannot_be_relabelled(self):
        for key, value in [('trainer_id', 1801), ('name', 'MAY'), ('trainer_pic', 99)]:
            report = self.rivals(); report['trainer_observations'][0][key] = value
            with self.assertRaises(AssertionError): verify_rival_identities(report, self.directory)

    def test_every_native_map_and_context_is_observed_once(self):
        report = self.rivals()
        report['map_observations'][-1] = copy.deepcopy(report['map_observations'][0])
        with self.assertRaises(AssertionError): verify_rival_identities(report, self.directory)

    def test_wally_and_blue_keep_their_native_identity(self):
        for key, value in [('observed_hero', 1), ('name', 'RED'), ('trainer_pic', 3)]:
            report = self.rivals(); report['negative_controls'][0][key] = value
            with self.assertRaises(AssertionError): verify_rival_identities(report, self.directory)

    def test_representative_rival_scenes_need_controller_battles_and_loaded_portraits(self):
        for key, value in [('actual_attacks', 0), ('controller_triggered', False),
                           ('battle_outcome', 2), ('native_scene_completed', False)]:
            report = self.rivals(); report['actual_encounters'][0][key] = value
            with self.assertRaises(AssertionError): verify_rival_identities(report, self.directory)
        report = self.rivals(); report['actual_encounters'][0]['portrait']['trainer_pic'] = 3
        with self.assertRaises(AssertionError): verify_rival_identities(report, self.directory)


class NativeQualifierReportContracts(unittest.TestCase):
    directory = BASELINE.parent / 'Gen1-9-Normal'

    def report(self):
        return json.loads((self.directory / 'qualifier-event.json').read_text())

    def verify(self, report):
        verify_qualifier_event(report, self.directory)

    def test_actual_native_qualifier_ledgers_battles_items_and_celebration_pass(self):
        self.verify(self.report())

    def test_native_results_need_every_pair_once_and_a_real_final(self):
        report = self.report()
        report['attempts'][2]['final_core']['ledger'][4] = copy.deepcopy(report['attempts'][2]['final_core']['ledger'][0])
        with self.assertRaises(AssertionError): self.verify(report)
        report = self.report(); report['attempts'][2]['player_battles'].pop()
        with self.assertRaises(AssertionError): self.verify(report)

    def test_losses_go_to_center_without_qualification(self):
        for key, value in [('map', 'BattleFrontier_OutsideWest'), ('state', 3), ('won', True)]:
            report = self.report(); report['attempts'][0]['after'][key] = value
            with self.assertRaises(AssertionError): self.verify(report)

    def test_native_defeat_keeps_ordinary_money_deduction_observable(self):
        report = self.report()
        loss = report['attempts'][0]['after']
        self.assertLess(loss['money_after'], loss['money_before'])
        self.verify(report)
        report['attempts'][2]['after']['money_after'] = -1
        with self.assertRaises(AssertionError): self.verify(report)

    def test_each_real_battle_starts_with_healed_hp_pp_and_status(self):
        for key, value in [('hp', 1), ('status', 8), ('pp', [0, 0, 0, 0])]:
            report = self.report(); report['attempts'][2]['player_battles'][1]['entry_party'][0][key] = value
            with self.assertRaises(AssertionError): self.verify(report)

    def test_consumed_berry_is_restored_by_pokemon_identity(self):
        report = self.report(); report['attempts'][2]['player_battles'][1]['entry_party'][0]['item'] = 0
        with self.assertRaises(AssertionError): self.verify(report)
        report = self.report(); report['attempts'][2]['player_battles'][0]['berry_consumed_natively'] = False
        with self.assertRaises(AssertionError): self.verify(report)
        report = self.report(); report['attempts'][2]['after']['native_party_switch'] = False
        with self.assertRaises(AssertionError): self.verify(report)
        report = self.report(); report['attempts'][2]['player_battles'][0]['active_party_indices'] = [0]
        with self.assertRaises(AssertionError): self.verify(report)

    def test_bag_consumption_and_experience_cannot_be_rolled_back(self):
        report = self.report(); report['attempts'][2]['after']['x_attack_after'] = 5
        with self.assertRaises(AssertionError): self.verify(report)
        report = self.report(); report['attempts'][2]['after']['total_experience_gain'] = 0
        with self.assertRaises(AssertionError): self.verify(report)

    def test_pwt_or_facility_flags_cannot_enter_campaign_battles(self):
        report = self.report(); report['attempts'][2]['player_battles'][0]['battle_flags'] |= 0x100
        with self.assertRaises(AssertionError): self.verify(report)
        report = self.report(); report['attempts'][2]['player_battles'][0]['command_menu_capture'] = False
        with self.assertRaises(AssertionError): self.verify(report)

    def test_eren_luffy_are_whole_native_objects_at_the_rival_scale(self):
        for index in [4, 5]:
            report = self.report()
            report['attempts'][0]['outdoor_intro']['objects'][index]['native_obj_pixels']['opaque_bbox'][3] = 12 if index == 4 else 30
            with self.assertRaises(AssertionError): self.verify(report)
        report = self.report()
        report['attempts'][0]['outdoor_intro']['objects'][4]['native_obj_pixels']['matching_scanout_pixels'] = 0
        with self.assertRaises(AssertionError): self.verify(report)

    def test_all_five_speeches_need_their_own_context_outside(self):
        for key, value in [('map', 'JourneyPWTArena'), ('text', 'Congratulations!')]:
            report = self.report(); report['celebrations'][0][key] = value
            with self.assertRaises(AssertionError): self.verify(report)
        report = self.report(); report['celebrations'].pop()
        with self.assertRaises(AssertionError): self.verify(report)

    def test_pwt_state_and_battle_points_are_untouched(self):
        for key, value in [('initial_state_sha256', '0' * 64), ('battle_points', 1)]:
            report = self.report(); report['pwt_isolation'][key] = value
            with self.assertRaises(AssertionError): self.verify(report)

    def test_win_is_saved_and_interrupted_arena_cannot_manufacture_it(self):
        report = self.report(); report['saved_win']['native_flash_roundtrip'] = False
        with self.assertRaises(AssertionError): self.verify(report)
        report = self.report(); report['interrupted_arena']['qualifier_won'] = True
        with self.assertRaises(AssertionError): self.verify(report)


if __name__ == '__main__':
    unittest.main()
