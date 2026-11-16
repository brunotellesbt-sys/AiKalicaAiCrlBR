"""Execute version3 restore C with old geometry, sentinels and saved objects.

Host fixtures prove serialized record behavior and table equivalence; these
tests never stand in for an old-ROM battery continued in the new ROM.
"""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest

from atlas_surf_candidate_migration import render, resolve, upgrade_restore_source
from atlas_surf_legacy import _render as render_legacy
from atlas_surf_migration import render_fallback
from atlas_surface_batteries import migration_source
from test_atlas_surface_batteries import PREFIX, WRAPPERS
from test_atlas_surf_migration import EXACT, LEGACY, fixture_tables


TABLES = dict(maps=[(0x5a00,4,2,0,3),(0x5a01,2,2,3,1)],
              runs=[(2,0,0),(4,1,1),(8,1,2),(4,1,2)],
              targets=[(0x0304,10,20,2,1),(0x0405,4,5,129,3),(0x0304,8,9,130,1)],
              warps=[(0x5a00,0,0x5a00,0)])
EXTRA = r'''
void surfing(void) { saved.objectEvents[0].graphicsId=0x0201; }
void stale(void)
{
    saved.location.x=-123;saved.location.y=999;
    saved.objectEvents[0].currentCoords.x=999;saved.objectEvents[0].currentCoords.y=-999;
}
void unknown_warp(void) { saved.dynamicWarp.warpId=7;saved.dynamicWarp.x=-1;saved.dynamicWarp.y=-1; }
int template_id(void) { return saved.objectEventTemplates[0].localId; }
int location_x(void) { return saved.location.x; }
void follower(void)
{
    struct ObjectEvent *object=&saved.objectEvents[2];
    object->localId=OBJ_EVENT_ID_FOLLOWER;object->active=1;
    object->currentCoords.x=saved.pos.x+6;object->currentCoords.y=saved.pos.y+7;
    object->previousCoords=object->initialCoords=object->currentCoords;
}
int follower_x(void) { return saved.objectEvents[2].currentCoords.x; }
int follower_active(void) { return saved.objectEvents[2].active; }
void point(u16 packed,s16 x,s16 y,u8 surf,s16 *out)
{
    const struct JourneyAtlasSaveMove *move;
    reset(2,packed,x,y);if(surf) surfing();
    move=JourneyCandidateResolve(packed>>8,packed&255,x,y);
    if(move==NULL) { out[0]=-1;return; }
    out[0]=(move->newGroup<<8)|move->newNum;
    out[1]=x+move->dx;out[2]=y+move->dy;out[3]=move->mode;out[4]=move->elevation;
}
'''


class CandidateSaveRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(); root = Path(cls.temp.name); (root/'data').mkdir()
        (root/'data/journey_atlas_legacy.h').write_text(render_legacy(LEGACY))
        (root/'data/journey_atlas_migration.h').write_text(render_fallback(fixture_tables()))
        (root/'data/journey_atlas_candidate_migration.h').write_text(render(TABLES,refresh_native_maps=[0x0704]))
        source = PREFIX+'\n#define MAP_OFFSET 7\n'+upgrade_restore_source(migration_source(
            EXACT,fallback_header='data/journey_atlas_migration.h'))+WRAPPERS+EXTRA
        (root/'migration.c').write_text(source)
        subprocess.run(['gcc','-std=gnu17','-Wall','-Wextra','-Werror','-shared','-fPIC',
                        str(root/'migration.c'),'-o',str(root/'migration.so')],check=True,capture_output=True)
        cls.native = ctypes.CDLL(str(root/'migration.so'))

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def test_every_cell_and_invalid_coordinate_matches_independent_host_oracle(self):
        for packed,w,h,_,_ in TABLES['maps']:
            for x,y in [(x,y) for y in range(h) for x in range(w)]+[(-1,-1),(999,-123)]:
                for surf in [False,True]:
                    with self.subTest(packed=packed,x=x,y=y,surf=surf):
                        result=(ctypes.c_int16*5)();self.native.point(packed,x,y,surf,result)
                        self.assertEqual(tuple(result),resolve(TABLES,packed,x,y,surf))

    def test_published_save_uses_position_once_and_keeps_followers(self):
        self.native.reset(2,0x5a00,1,0);self.native.stale();self.native.follower();self.native.run()
        expected={0:3,1:11,2:20,3:0x0304,4:18,5:27,6:1,7:0,8:0,9:99,10:11,11:20,15:1,16:0x0201,17:127}
        self.assertEqual({k:self.native.get(k) for k in expected},expected)
        self.assertEqual(self.native.location_x(),11)
        self.assertEqual(self.native.follower_x(),17);self.assertEqual(self.native.follower_active(),1)
        before=[self.native.get(k) for k in range(18)];self.native.run()
        self.assertEqual([self.native.get(k) for k in range(18)],before)

    def test_retired_placeholder_and_bridge_prefer_saved_avatar_mode(self):
        self.native.reset(2,0x5a01,1,1);self.native.run()
        self.assertEqual([self.native.get(k) for k in (1,2,3,6)],[4,5,0x0405,3])
        self.native.reset(2,0x5a01,1,1);self.native.surfing();self.native.run()
        self.assertEqual([self.native.get(k) for k in (1,2,3,6)],[8,9,0x0304,1])

    def test_known_portal_retains_its_id_and_unset_coordinates(self):
        self.native.reset(2,0x5a00,1,0);self.native.set_event_warp();self.native.run()
        self.assertEqual([self.native.get(k) for k in (12,13,14)],[0x5a00,0,-1])

    def test_unknown_portal_uses_center_rescue_and_clears_invalid_id(self):
        self.native.reset(2,0x5a00,1,0);self.native.unknown_warp();self.native.run()
        self.assertEqual([self.native.get(k) for k in (12,13,14)],[0x0304,-1,8])

    def test_versions_zero_one_translate_directly_into_current_mesh(self):
        for version,x in [(0,10),(1,18)]:
            self.native.reset(version,0x0102,x,5);self.native.run();self.native.run()
            self.assertEqual(self.native.get(0),3);self.assertEqual(self.native.get(1),18)
        self.native.reset(1,0x0203,1,1);self.native.run()
        self.assertEqual([self.native.get(k) for k in (0,1,2,3)],[3,21,31,0x0304])

    def test_native_actor_refresh_is_limited_to_changed_maps(self):
        for version in [0,1,2]:
            self.native.reset(version,0x0704,7,7);self.native.run()
            self.assertEqual([self.native.get(k) for k in (1,2,3,7,15)],[7,7,0x0704,0,1])
            self.assertEqual(self.native.template_id(),0)
        self.native.reset(2,0x0601,7,7);self.native.run()
        self.assertEqual([self.native.get(k) for k in (7,15)],[1,0]);self.assertEqual(self.native.template_id(),7)
        self.assertEqual(self.native.get(8),0)
        self.native.reset(3,0x0704,7,7);self.native.run()
        self.assertEqual([self.native.get(k) for k in (7,8,15)],[1,0x1234,0])

    def test_changed_restore_anchor_is_rejected(self):
        text=migration_source(EXACT,fallback_header='data/journey_atlas_migration.h')
        with self.assertRaises(ValueError):upgrade_restore_source(text.replace('version >= 2','version >= 9'))


if __name__=='__main__':unittest.main()
