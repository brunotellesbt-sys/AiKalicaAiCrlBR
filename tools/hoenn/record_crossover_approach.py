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
frames=[frame()];origin=None;player=list(position());samples=[];last_position=None;spawn_box=None;first_visible=None;settled=0;trace=[];movement=None
def signed(value):return value-65536 if value&32768 else value
def screen_box(obj):
 sprite=s['gSprites']+lib.read8(obj+35)*68
 xx=signed(lib.read16(sprite+32))+signed(lib.read16(sprite+36))+signed(lib.read16(s['gSpriteCoordOffsetX']))
 yy=signed(lib.read16(sprite+34))+signed(lib.read16(sprite+38))+signed(lib.read16(s['gSpriteCoordOffsetY']))
 return sprite,[xx-8,yy-16,xx+8,yy+16]
def on_screen(box):return box[2]>0 and box[0]<240 and box[3]>0 and box[1]<160
lib.write16(pointer,0)
for tick in range(1600):
 step(1)
 if tick%4==0:frames.append(frame())
 for i in range(16):
  obj=s['gObjectEvents']+i*36
  if lib.read8(obj)&1 and lib.read8(obj+8)==240:
   initial=[lib.read16(obj+12)-7,lib.read16(obj+14)-7];current=[lib.read16(obj+16)-7,lib.read16(obj+18)-7]
   sprite,box=screen_box(obj)
   if origin is None:
    origin=initial;spawn_box=box;assert not on_screen(box),(hero,'Actor born in camera view',initial,box)
    movement=[]
    for at in range(128):
     action=lib.read8(s['gJourneyCrossoverMovement']+at)
     if action==0xFE:break
     assert action in [8,9,10,11];movement.append(action)
    assert len(movement)>=6,(hero,'Offscreen path too short',movement)
   if on_screen(box):
    assert not lib.read8(obj+1)&0x20,(hero,'Actor hidden inside viewport')
    if first_visible is None:first_visible=tick;picture(hero.lower()+'-first-visible')
   distance=sum(abs(a-b) for a,b in zip(current,player))
   if current!=last_position:
    samples.append(dict(frame=tick,actor=current,distance=distance,screen_box=box));last_position=current
   # Inspect real sprite animation commands and flips during lateral walking.
   anim=lib.read8(sprite+42);cmd=lib.read8(sprite+43)
   if anim>=4 and anim%4 in [2,3]:
    address=lib.read32(lib.read32(sprite+8)+anim*4)+cmd*4;image=lib.read16(address);flip=bool(lib.read16(sprite+2)&0x1000)
    if image<9:
     assert image in [2,7,8],(hero,'Non-lateral pose used in side walk',image)
     data=lib.read32(lib.read32(sprite+12)+image*8);physical=(data-s['gObjectEventPic_Journey'+hero.upper()])//256
     assert physical in [7,8],(hero,'Front/back pose in side walk',physical)
     left=(physical==7)!=flip;assert left==(anim%4==2),(hero,'Side walking rotated',anim,cmd,image,physical,flip)
     row=dict(animation=anim,image=image,physical_frame=physical,hflip=flip,facing='left' if left else 'right')
     if row not in trace:trace.append(row)
   settled=settled+1 if distance==1 and not lib.read8(obj)&2 else 0
   break
 if settled>=150:break
assert origin is not None and samples[-1]['distance']==1,(hero,origin,samples)
assert first_visible is not None and len(samples)>=7,(hero,'Approach not fully recorded',samples)
for a,b in zip(samples,samples[1:]):assert sum(abs(x-y) for x,y in zip(a['actor'],b['actor']))==1,(hero,'Actor teleported',a,b)
assert len(movement)==len(samples)-1,(hero,'Path not completely walked',movement,samples)
# Both lateral directions must stay correct at every supported walking speed,
# even when a particular route's shortest entrance is entirely vertical.
for avatar in [hero.upper(),'PWT'+hero.upper()]:
 images=s['sPicTable_Journey'+avatar];basepic=s['gObjectEventPic_Journey'+avatar]
 assert lib.read32(images+2*8)==basepic+7*256
 for direction in ['West','East']:
  for speed in ['','Fast','Faster','Fastest']:
   commands=s['sAnim_Go'+speed+direction+'_JourneyRivals']
   for k in range(4):
    image=lib.read16(commands+k*4);flip=bool(lib.read8(commands+k*4+2)&64)
    physical=(lib.read32(images+image*8)-basepic)//256
    assert ((physical==7)!=flip)==(direction=='West'),(avatar,direction,speed,image,physical,flip)
frame().save(args.output/(hero.lower()+'-dialogue.png'))
frames[0].save(args.output/(hero.lower()+'-approach.gif'),save_all=True,append_images=frames[1:]+[frames[-1]]*22,duration=67,loop=0,optimize=False)
strip=Image.new('RGB',(720*4,480))
indices=[0,1+first_visible//4,min(len(frames)-1,1+(first_visible+samples[-1]['frame'])//8),len(frames)-1]
for i,at in enumerate(indices):strip.paste(frames[at],(i*720,0))
strip.save(args.output/(hero.lower()+'-approach-steps.png'))
# Advance the ordinary dialogue using A, then allow the native transition.
for _ in range(120):
 press(1)
 if lib.read32(s['gMain']+4)&~1==s['BattleMainCB2']:break
else:raise AssertionError((hero,'Rival battle did not start'))
step(150);picture(hero.lower()+'-battle-entry')
assert lib.read32(s['gBattleTypeFlags'])&abi[10],(hero,'Not a trainer battle')
lib.stop()
(args.output/(hero.lower()+'-approach.json')).write_text(json.dumps(dict(passed=True,hero=hero,route=route,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),player=player,initial=origin,initial_screen_box=spawn_box,spawn_entirely_outside_camera=True,first_visible_native_frame=first_visible,movement_actions=movement,movement_samples=samples,lateral_animation_trace=trace,lateral_facing_preserved=True,visible=True,actual_native_movement=True,controller_dialogue_and_battle_entry=True,initial_route_party_and_flags_are_fixtures=True,actor_coordinates_not_written=True),indent=2)+'\n')
print(hero,route,'born outside camera',spawn_box,'walked',len(movement),'steps; facing stable; native battle entered',flush=True)
