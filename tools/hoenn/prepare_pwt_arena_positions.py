"""Place the PWT opponent on the stadium's right-hand entrance lane."""
import argparse
from pathlib import Path

from candidate_layer import Layer
from prepare_sootopolis_rescue import replace
from prepare_crossover_badges import LAYER as PREVIOUS, PRIOR as PARENT_LAYERS

LAYER = 'pwt-arena-positions'
PRIOR = [*PARENT_LAYERS, PREVIOUS]
ENTRANCE = 'src/journey_pwt_entrance.c'
SCRIPT = 'data/scripts/journey_pwt.inc'


def prepare(source):
    layer = Layer(source, LAYER, PRIOR)
    if previous := layer.existing():
        return previous
    text = (layer.source / ENTRANCE).read_text()
    old = 'MOVEMENT_TYPE_FACE_LEFT,14,17,6,0)'
    if text.count(old) != 1 or text.count('#include "event_data.h"') != 1:
        raise ValueError('Unexpected native PWT entrance')
    text = text.replace('#include "event_data.h"', '#include "event_data.h"\n#include "fieldmap.h"')
    text = text.replace(old, 'MOVEMENT_TYPE_FACE_LEFT, 14, 17 + MAP_OFFSET, 6 + MAP_OFFSET, 0)')
    layer.stage(ENTRANCE, text)
    spawn = '\tspecial JourneyPWTEntrance\n'
    fade = '\tfadescreen FADE_FROM_BLACK\n'
    check_spawn = '\tgoto_if_eq VAR_RESULT, FALSE, JourneyPWT_BoardStart\n'
    player_walk = '\tapplymovement LOCALID_PLAYER, JourneyPWT_PlayerEntranceMovement\n'
    opponent_walk = '\tapplymovement 14, JourneyPWT_EntranceMovement\n'
    wait_player = '\twaitmovement LOCALID_PLAYER\n'
    wait_opponent = '\twaitmovement 14\n'
    # At (9, 6) the native camera can keep a trainer at (17, 6) loaded.
    replace(layer, SCRIPT,
            spawn + fade + check_spawn + player_walk + opponent_walk + wait_player + wait_opponent,
            fade + player_walk + wait_player + spawn + check_spawn + opponent_walk + wait_opponent)
    return layer.finish(opponent_start=[17, 6], opponent_ready=[13, 6], player_ready=[9, 6])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    prepare(parser.parse_args().source)
