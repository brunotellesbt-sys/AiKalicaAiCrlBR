"""Execute the actual rival selector against independent birthplace fixtures."""
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

from badge_story_rivals import (
    BATTLE_TEXT, DATA, GRAPHICS, LEGACY, RIVAL_DIALOGUE_EDITS,
    SPEAKER_MAPS, STRINGS, TEAM_FILES, repair,
)
from story_rival_contract import MAPS, NATIVE_TRAINERS, ROLES

HERE = Path(__file__).resolve().parent


def compiled_contract():
    source = (HERE / 'story_rivals.c').read_text()
    with tempfile.TemporaryDirectory(prefix='story-rival-c-') as temporary:
        root = Path(temporary)
        (root / 'constants').mkdir()
        (root / 'global.h').write_text('''#ifndef FIXTURE_GLOBAL_H
#define FIXTURE_GLOBAL_H
#include <stdint.h>
#include <stddef.h>
typedef uint8_t u8, bool8;
typedef uint16_t u16;
typedef uint32_t u32, bool32;
#define TRUE 1
#define FALSE 0
#define MALE 0
#define FEMALE 1
#define _(x) x
#define ARRAY_COUNT(x) (sizeof(x)/sizeof((x)[0]))
struct FixtureSave1 { struct {u8 mapGroup,mapNum;} location; };
struct FixtureSave2 {u8 playerGender;};
extern struct FixtureSave1 *gSaveBlock1Ptr;
extern struct FixtureSave2 *gSaveBlock2Ptr;
extern u8 isFrlg;
#endif
''')
        (root / 'constants/trainers.h').write_text('''#ifndef FIXTURE_TRAINERS_H
#define FIXTURE_TRAINERS_H
enum TrainerPicID {TRAINER_PIC_RED=11,TRAINER_PIC_LEAF,TRAINER_PIC_BRENDAN,TRAINER_PIC_MAY,NATIVE_PIC=99};
#endif
''')
        (root / 'data.h').write_text('''#include "global.h"
#include "constants/trainers.h"
struct Trainer {enum TrainerPicID trainerPic; const u8 *trainerName;};
extern const struct Trainer gFixtureTrainer;
static inline const struct Trainer *GetTrainerStructFromId(u16 id) {(void)id;return &gFixtureTrainer;}
''')
        (root / 'event_data.h').write_text('#include "global.h"\nu16 VarGet(u16);\n')
        (root / 'journey_birth.h').write_text('#include "global.h"\nbool32 JourneyAvatarIsKanto(void);\n')
        (root / 'constants/regions.h').write_text('')
        (root / 'constants/vars.h').write_text('''#define VAR_EVER_GRANDE_CITY_STATE 0x409E
#define VAR_JOURNEY_START_REGION 0x40FD
#define VAR_MAP_SCENE_ROUTE22 0x4154
''')
        graphics = sorted(set(re.findall(r'OBJ_EVENT_GFX_\w+', source))
                          | {'OBJ_EVENT_GFX_JOURNEY_GYM_BLUE', 'OBJ_EVENT_GFX_WALLY'})
        (root / 'constants/event_objects.h').write_text(''.join(
            f'#define {name} {i+100}\n' for i, name in enumerate(graphics)))
        (root / 'constants/opponents.h').write_text(''.join(
            f'#define {name} {i+1}\n' for i, (name, _, _) in enumerate(NATIVE_TRAINERS))
            + '#define TRAINER_JOURNEY_BLUE 1800\n#define TRAINER_WALLY 1700\n')
        (root / 'constants/maps.h').write_text(''.join(
            f'#define {name} 0x{i+1:02X}{i+1:02X}\n' for i, (_, name, _, _) in enumerate(MAPS)))
        shutil.copyfile(HERE / 'story_rivals.h', root / 'journey_story_rivals.h')
        expected_trainers = ','.join('{' + name + ',' + str(int(kanto)) + ',' + str(slot) + '}'
                                     for name, kanto, slot in NATIVE_TRAINERS)
        expected_maps = ','.join('{' + name + ',' + str(int(kanto)) + ',' + str(slot) + '}'
                                 for _, name, kanto, slot in MAPS)
        expected_roles = ','.join('{' + ','.join('{' + ','.join(map(str, ROLES[hero, region])) + '}'
                                               for hero in range(1, 5)) + '}' for region in range(3))
        main = r'''#include <stdio.h>
#include <string.h>
#include "global.h"
#include "data.h"
#include "constants/event_objects.h"
#include "constants/opponents.h"
#include "constants/maps.h"
#include "constants/vars.h"
#include "journey_story_rivals.h"
struct FixtureSave1 save1; struct FixtureSave2 save2;
struct FixtureSave1 *gSaveBlock1Ptr=&save1;
struct FixtureSave2 *gSaveBlock2Ptr=&save2;
const struct Trainer gFixtureTrainer={NATIVE_PIC,(const u8 *)"NATIVE"};
u8 isFrlg; u16 values[512]; bool32 legacyKanto;
u16 VarGet(u16 id) {return values[id-0x4000];}
bool32 JourneyAvatarIsKanto(void) {return legacyKanto;}
static void setvar(u16 id,u16 value) {values[id-0x4000]=value;}
static void map(u16 id) {save1.location.mapGroup=id>>8;save1.location.mapNum=id&255;}
static const char *names[]={"","RED","LEAF","BRENDAN","MAY"};
static const u16 gfx[]={0,OBJ_EVENT_GFX_RED_NORMAL,OBJ_EVENT_GFX_GREEN_NORMAL,OBJ_EVENT_GFX_BRENDAN_NORMAL,OBJ_EVENT_GFX_MAY_NORMAL};
static const enum TrainerPicID pics[]={NATIVE_PIC,TRAINER_PIC_RED,TRAINER_PIC_LEAF,TRAINER_PIC_BRENDAN,TRAINER_PIC_MAY};
struct ExpectedTrainer {u16 id;bool32 kanto;u8 slot;};
static const struct ExpectedTrainer trainers[]={TRAINERS};
struct ExpectedMap {u16 id;bool32 kanto;u8 slot;};
static const struct ExpectedMap maps[]={MAPS};
static const u8 roles[3][4][3]={ROLES};
#define CHECK(x) do {if(!(x)){fprintf(stderr,"line %d: %s\n",__LINE__,#x);return 1;}}while(0)
int main(void) {
 unsigned nativeChecks=0,mapChecks=0;
 for(unsigned birth=0;birth<3;birth++)for(unsigned hero=1;hero<=4;hero++) {
  setvar(VAR_EVER_GRANDE_CITY_STATE,hero);setvar(VAR_JOURNEY_START_REGION,birth);
  save2.playerGender=!(hero&1); // Match the chosen hero for real-game parity.
  CHECK(JourneyStoryPlayerHero()==hero);
  unsigned mask=1u<<hero;
  for(unsigned slot=0;slot<3;slot++) {unsigned h=JourneyStoryRivalHero(slot);CHECK(h==roles[birth][hero-1][slot]);CHECK(!(mask&(1u<<h)));mask|=1u<<h;}
  CHECK(mask==30);
  // An old mismatched gender field cannot replace the selected avatar.
  save2.playerGender^=1;CHECK(JourneyStoryPlayerHero()==hero);
  for(unsigned i=0;i<ARRAY_COUNT(trainers);i++) {
   unsigned expected=roles[birth][hero-1][trainers[i].kanto==(birth!=0)?0:trainers[i].slot];
   CHECK(JourneyStoryNativeTrainerHero(trainers[i].id)==expected);
   CHECK(!strcmp((const char*)JourneyStoryTrainerName(trainers[i].id),names[expected]));
   CHECK(JourneyStoryTrainerPic(trainers[i].id)==pics[expected]);nativeChecks++;
  }
  for(unsigned i=0;i<ARRAY_COUNT(maps);i++) {
   map(maps[i].id);isFrlg=maps[i].kanto;setvar(VAR_MAP_SCENE_ROUTE22,1);
   unsigned expected=roles[birth][hero-1][maps[i].kanto==(birth!=0)?0:maps[i].slot];
   CHECK(JourneyStoryCurrentRivalHero()==expected);
   CHECK(JourneyStoryRivalGraphics(maps[i].kanto?OBJ_EVENT_GFX_BLUE:OBJ_EVENT_GFX_RIVAL_BRENDAN_NORMAL)==gfx[expected]);
   CHECK(JourneyStoryRivalGraphics(OBJ_EVENT_GFX_JOURNEY_GYM_BLUE)==OBJ_EVENT_GFX_JOURNEY_GYM_BLUE);
   CHECK(JourneyStoryRivalGraphics(OBJ_EVENT_GFX_WALLY)==OBJ_EVENT_GFX_WALLY);
   for(unsigned explicit=1;explicit<=4;explicit++)CHECK(JourneyStoryRivalGraphics(gfx[explicit])==gfx[explicit]);
   if(maps[i].id==MAP_ROUTE22) {
    setvar(VAR_MAP_SCENE_ROUTE22,3);expected=roles[birth][hero-1][maps[i].kanto==(birth!=0)?0:1];
    CHECK(JourneyStoryCurrentRivalHero()==expected);
    CHECK(JourneyStoryRivalGraphics(OBJ_EVENT_GFX_BLUE)==gfx[expected]);
   }
   if(!maps[i].kanto) {
    u16 bike=expected==1?OBJ_EVENT_GFX_RED_BIKE:expected==2?OBJ_EVENT_GFX_GREEN_BIKE:expected==3?OBJ_EVENT_GFX_RIVAL_BRENDAN_MACH_BIKE:OBJ_EVENT_GFX_RIVAL_MAY_MACH_BIKE;
    CHECK(JourneyStoryRivalGraphics(OBJ_EVENT_GFX_RIVAL_MAY_MACH_BIKE)==bike);
   }
   mapChecks++;
  }
  CHECK(JourneyStoryNativeTrainerHero(TRAINER_WALLY)==0);
  CHECK(JourneyStoryNativeTrainerHero(TRAINER_JOURNEY_BLUE)==0);
  CHECK(JourneyStoryTrainerPic(TRAINER_JOURNEY_BLUE)==NATIVE_PIC);
  CHECK(!strcmp((const char*)JourneyStoryTrainerName(TRAINER_WALLY),"NATIVE"));
  map(0xFEFE);CHECK(JourneyStoryRivalGraphics(OBJ_EVENT_GFX_BLUE)==OBJ_EVENT_GFX_BLUE);
 }
 setvar(VAR_EVER_GRANDE_CITY_STATE,0);
 for(unsigned kanto=0;kanto<2;kanto++)for(unsigned female=0;female<2;female++) {
  legacyKanto=kanto;save2.playerGender=female;
  CHECK(JourneyStoryPlayerHero()==(kanto?1u:3u)+female);
 }
 printf("%u native identities and %u map contexts passed\n",nativeChecks,mapChecks);
 return 0;
}
'''.replace('{TRAINERS}', '{' + expected_trainers + '}').replace('{MAPS}', '{' + expected_maps + '}').replace('{ROLES}', '{' + expected_roles + '}')
        (root / 'main.c').write_text(main)
        binary = root / 'rivals'
        subprocess.run(['cc', '-std=c99', '-O2', '-Wall', '-Wextra', '-Werror',
                        '-fsanitize=undefined', '-fno-sanitize-recover=all', '-I', str(root),
                        str(HERE / 'story_rivals.c'), str(root / 'main.c'), '-o', str(binary)],
                       capture_output=True, text=True, check=True)
        return subprocess.run([str(binary)], capture_output=True, text=True)


class RivalLayerFixture:
    def __init__(self, root):
        self.source = Path(root)
        self.outputs = {}
        texts = {
            LEGACY: '/* old compatibility wrapper */\n',
            DATA: '#include "journey_rival.h"\nstatic inline const u8 *GetTrainerNameFromId(u16 trainerId)\n{\n    return GetTrainerStructFromId(trainerId)->trainerName;\n}\n',
            GRAPHICS: '#include "global.h"\nvoid Test(void) {\n    if (graphicsId == OBJ_EVENT_GFX_BLUE)\n        graphicsId = gSaveBlock2Ptr->playerGender == MALE ? OBJ_EVENT_GFX_GREEN_NORMAL : OBJ_EVENT_GFX_RED_NORMAL;\n}\n',
            STRINGS: '#include "global.h"\nstatic const u8 *ExpandPlaceholder_RivalName(void)\n{\n if (old) {return old;}\n return legacy;\n}\nvoid Unrelated(void) {}\n',
            BATTLE_TEXT: '''        enum TrainerClassID trainerClass = GetTrainerClassFromId(TRAINER_BATTLE_PARAM.opponentA);

        if (trainerClass == TRAINER_CLASS_RIVAL_EARLY_FRLG || trainerClass == TRAINER_CLASS_RIVAL_LATE_FRLG || trainerClass == TRAINER_CLASS_CHAMPION_FRLG)
            toCpy = GetExpandedPlaceholder(PLACEHOLDER_ID_RIVAL);
        else
            toCpy = GetTrainerNameFromId(trainerId);''',
            TEAM_FILES[0]: 'Native Hoenn teams unchanged\n',
            TEAM_FILES[1]: 'Native Kanto teams unchanged\n',
        }
        for name in SPEAKER_MAPS:
            edits = '\n'.join('\t.string ' + old for old, _ in RIVAL_DIALOGUE_EDITS.get(name, ()))
            texts[f'data/maps/{name}/scripts.inc'] = ('NativeScript::\n\tsetflag UNRELATED\n\treturn\n'
                'NativeRivalText:\n\t.string "MAY: Hello!$"\n\t.string "BRENDAN: Hello!$"\n' + edits + '\n')
        for path, text in texts.items():
            target = self.source / path; target.parent.mkdir(parents=True, exist_ok=True); target.write_text(text)
        self.expected = {path: hashlib.sha256(text.encode()).hexdigest() for path, text in texts.items()}

    def stage(self, path, contents):
        self.outputs[path] = contents.encode() if isinstance(contents, str) else contents


class StoryRivals(unittest.TestCase):
    def test_actual_c_handles_all_avatars_regions_and_native_encounters(self):
        result = compiled_contract()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('684 native identities and 300 map contexts passed', result.stdout)

    def test_all_hooks_compose_and_preserve_teams_commands_and_neighbor_code(self):
        with tempfile.TemporaryDirectory(prefix='story-rival-layer-') as temporary:
            layer = RivalLayerFixture(temporary)
            layer.outputs[GRAPHICS] = (layer.source / GRAPHICS).read_bytes() + b'// earlier composed repair\n'
            report = repair(layer)
            first = dict(layer.outputs)
            repair(layer)
            self.assertEqual(layer.outputs, first)
            self.assertEqual(len(layer.outputs), 18)
            self.assertEqual(report['native_trainers'], 57)
            self.assertTrue(layer.outputs[GRAPHICS].endswith(b'// earlier composed repair\n'))
            self.assertIn(b'void Unrelated(void) {}', layer.outputs[STRINGS])
            for path in TEAM_FILES:
                self.assertNotIn(path, layer.outputs)
            for name in SPEAKER_MAPS:
                path = f'data/maps/{name}/scripts.inc'
                self.assertIn(b'NativeScript::\n\tsetflag UNRELATED\n\treturn\n', layer.outputs[path])
                self.assertNotRegex(layer.outputs[path], rb'\.string "(?:MAY|BRENDAN):')
            for path, sha in layer.expected.items():
                self.assertEqual(hashlib.sha256((layer.source/path).read_bytes()).hexdigest(), sha)

    def test_unreviewed_parent_hook_is_rejected_without_writing_source(self):
        with tempfile.TemporaryDirectory(prefix='story-rival-negative-') as temporary:
            layer = RivalLayerFixture(temporary)
            broken = (layer.source / DATA).read_text().replace('return GetTrainerStructFromId(trainerId)->trainerName;', 'return unexpected;')
            (layer.source/DATA).write_text(broken)
            layer.expected[DATA] = hashlib.sha256(broken.encode()).hexdigest()
            with self.assertRaises(AssertionError):
                repair(layer)
            self.assertEqual((layer.source/DATA).read_text(), broken)


if __name__ == '__main__':
    unittest.main()
