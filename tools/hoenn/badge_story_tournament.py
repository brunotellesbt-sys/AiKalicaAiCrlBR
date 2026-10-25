"""Install a campaign qualifier without registering or mutating any PWT cup."""
import hashlib
from pathlib import Path
import re


HERE = Path(__file__).resolve().parent
TRAINER_START = 1801
HEROES = ('RED', 'LEAF', 'BRENDAN', 'MAY', 'LUFFY', 'EREN')
# These are six-member end-of-campaign teams, all legal in the Gen 1-4 edition.
# Dynamic levels/evolutions, legal competitive moves, EVs and edition IV rules
# still go through the same battle creation path as the other important rivals.
TEAMS = {
    'RED': ('PIKACHU', 'SNORLAX', 'LAPRAS', 'VENUSAUR', 'BLASTOISE', 'CHARIZARD'),
    'LEAF': ('CLEFABLE', 'NIDOQUEEN', 'ARCANINE', 'EXEGGUTOR', 'BLASTOISE', 'VENUSAUR'),
    'BRENDAN': ('SWAMPERT', 'SCEPTILE', 'METAGROSS', 'SALAMENCE', 'MANECTRIC', 'BLAZIKEN'),
    'MAY': ('LUDICOLO', 'ALTARIA', 'MILOTIC', 'GARDEVOIR', 'SCEPTILE', 'BLAZIKEN'),
    'LUFFY': ('SOLROCK', 'LUDICOLO', 'TOGEKISS', 'MACHAMP', 'SNORLAX', 'EMPOLEON'),
    'EREN': ('SCIZOR', 'TYRANITAR', 'DUSKNOIR', 'GARCHOMP', 'AGGRON', 'REGIGIGAS'),
}
RESOURCES = {
    'badge_qualifier.c': 'src/journey_badge_qualifier.c',
    'badge_qualifier.h': 'include/journey_badge_qualifier.h',
    'qualifier_core.c': 'src/journey_qualifier_core.c',
    'qualifier_core.h': 'include/journey_qualifier_core.h',
}

BATTLE_CALLBACK = '''static void CB2_EndQualifierBattle(void)
{
    // A group loss is scored by the campaign script. It must not white out,
    // mark a story rival defeated or change PWT records before classification.
    JourneyQualifierBattleReturned();
    SetMainCallback2(CB2_ReturnToFieldContinueScriptPlayMapMusic);
}

void BattleSetup_StartQualifierBattle(void)
{
    if (!JourneyQualifierBattleReady()) return;
    JourneyQualifierBattleStarted();
    gMain.savedCallback = CB2_EndQualifierBattle;
    CreateBattleStartTask(GetTrainerBattleTransition(), 0);
    ScriptContext_Stop();
}

'''


def trainer_data():
    rows = []
    for hero in HEROES:
        female = hero in {'LEAF', 'MAY'}
        gender = 'FEMALE' if female else 'MALE'
        picture = ('TRAINER_PIC_JOURNEY_' + hero if hero in {'LUFFY', 'EREN'}
                   else 'TRAINER_PIC_' + hero)
        party = ','.join(
            '{.species=SPECIES_' + species + ',.lvl=' + str(45 + slot)
            + ',.iv=TRAINER_PARTY_IVS(20,20,20,20,20,20)'
            + ',.gender=TRAINER_MON_RANDOM_GENDER,.ball=POKEBALL_COUNT'
            + ',.nature=NATURE_HARDY,.heldItem=ITEM_SITRUS_BERRY}'
            for slot, species in enumerate(TEAMS[hero]))
        rows.append('[DIFFICULTY_NORMAL][TRAINER_JOURNEY_QUALIFIER_' + hero
            + ']={.trainerName=_("' + hero.title() + '")'
            + ',.trainerClass=TRAINER_CLASS_RIVAL,.trainerPic=' + picture
            + ',.gender=TRAINER_GENDER_' + gender
            + ',.encounterMusic=TRAINER_ENCOUNTER_MUSIC_' + gender
            + ',.aiFlags=AI_FLAG_BASIC_TRAINER,.partySize=6'
            + ',.party=(const struct TrainerMon[]){' + party + '}},\n')
    return ''.join(rows)


def repair(layer):
    from badge_story_layer import read

    resource_hashes = {}
    for local, target in RESOURCES.items():
        raw = (HERE / local).read_bytes()
        layer.stage(target, raw)
        resource_hashes[target] = hashlib.sha256(raw).hexdigest()

    path = 'include/constants/opponents.h'
    constants = read(layer, path).decode()
    old = '#define TRAINERS_COUNT                      1801'
    assert constants.count(old) == 1, path
    constants = constants.replace(old, '#define TRAINERS_COUNT                      1807')
    trainers = []
    for offset, hero in enumerate(HEROES):
        name = 'TRAINER_JOURNEY_QUALIFIER_' + hero
        assert name not in constants
        number = TRAINER_START + offset
        constants += '\n#define ' + name + ' ' + str(number) + '\n'
        trainers.append(dict(hero=hero, id=number, team=list(TEAMS[hero])))
    layer.stage(path, constants)

    # Luffy and Eren retain the final teams of their existing story encounters.
    crossover = read(layer, 'src/data/journey_crossover_trainers.h').decode()
    for hero in ('LUFFY', 'EREN'):
        row = re.search(r'\[DIFFICULTY_NORMAL\]\[TRAINER_JOURNEY_' + hero
                        + r'_6\]\s*=\s*(.*?)(?=\n\[|\Z)', crossover, re.S)
        assert row is not None, hero
        assert tuple(re.findall(r'\.species\s*=\s*SPECIES_(\w+)', row[1])) == TEAMS[hero]

    target = 'src/data/journey_qualifier_trainers.h'
    layer.stage(target, trainer_data())
    path = 'src/data.c'
    data = read(layer, path).decode()
    anchor = '#include "data/journey_extra_gym_trainers.h"'
    assert data.count(anchor) == 1, path
    data = data.replace(anchor, anchor + '\n#include "data/journey_qualifier_trainers.h"')
    layer.stage(path, data)

    path = 'src/battle_setup.c'
    battle = read(layer, path).decode()
    assert battle.count('#include "global.h"') == 1, path
    battle = battle.replace('#include "global.h"',
                            '#include "global.h"\n#include "journey_badge_qualifier.h"')
    anchor = 'static void CB2_EndPWTBattle(void)\n'
    assert battle.count(anchor) == 1 and 'CB2_EndQualifierBattle' not in battle, path
    battle = battle.replace(anchor, BATTLE_CALLBACK + anchor)
    layer.stage(path, battle)

    path = 'src/journey_gym_scaling.c'
    scaling = read(layer, path).decode()
    assert scaling.count('#include "global.h"') == 1, path
    scaling = scaling.replace('#include "global.h"',
                              '#include "global.h"\n#include "journey_badge_qualifier.h"')
    anchor = 'u32 JourneyGymLevel(const struct Trainer *trainer, u32 originalLevel)\n{'
    assert scaling.count(anchor) == 1, path
    scaling = scaling.replace(anchor, anchor
        + '\n    if (JourneyQualifierTrainer(trainer))\n'
        + '        return JourneyQualifierTrainerLevel(trainer, originalLevel);')
    layer.stage(path, scaling)
    return dict(trainers=trainers, resources_sha256=resource_hashes,
                two_groups_of_three=True, ordinary_trainer_battles=True,
                group_fixtures=6, finalists=2, final_matches=1,
                independent_pwt_state=True, full_party_snapshots=False,
                restores_held_items_and_health=True,
                preserves_experience_and_spent_bag_items=True,
                participant_important_scaling_only=True)
