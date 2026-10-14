"""Check the natural offscreen entrance hook at both sides of all 12 routes.
Initial party/progress/placements are fixtures; NPC creation and camera bounds
come from the compiled game. Encounters are cancelled after observing spawn.
"""
import sys,hashlib,json,struct
from pathlib import Path
from collections import deque
root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/'tools/hoenn'))
bootstrap=(root/'tools/hoenn/validate_trainer_levels.py').read_text().split('\nchecks=[]')[0]
exec(compile(bootstrap,__file__,'exec'))
native('VarSet',0x40FE,7)
rawflag(lib.read16(s['gBadgeFlags'])-7,True)
for tid in range(1,1589):rawflag(0x500+tid,True)
names=['Route4_Frlg','Route10_Frlg','Route17_Frlg','Route112','Route113','PetalburgWoods','Route6_Frlg','Route13_Frlg','Route20_Frlg','Route106','Route108','Route125'];cached={};records=[]
for name in names:
 m=json.loads((source/f'data/maps/{name}/map.json').read_text());l=layouts[m['layout']];w,h=l['width'],l['height'];v=struct.unpack('<'+'H'*w*h,(source/l['blockdata_filepath']).read_bytes());fr=l['layout_version']=='frlg';cut=640 if fr else 512;size=4 if fr else 2;mask=511 if fr else 255;attrs=[lib.read32(s[l[key]]+16) for key in ['primary_tileset','secondary_tileset']];land=set();reserved={(a['x'],a['y']) for a in m['warp_events']}
 for i,t in enumerate(v):
  if t&0xC00 or t>>12 not in [3,4] or (i%w,i//w) in reserved:continue
  mid=t&1023;at=attrs[mid>=cut]+size*(mid-cut if mid>=cut else mid);b=(lib.read32(at) if fr else lib.read16(at))&mask
  if b not in cached:cached[b]=not any(native('MetatileBehavior_Is'+fn,b) for fn in ['SurfableWaterOrUnderwater','JumpNorth','JumpSouth','JumpWest','JumpEast'])
  if cached[b]:land.add((i%w,i//w))
 comps=[];left=set(land)
 while left:
  q=[left.pop()];comp={q[0]}
  while q:
   x,y=q.pop()
   for xy in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
    if xy in left and v[xy[1]*w+xy[0]]>>12==v[y*w+x]>>12:left.remove(xy);comp.add(xy);q.append(xy)
  comps.append(comp)
 options=[]
 for comp in sorted(comps,key=len,reverse=True):
  pts=sorted(comp)
  if max(x for x,y in pts)-min(x for x,y in pts)<9 and max(y for x,y in pts)-min(y for x,y in pts)<7:continue
  options.extend([min(pts,key=lambda p:p[0]),max(pts,key=lambda p:p[0]),min(pts,key=lambda p:p[1]),max(pts,key=lambda p:p[1])]);options.extend(pts[::max(1,len(pts)//12)])
 found=[];scratch=s['gStringVar4']+600
 for x,y in dict.fromkeys(options):
  warp(name,x,y);step(90)
  pointer=native('GetVarPointer',0x40FE);native('VarSet',0x40FF,0);lib.write16(pointer,0);step(2)
  actor=next((s['gObjectEvents']+i*36 for i in range(16) if lib.read8(s['gObjectEvents']+i*36)&1 and lib.read8(s['gObjectEvents']+i*36+8)==240),None)
  if actor is not None:
   sprite=s['gSprites']+lib.read8(actor+35)*68
   def signed(v):return v-65536 if v&32768 else v
   sx=signed(lib.read16(sprite+32))+signed(lib.read16(sprite+36))+signed(lib.read16(s['gSpriteCoordOffsetX']))
   sy=signed(lib.read16(sprite+34))+signed(lib.read16(sprite+38))+signed(lib.read16(s['gSpriteCoordOffsetY']))
   box=[sx-8,sy-16,sx+8,sy+16];assert box[2]<=0 or box[0]>=240 or box[3]<=0 or box[1]>=160,(name,'Visible spawn',box)
   found.append(dict(player=[x,y],spawn=[lib.read16(actor+12)-7,lib.read16(actor+14)-7],screen_box=box,offscreen=True));picture(name+'-offscreen-site')
   lib.write16(pointer,7);native('JourneyCrossoverFinish')
   if len(found)>=2:break
  else:lib.write16(pointer,7)
 dims=sorted([(len(c),max(x for x,y in c)-min(x for x,y in c)+1,max(y for x,y in c)-min(y for x,y in c)+1) for c in comps],reverse=True)[:4]
 records.append(dict(map=name,valid_sites=found,largest_land_components=dims));print(name,'sites',found,'components',dims,flush=True)
assert all(r['valid_sites'] for r in records),records
lib.stop();(args.output/'crossover-sites.json').write_text(json.dumps(dict(passed=all(r['valid_sites'] for r in records),rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),routes=records,initial_positions_and_progress_are_fixtures=True,compiled_native_path_search=True),indent=2)+'\n')
