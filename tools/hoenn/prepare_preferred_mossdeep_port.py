"""Move Mossdeep's small port to its otherwise unused western island."""
import argparse,hashlib,json,re,struct
from pathlib import Path
from prepare_paradox_caves import PRIOR,LAYER as PREVIOUS
LAYER='preferred-mossdeep-port';PRIOR=PRIOR+[PREVIOUS];ROOT=Path(__file__).resolve().parents[2]
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
 layouts={l['id']:l for l in json.loads((source/'data/layouts/layouts.json').read_text())['layouts']};p='data/maps/MossdeepCity/map.json';m=json.loads((source/p).read_text());l=layouts[m['layout']];w=l['width'];raw=(source/l['blockdata_filepath']).read_bytes();blocks=list(struct.unpack('<'+'H'*(len(raw)//2),raw));old=(ROOT/'tools/hoenn/data/mossdeep-before-dock.bin').read_bytes();prior=json.loads((source/'.journey-small-ports').read_text());assert hashlib.sha256(old).hexdigest()==prior['original_sha256'][l['blockdata_filepath']];before=struct.unpack('<'+'H'*(len(old)//2),old)
 for y in range(35,39):
  for x in range(54,59):blocks[y*w+x]=before[y*w+x]
 removed=[]
 for y in range(20,31):
  for x in range(10):
   if blocks[y*w+x] in [0x3308,0x3309,0x3710,0x3711,0x0756]:removed.append([x,y]);blocks[y*w+x]=0x3124
 for y in range(25,28):
  for x in range(2,7):blocks[y*w+x]=0x3000|(966 if x==2 else 968 if x==6 else 967)
 for x in range(2,7):blocks[28*w+x]=0x1000|(969 if x==2 else 971 if x==6 else 970)
 for y in [26,27]:blocks[y*w+7]=0x1170
 captain=next(o for o in m['object_events'] if o['script']=='Journey_FerryPort16');captain.update(x=5,y=26,elevation=3)
 boat=next(o for o in m['object_events'] if o.get('local_id')=='LOCALID_JOURNEY_PORT_BOAT');boat.update(x=7,y=27,elevation=1)
 stage(p,json.dumps(m,indent=2)+'\n');stage(l['blockdata_filepath'],struct.pack('<'+'H'*len(blocks),*blocks))
 p='data/maps/PacifidlogTown/map.json';m=json.loads((source/p).read_text());next(o for o in m['object_events'] if o.get('local_id')=='LOCALID_JOURNEY_PORT_BOAT')['x']=15;stage(p,json.dumps(m,indent=2)+'\n')
 p='data/scripts/journey_campaign_gates.inc';t=(source/p).read_text();a=t.index('LavenderNetwork_Destination16::');b=t.index('Journey_FerryPort17::',a);part=t[a:b];part=re.sub(r'(setvar VAR_0x8009, )\d+',r'\g<1>4',part);part=re.sub(r'(setvar VAR_0x800A, )\d+',r'\g<1>26',part);stage(p,t[:a]+part+t[b:])
 p='include/journey_birth_arrivals.h';t=(source/p).read_text()
 for ident,coords in [('MAP_MOSSDEEP_CITY',[7,27,4,26]),('MAP_PACIFIDLOG_TOWN',[15,28,11,26])]:
  t,n=re.subn(r'\{'+ident+r', \d+, \d+, \d+, \d+, TRUE\}',lambda m:'{'+ident+', '+', '.join(map(str,coords))+', TRUE}',t);assert n==1,ident
 stage(p,t)
 p='src/journey_birth.c';t=(source/p).read_text().replace('if (!(index >= 10 && index <= 16))','if (!(index >= 10 && index <= 16) && index != 29 && index != 31)');stage(p,t)
 r=dict(layer=LAYER,mossdeep_port_on_western_island=True,old_south_dock_removed=True,original_south_coast_restored=True,removed_tree_tiles=removed,ports=[dict(map='MossdeepCity',id=16,captain=[5,26],arrival=[4,26],boat=[7,27]),dict(map='PacifidlogTown',id=11,captain=[12,26],arrival=[11,26],boat=[15,28])],boat_intro_arrivals_use_real_docks=True,original_sha256=originals,prepared_sha256={p:hashlib.sha256(raw).hexdigest() for p,raw in outputs.items()})
 for p,raw in outputs.items():(source/p).write_bytes(raw)
 marker.write_text(json.dumps(r,indent=2)+'\n');return r
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);a=p.parse_args();print(json.dumps(prepare(a.source),indent=2))
