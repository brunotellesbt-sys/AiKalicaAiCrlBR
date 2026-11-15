"""Compile and execute the real fallback, legacy RLE and versioned restore C."""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest

from atlas_surf_legacy import _render as render_legacy
from atlas_surface_batteries import migration_source
from atlas_surf_migration import fallback_tables,render_fallback
from test_atlas_surface_batteries import PREFIX,WRAPPERS


PIXEL=9|(8<<8)
EXACT=[dict(old_map='MAP_OLD',destination_map='MAP_NEW',source_rect=[1,1,2,2],
            destination_origin=[21,31],mode='surf',elevation=1,
            warp_relocations=[dict(old_warp_id=0,destination_warp_id=3)])]


def fixture_tables():
    def target(packed,tile,mode,elevation):
        return dict(map='Target',packed_id=packed,tile=tile,mode=mode,elevation=elevation,
                    atlas_pixel=PIXEL,word=0x1170 if mode=='surf' else 0x3001,behavior=0)
    return fallback_tables([PIXEL],dict(walk={PIXEL:target(0x0405,[4,5],'walk',3)},
                                       surf={PIXEL:target(0x0304,[8,9],'surf',1)}))


LEGACY=dict(maps=[(0,0x0203,0,4,4)],row_first=[0,0,0,0],run_ends=[4],run_pixels=[PIXEL],
            water=bytes([254,255]),index_bytes=2,end_bytes=1)
EXTRA=r'''
void unmatched_event_warp(void){saved.dynamicWarp.warpId=7;saved.dynamicWarp.x=-1;saved.dynamicWarp.y=-1;}
void stale_player_coordinates(void){saved.objectEvents[0].currentCoords.x=999;saved.objectEvents[0].currentCoords.y=-999;}
int template_id(void){return saved.objectEventTemplates[0].localId;}
'''


class FallbackRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();root=Path(cls.temp.name)
        (root/'data').mkdir()
        (root/'data/journey_atlas_legacy.h').write_text(render_legacy(LEGACY))
        (root/'data/journey_atlas_migration.h').write_text(render_fallback(fixture_tables()))
        source=PREFIX+'\n#define MAP_OFFSET 7\n'+migration_source(EXACT,fallback_header='data/journey_atlas_migration.h')+WRAPPERS+EXTRA
        (root/'migration.c').write_text(source)
        subprocess.run(['gcc','-std=gnu17','-Wall','-Wextra','-Werror','-shared','-fPIC',
                        str(root/'migration.c'),'-o',str(root/'migration.so')],check=True,capture_output=True)
        cls.native=ctypes.CDLL(str(root/'migration.so'))

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def test_exact_stamp_translation_has_priority_over_same_pixel_fallback(self):
        self.native.reset(1,0x0203,1,1);self.native.run()
        self.assertEqual([self.native.get(k) for k in (1,2,3,6)],[21,31,0x0304,1])

    def test_outside_stamp_uses_safe_surf_and_authoritative_saved_position(self):
        self.native.reset(1,0x0203,3,2);self.native.stale_player_coordinates();self.native.run()
        self.assertEqual([self.native.get(k) for k in (1,2,3,4,5,6)],[8,9,0x0304,15,16,1])
        self.assertEqual(self.native.get(7),0)
        self.assertEqual(self.native.get(8),0)
        self.assertEqual(self.native.template_id(),0)

    def test_clear_water_bit_uses_authenticated_ground_target(self):
        self.native.reset(1,0x0203,0,0);self.native.run()
        self.assertEqual([self.native.get(k) for k in (1,2,3,6)],[4,5,0x0405,3])

    def test_known_event_warp_uses_explicit_identity_and_preserves_unset_coords(self):
        self.native.reset(1,0x0203,3,2);self.native.set_event_warp();self.native.run()
        self.assertEqual([self.native.get(k) for k in (12,13,14)],[0x0304,3,-1])

    def test_unmatched_event_id_uses_declared_map_center_not_unset_coordinate(self):
        self.native.reset(1,0x0203,3,2);self.native.unmatched_event_warp();self.native.run()
        self.assertEqual([self.native.get(k) for k in (12,13,14)],[0x0304,-1,8])

    def test_version_two_never_reapplies_rescue_or_historical_treasure_translation(self):
        for version,x,expected in ((0,10,18),(1,18,18),(2,18,18)):
            self.native.reset(version,0x0102,x,5);self.native.run();self.native.run()
            self.assertEqual(self.native.get(1),expected)
        self.native.reset(1,0x0203,3,2);self.native.run()
        before=[self.native.get(k) for k in range(18)]
        self.native.run()
        self.assertEqual([self.native.get(k) for k in range(18)],before)


class FallbackTableTests(unittest.TestCase):
    def test_missing_pixel_targets_are_frozen_and_deduplicated(self):
        fixture=fixture_tables()
        candidates={'walk':{PIXEL:fixture['target_evidence'][0]},'surf':{PIXEL:fixture['target_evidence'][1]}}
        tables=fallback_tables([PIXEL,PIXEL+1,PIXEL+2],candidates)
        self.assertEqual(len(tables['targets']),2)
        self.assertEqual(len(tables['rows']),3)
        self.assertEqual(tables['maximum_rescue_distance'],2)
        self.assertEqual(tables['table_bytes'],30)

    def test_no_exact_rectangles_still_compiles_with_complete_legacy_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'data').mkdir()
            (root/'data/journey_atlas_legacy.h').write_text(render_legacy(LEGACY))
            (root/'data/journey_atlas_migration.h').write_text(render_fallback(fixture_tables()))
            (root/'migration.c').write_text(PREFIX+'\n#define MAP_OFFSET 7\n'+migration_source([],fallback_header='data/journey_atlas_migration.h')+WRAPPERS)
            subprocess.run(['gcc','-std=gnu17','-Wall','-Wextra','-Werror','-shared','-fPIC',
                            str(root/'migration.c'),'-o',str(root/'migration.so')],check=True,capture_output=True)


if __name__=='__main__':unittest.main()
