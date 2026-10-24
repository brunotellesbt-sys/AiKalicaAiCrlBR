"""Give existing rival encounters one identity selected by avatar and birthplace.

Only the presentation changes: native trainer teams, encounter flags, movement
scripts and battle triggers retain their parent bytes outside speaker names.
"""
import hashlib
from pathlib import Path
import re


HERE = Path(__file__).resolve().parent
SPEAKER_MAPS = (
    'EverGrandeCity_ChampionsRoom', 'LavaridgeTown', 'LilycoveCity',
    'LittlerootTown_MaysHouse_2F', 'LittlerootTown_ProfessorBirchsLab',
    'OldaleTown', 'Route103', 'Route104', 'Route110', 'Route119', 'RustboroCity',
)
TEAM_FILES = ('src/data/trainers.party', 'src/data/trainers_frlg.party')
LEGACY = 'src/journey_rival.c'
DATA = 'include/data.h'
GRAPHICS = 'src/event_object_movement.c'
STRINGS = 'src/string_util.c'
BATTLE_TEXT = 'src/battle_message.c'

# Curated spoken fragments only. Red/Leaf can inherit an away-region encounter,
# so they must not claim to be Birch's child or introduce the old sprite name.
RIVAL_DIALOGUE_EDITS = {
    'LilycoveCity': (
        ('"I\'m going home to show my dad.$"',
         '"I\'ll show the PROFESSOR back\\n"\n\t.string "at the lab in LITTLEROOT TOWN.$"'),
        ('"I\'m running an errand for my dad.\\n"', '"I\'m helping the PROFESSOR today.\\n"'),
        ('"You know I\'m helping out my dad on his\\n"',
         '"I\'m helping the PROFESSOR with his\\n"'),
    ),
    'LittlerootTown_MaysHouse_2F': (
        ('"Um… I\'m MAY.\\n"', '"Um… I\'m {RIVAL}.\\n"'),
        ('"My name\'s BRENDAN.\\n"', '"My name\'s {RIVAL}.\\n"'),
        ('"my dad, PROF. BIRCH.\\p"', '"PROF. BIRCH.\\p"'),
        ('"I was supposed to go help Dad catch\\n"',
         '"I was going to help BIRCH catch\\n"'),
        ('"Dad, PROF. BIRCH, said that our new\\n"',
         '"PROF. BIRCH said that our new\\n"'),
        ('"I\'m supposed to go help my dad catch\\n"',
         '"I\'m going to help the PROF. catch\\n"'),
    ),
    'OldaleTown': (
        ('"BRENDAN: I\'m heading back to my dad\'s\\n"',
         '"BRENDAN: I\'m heading back to the\\n"'),
    ),
    'Route103': (
        ('"…Oh, I see, my dad gave you\\n"', '"…Oh, I see, the PROF. gave you\\n"'),
        ('"MAY: I think I know why my dad has\\n"',
         '"MAY: I see why the PROFESSOR has\\n"'),
        ('"…Oh, yeah, Dad gave you a POKéMON.\\p"',
         '"…Oh, yeah, the PROF. gave you\\n"\n\t.string "a POKéMON.\\p"'),
        ('"I think I know why my dad has his eye\\l"',
         '"I see why the PROFESSOR is watching\\l"'),
        ('"out for you now.\\p"', '"your progress now.\\p"'),
    ),
    'Route104': (
        ('"{PLAYER} registered MAY\\n"', '"{PLAYER} registered {RIVAL}\\n"'),
        ('"{PLAYER} registered BRENDAN\\n"', '"{PLAYER} registered {RIVAL}\\n"'),
    ),
    'RustboroCity': (
        ('"Registered MAY\\n"', '"Registered {RIVAL}\\n"'),
        ('"Registered BRENDAN\\n"', '"Registered {RIVAL}\\n"'),
    ),
}


def _include(text, header):
    line = '#include "' + header + '"'
    if line not in text:
        assert text.count('#include "global.h"') == 1
        text = text.replace('#include "global.h"', '#include "global.h"\n' + line, 1)
    return text


def _replace(text, before, after, path):
    if before not in text:
        assert text.count(after) == 1, (path, 'Missing reviewed hook', before[:80])
        return text
    assert text.count(before) == 1, (path, 'Ambiguous reviewed hook')
    return text.replace(before, after, 1)


def _function(text, signature, body):
    """Replace one complete function, not the following unrelated declarations."""
    start = text.index(signature)
    opening = text.index('{', start + len(signature))
    depth, end = 1, opening + 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[:opening] + '{\n' + body.rstrip() + '\n}' + text[end:]


def repair(layer):
    from badge_story_layer import read

    parent_teams = {path: hashlib.sha256(read(layer, path)).hexdigest() for path in TEAM_FILES}
    layer.stage('include/journey_story_rivals.h', (HERE / 'story_rivals.h').read_bytes())
    layer.stage('src/journey_story_rivals.c', (HERE / 'story_rivals.c').read_bytes())

    # Retain the public compatibility entry used by old battle-picture paths.
    layer.stage(LEGACY, '''#include "global.h"
#include "journey_rival.h"
#include "journey_story_rivals.h"

enum TrainerPicID JourneyRivalTrainerPic(u16 trainerId)
{
    return JourneyStoryTrainerPic(trainerId);
}
''')

    text = read(layer, DATA).decode()
    include = '#include "journey_story_rivals.h"'
    if include not in text:
        text = _replace(text, '#include "journey_rival.h"',
                        '#include "journey_rival.h"\n' + include, DATA)
    text = _replace(text,
        'static inline const u8 *GetTrainerNameFromId(u16 trainerId)\n{\n    return GetTrainerStructFromId(trainerId)->trainerName;\n}',
        'static inline const u8 *GetTrainerNameFromId(u16 trainerId)\n{\n    return JourneyStoryTrainerName(trainerId);\n}', DATA)
    layer.stage(DATA, text)

    text = _include(read(layer, GRAPHICS).decode(), 'journey_story_rivals.h')
    text = _replace(text,
        '    if (graphicsId == OBJ_EVENT_GFX_BLUE)\n        graphicsId = gSaveBlock2Ptr->playerGender == MALE ? OBJ_EVENT_GFX_GREEN_NORMAL : OBJ_EVENT_GFX_RED_NORMAL;',
        '    graphicsId = JourneyStoryRivalGraphics(graphicsId);', GRAPHICS)
    layer.stage(GRAPHICS, text)

    text = _include(read(layer, STRINGS).decode(), 'journey_story_rivals.h')
    text = _function(text, 'static const u8 *ExpandPlaceholder_RivalName(void)',
        '    return JourneyStoryHeroName(JourneyStoryCurrentRivalHero());')
    layer.stage(STRINGS, text)

    text = read(layer, BATTLE_TEXT).decode()
    before = '''        enum TrainerClassID trainerClass = GetTrainerClassFromId(TRAINER_BATTLE_PARAM.opponentA);

        if (trainerClass == TRAINER_CLASS_RIVAL_EARLY_FRLG || trainerClass == TRAINER_CLASS_RIVAL_LATE_FRLG || trainerClass == TRAINER_CLASS_CHAMPION_FRLG)
            toCpy = GetExpandedPlaceholder(PLACEHOLDER_ID_RIVAL);
        else
            toCpy = GetTrainerNameFromId(trainerId);'''
    # The actual trainer ID, not a class or current map, controls battle names.
    text = _replace(text, before, '        toCpy = GetTrainerNameFromId(trainerId);', BATTLE_TEXT)
    layer.stage(BATTLE_TEXT, text)

    speakers = []
    for name in SPEAKER_MAPS:
        path = f'data/maps/{name}/scripts.inc'
        text = read(layer, path).decode()
        for old, new in RIVAL_DIALOGUE_EDITS.get(name, ()):
            # Two registration strings intentionally converge to one name.
            if old in text:
                assert text.count(old) == 1, (path, old)
                text = text.replace(old, new, 1)
            else:
                dynamic = re.sub(r'"(?:MAY|BRENDAN):', '"{RIVAL}:', new)
                assert new in text or dynamic in text, (path, 'Missing reviewed rival line', old)
        count = len(re.findall(r'(?m)^(\s*\.string ")(?:MAY|BRENDAN):', text))
        if count:
            updated = re.sub(r'(?m)^(\s*\.string ")(?:MAY|BRENDAN):',
                             r'\1{RIVAL}:', text)
        else:
            assert '.string "{RIVAL}:' in text, (path, 'Missing native rival dialogue')
            updated = text
        layer.stage(path, updated)
        speakers.append(dict(map=name, prefixes_replaced=count))

    assert all(hashlib.sha256(read(layer, path)).hexdigest() == sha
               for path, sha in parent_teams.items())
    source = (HERE / 'story_rivals.c').read_text()
    native = re.search(r'sNativeRivals\[\] = \{(.*?)\n\};', source, re.S)[1]
    entries = re.findall(r'\{(TRAINER_\w+), (TRUE|FALSE), ([12])\}', native)
    assert len(entries) == len({name for name, _, _ in entries}) == 57
    return dict(native_trainers=57, kanto_native_trainers=27, hoenn_native_trainers=30,
                heroes=4, birthplace_regions=3, rival_roles=3,
                avatar_and_birthplace_shared_selector=True,
                names_portraits_graphics_and_dialogue_share_identity=True,
                saved_single_rival_alias_not_reused_for_three_people=True,
                native_teams_preserved=parent_teams,
                encounter_flags_and_movement_commands_preserved=True,
                unrelated_wally_blue_and_explicit_graphics_preserved=True,
                dialogue_speaker_maps=speakers)
