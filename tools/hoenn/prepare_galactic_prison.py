"""Build three sealed Galactic cells and release the prisoners in the finale."""
import argparse,hashlib,io,json,struct
from pathlib import Path
from PIL import Image
from candidate_layer import Layer
from prepare_reproducible_water import PRIOR,LAYER as PREVIOUS

LAYER='galactic-prison';PRIOR=PRIOR+[PREVIOUS]
ROOT=Path(__file__).resolve().parents[2]
BOXES=[(61,59,425,401),(492,59,854,401),(921,59,1284,401),(1350,59,1713,401),
       (61,468,425,818),(492,468,854,818),(921,468,1284,818),(1350,468,1713,818)]


def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if result:=layer.existing():return result
    source=layer.source
    sheet=ROOT/'tools/hoenn/data/galactic-prison-sheet.png';art=Image.open(sheet).convert('RGB')
    props=[art.crop(box).resize((32,32),Image.Resampling.NEAREST) for box in BOXES]
    # Reserve palette index zero for transparent navy behind the energy bars.
    strip=Image.new('RGB',(256,32))
    for i,prop in enumerate(props):strip.paste(prop,(i*32,0))
    quantized=strip.quantize(colors=15,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
    colors=[(0,0,0)]+[tuple(quantized.getpalette()[i:i+3]) for i in range(0,45,3)]
    original=Image.open(source/'data/tilesets/secondary/inside_ship/tiles.png')
    oldtiles=original.width//8*(original.height//8);assert oldtiles==352
    tiles=Image.new('P',(128,240));tiles.putpalette(original.getpalette());tiles.paste(original,(0,0))
    data=list(quantized.get_flattened_data())
    for prop in range(8):
        for ty in range(4):
            for tx in range(4):
                number=oldtiles+prop*16+ty*4+tx
                for y in range(8):
                    for x in range(8):
                        color=data[(ty*8+y)*256+prop*32+tx*8+x]+1
                        rgb=colors[color]
                        # The sheet's darkest navy is empty cage space.
                        if prop in [0,1,4,7] and max(rgb)<60:color=0
                        tiles.putpixel((number%16*8+x,number//16*8+y),color)
    folder='data/tilesets/secondary/journey_galactic_prison'
    buf=io.BytesIO();tiles.save(buf,format='PNG');layer.stage(folder+'/tiles.png',buf.getvalue())
    for i in range(16):
        text=(source/f'data/tilesets/secondary/journey_galactic_ship/palettes/{i:02}.pal').read_text()
        if i==15:text='JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in colors)+'\n'
        layer.stage(folder+f'/palettes/{i:02}.pal',text)
    raw=(source/'data/tilesets/secondary/inside_ship/metatiles.bin').read_bytes()
    metas=list(struct.unpack('<'+'H'*(len(raw)//2),raw));attrs=bytearray((source/'data/tilesets/secondary/inside_ship/metatile_attributes.bin').read_bytes())
    first=len(attrs)//2;assert first==252
    # Four metatiles per 32px prop. Energy lattices use bottom/top layers,
    # so the imprisoned Pokémon remain visible beneath transparent bars.
    for prop in range(8):
        for q in range(4):
            x=q%2*2;y=q//2*2
            quad=[(512+oldtiles+prop*16+(y+dy)*4+x+dx)|(15<<12) for dy,dx in [(0,0),(0,1),(1,0),(1,1)]]
            floor=[(512+oldtiles+3*16+(y+dy)*4+x+dx)|(15<<12) for dy,dx in [(0,0),(0,1),(1,0),(1,1)]]
            metas+=floor+quad if prop in [0,1,4,7] else quad+[0,0,0,0]
            attrs+=struct.pack('<H',0x2000 if prop in [0,1,4,7] else 0)
    layer.stage(folder+'/metatiles.bin',struct.pack('<'+'H'*len(metas),*metas));layer.stage(folder+'/metatile_attributes.bin',bytes(attrs))
    p='src/data/tilesets/graphics.h';text=(source/p).read_text()+f'\nconst u32 gTilesetTiles_JourneyGalacticPrison[] = INCBIN_U32("{folder}/tiles.4bpp.lz");\nconst u16 gTilesetPalettes_JourneyGalacticPrison[][16] = {{\n'+''.join(f' INCBIN_U16("{folder}/palettes/{i:02}.gbapal"),\n' for i in range(16))+'};\n';layer.stage(p,text)
    p='src/data/tilesets/metatiles.h';layer.stage(p,(source/p).read_text()+f'\nconst u16 gMetatiles_JourneyGalacticPrison[] = INCBIN_U16("{folder}/metatiles.bin");\nconst u16 gMetatileAttributes_JourneyGalacticPrison[] = INCBIN_U16("{folder}/metatile_attributes.bin");\n')
    p='src/data/tilesets/headers.h';layer.stage(p,(source/p).read_text()+'''\nconst struct Tileset gTileset_JourneyGalacticPrison = {.isCompressed=TRUE,.isSecondary=TRUE,.tiles=gTilesetTiles_JourneyGalacticPrison,.palettes=gTilesetPalettes_JourneyGalacticPrison,.metatiles = gMetatiles_JourneyGalacticPrison,.metatileAttributes=gMetatileAttributes_JourneyGalacticPrison,.callback=NULL};\n''')
    p='data/layouts/layouts.json';layouts=json.loads((source/p).read_text());layout=next(l for l in layouts['layouts'] if l['name']=='JourneyGalacticHall_Layout');layout['secondary_tileset']='gTileset_JourneyGalacticPrison';layer.stage(p,json.dumps(layouts,indent=2)+'\n')
    p=layout['blockdata_filepath'];blocks=list(struct.unpack('<'+'H'*(layout['width']*layout['height']),(source/p).read_bytes()));w=layout['width']
    def prop(number,x,y,blocked=False):
        for q in range(4):blocks[(y+q//2)*w+x+q%2]=0x3000|(0xC00 if blocked else 0)|(512+first+number*4+q)
    # Native clear corridors remain unchanged below the detention sector.
    for y in range(2,34):
        for x in range(10,21):blocks[y*w+x]=0x3000|(512+first+12+(y%2)*2+x%2)
    cells=[]
    for center in [6,15,24]:
        cells.append(dict(center=[center,4],bounds=[center-3,1,center+3,6]))
        for y in range(1,7):
            for x in range(center-3,center+4):
                edge=x in [center-3,center+3] or y==1
                number=1 if edge else 4
                blocks[y*w+x]=0x3C00|(512+first+number*4+(y%2)*2+x%2)
        # Control terminal sits outside each locked cell.
        prop(2,center-1,7,True)
        prop(5,center-4,3,True)
    prop(6,14,11);prop(2,4,18,True);prop(2,25,18,True)
    layer.stage(p,struct.pack('<'+'H'*len(blocks),*blocks))
    p='data/maps/JourneyGalacticHall/map.json';m=json.loads((source/p).read_text());m['object_events'][0]['y']=10;layer.stage(p,json.dumps(m,indent=2)+'\n')
    p='src/journey_galactic.c';text=(source/p).read_text().replace('#include "global.h"','#include "global.h"\n#include "fieldmap.h"\n#include "field_camera.h"',1)
    text+='''
void JourneyGalacticCellState(void)
{
    if(VarGet(VAR_JOURNEY_GALACTIC_STATE)<4)return;
    static const u8 centers[]={6,15,24};
    for(u32 i=0;i<3;i++)for(u32 y=2;y<=6;y++)for(u32 x=centers[i]-2;x<=centers[i]+2;x++)
        MapGridSetMetatileIdAt(x+7,y+7,'''+str(512+first+12)+'''+(y%2)*2+x%2);
    DrawWholeMapView();
}
''';layer.stage(p,text)
    p='data/scripts/journey_galactic.inc';text=(source/p).read_text().replace('JourneyGalactic_OnTransition::','JourneyGalactic_OnTransition::\n\tcallnative JourneyGalacticCellState',1)
    text=text.replace('\tsetvar VAR_JOURNEY_GALACTIC_STATE, 4','\tsetvar VAR_JOURNEY_GALACTIC_STATE, 4\n\tplayse SE_M_THUNDERBOLT\n\tcallnative JourneyGalacticCellState\n\tmsgbox JourneyGalactic_Text_CellsOpen',1)
    text+='''
JourneyGalactic_Text_CellsOpen::
\t.string "The containment fields shut down!\\nDIALGA, PALKIA and GIRATINA are free.$"
''';layer.stage(p,text)
    # Canonical JSON also removes recovery-order differences between trees.
    p='src/data/wild_encounters.json';layer.stage(p,json.dumps(json.loads((source/p).read_text()),indent=2,sort_keys=True)+'\n')
    return layer.finish(cells=cells,prisoners=['DIALGA','GIRATINA','PALKIA'],fields_release_at_state=4,
                        sprite_sheet_sha256=hashlib.sha256(sheet.read_bytes()).hexdigest(),source_props=BOXES,source_tiles=oldtiles+128,metatile_base=512+first)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    print(prepare(p.parse_args().source)['layer'])
