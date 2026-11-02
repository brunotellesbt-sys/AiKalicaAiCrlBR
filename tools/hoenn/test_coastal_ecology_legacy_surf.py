"""Exercise the native legacy-save guard and the exact restore lifecycle."""
from pathlib import Path
import hashlib
import subprocess
import tempfile
import unittest

from coastal_ecology_legacy_surf import ANCHOR, PATH, RECOVERY, repair


class LegacyWalkingWater(unittest.TestCase):
    def fixture(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        source = Path(temporary.name)
        target = source / PATH
        target.parent.mkdir(parents=True)
        target.write_text('/* native prefix */\n' + ANCHOR + '\n/* native suffix */\n')

        class Layer:
            def __init__(self):
                self.source, self.outputs = source, {}
                self.expected = {PATH: hashlib.sha256(target.read_bytes()).hexdigest()}

            def stage(self, path, raw):
                self.outputs[path] = raw.encode() if isinstance(raw, str) else raw

        return Layer()

    def test_only_stages_native_hook_after_all_saved_objects_and_sprites_exist(self):
        layer = self.fixture()
        before = (layer.source / PATH).read_bytes()
        report = repair(layer)
        self.assertEqual(set(layer.outputs), {PATH})
        self.assertEqual((layer.source / PATH).read_bytes(), before)
        result = layer.outputs[PATH].decode()
        self.assertIn('SpawnObjectEventsOnReturnToField(0, 0);\n    RecoverSeviiLegacyWalkingWater();\n    RotatingGate_', result)
        self.assertTrue(report['coordinates_and_elevations_preserved'])
        self.assertTrue(report['native_avatar_transition_without_direct_state_or_save_memory_writes'])

    def test_refuses_to_guess_when_native_return_to_field_order_changes(self):
        layer = self.fixture()
        (layer.source / PATH).write_text(ANCHOR.replace('SpawnObjectEventsOnReturnToField(0, 0);', 'SpawnObjectEventsOnReturnToField(1, 0);'))
        layer.expected[PATH] = hashlib.sha256((layer.source / PATH).read_bytes()).hexdigest()
        with self.assertRaisesRegex(AssertionError, 'lifecycle changed'):
            repair(layer)
        self.assertEqual(layer.outputs, {})

    def test_compiled_native_guard_recovers_only_invalid_legacy_walking_water(self):
        # Compile the emitted C itself. Cases include the real continued
        # save, a deck/bridge, another island, valid Surf and unrelated modes.
        harness = r'''
#include <assert.h>
typedef unsigned char u8;
typedef unsigned short u16;
struct ObjectEvent { struct {short x,y;} currentCoords; };
struct SaveBlock { struct {u8 mapGroup,mapNum;} location; } save;
struct SaveBlock *gSaveBlock1Ptr=&save;
struct ObjectEvent gObjectEvents[1];
struct {u8 objectEventId;} gPlayerAvatar;
#define MAP_ONE_ISLAND_TREASURE_BEACH 0
#define MAP_GROUP(x) 37
#define MAP_NUM(x) 46
#define PLAYER_AVATAR_FLAG_ON_FOOT 1
#define PLAYER_AVATAR_FLAG_SURFING 8
#define ELEVATION_SURF 1
#define FLAG_SYS_CRUISE_MODE 0
static int avatarFlags,playerElevation,mapElevation,water,cruise,calls,lastFlag;
static int TestPlayerAvatarFlags(int flag){return avatarFlags&flag;}
static int PlayerGetElevation(void){return playerElevation;}
static int FlagGet(int flag){return cruise;}
static int MapGridGetElevationAt(int x,int y){assert(x==28&&y==14);return mapElevation;}
static int MapGridGetMetatileBehaviorAt(int x,int y){assert(x==28&&y==14);return water;}
static int MetatileBehavior_IsSurfableWaterOrUnderwater(int behavior){return behavior;}
static void SetPlayerAvatarTransitionFlags(int flag){calls++;lastFlag=flag;}
'''
        harness += RECOVERY
        harness += r'''
int main(void){
    struct Case {int group,num,flags,playerHeight,mapHeight,wet,cruise,expected;} cases[]={
        {37,46,1,1,1,1,0,1}, /* real obsolete walking-water save */
        {37,46,1,1,1,1,1,0}, /* preserve intentional cruise state */
        {37,45,1,1,1,1,0,0}, /* neighboring One Island town */
        {36,46,1,1,1,1,0,0}, /* unrelated map group */
        {37,46,1,3,3,0,0,0}, /* ordinary dry pier */
        {37,46,1,3,1,1,0,0}, /* elevated pedestrian above water */
        {37,46,1,15,1,1,0,0},/* multi-level bridge */
        {37,46,1,1,0,1,0,0}, /* transition tile */
        {37,46,1,1,1,0,0,0}, /* non-water floor at level one */
        {37,46,8,1,1,1,0,0}, /* already Surfing; no duplicate blob */
        {37,46,16,1,1,1,0,0},/* underwater */
        {37,46,2,1,1,1,0,0}  /* bicycle */
    };
    unsigned i;
    for(i=0;i<sizeof(cases)/sizeof(cases[0]);i++){
        struct Case c=cases[i];
        save.location.mapGroup=c.group;save.location.mapNum=c.num;
        avatarFlags=c.flags;playerElevation=c.playerHeight;mapElevation=c.mapHeight;
        water=c.wet;cruise=c.cruise;calls=lastFlag=0;
        gObjectEvents[0].currentCoords.x=28;gObjectEvents[0].currentCoords.y=14;
        RecoverSeviiLegacyWalkingWater();
        assert(calls==c.expected);assert(lastFlag==(c.expected?8:0));
        assert(gObjectEvents[0].currentCoords.x==28&&gObjectEvents[0].currentCoords.y==14);
        assert(playerElevation==c.playerHeight&&mapElevation==c.mapHeight);
        assert(avatarFlags==c.flags&&save.location.mapGroup==c.group&&save.location.mapNum==c.num);
    }
    return 0;
}
'''
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / 'native-guard'
            subprocess.run(['cc', '-std=c99', '-Wall', '-Werror', '-x', 'c', '-', '-o', str(binary)],
                           input=harness, text=True, check=True, capture_output=True)
            subprocess.run([str(binary)], check=True)


if __name__ == '__main__':
    unittest.main()
