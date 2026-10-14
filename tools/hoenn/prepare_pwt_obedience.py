"""Use facility obedience in PWT and badge progress from either campaign."""
import argparse
from pathlib import Path
from candidate_layer import Layer
from prepare_workshop_graphics_rules import PRIOR,LAYER as PREVIOUS
LAYER='pwt-obedience';PRIOR=PRIOR+[PREVIOUS]
def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if old:=layer.existing():return old
    p='src/battle_util.c';text=(layer.source/p).read_text()
    text=text.replace('#include "global.h"','#include "global.h"\n#include "journey_gym_scaling.h"',1)
    start=text.index('enum Obedience GetAttackerObedienceForAction(void)')
    head,body=text[:start],text[start:]
    old='    if (gBattleTypeFlags & BATTLE_TYPE_FRONTIER)\n        return OBEYS;'
    assert body.count(old)==1
    body=body.replace(old,'    if (gBattleTypeFlags & (BATTLE_TYPE_FRONTIER | BATTLE_TYPE_PWT))\n        return OBEYS;')
    begin=body.index('    if (FlagGet(FLAG_BADGE08_GET))')
    end=body.index('    if (B_OBEDIENCE_MECHANICS >= GEN_8',begin)
    body=body[:begin]+'''    // Completing either regional badge case keeps obedience when travelling.
    u32 badges = max(JourneyGymBadgeCount(TRUE), JourneyGymBadgeCount(FALSE));
    if (badges >= 8) return OBEYS;
    obedienceLevel = 10 + badges * 10;

'''+body[end:]
    layer.stage(p,head+body)
    return layer.finish(pwt_obeys_regardless_of_original_met_level=True,obedience_badges=max.__name__,
                        either_region_counts=True,ordinary_campaign_obedience_thresholds_preserved=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    print(prepare(p.parse_args().source)['layer'])
