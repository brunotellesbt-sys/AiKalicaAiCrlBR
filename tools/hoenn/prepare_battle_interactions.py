"""Make AI entry-hazard evaluation honor active Heavy-Duty Boots."""
import argparse
from pathlib import Path
from candidate_layer import Layer
from prepare_move_history_rules import PRIOR,LAYER as PREVIOUS

LAYER='battle-interactions'
PRIOR=PRIOR+[PREVIOUS]

def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if old:=layer.existing():return old
    path='src/battle_ai_switch.c'
    text=(layer.source/path).read_text()
    old='''    if (ability != ABILITY_MAGIC_GUARD || (heldItemEffect == HOLD_EFFECT_HEAVY_DUTY_BOOTS &&
        !((gFieldStatuses & STATUS_FIELD_MAGIC_ROOM) || ability == ABILITY_KLUTZ)))'''
    new='''    // The AI cache already accounts for Magic Room, Embargo and Klutz.
    // Active Boots prevent entry hazards, including Spikes and Toxic Spikes.
    if (ability != ABILITY_MAGIC_GUARD && heldItemEffect != HOLD_EFFECT_HEAVY_DUTY_BOOTS)'''
    assert text.count(old)==1
    layer.stage(path,text.replace(old,new))
    return layer.finish(ai_active_boots_prevent_hazard_damage_estimates=True,
        suppressed_boots_still_allow_hazards=True,magic_guard_behavior_preserved=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    print(prepare(p.parse_args().source)['layer'])
