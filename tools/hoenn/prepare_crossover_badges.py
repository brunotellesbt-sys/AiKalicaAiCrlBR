"""Unlock the existing rival encounters in badge order within each region."""
import argparse
import json
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
    original = read(layer, RIVAL_SOURCE).decode()
    table = original.index('struct JourneyCrossoverLocation {')
    end = original.index('extern const u8 JourneyCrossover_Encounter[];', table)
    layer.stage(RIVAL_SOURCE, original[:table] + PROGRESSION.read_text() + '\n' + original[end:])
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
            '            || !JourneyCrossoverReady(i, visits)) continue;\n')
    replace(layer, RIVAL_SOURCE, '        if (!JourneyApproachFindPath(x, y, &xx, &yy)) return FALSE;\n',
            '        bool8 found = map == MAP_ABANDONED_SHIP_DECK\n'
            '            ? JourneyCrossoverDeckApproach(x, y, &xx, &yy)\n'
            '            : JourneyApproachFindPath(x, y, &xx, &yy);\n'
            '        if (!found) return FALSE;\n')
    contents = read(layer, RIVAL_SOURCE).decode()
    guide = contents.index('void JourneyCrossoverMissing(void)')
    if not contents[guide:].rstrip().endswith('names[i]);break;}\n}'):
        raise ValueError('Unrecognized Galactic rival guide')
    layer.stage(RIVAL_SOURCE, contents[:guide] + '''void JourneyCrossoverMissing(void)
{
    u16 visits = VarGet(JOURNEY_RIVAL_VISITS);
    u32 next = JourneyCrossoverNext(TRUE, visits);
    if (next == ARRAY_COUNT(sJourneyCrossoverLocations))
        next = JourneyCrossoverNext(FALSE, visits);
    gSpecialVar_Result = next == ARRAY_COUNT(sJourneyCrossoverLocations);
    if (gSpecialVar_Result)
        return;

    const struct JourneyCrossoverLocation *entry = &sJourneyCrossoverLocations[next];
    StringCopy(gStringVar1, entry->gfx == OBJ_EVENT_GFX_JOURNEY_EREN
               ? COMPOUND_STRING("EREN") : COMPOUND_STRING("LUFFY"));
    StringCopy(gStringVar2, entry->name);
}
''')
    return layer.finish(regional_milestones=[1, 2, 3, 4, 5, 6], visit_bits_preserved=True,
                        route108_site='AbandonedShip_Deck')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('private_source', type=Path)
    print(json.dumps(prepare(parser.parse_args().private_source), indent=2))
