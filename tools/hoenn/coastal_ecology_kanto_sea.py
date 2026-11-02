"""Use the existing ocean palette along the connected Kanto marine coast.

Native FRLG shore and rock underlays still use palette6 for graphics454/455,
while the adjacent open sea uses palette4 for those same animated graphics.
Private tables preserve the upper objects, attributes, callbacks and phases.
Freshwater maps keep their original native banks.
"""
import hashlib
import json
from pathlib import Path
import re
import struct

from badge_story_layer import read
from coastal_ecology_ocean import normalize
from integrated_ocean_seams import _field, _header, _table_path


TARGET_MAPS = (
    'CinnabarIsland_Frlg', 'JourneyRoute12OuterSea', 'JourneyRoute12Shipyard',
    'NavelRock_Exterior_Frlg', 'PalletTown_Frlg', 'Route11_Frlg',
    'Route12_Frlg', 'Route13_Frlg', 'Route14_Frlg', 'Route19_Frlg',
    'Route20_Frlg', 'Route21_North_Frlg', 'Route21_South_Frlg',
    'TwoIsland_Harbor_Frlg', 'VermilionCity_Frlg',
)
FAMILIES = ('CinnabarIsland', 'PalletTown', 'LavenderTown', 'VermilionCity')
PRESERVED_FRESHWATER = ('CeruleanCity_Frlg', 'Route4_Frlg', 'Route6_Frlg',
    'Route10_Frlg', 'Route16_Frlg', 'Route17_Frlg', 'Route18_Frlg',
    'Route24_Frlg', 'Route25_Frlg')
EXPECTED_WORDS = {'CinnabarIsland':8, 'PalletTown':17,
                  'LavenderTown':82, 'VermilionCity':53}


def repair(layer):
    headers_path = 'src/data/tilesets/headers.h'
    definitions_path = 'src/data/tilesets/metatiles.h'
    declarations_path = 'include/tilesets.h'
    layouts_path = 'data/layouts/layouts.json'
    door_path = 'src/field_door.c'
    headers = read(layer,headers_path).decode()
    definitions = read(layer,definitions_path).decode()
    declarations = read(layer,declarations_path).decode()
    doors = read(layer,door_path).decode()
    data = json.loads(read(layer,layouts_path))
    layouts = {row['id']:row for row in data['layouts']}
    original_layouts = {key:dict(row) for key,row in layouts.items()}
    for native,private in [('gTileset_General_Frlg','gTileset_JourneySeviiSea'),
                            ('gTileset_SeviiIslands123','gTileset_JourneySeviiSea123')]:
        old_body,new_body = _header(headers,native),_header(headers,private)
        assert old_body==new_body.replace(_field(new_body,'metatiles'),
                                         _field(old_body,'metatiles')),private
        assert ('if (tileset == &'+private+')\n        return &'+native+';') in doors,private
    primary_body = _header(headers,'gTileset_JourneySeviiSea')
    primary_path = _table_path(definitions,_field(primary_body,'metatiles'))
    primary = read(layer,primary_path)
    primary_words = struct.unpack('<'+'H'*(len(primary)//2),primary)
    water_words = [word for index,word in enumerate(primary_words)
                   if index%8<4 and word&1023 in (454,455)]
    assert water_words and all(word>>12==4 for word in water_words)
    assert not any(index%8<4 and 464<=word&1023<468
                   for index,word in enumerate(primary_words))
    aliases = {}
    tables = []
    staged = {}
    for family in FAMILIES:
        native = 'gTileset_'+family
        private = 'gTileset_JourneyKantoSea'+family
        assert private not in headers and private not in declarations
        body = _header(headers,native)
        old_meta = _field(body,'metatiles')
        new_meta = private.replace('gTileset_','gMetatiles_')
        native_path = _table_path(definitions,old_meta)
        before = read(layer,native_path)
        after,changes = normalize(before)
        assert len(changes)==EXPECTED_WORDS[family], (family,len(changes))
        assert all(a==b or (i%8<4 and a^b==0x2000)
                   for i,(a,b) in enumerate(zip(struct.unpack('<'+'H'*(len(before)//2),before),
                                                  struct.unpack('<'+'H'*(len(after)//2),after))))
        path = str(Path(native_path).with_name('journey_kanto_sea_metatiles.bin'))
        new_body = body.replace('.metatiles = '+old_meta+',', '.metatiles = '+new_meta+',')
        assert new_body != body and new_body.replace(new_meta,old_meta)==body
        headers += '\nconst struct Tileset '+private+' =\n{'+new_body+'};\n'
        definitions += '\nconst u16 '+new_meta+'[] = INCBIN_U16("'+path+'");\n'
        assert declarations.count('\n#endif')==1
        declarations = declarations.replace('\n#endif','\nextern const struct Tileset '+private+';\n#endif')
        aliases[native] = private
        staged[path] = after
        tables.append(dict(native_tileset=native,tileset=private,
            native_metatile_symbol=old_meta,metatile_symbol=new_meta,
            native_path=native_path,path=path,
            before_sha256=hashlib.sha256(before).hexdigest(),
            after_sha256=hashlib.sha256(after).hexdigest(),
            lower_water_words_changed=len(changes),words_changed=changes,
            upper_object_words_and_attributes_unchanged=True,
            graphics_palettes_callbacks_and_all_other_header_fields_unchanged=True))

    function = re.search(r'(static const struct Tileset \*JourneySeviiDoorTileset\([^)]*\)\n\{)(.*?)(    return tileset;\n\})',doors,re.S)
    assert function, 'Existing native door aliases must be retained'
    extra = ''.join('    if (tileset == &'+private+')\n        return &'+native+';\n'
                    for native,private in aliases.items())
    doors = doors[:function.start(3)]+extra+doors[function.start(3):]
    assignments = []
    for name in TARGET_MAPS:
        mapping = json.loads(read(layer,f'data/maps/{name}/map.json'))
        row = layouts[mapping['layout']]
        assert row['layout_version']=='frlg' and row['primary_tileset']=='gTileset_General_Frlg',name
        before = dict(row)
        row['primary_tileset'] = 'gTileset_JourneySeviiSea'
        old_secondary = row['secondary_tileset']
        if name=='NavelRock_Exterior_Frlg':
            assert old_secondary=='gTileset_SeviiIslands123'
            row['secondary_tileset']='gTileset_JourneySeviiSea123'
        elif old_secondary in aliases:
            row['secondary_tileset']=aliases[old_secondary]
        assert all(row[k]==value for k,value in before.items()
                   if k not in ('primary_tileset','secondary_tileset'))
        assignments.append(dict(map=name,layout=row['id'],
            before_primary=before['primary_tileset'],before_secondary=old_secondary,
            primary=row['primary_tileset'],secondary=row['secondary_tileset'],
            blockdata_path=row['blockdata_filepath'],
            blockdata_sha256=hashlib.sha256(read(layer,row['blockdata_filepath'])).hexdigest()))
    modified = {row['layout'] for row in assignments}
    assert all(row==original_layouts[key] for key,row in layouts.items() if key not in modified)
    for name in PRESERVED_FRESHWATER:
        mapping = json.loads(read(layer,f'data/maps/{name}/map.json'))
        assert layouts[mapping['layout']]==original_layouts[mapping['layout']],name
    staged.update({headers_path:headers,definitions_path:definitions,
                   declarations_path:declarations,door_path:doors,
                   layouts_path:json.dumps(data,indent=2)+'\n'})
    for path,content in staged.items():layer.stage(path,content)
    return dict(kind='coastal-ecology-kanto-sea',target_maps=list(TARGET_MAPS),
        layout_assignments=assignments,tables=tables,door_aliases=[dict(original=k,private=v) for k,v in aliases.items()],
        lower_water_words_changed=sum(t['lower_water_words_changed'] for t in tables),
        original_palette=6,ocean_palette=4,water_graphics=[454,455],
        reused_primary='gTileset_JourneySeviiSea',
        preserved_freshwater_maps=list(PRESERVED_FRESHWATER),
        all_native_tables_and_freshwater_layouts_preserved=True,
        all_geometry_objects_events_attributes_animations_and_dive_behaviors_preserved=True,
        changed_paths=sorted(staged))


def render_review(source, output, metadata):
    """Compare whole native source maps using their original and private banks."""
    from PIL import Image, ImageDraw
    from render_sea_maps import MapRenderer

    source,output = Path(source),Path(output)
    output.mkdir(parents=True,exist_ok=True)
    renderer = MapRenderer(source)
    panels = []
    files = []
    for assignment in metadata['layout_assignments']:
        name,key = assignment['map'],assignment['layout']
        row = renderer.layouts[key]
        initial = dict(row)
        images = []
        for state in ('before','after'):
            row['primary_tileset'] = assignment['before_primary' if state=='before' else 'primary']
            row['secondary_tileset'] = assignment['before_secondary' if state=='before' else 'secondary']
            image,_ = renderer.render(name)
            path = output/f'{name}-{state}-whole-source.png'
            image.save(path)
            files.append(dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
            image.thumbnail((300,280))
            images.append(image)
        row.update(initial)
        panel = Image.new('RGB',(616,310),'#17232b')
        draw = ImageDraw.Draw(panel)
        for index,(state,image) in enumerate(zip(('before','after'),images)):
            panel.paste(image,(index*308,26))
            draw.text((index*308+3,6),f'{name}: {state} source',fill='white')
        panels.append(panel)
    for page in range(0,len(panels),6):
        selected = panels[page:page+6]
        contact = Image.new('RGB',(1232,310*((len(selected)+1)//2)),'#17232b')
        for index,panel in enumerate(selected):contact.paste(panel,((index%2)*616,(index//2)*310))
        path = output/f'Kanto-marine-whole-source-comparison-{page//6+1}.png'
        contact.save(path)
        files.append(dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    return files
