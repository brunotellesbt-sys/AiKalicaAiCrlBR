"""Place Mossdeep's terminal and eastward pier at the user's tile bounds."""
import argparse,copy,json,re,struct
from pathlib import Path
from candidate_layer import Layer
from import_native_pier import import_pier
from render_sea_maps import MapRenderer
from prepare_three_harbor_terminals import PRIOR,LAYER as PREVIOUS
LAYER='mossdeep-harbor';PRIOR=PRIOR+[PREVIOUS]
EXTERIOR='MossdeepCity';HARBOR='JourneyMossdeepHarbor';MAP='MAP_JOURNEY_MOSSDEEP_HARBOR'
TERMINAL=(3,26,5,5);DOOR=(5,30);ARRIVAL=(16,13)


def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if old:=layer.existing():return old
    s=layer.source;r=MapRenderer(s)
    data=json.loads((s/'data/layouts/layouts.json').read_text());layouts={l['id']:l for l in data['layouts']}
    def load(name):
        m=json.loads((s/f'data/maps/{name}/map.json').read_text());l=layouts[m['layout']]
        return m,l,list(struct.unpack('<'+'H'*(l['width']*l['height']),(s/l['blockdata_filepath']).read_bytes()))
    city,l,v=load(EXTERIOR);before=v.copy();w=l['width']
    _,donor,dv=load('SlateportCity')
    house=[dv[(7+y)*donor['width']+25+x] for y in range(6) for x in range(7)]
    used=set()
    for shared in layouts.values():
        if shared['secondary_tileset']!=l['secondary_tileset']:continue
        for field in ['blockdata_filepath','border_filepath']:
            raw=(s/shared[field]).read_bytes();used.update(b&1023 for b in struct.unpack('<'+'H'*(len(raw)//2),raw))
    free=[i for i in range(512,512+len(r.tileset(l['secondary_tileset'])[2])//8) if i not in used]
    donor_ids=sorted({b&1023 for b in house});slots=free[:len(donor_ids)]
    ids,files=import_pier(s,l['secondary_tileset'],emerald=True,donor=donor['secondary_tileset'],donor_emerald=True,mids=donor_ids,transparent_colors={2:{1,2,3,4}},metatile_slots=slots)
    meta=next(p for p in files if p.endswith('/metatiles.bin'));attr=meta.replace('metatiles.bin','metatile_attributes.bin')
    words=bytearray(files[meta]);attrs=bytearray(files[attr]);primary=r.tileset(l['primary_tileset'])[2]
    # The five-wide facade keeps both complete windows, the doorway and roof corners.
    cols=[0,1,3,5,6];rows=[0,1,3,4,5]
    for x in cols:
        mid=ids[house[x]&1023];struct.pack_into('<4H',words,(mid-512)*16,*primary[0x124*8:0x124*8+4])
    def native_words(y,x):return list(struct.unpack_from('<8H',words,(ids[house[y*7+x]&1023]-512)*16))
    custom={}
    for dest,a,b in [(1,1,2),(3,4,5)]:
        left,right=native_words(4,a),native_words(4,b);mid=free[len(donor_ids)+len(custom)]
        struct.pack_into('<8H',words,(mid-512)*16,*[left[q+1] if q%2==0 else right[q-1] for q in range(8)])
        at=(ids[house[4*7+1]&1023]-512)*2;attrs[(mid-512)*2:(mid-511)*2]=attrs[at:at+2];custom[dest]=0x400|mid
    assert 512+len(words)//16<=1024
    files[meta]=bytes(words);files[attr]=bytes(attrs)
    for path,raw in files.items():layer.stage(path,raw)
    def put(x,y,b):v[y*w+x]=b
    native=struct.unpack('<3200H',(Path(__file__).parent/'data/mossdeep-before-dock.bin').read_bytes())
    # Restore the retired south-facing pier to the original complete sand/water rim.
    for y in range(31,34):
        for x in (4,5):put(x,y,native[y*w+x])
    boat=next(o for o in city['object_events'] if o['script']=='JourneyCompactPort_Boat')
    for y in range(boat['y']-2,boat['y']+1):
        for x in range(boat['x']-2,boat['x']+3):
            if v[y*w+x]>>12==1:put(x,y,v[y*w+x]&~0x400)
    tx,ty,tw,th=TERMINAL
    for y,row in enumerate(rows):
        for x,col in enumerate(cols):
            b=house[row*7+col];put(tx+x,ty+y,custom[x] if row==4 and x in custom else (b&~1023)|ids[b&1023])
    # A complete sand lip links the front door to the horizontal pier without grass.
    put(7,31,0x31A6);put(8,31,0x31A7)
    # Match the two shoreline cells to the reference tiles selected by the user.
    put(3,32,v[32*w+4]);put(6,32,v[31*w+9])
    pier=[]
    for y in (29,30):
        for x in range(8,12):
            put(x,y,0x33CC if x==8 else 0x33CE if x==11 else 0x33CD);pier.append([x,y])
    city['object_events']=[o for o in city['object_events'] if o['script']!='Journey_FerryPort16']
    boat.update(graphics_id='OBJ_EVENT_GFX_SEAGALLOP',x=14,y=32,movement_type='MOVEMENT_TYPE_FACE_LEFT')
    sprite=r.sprite(boat['graphics_id']);ox,oy=boat['x']*16+8-sprite.width//2,boat['y']*16+16-sprite.height
    hull=sorted({((ox+x)//16,(oy+y)//16) for y in range(sprite.height) for x in range(sprite.width) if sprite.getpixel((x,y))[3]})
    for x,y in hull:
        assert v[y*w+x]>>12==1,('Boat overlaps land',x,y)
        put(x,y,v[y*w+x]|0x400)
    occupied={(x,y) for y in range(26,31) for x in range(3,8)}|set(map(tuple,pier))|set(hull)
    assert all((o['x'],o['y']) not in occupied for o in city['object_events'] if o is not boat)
    warp=next(p for p in city['warp_events'] if p['dest_map']=='MAP_JOURNEYMOSSDEEPSAILORSLODGE');index=city['warp_events'].index(warp)
    warp.update(x=DOOR[0],y=DOOR[1],elevation=0,dest_map=MAP,dest_warp_id='0')
    layer.stage(l['blockdata_filepath'],struct.pack('<'+'H'*len(v),*v));layer.stage(f'data/maps/{EXTERIOR}/map.json',json.dumps(city,indent=2)+'\n')
    inside,il,_=load('JourneyPalletHarbor');inside=copy.deepcopy(inside);il=copy.deepcopy(il)
    original_layout=layouts[inside['layout']]
    il.update(id='LAYOUT_JOURNEY_MOSSDEEP_HARBOR',name=HARBOR+'_Layout',blockdata_filepath=f'data/layouts/{HARBOR}/map.bin',border_filepath=f'data/layouts/{HARBOR}/border.bin');data['layouts'].append(il)
    inside.update(id=MAP,name=HARBOR,layout=il['id'],region='REGION_HOENN',region_map_section=city['region_map_section'],music=city['music'])
    for o in inside['object_events']:
        if o['script']=='Journey_FerryPort18':o['script']='Journey_FerryPort16'
    for p in inside['warp_events']:p.update(dest_map=city['id'],dest_warp_id=str(index))
    for field in ['blockdata_filepath','border_filepath']:layer.stage(il[field],(s/original_layout[field]).read_bytes())
    layer.stage(f'data/maps/{HARBOR}/map.json',json.dumps(inside,indent=2)+'\n');layer.stage(f'data/maps/{HARBOR}/scripts.inc',HARBOR+'_MapScripts::\n\t.byte 0\n')
    lodge,_,_=load('JourneyMossdeepSailorsLodge');lodge['object_events']=[];layer.stage('data/maps/JourneyMossdeepSailorsLodge/map.json',json.dumps(lodge,indent=2)+'\n')
    groups=json.loads((s/'data/maps/map_groups.json').read_text());group=next(k for k in groups['group_order'] if 'JourneyPetalburgHarbor' in groups[k]);groups[group].append(HARBOR)
    layer.stage('data/maps/map_groups.json',json.dumps(groups,indent=2)+'\n');layer.stage('data/layouts/layouts.json',json.dumps(data,indent=2)+'\n')
    layer.stage('data/event_scripts.s',(s/'data/event_scripts.s').read_text()+f'\n\t.include "data/maps/{HARBOR}/scripts.inc"\n')
    path='data/scripts/journey_campaign_gates.inc';text=(s/path).read_text();a=text.index('LavenderNetwork_Destination16::\n');b=text.index('\n\n',a)
    chunk=text[a:b].replace('MAP_MOSSDEEP_CITY)',MAP+')')
    for var,value in [('0x8009',16),('0x800A',13)]:
        chunk,count=re.subn(r'(setvar VAR_'+var+r', )\d+',lambda m:m[1]+str(value),chunk);assert count==1
    layer.stage(path,text[:a]+chunk+text[b:])
    return layer.finish(exterior=EXTERIOR,interior=HARBOR,terminal=list(TERMINAL),door=list(DOOR),pier=pier,arrival=list(ARRIVAL),captain=[16,12],outside_hull=[list(p) for p in hull],inside_hull=json.loads((s/'.journey-pallet-harbor').read_text())['hull'],old_lodge_warp=index,other_ports_preserved=True,changed_terrain=[[i%w,i//w] for i,(a,b) in enumerate(zip(before,v)) if a!=b])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);a=p.parse_args();print(json.dumps(prepare(a.source),indent=2))
