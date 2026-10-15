"""Finish the requested boat orientations and retain native story transport IDs."""
import argparse,copy,json,struct
from pathlib import Path
from candidate_layer import Layer
from world_projection import project
from prepare_final_port_alignment import PRIOR,LAYER as PREVIOUS
LAYER='port-orientation-finish';PRIOR=PRIOR+[PREVIOUS]
def prepare(source):
 layer=Layer(source,LAYER,PRIOR)
 if old:=layer.existing():return old
 s=layer.source;ld=json.loads((s/'data/layouts/layouts.json').read_text());ls={l['id']:l for l in ld['layouts']};maps={};blocks={}
 def load(n):
  if n not in maps:maps[n]=json.loads((s/f'data/maps/{n}/map.json').read_text())
  m=maps[n];l=ls[m['layout']];p=l['blockdata_filepath']
  if p not in blocks:
   raw=(s/p).read_bytes();blocks[p]=list(struct.unpack('<'+'H'*(len(raw)//2),raw))
  return m,l,blocks[p]
 n='PalletTown_Frlg';m,l,v=load(n);w=l['width'];left,right=v[17*w+10],v[17*w+12]
 # One more column west into the existing sea, retaining the east-bank house.
 for yy in [17,18]:
  for xx in range(9,13):v[yy*w+xx]=left if xx==9 else right if xx==12 else (left&~1023)|((left&1023)+1)
 # The rightward boat move needs one additional water row to keep its entire
 # hull below the extended pier. Continue the original land and inlet walls.
 v.extend([0x3001]*7+[0x112A,0x112B,0x112B,0x112C]+[0x3001]*(w-11));l['height']+=1
 for yy in [18,19]:
  for xx in [7,8,9]:
   if v[yy*w+xx]>>12==1:v[yy*w+xx]&=~0x400
 o=next(o for o in m['object_events'] if o['graphics_id']=='OBJ_EVENT_GFX_MR_BRINEYS_BOAT');o.update(x=9,y=20)
 for yy in [19,20]:
  for xx in [8,9,10]:assert v[yy*w+xx]>>12==1;v[yy*w+xx]|=0x400
 for island in ['One','Two','Three','Four','Five','Six','Seven']:
  m,_,_=load(island+'Island_Harbor_Frlg');next(o for o in m['object_events'] if o['graphics_id']=='OBJ_EVENT_GFX_MR_BRINEYS_BOAT')['movement_type']='MOVEMENT_TYPE_FACE_DOWN'
 # Preserve Briney's original object ID, starting cell and story flag. The
 # permanent local ferry has its own vertical boat beside the western pier tip.
 m,_,_=load('Route104');o=next(o for o in m['object_events'] if o['graphics_id']=='OBJ_EVENT_GFX_MR_BRINEYS_BOAT');decor=copy.deepcopy(o);decor.pop('local_id',None);decor.update(movement_type='MOVEMENT_TYPE_FACE_DOWN',script='JourneyCompactPort_Boat',flag='0');o.update(x=12,y=54,movement_type='MOVEMENT_TYPE_FACE_UP',script='0x0',flag='FLAG_HIDE_ROUTE_104_MR_BRINEY_BOAT');m['object_events'].append(decor)
 m,_,_=load('DewfordTown')
 for o in m['object_events']:
  if o['script']=='LavenderNetwork_Service9_8':o['script']='DewfordTown_EventScript_Briney'
 # One permanent large ship per harbor; reuse the native story object instead
 # of leaving a second hull that could appear when its old hide flag clears.
 for n,obsolete in [('SlateportCity_Harbor','LavenderNetwork_Service1_0'),('LilycoveCity_Harbor','LavenderNetwork_Service10_10')]:
  m,_,_=load(n);ships=[o for o in m['object_events'] if o['graphics_id']=='OBJ_EVENT_GFX_SS_TIDAL'];assert len(ships)==2
  native,decor=ships;native.update(x=decor['x'],y=decor['y'],elevation=1,movement_type=decor['movement_type'],flag='0',script='JourneyCompactPort_Boat');m['object_events'].remove(decor)
  for o in m['object_events']:
   if o['script']==obsolete:o['script']='JourneyHarbor_Worker'
 p='data/scripts/journey_campaign_gates.inc';layer.stage(p,(s/p).read_text()+'\nJourneyHarbor_Worker::\n\tmsgbox JourneyHarbor_WorkerText, MSGBOX_NPC\n\tend\nJourneyHarbor_WorkerText::\n\t.string "Speak to the captain near the\\nentrance to arrange your voyage.$"\n')
 layer.stage('data/layouts/layouts.json',json.dumps(ld,indent=2)+'\n')
 for n,m in maps.items():layer.stage(f'data/maps/{n}/map.json',json.dumps(m,indent=2)+'\n')
 for p,v in blocks.items():layer.stage(p,struct.pack('<'+'H'*len(v),*v))
 old=json.loads((s/'.journey-final-port-alignment').read_text());allmaps={p.parent.name:json.loads(p.read_text()) for p in (s/'data/maps').glob('*/map.json')};allmaps.update(maps);coords={p['map']:tuple(p['center']) for p in old['projections']};geometry=project(allmaps,ls,coords);layer.stage('src/data/journey_world_position.h',geometry.pop('data'))
 return layer.finish(cottages=old['cottages'],pallet_horizontal_pier=[9,17,4,2],pallet_boat=[9,20],pallet_rightward_boat_shift=1,pallet_house=old['pallet_house'],sevii_vertical_boats=True,petalburg_vertical_boat=[9,52],native_briney_story_boat_preserved=True,one_large_ship_and_world_ferry_per_harbor=True,fuchsia_preserved=True,**geometry)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);print(prepare(p.parse_args().source)['layer'])
