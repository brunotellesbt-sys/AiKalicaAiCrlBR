"""Retain true rare encounter weights and open the player's home badge tab."""
import argparse
from pathlib import Path
from candidate_layer import Layer
from prepare_galactic_prison import PRIOR,LAYER as PREVIOUS
LAYER='final-balance';PRIOR=PRIOR+[PREVIOUS]


def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if result:=layer.existing():return result
    source=layer.source
    p='src/journey_wild.c';text=(source/p).read_text()
    text=text.replace('        selected=p->species[Random()%p->count];','''        static const u8 rates[]={20,20,10,10,10,10,5,5,4,4,1,1};
        if(p->count==ARRAY_COUNT(rates))
        {
            u32 roll=Random()%100;
            for(u32 j=0;j<p->count;j++)
            {
                if(roll<rates[j]){selected=p->species[j];break;}
                roll-=rates[j];
            }
        }
        else selected=p->species[Random()%p->count];''')
    layer.stage(p,text)
    p='src/trainer_card.c';text=(source/p).read_text()
    anchor='void ShowPlayerTrainerCard(void (*callback)(void))\n{\n    sData = AllocZeroed(sizeof(*sData));'
    assert anchor in text
    text=text.replace(anchor,anchor+'\n    sData->unused_E=gSaveBlock2Ptr->playerRegion==REGION_KANTO;')
    text=text.replace('#include "global.h"','#include "global.h"\n#include "constants/regions.h"',1)
    layer.stage(p,text)
    return layer.finish(wild_slot_percentages=[20,20,10,10,10,10,5,5,4,4,1,1],badge_case_defaults_to_birth_region=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    print(prepare(p.parse_args().source)['layer'])
