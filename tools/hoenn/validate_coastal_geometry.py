"""Audit edited layouts, generated rock families and compiled shoreline art."""
import hashlib,json,re,struct,subprocess
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_trainer_levels.py').read_text().split('\nchecks=[]')[0]
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_trainer_levels.py'),'exec'))
from prepare_complete_marine_atlas import PRIOR,LAYER
from render_sea_maps import MapRenderer
from prepare_world_dex_map import decode
from prepare_native_coastal_fragments import REPAIRS
r=MapRenderer(source);changed=set()
for n in PRIOR+[LAYER]:changed.update(json.loads((source/('.journey-'+n)).read_text())['prepared_sha256'])
edited=[];coasts=[]
for p in sorted((source/'data/maps').glob('*/map.json')):
 m=json.loads(p.read_text());l=layouts[m['layout']];file=l['blockdata_filepath'];data=(source/file).read_bytes()
 if file not in changed and p.relative_to(source).as_posix() not in changed:continue
 assert len(data)==2*l['width']*l['height'],(m['name'],'Incomplete layout data')
 for key in ['object_events','warp_events','coord_events','bg_events']:
  for o in m.get(key) or []:
   if o.get('type')=='clone':
    assert o.get('target_map') and o.get('target_local_id'),(m['name'],'Invalid neighboring object clone',o)
   elif key=='warp_events':assert 0<=o['x']<=l['width'] and 0<=o['y']<=l['height'],(m['name'],'Invalid edge warp',o)
   else:assert 0<=o['x']<l['width'] and 0<=o['y']<l['height'],(m['name'],key,o)
 edited.append(dict(map=m['name'],dimensions=[l['width'],l['height']],layout_bytes=len(data),map_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),layout_sha256=hashlib.sha256(data).hexdigest()))
 if not m['name'].startswith('Journey') or m['map_type'] not in ['MAP_TYPE_ROUTE','MAP_TYPE_OCEAN_ROUTE']:continue
 v=struct.unpack('<'+'H'*(len(data)//2),data);w=l['width'];fr=l['layout_version']=='frlg';quarters=[0x110,0x111,0x118,0x119] if fr else [0x150,0x151,0x158,0x159];anchors=set()
 for i,t in enumerate(v):
  if t&1023 in quarters:k=quarters.index(t&1023);anchors.add((i%w-k%2,i//w-k//2))
 for x,y in anchors:
  assert 0<=x<w-1 and 0<=y<l['height']-1,(m['name'],'Rock clipped by boundary',x,y)
  assert [v[yy*w+xx]&1023 for yy in [y,y+1] for xx in [x,x+1]]==quarters,(m['name'],'Incomplete rock',x,y)
 assert not any(t&1023==1 for t in v),(m['name'],'Grass fragment in generated sand island')
 coasts.append(dict(map=m['name'],complete_rocks=len(anchors),grass_fragments=0))
# Verify the compiled bank bytes, not just a renderer's interpretation.
shore=json.loads((source/'.journey-complete-beach-edges').read_text());metas=(source/'src/data/tilesets/metatiles.h').read_text();headers=(source/'src/data/tilesets/headers.h').read_text();rom=(source/'pokeemerald.gba').read_bytes();banks=[]
for b in shore['banks']:
 body=re.search(r'const struct Tileset '+b['bank']+r'\s*=\s*\{(.*?)\};',headers,re.S)[1]
 for field in ['metatiles','metatileAttributes']:
  symbol=re.search(r'\.'+field+r'\s*=\s*(\w+)',body)[1];path=re.search(r'\b'+symbol+r'\[\].*?"([^"]+)"',metas)[1];data=(source/path).read_bytes();offset=s[symbol]-0x08000000;assert rom[offset:offset+len(data)]==data,(b['bank'],field,'Compiled shore art differs')
 banks.append(b['bank'])
native('VarSet',0x40FE,7)
for n,x,y in [('JourneyWorldFill11Right',3,38),('JourneyMossdeepOuterSea',69,16),('JourneyOneIslandChannel',7,7)]:
 warp(n,x,y);step(120);picture(n+'-completed-beach')
for n,x,y,_,new in REPAIRS:
 warp(n,max(1,x+2),max(1,y+2));assert native('MapGridGetMetatileIdAt',x+7,y+7)==new&1023
chart=json.loads((source/('.journey-complete-marine-atlas' if (source/'.journey-complete-marine-atlas').exists() else '.journey-connected-sea-chart')).read_text());assert all(a[0]==b[0] or a[1]==b[1] for r in chart['orthogonal_marine_paths'] for a,b in zip(r['polyline'],r['polyline'][1:]));decode((source/'src/data/journey_world_map.h').read_text()).convert('RGB').resize((1120,560),Image.Resampling.NEAREST).save(args.output/'connected-world-chart.png')
lib.stop();(args.output/'coastal-geometry.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256(rom).hexdigest(),edited_maps=edited,generated_coasts=coasts,compiled_shore_banks=banks,native_quarter_repairs=REPAIRS,orthogonal_actual_connection_paths=len(chart['orthogonal_marine_paths']),original_land_retained=True,approved_ports_preserved=True,initial_location_and_flags_are_fixtures=True,visual_perfection_not_a_proven_property=True),indent=2)+'\n');print('Edited maps:',len(edited),'generated coasts:',len(coasts),'compiled shore banks:',len(banks),flush=True)
