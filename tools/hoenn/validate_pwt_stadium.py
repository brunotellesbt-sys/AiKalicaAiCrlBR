"""Spawn every walking identity in the native stadium and inspect its frames.

Travel, party registration and opponent selection are declared fixtures. The
compiled graphics table, palette loading and object spawning are native.
"""
from pathlib import Path
import hashlib,json,re,struct,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2]
prefix=(ROOT/'tools/hoenn/validate_pwt_world.py').read_text().split('for generation in range(cap+1):')[0]
exec(compile(prefix,str(ROOT/'tools/hoenn/validate_pwt_world.py'),'exec'))
with tempfile.TemporaryDirectory(dir='/tmp') as directory:
    out=Path(directory)/'graphics.s'
    fields=['offsetof(struct ObjectEventGraphicsInfo,size)','offsetof(struct ObjectEventGraphicsInfo,width)',
        'offsetof(struct ObjectEventGraphicsInfo,height)','offsetof(struct ObjectEventGraphicsInfo,images)',
        'sizeof(struct SpriteFrameImage)','offsetof(struct SpriteFrameImage,data)',
        'offsetof(struct SpriteFrameImage,size)','offsetof(struct SpriteFrameImage,relativeFrames)']
    code='#include "global.h"\n#include "event_object_movement.h"\n#include <stddef.h>\nconst u32 gfx_abi[]={'+','.join(fields)+'};'
    subprocess.run([str(ROOT/'.local/arm-gcc/usr/bin/arm-none-eabi-gcc'),'-S','-mabi=apcs-gnu','-iquote',str(source/'include'),'-x','c','-','-o',str(out)],input=code,text=True,check=True)
    gfx_abi=[int(v) for v in re.findall(r'\.word\s+(\d+)',out.read_text().split('gfx_abi:',1)[1].split('.size',1)[0])]
ids=begin(0);warp('JourneyPWTArena',9,6)
# Let the real entrance and board execute, then isolate the graphics fixture.
press(2);step(120)
for _ in range(200):
    if task('Task_HandleYesNoInput'):break
    press(1)
assert task('Task_HandleYesNoInput')
for i in range(16):
    if lib.read8(s['gTasks']+i*40+4) and lib.read32(s['gTasks']+i*40)&~1==s['Task_HandleYesNoInput']:
        native('DestroyTask',i)
native('HideFieldMessageBox')
checks=[]
picture('pwt-stadium-before-spawn')
scratch=s['gStringVar4']+900
for index in ids[1:]:
    lib.write16(cup+offsets[9],ids.index(index))
    assert native('JourneyPWTWalkingAvailable',index)
    graphics=lib.read16(s['sPWTWalking']+index*2)
    info=native('GetObjectEventGraphicsInfo',graphics)
    width,height=lib.read16(info+gfx_abi[1]),lib.read16(info+gfx_abi[2])
    size=lib.read16(info+gfx_abi[0]);assert width in (16,32) and height==32
    frames=lib.read32(info+gfx_abi[3]);hashes=[]
    for frame in range(9):
        relative=bool(lib.read8(frames+gfx_abi[7]))
        entry=frames if relative else frames+frame*gfx_abi[4];data=lib.read32(entry+gfx_abi[5])
        length=lib.read16(entry+gfx_abi[6]);assert length==width*height//2
        if relative:data+=frame*length
        rawframe=bytes(lib.read8(data+i) for i in range(length));assert any(rawframe)
        hashes.append(hashlib.sha256(rawframe).hexdigest())
    authored={r['key'] for r in json.loads((ROOT/'tools/hoenn/data/pwt/generated/sources.json').read_text())['records']}
    assert len(set(hashes))>=(5 if rows[index]['key'] in authored else 3),(rows[index]['name'],'Missing directional frames',len(set(hashes)))
    native('JourneyPWTEntrance');assert lib.read16(s['gSpecialVar_Result'])==1
    group,number=location()
    assert native('TryGetObjectEventIdByLocalIdAndMap',14,number,group,scratch)==0
    step(8)
    if rows[index]['key'] in ['IONO','VIOLA','KIERAN','LACEY','EREN','LUFFY','ASH']:
        picture('pwt-stadium-'+rows[index]['key'].lower())
    checks.append(dict(name=rows[index]['name'],graphics_id=graphics,width=width,height=height,frame_bytes=size,frame_sha256=hashes,spawned=True))
    native('JourneyPWTExit')
assert len(checks)==len(eligible(rows,cap,0))
for x in range(2,18):assert native('MapGridGetCollisionAt',x+7,6+7)==0
picture('pwt-stadium-native')
native('JourneyPWTFinish')
assert bytes(lib.read8(party+i) for i in range(6*abi[2]))==original
lib.stop()
(args.output/'pwt-stadium.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),checks=checks,all_eligible_identities_spawned=True,nine_frames_per_identity=True,entrance_lane_unblocked=True,dedicated_stadium=True,travel_and_opponent_selection_are_fixtures=True,full_campaign_playthrough=False),indent=2)+'\n')
print('Native stadium sprites passed:',len(checks),flush=True)
