"""Reject arrivals that retain passing labels but lose the native observations."""
from contextlib import contextmanager
import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from verify_arrival_coast_landing_proof import verify

ROOT = Path(__file__).resolve().parents[2]
PROOF = ROOT/'mods/hoenn/arrival-coast-review-validation/common/landing'


class ArrivalLandingEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='arrival-landing-contract-')
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.directory = Path(cls.temporary.name)/'landing'
        shutil.copytree(PROOF, cls.directory)
        cls.observed = json.loads((cls.directory/'arrival-coast-landing.json').read_bytes())

    def setUp(self):
        self.report = copy.deepcopy(self.observed)

    @contextmanager
    def altered_case(self, home, mutation):
        index = next(i for i, row in enumerate(self.report['cases']) if row['home_index'] == home)
        path = self.directory/self.report['components'][index]['file']
        original = path.read_bytes()
        case = json.loads(original)
        mutation(case)
        raw = (json.dumps(case, indent=2)+'\n').encode()
        path.write_bytes(raw)
        digest = hashlib.sha256(raw).hexdigest()
        for key in ('components', 'case_reports'):
            self.report[key][index]['sha256'] = digest
        self.report['cases'][index] = {key: value for key, value in case.items()
            if key not in ('captures', 'input_log', 'callback_transitions')}
        try:
            yield
        finally:
            path.write_bytes(original)

    def reject(self):
        with self.assertRaises(AssertionError):
            verify(self.report, self.directory)

    def test_complete_final_coldboots_are_accepted(self):
        verify(self.report, self.directory)
        self.assertEqual(len(self.report['cases']), 30)
        self.assertEqual(len(self.report['captures']), 210)

    def test_summary_flags_cannot_replace_actual_dry_ground(self):
        def corrupt(case):
            player = case['welcome']['player']
            player['surfing'] = True
            player['elevation'] = 1
            player['terrain'] = dict(block=0x112B, elevation=1, collision=0,
                                     behavior=21, surfable=True, dry=False)
        with self.altered_case(10, corrupt):
            self.reject()

    def test_wrong_dry_destination_cannot_reuse_the_right_bedroom(self):
        def corrupt(case):
            case['welcome']['player']['tile'][0] += 1
        with self.altered_case(11, corrupt):
            self.reject()

    def test_mother_height_and_npc_overlap_are_checked(self):
        def corrupt(case):
            case['welcome']['mother']['elevation'] = 1
            case['welcome']['other_npc_overlaps'] = [{'tile': case['welcome']['mother']['tile']}]
        with self.altered_case(21, corrupt):
            self.reject()

    def test_menu_only_boot_cannot_claim_a_complete_arrival(self):
        def corrupt(case):
            case['callback_transitions'] = [row for row in case['callback_transitions']
                if row['callback'] not in ('CB2_NewGame', 'CB2_Overworld')]
        with self.altered_case(1, corrupt):
            self.reject()

    def test_missing_voyage_cannot_keep_the_boat_observed_label(self):
        def corrupt(case):
            case['callback_transitions'] = [row for row in case['callback_transitions']
                if 'SeaGallop' not in row['callback']]
        with self.altered_case(29, corrupt):
            self.reject()

    def test_controller_labels_cannot_replace_the_input_log(self):
        with self.altered_case(31, lambda case: case.update(input_log=[])):
            self.reject()

    def test_stale_native_elf_in_a_rehashed_case_is_rejected(self):
        with self.altered_case(12, lambda case: case.update(elf_sha256='0'*64)):
            self.reject()

    def test_one_city_cannot_be_counted_twice(self):
        for key in ('cases', 'components', 'case_reports'):
            self.report[key][-1] = copy.deepcopy(self.report[key][0])
        self.reject()

    def test_full_components_are_required_alongside_summaries(self):
        self.report['components'] = []
        self.reject()

    def test_table_fields_must_reproduce_the_compiled_table_hash(self):
        self.report['compiled_arrival_census']['rows'][0]['truck'][0] += 1
        self.reject()

    def test_different_home_cannot_replace_the_selected_home(self):
        def corrupt(case):
            case['bedroom']['map'] = 'JourneyFamilyBedroom01'
        with self.altered_case(15, corrupt):
            self.reject()

    def test_native_pacifidlog_animation_does_not_allow_arbitrary_tiles(self):
        def corrupt(case):
            case['welcome']['player']['terrain']['block'] = 0x3263
        with self.altered_case(31, corrupt):
            self.reject()

    def test_capture_content_is_checked_not_only_the_json_labels(self):
        path = self.directory/'sevii-00/06-mother-welcome.png'
        original = path.read_bytes()
        try:
            path.write_bytes(original+b'changed')
            self.reject()
        finally:
            path.write_bytes(original)

    def test_case_capture_paths_cannot_escape_the_proof_directory(self):
        def corrupt(case):
            case['captures'][0]['file'] = '../outside.png'
        with self.altered_case(10, corrupt):
            self.reject()


if __name__ == '__main__':
    unittest.main()
