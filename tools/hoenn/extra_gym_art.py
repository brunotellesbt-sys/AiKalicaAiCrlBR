"""Pack exact native indoor metatiles into a private Emerald secondary bank.

Each source palette is retained exactly. Floors can use a normal walking
behavior without inheriting tower encounters or cave ice/warp side effects.
"""
import io
import re
import struct
from PIL import Image


class IndoorBank:
    def __init__(self, renderer, name):
        self.r, self.name = renderer, name
        self.tiles = Image.new('P', (128, 256))
        self.tiles.putpalette(renderer.tileset('gTileset_Building')[0].getpalette())
        self.palettes = list(renderer.tileset('gTileset_Building')[1][:6])
        self.graphics, self.metas, self.attrs, self.ids = {}, [], [], {}

    def add(self, source_map, mid, behavior=None, effect=None):
        key = (source_map, mid, behavior, effect)
        if key in self.ids:
            return self.ids[key]
        import json
        m = json.loads((self.r.source/f'data/maps/{source_map}/map.json').read_text())
        layout = self.r.layouts[m['layout']]
        cut = 640 if layout['layout_version'] == 'frlg' else 512
        palcut = 7 if cut == 640 else 6
        primary, secondary = [self.r.tileset(layout[k]) for k in ['primary_tileset', 'secondary_tileset']]
        bank = secondary if mid >= cut else primary
        at = mid-cut if mid >= cut else mid
        name = layout['secondary_tileset' if mid >= cut else 'primary_tileset']
        h = re.search(r'const struct Tileset '+name+r'\s*=\s*\{(.*?)\};', self.r.headers, re.S)[1]
        symbol = re.search(r'\.metatileAttributes\s*=\s*(\w+)', h)[1]
        path = re.search(r'\b'+symbol+r'\[\].*?"([^"]+)"', self.r.metas)[1]
        size = 4 if cut == 640 else 2
        raw = (self.r.source/path).read_bytes()
        attr = int.from_bytes(raw[at*size:(at+1)*size], 'little')
        native_behavior = attr & (511 if cut == 640 else 255)
        assert native_behavior < 256
        attr = (native_behavior if behavior is None else behavior) | (((attr >> (29 if cut == 640 else 12)) & 3) << 12)
        packed = []
        for word in bank[2][at*8:(at+1)*8]:
            tile, pal = word & 1023, word >> 12
            colors = (primary if pal < palcut else secondary)[1][pal]
            if effect:
                def tint(c):
                    rr,gg,bb=c;light=(rr*3+gg*6+bb)//10
                    if effect.startswith('wallfill_'):
                        base={'MORTY':(40,36,56),'WHITNEY':(152,116,64),'STEVEN':(56,68,80),'BUGSY':(88,60,36),
                              'CANDICE':(64,120,168),'CLAIR':(32,52,72),'KAREN':(64,32,80),'OAK':(88,104,120)}[effect[9:]]
                        return base
                    if effect=='snow':return tuple(min(248,v) for v in (210+light//6,220+light//8,232+light//12))
                    if effect=='stone':return (light*3//4,light*3//4, min(248,light*3//4+16))
                    if effect=='slate':return (light//2,light//2+12,min(248,light//2+32))
                    if effect=='carpet':return (min(248,light//2+40),light//4,min(248,light//2+30))
                    if effect=='violet' and rr>gg and gg>=bb:return (rr//2+24,gg//3+12,min(248,bb+56))
                    if effect=='wood':return (min(248,light*3//4+44),light//2+28,light//3+12)
                    if effect=='lab':return (min(248,light//2+112),min(248,light//2+120),min(248,light//2+128))
                    return c
                colors=[tint(c) for c in colors]
            if colors not in self.palettes:
                assert len(self.palettes) < 13, (self.name, 'palette capacity')
                self.palettes.append(colors)
            target_pal = self.palettes.index(colors)
            graphics = (primary if tile < cut else secondary)[0]
            index = tile if tile < cut else tile-cut
            cols = graphics.width//8
            im = graphics.crop((index%cols*8, index//cols*8, index%cols*8+8, index//cols*8+8))
            pixels = im.tobytes()
            if pixels not in self.graphics:
                number = len(self.graphics)
                assert number < 512
                self.graphics[pixels] = number
                self.tiles.paste(im, (number%16*8, number//16*8))
            packed.append((512+self.graphics[pixels]) | (word & 0xC00) | (target_pal << 12))
        result = 512+len(self.attrs)
        self.ids[key] = result
        self.metas.extend(packed)
        self.attrs.append(attr)
        return result

    def stage(self, layer):
        folder = 'data/tilesets/secondary/'+self.name.lower()
        png = io.BytesIO(); self.tiles.save(png, format='PNG')
        layer.stage(folder+'/tiles.png', png.getvalue())
        layer.stage(folder+'/metatiles.bin', struct.pack('<'+'H'*len(self.metas), *self.metas))
        layer.stage(folder+'/metatile_attributes.bin', struct.pack('<'+'H'*len(self.attrs), *self.attrs))
        palettes = self.palettes+[[(0,0,0)]*16]*(16-len(self.palettes))
        for i, colors in enumerate(palettes):
            layer.stage(folder+f'/palettes/{i:02}.pal', 'JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,c)) for c in colors)+'\n')
        symbol = 'JourneyExtra'+self.name
        return (f'const struct Tileset gTileset_{symbol} = {{.isCompressed=TRUE, .isSecondary=TRUE, .tiles=gTilesetTiles_{symbol}, .palettes=gTilesetPalettes_{symbol}, .metatiles=gMetatiles_{symbol}, .metatileAttributes=gMetatileAttributes_{symbol}, .callback=NULL}};\n',
                f'const u32 gTilesetTiles_{symbol}[] = INCBIN_U32("{folder}/tiles.4bpp.lz");\nconst u16 gTilesetPalettes_{symbol}[][16] = {{'+','.join(f'INCBIN_U16("{folder}/palettes/{i:02}.gbapal")' for i in range(16))+'};\n',
                f'const u16 gMetatiles_{symbol}[] = INCBIN_U16("{folder}/metatiles.bin");\nconst u16 gMetatileAttributes_{symbol}[] = INCBIN_U16("{folder}/metatile_attributes.bin");\n')
