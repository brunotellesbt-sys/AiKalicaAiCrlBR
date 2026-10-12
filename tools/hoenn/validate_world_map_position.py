"""Execute the compiled position projection and a short controller Surf crossing."""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_coast_connectivity.py').read_text().split('required={')[0]
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_coast_connectivity.py'),'exec'))
projection=json.loads((source/'.journey-world-map-position').read_text())
byname={p['map']:p for p in projection['projections']}
import subprocess
symbols=subprocess.check_output([str(ROOT/'.local/arm-binutils/usr/bin/arm-none-eabi-nm'),'-S',str(source/'pokeemerald.elf')],text=True)
match=re.search(r'^(\w+) (\w+) r sWorldAnchors$',symbols,re.M);assert match
anchor_offset=int(match[1],16)-0x08000000;anchor_bytes=int(match[2],16)
assert anchor_bytes%len(projection['anchors'])==0
anchor_stride=anchor_bytes//len(projection['anchors']);assert anchor_stride>=10
rom=(source/'pokeemerald.gba').read_bytes();compiled_anchors=rom[anchor_offset:anchor_offset+anchor_bytes]
for i,a in enumerate(projection['anchors']):
 assert compiled_anchors[i*anchor_stride:i*anchor_stride+10]==struct.pack('<hhhhBB',*a),('Compiled GPS anchor differs',i)
assert projection['maximum_neighbor_pixel_step']<=2
def packed_position():
 v=native('JourneyWorldMapPosition');return [v&255,v>>8]
def fixture(name,x,y):
 g,num=map_id(name);lib.write8(save()+4,g);lib.write8(save()+5,num)
 obj=s['gObjectEvents']+lib.read8(s['gPlayerAvatar']+5)*36
 for offset,v in [(16,x+7),(18,y+7),(20,x+7),(22,y+7)]:lib.write16(obj+offset,v)
 return packed_position()
def unambiguous(n,x,y):
 p=byname[n];aa=projection['anchors'][p['first']:p['first']+p['count']+1]
 return sum(a[0]<=x<=a[2] and a[1]<=y<=a[3] for a in aa)==1
checks=[]
for link in projection['seams']:
 n,other,d,off=link['map'],link['other'],link['direction'],link['offset'];p=byname[n];q=byname[other]
 l,t,r,b=link['box'];pairs=[]
 for x,y in [(l,t),(r,b),((l+r)//2,(t+b)//2)]:
  ox,oy={'right':(0,y-off),'left':(q['width']-1,y-off),'up':(x-off,q['height']-1),'down':(x-off,0)}[d]
  a=fixture(n,x,y);bb=fixture(other,ox,oy)
  assert a==bb,(n,other,(x,y),(ox,oy),a,bb,link['position'])
  pairs.append(dict(source_tile=[x,y],destination_tile=[ox,oy],position=a))
 if pairs:checks.append(dict(source=n,destination=other,samples=pairs))
print('Compiled seamless projections:',len(checks),'directed connections',flush=True)
# Restore real terrain with one placement; crossing itself uses controller only.
a,b='MossdeepCity','JourneyMossdeepOuterSea'
link=next(c for c in projection['seams'] if c['map']==a and c['other']==b)
p,q=byname[a],byname[b];off=link['offset'];w=p['width'];h=p['height']
ys=[y for y in range(max(1,off+1),min(h-1,off+q['height']-1)) if all((y*w+x) in passable[a] for x in range(w-4,w)) and all(((y-off)*q['width']+x) in passable[b] for x in range(4))]
assert ys,'No open Mossdeep east seam'
y=min(ys,key=lambda y:abs(y-h//2));g,num=map_id(a)
script(b'\x39'+bytes([g,num,255])+struct.pack('<HH',w-3,y)+b'\x27\x6b\x02',frames=240)
step(30);native('SetPlayerAvatarTransitionFlags',8);step(30)
assert location()==map_id(a) and position()==(w-3,y)
journey=[]
for target in [(a,w-3,y),(a,w-1,y),(b,0,y-off),(b,3,y-off)]:
 walk(target);xy=packed_position();journey.append(dict(map=target[0],tile=list(position()),marker=xy))
print('Mossdeep short eastward trip:',journey,flush=True)
assert journey[-1]['marker'][0]>=journey[0]['marker'][0]
assert max(abs(c['marker'][1]-journey[0]['marker'][1]) for c in journey)<=1
assert max(max(abs(a-b) for a,b in zip(c['marker'],d['marker'])) for c,d in zip(journey,journey[1:]))<=1
assert journey[1]['marker']==journey[2]['marker']
# Capture native map screen after the actual Surf trip.
opening=(ROOT/'tools/hoenn/validate_world_map.py').read_text().split('checks=[]')[0].split('def callback():')[1]
exec('def callback():'+opening)
ptr=open_map();assert [lib.read8(ptr+2056),lib.read8(ptr+2057)]==journey[-1]['marker'];picture('mossdeep-east-position')
press(16);press(4);assert [lib.read8(ptr+2056),lib.read8(ptr+2057)]==journey[-1]['marker']
press(2);wait_for(lambda:callback()==s['CB2_Overworld']);step(120);press(2)
progress=[]
for x in [15,35]:
 walk((b,x,y-off));progress.append(dict(tile=list(position()),marker=packed_position()))
assert progress[-1]['marker'][0]>journey[-1]['marker'][0],('Marker did not follow eastward Surf',progress)
print('Marker follows movement within route:',progress,flush=True)
lib.stop()
(args.output/'world-map-position.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),connections=checks,mossdeep_short_controller_trip=journey,recenter_uses_real_position=True,within_route_controller_progress=progress,atlas_pixels_unchanged=True,compiled_anchor_offset=anchor_offset,compiled_anchor_bytes=len(compiled_anchors),compiled_anchor_stride=anchor_stride,compiled_anchor_sha256=hashlib.sha256(compiled_anchors).hexdigest(),maximum_neighbor_pixel_step=projection['maximum_neighbor_pixel_step'],projection_coordinates_are_fixtures=True,short_trip_has_no_midroute_fixture_warp=True),indent=2)+'\n')
