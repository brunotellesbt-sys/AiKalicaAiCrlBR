"""Read-only census of native FRLG interior forest newly exposed to ocean.

This intentionally flags context for joined review. It does not rewrite maps
or certify standalone trees, other object types, movement, or unconnected edges.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

from PIL import Image, ImageDraw

from arrival_coast_forest import unpack
from render_sea_maps import MapRenderer

INTERIOR_FOREST = {0x014,0x015,0x01C,0x01D}


def audit(source, original, output, previews=True, layer=None):
    source,original,output=Path(source),Path(original),Path(output)
    output.mkdir(parents=True,exist_ok=True)
    renderer=MapRenderer(source)
    def raw(path): return layer.outputs[path] if layer and path in layer.outputs else (source/path).read_bytes()
    if layer:renderer.layouts={r['id']:r for r in json.loads(raw('data/layouts/layouts.json'))['layouts']}
    maps={p.parent.name:json.loads(p.read_text()) for p in (source/'data/maps').glob('*/map.json')}
    by_id={m['id']:n for n,m in maps.items()}
    enum_text=(source/'include/constants/metatile_behaviors.h').read_text()
    constants={};value=-1
    for name,assigned in re.findall(r'^\s*(MB_\w+)(?:\s*=\s*(0x[\da-fA-F]+|\d+))?\s*[,}]',enum_text,re.M):
        value=int(assigned,0) if assigned else value+1;constants[name]=value
    behavior_text=(source/'src/metatile_behavior.c').read_text()
    surfable={constants[name] for name,body in re.findall(r'\[(MB_\w+)\]\s*=([^,]+),',behavior_text) if 'TILE_FLAG_SURFABLE' in body}
    grids={};attributes={};input_hashes={}
    for path in ('data/layouts/layouts.json','include/constants/metatile_behaviors.h',
                 'src/metatile_behavior.c','src/data/tilesets/headers.h','src/data/tilesets/metatiles.h'):
        input_hashes[path]=hashlib.sha256(raw(path)).hexdigest()
    header_inventory={n:hashlib.sha256((source/f'data/maps/{n}/map.json').read_bytes()).hexdigest() for n in maps}
    original_inventory={p.parent.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (original/'data/maps').glob('*/map.json')}
    def grid(name):
        if name not in grids:
            layout=renderer.layouts[maps[name]['layout']]
            blob=raw(layout['blockdata_filepath'])
            input_hashes[layout['blockdata_filepath']]=hashlib.sha256(blob).hexdigest()
            grids[name]=(layout,unpack(blob))
        return grids[name]
    def wet(name,x,y):
        layout,values=grid(name);word=values[y*layout['width']+x];mid=word&1023
        bank=layout['primary_tileset' if mid<640 else 'secondary_tileset'];index=mid if mid<640 else mid-640
        if bank not in attributes:
            body=re.search(r'const struct Tileset '+bank+r'\s*=\s*\{(.*?)\};',renderer.headers,re.S)[1]
            symbol=re.search(r'\.metatileAttributes\s*=\s*(\w+)',body)[1]
            path=re.search(r'\b'+symbol+r'\[\].*?"([^"]+)"',renderer.metas)[1]
            blob=raw(path);attributes[bank]=blob;input_hashes[path]=hashlib.sha256(blob).hexdigest()
        behavior=int.from_bytes(attributes[bank][index*4:(index+1)*4],'little')&511
        return behavior in surfable
    inspected=[];suspects=[]
    for name,mapping in sorted(maps.items()):
        oldpath=original/f'data/maps/{name}/map.json'
        if not oldpath.exists():continue
        layout,values=grid(name)
        if layout['layout_version']!='frlg' or layout['primary_tileset'] not in ('gTileset_General_Frlg','gTileset_JourneySeviiSea'):continue
        old=json.loads(oldpath.read_text());oldconnections=old.get('connections') or []
        for connection in mapping.get('connections') or []:
            if connection in oldconnections or connection['direction'] not in ('up','down','left','right'):continue
            target=by_id[connection['map']]
            if (original/f'data/maps/{target}/map.json').exists():continue
            other,otherwords=grid(target)
            if other['layout_version']!='frlg' or maps[target]['map_type']!='MAP_TYPE_OCEAN_ROUTE':continue
            width,height=layout['width'],layout['height'];tw,th=other['width'],other['height']
            direction,offset=connection['direction'],connection['offset'];pairs=[]
            if direction in ('up','down'):
                for x in range(max(0,offset),min(width,offset+tw)):
                    pairs.append(((x,0 if direction=='up' else height-1),(x-offset,th-1 if direction=='up' else 0)))
            else:
                for y in range(max(0,offset),min(height,offset+th)):
                    pairs.append(((0 if direction=='left' else width-1,y),(tw-1 if direction=='left' else 0,y-offset)))
            row=dict(map=name,map_id=mapping['id'],target=target,target_map_id=connection['map'],
                direction=direction,offset=offset,boundary_cell_pairs=len(pairs),
                native_map_json_sha256=header_inventory[name],target_map_json_sha256=header_inventory[target],
                original_native_map_json_sha256=original_inventory[name])
            inspected.append(row)
            flagged=[]
            for (x,y),(xx,yy) in pairs:
                word=values[y*width+x]
                if word&1023 in INTERIOR_FOREST and wet(target,xx,yy):
                    flagged.append(dict(cell=[x,y],word=word,neighbor=[xx,yy],neighbor_word=otherwords[yy*tw+xx]))
            if flagged:
                suspects.append(dict(row,cells=flagged,requires_joined_context_review=True,
                    observed_rule='native interior forest immediately touches real surfable neighbor'))
    contact=[]
    if previews:
        for i,row in enumerate(suspects):
            name,target=row['map'],row['target'];layout,_=grid(name);other,_=grid(target)
            direction,offset=row['direction'],row['offset']
            origin=(offset,-other['height']) if direction=='up' else (offset,layout['height']) if direction=='down' else (-other['width'],offset) if direction=='left' else (layout['width'],offset)
            left,top=min(0,origin[0]),min(0,origin[1]);right=max(layout['width'],origin[0]+other['width']);bottom=max(layout['height'],origin[1]+other['height'])
            image=Image.new('RGB',((right-left)*16,(bottom-top)*16),'#263642')
            for n,(x,y) in [(name,(0,0)),(target,origin)]:
                _,values=grid(n);rendered,_=renderer.render(n,values=values,npcs=False);image.paste(rendered,((x-left)*16,(y-top)*16))
            draw=ImageDraw.Draw(image)
            for cell in row['cells']:
                x,y=cell['cell'];draw.rectangle(((x-left)*16,(y-top)*16,(x-left+1)*16-1,(y-top+1)*16-1),outline='red',width=2)
            filename=f'{i:02d}-{name}-{target}-joined-source.png';image.save(output/filename);row['joined_source_review']=filename
            image.thumbnail((390,300));contact.append((name+' / '+target,image))
        if contact:
            sheet=Image.new('RGB',(800,((len(contact)+1)//2)*330),'#222');draw=ImageDraw.Draw(sheet)
            for i,(label,image) in enumerate(contact):
                x=i%2*400;y=i//2*330;draw.text((x,y),label,fill='white');sheet.paste(image,(x,y+22))
            sheet.save(output/'suspects-contact-source.png')
    result=dict(kind='native-frlg-added-ocean-interior-forest-census',read_only=True,
        inspected_added_native_to_generated_ocean_connections=inspected,
        suspect_connections=suspects,suspect_cell_count=sum(len(r['cells']) for r in suspects),
        source_inputs_sha256=input_hashes,
        source_map_headers_inventory_sha256=hashlib.sha256(json.dumps(header_inventory,sort_keys=True).encode()).hexdigest(),
        original_map_headers_inventory_sha256=hashlib.sha256(json.dumps(original_inventory,sort_keys=True).encode()).hexdigest(),
        requires_joined_context_review=True,staged=layer is not None,
        no_automatic_rewrite=True,no_global_complete_object_or_movement_certification=True,
        scope='FRLG native map; added direct cardinal connection to newly generated ocean; interior forest IDs014/015/01C/01D versus actual surfable behavior')
    (output/'forest-seam-census.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True)
    p.add_argument('--original',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--no-previews',action='store_true');p.add_argument('--staged',action='store_true');a=p.parse_args()
    layer=None
    if a.staged:
        from arrival_coast_forest import repair
        from candidate_layer import Layer
        from prepare_arrival_coast_review import LAYER,PRIOR
        layer=Layer(a.source,LAYER,PRIOR);repair(layer)
    r=audit(a.source,a.original,a.output,not a.no_previews,layer)
    print(json.dumps(dict(connections=len(r['inspected_added_native_to_generated_ocean_connections']),suspects=len(r['suspect_connections']),cells=r['suspect_cell_count'],maps=[r['map'] for r in r['suspect_connections']]),indent=2))
