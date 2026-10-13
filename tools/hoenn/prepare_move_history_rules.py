"""Keep move-history effects and move selection away from invalid sentinels."""
import argparse
from pathlib import Path
from candidate_layer import Layer
from prepare_pwt_encore_guard import PRIOR,LAYER as PREVIOUS
LAYER='move-history-rules';PRIOR=PRIOR+[PREVIOUS]
def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if old:=layer.existing():return old
    source=layer.source
    p='src/battle_script_commands.c';text=(source/p).read_text()
    def edit(function,old,new):
        nonlocal text
        start=text.index(function+'\n{');end=text.index('\n}',start)+2
        body=text[start:end];assert body.count(old)==1,(function,old)
        text=text[:start]+body.replace(old,new)+text[end:]
    edit('static void Cmd_disablelastusedattack(void)','    s32 i;\n','''    s32 i;
    if (gLastMoves[gBattlerTarget] == MOVE_NONE
        || gLastMoves[gBattlerTarget] >= MOVES_COUNT_ALL)
    {
        gBattlescriptCurrInstr = cmd->failInstr;
        return;
    }
''')
    edit('static void Cmd_mimicattackcopy(void)','gLastMoves[gBattlerTarget] == MOVE_UNAVAILABLE','gLastMoves[gBattlerTarget] >= MOVES_COUNT_ALL')
    edit('static void Cmd_copymovepermanently(void)','&& gLastPrintedMoves[gBattlerTarget] != MOVE_UNAVAILABLE',
        '&& gLastPrintedMoves[gBattlerTarget] != MOVE_NONE\n        && gLastPrintedMoves[gBattlerTarget] < MOVES_COUNT_ALL')
    edit('static void Cmd_tryspiteppreduce(void)','&& gLastMoves[gBattlerTarget] != MOVE_UNAVAILABLE','&& gLastMoves[gBattlerTarget] < MOVES_COUNT_ALL')
    edit('void BS_TryInstruct(void)','move == MOVE_NONE || move == MOVE_UNAVAILABLE','move == MOVE_NONE || move >= MOVES_COUNT_ALL')
    edit('static inline bool32 IsInstructBannedChargingMove(u32 battler)',
        'gChosenActionByBattler[battler] != B_ACTION_USE_MOVE || HasBattlerActedThisTurn(battler)',
        'gChosenActionByBattler[battler] != B_ACTION_USE_MOVE || HasBattlerActedThisTurn(battler)\n        || gChosenMoveByBattler[battler] >= MOVES_COUNT_ALL')
    layer.stage(p,text)
    p='src/battle_move_resolution.c';text=(source/p).read_text()
    start=text.index('static enum Move GetCopycatMove(void)\n{');end=text.index('\n}',start)+2
    body=text[start:end];assert body.count('gLastUsedMove == MOVE_UNAVAILABLE')==1
    text=text[:start]+body.replace('gLastUsedMove == MOVE_UNAVAILABLE','gLastUsedMove >= MOVES_COUNT_ALL')+text[end:]
    start=text.index('static enum Move GetMeFirstMove(void)\n{');end=text.index('\n}',start)+2
    body=text[start:end];assert body.count('if (IsBattleMoveStatus(move)')==1
    text=text[:start]+body.replace('if (IsBattleMoveStatus(move)','if (move == MOVE_NONE || move >= MOVES_COUNT_ALL\n     || IsBattleMoveStatus(move)')+text[end:]
    layer.stage(p,text)
    p='src/battle_util.c';text=(source/p).read_text();start=text.index('u32 CheckMoveLimitations(');end=text.index('\n#define ALL_MOVES_MASK',start)
    body=text[start:end];anchor='        move = gBattleMons[battler].moves[i];\n';assert body.count(anchor)==1
    body=body.replace(anchor,anchor+'''        if (move >= MOVES_COUNT_ALL)
        {
            unusableMoves |= 1u << i;
            continue;
        }
''');layer.stage(p,text[:start]+body+text[end:])
    p='src/battle_ai_main.c';text=(source/p).read_text()
    old='if (IsSpeciesOfType(gBattleMons[battler].species, GetMoveType(playerMove)) && GetMovePower(playerMove != 0))'
    assert text.count(old)==1
    text=text.replace(old,'if (playerMove != MOVE_NONE && playerMove < MOVES_COUNT_ALL\n         && IsSpeciesOfType(gBattleMons[battler].species, GetMoveType(playerMove)) && GetMovePower(playerMove) != 0)')
    old='(gLastMoves[battler] == MOVE_UNAVAILABLE) ? MOVE_NONE : gLastMoves[battler]';assert text.count(old)==1
    layer.stage(p,text.replace(old,'(gLastMoves[battler] >= MOVES_COUNT_ALL) ? MOVE_NONE : gLastMoves[battler]'))
    return layer.finish(disable_without_history_fails=True,sketch_cannot_copy_empty_move=True,
        mimic_spite_copycat_instruct_me_first_invalid_history_guarded=True,
        invalid_slots_are_unusable=True,ai_stab_recording_checks_actual_move_power=True,
        pp_clamping_and_valid_torment_behavior_unchanged=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    print(prepare(p.parse_args().source)['layer'])
