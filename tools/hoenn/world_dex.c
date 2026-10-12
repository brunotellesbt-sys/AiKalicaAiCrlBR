#include "global.h"
#include "main.h"
#include "journey_habitats.h"
#include "bg.h"
#include "gpu_regs.h"
#include "malloc.h"
#include "palette.h"
#include "pokemon.h"
#include "pokedex.h"
#include "sound.h"
#include "sprite.h"
#include "task.h"
#include "window.h"
#include "text.h"
#include "menu.h"
#include "string_util.h"
#include "constants/maps.h"
#include "constants/region_map_sections.h"
#include "constants/rgb.h"
#include "constants/songs.h"
#include "journey_world_dex.h"
struct JourneyWorldPoint { u16 map; u16 section; u8 x, y; const u8 *name; };
#include "data/journey_world_map.h"
#include "data/journey_world_dex_locations.h"
#define WORLD_DEX_TAG 0x7E40
static EWRAM_DATA struct {
    u8 *result;
    u16 species;
    u8 sprites[32], count, caption;
} *sWorldDex;
static const struct WindowTemplate sCaptionWindow = {.bg=3,.tilemapLeft=1,.tilemapTop=18,.width=28,.height=2,.paletteNum=7,.baseBlock=400};
static const u8 sCaptionColors[3]={0,14,0};
static const u8 sHabitatLabel[]=_("HABITAT: ");
static const u8 sLocationsLabel[]=_("ORANGE MARKS: LOCATIONS");
static const u8 sUnknownLabel[]=_("AREA UNKNOWN");
static const u8 sMarkerTiles[32] = {0,0x11,0x11,0,0x10,0x22,0x22,1,0x21,0x22,0x22,0x12,0x21,0x22,0x22,0x12,0x21,0x22,0x22,0x12,0x21,0x22,0x22,0x12,0x10,0x22,0x22,1,0,0x11,0x11,0};
static const u16 sMarkerColors[16] = {RGB_BLACK,RGB(31,12,0),RGB(31,26,4)};
static const struct SpriteSheet sMarkerSheet = {sMarkerTiles,sizeof(sMarkerTiles),WORLD_DEX_TAG};
static const struct SpritePalette sMarkerPalette = {sMarkerColors,WORLD_DEX_TAG};
static const struct OamData sMarkerOam = {.shape=SPRITE_SHAPE(8x8),.size=SPRITE_SIZE(8x8),.priority=0};
static void MarkerBlink(struct Sprite *sprite) { sprite->invisible = (++sprite->data[0] % 48) >= 36; }
static const struct SpriteTemplate sMarkerTemplate = {WORLD_DEX_TAG,WORLD_DEX_TAG,&sMarkerOam,gDummySpriteAnimTable,NULL,gDummySpriteAffineAnimTable,MarkerBlink};
static void Task_WorldDex(u8 id)
{
    u16 i;
    u8 result = 0;
    if (gTasks[id].data[0] == 0)
    {
        u16 *tm = GetBgTilemapBuffer(3);
        ResetSpriteData();FreeAllSpritePalettes();HideBg(0);HideBg(2);HideBg(3);
        SetBgAttribute(3,BG_ATTR_CHARBASEINDEX,3);
        SetBgAttribute(3,BG_ATTR_PALETTEMODE,0);
        SetBgAttribute(3,BG_ATTR_METRIC,0);
        LoadBgTiles(3,sWorldTiles,sizeof(sWorldTiles),0);
        for (i=0;i<1024;i++) tm[i]=sWorldTilemap[i] | (7<<12);
        CopyBgTilemapBufferToVram(3);LoadPalette(sWorldPalette,BG_PLTT_ID(7),sizeof(sWorldPalette));
        ChangeBgX(3,0,BG_COORD_SET);ChangeBgY(3,0,BG_COORD_SET);
        if(JourneyWorldDexLocationCount(sWorldDex->species)){LoadSpriteSheet(&sMarkerSheet);LoadSpritePalette(&sMarkerPalette);}
        for(i=0;i<ARRAY_COUNT(sWorldDexLocations);i++)
            if(sWorldDexLocations[i].species==sWorldDex->species && (sWorldDexLocations[i].fixed || JourneyHabitatHasSpecies(MAP_GROUP(sWorldDexLocations[i].map),MAP_NUM(sWorldDexLocations[i].map),sWorldDex->species)) && sWorldDex->count<ARRAY_COUNT(sWorldDex->sprites))
            {
                u8 sprite=CreateSprite(&sMarkerTemplate,sWorldDexLocations[i].x+8,sWorldDexLocations[i].y+24,0);
                if(sprite!=MAX_SPRITES)sWorldDex->sprites[sWorldDex->count++]=sprite;
            }
        sWorldDex->caption=AddWindow(&sCaptionWindow);
        if(sWorldDex->caption!=WINDOW_NONE)
        {
            StringCopy(gStringVar4,sHabitatLabel);StringAppend(gStringVar4,gSpeciesInfo[sWorldDex->species].speciesName);
            FillWindowPixelBuffer(sWorldDex->caption,PIXEL_FILL(0));
            AddTextPrinterParameterized4(sWorldDex->caption,FONT_SMALL,0,0,0,0,sCaptionColors,0,gStringVar4);
            AddTextPrinterParameterized4(sWorldDex->caption,FONT_SMALL,0,8,0,0,sCaptionColors,0,sWorldDex->count?sLocationsLabel:sUnknownLabel);
            PutWindowTilemap(sWorldDex->caption);CopyWindowToVram(sWorldDex->caption,COPYWIN_FULL);
        }
        ShowBg(3);SetGpuRegBits(REG_OFFSET_DISPCNT,DISPCNT_OBJ_ON);
        BeginNormalPaletteFade(PALETTES_ALL & ~(0x14),0,16,0,RGB_BLACK);
        gTasks[id].data[0]=1;return;
    }
    if(gTasks[id].data[0]==1)
    {
        if(gPaletteFade.active)return;
        if(JOY_NEW(B_BUTTON) || JOY_NEW(DPAD_LEFT) || JOY_NEW(L_BUTTON))result=1;
        else if(JOY_NEW(DPAD_RIGHT) || JOY_NEW(R_BUTTON))
        {
            if(!GetSetPokedexFlag(SpeciesToNationalPokedexNum(sWorldDex->species),FLAG_GET_CAUGHT)) {PlaySE(SE_FAILURE);return;}
            result=2;
        }
        if(!result)return;
        gTasks[id].data[1]=result;gTasks[id].data[0]=2;
        PlaySE(SE_DEX_PAGE);BeginNormalPaletteFade(PALETTES_ALL & ~(0x14),0,0,16,RGB_BLACK);return;
    }
    if(gPaletteFade.active)return;
    for(i=0;i<sWorldDex->count;i++)DestroySprite(&gSprites[sWorldDex->sprites[i]]);
    FreeSpriteTilesByTag(WORLD_DEX_TAG);FreeSpritePaletteByTag(WORLD_DEX_TAG);
    if(sWorldDex->caption!=WINDOW_NONE){ClearWindowTilemap(sWorldDex->caption);RemoveWindow(sWorldDex->caption);}
    SetBgAttribute(3,BG_ATTR_CHARBASEINDEX,0);SetBgAttribute(3,BG_ATTR_PALETTEMODE,0);
    *sWorldDex->result=gTasks[id].data[1];FREE_AND_SET_NULL(sWorldDex);DestroyTask(id);
}
void JourneyWorldDexOpen(u16 species,u8 *result)
{
    sWorldDex=AllocZeroed(sizeof(*sWorldDex));
    if(sWorldDex==NULL){*result=1;return;}
    sWorldDex->species=species;sWorldDex->result=result;*result=0;CreateTask(Task_WorldDex,0);
}
u32 JourneyWorldDexLocationCount(u16 species)
{
    u32 i,count=0;
    for(i=0;i<ARRAY_COUNT(sWorldDexLocations);i++)if(sWorldDexLocations[i].species==species)count++;
    return count;
}
