"""Reject visually wrong or fabricated proofs of the reported Surf defects."""
import copy
import json
from pathlib import Path
import unittest

from verify_sevii_route_boundaries_native import verify_report

ROOT=Path(__file__).resolve().parents[2]
DIRECTORY=ROOT/'mods/hoenn/sevii-route-boundaries-validation/common/native'


class NativeBoundaryProofs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.actual=json.loads((DIRECTORY/'sevii-route-boundaries-native.json').read_text())

    def reject(self, change):
        report=copy.deepcopy(self.actual)
        change(report)
        with self.assertRaises(AssertionError):
            verify_report(report,DIRECTORY,self.actual['rom_sha256'])

    def test_current_native_observations_and_attachments_pass(self):
        verify_report(self.actual,DIRECTORY,self.actual['rom_sha256'])

    def test_dry_flag_alone_cannot_hide_a_surf_blob_on_the_dock(self):
        self.reject(lambda r:r['southern_loop']['arrivals'][9]['state'].update(active_surf_blobs=1))

    def test_default_reef_in_the_second_camera_is_rejected(self):
        self.reject(lambda r:r['corner_cases'][0]['after']['grid'].update(metatile=0x243))

    def test_visual_corner_must_not_open_the_undefined_movement_cell(self):
        self.reject(lambda r:r['corner_cases'][0]['after']['grid'].update(collision=0,border_id=1))

    def test_stale_second_continue_position_is_rejected(self):
        self.reject(lambda r:r['save_migration']['second_continue']['runs'][1].update(player_tile=[28,2]))

    def test_missing_animation_phase_is_rejected(self):
        self.reject(lambda r:r['shoreline_animation']['phases_observed']['ocean'].pop())

    def test_player_state_writes_are_not_readonly_observations(self):
        self.reject(lambda r:r['native_calls'].append(dict(phase='continuous-south-loop',
            function='SetPlayerAvatarTransitionFlags',arguments=[1],purpose='read-only-query')))

    def test_unbound_new_game_arrival_is_rejected(self):
        self.reject(lambda r:r['one_island_newgame']['case']['welcome']['player'].update(tile=[12,4]))


if __name__=='__main__':unittest.main()
