"""Make the Dex and aquatic encounters follow the actual variant habitats."""
import argparse
import copy
import json
import re
from pathlib import Path
from candidate_layer import Layer
from allocate_generation4 import allocate
from refresh_ecology import compile_tables
from aquatic_species import NAMES
from world_dex_locations import compile_locations
from prepare_battle_rule_coherence import PRIOR, LAYER as PREVIOUS

LAYER = 'final-ecology'
PRIOR = PRIOR + [PREVIOUS]


def prepare(source):
    layer = Layer(source, LAYER, PRIOR)
    if result := layer.existing():
        return result
    source = layer.source
    locations = copy.deepcopy(json.loads((source / '.journey-paradox-caves').read_text())['ecology']['locations_data'])
    # A penguin belongs at the tidal cave; move its former cave family inland.
    a = next(l for l in locations if l['section'] == 'MAPSEC_NEW_MAUVILLE')
    b = next(l for l in locations if l['section'] == 'MAPSEC_SHOAL_CAVE')
    penguin = next(f for f in a['families'] if f['root'] == 875)
    inland = next(f for f in b['families'] if f['root'] == 561)
    a['families'].remove(penguin); b['families'].remove(inland)
    a['families'].append(inland); b['families'].append(penguin)
    outputs, ecology = compile_tables(source, locations)
    for name, raw in outputs.items():
        layer.stage(name, raw)
    gen4 = allocate(source)
    pools = 'static const struct JourneyWildPool sJourneyGeneration4Pools[]={\n' + ''.join(
        '{' + p['map'] + ',' + str(p['area']) + ',' + str(len(p['roots'])) + ',{' + ','.join(p['roots']) + '}},\n'
        for p in gen4['pools']) + '};\n'
    layer.stage('include/journey_generation4_pools.h', pools)
    habitats = 'static const struct JourneyHabitat sJourneyGeneration4Habitats[]={\n' + ''.join(
        '{' + h['map'] + ',' + str(len(h['species'])) + ',{' + ','.join(h['species']) + '}},\n'
        for h in gen4['habitats']) + '};\n'
    max_members = max(len(h['species']) for h in gen4['habitats'])
    h9 = outputs['include/journey_habitat_data.h'].decode()
    size = int(re.search(r'species\[(\d+)\]', h9)[1])
    h9 = h9.replace(f'species[{size}]', f'species[{max(size,max_members)}]')
    layer.stage('include/journey_habitat_data.h', h9)
    layer.stage('include/journey_generation4_habitats.h', habitats)
    dex, dexmeta = compile_locations(source, {4: habitats, 9: h9})
    layer.stage('src/data/journey_world_dex_locations.h', dex)
    p = 'src/journey_world_dex.c'
    text = (source / p).read_text().replace('#include "global.h"', '#include "global.h"\n#include "journey_version.h"', 1)
    anchor = '#define WORLD_DEX_TAG'
    helper = '''static bool32 LocationAvailable(const struct JourneyWorldDexLocation *p,u16 species)
{
    return p->species==species && JourneySpeciesAllowed(species)
        && (!p->cap || p->cap==(gJourneyBuildRules.maxNational==493?4:9))
        && (p->fixed || JourneyHabitatHasSpecies(MAP_GROUP(p->map),MAP_NUM(p->map),species));
}
'''
    text = text.replace(anchor, helper + anchor, 1)
    start = text.index('            if(sWorldDexLocations[i].species==')
    end = text.index('\n            {', start)
    text = text[:start] + '            if(LocationAvailable(&sWorldDexLocations[i],sWorldDex->species) && sWorldDex->count<ARRAY_COUNT(sWorldDex->sprites))' + text[end:]
    text = text.replace('if(sWorldDexLocations[i].species==species)count++;', 'if(LocationAvailable(&sWorldDexLocations[i],species))count++;')
    layer.stage(p, text)
    p = 'src/journey_wild.c'
    text = (source / p).read_text()
    start = text.index('u32 JourneyWildSpecies('); end = text.index('u32 JourneyFishingOdds', start)
    text = text[:start] + '''bool32 JourneyAquaticSpecies(u32 species)
{
    if(gSpeciesInfo[species].types[0]==TYPE_WATER || gSpeciesInfo[species].types[1]==TYPE_WATER)return TRUE;
    switch(species){
''' + ''.join('    case '+name+':\n' for name in NAMES) + '''        return TRUE;
    default:return FALSE;}
}
u32 JourneyWildSpecies(u32 original,u32 area)
{
    const struct JourneyWildPool *pools=gJourneyBuildRules.maxNational==493?sJourneyGeneration4Pools:sJourneyWildPools;
    u32 length=gJourneyBuildRules.maxNational==493?ARRAY_COUNT(sJourneyGeneration4Pools):ARRAY_COUNT(sJourneyWildPools);
    u32 selected=original,phase=JourneyWildPhase(),stage;
    bool32 water=area==1 || area==3;
    for(u32 k=0;k<length;k++)
    {
        const struct JourneyWildPool *p=&pools[k];
        if(MAP_GROUP(p->map)!=gSaveBlock1Ptr->location.mapGroup || MAP_NUM(p->map)!=gSaveBlock1Ptr->location.mapNum || p->area!=area)continue;
        if(!p->count)return SPECIES_NONE;
        selected=p->species[Random()%p->count];
        break;
    }
    if(selected==SPECIES_NONE || selected>=ARRAY_COUNT(sJourneyWildStages))return SPECIES_NONE;
    const struct JourneyWildStages *family=&sJourneyWildStages[selected];
    stage=phase==0?0:phase==1?Random()%2:1+Random()%2;
    for(u32 attempt=0;attempt<3;attempt++)
    {
        u16 eligible[8];u32 count=0;
        for(u32 i=0;i<family->count[stage];i++)
        {
            u16 species=family->stages[stage][i];
            if(JourneySpeciesAllowed(species) && (!water || JourneyAquaticSpecies(species)))eligible[count++]=species;
        }
        if(count)return eligible[Random()%count];
        stage=stage?stage-1:0;
    }
    return SPECIES_NONE;
}

''' + text[end:]
    # Both variants have actual pools; absent water habitats never fall back to land.
    start = text.index('bool32 JourneyWildPoolAvailable')
    text = text[:start] + '''bool32 JourneyWildPoolAvailable(u32 area)
{
    const struct JourneyWildPool *pools=gJourneyBuildRules.maxNational==493?sJourneyGeneration4Pools:sJourneyWildPools;
    u32 length=gJourneyBuildRules.maxNational==493?ARRAY_COUNT(sJourneyGeneration4Pools):ARRAY_COUNT(sJourneyWildPools);
    for(u32 i=0;i<length;i++)
        if(MAP_GROUP(pools[i].map)==gSaveBlock1Ptr->location.mapGroup && MAP_NUM(pools[i].map)==gSaveBlock1Ptr->location.mapNum && pools[i].area==area)return pools[i].count>0;
    return FALSE;
}
'''
    layer.stage(p,text)
    p='include/journey_wild.h'
    layer.stage(p,(source/p).read_text().replace('#endif','bool32 JourneyAquaticSpecies(u32);\n#endif'))
    return layer.finish(generation4=gen4,ecology=ecology,dex=dexmeta,water_never_returns_terrestrial_species=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True)
    result=prepare(parser.parse_args().source);print(result['layer'],result['dex'])
