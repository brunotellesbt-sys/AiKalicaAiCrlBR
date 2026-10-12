"""Supply all evolution items and ZA Mega Stones, with practical regional training."""
import argparse
import json
import re
from pathlib import Path
from candidate_layer import Layer
from prepare_final_story import PRIOR,LAYER as PREVIOUS

LAYER='evolution-supplies';PRIOR=PRIOR+[PREVIOUS]
CENTERS=['PewterCity_PokemonCenter_1F','CeruleanCity_PokemonCenter_1F','CeladonCity_PokemonCenter_1F','FuchsiaCity_PokemonCenter_1F','VermilionCity_PokemonCenter_1F','SlateportCity_PokemonCenter_1F','MauvilleCity_PokemonCenter_1F','LilycoveCity_PokemonCenter_1F','MossdeepCity_PokemonCenter_1F','PacifidlogTown_PokemonCenter_1F']


def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if result:=layer.existing():return result
    source=layer.source
    centers=[n if (source/f'data/maps/{n}/map.json').exists() else n.replace('_PokemonCenter_1F','_PokemonCenter_1F_Frlg') for n in CENTERS]
    speciesdir=source/'src/data/pokemon/species_info'
    conversions=[]
    for file in sorted(speciesdir.glob('*.h')):
        text=file.read_text();before=text
        for target,level in [('SPECIES_PAWMOT',36),('SPECIES_BRAMBLEGHAST',30),('SPECIES_RABSCA',30)]:
            pattern=r'\{EVO_LEVEL,\s*0,\s*'+target+r',\s*CONDITIONS\(\{IF_MIN_OVERWORLD_STEPS,\s*1000\}\)\}'
            text,count=re.subn(pattern,'{EVO_LEVEL, '+str(level)+', '+target+'}',text)
            if count:conversions.append(dict(target=target,level=level,former='following_steps'))
        text,count=re.subn(r'\{EVO_SCRIPT_TRIGGER,\s*EVO_TRIGGER_TABLET_CURSE,\s*SPECIES_RUNERIGUS,\s*CONDITIONS\(\{IF_CURRENT_DAMAGE_GE,\s*49\}\)\}','{EVO_LEVEL, 34, SPECIES_RUNERIGUS}',text)
        if count:conversions.append(dict(target='SPECIES_RUNERIGUS',level=34,former='script_trigger'))
        text=text.replace('{EVO_SCRIPT_TRIGGER, EVO_TRIGGER_DARK_SCROLL, SPECIES_URSHIFU_SINGLE_STRIKE}', '{EVO_LEVEL, 36, SPECIES_URSHIFU_SINGLE_STRIKE}')
        # Place the water branch first; a held Mystic Water selects it explicitly.
        text=text.replace('{EVO_LEVEL, 36, SPECIES_URSHIFU_SINGLE_STRIKE},\n                                {EVO_SCRIPT_TRIGGER, EVO_TRIGGER_WATER_SCROLL, SPECIES_URSHIFU_RAPID_STRIKE}', '{EVO_LEVEL, 36, SPECIES_URSHIFU_RAPID_STRIKE, CONDITIONS({IF_HOLD_ITEM, ITEM_MYSTIC_WATER})},\n                                {EVO_LEVEL, 36, SPECIES_URSHIFU_SINGLE_STRIKE}')
        if text!=before:layer.stage(str(file.relative_to(source)),text)
    form=(source/'src/data/pokemon/form_change_tables.h').read_text()
    megas=sorted(set(re.findall(r'\{FORM_CHANGE_BATTLE_MEGA_EVOLUTION_ITEM,\s*(SPECIES_\w+),\s*(ITEM_\w+)',form)))
    mega_items=sorted({item for species,item in megas})
    speciestext='\n'.join(layer.outputs.get(str(f.relative_to(source)),f.read_bytes()).decode() for f in sorted(speciesdir.glob('*.h')))
    evo_items=set(re.findall(r'\{EVO_ITEM,\s*(ITEM_\w+)',speciestext))
    evo_items.update(re.findall(r'\{IF_HOLD_ITEM,\s*(ITEM_\w+)',speciestext))
    # Origin items are earned exclusively from the Galactic finale.
    excluded={'ITEM_ADAMANT_CRYSTAL','ITEM_LUSTROUS_GLOBE','ITEM_GRISEOUS_CORE','ITEM_NONE'}
    evo_items=sorted(evo_items-excluded-set(mega_items))
    stocks=[[] for _ in centers]
    for i,item in enumerate(mega_items):stocks[i%len(stocks)].append(item)
    for i,item in enumerate(evo_items):stocks[i%len(stocks)].append(item)
    scripts=''
    inventory=[]
    for i,name in enumerate(centers):
        p=f'data/maps/{name}/map.json';m=json.loads((source/p).read_text())
        occupied={(o['x'],o['y']) for o in m['object_events']}
        x,y=next(pos for pos in [(4,5),(5,5),(10,5),(2,5)] if pos not in occupied)
        m['object_events'].append(dict(local_id='LOCALID_JOURNEY_SUPPLIES_'+name.upper(),graphics_id='OBJ_EVENT_GFX_SCIENTIST_1',x=x,y=y,elevation=3,movement_type='MOVEMENT_TYPE_FACE_DOWN',movement_range_x=0,movement_range_y=0,trainer_type='TRAINER_TYPE_NONE',trainer_sight_or_berry_tree_id='0',script=f'JourneySupplies_{i}',flag='0'))
        layer.stage(p,json.dumps(m,indent=2)+'\n')
        scripts+=f'''JourneySupplies_{i}::
\tlock
\tfaceplayer
\tcallnative JourneySuppliesRing
\tgoto_if_eq VAR_RESULT, 1, JourneySupplies_RingGiven_{i}
JourneySupplies_Open_{i}::
\tmsgbox JourneySupplies_Text
\tpokemart JourneySupplies_Stock_{i}
\tmsgbox JourneySupplies_After
\treleaseall
\tend
JourneySupplies_RingGiven_{i}::
\tmsgbox JourneySupplies_RingText
\tgoto JourneySupplies_Open_{i}
\t.align 2
JourneySupplies_Stock_{i}:
'''+''.join('\t.2byte '+item+'\n' for item in stocks[i])+'\t.2byte ITEM_NONE\n'
        inventory.append(dict(map=name,position=[x,y],items=stocks[i]))
    scripts+='''JourneySupplies_Text::
\t.string "I stock evolution supplies and\\nMega Stones from our expeditions.$"
JourneySupplies_After::
\t.string "A MEGA RING is awarded after\\ntwo badges across both regions.\\pHold the matching Mega Stone, then\\npress START before choosing a move.\\pRAYQUAZA needs DRAGON ASCENT.\\nVisit our regional tutor for help.$"
JourneySupplies_RingText::
\t.string "Your progress earned a MEGA RING!\\nIt is now in your bag.$"
JourneyRegionalTutor::
\tlock
\tfaceplayer
\tmsgbox JourneyRegionalTutor_Text
\tmultichoice 0, 0, MULTI_JOURNEY_EVOLUTION_REGION, FALSE
\tgoto_if_eq VAR_RESULT, MULTI_B_PRESSED, JourneyRegionalTutor_End
\tsetvar VAR_UNUSED_0x404E, VAR_RESULT
\tcallnative JourneyRegionalTutorApply
\tmsgbox JourneyRegionalTutor_Done
\tmsgbox JourneyRegionalTutor_Ascent, MSGBOX_YESNO
\tgoto_if_eq VAR_RESULT, NO, JourneyRegionalTutor_End
\tcallnative JourneyRegionalTutorAscent
\tgoto_if_eq VAR_RESULT, FALSE, JourneyRegionalTutor_NoRay
\tmsgbox JourneyRegionalTutor_AscentDone
JourneyRegionalTutor_End::
\treleaseall
\tend
JourneyRegionalTutor_NoRay::
\tmsgbox JourneyRegionalTutor_NoRayText
\tgoto JourneyRegionalTutor_End
JourneyRegionalTutor_Text::
\t.string "Choose the regional conditions\\nused by your Pokemon's evolutions.\\pThis affects regional branches,\\nnot your location or journey.$"
JourneyRegionalTutor_Done::
\t.string "Your evolution training is set.\\nChange it here whenever you like.$"
JourneyRegionalTutor_Ascent::
\t.string "Teach DRAGON ASCENT to RAYQUAZA?\\nAn empty move slot is used first.\\pIf all four slots are filled,\\nits fourth move will be replaced.$"
JourneyRegionalTutor_AscentDone::
\t.string "RAYQUAZA learned DRAGON ASCENT!$"
JourneyRegionalTutor_NoRayText::
\t.string "Bring RAYQUAZA in your party\\nif you want this training.$"
'''
    # Existing save variable 404E is unused in both regional campaigns.
    for name in ['PalletTown_ProfessorOaksLab_Frlg','LittlerootTown_ProfessorBirchsLab']:
        p=f'data/maps/{name}/map.json';m=json.loads((source/p).read_text());occupied={(o['x'],o['y']) for o in m['object_events']}
        x,y=next(pos for pos in [(3,5),(4,5),(3,6),(4,6)] if pos not in occupied)
        m['object_events'].append(dict(local_id='LOCALID_JOURNEY_REGIONAL_'+name.upper(),graphics_id='OBJ_EVENT_GFX_SCIENTIST_1',x=x,y=y,elevation=3,movement_type='MOVEMENT_TYPE_FACE_DOWN',movement_range_x=0,movement_range_y=0,trainer_type='TRAINER_TYPE_NONE',trainer_sight_or_berry_tree_id='0',script='JourneyRegionalTutor',flag='0'))
        layer.stage(p,json.dumps(m,indent=2)+'\n')
    layer.stage('data/scripts/journey_supplies.inc',scripts)
    p='data/event_scripts.s';layer.stage(p,(source/p).read_text()+'\n\t.include "data/scripts/journey_supplies.inc"\n')
    p='include/constants/script_menu.h';text=(source/p).read_text();match=re.search(r'#define MULTI_COUNT\s+(\d+)',text)
    if match:
        n=int(match[1]);text=text[:match.start()]+f'#define MULTI_JOURNEY_EVOLUTION_REGION {n}\n#define MULTI_COUNT {n+1}'+text[match.end():]
    else:
        matches=re.findall(r'#define\s+MULTI_\w+\s+(\d+)',text);n=max(map(int,matches))+1
        text=text.replace('#endif',f'#define MULTI_JOURNEY_EVOLUTION_REGION {n}\n#endif')
    layer.stage(p,text)
    p='src/data/script_menu.h';text=(source/p).read_text();anchor='static const struct MultichoiceListStruct sMultichoiceLists[]'
    text=text.replace(anchor,'''static const struct MenuAction sJourneyEvolutionRegionMenu[]={
    {COMPOUND_STRING("LOCAL"),NULL},{COMPOUND_STRING("ALOLA"),NULL},{COMPOUND_STRING("GALAR"),NULL},{COMPOUND_STRING("HISUI"),NULL}};
'''+anchor,1)
    pos=text.index('{',text.index(anchor));text=text[:pos+1]+'\n    [MULTI_JOURNEY_EVOLUTION_REGION]={sJourneyEvolutionRegionMenu,4},'+text[pos+1:]
    layer.stage(p,text)
    body='''#include "global.h"
#include "pokemon.h"
#include "item.h"
#include "event_data.h"
#include "journey_gym_scaling.h"
#include "constants/items.h"
#include "constants/vars.h"
#include "constants/species.h"
#include "constants/moves.h"
#include "constants/regions.h"
#include "regions.h"
u32 JourneyEvolutionRegion(void)
{
    u16 selection=VarGet(VAR_UNUSED_0x404E);
    return selection==1?REGION_ALOLA:selection==2?REGION_GALAR:selection==3?REGION_HISUI:GetCurrentRegion();
}
void JourneyRegionalTutorApply(void) { }
void JourneySuppliesRing(void)
{
    gSpecialVar_Result=FALSE;
    if(JourneyGymBadgeCount(TRUE)+JourneyGymBadgeCount(FALSE)<2 || CheckBagHasItem(ITEM_MEGA_RING,1))return;
    if(AddBagItem(ITEM_MEGA_RING,1))gSpecialVar_Result=TRUE;
}
void JourneyRegionalTutorAscent(void)
{
    gSpecialVar_Result=FALSE;
    for(u32 i=0;i<PARTY_SIZE;i++)if(GetMonData(&gPlayerParty[i],MON_DATA_SPECIES)==SPECIES_RAYQUAZA)
    {
        u32 slot=3;u16 move=MOVE_DRAGON_ASCENT;
        for(u32 j=0;j<MAX_MON_MOVES;j++)if(GetMonData(&gPlayerParty[i],MON_DATA_MOVE1+j)==MOVE_NONE){slot=j;break;}
        SetMonMoveSlot(&gPlayerParty[i],move,slot);gSpecialVar_Result=TRUE;break;
    }
}
'''
    layer.stage('src/journey_supplies.c',body)
    layer.stage('include/journey_supplies.h','#ifndef GUARD_JOURNEY_SUPPLIES\n#define GUARD_JOURNEY_SUPPLIES\nu32 JourneyEvolutionRegion(void);\n#endif\n')
    p='src/pokemon.c';text=(source/p).read_text().replace('#include "global.h"','#include "global.h"\n#include "journey_supplies.h"',1)
    text=text.replace('GetCurrentRegion() == params[i].arg1','JourneyEvolutionRegion() == params[i].arg1').replace('GetCurrentRegion() != params[i].arg1','JourneyEvolutionRegion() != params[i].arg1')
    layer.stage(p,text)
    p='src/data/items.h';text=(source/p).read_text()
    for item in mega_items+evo_items:
        match=re.search(r'\['+item+r'\]\s*=\s*\{(.*?)\n    \}',text,re.S)
        assert match,item
        block=match[0]
        if item in mega_items or re.search(r'\.price\s*=\s*0\s*,',block):
            new=re.sub(r'\.price\s*=\s*\d+\s*,', '.price = '+str(25000 if item in mega_items else 6000)+',',block,count=1)
            text=text[:match.start()]+new+text[match.end():]
    layer.stage(p,text)
    return layer.finish(mega_species_items=[dict(species=s,item=i) for s,i in megas],mega_stones=len(mega_items),evolution_items=evo_items,shops=inventory,mega_ring_after_two_total_badges=True,regional_tutors=['PalletTown_ProfessorOaksLab','LittlerootTown_ProfessorBirchsLab'],regional_training_variable='VAR_UNUSED_0x404E',converted_evolutions=conversions,origin_items_not_sold=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    r=prepare(p.parse_args().source);print(r['layer'],r['mega_stones'],len(r['evolution_items']))
