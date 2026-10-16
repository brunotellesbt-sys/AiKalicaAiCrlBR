"""Add Slateport terminals to Cinnabar, Cerulean Port and Petalburg Coast."""
import argparse
import copy
import json
import re
import struct
from pathlib import Path

from candidate_layer import Layer
from import_native_pier import import_pier
from prepare_fuchsia_harbor import PRIOR,LAYER as PREVIOUS
from render_sea_maps import MapRenderer

LAYER='three-harbor-terminals'
PRIOR=PRIOR+[PREVIOUS]
ARRIVAL=(16,13)
CAPTAIN=(16,12)
PORTS=[
    dict(name='Cinnabar',exterior='CinnabarIsland_Frlg',interior='JourneyCinnabarHarbor',
         map_id='MAP_JOURNEY_CINNABAR_HARBOR',pid=19,terminal=[4,11,7,4],door=[7,14],boat=[13,18],
         start=[13,13],walk=[[11,13],[11,15],[7,15]],return_walk=[[11,15],[11,13],[13,13]],
         crop=[0,7,24,20],legacy='JourneyCinnabarSailorsLodge'),
    dict(name='Cerulean Port',exterior='Route25_Frlg',interior='JourneyCeruleanHarbor',
         map_id='MAP_JOURNEY_CERULEAN_HARBOR',pid=21,terminal=[61,6,6,4],door=[64,9],boat=[68,12],
         start=[60,10],walk=[[64,10]],return_walk=[[60,10]],
         crop=[50,1,72,20]),
    dict(name='Petalburg Coast',exterior='Route104',interior='JourneyPetalburgHarbor',
         map_id='MAP_JOURNEY_PETALBURG_HARBOR',pid=12,terminal=[15,47,5,4],door=[17,50],boat=[8,51],
         start=[18,52],walk=[[17,52],[17,51]],return_walk=[[17,52],[18,52]],
         crop=[3,44,24,59]),
]


def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if old:=layer.existing():return old
    s=layer.source;r=MapRenderer(s)
    data=json.loads((s/'data/layouts/layouts.json').read_text())
    layouts={l['id']:l for l in data['layouts']}
    def load(n):
        m=json.loads((s/f'data/maps/{n}/map.json').read_text());l=layouts[m['layout']]
        v=list(struct.unpack('<'+'H'*(l['width']*l['height']),(s/l['blockdata_filepath']).read_bytes()))
        return m,l,v
    _,donor,dv=load('SlateportCity')
    house=[dv[(7+y)*donor['width']+25+x] for y in range(6) for x in range(7)]
    donor_inside,donor_layout,_=load('JourneyPalletHarbor')
    groups=json.loads((s/'data/maps/map_groups.json').read_text())
    group=next(k for k in groups['group_order'] if 'JourneyFuchsiaHarbor' in groups[k])
    scripts=(s/'data/scripts/journey_campaign_gates.inc').read_text()
    includes=(s/'data/event_scripts.s').read_text()
    records=[]
    for config in PORTS:
        config=copy.deepcopy(config);name=config['exterior'];m,l,v=load(name);before=v.copy();w=l['width']
        emerald=l['layout_version']=='emerald';water=0x1170 if emerald else 0x112B
        tx,ty,tw,th=config['terminal']
        columns={7:[0,1,2,3,4,5,6],6:[0,1,2,3,5,6],5:[0,1,3,5,6]}[tw]
        # Keep native corners, portholes, door and roof base; shorten only
        # repeated roof rows to fit the exact four-row bounds the user marked.
        facade=[house[y*7+x] for y in [0,3,4,5] for x in columns]
        ids,files=import_pier(s,l['secondary_tileset'],emerald=emerald,
            donor=donor['secondary_tileset'],donor_emerald=True,
            mids=sorted({b&1023 for b in house}),transparent_colors={2:{1,2,3,4}})
        path=next(p for p in files if p.endswith('/metatiles.bin'))
        attrs_path=path.replace('metatiles.bin','metatile_attributes.bin')
        words=bytearray(files[path]);attrs=bytearray(files[attrs_path]);cutoff=512 if emerald else 640
        attrsize=2 if emerald else 4
        primary=r.tileset(l['primary_tileset'])[2]
        # Roof backing follows the actual shore: grass on Briney's plot and
        # Cerulean's landward corner, native ground in Cinnabar, blue at sea.
        for x,value in enumerate(facade[:tw]):
            mid=water&1023
            if name=='Route104' or name=='Route25_Frlg' and x==0:mid=1
            elif name=='CinnabarIsland_Frlg':
                native=struct.unpack('<480H',(Path(__file__).parent/'data/cinnabar-original.bin').read_bytes())
                mid=native[ty*w+tx+x]&1023
            bg=primary[mid*8:mid*8+4]
            assert len(bg)==4
            struct.pack_into('<4H',words,(ids[value&1023]-cutoff)*16,*bg)
        custom_wall={}
        if tw<7:
            def original_words(y,x):
                value=house[y*7+x]&1023
                return list(struct.unpack_from('<8H',words,(ids[value]-cutoff)*16))
            def append(parts):
                value=cutoff+len(words)//16
                words.extend(struct.pack('<8H',*parts))
                source_id=ids[house[4*7+1]&1023]-cutoff
                attrs.extend(attrs[source_id*attrsize:(source_id+1)*attrsize])
                return 0x400|value
            # A porthole spans two source metatiles. Join its two eight-pixel
            # halves into one complete window, rather than dropping a half.
            left,right=original_words(4,1),original_words(4,2)
            custom_wall[1]=append([left[q+1] if q%2==0 else right[q-1] for q in range(8)])
            left,right=original_words(4,4),original_words(4,5)
            custom_wall[tw-2]=append([left[q+1] if q%2==0 else right[q-1] for q in range(8)])
            if tw==6:
                blank=original_words(4,1)
                custom_wall[2]=append([blank[q-q%2] for q in range(8)])
        assert cutoff+len(words)//16<=1024
        files[path]=bytes(words);files[attrs_path]=bytes(attrs)
        for path,raw in files.items():layer.stage(path,raw)
        def put(x,y,value):
            assert 0<=x<w and 0<=y<l['height'],(name,x,y)
            v[y*w+x]=value
        def deck(x0,x1,y):
            # Reuse the exact local native wooden bridge metatiles.
            left,middle,right=(0x3306,0x3307,0x3308) if name=='Route25_Frlg' else (0x32D3,0x32D4,0x32D5) if name=='CinnabarIsland_Frlg' else (0x330C,0x330D,0x330E)
            for x in range(x0,x1+1):put(x,y,left if x==x0 else right if x==x1 else middle)
        old_boat=next(o for o in m['object_events'] if o['script']=='JourneyCompactPort_Boat')
        old_boat=copy.deepcopy(old_boat)
        # Clear only the old added boat's blocked ocean, leaving native vessels
        # and local story characters in their original places.
        for y in range(old_boat['y']-1,old_boat['y']+1):
            for x in range(old_boat['x']-1,old_boat['x']+2):
                if v[y*w+x]&1023==water&1023:put(x,y,v[y*w+x]&~0x400)
        removed_rocks=[]
        if name=='CinnabarIsland_Frlg':
            native=struct.unpack('<480H',(Path(__file__).parent/'data/cinnabar-original.bin').read_bytes())
            for y in range(11,15):
                for x in range(8,12):put(x,y,native[y*w+x])
        for y in range(th):
            for x in range(tw):
                value=facade[y*tw+x]
                put(tx+x,ty+y,custom_wall[x] if y==2 and x in custom_wall else (value&~1023)|ids[value&1023])
        if name=='CinnabarIsland_Frlg':
            deck(7,11,15)
        # Cerulean uses its existing pier, and Petalburg keeps Briney's
        # original deck, boat and the entire rival arrival corridor.
        captain=next(o for o in m['object_events'] if o['script']=='Journey_FerryPort'+str(config['pid']))
        m['object_events'].remove(captain)
        boat=next(o for o in m['object_events'] if o['script']=='JourneyCompactPort_Boat')
        boat.update(graphics_id='OBJ_EVENT_GFX_SEAGALLOP',x=config['boat'][0],y=config['boat'][1],movement_type='MOVEMENT_TYPE_FACE_LEFT')
        sprite=r.sprite(boat['graphics_id'],0)
        ox,oy=boat['x']*16+8-sprite.width//2,boat['y']*16+16-sprite.height
        hull=sorted({((ox+x)//16,(oy+y)//16) for y in range(sprite.height) for x in range(sprite.width) if sprite.getpixel((x,y))[3]})
        for x,y in hull:
            if v[y*w+x]&1023 in (0x1D2,0x1D9,0x1E2) and not emerald:put(x,y,water)
            assert v[y*w+x]>>12==1,(name,'Hull overlaps ground',x,y,hex(v[y*w+x]))
            put(x,y,v[y*w+x]|0x400)
        if name=='Route104':
            rival=next(o for o in m['object_events'] if o['script']=='Route104_EventScript_Rival')
            rival.update(x=17,y=52)  # Same waiting tile selected by the native transition script.
        occupied={(x,y) for y in range(ty,ty+th) for x in range(tx,tx+tw)}|set(hull)
        assert all((o['x'],o['y']) not in occupied for o in m['object_events'] if o is not boat),(name,'Existing NPC covered')
        if config.get('legacy'):
            warp=next(w for w in m['warp_events'] if w['dest_map']=='MAP_JOURNEYCINNABARSAILORSLODGE')
            index=m['warp_events'].index(warp)
            warp.update(x=config['door'][0],y=config['door'][1],elevation=0,dest_map=config['map_id'],dest_warp_id='0')
            old,_,_=load(config['legacy']);old['object_events']=[]
            layer.stage(f'data/maps/{config["legacy"]}/map.json',json.dumps(old,indent=2)+'\n')
        elif name=='Route104':
            index=0
            m['warp_events'][index].update(dest_map=config['map_id'],dest_warp_id='0')
        else:
            index=len(m['warp_events'])
            m['warp_events'].append(dict(x=config['door'][0],y=config['door'][1],elevation=0,dest_map=config['map_id'],dest_warp_id='0'))
        layer.stage(l['blockdata_filepath'],struct.pack('<'+'H'*len(v),*v))
        layer.stage(f'data/maps/{name}/map.json',json.dumps(m,indent=2)+'\n')
        inside=copy.deepcopy(donor_inside);il=copy.deepcopy(donor_layout)
        il.update(id='LAYOUT_'+config['map_id'].removeprefix('MAP_'),name=config['interior']+'_Layout',
            blockdata_filepath=f'data/layouts/{config["interior"]}/map.bin',border_filepath=f'data/layouts/{config["interior"]}/border.bin')
        data['layouts'].append(il)
        inside.update(id=config['map_id'],name=config['interior'],layout=il['id'],region=m.get('region','REGION_HOENN' if emerald else 'REGION_KANTO'),region_map_section=m['region_map_section'],music=m['music'])
        for o in inside['object_events']:
            if o['script']=='Journey_FerryPort18':
                o['script']='ThreeHarbors_PetalburgCaptain' if name=='Route104' else 'Journey_FerryPort'+str(config['pid'])
        for warp in inside['warp_events']:warp.update(dest_map=m['id'],dest_warp_id=str(index))
        layer.stage(il['blockdata_filepath'],(s/donor_layout['blockdata_filepath']).read_bytes())
        layer.stage(il['border_filepath'],(s/donor_layout['border_filepath']).read_bytes())
        layer.stage(f'data/maps/{config["interior"]}/map.json',json.dumps(inside,indent=2)+'\n')
        layer.stage(f'data/maps/{config["interior"]}/scripts.inc',config['interior']+'_MapScripts::\n\t.byte 0\n')
        groups[group].append(config['interior'])
        includes+=f'\n\t.include "data/maps/{config["interior"]}/scripts.inc"\n'
        a=scripts.index('LavenderNetwork_Destination'+str(config['pid'])+'::\n');b=scripts.index('\n\n',a)
        chunk=scripts[a:b].replace(m['id']+')',config['map_id']+')')
        for var,value in [('0x8009',ARRIVAL[0]),('0x800A',ARRIVAL[1])]:
            chunk,count=re.subn(r'(setvar VAR_'+var+r', )\d+',lambda m:m[1]+str(value),chunk);assert count==1
        scripts=scripts[:a]+chunk+scripts[b:]
        config.update(captain=list(CAPTAIN),arrival=list(ARRIVAL),door_warp=index,
            outside_hull=[list(p) for p in hull],inside_hull=json.loads((s/'.journey-pallet-harbor').read_text())['hull'],
            removed_whole_rocks=removed_rocks,changed_terrain=[[i%w,i//w] for i,(a,b) in enumerate(zip(before,v)) if a!=b],
            original_boat=old_boat,medium_boat_sprite_size=[64,64],inside_ship_sprite_size=[96,40])
        records.append(config)
    scripts+='''
ThreeHarbors_PetalburgCaptain::
	lock
	faceplayer
	msgbox LavenderNetwork_ServiceText, MSGBOX_DEFAULT
	closemessage
	multichoice 0, 0, MULTI_LAVENDER_SERVICES, FALSE
	switch VAR_RESULT
	case 0, ThreeHarbors_PetalburgWorld
	case 1, ThreeHarbors_PetalburgLocal
	release
	end
ThreeHarbors_PetalburgWorld::
	release
	goto Journey_FerryPort12
ThreeHarbors_PetalburgLocal::
	warp MAP_ROUTE104_MR_BRINEYS_HOUSE, 255, 5, 7
	waitstate
	release
	end
'''
    layer.stage('data/layouts/layouts.json',json.dumps(data,indent=2)+'\n')
    layer.stage('data/maps/map_groups.json',json.dumps(groups,indent=2)+'\n')
    layer.stage('data/event_scripts.s',includes)
    layer.stage('data/scripts/journey_campaign_gates.inc',scripts)
    return layer.finish(ports=records,existing_npcs_preserved=True,other_ports_preserved=True,
        mr_briney_interior_boat_and_story_preserved=True,atlas_unchanged=True,one_indoor_captain_per_port=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True)
    print(json.dumps(prepare(p.parse_args().source),indent=2))
