"""Reject incomplete portal objects, fabricated routes and lost old batteries."""
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest

from PIL import Image

from publish_coastal_closures import copy_current_proof
from validate_generated_cave_portals import verify_report

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = Path(os.environ.get('CAVE_PORTALS_PROOF_DIR',
    ROOT/'mods/hoenn/generated-area-review-validation/common/native/caves'))


class GeneratedCaveNativeProofs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.actual = json.loads((DIRECTORY/'caves.json').read_bytes())

    def reject(self, change):
        report = copy.deepcopy(self.actual)
        change(report)
        with self.assertRaises(AssertionError):
            verify_report(report, DIRECTORY, self.actual['rom_sha256'])

    def test_native_whole_objects_actors_exit_floor_and_batteries_pass(self):
        verify_report(self.actual, DIRECTORY, self.actual['rom_sha256'])

    def test_half_arch_or_missing_extra_left_arch_cell_is_rejected(self):
        self.reject(lambda r: r['portals'][0]['pixels']['cells'].pop())
        self.reject(lambda r: r['portals'][1]['pixels']['cells'].pop(0))

    def test_a_south_threshold_must_be_proved_as_a_complete_three_cell_lip(self):
        self.reject(lambda r: r['portals'][2]['pixels']['cells'].pop())
        self.reject(lambda r: r['portals'][3]['target'].update(collision=0))

    def test_collision_flag_without_a_controller_bump_is_rejected(self):
        self.reject(lambda r: r['portals'][0].update(held_frames=0))
        self.reject(lambda r: r['portals'][1]['after'].update(tile=[30, 25]))
        self.reject(lambda r: r.update(controls=[c for c in r['controls'] if c['phase'] != 'retired-portal-1']))

    def test_isolated_portal_placement_must_not_replace_real_entry_trip(self):
        self.reject(lambda r: r['fixtures'][-1].update(map='JourneyCaveHorizonte', tile=[15, 20]))
        self.reject(lambda r: r['route'].append(dict(phase='usable-floor-5',
            source=['JourneyCaveHorizonte', 14, 32], destination=['JourneyCaveHorizonte', 15, 20])))

    def test_actor_presence_and_all_three_adjacent_arrivals_are_required(self):
        self.reject(lambda r: r['actor_approaches'][0]['object'].update(local_id=1))
        self.reject(lambda r: r['actor_approaches'].pop())
        self.reject(lambda r: r['arrivals'][3]['player'].update(tile=[10, 31]))
        self.reject(lambda r: next(c for c in r['route'] if c['phase'] == 'usable-floor-1').update(phase='usable-floor-0'))

    def test_the_actual_exit_and_controller_return_cannot_be_omitted(self):
        self.reject(lambda r: r['arrivals'].pop())
        self.reject(lambda r: r['arrivals'][4]['player'].update(map='JourneyCaveHorizonte'))

    def test_false_stair_must_walk_both_ways_without_a_jump(self):
        self.reject(lambda r: r['corrected_floor']['arrivals'].pop())
        self.reject(lambda r: r['corrected_floor']['samples'][0].update(action=0x44))
        self.reject(lambda r: r['corrected_floor']['jump_actions'].remove(0x3A))
        self.reject(lambda r: r['corrected_floor']['samples'][0].update(landing_jump=True))
        self.reject(lambda r: r['corrected_floor']['grid'].update(metatile=0x209))

    def test_a_midtrip_avatar_state_write_is_not_a_readonly_query(self):
        self.reject(lambda r: r['queries'].append(dict(phase='usable-floor-1',
            function='SetPlayerAvatarTransitionFlags', arguments=[1])))

    def test_legacy_battery_must_come_from_the_real_old_passable_door(self):
        self.reject(lambda r: r['parent_legacy_fixture']['entered'].update(tile=[15, 20]))
        self.reject(lambda r: r['parent_legacy_fixture'].update(rom_sha256=r['rom_sha256']))
        self.reject(lambda r: r['parent_legacy_fixture']['queries'].append(dict(phase='legacy-passable-north-door',
            function='SetPlayerAvatarTransitionFlags', arguments=[1])))

    def test_continue_must_escape_the_new_blocked_door_using_down(self):
        self.reject(lambda r: r['legacy_cold_continue']['runs'][1]['after_escape'].update(tile=[15, 19]))
        self.reject(lambda r: r['legacy_cold_continue']['runs'][1]['escape_input'].update(key=64))
        self.reject(lambda r: r['legacy_cold_continue']['runs'][1].update(loaded_grid_block=0x3214))

    def test_rehashed_wrong_scanout_pixel_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp)/'proof.json'
            copy_current_proof(DIRECTORY/'caves.json', destination)
            report = json.loads(destination.read_bytes())
            row = report['portals'][0]
            attachment = row['capture']
            image_path = destination.parent/attachment['file']
            image = Image.open(image_path).convert('RGB')
            x, y, *_ = row['pixels']['cells'][0]['samples'][0]
            image.putpixel((x, y), (255, 0, 255))
            image.save(image_path)
            attachment['sha256'] = hashlib.sha256(image_path.read_bytes()).hexdigest()
            next(c for c in report['captures'] if c['file'] == attachment['file'])['sha256'] = attachment['sha256']
            with self.assertRaises(AssertionError):
                verify_report(report, destination.parent, self.actual['rom_sha256'])

    def test_recursive_proof_copy_contains_both_batteries_and_all_cold_captures(self):
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp)/'proof.json'
            copy_current_proof(DIRECTORY/'caves.json', destination)
            report = json.loads(destination.read_bytes())
            verify_report(report, destination.parent, self.actual['rom_sha256'])
            old_battery = destination.parent/'parent170/layer170-retired-door.sav'
            self.assertEqual(old_battery.stat().st_size, 131072)
            old_battery.write_bytes(b'x'*131072)
            with self.assertRaises(AssertionError):
                verify_report(report, destination.parent, self.actual['rom_sha256'])


if __name__ == '__main__':
    unittest.main()
