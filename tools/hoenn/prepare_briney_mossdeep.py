"""Transplant Mr Briney's real house and small jetty to Mossdeep's west island."""
import argparse,json,struct
from pathlib import Path
from candidate_layer import Layer
from import_native_pier import import_pier
from prepare_lavender_rotom_room import PRIOR,LAYER as PREVIOUS
LAYER='briney-mossdeep';PRIOR=PRIOR+[PREVIOUS];ROOT=Path(__file__).resolve().parents[2]
def prepare(source):
 layer=Layer(source,LAYER,PRIOR)
 if old:=layer.existing():return old
 s=layer.source;ls={l['id']:l for l in json.loads((s/'data/layouts/layouts.json').read_text())['layouts']};m=json.loads((s/'data/maps/MossdeepCity/map.json').read_text());l=ls[m['layout']];w=l['width'];v=list(struct.unpack('<3200H',(s/l['blockdata_filepath']).read_bytes()));original=struct.unpack('<3200H',(ROOT/'tools/hoenn/data/mossdeep-before-dock.bin').read_bytes())
 for y in range(20,34):
  for x in range(16):
   t=original[y*w+x];v[y*w+x]=0x3124 if t in [0x3308,0x3309,0x3710,0x3711,0x0756] else t
 donor=json.loads((s/'data/maps/Route104/map.json').read_text());dl=ls[donor['layout']];dv=struct.unpack('<3200H',(s/dl['blockdata_filepath']).read_bytes());house=[dv[(47+dy)*40+15+dx] for dy in range(4) for dx in range(5)];pier=[dv[(51+dy)*40+11+dx] for dy in range(3) for dx in range(4)]
 ids,files=import_pier(s,l['secondary_tileset'],emerald=True,donor=dl['secondary_tileset'],mids=sorted({t&1023 for t in house+pier}),donor_emerald=True)
 for p,raw in files.items():layer.stage(p,raw)
 for dy in range(4):
  for dx in range(5):t=house[dy*5+dx];v[(27+dy)*w+2+dx]=(t&~1023)|ids[t&1023]
 for dy in range(3):
  for dx in range(4):
   t=pier[dy*4+dx];v[(30+dy)*w+7+dx]=(t&~1023)|ids[t&1023]
 m['object_events']=[o for o in m['object_events'] if o['graphics_id']!='OBJ_EVENT_GFX_MR_BRINEYS_BOAT']
 captain=next(o for o in m['object_events'] if o['script']=='Journey_FerryPort16');captain.update(x=8,y=31,elevation=4,movement_type='MOVEMENT_TYPE_FACE_RIGHT')
 for warp in m['warp_events']:
  if warp['dest_map']=='MAP_JOURNEYMOSSDEEPSAILORSLODGE':warp.update(x=4,y=30)
 base=dict(captain);base.update(x=12,y=31,elevation=1,graphics_id='OBJ_EVENT_GFX_MR_BRINEYS_BOAT',script='JourneyCompactPort_Boat',movement_type='MOVEMENT_TYPE_FACE_LEFT');m['object_events'].append(base)
 footprint=[]
 for yy in [30,31]:
  for xx in [11,12,13]:
   assert original[yy*w+xx]>>12==1,(xx,yy,hex(original[yy*w+xx]));v[yy*w+xx]=original[yy*w+xx]|0x400;footprint.append([xx,yy])
 layer.stage(l['blockdata_filepath'],struct.pack('<3200H',*v));layer.stage('data/maps/MossdeepCity/map.json',json.dumps(m,indent=2)+'\n')
 p='data/scripts/journey_campaign_gates.inc';text=(s/p).read_text();a=text.index('LavenderNetwork_Destination16::');b=text.index('\n\n',a);chunk=text[a:b].replace('setvar VAR_0x8009, 4','setvar VAR_0x8009, 9').replace('setvar VAR_0x800A, 30','setvar VAR_0x800A, 31');layer.stage(p,text[:a]+chunk+text[b:])
 p='include/journey_birth_arrivals.h';layer.stage(p,(s/p).read_text().replace('{MAP_MOSSDEEP_CITY, 5, 33, 4, 30, TRUE}','{MAP_MOSSDEEP_CITY, 12, 31, 9, 31, TRUE}'))
 # The interior is Mr Briney's cottage, with a permanent boatman and no duplicate ferry.
 p='data/maps/JourneyMossdeepSailorsLodge/map.json';inside=json.loads((s/'data/maps/Route104_MrBrineysHouse/map.json').read_text());prior=json.loads((s/p).read_text());inside.update(id=prior['id'],name=prior['name'],region_map_section=prior['region_map_section'],object_events=prior['object_events'],bg_events=[],coord_events=[])
 for warp in inside['warp_events']:warp.update(dest_map=m['id'],dest_warp_id=str(next(i for i,e in enumerate(m['warp_events']) if e['dest_map']==inside['id'])))
 layer.stage(p,json.dumps(inside,indent=2)+'\n')
 return layer.finish(house_source='Route104',house_source_box=[15,47,5,4],house=[2,27,5,4],pier_source_box=[11,51,4,3],pier=[7,30,4,3],captain=[8,31],arrival=[9,31],boat=[12,31],boat_footprint=footprint,west_island_south_edge=True,existing_land_not_replaced_with_water=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);print(prepare(p.parse_args().source)['layer'])
