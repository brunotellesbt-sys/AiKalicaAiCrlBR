"""Buy at restored Dewford seller and inspect actual directional Luffy frames."""
import hashlib,json,re,subprocess
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
prefix=(ROOT/'tools/hoenn/validate_dewford_competitive_shop.py').read_text().split("\nnative('SetPlayerAvatarTransitionFlags',1)")[0]
exec(compile(prefix,__file__,'exec'))
native('SetPlayerAvatarTransitionFlags',1)
report['seller_map']='Route107';report['frontier_market']['approach']=[2,16]
native('SetMoney',save()+c['offsetof(struct SaveBlock1,money)'],999999)
purchase=buy(0,report['stocks'][0].index('CHOICE_SCARF'),'CHOICE_SCARF')
warp('Route107',1,16);talk_vendor();advance_to('Task_HandleChooseMonInput');picture('dewford-hyper-trainer');press(2);finish()
warp('Route107',5,16);picture('dewford-two-vendors')
# Use an existing visible object's position as an art fixture. Its graphics
# and facing run through the native object-event/sprite engine, not a montage.
obj=next(s['gObjectEvents']+36*i for i in range(16) if lib.read8(s['gObjectEvents']+36*i)&1 and lib.read8(s['gObjectEvents']+36*i+8)==next(i+1 for i,o in enumerate(json.loads((source/'data/maps/Route107/map.json').read_text())['object_events']) if o['script']=='JourneyCompetitive_Seller'))
expr=['OBJ_EVENT_GFX_JOURNEY_LUFFY','sizeof(struct Sprite)','offsetof(struct Sprite,animNum)']
code='#include "global.h"\n#include "sprite.h"\n#include "constants/event_objects.h"\n#include <stddef.h>\nconst u32 probe[]={'+','.join(expr)+'};'
a=subprocess.check_output([str(ROOT/'.local/arm-gcc/usr/bin/arm-none-eabi-gcc'),'-S','-mabi=apcs-gnu','-iquote',str(source/'include'),'-x','c','-','-o','-'],input=code,text=True)
gfx,sprite_size,anim_offset=map(int,re.findall(r'\.word\s+(\d+)',a.split('probe:',1)[1].split('.size',1)[0]))
native('ObjectEventSetGraphicsId',obj,gfx)
frames=[]
for direction in [1,2,3,4]:
    native('ObjectEventTurn',obj,direction);step(60);picture('luffy-direction-'+str(direction))
    sprite=s['gSprites']+lib.read8(obj+35)*sprite_size;frames.append(lib.read8(sprite+anim_offset))
assert frames==[0,1,2,3],frames
pic=Image.open(ROOT/'tools/hoenn/data/luffy-overworld.png').convert('RGB')
assert pic.size==(16,288)
for i in range(9):
    tile=pic.crop((0,32*i,16,32*(i+1)));bg=tile.getpixel((0,0));ys=[y for y in range(32) for x in range(16) if tile.getpixel((x,y))!=bg];assert max(ys)-min(ys)+1>=27
coasts=json.loads((source/'.journey-extra-gyms').read_text())['coastal_fixes']
for cave in coasts['cave_crowns']:
    name=cave['map'];warp(name,*[cave['repaired_crowns'][0][0],cave['repaired_crowns'][0][1]+4]);step(60)
    if len(cave['repaired_crowns'])==1:picture('cave-'+name)
# Exercise the newly finished southern shores, not only the older remote
# beaches: arrive from water, disembark, invoke native Surf and hit the reef.
for i in range(6*c['sizeof(struct Pokemon)']):lib.write8(party+i,0)
lib.write8(s['gPartiesCount'],0);native('ScriptGiveMon',c['SPECIES_SWAMPERT'],50,0)
native('ScriptSetMonMoveSlot',0,57,0)
for f in [lib.read16(s['gBadgeFlags']+i*2) for i in range(8)]+list(range(0x1ab0,0x1ab8)):
    address=save()+FLAG_OFFSET+f//8;lib.write8(address,lib.read8(address)|(1<<(f&7)))
native('VarSet',0x40fe,7)
names=['DewfordTown','Route107'];allowed=set();walk_prefix='dewford-shore';walk_transition_pictures=False
def finish(limit=500):
    for _ in range(limit):
        if idle():return
        press(1)
    raise AssertionError('Shore Surf prompt did not settle')
exec(compile((ROOT/'tools/hoenn/native_water_walk.py').read_text(),'dewford-shore-native-walker','exec'))
shores=[]
for name in names:
    w,h,tiles=blocks[name]
    if name=='DewfordTown':
        choices=[x for x in range(1,w-1) if tiles[20*w+x]==0x112c and tiles[21*w+x]==0x1170 and tiles[19*w+x]>>12==3 and not tiles[19*w+x]&0xc00 and not water_behaviors[behaviors[name][19*w+x]]]
        assert choices,name
        x=choices[len(choices)//2];start=(x,21);land=(x,19);water=(x,21);reef=(x,21)
    else:
        # Route 107's southern tree bank is intentionally closed. Its intact
        # southeast sand corner is the landing, with the new reef below it.
        start=(8,18);land=(7,18);water=(8,18);reef=(8,21)
        assert not tiles[land[1]*w+land[0]]&0xc00
        assert not water_behaviors[behaviors[name][land[1]*w+land[0]]]
    warp(name,*start);native('SetPlayerAvatarTransitionFlags',8);step(90)
    walk((name,*land));step(90)
    assert lib.read8(s['gPlayerAvatar'])&25==1 and position()==land
    picture(name+'-south-shore-foot')
    prompts=len(surf_prompts);walk((name,*water));step(90)
    assert lib.read8(s['gPlayerAvatar'])&8 and len(surf_prompts)>prompts
    if name=='Route107':
        walk((name,7,19));step(90);before=position();step(90,32);step(60);assert position()==before
    walk((name,*reef));step(90);before=position();step(90,128);step(60);assert position()==before
    assert lib.read8(s['gPlayerAvatar'])&8
    picture(name+'-south-reef-surf')
    shores.append(dict(map=name,shore=list(land),native_disembark=True,native_surf_prompt=True,closed_reef_blocks_controller=True,closed_forest_blocks_controller=name=='Route107'))

lib.stop()
(args.output/'coastal-details.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
    two_dewford_vendors_interacted=True,dewford_purchase=purchase,luffy_native_directional_frames=frames,
    dewford_shores=shores,visible_luffy_height=28,full_cave_crowns=len(coasts['cave_crowns']),art_object_position_is_fixture=True),indent=2)+'\n')
