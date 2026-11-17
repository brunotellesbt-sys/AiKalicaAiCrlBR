"""Exhaustive emitted-C/terrain checks for candidate533 save coordinates.

This is host C and source evidence. It does not claim a native battery passed.
"""
import ctypes
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from atlas_surf_candidate_migration import render, resolve
from atlas_surf_migration import _safe_behaviors, _mode, _occupied


PREFIX = r'''
#include <stdint.h>
#include <stddef.h>
typedef uint8_t u8; typedef uint16_t u16; typedef uint32_t u32;
typedef int16_t s16; typedef int8_t s8; typedef uint8_t bool8;
#define EWRAM_DATA
#define TRUE 1
#define FALSE 0
#define ARRAY_COUNT(x) (sizeof(x)/sizeof((x)[0]))
#define OBJECT_EVENTS_COUNT 4
#define PLAYER_AVATAR_STATE_SURFING 2
struct Object { u8 isPlayer; u16 graphicsId; };
struct Save { struct Object objectEvents[OBJECT_EVENTS_COUNT]; };
struct Save2 { u8 playerGender; };
static struct Save saved;
static struct Save2 saved2;
static struct Save *gSaveBlock1Ptr=&saved;
static struct Save2 *gSaveBlock2Ptr=&saved2;
static u16 GetPlayerAvatarGraphicsIdByStateIdAndGender(u16 state,u16 gender) { return 0x100+state+gender; }
struct WarpData { s8 mapGroup,mapNum,warpId; s16 x,y; };
struct JourneyAtlasSaveMove {
    u8 oldGroup,oldNum,newGroup,newNum;
    s16 left,top,right,bottom,dx,dy;
    u8 mode,elevation;
};
'''
WRAPPER = r'''
int point(u16 packed,s16 x,s16 y,u8 surf,s16 *out)
{
    const struct JourneyAtlasSaveMove *move;
    saved.objectEvents[0].isPlayer=1;saved.objectEvents[0].graphicsId=surf?0x0201:1;
    sJourneyCandidateUpgrade=TRUE;
    move=JourneyCandidateResolve(packed>>8,packed&255,x,y);
    if(move==NULL) return 0;
    out[0]=(move->newGroup<<8)|move->newNum;out[1]=x+move->dx;out[2]=y+move->dy;
    out[3]=move->mode;out[4]=move->elevation;
    return 1;
}
int portal(u16 packed,s8 id,s16 *out)
{
    struct WarpData warp={packed>>8,packed&255,id,-1,-1};
    if(!JourneyCandidateMigrateWarp(&warp)) return 0;
    out[0]=((u16)(u8)warp.mapGroup<<8)|(u8)warp.mapNum;out[1]=warp.warpId;
    out[2]=warp.x;out[3]=warp.y;
    return 1;
}
int native_refresh(u16 packed) { return JourneyCandidateNativeObjectsChanged(packed); }
'''


def verify(tables, view):
    compiler = shutil.which('cc') or shutil.which('gcc')
    if compiler is None:
        raise RuntimeError('Host C compiler required for complete candidate migration verification')
    enums = _safe_behaviors(view); occupied = {}; identities = {v:k for k,v in view.identities.items()}
    code = PREFIX+render(tables)+WRAPPER
    checked = 0; invalid = 0; portals = 0
    with tempfile.TemporaryDirectory(prefix='candidate533-migration-host-') as directory:
        root = Path(directory); source = root/'verify.c'; source.write_text(code)
        subprocess.run([compiler,'-std=gnu17','-Wall','-Wextra','-Werror','-shared','-fPIC',
                        str(source),'-o',str(root/'verify.so')],check=True,capture_output=True)
        lib = ctypes.CDLL(str(root/'verify.so')); out = (ctypes.c_int16*5)()
        for packed, width, height, first, count in tables['maps']:
            runs = tables['runs'][first:first+count]
            if not runs or runs[-1][0] != width*height or any(a[0]>=b[0] for a,b in zip(runs,runs[1:])):
                raise ValueError(('Candidate migration RLE has a gap/overlap',packed))
            for x,y in [(x,y) for y in range(height) for x in range(width)]+[(-1,-1),(32767,-32768)]:
                for surf in [False,True]:
                    expected = resolve(tables,packed,x,y,surf)
                    if not lib.point(packed,x,y,surf,out) or tuple(out) != expected:
                        raise ValueError(('Emitted candidate C differs from host oracle',packed,x,y,surf,expected,list(out)))
                    target, a,b, mode,elevation = expected; name = identities.get(target)
                    if name is None:
                        raise ValueError(('Migration target has no compiled identity',target))
                    if name not in occupied:
                        occupied[name] = _occupied(view.maps[name])
                    if ((a,b) in occupied[name] or _mode(view,name,a,b,enums) != ('walk' if mode==1 else 'surf')
                            or elevation != view.word(name,a,b)>>12):
                        raise ValueError(('Migration enters unsafe terrain/events',packed,x,y,surf,name,a,b))
                    if 0<=x<width and 0<=y<height: checked += 1
                    else: invalid += 1
        for packed, old_id, new, new_id in tables['warps']:
            if not lib.portal(packed,old_id,out) or tuple(out[:4]) != (new,new_id,-1,-1):
                raise ValueError('Candidate event warp identity/sentinels changed')
            portals += 1
    view.assert_unchanged()
    return dict(kind='candidate533-coordinate-exhaustive-host-C',passed=True,
                maps=len(tables['maps']),legal_and_blocked_cells_checked=checked//2,
                both_saved_avatar_modes_checked=checked,invalid_coordinate_cases_checked=invalid,
                event_warps_checked=portals,emitted_C_sha256=hashlib.sha256(code.encode()).hexdigest(),
                table_sha256=tables['table_sha256'],table_bytes=tables['table_bytes'],
                target_collision_height_behavior_and_events_checked=True,
                view_input_sha256=dict(view.inputs),native_battery_validated=False,final_release_validated=False)
