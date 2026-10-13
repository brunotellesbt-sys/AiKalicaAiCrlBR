"""Limit the Gen 1–4 Dex and gifts without resizing persistent save arrays."""
import argparse
from pathlib import Path
from candidate_layer import Layer
from prepare_badge_case import PRIOR,LAYER as PREVIOUS

LAYER='variant-dex';PRIOR=PRIOR+[PREVIOUS]


def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if result:=layer.existing():return result
    source=layer.source
    p='src/pokedex.c';text=(source/p).read_text().replace('#include "global.h"','#include "global.h"\n#include "journey_version.h"',1)
    text=text.replace('temp_dexCount = NATIONAL_DEX_COUNT;', 'temp_dexCount = gJourneyBuildRules.maxNational;')
    text=text.replace('temp_dexNum <= NATIONAL_DEX_COUNT', 'temp_dexNum <= gJourneyBuildRules.maxNational')
    # Keep allocation/blanking bounds fixed; only species enumeration changes.
    text=text.replace('for (i = 0; i < NATIONAL_DEX_COUNT; i++)','for (i = 0; i < gJourneyBuildRules.maxNational; i++)')
    text=text.replace('for (i = 1; i < NATIONAL_DEX_COUNT + 1; i++)','for (i = 1; i <= gJourneyBuildRules.maxNational; i++)')
    text=text.replace('for (i = 0, resultsCount = 0; i < NATIONAL_DEX_COUNT; i++)','for (i = 0, resultsCount = 0; i < gJourneyBuildRules.maxNational; i++)')
    text=text.replace('NATIONAL_DEX_COUNT > 999', 'gJourneyBuildRules.maxNational > 999')
    anchor='    nationalDexNo--;'
    assert text.count(anchor)==1
    text=text.replace(anchor,'    if(nationalDexNo==0 || nationalDexNo>gJourneyBuildRules.maxNational)return 0;\n'+anchor)
    layer.stage(p,text)
    p='src/script_pokemon_util.c';text=(source/p).read_text().replace('#include "global.h"','#include "global.h"\n#include "journey_version.h"',1)
    anchor='u32 ScriptGiveMon(enum Species species, u8 level, enum Item item)\n{'
    assert anchor in text
    text=text.replace(anchor,anchor+'\n    if(!JourneySpeciesAllowed(species))return MON_CANT_GIVE;')
    layer.stage(p,text)
    return layer.finish(national_dex_limit_per_variant=True,gifts_respect_generation=True,save_arrays_unchanged=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    print(prepare(p.parse_args().source)['layer'])
