"""Walk native island entrances, Dive connections and the special capture gate in mGBA."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--library',type=Path,required=True);p.add_argument('--output',type=Path,default=ROOT/'mods/hoenn/integration-validation');p.add_argument('--site')
options=p.parse_args();sys.argv=[sys.argv[0],'--source',str(options.source),'--library',str(options.library),'--output',str(options.output),'--water-hms','--westsea']
exec(compile((ROOT/'tools/hoenn/validate_crossing.py').read_text().split('\nstep(900)\n')[0],str(ROOT/'tools/hoenn/validate_crossing.py'),'exec'))
def press(key=1):step(1,key);step(35)
def task(name):return any(lib.read8(s['gTasks']+i*40+4) and lib.read32(s['gTasks']+i*40)&~1==s[name] for i in range(16))
step(900);save2=lib.read32(s['gSaveBlock2Ptr']);lib.write8(save2,255);lib.write8(save2+8,255);lib.write8(save2+abi[45],abi[46]);lib.write32(s['gMain'],0);lib.write8(s['gMain']+0x438,0);lib.write32(s['gMain']+4,s['CB2_NewGame']|1);step(300)
for _ in range(100):
 if task('Task_HandleMultichoiceGridInput'):break
 press()
assert task('Task_HandleMultichoiceGridInput');press();step(1500);warp('Route1_Frlg',5,12);native('DisableWildEncounters',1);native('ScriptGiveMon',7,60,0)
r=json.loads((source/'.journey-sanctuaries').read_text());checks=[]
# Raw writes select each regional bank independently; FlagSet remaps active-region badges.
for k,h in [(0,0),(8,0),(0,8),(8,7),(7,8),(8,8)]:
 for count,start in [(k,0x1AB0),(h,abi[63])]:
  for i in range(8):
   f=start+i;a=save()+4720+f//8;v=lib.read8(a);mask=1<<(f&7);lib.write8(a,v|mask if i<count else v&~mask)
 assert bool(native('JourneySpecialUnlocked'))==(k==h==8),(k,h)
print('Both regional badge banks gate captures at exactly 16 badges',flush=True)
for site in r['sites']:
 if options.site and site['theme']!=options.site:continue
 surface=site['surface'];cx,cy=site['entry']
 if site['access']=='surf':
  # Reach the beach from the surrounding ocean using real directional movement.
  warp(surface,cx,cy+9);native('SetPlayerAvatarTransitionFlags',8);step(30)
  assert lib.read8(s['gPlayerAvatar'])&8
  step(20,64);step(35)
  assert position()[1]<=cy+8,(surface,position())
  assert not lib.read8(s['gPlayerAvatar'])&8,('Surf did not end at beach',surface)
  # Walk the native cave mouth and its reciprocal stairs.
  warp(surface,cx,cy-3);native('SetPlayerAvatarTransitionFlags',1);step(30)
  picture('sanctuary-'+site['theme']+'-island')
  step(20,64);step(350)
  assert location()==map_id(site['map']),('Island cave entry failed',surface,location(),position())
 else:
  warp(surface,cx+1,cy+1);native('SetPlayerAvatarTransitionFlags',8);step(30)
  assert native('MapGridGetMetatileBehaviorAt',cx+8,cy+8)==18
  assert native('TrySetDiveWarp')==2
  picture('sanctuary-'+site['theme']+'-dive')
  scratch=s['gStringVar4']+800
  lib.write16(scratch,cx+8);lib.write16(scratch+2,cy+8);lib.write8(scratch+4,3)
  lib.write32(s['gFieldEffectArguments'],0);lib.write32(s['gFieldEffectArguments']+4,2)
  native('FieldEffectStart',44)
  step(600);depth='JourneyDepth'+site['theme']
  if location()!=map_id(depth):
   print('Dive diagnostic:',location(),position(),'callback',hex(lib.read32(s['gMain']+4)&~1),'destination',list(lib.read8(s['sWarpDestination']+i) for i in range(8)),'tasks',[(i,hex(lib.read32(s['gTasks']+i*40)&~1),lib.read16(s['gTasks']+i*40+8)) for i in range(16) if lib.read8(s['gTasks']+i*40+4)],flush=True)
  assert location()==map_id(depth),('Dive destination failed',surface,location())
  assert position()==(cx+1,cy+1),(surface,position())
  warp(depth,cx,cy+1);native('SetPlayerAvatarTransitionFlags',16);step(30)
  step(20,64);step(350)
  assert location()==map_id(site['map']),('Underwater cave entry failed',surface,location(),position())
 picture('sanctuary-'+site['theme']+'-chamber')
 for cap in [c for c in r['captures'] if c['site']==site['theme']]:
  x,y=cap['position'];assert native('MapGridGetCollisionAt',x+7,y+7)==0,cap
  # Adjacent interaction tiles remain free of geometry barriers.
  assert native('MapGridGetCollisionAt',x+7,y+8)==0,cap
 warp(site['map'],14,18);native('SetPlayerAvatarTransitionFlags',1);step(30)
 step(20,128);step(350)
 expected=surface if site['access']=='surf' else 'JourneyDepth'+site['theme']
 assert location()==map_id(expected),('Return stairs failed',site['theme'],location(),position())
 if site['access']=='dive':
  warp(expected,cx+1,cy+1);native('SetPlayerAvatarTransitionFlags',16);step(30)
  assert native('TrySetDiveWarp')==1
  lib.write16(scratch,cx+8);lib.write16(scratch+2,cy+8);lib.write8(scratch+4,3)
  lib.write32(s['gFieldEffectArguments'],0);lib.write32(s['gFieldEffectArguments']+4,1)
  native('FieldEffectStart',44)
  step(600);assert location()==map_id(surface),('Emerge failed',site['theme'],location())
 checks.append(dict(site=site['theme'],access=site['access'],native_entry_and_return=True,interaction_cells=site['species_count']))
 print('Native sanctuary passage passed:',site['theme'],flush=True)
lib.stop();args.output.mkdir(parents=True,exist_ok=True)
(args.output/'sanctuaries.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),gate_cases=6,sites=checks,special_species=105,full_campaign_validated=False,capture_battle_not_yet_validated=True),indent=2)+'\n')
