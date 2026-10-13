"""Complete crossover guidance and keep named characters in one story phase."""
import argparse
import json
import re
from pathlib import Path
from candidate_layer import Layer
from prepare_ecology import weighted_slots, LAND_RATES
from prepare_final_ecology import PRIOR, LAYER as PREVIOUS

LAYER='final-story'; PRIOR=PRIOR+[PREVIOUS]


def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if result:=layer.existing():return result
    source=layer.source
    gen4=json.loads((source/'.journey-final-ecology').read_text())['generation4']
    families={f['name']:f for l in gen4['locations'] for f in l['families']}
    pooltext='static const struct JourneyWildPool sJourneyGeneration4Pools[]={\n'
    for p in gen4['pools']:
        roots=weighted_slots([families[n] for n in p['roots']],LAND_RATES) if p['roots'] else []
        names={f['root']:f['name'] for f in families.values()}
        pooltext+='{'+p['map']+','+str(p['area'])+','+str(len(roots))+',{'+','.join(names[r] for r in roots)+'}},\n'
    layer.stage('include/journey_generation4_pools.h',pooltext+'};\n')
    p='src/journey_crossover.c';text=(source/p).read_text()
    text=text.replace('    if (JourneyGymBadgeCount(TRUE)==8 && JourneyGymBadgeCount(FALSE)==8) return FALSE;\n','')
    # The ship scene requires all prior visits; no blanket badge cutoff can strand them.
    text+='''
bool32 JourneyCrossoverComplete(void) { return (VarGet(JOURNEY_RIVAL_VISITS)&0xFFF)==0xFFF; }
void JourneyCrossoverMissing(void)
{
    static const u8 *const names[]={COMPOUND_STRING("ROUTE 4, KANTO"),COMPOUND_STRING("ROUTE 10, KANTO"),COMPOUND_STRING("ROUTE 17, KANTO"),COMPOUND_STRING("ROUTE 112, HOENN"),COMPOUND_STRING("ROUTE 113, HOENN"),COMPOUND_STRING("PETALBURG WOODS"),COMPOUND_STRING("ROUTE 6, KANTO"),COMPOUND_STRING("ROUTE 13, KANTO"),COMPOUND_STRING("ROUTE 20, KANTO"),COMPOUND_STRING("ROUTE 106, HOENN"),COMPOUND_STRING("ROUTE 108, HOENN"),COMPOUND_STRING("ROUTE 125, HOENN")};
    gSpecialVar_Result=JourneyCrossoverComplete();
    for(u32 i=0;i<12;i++)if(!(VarGet(JOURNEY_RIVAL_VISITS)&(1<<i)))
    {StringCopy(gStringVar1,i<6?COMPOUND_STRING("EREN"):COMPOUND_STRING("LUFFY"));StringCopy(gStringVar2,names[i]);break;}
}
'''
    text=text.replace('#include "global.h"','#include "global.h"\n#include "string_util.h"',1)
    layer.stage(p,text)
    p='include/journey_crossover.h';layer.stage(p,(source/p).read_text().replace('#endif','bool32 JourneyCrossoverComplete(void);\nvoid JourneyCrossoverMissing(void);\n#endif'))
    p='src/journey_galactic.c';text=(source/p).read_text().replace('#include "global.h"','#include "global.h"\n#include "journey_crossover.h"',1)
    text=text.replace(' && VarGet(VAR_JOURNEY_GALACTIC_STATE)>=7',' && JourneyCrossoverComplete() && VarGet(VAR_JOURNEY_GALACTIC_STATE)>=7',1)
    anchor=' const u8 *script=o->script;'
    text=text.replace(anchor,anchor+'''
 if(group!=MAP_GROUP(MAP_JOURNEYGALACTICHALL) || num!=MAP_NUM(MAP_JOURNEYGALACTICHALL))
 {
  extern const u8 JourneySanctuary_483[],JourneySanctuary_484[],JourneySanctuary_487[];
  if((script==JourneySanctuary_483 || script==JourneySanctuary_484 || script==JourneySanctuary_487) && VarGet(VAR_JOURNEY_GALACTIC_STATE)<7)return FALSE;
 }
''',1)
    layer.stage(p,text)
    p='data/scripts/journey_galactic.inc';text=(source/p).read_text()
    needle='\tgoto_if_eq VAR_RESULT, FALSE, JourneyGalactic_TooEarly\n'
    text=text.replace(needle,needle+'\tcallnative JourneyCrossoverMissing\n\tgoto_if_eq VAR_RESULT, FALSE, JourneyGalactic_MissingRivals\n',1)
    text+='''
JourneyGalactic_MissingRivals::
\tmsgbox JourneyGalactic_Text_MissingRivals
\tgoto JourneyGalactic_End
JourneyGalactic_Text_MissingRivals::
\t.string "Before entering, find {STR_VAR_1}\\n"
\t.string "on {STR_VAR_2}.\\p"
\t.string "Finish all six encounters with\\n"
\t.string "each stranded traveler first.$"
'''
    needle='\tmsgbox JourneyGalactic_Text_LeagueDistortion\n'
    text=text.replace(needle,needle+'\tcallnative JourneyCrossoverMissing\n\tcall_if_eq VAR_RESULT, FALSE, JourneyGalactic_LeagueRivals\n',1)
    text+='''
JourneyGalactic_LeagueRivals::
\tmsgbox JourneyGalactic_Text_MissingRivals
\treturn
'''
    layer.stage(p,text)
    p='data/maps/JourneyGalacticHall/map.json';m=json.loads((source/p).read_text())
    for i,o in enumerate(m['object_events'],1):
        if str(o.get('local_id',i))=='8':o['x']=6
        if str(o.get('local_id',i))=='9':o['x']=24
    layer.stage(p,json.dumps(m,indent=2)+'\n')
    p='src/journey_story_continuity.c';text=(source/p).read_text()
    text=text.replace('if(script==Route120_EventScript_Steven)return FlagGet(FLAG_DELIVERED_STEVEN_LETTER);','if(script==Route120_EventScript_Steven)return FlagGet(FLAG_DELIVERED_STEVEN_LETTER) && !FlagGet(FLAG_RECEIVED_DEVON_SCOPE);')
    text=text.replace('&& FlagGet(FLAG_RECEIVED_HM_DIVE);','&& VarGet(VAR_MOSSDEEP_SPACE_CENTER_STATE)<3;')
    decl='extern const u8 GraniteCave_StevensRoom_EventScript_Steven[];\nextern const u8 MossdeepCity_SpaceCenter_2F_EventScript_Steven[];\n'
    text=text.replace('bool32 JourneyStoryObjectVisible',decl+'bool32 JourneyStoryObjectVisible',1)
    text=text.replace('    if(script==AquaHideout', '    if(script==GraniteCave_StevensRoom_EventScript_Steven)return !FlagGet(FLAG_DELIVERED_STEVEN_LETTER);\n    if(script==MossdeepCity_SpaceCenter_2F_EventScript_Steven)return JourneyPendingCampaignEvent(FALSE)==5;\n    if(script==AquaHideout',1)
    layer.stage(p,text)
    return layer.finish(all_twelve_crossover_visits_required=True,visits_possible_after_sixteen_badges=True,missing_route_guidance=True,legends_unique_until_galactic_farewell=True,generation4_weighted_pools=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    print(prepare(p.parse_args().source)['layer'])
