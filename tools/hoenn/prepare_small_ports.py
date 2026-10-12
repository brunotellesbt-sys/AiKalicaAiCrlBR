"""Add small walkable native wooden docks and moored boats to two Hoenn ports."""
import argparse,hashlib,json,struct,re
from pathlib import Path
from prepare_version_play import PRIOR,LAYER as PREVIOUS
from import_dock_tiles import import_dock
LAYER='small-ports';PRIOR=PRIOR+[PREVIOUS]
def prepare(source):
 source=Path(source);marker=source/('.journey-'+LAYER)
 if marker.exists():
  r=json.loads(marker.read_text())
  for p,h in r['prepared_sha256'].items():assert hashlib.sha256((source/p).read_bytes()).hexdigest()==h,p
  return r
 expected=dict(json.loads((source/'.source-acquired.json').read_text())['sha256'])
 for layer in PRIOR:expected.update(json.loads((source/('.journey-'+layer)).read_text())['prepared_sha256'])
 outputs={};originals={}
 def stage(p,raw):
  old=(source/p).read_bytes() if (source/p).exists() else None;h=hashlib.sha256(old).hexdigest() if old else None
  assert h==expected.get(p),p
  if h:originals[p]=h
  outputs[p]=raw.encode() if isinstance(raw,str) else raw
 ids,files=import_dock(source)
 for p,raw in files.items():stage(p,raw)
 layouts={x['id']:x for x in json.loads((source/'data/layouts/layouts.json').read_text())['layouts']};ports=[]
 for name,pid,x,y,width,captain,arrival,boat in [('MossdeepCity',16,54,35,5,(56,36),(55,36),(60,38)),('PacifidlogTown',11,10,25,5,(12,26),(11,26),(16,28))]:
  p='data/maps/'+name+'/map.json';m=json.loads((source/p).read_text());l=layouts[m['layout']];w,h=l['width'],l['height'];raw=(source/l['blockdata_filepath']).read_bytes();blocks=list(struct.unpack('<'+'H'*(w*h),raw));deck=ids if name=='MossdeepCity' else {i:i for i in ids}
  for dy in range(3):
   for dx in range(width):blocks[(y+dy)*w+x+dx]=0x3000|deck[0x220 if dx==0 else 0x224 if dx==width-1 else 0x221]
  for dx in range(width):blocks[(y+3)*w+x+dx]=0x1000|deck[0x228 if dx==0 else 0x22c if dx==width-1 else 0x229]
  npc=next(o for o in m['object_events'] if o['script']=='Journey_FerryPort'+str(pid));npc.update(x=captain[0],y=captain[1],elevation=3,movement_type='MOVEMENT_TYPE_FACE_DOWN',movement_range_x=0,movement_range_y=0)
  m['object_events'].append(dict(local_id='LOCALID_JOURNEY_PORT_BOAT',graphics_id='OBJ_EVENT_GFX_MR_BRINEYS_BOAT',x=boat[0],y=boat[1],elevation=1,movement_type='MOVEMENT_TYPE_FACE_LEFT',movement_range_x=0,movement_range_y=0,trainer_type='TRAINER_TYPE_NONE',trainer_sight_or_berry_tree_id='0',script='EventScript_TestSignpostMsg',flag='0'))
  stage(p,json.dumps(m,indent=2)+'\n');stage(l['blockdata_filepath'],struct.pack('<'+'H'*len(blocks),*blocks));ports.append(dict(map=name,id=pid,deck=[x,y,width,3],captain=list(captain),arrival=list(arrival),boat=list(boat)))
 p='data/scripts/journey_campaign_gates.inc';t=(source/p).read_text()
 for row in ports:
  a=t.index('LavenderNetwork_Destination'+str(row['id'])+'::');b=t.find('\nJourney_FerryPort',a);b=len(t) if b<0 else b;block=t[a:b]
  block=re.sub(r'(setvar VAR_0x8009, )\d+',lambda m:m[1]+str(row['arrival'][0]),block);block=re.sub(r'(setvar VAR_0x800A, )\d+',lambda m:m[1]+str(row['arrival'][1]),block);t=t[:a]+block+t[b:]
 stage(p,t)
 r=dict(layer=LAYER,ports=ports,existing_ferry_ids_and_menus_preserved=True,boats_moored_against_decks=True,original_sha256=originals,prepared_sha256={p:hashlib.sha256(raw).hexdigest() for p,raw in outputs.items()})
 for p,raw in outputs.items():(source/p).write_bytes(raw)
 marker.write_text(json.dumps(r,indent=2)+'\n');return r
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);a=p.parse_args();print(json.dumps(prepare(a.source),indent=2))
