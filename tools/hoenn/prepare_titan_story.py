"""Stage Lugia's rescue and the Titan Cave chapter after Sootopolis."""
import argparse
import json
from pathlib import Path
import struct

from badge_story_layer import read
from candidate_layer import Layer
from prepare_sootopolis_rescue import AREA, LAYER as PREVIOUS, PRIOR as PREVIOUS_LAYERS
from prepare_sootopolis_rescue import OCEAN, actor, read_json, replace, stage_json

LAYER = 'titan-story'
PRIOR = PREVIOUS_LAYERS + [PREVIOUS]
DATA = Path(__file__).parent / 'data/titan-story'


def add_actors(layer, name, rows, expected_tiles):
    path = f'data/maps/{name}/map.json'
    scene = read_json(layer, path)
    layouts = read_json(layer, 'data/layouts/layouts.json')['layouts']
    layout, = [row for row in layouts if row['id'] == scene['layout']]
    words = [word for word, in struct.iter_unpack('<H', read(layer, layout['blockdata_filepath']))]
    occupied = {(event['x'], event['y']) for key in ('object_events', 'warp_events', 'coord_events', 'bg_events')
                for event in scene[key]}
    for graphics, x, y, direction, script, flag in rows:
        if (x, y) in occupied or not (0 <= x < layout['width'] and 0 <= y < layout['height']):
            raise ValueError(('Overlapping story actor', name, x, y))
        word = words[y * layout['width'] + x]
        if word not in expected_tiles:
            raise ValueError(('Unexpected story actor floor', name, x, y, hex(word)))
        event = actor(graphics, x, y, word >> 12, direction, script, flag)
        event['script'] = 'JourneyTitanStory_' + script
        scene['object_events'].append(event)
        occupied.add((x, y))
    stage_json(layer, path, scene)


def prepare(source):
    layer = Layer(source, LAYER, PRIOR)
    if previous := layer.existing():
        return previous

    add_actors(layer, AREA, [
        ('ARTICUNO', 9, 16, 'DOWN', 'Idle', 'FLAG_TEMP_5'),
        ('ZAPDOS', 11, 16, 'DOWN', 'Idle', 'FLAG_TEMP_5'),
        ('MOLTRES', 10, 17, 'DOWN', 'Idle', 'FLAG_TEMP_5'),
    ], {OCEAN})
    add_actors(layer, 'JourneyLegendRoom0385', [
        ('JOURNEY_EREN', 17, 20, 'DOWN', 'WishstarEren', 'FLAG_TEMP_5'),
        ('SPECIES(JIRACHI)', 15, 19, 'DOWN', 'Idle', 'FLAG_TEMP_6'),
    ], {0x0364})
    add_actors(layer, 'JourneySanctuaryTitans', [
        ('JOURNEY_EREN', 14, 16, 'DOWN', 'TitanEren', 'FLAG_TEMP_5'),
        ('SPECIES(REGIROCK)', 6, 6, 'DOWN', 'Regirock', 'FLAG_TEMP_5'),
        ('SPECIES(REGICE)', 15, 15, 'LEFT', 'Regice', 'FLAG_TEMP_5'),
        ('SPECIES(REGISTEEL)', 15, 6, 'DOWN', 'Registeel', 'FLAG_TEMP_5'),
        ('SPECIES(REGIELEKI)', 6, 15, 'RIGHT', 'Regieleki', 'FLAG_TEMP_6'),
        ('SPECIES(REGIDRAGO)', 10, 16, 'UP', 'Regidrago', 'FLAG_TEMP_6'),
        ('SPECIES(REGIGIGAS)', 10, 7, 'DOWN', 'Regigigas', 'FLAG_TEMP_5'),
        ('GROUDON_FRONT', 8, 9, 'DOWN', 'Groudon', 'FLAG_TEMP_7'),
    ], {0x0364})

    for path in ('data/scripts/journey_titan_story.inc', 'include/constants/journey_titan_story.h'):
        layer.stage(path, (DATA / Path(path).name).read_bytes())
    scripts = 'data/event_scripts.s'
    replace(layer, scripts, '#include "constants/vars.h"\n',
            '#include "constants/vars.h"\n#include "constants/journey_titan_story.h"\n')
    anchor = f'\t.include "data/maps/{AREA}/scripts.inc"\n'
    replace(layer, scripts, anchor, anchor + '\t.include "data/scripts/journey_titan_story.inc"\n')
    for path, name, transition in (
        ('data/maps/JourneyLegendRooms.inc', 'JourneyLegendRoom0385', 'WishstarTransition'),
        ('data/maps/JourneySanctuaryTitans/scripts.inc', 'JourneySanctuaryTitans', 'CaveTransition'),
    ):
        start = f'{name}_MapScripts::\n\tmap_script MAP_SCRIPT_ON_TRANSITION, '
        replace(layer, path, start + 'JourneySanctuary_Sync\n', start + f'JourneyTitanStory_{transition}\n')

    rescue = f'data/maps/{AREA}/scripts.inc'
    replace(layer, rescue, '\tsetflag FLAG_TEMP_4\n', '\tsetflag FLAG_TEMP_4\n\tsetflag FLAG_TEMP_5\n')
    replace(layer, rescue, '\tclosemessage\n\tremoveobject 6\n',
            '\tclosemessage\n\tcall JourneyTitanStory_Seabirds\n\tremoveobject 6\n')
    replace(layer, rescue, '\tsetvar VAR_JOURNEY_SOOTOPOLIS_RESCUE, 4\n',
            '\tsetvar VAR_JOURNEY_SOOTOPOLIS_RESCUE, 4\n'
            '\tcall_if_lt VAR_JOURNEY_GALACTIC_STATE, 7, JourneyTitanStory_HarborClue\n')

    # Both the room entrance and Cyrus must check the chain. Old saves can
    # finish the prison once its first boss battle has already been recorded.
    galactic = 'data/scripts/journey_galactic.inc'
    original = read(layer, galactic).decode()
    badge_branch = '\tgoto_if_eq VAR_RESULT, FALSE, JourneyGalactic_TooEarly\n'
    if original.count(badge_branch) != 2:
        raise ValueError('Unexpected Galactic entrance and Cyrus scripts')
    layer.stage(galactic, original.replace(badge_branch, badge_branch + '\tcall JourneyTitanStory_CheckFinale\n'))
    native = 'src/journey_galactic.c'
    replace(layer, native, '#include "constants/maps.h"\n',
            '#include "constants/maps.h"\n#include "constants/journey_titan_story.h"\n'
            '#include "journey_version.h"\n\n'
            'void JourneyTitanStoryExpanded(void)\n{\n'
            '    gSpecialVar_Result = JourneySpeciesAllowed(SPECIES_REGIELEKI);\n}\n\n')
    replace(layer, native, 'return JourneyTotalBadgeCount() >= 22 && state<7;',
            'return JourneyTotalBadgeCount() >= 22 && state < 7\n'
            '      && (state >= 1 || (VarGet(VAR_JOURNEY_SOOTOPOLIS_RESCUE) == 4\n'
            '                         && VarGet(VAR_JOURNEY_TITAN_STORY) == TITAN_STORY_COMPLETE\n'
            '                         && JourneyQualifierWon()));')
    return layer.finish(save_variable='0x409B', rescue_state=4, complete_state=8,
                        needs_qualifier_before_finale=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('private_source', type=Path)
    print(json.dumps(prepare(parser.parse_args().private_source), indent=2))
