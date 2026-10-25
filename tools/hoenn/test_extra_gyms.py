"""Check the original gym proofs on their explicitly pinned release identity."""
import hashlib,json,unittest
from pathlib import Path
from verify_versions import verify
from verify_fuchsia_update import previous_release
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'mods/hoenn/extra-gyms-validation'
class ExtraGyms(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.release=verify(ROOT/'mods/hoenn/versions')
        cls.review=json.loads((ROOT/'roms/rom-de-teste/review.json').read_text())
        while cls.release['validation_scope'] in ('badge-story','coastal-closures','sevii-integrated-piers','dewford-coast-safety'):
            cls.review=json.loads((ROOT/cls.release['previous_review_validation']['file']).read_text())
            cls.release=previous_release(cls.release)
    def test_validated_gym_release_uses_correct_fairy_leader_and_all_badges(self):
        self.assertEqual(self.release['validation_scope'],'extra-gyms')
        expected={r['file'].removeprefix('Pokemon-Journey-').removesuffix('.gba'):r['sha256'] for r in self.release['variants']}
        expected['TESTE']=self.review['sha256']
        for edition,sha in expected.items():
            with self.subTest(edition=edition):
                r=json.loads((OUT/edition/'extra-gyms.json').read_text());self.assertEqual(r['rom_sha256'],sha)
                self.assertEqual(r['roster_cases'],40);self.assertEqual(len(r['gyms']),8)
                fairy=next(g for g in r['gyms'] if g['leader']=='WHITNEY')
                self.assertEqual(fairy['trainer'],1761 if edition.startswith('Gen1-4') else 1768)
                self.assertEqual(len(r['league']['missing_badge_cases']),24)
                self.assertTrue(r['league']['both_leagues_require_24'])
                self.assertTrue(r['all_24_badges_saved_and_continued'] and r['actual_three_page_trainer_card'])
    def test_gym_release_physical_routes_keep_their_native_roundtrips(self):
        r=json.loads((OUT/'native/surf-repairs.json').read_text())
        self.assertEqual(r['rom_sha256'],self.release['parent_rom_sha256'])
        self.assertEqual((r['links'],r['crossings']),(55,110))
        self.assertTrue(all(c['surf_continuous'] and c['returned_to_departure'] and c['loaded_tiles_match_current_bank'] for c in r['checks']))
        n=json.loads((OUT/'native/marine-network.json').read_text());self.assertEqual(n['rom_sha256'],r['rom_sha256'])
        self.assertEqual(len(n['towns']),7);self.assertTrue(n['all_seven_islands_reached_from_mossdeep'] and n['kanto_to_one_island_and_back'])
        self.assertEqual(hashlib.sha256((ROOT/'docs/videos/surf-connections-repaired.mp4').read_bytes()).hexdigest(),n['video_sha256'])
    def test_beaches_stop_surf_and_dry_piers_cannot_leak_to_ocean(self):
        r=json.loads((OUT/'native/coastal-landings.json').read_text())
        self.assertEqual(r['rom_sha256'],self.release['parent_rom_sha256'])
        self.assertTrue(r['all_repaired_beach_components_tested'] and r['surf_ends_on_land'])
        self.assertGreater(len(r['beaches']),16)
        self.assertTrue(r['decorative_collision_attempts'])
        p=json.loads((OUT/'native/map-finishing.json').read_text())
        self.assertEqual(p['rom_sha256'],r['rom_sha256']);self.assertEqual(len(p['ports']),7)
        self.assertTrue(p['restored_center_wall_blocks_controller'] and p['center_door_roundtrip'] and p['native_save_continue_on_pier'])
        self.assertTrue(all(x['foot_blocks_at_pier_end'] and x['controller_door_roundtrip'] and x['foot_drawn_above_bridge'] and x['under_pier_surf_roundtrip'] for x in p['ports']))
        d=json.loads((OUT/'native/coastal-details.json').read_text())
        self.assertEqual(d['rom_sha256'],r['rom_sha256'])
        self.assertEqual({c['map'] for c in d['dewford_shores']},{'DewfordTown','Route107'})
        for c in d['dewford_shores']:
            with self.subTest(map=c['map']):
                for check in ['native_disembark','native_surf_prompt','native_southern_terrain_restored','original_south_art_and_elevations_match_compiled_rom','original_border_retained']:
                    self.assertTrue(c[check],check)
    def test_atlas_and_prior_campaign_remain_and_pending_chapters_are_explicit(self):
        r=json.loads((OUT/'source.json').read_text());self.assertEqual(r['rom_sha256'],self.release['parent_rom_sha256'])
        self.assertTrue(r['atlas_graphics_unchanged'] and r['old_campaign_and_pwt_preserved'])
        self.assertTrue(r['save_and_link_abi_unchanged'] and r['allocated_flags_disjoint'])
        self.assertEqual(r['pending_story_milestones'],[18,22]);self.assertFalse(r['pending_story_events_implemented'])
        self.assertTrue(all(c['graphics_unchanged'] for c in r['coastal_fixes']['geography']['ornament_limits']))
if __name__=='__main__':unittest.main()
