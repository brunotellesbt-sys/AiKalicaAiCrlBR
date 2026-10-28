"""Reject incomplete controller evidence and unreviewed resource scope."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from generated_world_contract import PREPARED_SHA256
from publish_generated_world_audit import load_plan, visual_archive_inputs
from verify_generated_world_update import verify_proof


class VisualArchiveReferences(unittest.TestCase):
    def fixture(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        audit = root/'docs/design/generated-world-audit'
        files = {'before/Area-source.png':b'baseline picture',
                 'marine/final/Area-source.png':b'canonical final picture',
                 'marine/final/whole-source-sheet-01.png':b'duplicate contact sheet',
                 'visual-review-coverage.json':b'{}', 'VISUAL-REVIEW.md':b'review notes'}
        for name, data in files.items():
            path = audit/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        subprocess.run(['git','init','-q',str(root)],check=True)
        subprocess.run(['git','-C',str(root),'add','docs'],check=True)
        subprocess.run(['git','-C',str(root),'-c','user.name=Fixture','-c','user.email=fixture@example.invalid',
                        'commit','-qm','reviewed visual fixture'],check=True)
        commit = subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
        return root,audit,commit

    def test_references_are_pinned_and_canonical_final_images_stay_in_zip(self):
        root,audit,commit = self.fixture()
        files = visual_archive_inputs(commit,root=root)
        manifest = json.loads((audit/'SOURCE-RENDERS.json').read_bytes())
        names = {p.relative_to(audit).as_posix() for p in files}
        self.assertEqual(names,{'marine/final/Area-source.png','visual-review-coverage.json',
                               'VISUAL-REVIEW.md','SOURCE-RENDERS.json'})
        self.assertEqual(len(manifest['repository_reference_images']),2)
        self.assertEqual(len(manifest['included_final_whole_images']),1)
        for row in manifest['repository_reference_images']:
            self.assertIn('/'+commit+'/',row['url'])
            self.assertEqual(hashlib.sha256((root/row['file']).read_bytes()).hexdigest(),row['sha256'])

    def test_modified_reference_cannot_be_labeled_as_a_committed_picture(self):
        root,audit,commit = self.fixture()
        (audit/'before/Area-source.png').write_bytes(b'modified after review')
        with self.assertRaisesRegex(AssertionError,'Uncommitted or stale reference render'):
            visual_archive_inputs(commit,root=root)


class GeneratedReleaseContract(unittest.TestCase):
    def check(self, report, kind):
        verify_proof(report, Path('.'), kind, False, Path('/unused'),
                     {'integration_layers':['source']}, {'parent_rom_sha256':'parent'})

    def navigation(self):
        planned = [dict(source='A',destination='B',start=[1,0],end=[1,2],direction='up',
                        mode='surf' if index < 980 else 'walk') for index in range(990)]
        cases = [dict(index=index,**row,passed=True,observed=dict(
                     position=[1,2],surf=row['mode']=='surf',loaded_block=0x1170,expected_block=0x1170))
                 for index,row in enumerate(planned)]
        return dict(passed=True,kind='generated-navigation',graph_passed=True,native_passed=True,
                    native_all_planned_cases_executed=True,compiled_behavior_and_collision_graph=True,
                    forced_ocean_currents_respected=True,native_directional_input=True,
                    initial_placements_party_and_defeated_trainer_flags_are_fixtures=True,
                    surface_maps=417,reviewed_edge_count=470,nonreciprocal_edges=[],
                    disconnected_generated_ocean_maps=[],native_cases=cases,planned_native_cases=planned,
                    native_case_count=990,planned_native_case_count=990,native_surf_case_count=980,
                    native_walk_case_count=10)

    def test_complete_controller_plan_accepted(self):
        self.check(self.navigation(),'generated-navigation')

    def test_missing_one_crossing_rejected_even_with_a_passed_flag(self):
        report=self.navigation();report['native_cases'].pop()
        with self.assertRaises(AssertionError):self.check(report,'generated-navigation')

    def test_duplicate_crossing_cannot_cover_another_case(self):
        report=self.navigation();report['native_cases'][1]=copy.deepcopy(report['native_cases'][0])
        with self.assertRaises(AssertionError):self.check(report,'generated-navigation')

    def test_surf_dropped_during_crossing_is_rejected(self):
        report=self.navigation();report['native_cases'][0]['observed']['surf']=False
        with self.assertRaises(AssertionError):self.check(report,'generated-navigation')

    def test_mismatched_loaded_map_block_is_rejected_even_with_a_passed_flag(self):
        report=self.navigation();report['native_cases'][0]['observed']['loaded_block']=0x3001
        with self.assertRaises(AssertionError):self.check(report,'generated-navigation')

    def test_claimed_walking_count_requires_actual_planned_and_observed_walking_cases(self):
        report=self.navigation()
        for index,row in enumerate(report['planned_native_cases']):
            row['mode']='surf'
            report['native_cases'][index].update(mode='surf')
            report['native_cases'][index]['observed']['surf']=True
        with self.assertRaises(AssertionError):self.check(report,'generated-navigation')

    def test_static_graph_is_not_enough_to_seal_a_release(self):
        report=self.navigation();report['native_all_planned_cases_executed']=False
        with self.assertRaises(AssertionError):self.check(report,'generated-navigation')

    def source(self):
        return dict(passed=True,kind='generated-world-source',layers=['source'],
                    parent_rom_sha256='parent',prepared_sha256=dict(PREPARED_SHA256),
                    changed_files=list(PREPARED_SHA256),source_hashes_checked=32240,
                    compiled_rom=True,preflight=False,independent_replay=True,idempotent=True,
                    unrelated_source_files_unchanged=True,atlas_graphics_unchanged=True,
                    campaign_and_save_abi_source_unchanged=True,
                    compiled_blockdata=[dict(file=name,sha256=sha,bytes=100)
                                        for name,sha in PREPARED_SHA256.items() if name.endswith('.bin')])

    def test_unreviewed_source_change_is_rejected(self):
        report=self.source();report['changed_files'].append('src/overworld.c')
        with self.assertRaises(AssertionError):self.check(report,'generated-world-source')

    def test_changed_source_hash_is_rejected(self):
        report=self.source();name=next(iter(report['prepared_sha256']))
        report['prepared_sha256'][name]='0'*64
        with self.assertRaises(AssertionError):self.check(report,'generated-world-source')

    def test_missing_compiled_block_cannot_pass_with_source_only_evidence(self):
        report=self.source();report['compiled_blockdata'].pop()
        with self.assertRaises(AssertionError):self.check(report,'generated-world-source')

    def test_same_house_cannot_supply_both_one_time_gifts(self):
        gifts=[dict(map='house',item=item,before=0,after=1,physical_door_entry_and_exit=True,
                    native_gift_once=True,repeat_conversation_does_not_duplicate=True) for item in (32,34)]
        report=dict(passed=True,kind='generated-ever-grande',physical_market_access_and_native_shop=True,gifts=gifts)
        with self.assertRaises(AssertionError):self.check(report,'generated-ever-grande')

    def test_explicit_plan_rejects_duplicate_and_escaping_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);(root/'proof.json').write_text('{}')
            row=dict(target='common',kind='proof',file='proof.json')
            path=root/'plan.json';path.write_text(json.dumps([row,row]))
            with self.assertRaises(AssertionError):load_plan(path,root)
            row['file']='../proof.json';path.write_text(json.dumps([row]))
            with self.assertRaises(AssertionError):load_plan(path,root)


if __name__=='__main__':unittest.main()
