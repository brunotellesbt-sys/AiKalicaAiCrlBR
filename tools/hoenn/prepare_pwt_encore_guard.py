"""Fail Encore cleanly when its target has no valid last move."""
import argparse
from pathlib import Path
from candidate_layer import Layer
from prepare_pwt_entrance_wait import PRIOR,LAYER as PREVIOUS
LAYER='pwt-encore-guard';PRIOR=PRIOR+[PREVIOUS]
def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if old:=layer.existing():return old
    p='src/battle_script_commands.c';text=(layer.source/p).read_text()
    start=text.index('static void Cmd_trysetencore(void)\n{')
    end=text.index('\nstatic void Cmd_painsplitdmgcalc',start)
    body=text[start:end]
    anchor='    s32 i;\n'
    assert body.count(anchor)==1
    body=body.replace(anchor,anchor+'''
    // Encore can run before the target's first action (for example Prankster).
    // MOVE_UNAVAILABLE is a sentinel, never an index into gMovesInfo.
    if (gLastMoves[gBattlerTarget] == MOVE_NONE
        || gLastMoves[gBattlerTarget] >= MOVES_COUNT_ALL)
    {
        gBattlescriptCurrInstr = cmd->failInstr;
        return;
    }
''')
    anchor='     || GetMoveEffect(gChosenMoveByBattler[gBattlerTarget]) == EFFECT_SHELL_TRAP)'
    assert body.count(anchor)==1
    body=body.replace(anchor,'     || (gChosenMoveByBattler[gBattlerTarget] < MOVES_COUNT_ALL\n         && GetMoveEffect(gChosenMoveByBattler[gBattlerTarget]) == EFFECT_SHELL_TRAP))')
    layer.stage(p,text[:start]+body+text[end:])
    return layer.finish(encore_without_last_move_fails_normally=True,invalid_move_sentinels_never_indexed=True,
        valid_encore_and_shell_trap_rules_preserved=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    print(prepare(p.parse_args().source)['layer'])
