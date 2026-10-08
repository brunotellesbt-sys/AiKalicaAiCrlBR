"""Migrate Kanto's opposite-sex rival while retaining Blue as a distinct leader."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from prepare_crossing import PIN
from prepare_free_access import LAYERS


def prepare(source):
    source = Path(source)
    marker = source / '.journey-rival'
    if marker.exists():
        report = json.loads(marker.read_text())
        for path, digest in report['prepared_sha256'].items():
            assert hashlib.sha256((source / path).read_bytes()).hexdigest() == digest, path
        return report
    acquired = json.loads((source / '.source-acquired.json').read_text())
    assert acquired['commit'] == PIN
    expected = dict(acquired['sha256'])
    for layer in LAYERS + ['free-access', 'blue-gym', 'road-access', 'mach-bike',
                          'yellow-stairs', 'story-access', 'story-completion', 'water-hms', 'ferry']:
        expected.update(json.loads((source / f'.journey-{layer}').read_text())['prepared_sha256'])
    inputs, originals, outputs = {}, {}, {}

    def read(path):
        raw = (source / path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected[path], path
        if path in acquired['sha256']: inputs[path] = acquired['sha256'][path]
        return raw

    def stage(path, body):
        if path in expected: originals[path] = hashlib.sha256(read(path)).hexdigest()
        elif (source / path).exists(): assert (source / path).read_bytes() == body.encode(), path
        outputs[path] = body.encode()

    stage('include/journey_rival.h', '''#ifndef GUARD_JOURNEY_RIVAL_H
#define GUARD_JOURNEY_RIVAL_H
#include "constants/trainers.h"
enum TrainerPicID JourneyRivalTrainerPic(u16 trainerId);
#endif
''')
    stage('src/journey_rival.c', '''#include "global.h"
#include "data.h"
#include "journey_rival.h"
#include "constants/opponents.h"

enum TrainerPicID JourneyRivalTrainerPic(u16 trainerId)
{
    enum TrainerPicID pic = GetTrainerStructFromId(trainerId)->trainerPic;
    // The gym leader intentionally shares the native champion portrait.
    if (trainerId == TRAINER_JOURNEY_BLUE)
        return pic;
    if (pic == TRAINER_PIC_RIVAL_EARLY_FRLG
        || pic == TRAINER_PIC_RIVAL_LATE_FRLG
        || pic == TRAINER_PIC_CHAMPION_RIVAL_FRLG)
        return gSaveBlock2Ptr->playerGender == MALE ? TRAINER_PIC_LEAF : TRAINER_PIC_RED;
    return pic;
}
''')
    path = 'include/data.h'
    body = read(path).decode()
    anchor = '#include "difficulty.h"'
    assert body.count(anchor) == 1
    body = body.replace(anchor, anchor + '\n#include "journey_rival.h"')
    anchor = '    return GetTrainerStructFromId(trainerId)->trainerPic;'
    assert body.count(anchor) == 1
    stage(path, body.replace(anchor, '    return JourneyRivalTrainerPic(trainerId);'))
    path = 'include/constants/event_objects.h'
    body = read(path).decode()
    anchor = '    NUM_OBJ_EVENT_GFX,\n'
    assert body.count(anchor) == 1
    stage(path, body.replace(anchor, '    OBJ_EVENT_GFX_JOURNEY_GYM_BLUE,\n' + anchor))
    path = 'src/data/object_events/object_event_graphics_info_pointers.h'
    body = read(path).decode()
    match = re.search(r'^\s*\[OBJ_EVENT_GFX_BLUE\].*?=\s*&([\w]+),$', body, re.M)
    assert match
    stage(path, body[:match.end()] + '\n    [OBJ_EVENT_GFX_JOURNEY_GYM_BLUE] = &' + match[1] + ',' + body[match.end():])
    path = 'src/event_object_movement.c'
    body = read(path).decode()
    anchor = '    if (graphicsId == OBJ_EVENT_GFX_BARD)'
    assert body.count(anchor) == 1
    stage(path, body.replace(anchor, '''    if (graphicsId == OBJ_EVENT_GFX_BLUE)
        graphicsId = gSaveBlock2Ptr->playerGender == MALE ? OBJ_EVENT_GFX_GREEN_NORMAL : OBJ_EVENT_GFX_RED_NORMAL;

''' + anchor))
    path = 'data/maps/ViridianCity_Gym_Frlg/map.json'
    before = json.loads(read(path))
    after = json.loads(json.dumps(before))
    leaders = [o for o in after['object_events'] if o['graphics_id'] == 'OBJ_EVENT_GFX_BLUE']
    assert len(leaders) == 1
    leaders[0]['graphics_id'] = 'OBJ_EVENT_GFX_JOURNEY_GYM_BLUE'
    stage(path, json.dumps(after, indent=2) + '\n')
    path = 'src/oak_speech.c'
    body = read(path).decode()
    anchor = '''        LoadPalette(sOakSpeech_Rival_Pal, BG_PLTT_ID(6), sizeof(sOakSpeech_Rival_Pal));
        DecompressDataWithHeaderVram(sOakSpeech_Rival_Tiles, (void *)VRAM + 0x600 + tileOffset);'''
    assert body.count(anchor) == 1
    stage(path, body.replace(anchor, '''        if (gSaveBlock2Ptr->playerGender == MALE)
        {
            LoadPalette(sOakSpeech_Leaf_Pal, BG_PLTT_ID(6), sizeof(sOakSpeech_Leaf_Pal));
            DecompressDataWithHeaderVram(sOakSpeech_Leaf_Tiles, (void *)VRAM + 0x600 + tileOffset);
        }
        else
        {
            LoadPalette(sOakSpeech_Red_Pal, BG_PLTT_ID(6), sizeof(sOakSpeech_Red_Pal));
            DecompressDataWithHeaderVram(sOakSpeech_Red_Tiles, (void *)VRAM + 0x600 + tileOffset);
        }'''))
    path = 'src/naming_screen.c'
    body = read(path).decode()
    anchor = 'static void NamingScreen_CreateRivalIcon(void)\n{'
    start = body.index(anchor)
    end = body.index('\n}\n', start) + 3
    replacement = '''static void NamingScreen_CreateRivalIcon(void)
{
    u16 graphics = gSaveBlock2Ptr->playerGender == MALE ? OBJ_EVENT_GFX_GREEN_NORMAL : OBJ_EVENT_GFX_RED_NORMAL;
    u8 spriteId = CreateObjectGraphicsSprite(graphics, SpriteCallbackDummy, 56, 37, 0);
    gSprites[spriteId].oam.priority = 3;
    StartSpriteAnim(&gSprites[spriteId], ANIM_STD_GO_SOUTH);
}
'''
    stage(path, body[:start] + replacement + body[end:])
    path = 'data/text/new_game_intro_frlg.inc'
    body = read(path).decode()
    assert body.count('This is my grandson.') == 1
    stage(path, body.replace('This is my grandson.', 'This is my grandchild.'))
    # Enumerate every native FRLG rival team without altering its Pokemon.
    trainers = read('src/data/trainers_frlg.party').decode()
    rival_names = [name for name, entry in re.findall(r'^=== (\w+) ===\n(.*?)(?=^=== |\Z)', trainers, re.M | re.S)
                   if re.search(r'^Pic: (Rival Early Frlg|Rival Late Frlg|Champion Rival Frlg)$', entry, re.M)]
    assert rival_names
    id_text = read('include/constants/opponents.h').decode() + '\n' + read('include/constants/opponents_frlg.h').decode()
    ids = dict((n, int(v)) for n, v in re.findall(r'^#define\s+(TRAINER_\w+)\s+(\d+)', id_text, re.M))
    preserved = {p: hashlib.sha256(read(p)).hexdigest() for p in [
        'src/data/trainers_frlg.party', 'src/data/trainers.party',
        'data/maps/PalletTown_ProfessorOaksLab_Frlg/scripts.inc',
        'data/maps/SilphCo_7F_Frlg/scripts.inc']}
    report = dict(status='opposite_sex_kanto_rival_candidate', source_commit=PIN,
        male_player_rival='Leaf', female_player_rival='Red', rival_trainer_ids=[ids[n] for n in rival_names],
        rival_trainer_names=rival_names, gym_blue_trainer_id=ids['TRAINER_JOURNEY_BLUE'],
        blue_keeps_native_appearance=True, hoenn_rival_preserved=True,
        intro_and_naming_screen_updated=True, parties_and_event_scripts_unchanged=True,
        event_changes=[dict(map='ViridianCity_Gym_Frlg', before=before, after=after)],
        preserved_native_sha256=preserved, full_story_validated=False, requires_new_save=True,
        input_sha256=inputs, original_sha256=originals,
        prepared_sha256={p: hashlib.sha256(v).hexdigest() for p, v in outputs.items()})
    for path, raw in outputs.items():
        (source / path).parent.mkdir(parents=True, exist_ok=True)
        (source / path).write_bytes(raw)
    marker.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source), indent=2))
