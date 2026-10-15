"""Controller journeys through every active generated sea (initial fixtures only)."""
import hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
exec(compile((ROOT/'tools/hoenn/validate_team_missions.py').read_text().split('\nassert pending(True) == 7')[0],__file__,'exec'))
allmaps={p.parent.name:json.loads(p.read_text()) for p in (source/'data/maps').glob('*/map.json')}
geometry=json.loads((source/'.journey-complete-marine-atlas').read_text())
centers={p['map']:p['center'] for p in geometry['projections']}
required={n for n,m in allmaps.items() if n.startswith('Journey') and m['map_type'] in ['MAP_TYPE_ROUTE','MAP_TYPE_OCEAN_ROUTE'] and m.get('connections')}
# One sea network, split into four journeys to keep observations reviewable.
profile=int(args.output.name.rsplit('-',1)[1]);partitions=[[],[],[],[]]
for n in sorted(required):
 x,y=centers[n];partitions[(0 if x<100 else 2)+(y>=72)].append(n)
targets=set(partitions[profile]);assert targets
names=sorted(n for n,m in allmaps.items() if m['map_type'] in ['MAP_TYPE_ROUTE','MAP_TYPE_CITY','MAP_TYPE_TOWN','MAP_TYPE_OCEAN_ROUTE'] or 'Harbor' in n and m.get('connections'))
allowed=set();walk_prefix=f'generated-{profile}';walk_cache_paths=True;walk_max_ticks=2400;walk_transition_pictures=False
native('VarSet',0x40FE,7);rawflag(lib.read16(s['gBadgeFlags'])-7,True)
for tid in range(1,1589):rawflag(0x500+tid,True)
native('ScriptSetMonMoveSlot',0,57,1)
native('AddBagItem',102,999);native('AddBagItem',116,999)
native('VarSet',0x4021,65535);native('VarSet',0x4120,65535)
exec(compile((ROOT/'tools/hoenn/native_water_walk.py').read_text(),'native-controller-walker','exec'))
def choose(n):
 w,h,t=blocks[n]
 valid=[(abs(x-w//2)+abs(y-h//2),y,x) for y in range(1,h-1) for x in range(1,w-1) if y*w+x in passable[n] and not t[y*w+x]&0xC00 and water_behaviors[behaviors[n][y*w+x]] and (x,y) not in warps[n]]
 _,y,x=min(valid);return n,x,y
byident={m['id']:n for n,m in maps.items()}
graph={n:{byident[c['map']] for c in m.get('connections') or [] if c['direction'] in ['up','down','left','right'] and c['map'] in byident} for n,m in maps.items()}
def distance(a,b):
 todo=deque([(a,0)]);seen={a}
 for n,d in iter(todo.popleft,None):
  if n==b:return d
  for other in graph[n]-seen:seen.add(other);todo.append((other,d+1))
  if not todo:break
 return 999
initial=choose(min(targets));name,x,y=initial;g,num=map_id(name)
script(b'\x39'+bytes([g,num,255])+struct.pack('<HH',x,y)+b'\x27\x6b\x02',frames=240);step(60)
native('SetPlayerAvatarTransitionFlags',8);step(30)
assert idle() and location()==(g,num) and position()==(x,y)
markers=[];arrivals=[];jumps=[]
def marker():
 p=native('JourneyWorldMapPosition');return[p&255,p>>8]
markers.append(dict(map=name,tile=[x,y],marker=marker()))
def walk_observer(before,after):
 p=marker();delta=max(abs(a-b) for a,b in zip(p,markers[-1]['marker']))
 if delta>2:jumps.append(dict(before=list(before),after=list(after),previous=markers[-1]['marker'],marker=p,delta=delta))
 markers.append(dict(map=after[0],tile=list(after[1:]),marker=p,seam=before[0]!=after[0]))
while targets:
 current=by_location[location()]
 n=min(targets,key=lambda n:(distance(current,n),abs(centers.get(current,[0,0])[0]-centers[n][0])+abs(centers.get(current,[0,0])[1]-centers[n][1]),n))
 walk(choose(n));picture(n+'-arrived');targets.remove(n);arrivals.append(dict(map=n,tile=list(position()),marker=marker()))
 print('Generated journey',profile,'remaining',len(targets),'arrived',n,flush=True)
walk(initial)
before=(location(),position(),lib.read8(s['gPlayerAvatar'])&25)
assert native('TrySavingData',0,max_frames=6000)==1;assert native('LoadGameSave',0,max_frames=6000)==1
lib.write32(s['gMain']+4,s['CB2_ContinueSavedGame']|1);step(1500);finish()
assert before==(location(),position(),lib.read8(s['gPlayerAvatar'])&25)
picture('saved-return');lib.stop()
(args.output/('generated-sea-journey-'+str(profile)+'.json')).write_text(json.dumps(dict(passed=not jumps,physical_route_roundtrip_passed=True,gps_jumps=jumps,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),profile=profile,required_maps=partitions[profile],arrivals=arrivals,transitions=transitions,walked_tiles=walked,marker_samples=markers,surf_prompts=surf_prompts,controller_roundtrip=True,no_midroute_warps_or_coordinate_writes=True,save_continue_preserves_location=True,initial_party_flags_and_position_are_fixtures=True,level_100_and_max_repel_are_test_fixtures=True,trainer_battles_and_balance_not_tested=True),indent=2)+'\n')
print('Generated sea journey passed',profile,walked,len(transitions),flush=True)
