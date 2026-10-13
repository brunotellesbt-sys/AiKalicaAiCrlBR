"""Wait for both native entrance movements before opening the tournament board."""
import argparse
from pathlib import Path
from candidate_layer import Layer
from prepare_pwt_stadium_camera import PRIOR,LAYER as PREVIOUS
LAYER='pwt-entrance-wait';PRIOR=PRIOR+[PREVIOUS]
def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if old:=layer.existing():return old
    p='data/scripts/journey_pwt.inc';t=(layer.source/p).read_text()
    setup='\tapplymovement LOCALID_PLAYER, JourneyPWT_PlayerSetupMovement\n\twaitmovement 0'
    entrance='\tapplymovement 14, JourneyPWT_EntranceMovement\n\twaitmovement 0'
    assert t.count(setup)==1 and t.count(entrance)==1
    t=t.replace(setup,setup.replace('waitmovement 0','waitmovement LOCALID_PLAYER'))
    t=t.replace(entrance,entrance.replace('waitmovement 0','waitmovement LOCALID_PLAYER\n\twaitmovement 14'))
    layer.stage(p,t)
    return layer.finish(both_entrances_complete_before_board=True,explicit_player_and_opponent_movement_ids=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    print(prepare(p.parse_args().source)['layer'])
