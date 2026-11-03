"""Reject incomplete trips, hidden feet and fake legacy-save coverage."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from PIL import Image

from verify_arrival_coast_cinnabar_proof import verify

ROOT = Path(__file__).resolve().parents[2]
PROOF = ROOT/'mods/hoenn/arrival-coast-review-validation/common/photos/cinnabar/cinnabar-door-exit.json'


class CinnabarProofContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(PROOF.read_bytes())

    def test_actual_final_controller_and_cold_continue_evidence_passes(self):
        verify(self.report, PROOF.parent)

    def test_rejects_missing_or_changed_geometry_observations(self):
        mutations = {
            'missing_deck_cell': lambda r: r['all_ten_dry_pier_cells'].pop(),
            'duplicated_edge': lambda r: r['perimeter'].__setitem__(1, r['perimeter'][0]),
            'no_actual_door': lambda r: r.__setitem__('controller_terminal_entry_and_exit', False),
            'walks_on_water': lambda r: r['perimeter'][4]['after'].__setitem__('tile', [12, 15]),
            'underpass_loses_surf': lambda r: r['underpass'][8].__setitem__('surfing', False),
            'cannot_reboard': lambda r: r['reboarded'].__setitem__('surfing', True),
            'wrong_door_priority': lambda r: r['door_exit'].__setitem__('priority', 2),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                report = copy.deepcopy(self.report)
                mutate(report)
                with self.assertRaises(AssertionError):
                    verify(report, PROOF.parent)

    def test_rejects_missing_stale_or_injected_legacy_save_proofs(self):
        mutations = {
            'wrong_old_save': lambda r: r['legacy_continue'].__setitem__('bundled_save_sha256', '0'*64),
            'stale_rom': lambda r: r['legacy_water_continue'].__setitem__('rom_sha256', '0'*64),
            'not_cold_boot': lambda r: r['legacy_continue'].__setitem__('controllers_only', False),
            'ram_injection': lambda r: r['legacy_water_continue'].__setitem__('no_game_memory_writes', False),
            'water_still_on_foot': lambda r: r['legacy_water_continue']['runs'][-1]['legacy_initial_state'].__setitem__('surfing', False),
            'missing_water_return': lambda r: r['legacy_water_continue']['runs'][-1]['legacy_controller_movements'].pop(),
            'missing_old_water_battery': lambda r: r.__setitem__('legacy_actual_walking_water_battery_tested', False),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                report = copy.deepcopy(self.report)
                mutate(report)
                with self.assertRaises(AssertionError):
                    verify(report, PROOF.parent)

    def test_rejects_capture_hash_changes(self):
        report = copy.deepcopy(self.report)
        report['captures'][0]['sha256'] = '0'*64
        with self.assertRaises(AssertionError):
            verify(report, PROOF.parent)

    def test_hidden_feet_fail_even_with_rehashed_image_and_correct_priority(self):
        report = copy.deepcopy(self.report)
        with tempfile.TemporaryDirectory() as name:
            output = Path(name)
            for row in report['captures']:
                path = output/row['file']
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(PROOF.parent/row['file'], path)
            path = output/'door-exit-on-high-pier.png'
            with Image.open(path) as original:
                picture = original.convert('RGB')
            # Cover the actual feet pixels, preserving the JSON's successful
            # state/priority flags and updating the PNG's attachment hash.
            for x, y, red, green, blue, band, unique in report['door_exit']['native_avatar_pixels']['expected_scanout_pixels']:
                if band == 2:
                    picture.putpixel((x, y), (0, 0, 255))
            picture.save(path)
            row = next(r for r in report['captures'] if r['file'] == path.name)
            row['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            with self.assertRaises(AssertionError):
                verify(report, output)


if __name__ == '__main__':
    unittest.main()
