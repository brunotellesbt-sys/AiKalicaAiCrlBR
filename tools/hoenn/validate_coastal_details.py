"""Buy at restored Dewford seller and inspect actual directional Luffy frames."""
import hashlib,json,re,struct,subprocess
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
restorations={row['map']:row for row in coasts['dewford_coast']}
for name in names:
    w,h,tiles=blocks[name];restored=restorations[name]
    assert h==20 and restored['native_southern_terrain_restored'] and restored['original_border_retained']
    assert hashlib.sha256(struct.pack('<'+'H'*(4*w),*[t&~0xc00 for t in tiles[-4*w:]])).hexdigest()==restored['southern_art_and_elevations_sha256']
    choices=[]
    for yy in range(1,h-1):
        for xx in range(1,w-1):
            at=yy*w+xx
            # The original Route107 shore meets the sea at its dry native
            # corner (7,16), not at an interior plain-sand tile. The isolated
            # sand fragment (7,18) has a closed reef to its east.
            if tiles[at] not in ([0x3124,0x3241] if name=='Route107' else [0x3124]):continue
            if tiles[at]&0xc00 or tiles[at]>>12!=3 or water_behaviors[behaviors[name][at]]:continue
            for dx,dy,key in keys:
                nx,ny=xx+dx,yy+dy
                ni=ny*w+nx
                if 0<nx<w-1 and 0<ny<h-1 and ni in passable[name] and tiles[ni]>>12==1 and water_behaviors[behaviors[name][ni]]:
                    choices.append(((xx,yy),(nx,ny)))
    assert choices,(name,'No native sand landing')
    land,water=(((7,16),(8,16)) if name=='Route107' else choices[len(choices)//2])
    assert (land,water) in choices,(name,'Original southeast shore landing is blocked',land,water)
    warp(name,*water);native('SetPlayerAvatarTransitionFlags',8);step(90)
    walk((name,*land));step(90)
    assert lib.read8(s['gPlayerAvatar'])&25==1 and position()==land
    picture(name+'-native-coast-foot')
    prompts=len(surf_prompts);walk((name,*water));step(90)
    assert lib.read8(s['gPlayerAvatar'])&8 and len(surf_prompts)>prompts
    picture(name+'-native-coast-surf')
    if name=='DewfordTown':
        warp(name,10,18);native('SetPlayerAvatarTransitionFlags',1);step(90)
        walk((name,10,19));step(60);before=position()
        step(90,128);step(60)
        assert position()==before and lib.read8(s['gPlayerAvatar'])&25==1,('Native southern forest border did not block walking',before,position())
        picture(name+'-native-south-original')
    else:
        walk((name,*land));step(90)
        assert lib.read8(s['gPlayerAvatar'])&25==1 and position()==land
        picture(name+'-native-south-original')
    shores.append(dict(map=name,shore=list(land),shore_metatile=tiles[land[1]*w+land[0]],native_disembark=True,native_surf_prompt=True,
        native_southern_terrain_restored=True,original_south_art_and_elevations_match_compiled_rom=True,original_border_retained=True))

lib.stop()
(args.output/'coastal-details.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
    two_dewford_vendors_interacted=True,dewford_purchase=purchase,luffy_native_directional_frames=frames,
    dewford_shores=shores,visible_luffy_height=28,full_cave_crowns=len(coasts['cave_crowns']),art_object_position_is_fixture=True),indent=2)+'\n')
