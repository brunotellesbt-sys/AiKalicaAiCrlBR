"""Add seven Pallet-style terminals while retaining wide continuous Surf lanes."""
import argparse,copy,json,re,struct
from pathlib import Path
from candidate_layer import Layer
from import_native_pier import import_pier
from prepare_three_harbor_terminals import PRIOR,LAYER as PREVIOUS
from render_sea_maps import MapRenderer

LAYER='sevii-harbors'
PRIOR=PRIOR+[PREVIOUS]
ISLANDS=['One','Two','Three','Four','Five','Six','Seven']
ARRIVAL=(16,13)
CAPTAIN=(16,12)
DOOR=(13,5)
BERTHS=[
    (7,(9,11),(4,11)),
    (10,(8,11),(14,11)),
    (7,(5,11),(11,11)),
    (10,(12,11),(7,11)),
    (8,(10,11),(5,11)),
    (9,(7,11),(13,11)),
    (7,(10,11),(4,11)),
]


def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if old:=layer.existing():return old
    s=layer.source;r=MapRenderer(s)
    data=json.loads((s/'data/layouts/layouts.json').read_text());layouts={l['id']:l for l in data['layouts']}
    def load(n):
        m=json.loads((s/f'data/maps/{n}/map.json').read_text());l=layouts[m['layout']]
        return m,l,list(struct.unpack('<'+'H'*(l['width']*l['height']),(s/l['blockdata_filepath']).read_bytes()))
    first,exterior,original=load('OneIsland_Harbor_Frlg')
    _,donor,lavender=load('JourneyRoute12Shipyard')
    house=[lavender[(35+y)*donor['width']+8+x] for y in range(6) for x in range(7)]
    wood=0x2F4  # Native continuous middle plank, without repeated end posts.
    ids,files=import_pier(s,exterior['secondary_tileset'],donor=donor['secondary_tileset'],mids=sorted({wood}|{v&1023 for v in house}))
    path=next(p for p in files if p.endswith('/metatiles.bin'));attrs_path=path.replace('metatiles.bin','metatile_attributes.bin')
    words=bytearray(files[path]);attrs=bytearray(files[attrs_path]);bridge=640+len(words)//16
    words.extend(words[(ids[wood]-640)*16:(ids[wood]-640+1)*16]);attrs.extend((0x71).to_bytes(4,'little'))
    files[path]=bytes(words);files[attrs_path]=bytes(attrs)
    for p,raw in files.items():layer.stage(p,raw)
    blocks=original.copy();w,h=exterior['width'],exterior['height'];assert [w,h]==[17,13]
    # Clear the original small boat's blocked water before reusing its berth.
    for y in range(3,7):
        for x in range(9,11):
            if blocks[y*w+x]&1023==0x12B:blocks[y*w+x]&=~0x400
    for y in range(6):
        for x in range(7):
            v=house[y*7+x];blocks[y*w+10+x]=(v&~1023)|ids[v&1023]
    for x in range(10,17):blocks[6*w+x]=0x3000|ids[wood]
    for x in range(7,17):blocks[7*w+x]=bridge
    # Remove the former pier's right-hand end posts at the join. All three
    # upper columns use the same continuous middle planks as the main quay.
    for y in range(3,7):
        for x in range(7,10):blocks[y*w+x]=0x3000|ids[wood]
    donor_inside,inside_layout,_=load('JourneyPalletHarbor')
    groups=json.loads((s/'data/maps/map_groups.json').read_text());group=next(g for g in groups['group_order'] if 'JourneyPetalburgHarbor' in groups[g])
    includes=(s/'data/event_scripts.s').read_text();path_scripts='data/scripts/journey_campaign_gates.inc';scripts=(s/path_scripts).read_text();ports=[]
    hull=json.loads((s/'.journey-pallet-harbor').read_text())['hull']
    for i,island in enumerate(ISLANDS):
        name=island+'Island_Harbor_Frlg';city,l,old=load(name);assert l==exterior and old==original
        pid=i+2;room='JourneySevii'+island+'Harbor';mapid='MAP_JOURNEY_SEVII_'+island.upper()+'_HARBOR'
        original_boat=copy.deepcopy(next(o for o in city['object_events'] if o['script']=='JourneyCompactPort_Boat'))
        pier_x,small_xy,medium_xy=BERTHS[i];specific=blocks.copy()
        boat=copy.deepcopy(original_boat);boat.update(x=small_xy[0],y=small_xy[1])
        medium=copy.deepcopy(original_boat);medium.update(graphics_id='OBJ_EVENT_GFX_SEAGALLOP',x=medium_xy[0],y=medium_xy[1],movement_type='MOVEMENT_TYPE_FACE_LEFT')
        extension=[[x,y] for y in range(8,11) for x in (pier_x,pier_x+1)]
        for x,y in extension:specific[y*w+x]=bridge
        outside_hulls=[]
        for o in [boat,medium]:
            sprite=r.sprite(o['graphics_id'],0);dx,dy=r.sprite_offset(o['graphics_id'])
            ox=o['x']*16+8-sprite.width//2+dx;oy=o['y']*16+16-sprite.height+dy
            occupied=sorted({((ox+x)//16,(oy+y)//16) for y in range(sprite.height) for x in range(sprite.width) if sprite.getpixel((x,y))[3]})
            assert min(y for x,y in occupied)>=9,'Keep a full water tile below the upper quay'
            for x,y in occupied:
                assert 0<=x<w and 0<=y<h and specific[y*w+x]>>12==1,(island,o['graphics_id'],x,y,hex(specific[y*w+x]))
                specific[y*w+x]|=0x400
            outside_hulls.append([list(cell) for cell in occupied])
        assert specific[12*w:]==original[12*w:]
        assert all(specific[y*w+x]==original[y*w+x] for y in range(h) for x in range(2))
        out_layout=copy.deepcopy(exterior);out_name='JourneySevii'+island+'Port'
        out_layout.update(id='LAYOUT_JOURNEY_SEVII_'+island.upper()+'_PORT',name=out_name+'_Layout',blockdata_filepath=f'data/layouts/{out_name}/map.bin')
        data['layouts'].append(out_layout);city['layout']=out_layout['id']
        layer.stage(out_layout['blockdata_filepath'],struct.pack('<'+'H'*len(specific),*specific))
        city['object_events']=[boat,medium]
        warp=city['warp_events'][1];assert warp['dest_map'].endswith('PORTLODGE')
        warp.update(x=DOOR[0],y=DOOR[1],dest_map=mapid,dest_warp_id='0')
        layer.stage(f'data/maps/{name}/map.json',json.dumps(city,indent=2)+'\n')
        interior=copy.deepcopy(donor_inside);layout=copy.deepcopy(inside_layout)
        layout.update(id='LAYOUT_JOURNEY_SEVII_'+island.upper()+'_HARBOR',name=room+'_Layout',
                      blockdata_filepath=f'data/layouts/{room}/map.bin',border_filepath=f'data/layouts/{room}/border.bin')
        data['layouts'].append(layout)
        interior.update(id=mapid,name=room,layout=layout['id'],region_map_section=city['region_map_section'])
        captain=next(o for o in interior['object_events'] if o['script']=='Journey_FerryPort18');captain['script']='Journey_FerryPort'+str(pid)
        for warp in interior['warp_events']:warp.update(dest_map=city['id'],dest_warp_id='1')
        layer.stage(layout['blockdata_filepath'],(s/inside_layout['blockdata_filepath']).read_bytes())
        layer.stage(layout['border_filepath'],(s/inside_layout['border_filepath']).read_bytes())
        layer.stage(f'data/maps/{room}/map.json',json.dumps(interior,indent=2)+'\n')
        layer.stage(f'data/maps/{room}/scripts.inc',room+'_MapScripts::\n\t.byte 0\n')
        groups[group].append(room);includes+=f'\n\t.include "data/maps/{room}/scripts.inc"\n'
        a=scripts.index(f'LavenderNetwork_Destination{pid}::\n');b=scripts.index('\n\n',a)
        dest=scripts[a:b].replace(city['id']+')',mapid+')')
        for var,value in [('0x8009',ARRIVAL[0]),('0x800A',ARRIVAL[1])]:
            dest,count=re.subn(r'(setvar VAR_'+var+r', )\d+',lambda m:m[1]+str(value),dest);assert count==1
        scripts=scripts[:a]+dest+scripts[b:]
        ports.append(dict(island=island,exterior=name,exterior_layout=out_layout['id'],interior=room,pid=pid,terminal=[10,0,7,6],door=list(DOOR),arrival=list(ARRIVAL),captain=list(CAPTAIN),
                          original_boat=original_boat,outside_boat=boat,medium_boat=medium,outside_hulls=outside_hulls,
                          pier_x=pier_x,bridge_extension=extension,hull=hull))
    layer.stage('data/layouts/layouts.json',json.dumps(data,indent=2)+'\n')
    layer.stage('data/maps/map_groups.json',json.dumps(groups,indent=2)+'\n')
    layer.stage('data/event_scripts.s',includes);layer.stage(path_scripts,scripts)
    # The existing Cinnabar quay seals the narrow passage around its ferry.
    # Keep all artwork and placements, but allow the native lower Surf layer.
    _,cl,cv=load('CinnabarIsland_Frlg')
    # Resolve the donor folder through its declaration rather than spelling.
    candidate=next(p for p in json.loads((s/'.journey-three-harbor-terminals').read_text())['prepared_sha256']
                   if 'cinnabar' in p and p.endswith('/metatiles.bin'))
    cp=candidate;ca=cp.replace('metatiles.bin','metatile_attributes.bin')
    cw=bytearray((s/cp).read_bytes());cattrs=bytearray((s/ca).read_bytes());cids={}
    for x in range(6,12):
        mid=cv[15*cl['width']+x]&1023
        if mid not in cids:
            cids[mid]=640+len(cw)//16
            cw.extend(cw[(mid-640)*16:(mid-640+1)*16]);cattrs.extend((0x71).to_bytes(4,'little'))
        cv[15*cl['width']+x]=cids[mid]
    layer.stage(cp,cw);layer.stage(ca,cattrs)
    layer.stage(cl['blockdata_filepath'],struct.pack('<'+'H'*len(cv),*cv))
    return layer.finish(ports=ports,surface_connections_unchanged=True,exterior_dimensions_unchanged=True,
                        south_water_lane=[0,12,17,1],west_water_lane=[0,0,2,13],
                        bridge_over_water=[[x,7] for x in range(7,17)],bridge_behavior=0x71,
                        filled_old_boat_gap=[[9,y] for y in range(3,7)],
                        upper_bridge_continuous=[[x,y] for y in range(3,7) for x in range(7,10)],
                        small_boats_repositioned=True,medium_boats_added=True,outside_captains_removed=True,
                        ship_sprite_size=[96,40],atlas_unchanged=True,cinnabar_surf_under_pier=[6,15,6,1])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);print(json.dumps(prepare(p.parse_args().source),indent=2))
