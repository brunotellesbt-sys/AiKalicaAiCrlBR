#include "global.h"
#include "journey_pwt.h"
#include "journey_pwt_cup.h"
#include "bg.h"
#include "gpu_regs.h"
#include "main.h"
#include "malloc.h"
#include "menu.h"
#include "overworld.h"
#include "palette.h"
#include "sprite.h"
#include "text.h"
#include "window.h"
#include "string_util.h"
#include "constants/rgb.h"

static EWRAM_DATA struct { u16 tiles[1024]; u8 state, mode, group, depth, page; } *sBoard;
static const struct BgTemplate sBgs[] = {{.bg=0,.charBaseIndex=0,.mapBaseIndex=31,.priority=0}};
static const struct WindowTemplate sWindows[] = {
    {.bg=0,.tilemapLeft=1,.tilemapTop=1,.width=28,.height=18,.paletteNum=15,.baseBlock=1},
    DUMMY_WIN_TEMPLATE
};
static const u16 sPalette[] = {RGB(2,3,7),RGB(3,6,12),RGB(31,31,31),RGB(13,17,22),RGB(5,24,30),RGB(30,23,7)};
static const u8 sInk[] = {1,2,3}, sHuman[] = {1,4,3};
static void Text(const u8 *text,u32 x,u32 y,bool32 human)
{ AddTextPrinterParameterized4(0,FONT_SMALL,x,y,0,0,human?sHuman:sInk,0,text); }
static void Number(s32 value,u32 x,u32 y)
{
    u8 text[12];
    if(value<0){text[0]=CHAR_HYPHEN;ConvertIntToDecimalStringN(text+1,-value,STR_CONV_MODE_LEFT_ALIGN,3);}
    else ConvertIntToDecimalStringN(text,value,STR_CONV_MODE_LEFT_ALIGN,3);
    Text(text,x,y,FALSE);
}
static void Draw(void)
{
    const struct JourneyCup *cup=JourneyPWTCupState();
    u32 i;
    FillWindowPixelBuffer(0,PIXEL_FILL(1));
    Text(COMPOUND_STRING("PWT / WORLD CUP"),4,0,FALSE);
    FillWindowPixelRect(0,PIXEL_FILL(4),0,15,224,1);
    if(!sBoard->mode)
    {
        Text(COMPOUND_STRING("GROUP"),4,19,FALSE);Number(sBoard->group+1,40,19);
        Text(COMPOUND_STRING("P  W  PTS  KO  +/-"),111,19,FALSE);
        for(i=0;i<cup->groupSize[sBoard->group];i++)
        {
            u16 entrant=JourneyCupRankedEntrant(cup,sBoard->group,i);
            u32 y=36+i*14;
            Number(i+1,3,y);Text(JourneyPWTEntrantName(entrant),15,y,entrant==0);
            Number(cup->played[entrant],111,y);Number(cup->wins[entrant],127,y);
            Number(cup->points[entrant],145,y);Number(cup->scored[entrant],171,y);
            Number((s32)cup->scored[entrant]-cup->conceded[entrant],198,y);
        }
    }
    else
    {
        u32 base=(1u<<sBoard->depth)-1, pairs=(base+1)/2;
        Text(COMPOUND_STRING("KNOCKOUT / ROUND"),4,19,FALSE);
        Number(sBoard->depth,116,19);Text(COMPOUND_STRING("PAGE"),144,19,FALSE);
        Number(sBoard->page+1,176,19);
        for(i=0;i<2 && sBoard->page*2+i<pairs;i++)
        {
            u32 node=base+2*(sBoard->page*2+i), parent=(node-1)/2, y=39+i*40;
            u16 a=cup->bracket[node],b=cup->bracket[node+1],winner=cup->bracket[parent];
            Text(JourneyPWTEntrantName(a),4,y,a==0);
            Text(JourneyPWTEntrantName(b),4,y+17,b==0);
            FillWindowPixelRect(0,PIXEL_FILL(4),86,y+6,7,1);
            FillWindowPixelRect(0,PIXEL_FILL(4),86,y+23,7,1);
            FillWindowPixelRect(0,PIXEL_FILL(4),92,y+6,1,18);
            FillWindowPixelRect(0,PIXEL_FILL(4),93,y+15,12,1);
            Text(JourneyPWTEntrantName(winner),111,y+8,winner==0);
        }
        if(cup->stage==JOURNEY_CUP_GROUP_STAGE)Text(COMPOUND_STRING("Bracket opens after group stage."),4,108,FALSE);
    }
    FillWindowPixelRect(0,PIXEL_FILL(4),0,118,224,1);
    Text(COMPOUND_STRING("L/R: PAGE  UP/DOWN: ROUND"),4,120,FALSE);
    Text(COMPOUND_STRING("SELECT: VIEW  A/B: CONTINUE"),4,132,FALSE);
    // Controls also accept left/right; SELECT toggles standings/bracket.
    CopyWindowToVram(0,COPYWIN_FULL);
}
static void VBlank(void){LoadOam();ProcessSpriteCopyRequests();TransferPlttBuffer();}
static void Return(void)
{
    SetVBlankCallback(NULL);FreeAllWindowBuffers();UnsetBgTilemapBuffer(0);
    FREE_AND_SET_NULL(sBoard);SetMainCallback2(CB2_ReturnToFieldContinueScriptPlayMapMusic);
}
static void Main(void)
{
    const struct JourneyCup *cup=JourneyPWTCupState();
    if(sBoard->state==0)
    {
        SetGpuReg(REG_OFFSET_DISPCNT,0);ResetBgsAndClearDma3BusyFlags(0);
        ResetSpriteData();FreeAllSpritePalettes();ResetPaletteFade();
        InitBgsFromTemplates(0,sBgs,ARRAY_COUNT(sBgs));SetBgTilemapBuffer(0,sBoard->tiles);
        InitWindows(sWindows);DeactivateAllTextPrinters();
        LoadPalette(sPalette,BG_PLTT_ID(15),sizeof(sPalette));PutWindowTilemap(0);
        Draw();ShowBg(0);SetVBlankCallback(VBlank);
        BeginNormalPaletteFade(PALETTES_ALL,0,16,0,RGB_BLACK);sBoard->state=1;
    }
    else if(sBoard->state==1 && !gPaletteFade.active)
    {
        bool32 change=FALSE;
        if(JOY_NEW(A_BUTTON|B_BUTTON)){BeginNormalPaletteFade(PALETTES_ALL,0,0,16,RGB_BLACK);sBoard->state=2;}
        else if(JOY_NEW(SELECT_BUTTON)){sBoard->mode^=1;sBoard->page=0;change=TRUE;}
        else if(!sBoard->mode)
        {
            if(JOY_NEW(DPAD_RIGHT|R_BUTTON)){sBoard->group=(sBoard->group+1)%cup->groupCount;change=TRUE;}
            if(JOY_NEW(DPAD_LEFT|L_BUTTON)){sBoard->group=(sBoard->group+cup->groupCount-1)%cup->groupCount;change=TRUE;}
        }
        else
        {
            u32 maxDepth=1,pages;
            while((1u<<maxDepth)<cup->groupCount*2u)maxDepth++;
            if(JOY_NEW(DPAD_UP) && sBoard->depth>1){sBoard->depth--;sBoard->page=0;change=TRUE;}
            if(JOY_NEW(DPAD_DOWN) && sBoard->depth<maxDepth){sBoard->depth++;sBoard->page=0;change=TRUE;}
            pages=max(1,(1u<<sBoard->depth)/4);
            if(JOY_NEW(DPAD_RIGHT|R_BUTTON)){sBoard->page=(sBoard->page+1)%pages;change=TRUE;}
            if(JOY_NEW(DPAD_LEFT|L_BUTTON)){sBoard->page=(sBoard->page+pages-1)%pages;change=TRUE;}
        }
        if(change)Draw();
    }
    else if(sBoard->state==2 && !gPaletteFade.active){Return();return;}
    UpdatePaletteFade();
}
void JourneyPWTBoard(void)
{
    const struct JourneyCup *cup=JourneyPWTCupState();
    SetVBlankCallback(NULL);sBoard=AllocZeroed(sizeof(*sBoard));
    if(sBoard==NULL){SetMainCallback2(CB2_ReturnToFieldContinueScriptPlayMapMusic);return;}
    sBoard->group=cup->groupOf[0];sBoard->mode=cup->stage!=JOURNEY_CUP_GROUP_STAGE;
    sBoard->depth=1;while((1u<<sBoard->depth)<cup->groupCount*2u)sBoard->depth++;
    SetMainCallback2(Main);
}
