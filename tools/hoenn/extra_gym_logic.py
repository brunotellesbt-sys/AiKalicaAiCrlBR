"""C/script integration for the extra circuit without changing link/save ABIs."""
import re
from extra_gyms import GYMS, VALERIE


def apply_logic(layer, records):
    s=layer.source
    def text(p):return (layer.outputs[p] if p in layer.outputs else (s/p).read_bytes()).decode()
    def edit(p,before,after):
        t=text(p);assert t.count(before)==1,(p,before[:80]);layer.stage(p,t.replace(before,after))
    flags=', '.join('FLAG_JOURNEY_BADGE_'+g['key'] for g in GYMS)
    layer.stage('include/journey_extra_gyms.h','''#ifndef GUARD_JOURNEY_EXTRA_GYMS_H
#define GUARD_JOURNEY_EXTRA_GYMS_H
u32 JourneyExtraBadgeCount(void);
u32 JourneyTotalBadgeCount(void);
bool32 JourneyBadgeAt(u32 index);
void JourneyExtraGymEdition(void);
#endif
''')
    layer.stage('src/journey_extra_gyms.c','''#include "global.h"
#include "event_data.h"
#include "journey_extra_gyms.h"
#include "journey_gym_scaling.h"
#include "journey_version.h"
#include "constants/flags.h"
#include "constants/vars.h"
#include "constants/event_objects.h"
static const u16 sExtraBadgeFlags[] = {'''+flags+'''};
bool32 JourneyBadgeAt(u32 index)
{
    u16 flag;
    if (index >= 24) return FALSE;
    flag = index < 8 ? FLAG_BADGE01_GET + index
        : index < 16 ? FLAG_KANTO_BADGE01_GET + index - 8
        : sExtraBadgeFlags[index - 16];
    return (gSaveBlock1Ptr->flags[flag / 8] >> (flag & 7)) & 1;
}
u32 JourneyExtraBadgeCount(void)
{
    u32 i, count = 0;
    for (i = 16; i < 24; i++) count += JourneyBadgeAt(i);
    return count;
}
u32 JourneyTotalBadgeCount(void)
{
    return JourneyGymBadgeCount(TRUE) + JourneyGymBadgeCount(FALSE) + JourneyExtraBadgeCount();
}
void JourneyExtraGymEdition(void)
{
    bool32 modern = gJourneyBuildRules.maxNational > 493;
    VarSet(VAR_OBJ_GFX_ID_0, modern ? OBJ_EVENT_GFX_JOURNEY_PWT_VALERIE : OBJ_EVENT_GFX_JOURNEY_PWT_WHITNEY);
    gSpecialVar_Result = modern;
}
''')
    for p in ['src/journey_adaptive_gym.c','src/journey_galactic.c','src/trainer_card.c']:
        edit(p,'#include "global.h"','#include "global.h"\n#include "journey_extra_gyms.h"')
    p='include/journey_gym_maps.h';t=text(p);at=t.rfind('};');t=t[:at]+''.join('    {MAP_'+g['name'].upper()+', '+('TRUE' if g['kanto'] else 'FALSE')+'},\n' for g in GYMS)+t[at:];layer.stage(p,t)
    p='src/journey_adaptive_gym.c'
    def family(f):
        out='SPECIES_'+f[0]
        for i in range(1,len(f),2):out='(level >= '+str(f[i+1])+' ? SPECIES_'+f[i]+' : '+out+')'
        return out
    branch=''
    for g in GYMS+[VALERIE]:
        branch+='    if (trainer->party == GetTrainerStructFromId(TRAINER_JOURNEY_GYM_'+g['key']+')->party)\n    {\n        switch (slot)\n        {\n'
        for i,f in enumerate(g['team']):branch+='        case '+str(i)+': return '+family(f)+';\n'
        branch+='        }\n    }\n'
    edit(p,'static u16 LeaderSpecies(const struct Trainer *trainer, u32 slot, u32 level)\n{','static u16 LeaderSpecies(const struct Trainer *trainer, u32 slot, u32 level)\n{\n'+branch)
    edit(p,'rank = JourneyGymBadgeCount(sJourneyGyms[gym].kanto);','rank = gym >= 18 ? JourneyTotalBadgeCount() : JourneyGymBadgeCount(sJourneyGyms[gym].kanto);')
    p='src/journey_galactic.c'
    edit(p,'bool32 JourneyGalacticLeagueReady(void) { return JourneyGymBadgeCount(TRUE)==8 && JourneyGymBadgeCount(FALSE)==8 &&','bool32 JourneyGalacticLeagueReady(void) { return JourneyTotalBadgeCount()==24 &&')
    edit('src/journey_adaptive_gym.c','#include \"journey_extra_gyms.h\"','#include \"journey_extra_gyms.h\"\n#include \"journey_wild.h\"')
    edit('src/journey_adaptive_gym.c','    *trainer = *original;','    if (original->party == GetTrainerStructFromId(TRAINER_JOURNEY_GYM_CLAIR)->party)\n        count = min(count, JourneyWildMean() < 36 ? 3 : JourneyWildMean() < 50 ? 5 : 6);\n    *trainer = *original;')
    # Availability of the Galactic episode remains at the original 16 badges.
    # Only the admission denial branch uses the new, complete 24-badge check.
    p='data/scripts/journey_galactic.inc'
    edit(p,'JourneyGalactic_LeagueDenied::\n\tspecial JourneyGalacticAvailable','JourneyGalactic_LeagueDenied::\n\tcallnative JourneyExtraLeagueBadges')
    p='src/journey_extra_gyms.c';layer.stage(p,text(p)+'\nvoid JourneyExtraLeagueBadges(void) { gSpecialVar_Result = JourneyTotalBadgeCount() == 24; }\n')
    old='\t.string "16 GYM BADGES: eight from\\p"\n\t.string "KANTO and eight from HOENN.\\n"\n\t.string "Complete both GYM circuits!$"'
    new='\t.string "24 GYM BADGES: the original\\p"\n\t.string "16 and all eight extra GYMS.\\n"\n\t.string "Check your TRAINER CARD!$"'
    for p in ['data/maps/EverGrandeCity_PokemonLeague_1F/scripts.inc','data/maps/IndigoPlateau_PokemonCenter_1F_Frlg/scripts.inc']:edit(p,old,new)
    # Trainer Card link data stays 16-badge ABI; only the local screen expands.
    p='src/trainer_card.c'
    edit(p,'bool8 unused_E;','u8 unused_E;')
    edit(p,'u8 badgeCount[TRAINER_CARD_BADGES_COUNT];','u8 badgeCount[24];')
    edit(p,'u8 badgeTiles[0x80 * TRAINER_CARD_BADGES_COUNT];','u8 badgeTiles[0x80 * 24];')
    edit(p,'sData->unused_E=!sData->unused_E;','sData->unused_E=(sData->unused_E + (JOY_NEW(L_BUTTON) ? 2 : 1)) % 3;')
    t=text(p)
    t=re.sub(r'    static const u16 sBadgeFlags\[16\] =\s*\{.*?\n    \};','',t,count=1,flags=re.S)
    t=t.replace('for (i = 0; i < TRAINER_CARD_BADGES_COUNT; i++)\n    {\n        if (FlagGet(sBadgeFlags[i]))','for (i = 0; i < 24; i++)\n    {\n        if (JourneyBadgeAt(i))')
    assert 'sBadgeFlags' not in t
    # Native glyph badges are private and occupy the same 32-tile row layout.
    anchor='static const u32 sKantoTrainerCardBadges_Gfx[]'
    pos=t.index(anchor)
    glyphs=['G','F','S','B','I','D','N','O']
    patterns={'G':['01110','10000','10111','10001','01110'],'F':['11111','10000','11110','10000','10000'],'S':['01111','10000','01110','00001','11110'],'B':['11110','10001','11110','10001','11110'],'I':['11111','00100','00100','00100','11111'],'D':['11110','10001','10001','10001','11110'],'N':['10001','11001','10101','10011','10001'],'O':['01110','10001','10001','10001','01110']}
    pixels=[[0]*128 for _ in range(16)]
    for i,g in enumerate(glyphs):
        for y in range(2,14):
            for x in range(2,14):
                if abs(x-7)+abs(y-7)<=8:pixels[y][i*16+x]=3 if abs(x-7)+abs(y-7)>=7 else 1
        for y,row in enumerate(patterns[g]):
            for x,c in enumerate(row):
                if c=='1':pixels[5+y][i*16+5+x]=2
    raw=[]
    for ty in range(2):
        for tx in range(16):
            for y in range(8):
                for x in range(0,8,2):raw.append(pixels[ty*8+y][tx*8+x]|pixels[ty*8+y][tx*8+x+1]<<4)
    array='static const u8 sExtraGymBadges_Gfx[] __attribute__((aligned(4))) = {'+','.join(map(str,raw))+'};\nstatic const u16 sExtraGymBadges_Pal[16] = {RGB(0,0,0),RGB(29,24,9),RGB(8,9,16),RGB(31,31,27)};\n'
    t=t[:pos]+array+t[pos:]
    t=t.replace('sData->badgeTiles + 0x80 * 8);','sData->badgeTiles + 0x80 * 8);\n        CpuCopy16(sExtraGymBadges_Gfx,sData->badgeTiles + 0x80 * 16,sizeof(sExtraGymBadges_Gfx));')
    start=t.index('        LoadPalette(sData->unused_E?sKantoTrainerCardBadges_Pal:')
    end=t.index('        CopyWindowToVram(WIN_CARD_TEXT,COPYWIN_GFX);',start)
    t=t[:start]+'''        u32 page = sData->unused_E, earned = 0, total = 0;
        for (i = 0; i < 24; i++)
        {
            total += sData->badgeCount[i] != 0;
            if (i / 8 == page) earned += sData->badgeCount[i] != 0;
        }
        LoadPalette(page==2?sExtraGymBadges_Pal:page==1?sKantoTrainerCardBadges_Pal:sHoennTrainerCardBadges_Pal,BG_PLTT_ID(3),PLTT_SIZE_4BPP);
        ConvertIntToDecimalStringN(gStringVar1,earned,STR_CONV_MODE_LEFT_ALIGN,1);
        ConvertIntToDecimalStringN(gStringVar2,total,STR_CONV_MODE_LEFT_ALIGN,2);
        StringExpandPlaceholders(gStringVar4,page==2?COMPOUND_STRING("EXTRA {STR_VAR_1}/8  TOTAL {STR_VAR_2}/24"):page==1?COMPOUND_STRING("KANTO {STR_VAR_1}/8  TOTAL {STR_VAR_2}/24"):COMPOUND_STRING("HOENN {STR_VAR_1}/8  TOTAL {STR_VAR_2}/24"));
        FillWindowPixelRect(WIN_CARD_TEXT,PIXEL_FILL(0),24,128,192,14);
        AddTextPrinterParameterized3(WIN_CARD_TEXT,FONT_SMALL,24,128,sTrainerCardTextColors,TEXT_SKIP_DRAW,gStringVar4);
'''+t[end:]
    t=t.replace('for (i = sData->unused_E?8:0; i < (sData->unused_E?16:8); i++)','for (i = page*8; i < (page+1)*8; i++)')
    start=t.index('            if (i < 8)\n',t.index('static void DrawStarsAndBadgesOnCard(void)\n{'))
    end=t.index('\n            FillBgTilemapBufferRect',start)
    t=t[:start]+'''            badgeIndex = i % 8;
            tileNum = 192 + page*32 + badgeIndex*2;
'''+t[end:]
    layer.stage(p,t)
    # Resolve the new indoor player marker to the containing city's actual GPS.
    p='src/data/journey_world_map.h';t=text(p)
    additions=[]
    from prepare_world_dex_map import PAT
    for rec in records:
        m=re.search(PAT,t)
        city=__import__('json').loads((s/f'data/maps/{rec["city"]}/map.json').read_text())
        symbol=city['id']
        match=next(m for m in re.finditer(PAT,t) if m[1]==symbol or (rec['key']=='OAK' and m[1]=='MAP_PALLET_TOWN'))
        additions.append('    {(MAP_GROUP(MAP_'+rec['name'].upper()+')<<8)|MAP_NUM(MAP_'+rec['name'].upper()+'), '+city['region_map_section']+', '+match[3]+', '+match[4]+', COMPOUND_STRING("'+('OAK LAB - BASEMENT' if rec['key']=='OAK' else rec['leader'].upper()+' GYM')+'")},\n')
    start=t.index('static const struct JourneyWorldPoint sWorldPoints[]');end=t.index('\n};',start)
    layer.stage(p,t[:end]+'\n'+''.join(additions)+t[end:])
