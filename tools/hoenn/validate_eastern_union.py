"""Native Surf seams and a continuous trip behind Ever Grande; geometry fixtures."""
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_team_missions.py').read_text().split('\nassert pending(True) == 7')[0]
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_team_missions.py'),'exec'))
report=json.loads((source/'.journey-eastern-sea-union').read_text())
names=[r['map'] for r in report['rectangles']];allowed=set();walk_prefix='eastern-union'
# Battles are outside this terrain check. Suppress sightings using defeated flags.
trainer_count=int(re.search(r'^#define\s+TRAINERS_COUNT\s+(\d+)',(source/'include/constants/opponents.h').read_text(),re.M)[1])
assert trainer_count<=int(re.search(r'^#define\s+MAX_TRAINERS_COUNT\s+(\d+)',(source/'include/constants/opponents.h').read_text(),re.M)[1])
for i in range(1,trainer_count):rawflag(0x500+i,True)
assert native('GetSafariZoneFlag')==0,'Trainer fixture must not enable system flags'
native('ScriptSetMonMoveSlot',0,57,1)
for f in kanto_flags+hoenn_flags:rawflag(f,False)
exec(compile((ROOT/'tools/hoenn/native_water_walk.py').read_text(),str(ROOT/'tools/hoenn/native_water_walk.py'),'exec'))
def warp(name,x,y):
 g,n=map_id(name)
 script(b'\x39'+bytes([g,n,255])+struct.pack('<HH',x,y)+b'\x27\x6b\x02',frames=240)
 for _ in range(60):
  if idle():break
  step(8)
 assert idle() and location()==(g,n) and position()==(x,y),(name,'Initial placement failed',location(),position())

seams=[];cliffs=[]
for link in report['connections']:
 a,b,d,off=link['source'],link['destination'],link['direction'],link['offset']
 aw,ah,_=blocks[a];bw,bh,_=blocks[b];pairs=[]
 if d=='right':
  for y in range(max(0,off),min(ah,off+bh)):pairs.append(((aw-1,y),(0,y-off)))
 else:
  for x in range(max(0,off),min(aw,off+bw)):pairs.append(((x,ah-1),(x-off,0)))
 def surf(n,xy):
  w,_,v=blocks[n];i=xy[1]*w+xy[0]
  return i in passable[n] and water_behaviors[behaviors[n][i]] and not v[i]&0xC00
 usable=[p for p in pairs if surf(a,p[0]) and surf(b,p[1]) and blocks[a][2][p[0][1]*aw+p[0][0]]>>12 == blocks[b][2][p[1][1]*bw+p[1][0]]>>12]
 if not usable:
  assert a=='EverGrandeCity' or b=='EverGrandeCity' or 'Harbor' in a or 'Harbor' in b,(link,'unexpected obstructed seam')
  cliffs.append(dict(**link,reason='Preserved native mountain or harbor building; no Surf shore here'))
  continue
 # Check endpoint tiles as well as the middle where parallel spans meet.
 selected=list(dict.fromkeys([usable[0],usable[len(usable)//2],usable[-1]]))
 key=16 if d=='right' else 128;reverse=32 if d=='right' else 64
 for p1,p2 in selected:
  for start,target,xy,end,k in [(a,b,p1,p2,key),(b,a,p2,p1,reverse)]:
   warp(start,*xy);assert position()==xy,(start,'Fixture coordinate mismatch',xy,position())
   native('SetPlayerAvatarTransitionFlags',8);step(30)
   cross(target,k)
   assert position()==end,(start,target,position(),end)
   seams.append(dict(source=start,destination=target,start=list(xy),end=list(end),surf_preserved=True))
 print('Native eastern seam:',a,b,flush=True)
# Start the continuous trip in a fresh emulator, independent of hundreds of
# synthetic border placements. No fixture warp or reset occurs during the trip.
lib.stop();emulator_workspace.cleanup()
sys.argv=[sys.argv[0],'--source',str(source),'--library',str(args.library),'--output',str(args.output)]
setup=Path(__file__).read_text().split('seams=[];cliffs=[]')[0]
exec(compile(setup,str(Path(__file__)),'exec'))
# This itinerary stays on sea-level Surf water. Exclude beaches, elevated
# pools and collision-marked reefs from the planner, just as the player must.
for n,(w,h,values) in blocks.items():
 passable[n]={i for i in passable[n] if values[i]>>12==1 and not values[i]&0xC00 and water_behaviors[behaviors[n][i]]}
# One initial placement; every following leg is ordinary controller movement.
start=('Route125',77,22);warp(*start);native('SetPlayerAvatarTransitionFlags',8);step(30)
legs=[];saves=[]
def leg(n,x,y):
 w,h,vals=blocks[n]
 if vals[y*w+x] not in [0x1170,0x112B]:
  _,y,x=min((abs(xx-x)+abs(yy-y),yy,xx) for yy in range(3,h-3) for xx in range(3,w-3) if vals[yy*w+xx] in [0x1170,0x112B])
 walk((n,x,y));legs.append(dict(map=n,position=list(position())));print('Eastern union arrival:',n,position(),flush=True)
def checkpoint(label):
 before=(location(),position(),lib.read8(s['gPlayerAvatar'])&25)
 assert native('TrySavingData',0,max_frames=6000)==1
 step(60)
 assert native('LoadGameSave',0,max_frames=6000)==1
 lib.write32(s['gMain']+4,s['CB2_ContinueSavedGame']|1);step(1500);finish()
 assert before==(location(),position(),lib.read8(s['gPlayerAvatar'])&25)
 saves.append(label);picture(label+'-continue')
for n,x,y in [
 ('JourneyHoennNorthSea',40,22),('JourneyHoennNorthSea',100,35),
 ('JourneyMossdeepOuterSea',100,20),('JourneyHoennMiddleSea',95,30),
 ('JourneyEverGrandeBackSea',30,20),('JourneyEverGrandeBackSouthSea',30,20),
 ('JourneyHoennSouthSea',90,12),('JourneyHoennSouthEastSea',40,12),
 ('JourneyWorldSea06',12,20),('JourneyWorldLane11',8,30),
 ('JourneyWorldSea04',12,36),('JourneyEverGrandeBackSea',80,20),
 ('JourneyHoennMiddleSea',100,30),('JourneyMossdeepOuterSea',100,20),
 ('JourneyHoennNorthSea',100,35),('JourneyHoennNorthSea',40,22),start]:
 leg(n,x,y)
 if n in ['JourneyEverGrandeBackSouthSea','JourneyWorldSea06']:checkpoint(n)
assert location()==map_id(start[0]) and position()==start[1:]
lib.stop()
(args.output/'eastern-union.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),surf_seams=seams,preserved_cliff_edges=cliffs,continuous_roundtrip=True,independent_seam_and_roundtrip_emulators=True,legs=legs,transitions=transitions,position_changes=walked,save_continue=saves,initial_party_location_and_defeated_trainer_flags_are_fixtures=True,no_midroute_warps=True,defeated_trainer_flags_count=trainer_count-1,safari_mode_disabled=True,full_campaign_playthrough=False),indent=2)+'\n')
print('Eastern ocean native seams and continuous roundtrip passed',flush=True)
