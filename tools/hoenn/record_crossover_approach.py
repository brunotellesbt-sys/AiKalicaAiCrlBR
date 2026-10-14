"""Record actual mGBA rival walking/dialogue and controller-driven battle entry.

Party, route placement and encounter state are fixtures. No rival coordinates,
movement commands or battle transition are written by this recorder.
"""
import ctypes,hashlib,json
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_trainer_levels.py').read_text().split('\nchecks=[]')[0]
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_trainer_levels.py'),'exec'))
hero='Luffy' if 'luffy' in args.output.name.lower() else 'Eren'
route,x,y=('Route6_Frlg',12,20) if hero=='Luffy' else ('Route4_Frlg',30,8)
team([25,26,27]);rawflag(lib.read16(s['gBadgeFlags'])-7,True)
native('VarSet',0x40FE,7);native('VarSet',0x40FF,0)
pointer=native('GetVarPointer',0x40FE)
warp(route,x,y);step(120)
def frame():return Image.frombytes('RGBA',(240,160),ctypes.string_at(lib.image(),240*160*4)).convert('RGB').resize((720,480),Image.Resampling.NEAREST)
frames=[frame()];distances=[];shots=[];origin=None;player=list(position());samples=[]
lib.write16(pointer,0)
for tick in range(330):
 step(1)
 if tick%4==0:frames.append(frame())
 for i in range(16):
  obj=s['gObjectEvents']+i*36
  if lib.read8(obj)&1 and lib.read8(obj+8)==240:
   initial=[lib.read16(obj+12)-7,lib.read16(obj+14)-7];current=[lib.read16(obj+16)-7,lib.read16(obj+18)-7]
   assert not lib.read8(obj+1)&0x60,(hero,'Invisible rival')
   if origin is None:origin=initial
   distance=sum(abs(a-b) for a,b in zip(current,player))
   if distance not in distances:
    distances.append(distance);samples.append(dict(frame=tick,actor=current,distance=distance));shots.append(frame());frame().save(args.output/(hero.lower()+'-step-'+str(distance)+'.png'))
   break
assert origin is not None and distances[-1]==1,(hero,origin,distances)
assert len(distances)>=3,(hero,'Approach animation was not fully observed',distances)
assert distances==list(range(distances[0],0,-1)),distances
frame().save(args.output/(hero.lower()+'-dialogue.png'))
frames[0].save(args.output/(hero.lower()+'-approach.gif'),save_all=True,append_images=frames[1:]+[frames[-1]]*22,duration=67,loop=0,optimize=False)
strip=Image.new('RGB',(720*len(shots),480))
for i,im in enumerate(shots):strip.paste(im,(i*720,0))
strip.save(args.output/(hero.lower()+'-approach-steps.png'))
# Advance the ordinary dialogue using A, then allow the native transition.
for _ in range(120):
 press(1)
 if lib.read32(s['gMain']+4)&~1==s['BattleMainCB2']:break
else:raise AssertionError((hero,'Rival battle did not start'))
step(150);picture(hero.lower()+'-battle-entry')
assert lib.read32(s['gBattleTypeFlags'])&abi[10],(hero,'Not a trainer battle')
lib.stop()
(args.output/(hero.lower()+'-approach.json')).write_text(json.dumps(dict(passed=True,hero=hero,route=route,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),player=player,initial=origin,movement_samples=samples,visible=True,actual_native_movement=True,controller_dialogue_and_battle_entry=True,initial_route_party_and_flags_are_fixtures=True,actor_coordinates_not_written=True),indent=2)+'\n')
print(hero,route,'walked distances',distances,'and entered its native trainer battle',flush=True)
