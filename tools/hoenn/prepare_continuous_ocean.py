"""Use one animated ocean across Hoenn/Kanto and open the Sevii strait mouths."""
import argparse,copy,io,json,re,struct
from pathlib import Path
from PIL import Image
from candidate_layer import Layer
from prepare_dewford_island_harbor import PRIOR,LAYER as PREVIOUS
from sevii_navigation_grid import reconcile
from world_grid_updates import rebuild

LAYER='continuous-ocean'
PRIOR=PRIOR+[PREVIOUS]


def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if old:=layer.existing():return old
    s=layer.source
    maps={p.parent.name:json.loads(p.read_text()) for p in (s/'data/maps').glob('*/map.json')}
    layouts={l['id']:l for l in json.loads((s/'data/layouts/layouts.json').read_text())['layouts']}
    def load(name):
        l=layouts[maps[name]['layout']];p=l['blockdata_filepath']
        return l,p,list(struct.unpack('<'+'H'*(l['width']*l['height']),(s/p).read_bytes()))
    # Remove whole loose rock pairs at the mouth, retaining the two native
    # cliff islands on either side. The ten-tile entrance has no slalom.
    l,p,v=load('Route124');changed=[]
    for y in range(7):
        for x in range(41,51):
            i=y*l['width']+x
            assert v[i]>>12<=1,('Would erase original elevated land',x,y,hex(v[i]))
            if v[i]!=0x1170:changed.append([x,y,v[i]])
            v[i]=0x1170
    layer.stage(p,struct.pack('<'+'H'*len(v),*v))
    l,p,v=load('JourneyNorthHoennStrait');rocks=[]
    for i,t in enumerate(v):
        if t&1023 in (0x110,0x111,0x118,0x119):
            rocks.append([i%l['width'],i//l['width'],t]);v[i]=0x112B
    layer.stage(p,struct.pack('<'+'H'*len(v),*v))
    layer.stage(l['border_filepath'],struct.pack('<4H',*[0x152B]*4))
    # Lateral reefs mark the outside limits; both long mouths stay open.
    for y in range(l['height']):
        for x in range(l['width']):
            v[y*l['width']+x]=[0x510,0x511,0x518,0x519][y%2*2+x%2] if x<2 or x>=l['width']-2 else 0x112B
    layer.stage(p,struct.pack('<'+'H'*len(v),*v))
    layer.stage(l['border_filepath'],struct.pack('<4H',0x510,0x511,0x518,0x519))
    # Keep the two southward branches disjoint. Expanding the empty eastern
    # water apron exposes all 32 strait columns instead of only four.
    a,b='JourneyNorthHoennStrait','JourneyKantoEasternChannel'
    l,p,v=load(b);assert l['width']==27
    expanded=[v[y*27+x] if x<27 else 0x112B for y in range(l['height']) for x in range(59)]
    layer.stage(p,struct.pack('<'+'H'*len(expanded),*expanded))
    ld=json.loads((s/'data/layouts/layouts.json').read_text());next(q for q in ld['layouts'] if q['id']==l['id'])['width']=59
    layer.stage('data/layouts/layouts.json',json.dumps(ld,indent=2)+'\n')
    # Keep the ocean at the same VRAM tile addresses and palette indices in
    # both engines. Loading another region cannot reinterpret the visible sea.
    hoenn='data/tilesets/primary/general';frlg='data/tilesets/primary/general_frlg'
    reference=(s/f'{hoenn}/palettes/04.pal').read_text().splitlines()
    for folder in [hoenn,frlg]:
        palette=(s/f'{folder}/palettes/04.pal').read_text().splitlines()
        for dst,src in [(3,11),(4,12),(5,13),(7,14)]:palette[3+dst]=reference[3+src]
        if folder==frlg:palette[3+6]=reference[3+14]
        layer.stage(f'{folder}/palettes/04.pal','\n'.join(palette)+'\n')
    colors={11:3,12:4,13:5,14:7}
    def pixels(im,tid,remap=False):
        columns=im.width//8;x=tid%columns*8;y=tid//columns*8
        return [[colors[im.getpixel((x+dx,y+dy))] if remap else im.getpixel((x+dx,y+dy)) for dx in range(8)] for dy in range(8)]
    def put(im,tid,values):
        columns=im.width//8;x=tid%columns*8;y=tid//columns*8
        for dy in range(8):
            for dx in range(8):im.putpixel((x+dx,y+dy),values[dy][dx])
    def stage_png(path,im):
        out=io.BytesIO();im.save(out,format='PNG');layer.stage(path,out.getvalue())
    # Relocate the two old FRLG bank-edge tiles into the freed ocean slots.
    remap={416:454,417:455,418:455,419:454,454:416,455:417}
    original=Image.open(s/f'{hoenn}/tiles.png');target=original.copy()
    for tid in [454,455]:put(target,tid,pixels(original,tid,True))
    stage_png(f'{hoenn}/tiles.png',target)
    original=Image.open(s/f'{frlg}/tiles.png');target=original.copy()
    for old,new in [(454,416),(455,417)]:put(target,new,pixels(original,old))
    for tid in [454,455]:put(target,tid,pixels(Image.open(s/f'{hoenn}/tiles.png'),tid,True))
    stage_png(f'{frlg}/tiles.png',target)
    for frame in range(8):
        path=f'{hoenn}/anim/water/{frame}.png';original=Image.open(s/path);target=original.copy()
        for tid in [22,23]:put(target,tid,pixels(original,tid,True))
        stage_png(path,target)
        path=f'{frlg}/anim/water_current_landwatersedge/{frame}.png';fr=Image.open(s/path);target=fr.copy()
        for old,new in [(38,0),(39,1)]:put(target,new,pixels(fr,old))
        for dst,src in [(38,22),(39,23)]:put(target,dst,pixels(original,src,True))
        stage_png(path,target)
    # Every coastal bank can contain references to primary water/edge tiles.
    headers=(s/'src/data/tilesets/headers.h').read_text();metas=(s/'src/data/tilesets/metatiles.h').read_text()
    banks={'gTileset_General_Frlg'}|{l['secondary_tileset'] for l in layouts.values() if l['primary_tileset']=='gTileset_General_Frlg'}
    retargeted=[]
    for bank in sorted(banks):
        body=re.search(r'const struct Tileset '+bank+r'\s*=\s*\{(.*?)\};',headers,re.S)[1]
        sym=re.search(r'\.metatiles\s*=\s*(\w+)',body)[1]
        path=re.search(r'\b'+sym+r'\[\].*?"([^"]+)"',metas)[1]
        raw=(s/path).read_bytes();words=struct.unpack('<'+'H'*(len(raw)//2),raw)
        values=[(w&~1023)|remap.get(w&1023,w&1023) for w in words]
        if list(words)!=values:layer.stage(path,struct.pack('<'+'H'*len(values),*values));retargeted.append(bank)
    # A bank switch must redraw the visible layers, even when both maps use
    # FRLG: otherwise old tile references turn into the new bank's rocks.
    p='src/field_camera.c';text=(s/p).read_text()
    assert text.count('bool32 oldFrlgFormat = gMapHeader.mapLayout->isFrlg;')==2
    text=text.replace('bool32 oldFrlgFormat = gMapHeader.mapLayout->isFrlg;','const struct MapLayout *oldLayout = gMapHeader.mapLayout;')
    text=text.replace('if (oldFrlgFormat != gMapHeader.mapLayout->isFrlg)','if (oldLayout->primaryTileset != gMapHeader.mapLayout->primaryTileset\n         || oldLayout->secondaryTileset != gMapHeader.mapLayout->secondaryTileset\n         || (gCamera.active && (gPlayerAvatar.flags & PLAYER_AVATAR_FLAG_SURFING)))')
    layer.stage(p,text)
    p='src/fieldmap.c';text=(s/p).read_text()
    old='''        SetPositionFromConnection(connection, direction, x, y);
        LoadMapFromCameraTransition(connection->mapGroup, connection->mapNum);'''
    assert text.count(old)==1
    text=text.replace(old,'''        if (gPlayerAvatar.flags & PLAYER_AVATAR_FLAG_SURFING)
        {
            const struct MapLayout *next = GetMapHeaderFromConnection(connection)->mapLayout;
            freshCoastView |= next->primaryTileset != gMapHeader.mapLayout->primaryTileset
                           || next->secondaryTileset != gMapHeader.mapLayout->secondaryTileset;
        }
        // Clear BEFORE InitMap/LoadSavedMapView can replay foreign bank IDs.
        if (freshCoastView)
            ClearSavedMapView();
        SetPositionFromConnection(connection, direction, x, y);
        LoadMapFromCameraTransition(connection->mapGroup, connection->mapNum);''')
    layer.stage(p,text)
    p='src/overworld.c';text=(s/p).read_text()
    text=text.replace('    bool32 oldFrlgFormat = gMapHeader.mapLayout->isFrlg;','    bool32 oldFrlgFormat = gMapHeader.mapLayout->isFrlg;\n    bool32 oldPaletteTransferDisabled = gPaletteFade.bufferTransferDisabled;',1)
    begin=text.index('    if (oldFrlgFormat != gMapHeader.mapLayout->isFrlg)',text.index('void LoadMapFromCameraTransition('))
    end=text.index('    LoadObjEventTemplatesFromHeader();',begin)
    text=text[:begin]+'''    if (oldFrlgFormat != gMapHeader.mapLayout->isFrlg)
        CpuFill16(0, gSaveBlock1Ptr->mapView, sizeof(gSaveBlock1Ptr->mapView));
'''+text[end:]
    old='    ApplyWeatherColorMapToPals(GetNumPalsInPrimary(gMapHeader.mapLayout), NUM_PALS_TOTAL - GetNumPalsInPrimary(gMapHeader.mapLayout)); // palettes [6,12]'
    assert text.count(old)==1
    text=text.replace(old,'''    // The new primary palette also needs the current weather/time tint.
    // Leaving it in daylight makes an ocean seam flash at night.
    if (oldPrimary != gMapHeader.mapLayout->primaryTileset)
        ApplyWeatherColorMapToPals(0, NUM_PALS_TOTAL);
    else
        ApplyWeatherColorMapToPals(GetNumPalsInPrimary(gMapHeader.mapLayout), NUM_PALS_TOTAL - GetNumPalsInPrimary(gMapHeader.mapLayout));''')
    text=text.replace('        CopyPrimaryTilesetToVram(gMapHeader.mapLayout);\n        LoadMapTilesetPalettes(gMapHeader.mapLayout);', '        gPaletteFade.bufferTransferDisabled = TRUE;\n        CopyPrimaryTilesetToVram(gMapHeader.mapLayout);\n        LoadMapTilesetPalettes(gMapHeader.mapLayout);',1)
    needle='    InitSecondaryTilesetAnimation();\n    UpdateLocationHistoryForRoamer();'
    assert text.count(needle)==1
    text=text.replace(needle,'    gPaletteFade.bufferTransferDisabled = oldPaletteTransferDisabled;\n'+needle)
    layer.stage(p,text)
    p='src/tileset_anims.c';text=(s/p).read_text().replace('#include "fieldmap.h"','#include "fieldmap.h"\n#include "main.h"',1)
    text=text.replace('static void ResetTilesetAnimBuffer(void)','static void RefreshContinuousOceanTiles(void);\n\nstatic void ResetTilesetAnimBuffer(void)',1)
    text=text.replace('    _InitSecondaryTilesetAnimation();\n}\n\nvoid InitSecondaryTilesetAnimation','    _InitSecondaryTilesetAnimation();\n    RefreshContinuousOceanTiles();\n}\n\nvoid InitSecondaryTilesetAnimation',1)
    old='    u8 i = timer % ARRAY_COUNT(gTilesetAnims_General_Water);'
    assert text.count(old)==1
    text=text.replace(old,'    u8 i = (gMain.vblankCounter1 >> 4) % ARRAY_COUNT(gTilesetAnims_General_Water);')
    old='sTilesetAnims_General_Water_Current_LandWatersEdge[timer % ARRAY_COUNT(sTilesetAnims_General_Water_Current_LandWatersEdge)]'
    assert text.count(old)==1
    text=text.replace(old,'sTilesetAnims_General_Water_Current_LandWatersEdge[(gMain.vblankCounter1 >> 4) % ARRAY_COUNT(sTilesetAnims_General_Water_Current_LandWatersEdge)]')
    text+='''
// Populate the current ocean frame immediately when a primary bank loads.
// Ordinary water animation uses the same global clock on both sides.
static void RefreshContinuousOceanTiles(void)
{
    u16 phase = (gMain.vblankCounter1 >> 4) & 7;
    if (sPrimaryTilesetAnimCallback == TilesetAnim_General)
        CpuCopy16(gTilesetAnims_General_Water[phase], (void *)(BG_VRAM + TILE_OFFSET_4BPP(432)), 30 * TILE_SIZE_4BPP);
    else if (sPrimaryTilesetAnimCallback == TilesetAnim_General_Frlg)
        CpuCopy16(sTilesetAnims_General_Water_Current_LandWatersEdge[phase], (void *)(BG_VRAM + TILE_OFFSET_4BPP(416)), 48 * TILE_SIZE_4BPP);
}
'''
    layer.stage(p,text)
    geometry=json.loads((s/'.journey-world-route-chart').read_text())
    old_projections=copy.deepcopy(geometry['projections'])
    next(p for p in geometry['projections'] if p['map']=='JourneyKantoEasternChannel')['width']=59
    header=rebuild((s/'src/data/journey_world_position.h').read_text(),old_projections,geometry['projections'])
    header,gps=reconcile(header,geometry['projections'],maps)
    layer.stage('src/data/journey_world_position.h',header)
    return layer.finish(route124_mouth=[41,0,10,7],route124_replaced_cells=changed,strait_removed_rocks=rocks,
        north_mouth_width=28,north_mouth_offset=-23,lateral_reefs_closed=True,chart=geometry,gps=gps,
        shared_ocean_palette=True,shared_ocean_tile_addresses=[454,455],shared_ocean_color_indices=[3,4,5,7],retargeted_banks=retargeted,shared_eight_frame_wave_art=True,continuous_animation_clock=True,
        weather_and_time_tint_applied_on_primary_switch=True,redraw_on_secondary_bank_switch=True,
        all_port_placements_and_events_preserved=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True)
    print(json.dumps(prepare(p.parse_args().source),indent=2))
