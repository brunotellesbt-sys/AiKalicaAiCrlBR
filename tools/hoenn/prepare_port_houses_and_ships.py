"""Native compact cottages and fully waterborne moorings at the existing ports."""
import argparse,copy,json,re,struct,shutil
from pathlib import Path
from candidate_layer import Layer
from import_native_pier import import_pier
from world_projection import project
from prepare_cinnabar_shore_polish import PRIOR,LAYER as PREVIOUS
LAYER='port-houses-and-ships';PRIOR=PRIOR+[PREVIOUS]

def prepare(source):
 layer=Layer(source,LAYER,PRIOR)
 if old:=layer.existing():return old
 s=layer.source;ld=json.loads((s/'data/layouts/layouts.json').read_text());ls={l['id']:l for l in ld['layouts']};maps={};blocks={};cottages=[];moorings=[];newmaps=[]
 def load(n):
  if n not in maps:maps[n]=json.loads((s/f'data/maps/{n}/map.json').read_text())
  m=maps[n];l=ls[m['layout']];p=l['blockdata_filepath']
  if p not in blocks:blocks[p]=list(struct.unpack('<'+'H'*(l['width']*l['height']),(s/p).read_bytes()))
  return m,l,blocks[p]
 def npc(x,y,gfx='OBJ_EVENT_GFX_SAILOR_FRLG',script='JourneyShipyard_LodgeKeeper',elevation=3):
  return dict(graphics_id=gfx,x=x,y=y,elevation=elevation,movement_type='MOVEMENT_TYPE_FACE_DOWN',movement_range_x=0,movement_range_y=0,trainer_type='TRAINER_TYPE_NONE',trainer_sight_or_berry_tree_id='0',script=script,flag='0')
 donor,dl,dv=load('OneIsland_Frlg');house=[dv[(7+y)*dl['width']+18+x] for y in range(3) for x in range(5)];imports={}
 def cottage(n,x,y):
  m,l,v=load(n);key=l['secondary_tileset']
  if key not in imports:
   ids,files=import_pier(s,key,donor=dl['secondary_tileset'],mids=sorted({t&1023 for t in house}),overrides=layer.outputs);imports[key]=ids
   for p,raw in files.items():layer.stage(p,raw)
  for yy in range(3):
   for xx in range(5):
    at=(y+yy)*l['width']+x+xx;assert v[at]>>12==3,(n,x+xx,y+yy,hex(v[at]),'Cottage must sit on dry land');t=house[yy*5+xx];v[at]=(t&~1023)|imports[key][t&1023]
  name='Journey'+n.removesuffix('_Frlg').replace('_','')+'PortLodge';interior=copy.deepcopy(json.loads((s/'data/maps/OneIsland_House1_Frlg/map.json').read_text()));interior.update(id='MAP_'+name.upper(),name=name,region_map_section=m['region_map_section'],music=m['music'],object_events=[npc(7,5)],coord_events=[],bg_events=[])
  door=[x+1,y+2];wid=len(m['warp_events'])
  for w in interior['warp_events']:w.update(dest_map=m['id'],dest_warp_id=str(wid))
  m['warp_events'].append(dict(x=door[0],y=door[1],elevation=3,dest_map=interior['id'],dest_warp_id='0'));maps[name]=interior;newmaps.append(name)
  layer.stage(f'data/maps/{name}/scripts.inc',name+'_MapScripts::\n\t.byte 0\n')
  cottages.append(dict(map=n,house=[x,y,5,3],door=door,interior=name))
 def moor(n,x,y,gfx='OBJ_EVENT_GFX_MR_BRINEYS_BOAT',size=(32,32),existing=None):
  m,l,v=load(n);w,h=size;cells=[]
  for yy in range((y*16+16-h)//16,y+1):
   for xx in range((x*16+8-w//2)//16,(x*16+8+w//2-1)//16+1):
    assert 0<=xx<l['width'] and 0<=yy<l['height'];at=yy*l['width']+xx;t=v[at]
    assert t>>12==1 or (n=='BattleFrontier_OutsideWest' and t==0x170),(n,xx,yy,hex(t),'Hull must be entirely over existing water')
    v[at]=t|0x400;cells.append([xx,yy])
  o=existing if existing is not None else npc(x,y,gfx,'JourneyCompactPort_Boat',1)
  o.update(x=x,y=y,elevation=1,movement_type='MOVEMENT_TYPE_FACE_LEFT',flag='0')
  if existing is None:m['object_events'].append(o)
  moorings.append(dict(map=n,anchor=[x,y],graphics=gfx,footprint=cells))
 # The seven ports keep their original short vertical pier and exit warp.
 # A dry eastern beach lobe holds a complete native Sevii cottage.
 for island in ['One','Two','Three','Four','Five','Six','Seven']:
  n=island+'Island_Harbor_Frlg';m,l,v=load(n);w=l['width'];oldwarp=v[2*w+8]
  for yy in range(5):
   for xx in range(10,16):v[yy*w+xx]=0x3115
  for yy in range(4):
   for xx in range(6,16):
    if xx>=10 or yy<=2:v[yy*w+xx]=0x3115
  # Complete the outer side and bottom shoreline, retaining all prior land.
  for yy in range(5):v[yy*w+15]=0x3116
  for xx in range(10,16):v[4*w+xx]=0x311D if xx<15 else 0x311E
  v[3*w+10]=0x3115;v[3*w+9]=0x311D;v[2*w+8]=oldwarp
  cottage(n,11,1)
 # Pallet's existing southern yard fits a five-by-three cottage.
 n='PalletTown_Frlg';m,l,v=load(n);w=l['width'];original_height=l['height'];left,right=v[18*w+11],v[18*w+12]
 for yy in [18,19]:
  for xx in range(2,7):v[yy*w+xx]=0x3001
 cottage(n,2,15)
 # Extend the southern sea by two rows, without deleting native shore terrain.
 v.extend([0x112B]*(w*2));l['height']+=2
 # Continue both shoreline walls into the added rows, matching Route21's inlet.
 for yy in range(20,22):
  for xx in range(7):v[yy*w+xx]=0x3001
  v[yy*w+7]=0x112A
  for xx in range(11,w):v[yy*w+xx]=0x3001
  v[yy*w+10]=0x112C
 v[19*w+11]=left;v[19*w+12]=right
 for yy in [18,19]:
  for xx in [8,9,10]:v[yy*w+xx]&=~0x400
 o=next(o for o in m['object_events'] if o['graphics_id']=='OBJ_EVENT_GFX_MR_BRINEYS_BOAT');moor(n,9,20,existing=o)
 # Fuchsia's western beach cottage opens directly onto the existing walkway.
 cottage('Route19_Frlg',9,9)
 # Submarine: one water row between the captain and the hull, six blocked cells.
 n='SootopolisCity';m,l,v=load(n);o=next(o for o in m['object_events'] if o['graphics_id']=='OBJ_EVENT_GFX_JOURNEY_SUBMARINE')
 for yy in [40,41]:
  for xx in [20,21,22]:v[yy*l['width']+xx]&=~0x400
 moor(n,21,40,o['graphics_id'],existing=o)
 # The native Briney boats now remain visible beside their original piers.
 for n,x,y in [('DewfordTown',12,8),('Route104',9,53)]:
  m,l,v=load(n);o=next(o for o in m['object_events'] if o['graphics_id']=='OBJ_EVENT_GFX_MR_BRINEYS_BOAT');moor(n,x,y,existing=o)
 n='PacifidlogTown';m,l,v=load(n);o=next(o for o in m['object_events'] if o['graphics_id']=='OBJ_EVENT_GFX_MR_BRINEYS_BOAT');moor(n,o['x'],o['y'],existing=o)
 # Frontier's existing two-column shoreline opening becomes a short vertical pier.
 n='BattleFrontier_OutsideWest';m,l,v=load(n);ids,files=import_pier(s,l['secondary_tileset'],emerald=True,mids=[0x2F3,0x2F5],overrides=layer.outputs)
 for p,raw in files.items():layer.stage(p,raw)
 v.extend([0x1170]*(l['width']*2));l['height']+=2
 for yy in range(69,73):v[yy*l['width']+19]=0x3000|ids[0x2F3];v[yy*l['width']+20]=0x3000|ids[0x2F5]
 o=next(o for o in m['object_events'] if o['script']=='LavenderNetwork_Service15_12');o.update(x=19,y=71,graphics_id='OBJ_EVENT_GFX_SAILOR',movement_type='MOVEMENT_TYPE_FACE_RIGHT',elevation=3)
 o=next(o for o in m['object_events'] if o['graphics_id']=='OBJ_EVENT_GFX_SS_TIDAL');moor(n,24,73,'OBJ_EVENT_GFX_SS_TIDAL',(96,40),existing=o)
 # Native large Hoenn ships sit inside the existing enclosed harbor water basin.
 # Both maps share this layout; their hulls and gangways consequently align.
 for n in ['SlateportCity_Harbor','LilycoveCity_Harbor']:moor(n,10,9,'OBJ_EVENT_GFX_SS_TIDAL',(96,40))
 # Cover the water-backed notch beneath the eastern pier with a horizontal
 # mooring. Leave the western gangway and its three original warps intact.
 n='VermilionCity_Frlg';m,l,v=load(n)
 moor(n,34,32)
 scripts=(s/'data/scripts/journey_campaign_gates.inc').read_text();a=scripts.index('LavenderNetwork_Destination15::');b=scripts.index('\n\n',a);part=scripts[a:b];part=re.sub(r'(setvar VAR_0x8009, )\d+',r'\g<1>20',part);part=re.sub(r'(setvar VAR_0x800A, )\d+',r'\g<1>71',part);layer.stage('data/scripts/journey_campaign_gates.inc',scripts[:a]+part+scripts[b:])
 p='data/maps/map_groups.json';groups=json.loads((s/p).read_text());group=next(k for k in groups['group_order'] if 'JourneyMossdeepSailorsLodge' in groups[k]);groups[group].extend(newmaps);layer.stage(p,json.dumps(groups,indent=2)+'\n')
 layer.stage('data/event_scripts.s',(s/'data/event_scripts.s').read_text()+''.join('\n\t.include "data/maps/'+n+'/scripts.inc"\n' for n in newmaps))
 layer.stage('data/layouts/layouts.json',json.dumps(ld,indent=2)+'\n')
 for n,m in maps.items():
  if n==donor['name']:continue
  layer.stage(f'data/maps/{n}/map.json',json.dumps(m,indent=2)+'\n')
 for p,v in blocks.items():
  if p==dl['blockdata_filepath']:continue
  layer.stage(p,struct.pack('<'+'H'*len(v),*v))
 # Preserve chart pixels and shared seam positions after extending Pallet.
 allmaps={p.parent.name:json.loads(p.read_text()) for p in (s/'data/maps').glob('*/map.json')};allmaps.update(maps)
 old=json.loads((s/'.journey-world-dex-map').read_text());coords={p['map']:tuple(p['center']) for p in old['projections']};geometry=project(allmaps,ls,coords);layer.stage('src/data/journey_world_position.h',geometry.pop('data'))
 # Keep a small, reversible local checkpoint until the visual review is complete.
 backup=s.parent/'port-houses-baseline';backup.mkdir(exist_ok=True)
 for p in layer.outputs:
  origin=s/p
  if origin.exists():dest=backup/p;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(origin,dest)
 return layer.finish(cottages=cottages,moorings=moorings,pallet_original_height=original_height,pallet_pier_extra_rows=1,pallet_boat_shift=[0,1],sootopolis_clear_water_rows=[38],native_house_reference='OneIsland_Frlg [18..22,7..9]',native_large_ship='OBJ_EVENT_GFX_SS_TIDAL',original_terrain_retained=True,**geometry)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);print(prepare(p.parse_args().source)['layer'])
