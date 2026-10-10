#include "global.h"
#include "bg.h"
#include "event_data.h"
#include "gpu_regs.h"
#include "main.h"
#include "malloc.h"
#include "menu.h"
#include "overworld.h"
#include "palette.h"
#include "sprite.h"
#include "text.h"
#include "text_window.h"
#include "window.h"
#include "sound.h"
#include "field_effect.h"
#include "party_menu.h"
#include "item_menu.h"
#include "constants/maps.h"
#include "constants/rgb.h"
#include "constants/songs.h"
#include "journey_world_map.h"

extern bool8 gFlightCallFromBag;
void ClearForcedFlightRegion(void);

struct JourneyWorldPoint { u16 map; u16 section; u8 x, y; const u8 *name; };
#include "data/journey_world_map.h"

static EWRAM_DATA struct {
    MainCallback callback;
    u16 tilemap[1024];
    u16 player, selected;
    u8 x, y, state, fly;
} *sJourneyWorldMap;

static const struct BgTemplate sWorldBgs[] = {
    {.bg=0, .charBaseIndex=0, .mapBaseIndex=31, .priority=0},
    {.bg=1, .charBaseIndex=2, .mapBaseIndex=30, .priority=1}
};
static const struct WindowTemplate sWorldWindows[] = {
    {.bg=0,.tilemapLeft=1,.tilemapTop=0,.width=28,.height=3,.paletteNum=15,.baseBlock=1},
    {.bg=0,.tilemapLeft=1,.tilemapTop=17,.width=28,.height=3,.paletteNum=15,.baseBlock=85},
    {.bg=0,.tilemapLeft=1,.tilemapTop=3,.width=28,.height=14,.paletteNum=15,.baseBlock=170},
    DUMMY_WIN_TEMPLATE
};
static const u16 sWorldUiPalette[] = { RGB(0,0,0), RGB(3,5,9), RGB(31,31,31), RGB(10,12,15), RGB(31,4,4), RGB(0,31,31) };

u16 JourneyWorldMapPlayerPoint(void)
{
    u16 i, map=(gSaveBlock1Ptr->location.mapGroup<<8)|gSaveBlock1Ptr->location.mapNum;
    for(i=0;i<ARRAY_COUNT(sWorldPoints);i++) if(sWorldPoints[i].map==map) return i;
    // Interiors, underwater areas and native caves retain their regional section.
    for(i=0;i<ARRAY_COUNT(sWorldPoints);i++) if(sWorldPoints[i].section==gMapHeader.regionMapSectionId) return i;
    return 0;
}

static void WorldDraw(void)
{
    u16 i, best=0;
    u32 distance=65535, d;
    s16 dx,dy;
    const struct JourneyWorldPoint *player=&sWorldPoints[sJourneyWorldMap->player];
    for(i=0;i<ARRAY_COUNT(sWorldPoints);i++) {
        if(sJourneyWorldMap->fly && !JourneyWorldFlyAllowed(sWorldPoints[i].map,sWorldPoints[i].section))continue;
        dx=sJourneyWorldMap->x-sWorldPoints[i].x;dy=sJourneyWorldMap->y-sWorldPoints[i].y;d=dx*dx+dy*dy;
        if(d<distance){distance=d;best=i;}
    }
    sJourneyWorldMap->selected=best;
    FillWindowPixelBuffer(2,PIXEL_FILL(0));
    FillWindowPixelRect(2,PIXEL_FILL(5),player->x-1,player->y-1,3,3);
    FillWindowPixelRect(2,PIXEL_FILL(4),sJourneyWorldMap->x-3,sJourneyWorldMap->y-3,7,7);
    FillWindowPixelRect(2,PIXEL_FILL(0),sJourneyWorldMap->x-2,sJourneyWorldMap->y-2,5,5);
    FillWindowPixelRect(2,PIXEL_FILL(2),sJourneyWorldMap->x,sJourneyWorldMap->y,1,1);
    FillWindowPixelBuffer(1,PIXEL_FILL(1));
    AddTextPrinterParameterized(1,FONT_SMALL,distance<100?sWorldPoints[best].name:COMPOUND_STRING("OPEN SEA"),0,0,0,NULL);
    AddTextPrinterParameterized(1,FONT_SMALL,sJourneyWorldMap->fly?COMPOUND_STRING("A: FLY  SELECT: YOU  B: BACK"):COMPOUND_STRING("D-PAD: MOVE  SELECT: YOU  B: BACK"),0,12,0,NULL);
    CopyWindowToVram(1,COPYWIN_FULL);CopyWindowToVram(2,COPYWIN_FULL);
}

static void WorldVBlank(void) { LoadOam();ProcessSpriteCopyRequests();TransferPlttBuffer(); }

void CB2_JourneyWorldMap(void)
{
    if(sJourneyWorldMap->state==0) {
        SetGpuReg(REG_OFFSET_DISPCNT,0);ResetBgsAndClearDma3BusyFlags(0);
        ResetSpriteData();FreeAllSpritePalettes();ResetPaletteFade();
        InitBgsFromTemplates(0,sWorldBgs,ARRAY_COUNT(sWorldBgs));
        ChangeBgX(0,0,BG_COORD_SET);ChangeBgY(0,0,BG_COORD_SET);
        ChangeBgX(1,0,BG_COORD_SET);ChangeBgY(1,0,BG_COORD_SET);
        SetBgTilemapBuffer(1,sJourneyWorldMap->tilemap);
        CpuCopy16(sWorldTilemap,sJourneyWorldMap->tilemap,sizeof(sWorldTilemap));
        LoadBgTiles(1,sWorldTiles,sizeof(sWorldTiles),0);CopyBgTilemapBufferToVram(1);
        LoadPalette(sWorldPalette,0,sizeof(sWorldPalette));LoadPalette(sWorldUiPalette,BG_PLTT_ID(15),sizeof(sWorldUiPalette));
        InitWindows(sWorldWindows);DeactivateAllTextPrinters();
        FillWindowPixelBuffer(0,PIXEL_FILL(1));
        AddTextPrinterParameterized(0,FONT_SMALL,COMPOUND_STRING("WORLD MAP: KANTO / HOENN / SEVII"),0,0,0,NULL);
        AddTextPrinterParameterized(0,FONT_SMALL,COMPOUND_STRING("CYAN: YOU   RED: CURSOR"),0,12,0,NULL);
        PutWindowTilemap(0);PutWindowTilemap(1);PutWindowTilemap(2);CopyWindowToVram(0,COPYWIN_FULL);
        WorldDraw();ShowBg(0);ShowBg(1);SetVBlankCallback(WorldVBlank);
        BeginNormalPaletteFade(PALETTES_ALL,0,16,0,RGB_BLACK);sJourneyWorldMap->state=1;
    } else if(sJourneyWorldMap->state==1 && !gPaletteFade.active) {
        if(JOY_NEW(B_BUTTON)) { BeginNormalPaletteFade(PALETTES_ALL,0,0,16,RGB_BLACK);sJourneyWorldMap->state=2; }
        else if(sJourneyWorldMap->fly && JOY_NEW(A_BUTTON)) {
            const struct JourneyWorldPoint *p=&sWorldPoints[sJourneyWorldMap->selected];
            s16 dx=sJourneyWorldMap->x-p->x,dy=sJourneyWorldMap->y-p->y;
            if(dx*dx+dy*dy<=16 && JourneyWorldFlyAllowed(p->map,p->section)) {
                BeginNormalPaletteFade(PALETTES_ALL,0,0,16,RGB_BLACK);sJourneyWorldMap->state=3;
            }
        }
        else {
            u8 x=sJourneyWorldMap->x,y=sJourneyWorldMap->y;
            if(JOY_REPEAT(DPAD_LEFT) && x>5)x-=3;
            if(JOY_REPEAT(DPAD_RIGHT) && x<217)x+=3;
            if(JOY_REPEAT(DPAD_UP) && y>5)y-=3;
            if(JOY_REPEAT(DPAD_DOWN) && y<107)y+=3;
            if(JOY_NEW(SELECT_BUTTON)){x=sWorldPoints[sJourneyWorldMap->player].x;y=sWorldPoints[sJourneyWorldMap->player].y;}
            if(x!=sJourneyWorldMap->x || y!=sJourneyWorldMap->y){sJourneyWorldMap->x=x;sJourneyWorldMap->y=y;WorldDraw();}
        }
    } else if((sJourneyWorldMap->state==2 || sJourneyWorldMap->state==3) && !gPaletteFade.active) {
        MainCallback callback=sJourneyWorldMap->callback;
        bool8 fly=sJourneyWorldMap->state==3;
        bool8 wasFly=sJourneyWorldMap->fly;
        u16 map=sWorldPoints[sJourneyWorldMap->selected].map,section=sWorldPoints[sJourneyWorldMap->selected].section;
        SetVBlankCallback(NULL);FreeAllWindowBuffers();UnsetBgTilemapBuffer(1);
        FREE_AND_SET_NULL(sJourneyWorldMap);
        if(fly) {
            JourneyWorldFlyDestination(map,section);
            if(gFlightCallFromBag)gSkipShowMonAnim=TRUE;
            gFlightCallFromBag=FALSE;ClearForcedFlightRegion();ReturnToFieldFromFlyMapSelect();
        } else {
            if(wasFly){ClearForcedFlightRegion();gFlightCallFromBag=FALSE;}
            SetMainCallback2(callback);
        }
        return;
    }
    UpdatePaletteFade();
}

void JourneyWorldMapOpen(MainCallback callback)
{
    SetVBlankCallback(NULL);
    sJourneyWorldMap=AllocZeroed(sizeof(*sJourneyWorldMap));
    if(sJourneyWorldMap==NULL){SetMainCallback2(callback);return;}
    sJourneyWorldMap->callback=callback;sJourneyWorldMap->player=JourneyWorldMapPlayerPoint();
    sJourneyWorldMap->x=sWorldPoints[sJourneyWorldMap->player].x;sJourneyWorldMap->y=sWorldPoints[sJourneyWorldMap->player].y;
    SetMainCallback2(CB2_JourneyWorldMap);
}

void JourneyWorldMapOpenFly(void)
{
    JourneyWorldMapOpen(gFlightCallFromBag?CB2_ReturnToBagMenuPocket:CB2_ReturnToPartyMenuFromFlyMap);
    if(sJourneyWorldMap!=NULL)sJourneyWorldMap->fly=TRUE;
}
