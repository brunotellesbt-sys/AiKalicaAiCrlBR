"""Keep the native camera aligned while both participants enter the stadium."""
import argparse
from pathlib import Path
from candidate_layer import Layer
from prepare_pwt_stadium import PRIOR,LAYER as PREVIOUS
LAYER='pwt-stadium-camera';PRIOR=PRIOR+[PREVIOUS]
def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if old:=layer.existing():return old
    source=layer.source
    p='src/journey_pwt_entrance.c';t=(source/p).read_text()
    line='    TryMoveObjectEventToMapCoords(LOCALID_PLAYER,gSaveBlock1Ptr->location.mapNum,gSaveBlock1Ptr->location.mapGroup,2,6);\n'
    assert t.count(line)==1
    layer.stage(p,t.replace(line,''))
    p='data/scripts/journey_pwt.inc';t=(source/p).read_text()
    anchor='JourneyPWT_NextRound::\n\tfadescreen FADE_TO_BLACK\n'
    assert t.count(anchor)==1
    t=t.replace(anchor,anchor+'\tapplymovement LOCALID_PLAYER, JourneyPWT_PlayerSetupMovement\n\twaitmovement 0\n')
    # Fade back even if an allocation failure prevents the opponent spawning.
    t=t.replace('\tgoto_if_eq VAR_RESULT, FALSE, JourneyPWT_BoardStart\n\tfadescreen FADE_FROM_BLACK',
        '\tfadescreen FADE_FROM_BLACK\n\tgoto_if_eq VAR_RESULT, FALSE, JourneyPWT_BoardStart')
    t+='\nJourneyPWT_PlayerSetupMovement:\n'+'\twalk_left\n'*7+'\tstep_end\n'
    layer.stage(p,t)
    return layer.finish(camera_uses_native_walk_displacement=True,player_ready_position=[9,6],
        player_entry_position=[2,6],opponent_ready_position=[13,6],hidden_setup_then_visible_entrances=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    print(prepare(p.parse_args().source)['layer'])
