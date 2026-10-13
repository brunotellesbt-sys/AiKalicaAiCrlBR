"""Add regional badge tabs and apply campaign battle rules to the PWT."""
import argparse
import re
from pathlib import Path
from candidate_layer import Layer
from prepare_evolution_supplies import PRIOR,LAYER as PREVIOUS

LAYER='badge-case';PRIOR=PRIOR+[PREVIOUS]


def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if result:=layer.existing():return result
    source=layer.source
    p='data/scripts/journey_supplies.inc'
    layer.stage(p,(source/p).read_text().replace('setvar VAR_UNUSED_0x404E, VAR_RESULT','copyvar VAR_UNUSED_0x404E, VAR_RESULT'))
    p='src/data/script_menu.h';text=(source/p).read_text()
    text=re.sub(r'\{(COMPOUND_STRING\("(?:LOCAL|ALOLA|GALAR|HISUI)"\)),NULL\}',r'{.text=\1}',text)
    layer.stage(p,text)
    p='src/trainer_card.c';text=(source/p).read_text()
    anchor='        if (JOY_NEW(A_BUTTON))\n        {\n            FlipTrainerCard();'
    assert anchor in text
    text=text.replace(anchor,'''        if (!sData->isLink && JOY_NEW(L_BUTTON | R_BUTTON | SELECT_BUTTON))
        {
            sData->unused_E=!sData->unused_E;
            DrawStarsAndBadgesOnCard();
            PlaySE(SE_SELECT);
        }
        else if (JOY_NEW(A_BUTTON))
        {
            FlipTrainerCard();''',1)
    anchor='        for (i = 0; i < TRAINER_CARD_BADGES_COUNT; i++)'
    assert text.count(anchor)==1
    text=text.replace(anchor,'''        FillBgTilemapBufferRect(3,0,4,startY,24,4,0);
        LoadPalette(sData->unused_E?sKantoTrainerCardBadges_Pal:sHoennTrainerCardBadges_Pal,BG_PLTT_ID(3),PLTT_SIZE_4BPP);
        FillWindowPixelRect(WIN_CARD_TEXT,PIXEL_FILL(0),24,128,192,14);
        AddTextPrinterParameterized3(WIN_CARD_TEXT,FONT_SMALL,24,128,sTrainerCardTextColors,TEXT_SKIP_DRAW,
            sData->unused_E?COMPOUND_STRING("KANTO  L/R: HOENN"):COMPOUND_STRING("HOENN  L/R: KANTO"));
        CopyWindowToVram(WIN_CARD_TEXT,COPYWIN_GFX);
        for (i = sData->unused_E?8:0; i < (sData->unused_E?16:8); i++)''')
    text=text.replace('y = startY + (i / 8) * 2;','y = startY;')
    layer.stage(p,text)
    # Normal uses random native IVs for important opponents; Hard forces 31.
    p='src/battle_main.c';text=(source/p).read_text()
    anchor='            SetMonData(&party[i], MON_DATA_IVS, &(partyData[monIndex].iv));'
    assert text.count(anchor)==1
    text=text.replace(anchor,'            if(!JourneyCompetitiveTrainer(trainer) || gJourneyBuildRules.perfectIvs)\n    '+anchor)
    layer.stage(p,text)
    p='src/battle_ai_main.c';text=(source/p).read_text()
    anchor='        else if (gBattleTypeFlags & (BATTLE_TYPE_FRONTIER | BATTLE_TYPE_PWT |'
    text=text.replace(anchor,'''        else if (gBattleTypeFlags & BATTLE_TYPE_PWT)
            flags = JourneyCompetitiveAiFlags(trainerId);
        else if (gBattleTypeFlags & (BATTLE_TYPE_FRONTIER |''',1)
    layer.stage(p,text)
    p='src/journey_pwt.c';text=(source/p).read_text().replace('#include "global.h"','#include "global.h"\n#include "journey_version.h"\n#include "journey_competitive.h"\n#include "data.h"',1)
    start=text.index('        u8 ev = 252;');end=text.index('        Level50(mon);',start)
    text=text[:start]+'''        struct TrainerMon build={0};
        build.species=JourneyTrainerSpecies(trainer->species[picks[i]],50);
        build.lvl=50;build.heldItem=items[picks[i]];
        JourneyPrepareCompetitiveMon(&build,50);
        u32 personality=Random32();ModifyPersonalityForNature(&personality,build.nature);
        CreateMon(mon,build.species,50,personality,OTID_STRUCT_RANDOM_NO_SHINY);
        if(gJourneyBuildRules.perfectIvs)SetMonData(mon,MON_DATA_IVS,&build.iv);
        SetMonData(mon,MON_DATA_HELD_ITEM,&build.heldItem);
        SetMonData(mon,MON_DATA_FRIENDSHIP,&build.friendship);
        static const u8 fields[]={MON_DATA_HP_EV,MON_DATA_ATK_EV,MON_DATA_DEF_EV,MON_DATA_SPATK_EV,MON_DATA_SPDEF_EV,MON_DATA_SPEED_EV};
        for(u32 slot=0;slot<6;slot++)SetMonData(mon,fields[slot],&build.ev[slot]);
        for(u32 slot=0;slot<MAX_MON_MOVES;slot++)SetMonMoveSlot(mon,build.moves[slot],slot);
        for(u32 ability=0;ability<NUM_ABILITY_SLOTS;ability++)if(gSpeciesInfo[build.species].abilities[ability]==build.ability){SetMonData(mon,MON_DATA_ABILITY_NUM,&ability);break;}
'''+text[end:]
    layer.stage(p,text)
    # No coin hunt exists in these campaigns; use the requested level alternative.
    p='src/data/pokemon/species_info/gen_9_families.h';text=(source/p).read_text()
    text,count=re.subn(r'\{EVO_LEVEL,\s*0,\s*SPECIES_GHOLDENGO,\s*CONDITIONS\(\{IF_BAG_ITEM_COUNT,\s*ITEM_GIMMIGHOUL_COIN,\s*999\}\)\}','{EVO_LEVEL, 36, SPECIES_GHOLDENGO}',text)
    assert count==2
    layer.stage(p,text)
    return layer.finish(badge_tabs=['HOENN','KANTO'],tab_buttons=['L','R','SELECT'],normal_important_opponents_random_ivs=True,pwt_competitive_profiles_and_max_ai=True,gholdengo_level=36)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    print(prepare(p.parse_args().source)['layer'])
