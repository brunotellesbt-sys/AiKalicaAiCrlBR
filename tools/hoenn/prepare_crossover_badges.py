"""Order the regional rival battles and add one late encounter per rival."""
import argparse
import json
import re
from pathlib import Path
import struct

from badge_story_layer import read
from candidate_layer import Layer
from prepare_sootopolis_rescue import read_json, replace
from prepare_titan_story import LAYER as PREVIOUS, PRIOR as PREVIOUS_LAYERS

LAYER = 'crossover-badges'
PRIOR = PREVIOUS_LAYERS + [PREVIOUS]
PROGRESSION = Path(__file__).with_name('data') / LAYER / 'progression.inc'
RIVAL_SOURCE = 'src/journey_crossover.c'
SCRIPTS = 'data/scripts/journey_crossover.inc'
GALACTIC = 'data/scripts/journey_galactic.inc'
TEAMS = 'src/data/journey_crossover_trainers.h'
POKEMON = 'src/pokemon.c'
OUTPUTS = {RIVAL_SOURCE, SCRIPTS, GALACTIC, TEAMS, POKEMON}


def stage_four_rounds(layer):
    teams = read(layer, TEAMS).decode()
    late = PROGRESSION.with_name('late_teams.h').read_text()
    for hero in ('EREN', 'LUFFY'):
        pattern = r'(?ms)^\[DIFFICULTY_NORMAL\]\[TRAINER_JOURNEY_' + hero + r'_(\d)\] = .*?(?=^\[DIFFICULTY_NORMAL\]|\Z)'
        rows = {int(m[1]): m[0] for m in re.finditer(pattern, teams)}
        if set(rows) != set(range(1, 7)):
            raise ValueError(('Incomplete rival roster', hero))
        # The battle script keeps the original rank's defeated flag.
        for rank, donor in ((2, 3), (3, 5)):
            teams = teams.replace(rows[rank], rows[donor].replace(f'_{hero}_{donor}]', f'_{hero}_{rank}]'))
        teams = teams.replace(rows[4], '')
    layer.stage(TEAMS, teams.rstrip() + '\n\n' + late)
    scripts = read(layer, SCRIPTS).decode()
    revised = PROGRESSION.with_name('late_encounters.inc').read_text()
    for label, lines in re.findall(r'(?m)^(JourneyCrossover_Text_\w+)::\n((?:\t\.string .*\n)+)', revised):
        pattern = re.escape(label) + r'::\n(?:\t\.string .*\n)+'
        scripts, count = re.subn(pattern, lambda _: label + '::\n' + lines, scripts)
        if count != 1:
            raise ValueError(('Missing rival dialogue', label))
    layer.stage(SCRIPTS, scripts)
    for old, new in (
        ('Before entering, find {STR_VAR_1}', 'Antes de entrar, procure {STR_VAR_1}'),
        ('on {STR_VAR_2}.', 'em {STR_VAR_2}.'),
        ('Finish all six encounters with', 'Vença quatro batalhas contra'),
        ('each stranded traveler first.', 'cada viajante.'),
    ):
        replace(layer, GALACTIC, old, new)
    replace(layer, POKEMON, 'TRAINER_BATTLE_PARAM.opponentA == TRAINER_JOURNEY_EREN_6 ||',
            'TRAINER_BATTLE_PARAM.opponentA == TRAINER_JOURNEY_EREN_4 || '
            'TRAINER_BATTLE_PARAM.opponentA == TRAINER_JOURNEY_EREN_6 ||')

def check_deck_approach(layer):
    deck = read_json(layer, 'data/maps/AbandonedShip_Deck/map.json')
    entrances = {(warp['x'], warp['y']) for warp in deck['warp_events']
                 if warp['dest_map'] == 'MAP_ROUTE108' and warp['elevation'] == 3}
    if entrances != {(13, 15), (14, 15)}:
        raise ValueError('Unexpected Route 108 entrances on the ship deck')
    layout, = [row for row in read_json(layer, 'data/layouts/layouts.json')['layouts']
               if row['id'] == deck['layout']]
    floor = read(layer, layout['blockdata_filepath'])
    for y in range(11, 15):
        for x in (13, 14):
            word, = struct.unpack_from('<H', floor, 2 * (y * layout['width'] + x))
            if word & 0xFC00 != 0x3000:
                raise ValueError(('Unexpected deck approach tile', x, y, word))


def prepare(source):
    layer = Layer(source, LAYER, PRIOR)
    if previous := layer.existing():
        return previous

    check_deck_approach(layer)
    stage_four_rounds(layer)
    original = read(layer, RIVAL_SOURCE).decode()
    table = original.index('struct JourneyCrossoverLocation {')
    end = original.index('extern const u8 JourneyCrossover_Encounter[];', table)
    layer.stage(RIVAL_SOURCE, original[:table] + PROGRESSION.read_text() + '\n' + original[end:])
    replace(layer, RIVAL_SOURCE, '#include "journey_gym_scaling.h"\n',
            '#include "journey_gym_scaling.h"\n#include "journey_extra_gyms.h"\n')
    encounter = 'bool8 JourneyCrossoverTryEncounter(void)\n'
    replace(layer, RIVAL_SOURCE, encounter,
            PROGRESSION.with_name('deck_approach.inc').read_text() + '\n' + encounter)
    replace(layer, RIVAL_SOURCE,
            '    if (sJourneyCrossoverAttempted && sJourneyAttemptMap == map && sJourneyAttemptX == x && sJourneyAttemptY == y)\n'
            '        return FALSE;\n',
            '    if (sJourneyCrossoverAttempted && sJourneyAttemptMap == map && sJourneyAttemptX == x && sJourneyAttemptY == y)\n'
            '        return FALSE;\n'
            '    u16 visits = VarGet(JOURNEY_RIVAL_VISITS);\n')
    replace(layer, RIVAL_SOURCE, '            || (VarGet(JOURNEY_RIVAL_VISITS) & (1 << i))) continue;\n',
            '            || (entry->map == MAP_ROUTE123 && x >= 40 + MAP_OFFSET)\n'
            '            || !JourneyCrossoverReady(i, visits)) continue;\n')
    replace(layer, RIVAL_SOURCE, '        if (!JourneyApproachFindPath(x, y, &xx, &yy)) return FALSE;\n',
            '        bool8 found = map == MAP_ABANDONED_SHIP_DECK\n'
            '            ? JourneyCrossoverDeckApproach(x, y, &xx, &yy)\n'
            '            : JourneyApproachFindPath(x, y, &xx, &yy);\n'
            '        if (!found) return FALSE;\n')
    contents = read(layer, RIVAL_SOURCE).decode()
    start = contents.index('u32 JourneyCrossoverCount(u32 hero)')
    end = contents.index('#define JOURNEY_PATH_RADIUS', start)
    layer.stage(RIVAL_SOURCE, contents[:start] + """u32 JourneyCrossoverCount(u32 hero)
{
    return JourneyCrossoverWon(hero, VarGet(JOURNEY_RIVAL_VISITS));
}

""" + contents[end:])
    replace(layer, RIVAL_SOURCE, 'u32 hero=index>=6;', 'u32 hero=index>=4;')
    replace(layer, RIVAL_SOURCE, '(1<<(sJourneyCrossoverActive-1))',
            '(1 << sJourneyCrossoverLocations[sJourneyCrossoverActive - 1].visitBit)')
    replace(layer, RIVAL_SOURCE,
            'bool32 JourneyCrossoverComplete(void) { return (VarGet(JOURNEY_RIVAL_VISITS)&0xFFF)==0xFFF; }',
            """bool32 JourneyCrossoverComplete(void)
{
    u16 visits = VarGet(JOURNEY_RIVAL_VISITS);
    return JourneyCrossoverWon(FALSE, visits) >= 4 && JourneyCrossoverWon(TRUE, visits) >= 4;
}""")
    contents = read(layer, RIVAL_SOURCE).decode()
    guide = contents.index('void JourneyCrossoverMissing(void)')
    if not contents[guide:].rstrip().endswith('names[i]);break;}\n}'):
        raise ValueError('Unrecognized Galactic rival guide')
    layer.stage(RIVAL_SOURCE, contents[:guide] + '''void JourneyCrossoverMissing(void)
{
    u16 visits = VarGet(JOURNEY_RIVAL_VISITS);
    u32 next = JourneyCrossoverNext(FALSE, visits);
    u32 luffy = JourneyCrossoverNext(TRUE, visits);
    if (luffy < ARRAY_COUNT(sJourneyCrossoverLocations)
        && (next == ARRAY_COUNT(sJourneyCrossoverLocations)
            || sJourneyCrossoverLocations[luffy].badges < sJourneyCrossoverLocations[next].badges))
        next = luffy;
    gSpecialVar_Result = next == ARRAY_COUNT(sJourneyCrossoverLocations);
    if (gSpecialVar_Result)
        return;

    const struct JourneyCrossoverLocation *entry = &sJourneyCrossoverLocations[next];
    StringCopy(gStringVar1, entry->gfx == OBJ_EVENT_GFX_JOURNEY_EREN
               ? COMPOUND_STRING("EREN") : COMPOUND_STRING("LUFFY"));
    StringCopy(gStringVar2, entry->name);
}
''')
    return layer.finish(total_badges={'Eren': [1, 5, 13, 20], 'Luffy': [2, 7, 11, 15]},
                        visit_bits_preserved=True, route108_site='AbandonedShip_Deck')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('private_source', type=Path)
    print(json.dumps(prepare(parser.parse_args().private_source), indent=2))
