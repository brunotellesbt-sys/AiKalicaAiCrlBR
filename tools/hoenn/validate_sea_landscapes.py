"""Inspect compiled sea terrain/NPCs and climb the native Route114 waterfall.
Initial travel, party and defeated trainer flags are fixtures; field movement is native.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',required=True);p.add_argument('--library',required=True);p.add_argument('--output',required=True);p.add_argument('--waterfall-only',action='store_true');options=p.parse_args()
waterfall_only=options.waterfall_only
sys.argv=[sys.argv[0],'--source',options.source,'--library',options.library,'--output',options.output]
exec(compile((ROOT/'tools/hoenn/validate_abilities.py').read_text().split('\nability_field,')[0],str(ROOT/'tools/hoenn/validate_abilities.py'),'exec'))
report=json.loads((source/'.journey-sea-landscapes').read_text())
stories=json.loads((source/'.journey-team-stories').read_text())
for t in stories['trainers']:native('FlagSet',0x500+t['id'])
for i in range(8):native('FlagClear',0x1AB0+i);native('FlagClear',lib.read16(s['gBadgeFlags']+2*i))
assert native('ScriptGiveMon',7,30,0)==0
native('ScriptSetMonMoveSlot',0,57,0)
npcs=[];geometry=[]
for row in ([] if waterfall_only else report['maps']):
 name=row['map'];m=json.loads((source/f'data/maps/{name}/map.json').read_text());l=layouts[m['layout']];w,h=l['width'],l['height']
 values=struct.unpack('<'+'H'*(w*h),(source/l['blockdata_filepath']).read_bytes())
 x,y=next((i%w,i//w) for i,v in enumerate(values) if v in [0x112B,0x1170] and 3<=i%w<w-3 and 3<=i//w<h-3)
 warp(name,x,y);native('SetPlayerAvatarTransitionFlags',8);step(30)
 for e in m['object_events']:
  x,y=e['x'],e['y']
  warp(name,min(w-3,x+2),min(h-3,y+2));native('SetPlayerAvatarTransitionFlags',1 if e['elevation']==3 else 8);step(30)
  active=[]
  for i in range(16):
   o=s['gObjectEvents']+36*i
   if i!=lib.read8(s['gPlayerAvatar']+5) and lib.read8(o)&1:active.append((lib.read16(o+16)-7,lib.read16(o+18)-7))
  assert (x,y) in active,(name,e,'NPC absent')
  assert native('MapGridGetCollisionAt',x+7,y+7)==0,(name,e,'NPC blocked')
  behavior=native('MapGridGetMetatileBehaviorAt',x+7,y+7)
  water=bool(native('MetatileBehavior_IsSurfableWaterOrUnderwater',behavior))
  assert water==(e['elevation']==1),(name,e,hex(behavior),'wrong surface')
  npcs.append(dict(map=name,script=e['script'],graphics=e['graphics_id'],position=[x,y],native_visible=True,water=water))
 if name in ['JourneyRustboroCoast','JourneyDewfordCoast','JourneyWorldSea01']:
  e=next((e for e in m['object_events'] if 'AQUA' in e['graphics_id']),m['object_events'][-1])
  warp(name,e['x']+1,e['y']+2);native('SetPlayerAvatarTransitionFlags',1 if e['elevation']==3 else 8);step(30);picture(name+'-native-npcs')
 geometry.append(dict(map=name,native_npcs=len(m['object_events'])))
# Below the original waterfall, no Waterfall move: walking/Surf cannot climb it.
warp('Route114',12,13);native('SetPlayerAvatarTransitionFlags',8);step(30)
step(30,64);step(30);assert position()==(12,13),('Waterfall bypassed without move',position())
step(1,1);step(30)
for _ in range(60):
 if not lib.read8(s['sLockFieldControls']):break
 press(1)
picture('river-waterfall-without-move')
# Teach only the water HM, keeping both regional badge banks empty.
native('ScriptSetMonMoveSlot',0,127,1)
step(1,64);step(30)
press(1)
for _ in range(180):
 if position()[1]<=9 and not lib.read8(s['sLockFieldControls']):break
 press(1)
picture('river-waterfall-after-prompt')
assert position()[1]<=9,('Native Waterfall climb failed',position())
assert native('JourneyGymBadgeCount',0)==native('JourneyGymBadgeCount',1)==0
picture('river-waterfall-upper-pool');upper=list(position())
step(100,128);step(30);assert position()[1]>=13,('Native waterfall descent failed',position());picture('river-waterfall-descent')
lib.stop()
(args.output/'sea-landscapes.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),maps=geometry,npcs=npcs,waterfall=dict(no_move_cannot_climb=True,native_prompt_and_climb=True,native_descent=True,upper_position=upper,zero_badges=True),travel_party_and_trainer_flags_are_fixtures=True,full_campaign_playthrough=False),indent=2)+'\n')
print('All sea NPCs and native Waterfall requirement passed',flush=True)
