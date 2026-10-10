"""Native visited-town eligibility and controller Fly on the integrated map."""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_world_map.py').read_text().split('checks=[]')[0]
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_world_map.py'),'exec'))
def packed(name):
 g,n=map_id(name);return(g<<8)|n
def allowed(p):return bool(native('JourneyWorldFlyAllowed',packed(p['map']),p['section_number']))
sections=json.loads((source/'src/data/region_map/region_map_sections.json').read_text())['map_sections'];ids={p['id']:i for i,p in enumerate(sections)}
points={p['map']:dict(p,section_number=ids[p['section']]) for p in report['points']}
port=points['JourneyRoute12Shipyard'];assert not allowed(port)
warp(port['map'],24,39);step(90);assert allowed(port)
flags=(source/'include/constants/flags.h').read_text()
seviis=['One','Two','Three','Four','Five','Six','Seven'];eligibility=[]
for name in seviis:
 p=points[name+'Island_Frlg'];flag=int(re.search(r'^#define\s+FLAG_WORLD_MAP_'+name.upper()+r'_ISLAND\s+(0x[0-9A-Fa-f]+|\d+)',flags,re.M)[1],0)
 native('FlagSet',flag);assert allowed(p);eligibility.append(p['map'])
for p in points.values():
 if p['map'].startswith('JourneySanctuary'):assert not allowed(p)
warp('Route1_Frlg',5,12);step(90)
lib.write32(s['gFieldEffectArguments'],0) # Selected party slot is a fixture.
native('JourneyWorldMapOpenFly');wait_for(lambda:callback()==s['CB2_JourneyWorldMap']);step(90)
ptr=lib.read32(s['sJourneyWorldMap']);assert lib.read8(ptr+2059)==1
for axis,offset,positive,negative in [('x',2056,16,32),('y',2057,128,64)]:
 for _ in range(90):
  value=lib.read8(ptr+offset)
  if abs(value-port[axis])<=1:break
  press(positive if value<port[axis] else negative)
 else:raise AssertionError(('Cursor failed',axis,value,port[axis]))
picture('fly-lavender-selection');press(1)
wait_for(lambda:location()==map_id(port['map']),limit=1000);step(600)
assert position()==(24,39);assert callback()==s['CB2_Overworld'];assert lib.read32(s['sJourneyWorldMap'])==0
picture('fly-lavender-arrival')
assert native('TrySavingData',0,max_frames=6000)==1
assert native('LoadGameSave',0,max_frames=6000)==1
lib.write32(s['gMain']+4,s['CB2_ContinueSavedGame']|1);step(1500);assert allowed(port)
lib.stop()
(args.output/'world-fly.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),lavender_requires_visit=True,lavender_visit_persists_after_save=True,sevii_eligible=eligibility,caves_not_fly_destinations=True,controller_fly_with_native_animation=True,destination=port['map'],party_menu_entry_and_sevii_flights_not_exercised=True,initial_party_and_location_are_fixtures=True),indent=2)+'\n')
