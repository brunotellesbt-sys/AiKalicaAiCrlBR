"""Require a separate, functioning inspection ROM and all nine annotated cave trips."""
import hashlib,json,unittest
from pathlib import Path
from package_review_rom import verify as verify_test
from verify_versions import verify
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'mods/hoenn/surf-review-validation'
class SurfReview(unittest.TestCase):
    def test_release_separates_review_behavior_and_normal_battles(self):
        info=verify(ROOT/'mods/hoenn/versions')
        while info.get('validation_scope') in ['dewford-coast-safety','extra-gyms','ever-grande-market','dewford-competitive-shop']:
            from verify_fuchsia_update import previous_release
            info=previous_release(info)
        self.assertEqual(info['validation_scope'],'surf-review')
        test=verify_test(ROOT/'roms/rom-de-teste',ROOT/'roms/Pokemon-Journey-Gen1-9-Normal.gba')
        self.assertTrue(test['separate_save_identity']);self.assertFalse(test['automatic_trainer_approaches']);self.assertFalse(test['random_wild_encounters'])
        for edition in ['Gen1-4-Normal','Gen1-4-Hard','Gen1-9-Normal','Gen1-9-Hard','TESTE']:
            r=json.loads((OUT/edition/'review-mode.json').read_text());self.assertEqual(r['review_mode'],edition=='TESTE')
            self.assertEqual(bool(r['checks']['trainer_approach_result']),edition!='TESTE')
    def test_every_edition_enters_and_returns_from_all_annotated_caves(self):
        for edition in ['native','Gen1-4-Normal','Gen1-4-Hard','Gen1-9-Normal','Gen1-9-Hard','TESTE']:
            r=json.loads((OUT/edition/'surf-review.json').read_text());self.assertEqual(len(r['caves']),9)
            self.assertTrue(all(c['controller_entry_and_return'] and c['native_map_open_zoom_return'] and c['cursor']==c['position'] for c in r['caves']))
        aprons=json.loads((OUT/'native/ocean-aprons.json').read_text());self.assertEqual(len(aprons['checks']),3)
        self.assertTrue(all(c['foreign_rock_rendered_before_map_transition'] and c['rock_graphics_unchanged_over_256_frames_in_both_banks'] for c in aprons['checks']))
        source=json.loads((OUT/'source.json').read_text());self.assertEqual(source['total_special_species'],105)
        self.assertEqual(len(source['redistributed_from_fullest']),8);self.assertTrue(source['legendary_capture_flags_and_species_preserved'])
        self.assertEqual(len({b['interior_template'] for b in source['branches'] if not b['existing_cave']}),8)
        self.assertGreaterEqual(len(source['boundaries']),96);self.assertTrue(source['all_exposed_route_limits_blocked'])
        self.assertTrue(source['independent_source_reproduced'] and source['idempotent'])
if __name__=='__main__':unittest.main()
