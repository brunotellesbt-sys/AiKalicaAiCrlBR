"""Export named native map motifs with their exact donor data and animation frames."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import unicodedata

from PIL import Image, ImageDraw, ImageFont

from render_sea_maps import MapRenderer


ROOT = Path(__file__).resolve().parents[2]
PARENT_SHA = '08fc8a08b95e8e3a923e3342b4f1a31bbaccd1582cbc67ea010021191c43fd6e'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def four_bpp(image):
    """GBA tile order, two indexed pixels per byte, low nibble first."""
    assert image.mode=='P'
    pixels=[]
    for top in range(0,image.height,8):
        for left in range(0,image.width,8):
            pixels.extend(image.crop((left,top,left+8,top+8)).tobytes())
    assert all(0 <= value < 16 for value in pixels)
    return bytes(pixels[index] | pixels[index+1]<<4 for index in range(0,len(pixels),2))


def definitions():
    # Bounds refer to actual donor map cells, not guessed global metatile IDs.
    result = [
        ('emerald/grama/grama-baixa', 'Grama baixa', 'Route116', [14, 2, 1, 1], 'peca'),
        ('emerald/arvores/arvore-isolada-inteira-2x3', 'Árvore isolada inteira 2×3', 'Route116', [0, 13, 2, 3], 'objeto-inteiro'),
        ('emerald/areia/areia-seca', 'Areia seca', 'Route106', [51, 12, 1, 1], 'peca'),
        ('emerald/praias/mar-aberto', 'Mar aberto', 'Route106', [3, 3, 1, 1], 'peca'),
        ('frlg/grama/grama-baixa', 'Grama baixa', 'SixIsland_Frlg', [8, 3, 1, 1], 'peca'),
        ('frlg/arvores/arvore-isolada-inteira-2x3', 'Árvore isolada inteira 2×3', 'SixIsland_Frlg', [13, 14, 2, 3], 'objeto-inteiro'),
        ('frlg/areia/areia-de-praia', 'Areia de praia', 'Route20_Frlg', [23, 5, 1, 1], 'peca'),
        ('frlg/praias/ilha-de-areia-contorno-fechado', 'Ilha de areia com contorno fechado', 'Route20_Frlg', [20, 3, 9, 7], 'conjunto-inteiro'),
        ('frlg/cavernas/caverna-marinha-montanha-inteira-11x9', 'Caverna marinha: montanha inteira 11×9', 'Route20_Frlg', [67, 6, 11, 9], 'objeto-inteiro'),
        ('emerald/cavernas/entrada-na-encosta-rusturf', 'Entrada na encosta: encaixe de Rusturf', 'Route116', [46, 7, 3, 2], 'encaixe-em-montanha-continua'),
        ('frlg/encostas/face-oeste-com-agua', 'Face oeste com água', 'SevenIsland_Frlg', [1, 10, 2, 1], 'peca-composta'),
        ('frlg/encostas/pe-sudoeste-com-agua', 'Pé sudoeste com água', 'SevenIsland_Frlg', [1, 12, 2, 2], 'canto-completo'),
        ('frlg/encostas/face-sul-com-agua', 'Face sul com água', 'SevenIsland_Frlg', [3, 12, 1, 2], 'peca-composta'),
        ('frlg/encostas/canto-interno-sul-oeste', 'Canto interno: sul para oeste', 'SevenIsland_Frlg', [5, 12, 2, 2], 'canto-completo'),
        ('frlg/encostas/montanha-com-topo-faces-e-cantos', 'Montanha com topo, faces e cantos', 'Route20_Frlg', [67, 6, 11, 9], 'objeto-inteiro'),
    ]
    for title, name, donor, x, y in [
        ('canto-externo-noroeste', 'Canto externo noroeste', 'DewfordTown', 14, 10),
        ('reta-norte', 'Praia reta norte', 'DewfordTown', 15, 10),
        ('canto-externo-nordeste', 'Canto externo nordeste', 'JourneySootopolisSouthChannel', 13, 14),
        ('reta-oeste', 'Praia reta oeste', 'JourneySootopolisSouthChannel', 8, 18),
        ('reta-leste', 'Praia reta leste', 'DewfordTown', 11, 0),
        ('canto-externo-sudoeste', 'Canto externo sudoeste', 'JourneySootopolisSouthChannel', 7, 17),
        ('reta-sul', 'Praia reta sul', 'JourneySootopolisSouthChannel', 10, 20),
        ('canto-externo-sudeste', 'Canto externo sudeste', 'JourneySootopolisSouthChannel', 15, 18),
    ]:
        result.append(('emerald/praias/' + title, name, donor, [x, y, 1, 1], 'peca-de-contorno'))
    for title, name, x, y in [
        ('canto-externo-noroeste', 'Canto externo noroeste', 22, 4),
        ('reta-norte', 'Praia reta norte', 23, 4),
        ('canto-externo-nordeste', 'Canto externo nordeste', 24, 4),
        ('reta-oeste', 'Praia reta oeste', 21, 6),
        ('reta-leste', 'Praia reta leste', 45, 9),
        ('canto-externo-sudoeste', 'Canto externo sudoeste', 21, 8),
        ('reta-sul', 'Praia reta sul', 22, 8),
        ('canto-externo-sudeste', 'Canto externo sudeste', 26, 8),
        ('canto-interno-noroeste', 'Encaixe interno noroeste', 22, 5),
        ('canto-interno-nordeste', 'Encaixe interno nordeste', 24, 5),
    ]:
        result.append(('frlg/praias/' + title, name, 'Route20_Frlg', [x, y, 1, 1], 'peca-de-contorno'))
    return result


def export(source, output):
    source, output = Path(source), Path(output)
    assert digest(source / 'pokeemerald.gba') == PARENT_SHA, 'Use the pinned layer-162 donor snapshot'
    output.mkdir(parents=True, exist_ok=True)
    renderer = MapRenderer(source)
    source_files, entries = {}, []
    native_files = {}

    def native_file(relative,raw,**metadata):
        path=output/relative
        path.parent.mkdir(parents=True,exist_ok=True)
        if relative in native_files:
            assert path.read_bytes()==raw
        else:
            path.write_bytes(raw)
            native_files[relative]=dict(sha256=digest(path),bytes=len(raw),**metadata)
        return relative

    def pin(path):
        path = Path(path)
        relative = path.relative_to(source).as_posix()
        source_files.setdefault(relative, digest(path))
        return relative

    def table(field, layout):
        symbol = layout[field]
        body = re.search(r'const struct Tileset ' + re.escape(symbol) + r'\s*=\s*\{(.*?)\};', renderer.headers, re.S)[1]
        paths = {}
        for key in ('metatiles', 'metatileAttributes'):
            array = re.search(r'\.' + key + r'\s*=\s*(\w+)', body)[1]
            paths[key] = source / re.search(r'\b' + array + r'\[\].*?"([^"]+)"', renderer.metas)[1]
            pin(paths[key])
        gfx, palettes, words = renderer.tileset(symbol)
        folder = paths['metatiles'].parent
        pin(folder / 'tiles.png')
        for palette in (folder / 'palettes').glob('*.pal'):
            pin(palette)
        return words, paths['metatileAttributes'].read_bytes()

    for key, title, donor, bounds, role in definitions():
        mapping_path = source / f'data/maps/{donor}/map.json'
        mapping = json.loads(mapping_path.read_text())
        layout = renderer.layouts[mapping['layout']]
        frlg = layout['layout_version'] == 'frlg'
        cutoff, size = (640, 4) if frlg else (512, 2)
        block_path = source / layout['blockdata_filepath']
        data = struct.unpack('<' + 'H' * (block_path.stat().st_size // 2), block_path.read_bytes())
        x, y, width, height = bounds
        assert 0 <= x < x + width <= layout['width'] and 0 <= y < y + height <= layout['height']
        blocks = [data[yy * layout['width'] + xx] for yy in range(y, y+height) for xx in range(x, x+width)]
        tables = {field: table(field, layout) for field in ('primary_tileset', 'secondary_tileset')}
        cells, dynamic = [], False
        for index, block in enumerate(blocks):
            mid = block & 1023
            field = 'primary_tileset' if mid < cutoff else 'secondary_tileset'
            offset = mid if mid < cutoff else mid - cutoff
            words, attributes = tables[field]
            attr = int.from_bytes(attributes[offset * size:(offset+1) * size], 'little')
            refs = []
            for word in words[offset*8:(offset+1)*8]:
                graphic = word & 1023
                bank=word>>12
                graphic_tileset=layout['primary_tileset' if graphic<cutoff else 'secondary_tileset']
                palette_tileset=layout['primary_tileset' if bank<(7 if frlg else 6) else 'secondary_tileset']
                graphic_image=renderer.tileset(graphic_tileset)[0]
                graphic_index=graphic if graphic<cutoff else graphic-cutoff
                columns=graphic_image.width//8
                tile=graphic_image.crop((graphic_index%columns*8,graphic_index//columns*8,
                                         graphic_index%columns*8+8,graphic_index//columns*8+8))
                native_graphic=native_file(f'native/{layout["layout_version"]}/{graphic_tileset}/graphics/{graphic:03x}.4bpp',
                                          four_bpp(tile),kind='indexed-8x8-graphic',tileset=graphic_tileset,graphic=graphic)
                colors=renderer.tileset(palette_tileset)[1][bank]
                palette=('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,color)) for color in colors)+'\n').encode()
                native_palette=native_file(f'native/{layout["layout_version"]}/{palette_tileset}/palettes/{bank:02}.pal',
                                          palette,kind='palette',tileset=palette_tileset,palette=bank)
                channel = None
                if (frlg and 416 <= graphic < 464) or (not frlg and 432 <= graphic < 462):
                    channel = 'agua'
                elif (frlg and 464 <= graphic < 482) or (not frlg and 464 <= graphic < 474):
                    channel = 'espuma-areia'
                dynamic |= channel is not None
                refs.append(dict(word=f'0x{word:04X}', graphic=graphic, palette=bank,
                                 flip_x=bool(word&1024), flip_y=bool(word&2048), animation=channel,
                                 graphics_tileset=graphic_tileset,palette_tileset=palette_tileset,
                                 native_graphic_file=native_graphic,native_palette_file=native_palette))
            cells.append(dict(local=[index%width,index//width], donor_position=[x+index%width,y+index//width],
                              block=f'0x{block:04X}', metatile=f'0x{mid:03X}', elevation=block>>12,
                              collision=(block>>10)&3, behavior=attr&(511 if frlg else 255),
                              draw_layer=(attr>>(29 if frlg else 12))&3, attribute=f'0x{attr:0{size*2}X}',
                              tileset=layout[field], graphics=refs))
        folder = output / key
        folder.mkdir(parents=True, exist_ok=True)
        image, _ = renderer.render(donor, values=blocks, dimensions=(width,height), npcs=False)
        image.save(folder / 'source.png')
        frames = []
        original_primary = renderer.tileset(layout['primary_tileset'])
        if dynamic:
            frame_count, ticks = (16,8) if frlg else (8,16)
            channels = [(416,48,'general_frlg/anim/water_current_landwatersedge',lambda i:i//2),
                        (464,18,'general_frlg/anim/sandwatersedge',lambda i:i%8)] if frlg else [
                        (432,30,'general/anim/water',lambda i:i),
                        (464,10,'general/anim/sand_water_edge',lambda i:i if i<7 else 0)]
            frame_folder = folder / 'animacao'
            frame_folder.mkdir(exist_ok=True)
            for frame in range(frame_count):
                tiles = original_primary[0].copy()
                for first,count,relative,phase in channels:
                    frame_path = source / f'data/tilesets/primary/{relative}/{phase(frame)}.png'
                    pin(frame_path)
                    native = Image.open(frame_path)
                    native_file(f'native/{layout["layout_version"]}/animation/{relative.split("/")[-1]}/{phase(frame)}.4bpp',
                                four_bpp(native),kind='animation-frame',first_graphic=first,graphic_count=count,
                                donor_file=frame_path.relative_to(source).as_posix(),phase=phase(frame))
                    columns = native.width//8
                    for tile in range(count):
                        piece = native.crop((tile%columns*8,tile//columns*8,tile%columns*8+8,tile//columns*8+8))
                        target = first+tile
                        tiles.paste(piece,(target%(tiles.width//8)*8,target//(tiles.width//8)*8))
                renderer.cache[layout['primary_tileset']] = (tiles,*original_primary[1:])
                renderer.tile_images.clear()
                animated,_ = renderer.render(donor,values=blocks,dimensions=(width,height),npcs=False)
                path = frame_folder / f'{frame:02}.png'
                animated.save(path)
                frames.append(dict(file=path.relative_to(output).as_posix(),tick=frame*ticks,sha256=digest(path)))
            renderer.cache[layout['primary_tileset']] = original_primary
            renderer.tile_images.clear()
            assert len({row['sha256'] for row in frames}) > 1, ('Declared animation is static',key)
        entries.append(dict(id=key,name=title,category=key.split('/')[1],role=role,
                            format=layout['layout_version'],donor_map=donor,donor_bounds=bounds,
                            dimensions_tiles=[width,height],dimensions_pixels=[width*16,height*16],
                            primary_tileset=layout['primary_tileset'],secondary_tileset=layout['secondary_tileset'],
                            donor_map_file=pin(mapping_path),donor_blocks_file=pin(block_path),
                            file=(folder/'source.png').relative_to(output).as_posix(),sha256=digest(folder/'source.png'),
                            native_cells=cells,native_animation=dynamic,animation_frames=frames,
                            animation_note='Frames dos slots nativos; recortes de source, não capturas do emulador.',
                            movement_note='Alturas e colisões são do doador; validar o encaixe e o movimento na ROM destino.'))
    pin(source/'src/data/tilesets/headers.h')
    pin(source/'src/data/tilesets/metatiles.h')
    pin(source/'data/layouts/layouts.json')
    report = dict(schema=1,donor_layer=162,donor_rom_sha256=PARENT_SHA,source_renders_not_emulator_captures=True,
                  tile_ids_are_local_to_tilesets=True,source_files_sha256=source_files,
                  native_files=native_files,entries=entries)
    (output/'catalogo.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    sheet(entries,output)
    (output/'README.md').write_text(readme(entries))
    verify(output)
    return report


def sheet(entries,output):
    cols,cellw,cellh=4,320,230
    canvas=Image.new('RGB',(cols*cellw,((len(entries)+cols-1)//cols)*cellh),'#17232b')
    draw=ImageDraw.Draw(canvas)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12)
    for index,entry in enumerate(entries):
        left,top=index%cols*cellw,index//cols*cellh
        title=entry['format'].upper()+' · '+entry['name']
        draw.text((left+8,top+8),title,font=font,fill='white')
        draw.text((left+8,top+28),entry['role']+' · '+str(entry['dimensions_tiles']),font=font,fill='#b8cbd4')
        image=Image.open(output/entry['file'])
        scale=max(1,min(6,300//image.width,170//image.height))
        image=image.resize((image.width*scale,image.height*scale),Image.Resampling.NEAREST)
        canvas.paste(image,(left+8,top+52))
    canvas.save(output/'catalogo-visual.png')


def readme(entries):
    rows=['# Tiles nativos reutilizáveis\n',
          'Catálogo local com recortes dos tiles reais da camada 162. As imagens são renderizações do source, sem NPCs; não são capturas da ROM.\n',
          '[Catálogo visual](catalogo-visual.png) · [Dados completos](catalogo.json) · [Guia de ajustes](../../docs/AJUSTES-GBA.txt)\n',
          'Os nomes separam **Emerald** de **FRLG**. IDs, paletas, altura e comportamento pertencem ao tileset indicado, não são universais. `catalogo.json` contém mapa doador, coordenadas, oito referências gráficas por metatile e hashes.\n',
          '`native/` conserva os gráficos 8×8 indexados `.4bpp`, as paletas `.pal` e os frames nativos usados. Cada referência aponta para seu arquivo correto. `source.png` é um preview RGB; para implementar, use os dados indexados e preserve atributos, flips e callbacks. Os arquivos de animação declaram slot inicial e quantidade de gráficos no catálogo.\n',
          'Uma **peça de contorno** precisa ser combinada com topo, corpo, pé e vizinhos correspondentes. `objeto-inteiro` identifica árvores e montanhas exportadas com toda a sua composição. A entrada de Rusturf é um encaixe numa montanha contínua, não uma caverna isolada completa.\n',
          'Nas pastas `animacao/`, os PNGs mostram o ciclo dos gráficos nativos. Emerald é amostrado a cada 16 ticks; FRLG a cada 8, conservando a relação 16/8 entre água e espuma. Copiar `source.png` para outro slot não copia o callback de animação. O novo banco privado animado de Dewford, na camada 163, é tratado pelos helpers e provas específicos dessa camada; este catálogo conserva o doador 162.\n',
          '## Exemplos\n',
          '| Nome | Formato | Tipo | Doador (x,y,w,h) | Imagem |\n|---|---|---|---|---|']
    for row in entries:
        rows.append('| '+row['name']+' | '+row['format']+' | '+row['role']+' | '+row['donor_map']+' '+str(row['donor_bounds'])+' | [PNG]('+row['file']+') |')
    rows += ['\n## Regerar e conferir\n',
             '```bash\npython3 tools/hoenn/catalog_common_tiles.py --source .local/sevii-integrated-src --output assets/tiles\npython3 tools/hoenn/catalog_common_tiles.py --verify assets/tiles\n```\n',
             'Consulta curta, sem carregar o catálogo inteiro no contexto:\n\n```bash\npython3 tools/hoenn/catalog_common_tiles.py --find "arvore"\npython3 tools/hoenn/catalog_common_tiles.py --find "frlg praia canto"\n```\n',
             'O exportador exige o SHA do snapshot doador e não modifica o source. A verificação local confere arquivos, hashes, dimensões, matrizes completas e variação dos frames, e recompõe cada preview usando somente os bytes GBA e paletas exportados. Isso não substitui testar colisão, portas, Surf e camadas no mapa destino.\n']
    return '\n'.join(rows)


def verify(output):
    output=Path(output)
    report=json.loads((output/'catalogo.json').read_text())
    assert report['donor_rom_sha256']==PARENT_SHA
    assert len(report['entries'])==len({row['id'] for row in report['entries']})
    assert {'praias','encostas','arvores','areia','grama','cavernas'} <= {row['category'] for row in report['entries']}
    for relative,row in report['native_files'].items():
        path=output/relative
        assert digest(path)==row['sha256'] and path.stat().st_size==row['bytes']
        if row['kind']=='indexed-8x8-graphic':assert row['bytes']==32
        if row['kind']=='animation-frame':assert row['bytes']==row['graphic_count']*32
        if row['kind']=='palette':assert len(path.read_text().splitlines()[3:])==16
    indexed_cache,palette_cache={},{}
    for row in report['entries']:
        path=output/row['file']
        assert digest(path)==row['sha256']
        with Image.open(path) as preview:
            assert list(preview.size)==row['dimensions_pixels']
            expected_preview=preview.convert('RGB').tobytes()
        width,height=row['dimensions_tiles']
        assert len(row['native_cells'])==width*height
        assert {tuple(cell['local']) for cell in row['native_cells']}=={(x,y) for y in range(height) for x in range(width)}
        for frame in row['animation_frames']:
            assert digest(output/frame['file'])==frame['sha256']
            with Image.open(output/frame['file']) as frame_image:
                assert list(frame_image.size)==row['dimensions_pixels']
        for cell in row['native_cells']:
            for graphic in cell['graphics']:
                assert graphic['native_graphic_file'] in report['native_files']
                assert graphic['native_palette_file'] in report['native_files']
        # Reconstruct each preview using ONLY the exported GBA bytes, palettes
        # and words. This catches swapped nibble order, flips, banks and layers.
        rebuilt=Image.new('RGB',tuple(row['dimensions_pixels']))
        for cell in row['native_cells']:
            cx,cy=cell['local']
            for index,graphic in enumerate(cell['graphics']):
                file=graphic['native_graphic_file']
                if file not in indexed_cache:
                    raw=(output/file).read_bytes()
                    indexed_cache[file]=[value for byte in raw for value in (byte&15,byte>>4)]
                pal=graphic['native_palette_file']
                if pal not in palette_cache:
                    palette_cache[pal]=[tuple(map(int,line.split())) for line in (output/pal).read_text().splitlines()[3:]]
                pixels,colors=indexed_cache[file],palette_cache[pal]
                quadrant=index%4
                for yy in range(8):
                    for xx in range(8):
                        px,py=7-xx if graphic['flip_x'] else xx,7-yy if graphic['flip_y'] else yy
                        value=pixels[py*8+px]
                        if index>=4 and value==0:continue
                        rebuilt.putpixel((cx*16+quadrant%2*8+xx,cy*16+quadrant//2*8+yy),colors[value])
        assert rebuilt.tobytes()==expected_preview, ('GBA export cannot reconstruct preview',row['id'])
        if row['native_animation']:
            assert len({frame['sha256'] for frame in row['animation_frames']})>1
        if row['category']=='arvores':
            assert row['dimensions_tiles']==[2,3] and row['role']=='objeto-inteiro'
            expected=['0x1CE','0x1CF','0x1D6','0x1D7','0x1DC','0x1DD'] if row['format']=='emerald' else [
                '0x00E','0x00F','0x01E','0x01F','0x026','0x027']
            assert [cell['metatile'] for cell in row['native_cells']]==expected, ('Incomplete tree',row['id'])
        if row['id']=='frlg/cavernas/caverna-marinha-montanha-inteira-11x9':
            assert row['dimensions_tiles']==[11,9]
            entrance=next(cell for cell in row['native_cells'] if cell['local']==[5,8])
            assert entrance['metatile']=='0x0A9' and entrance['elevation']==3
        if row['id']=='frlg/praias/reta-leste':
            assert row['native_cells'][0]['metatile']=='0x116', 'Wrong corner labelled as straight edge'
    with Image.open(output/'catalogo-visual.png') as visual:
        assert visual.width==1280
    print('Catálogo conferido:',len(report['entries']),'exemplos,',sum(len(row['animation_frames']) for row in report['entries']),'frames')


def find(output,query):
    def normalized(text):
        return ''.join(char for char in unicodedata.normalize('NFD',text.lower())
                       if unicodedata.category(char)!='Mn')
    words=normalized(query).split()
    entries=json.loads((Path(output)/'catalogo.json').read_text())['entries']
    matches=[row for row in entries if all(word in normalized(row['id']+' '+row['name']) for word in words)]
    for row in matches:
        print(json.dumps({key:row[key] for key in ['id','role','donor_map','donor_bounds','dimensions_tiles','file','native_animation']},ensure_ascii=False))
    return matches


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path)
    parser.add_argument('--output',type=Path,default=ROOT/'assets/tiles')
    parser.add_argument('--verify',type=Path)
    parser.add_argument('--find')
    args=parser.parse_args()
    if args.verify:
        verify(args.verify)
    elif args.find:
        find(args.output,args.find)
    else:
        if args.source is None:
            parser.error('--source is required to export')
        export(args.source,args.output)
