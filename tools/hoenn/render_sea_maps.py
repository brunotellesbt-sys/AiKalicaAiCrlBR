"""Render actual map blockdata and source tilesets; no invented terrain."""
import argparse
import ast
import hashlib
import json
import re
import shutil
import struct
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def _without_comments(text):
    return re.sub(r'/\*.*?\*/|//[^\n]*', '', text, flags=re.S)


def _braced(text, opening):
    """Read a C initializer without confusing nested structs or strings."""
    assert text[opening] == '{'
    depth, quoted, escaped = 0, None, False
    for end in range(opening, len(text)):
        char = text[end]
        if quoted:
            if escaped: escaped = False
            elif char == '\\': escaped = True
            elif char == quoted: quoted = None
            continue
        if char in ('"', "'"): quoted = char
        elif char == '{': depth += 1
        elif char == '}':
            depth -= 1
            if not depth: return text[opening+1:end]
    raise AssertionError('Unclosed native C initializer')


def _field(body, name, default=None):
    match = re.search(r'\.'+re.escape(name)+r'\s*=\s*', body)
    if match is None:
        assert default is not None, ('Native sprite field missing', name)
        return default
    start = match.end(); depth = 0
    for end in range(start, len(body)):
        char = body[end]
        if char in '({[': depth += 1
        elif char in ')}]': depth -= 1
        elif char == ',' and depth == 0: return body[start:end].strip()
    return body[start:].strip()


def _choice(expression):
    expression = expression.strip()
    while expression.startswith('(') and expression.endswith(')'):
        depth = 0
        for index, char in enumerate(expression):
            if char == '(': depth += 1
            elif char == ')': depth -= 1
            if depth == 0: break
        if index != len(expression)-1: break
        expression = expression[1:-1].strip()
    depth, question = 0, None
    for index, char in enumerate(expression):
        if char in '({[': depth += 1
        elif char in ')}]': depth -= 1
        elif char == '?' and depth == 0: question = index
        elif char == ':' and depth == 0 and question is not None:
            condition = _integer(expression[:question])
            return _choice(expression[question+1:index] if condition else expression[index+1:])
    return expression


def _integer(expression):
    """Evaluate only the constant arithmetic used by native frame macros."""
    node = ast.parse(_choice(expression), mode='eval').body
    def visit(item):
        if isinstance(item, ast.Constant) and type(item.value) is int: return item.value
        if isinstance(item, ast.UnaryOp) and isinstance(item.op, ast.USub): return -visit(item.operand)
        if isinstance(item, ast.BinOp):
            left,right = visit(item.left),visit(item.right)
            if isinstance(item.op, ast.Add): return left+right
            if isinstance(item.op, ast.Sub): return left-right
            if isinstance(item.op, ast.Mult): return left*right
            if isinstance(item.op, (ast.Div, ast.FloorDiv)):
                assert right and left % right == 0
                return left//right
        if isinstance(item, ast.Compare) and len(item.ops) == 1 and isinstance(item.ops[0], ast.Eq):
            return int(visit(item.left) == visit(item.comparators[0]))
        raise AssertionError(('Unsupported native constant expression', expression))
    return visit(node)


def _alias(symbol, text):
    seen = set()
    while True:
        assert symbol not in seen, ('Cyclic native graphics alias', symbol)
        seen.add(symbol)
        match = re.search(r'^\s*#define\s+'+re.escape(symbol)+r'\s+(\w+)\s*$', text, re.M)
        if match is None: return symbol
        symbol = match[1]

class MapRenderer:
    def __init__(self,source):
        self.source=Path(source)
        self.layouts={x['id']:x for x in json.loads((self.source/'data/layouts/layouts.json').read_text())['layouts']}
        self.headers=(self.source/'src/data/tilesets/headers.h').read_text()
        self.metas=(self.source/'src/data/tilesets/metatiles.h').read_text()
        self.cache={}
        self.tile_images={}
        self.sprites={}
        self.sprite_sources={}
        self._species_body=None
        self._species_aliases={}

    def sprite_offset(self,graphics_id):
        marker=self.source/'.journey-close-vertical-boats'
        return json.loads(marker.read_text()).get('render_pixel_offsets',{}).get(graphics_id,[0,0]) if marker.exists() else [0,0]

    def sprite(self,graphics_id,frame_index=0):
        key=(graphics_id,frame_index)
        if key in self.sprites:return self.sprites[key]
        assert type(frame_index) is int and frame_index >= 0, ('Invalid native frame', frame_index)
        root=self.source/'src/data/object_events'
        graphics=_without_comments((root/'object_event_graphics.h').read_text())
        pokemon_graphics=self.source/'src/data/graphics/pokemon.h'
        if pokemon_graphics.exists(): graphics+='\n'+_without_comments(pokemon_graphics.read_text())
        species=re.fullmatch(r'OBJ_EVENT_GFX_SPECIES(_SHINY_FEMALE|_SHINY|_FEMALE)?\((\w+)\)',graphics_id)
        if species:
            info,palette_symbol,symbol=self._species_info(species[2],species[1] or '')
        else:
            pointers=_without_comments((root/'object_event_graphics_info_pointers.h').read_text())
            constants=_without_comments((self.source/'include/constants/event_objects.h').read_text())
            matches=re.findall(r'\[(\w+)\]\s*=\s*&([A-Za-z0-9_]+)',pointers)
            direct=[symbol for name,symbol in matches if name==graphics_id]
            if direct: symbol=direct[0]
            else:
                equivalent={symbol for name,symbol in matches if _alias(name,constants)==_alias(graphics_id,constants)}
                assert len(equivalent)==1, ('Unresolved native graphics pointer', graphics_id)
                symbol=equivalent.pop()
            definitions=_without_comments((root/'object_event_graphics_info.h').read_text())
            symbol=_alias(symbol,definitions)
            match=re.search(r'const struct ObjectEventGraphicsInfo '+re.escape(symbol)+r'\s*=\s*\{',definitions)
            assert match, ('Native graphics info missing', symbol)
            info=_braced(definitions,match.end()-1)
            palette_tag=_field(info,'paletteTag')
            palette_table=_without_comments((self.source/'src/event_object_movement.c').read_text())
            palette=re.search(r'\{\s*(gObjectEventPal_\w+),\s*'+re.escape(palette_tag)+r'\s*\}',palette_table)
            assert palette, ('Native object palette missing', palette_tag)
            palette_symbol=palette[1]
        width,height=(_integer(_field(info,field)) for field in ('width','height'))
        assert width>0 and height>0 and width%8==height%8==0
        assert _integer(_field(info,'size'))==width*height//2, ('Native object size differs from its full frame',symbol)
        pic=_field(info,'images')
        tables=_without_comments((root/'object_event_pic_tables.h').read_text())
        followers=root/'object_event_pic_tables_followers.h'
        if followers.exists(): tables+='\n'+_without_comments(followers.read_text())
        pic=_alias(pic,tables)
        match=re.search(r'(?:static\s+)?const struct SpriteFrameImage '+re.escape(pic)+r'\[\]\s*=\s*\{',tables)
        assert match, ('Native frame table missing',pic)
        table=_braced(tables,match.end()-1)
        entries=re.findall(r'\b(overworld_ascending_frames|overworld_frame|obj_frame_tiles)\s*\(([^)]*)\)',table)
        assert entries, ('Unsupported native frame table',pic)
        relative=entries[0][0]=='overworld_ascending_frames'
        assert relative and len(entries)==1 or frame_index<len(entries), ('Native frame index outside table',pic,frame_index)
        macro,args=entries[0 if relative else frame_index]
        args=[arg.strip() for arg in args.split(',')]
        graphic=_alias(args[0],graphics)
        if macro!='obj_frame_tiles':
            # overworld_frame uses these dimensions only to count bytes.
            # Seagallop's 4x16 declaration contains the same 2048-byte frame
            # that its native 64x64 OAM renders; it is not a 32x128 actor.
            assert _integer(args[1])*_integer(args[2])*64==width*height, ('Native frame byte count differs',pic)
        source_frame=frame_index if relative else (_integer(args[3]) if macro=='overworld_frame' else 0)
        path,inline=self._graphic_input(graphic,graphics)
        if inline is None:
            png=self.source/re.sub(r'\.4bpp(?:\.[\w]+)*$','.png',path)
            with Image.open(png) as loaded: original=loaded.copy()
            assert original.mode=='P', ('Native sprite must be indexed',png)
            assert original.width%width==original.height%height==0, ('Partial native source frame',png)
            assert source_frame<(original.width//width)*(original.height//height), ('Native frame outside source sheet',pic,source_frame)
            left=(source_frame%(original.width//width))*width;top=(source_frame//(original.width//width))*height
            frame=original.crop((left,top,left+width,top+height))
            graphic_source=png.relative_to(self.source).as_posix()
        else:
            assert source_frame*width*height//2+width*height//2<=len(inline), ('Native inline frame outside data',graphic)
            frame=Image.new('P',(width,height));tile_width=width//8
            raw=inline[source_frame*width*height//2:(source_frame+1)*width*height//2]
            for tile in range(len(raw)//32):
                for pixel in range(64):
                    value=(raw[tile*32+pixel//2]>>(4*(pixel%2)))&15
                    frame.putpixel(((tile%tile_width)*8+pixel%8,(tile//tile_width)*8+pixel//8),value)
            graphic_source='src/data/object_events/object_event_graphics.h:'+graphic
        assert max(frame.getdata())<16, ('Native 4bpp index outside palette',graphic)
        palette_path,palette_inline=self._graphic_input(_alias(palette_symbol,graphics),graphics)
        colors,palette_source=self._palette(palette_path,palette_inline)
        frame.putpalette(colors)
        sprite=frame.convert('RGBA')
        for y in range(height):
            for x in range(width):
                if frame.getpixel((x,y))==0:sprite.putpixel((x,y),(0,0,0,0))
        self.sprite_sources[graphics_id+'#'+str(frame_index)]=dict(graphics_info=symbol,frame_table=pic,
            graphic_symbol=graphic,graphic_source=graphic_source,palette_symbol=palette_symbol,
            palette_source=palette_source,width=width,height=height,oam=_choice(_field(info,'oam')),
            table_frame=frame_index,source_frame=source_frame,relative_frames=relative,
            native_graphics_info_sha256=hashlib.sha256(info.encode()).hexdigest(),
            transparent_index=0,source_render_not_emulator=True)
        self.sprites[key]=sprite
        return sprite

    def _species_info(self,name,variant):
        if self._species_body is None:
            candidates=[self.source.parent/'arm-gcc/usr/bin/arm-none-eabi-cpp']
            cpp=next((str(path.resolve()) for path in candidates if path.is_file()),shutil.which('cpp'))
            assert cpp, 'A C preprocessor is required to resolve native species macros'
            result=subprocess.run([cpp,'-E','-P','-iquote','include','-I','.',
                '-DMODERN=1','-DTESTING=0','-DEMERALD','src/pokemon.c'],cwd=self.source,
                check=True,capture_output=True,text=True)
            match=re.search(r'const struct SpeciesInfo gSpeciesInfo\[[^]]*\]\s*=\s*\{',result.stdout)
            assert match, 'Native compiled-configuration species table missing'
            self._species_body=_braced(result.stdout,match.end()-1)
            self._species_aliases=dict(re.findall(r'\b(SPECIES_\w+)\s*=\s*(SPECIES_\w+)\s*[,}]',result.stdout))
        seen=set()
        while 'SPECIES_'+name in self._species_aliases:
            assert name not in seen, ('Cyclic native species enum alias',name)
            seen.add(name)
            name=self._species_aliases['SPECIES_'+name].removeprefix('SPECIES_')
        match=re.search(r'\[SPECIES_'+re.escape(name)+r'\]\s*=\s*\{',self._species_body)
        assert match, ('Species not available in native configuration',name)
        record=_braced(self._species_body,match.end()-1)
        female='_FEMALE' in variant; shiny='_SHINY' in variant
        info_field='overworldDataFemale' if female and _field(record,'overworldDataFemale','NULL')!='NULL' else 'overworldData'
        raw_info=_field(record,info_field)
        assert raw_info.startswith('{') and raw_info.endswith('}')
        info=raw_info[1:-1]
        palette_field=('overworldShinyPalette' if shiny else 'overworldPalette')
        if female and _field(record,'overworldPaletteFemale','NULL')!='NULL': palette_field+='Female'
        palette=_field(record,palette_field,'NULL')
        if palette=='NULL':
            palette_field='shinyPalette' if shiny else 'palette'
            palette=_field(record,palette_field)
        assert re.fullmatch(r'\w+',palette), ('Unsupported native species palette',name,palette)
        return info,palette,'gSpeciesInfo[SPECIES_'+name+'].'+info_field

    def _graphic_input(self,symbol,graphics):
        match=re.search(r'\b(u8|u16|u32)\s+'+re.escape(symbol)+r'\s*\[\]\s*=\s*(?:INCBIN_\w+\("([^"]+)"\)|\{([^}]+)\})',graphics,re.S)
        assert match, ('Native indexed source missing',symbol)
        if match[2]: return match[2],None
        values=[_integer(value.strip()) for value in match[3].split(',') if value.strip()]
        bits=int(match[1][1:]);code={8:'B',16:'H',32:'I'}[bits]
        assert all(0<=value<1<<bits for value in values), ('Invalid native inline graphic',symbol,match[1])
        return None,struct.pack('<'+code*len(values),*values)

    def _palette(self,path,inline):
        if inline is not None:
            raw=inline; origin='inline native u16 palette'
        else:
            palette=(self.source/path).with_suffix('.pal')
            if palette.exists():
                lines=palette.read_text().splitlines();assert lines[:2]==['JASC-PAL','0100']
                colors=[int(value) for line in lines[3:] for value in line.split()]
                assert int(lines[2])>=16 and len(colors)==3*int(lines[2]) and all(0<=value<=255 for value in colors)
                return colors[:48],palette.relative_to(self.source).as_posix()
            raw=(self.source/path).read_bytes();origin=path
        # SpritePalette loads exactly16 colors for these4bpp object frames.
        # Some indexed PNG exports retain256 entries in their INCBIN file;
        # the native loader uses the first bank, rather than rejecting it.
        assert len(raw)>=32 and len(raw)%2==0, ('Incomplete native object palette',origin)
        colors=[((color>>shift)&31)*8 for color in struct.unpack('<16H',raw[:32]) for shift in (0,5,10)]
        return colors,origin

    def tileset(self,name):
        if name in self.cache:return self.cache[name]
        h=re.search(r'const struct Tileset '+name+r'\s*=\s*\{(.*?)\};',self.headers,re.S)[1]
        symbol=re.search(r'\.metatiles\s*=\s*(\w+)',h)[1]
        path=re.search(r'\b'+symbol+r'\[\].*?"([^"]+)"',self.metas)[1]
        folder=(self.source/path).parent
        tiles=Image.open(folder/'tiles.png');assert tiles.mode=='P'
        colors=[]
        for p in sorted((folder/'palettes').glob('*.pal'))[:16]:
            lines=p.read_text().splitlines();colors.append([tuple(map(int,l.split())) for l in lines[3:] if l.strip()])
        words=struct.unpack('<'+'H'*((self.source/path).stat().st_size//2),(self.source/path).read_bytes())
        self.cache[name]=(tiles,colors,words)
        return self.cache[name]
    def render(self,name, values=None, dimensions=None, npcs=True):
        m=json.loads((self.source/f'data/maps/{name}/map.json').read_text());l=self.layouts[m['layout']]
        primary=self.tileset(l['primary_tileset']);secondary=self.tileset(l['secondary_tileset'])
        cutoff=640 if l['layout_version']=='frlg' else 512
        palcut=7 if l['layout_version']=='frlg' else 6
        l=dict(l)
        if dimensions:l['width'],l['height']=dimensions
        if values is None:values=struct.unpack('<'+'H'*(l['width']*l['height']),(self.source/l['blockdata_filepath']).read_bytes())
        result=Image.new('RGB',(l['width']*16,l['height']*16))
        for cell,block in enumerate(values):
            mid=block&1023
            key=(l['primary_tileset'],l['secondary_tileset'],mid)
            if key in self.tile_images:
                result.paste(self.tile_images[key],(cell%l['width']*16,cell//l['width']*16));continue
            tile_image=Image.new('RGB',(16,16))
            words=(primary if mid<cutoff else secondary)[2]
            index=mid if mid<cutoff else mid-cutoff
            entries=words[index*8:(index+1)*8];assert len(entries)==8
            for layer in range(2):
                for quadrant in range(4):
                    entry=entries[layer*4+quadrant];tid=entry&1023;bank=entry>>12
                    tiles=(primary if tid<cutoff else secondary)[0];tid=tid if tid<cutoff else tid-cutoff
                    cols=tiles.width//8; colors=(primary if bank<palcut else secondary)[1][bank]
                    for y in range(8):
                        for x in range(8):
                            xx=7-x if entry&1024 else x; yy=7-y if entry&2048 else y
                            value=tiles.getpixel((tid%cols*8+xx,tid//cols*8+yy))
                            if layer and value==0:continue
                            tile_image.putpixel((quadrant%2*8+x,quadrant//2*8+y),colors[value])
            self.tile_images[key]=tile_image
            result.paste(tile_image,(cell%l['width']*16,cell//l['width']*16))
        if npcs:
            for event in sorted(m['object_events'],key=lambda e:e['y']):
                frame=2 if event['graphics_id']=='OBJ_EVENT_GFX_MR_BRINEYS_BOAT' and event['movement_type'] in ['MOVEMENT_TYPE_FACE_LEFT','MOVEMENT_TYPE_FACE_RIGHT'] else 0
                sprite=self.sprite(event['graphics_id'],frame);dx,dy=self.sprite_offset(event['graphics_id'])
                result.paste(sprite,(event['x']*16+8-sprite.width//2+dx,event['y']*16+16-sprite.height+dy),sprite)
        return result,m

def generate(source, output):
    source=Path(source); output=Path(output);output.mkdir(parents=True,exist_ok=True)
    renderer=MapRenderer(source); layouts=renderer.layouts
    groups={
        'oeste-kanto-hoenn':['JourneyCinnabarSouthSea','JourneyWestRiver','JourneyRustboroCoast','JourneyRustboroGate','JourneyDewfordCoast','JourneyDewfordGate'],
        'leste-hoenn-sevii':['JourneyHoennNorthSea','JourneyHoennMiddleSea','JourneyHoennSouthSea','JourneyPacifidlogSea','JourneyFuchsiaSea'],
        'mar-sevii':['JourneyWorldSea%02d'%i for i in range(10)],
        'cavernas-remotas':[x['map'] for x in json.loads((source/'.journey-sanctuaries').read_text())['sites']],
        'canais-sevii':['JourneyWorldLane'+i for i in ['10','11','20','21','30','31']]}
    report={}
    for title,names in groups.items():
        panels=[]
        for name in names:
            img,m=renderer.render(name)
            img.save(output/(name+'.png'))
            scale=min(1,650/img.width,450/img.height)
            img=img.resize((int(img.width*scale),int(img.height*scale)),Image.Resampling.NEAREST)
            label=name.removeprefix('Journey')
            connections=' / '.join(c['map'].removeprefix('MAP_') for c in (m.get('connections') or []))
            panels.append((img,label,connections))
            report[name]=dict(map_sha256=hashlib.sha256((source/f'data/maps/{name}/map.json').read_bytes()).hexdigest(), blockdata_sha256=hashlib.sha256((source/layouts[m['layout']]['blockdata_filepath']).read_bytes()).hexdigest(), width_tiles=layouts[m['layout']]['width'],height_tiles=layouts[m['layout']]['height'],connections=m.get('connections'),object_events=m['object_events'],terrain_only=False)
        rows=(len(panels)+1)//2
        canvas=Image.new('RGB',(1360,rows*525),(15,32,45));draw=ImageDraw.Draw(canvas)
        font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
        small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12)
        for i,(img,label,connections) in enumerate(panels):
            x=20+(i%2)*680;y=15+(i//2)*525
            draw.text((x,y),label,font=font,fill='white');canvas.paste(img,(x,y+30))
            # Exact identifiers can be long; details also appear in JSON/doc.
            draw.text((x,y+490),connections[:92],font=small,fill=(180,220,240))
        canvas.save(output/(title+'.png'))
    (output/'maps.json').write_text(json.dumps(dict(rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(), maps=report, terrain_only=False, campaign_validation=False),indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',required=True);p.add_argument('--output',required=True);a=p.parse_args();generate(a.source,a.output)
