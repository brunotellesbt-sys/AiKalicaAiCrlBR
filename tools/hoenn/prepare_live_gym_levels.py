"""Use the current party mean for gym opponents, never a fixed badge-level ladder."""
import argparse
from pathlib import Path
from candidate_layer import Layer
from prepare_port_finish import PRIOR,LAYER as PREVIOUS
LAYER='live-gym-levels';PRIOR=PRIOR+[PREVIOUS]
def prepare(source):
 layer=Layer(source,LAYER,PRIOR)
 if r:=layer.existing():return r
 s=layer.source;p='src/journey_gym_scaling.c';t=(s/p).read_text().replace('#include "journey_wild.h"','#include "journey_wild.h"\n#include "random.h"');t=t.replace('static const u8 sAceLevels[] = {14, 21, 28, 35, 42, 48, 54, 60};\n','');start=t.index('u32 JourneyGymLevel(');t=t[:start]+'''u32 JourneyGymLevel(const struct Trainer *trainer, u32 originalLevel)
{
    u32 gym, i, highest = 0, mean = JourneyWildMean();
    for (gym = 0; gym < ARRAY_COUNT(sJourneyGyms); gym++)
        if (gSaveBlock1Ptr->location.mapGroup == MAP_GROUP(sJourneyGyms[gym].map)
            && gSaveBlock1Ptr->location.mapNum == MAP_NUM(sJourneyGyms[gym].map))
            break;
    if (gym == ARRAY_COUNT(sJourneyGyms)
        || (trainer->trainerClass != TRAINER_CLASS_LEADER
            && trainer->trainerClass != TRAINER_CLASS_LEADER_FRLG))
        return JourneyWildLevel();
    for (i = 0; i < (trainer->poolSize ? trainer->poolSize : trainer->partySize); i++)
        if (trainer->party[i].lvl > highest) highest = trainer->party[i].lvl;
    // The adaptive roster uses the original ace's level only as a priority tag.
    // Every final level is calculated once against the player's current party.
    if (originalLevel >= highest) return min(mean + 5, 100);
    return min((mean > 1 ? mean - 1 : 1) + Random() % 6, 100);
}
''';layer.stage(p,t)
 p='src/journey_adaptive_gym.c';t=(s/p).read_text();assert t.count('mons[i].lvl = originalLevel;')==1;layer.stage(p,t.replace('mons[i].lvl = originalLevel;','mons[i].lvl = level;'))
 p='src/battle_main.c';t=(s/p).read_text();needle='    struct TrainerMon adaptiveMons[PARTY_SIZE];';assert t.count(needle)==1;t=t.replace(needle,needle+'\n    bool32 journeyAdaptiveGym = FALSE;');needle='        trainer = &adaptiveTrainer;';assert t.count(needle)==1;t=t.replace(needle,'    {\n        trainer = &adaptiveTrainer;\n        journeyAdaptiveGym = TRUE;\n    }');t=t.replace('u32 journeyLevel = JourneyGymLevel(trainer, competitiveMon.lvl);','u32 journeyLevel = journeyAdaptiveGym ? competitiveMon.lvl : JourneyGymLevel(trainer, competitiveMon.lvl);');layer.stage(p,t)
 return layer.finish(common_trainers_offset=[-5,2],gym_leaders_offset=[-1,5],signature_ace_offset=5,current_party_mean=True,level_computed_once_per_generated_mon=True,regional_party_size_and_evolution_legality_preserved=True,level_cap=100)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);print(prepare(p.parse_args().source)['layer'])
