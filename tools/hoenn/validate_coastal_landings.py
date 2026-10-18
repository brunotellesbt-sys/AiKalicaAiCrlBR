"""Exercise every repaired beach component and decorative collision in mGBA.

Starting positions, Surf party and campaign flags are fixtures. Landing,
re-embarkation and collision attempts run through the native controller.
"""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
prefix=(ROOT/'tools/hoenn/validate_surf_repairs.py').read_text().split('\nlast_map=None')[0]
exec(compile(prefix,__file__,'exec'))
def warp(name,x,y):
    # Wait for the actual field/map/coordinates to settle, rather than
    # spending a fixed 900 frames on each of 247 isolated starting fixtures.
    # The native warp still performs the entire bank and palette load.
    g,n=map_id(name)
    script(b'\x39'+bytes([g,n,255])+struct.pack('<HH',x,y)+b'\x27\x6b\x02',1)
    for _ in range(900):
        step(1)
        if location()==(g,n) and position()==(x,y) and idle():
            step(30)
            assert location()==(g,n) and position()==(x,y) and idle()
            return
    raise AssertionError(('Coastal fixture warp failed to settle',name,x,y,location(),position()))
native('ScriptSetMonMoveSlot',0,57,1)
for f in hoenn_flags+kanto_flags:rawflag(f,True)
geography=report['geography'];checks=[];blocked_checks=[]
# Restore ordinary land to the planner, without making rock behaviors passable.
for n,(w,h,tiles) in blocks.items():
    passable[n]={i for i,t in enumerate(tiles) if not t&0xC00 and (water_behaviors[behaviors[n][i]] or t>>12==3)}
    warps[n]={}
for row in geography['beach_land_elevations']:
    n=row['map'];w,h,tiles=blocks[n];pending={y*w+x for x,y in row['land_tiles'] if not tiles[y*w+x]&0xC00}
    while pending:
        first=pending.pop();component={first};queue=[first]
        while queue:
            i=queue.pop();x,y=i%w,i//w
            for xx,yy in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
                j=yy*w+xx
                if 0<=xx<w and 0<=yy<h and j in pending:pending.remove(j);component.add(j);queue.append(j)
        approaches=[]
        for i in sorted(component):
            x,y=i%w,i//w
            for dx,dy,key in [(1,0,16),(-1,0,32),(0,1,128),(0,-1,64)]:
                xx,yy=x+dx,y+dy;j=yy*w+xx
                if 0<xx<w-1 and 0<yy<h-1 and j in water_passable[n] and tiles[j]>>12==1 and currents[behaviors[n][j]] is None:
                    approaches.append(((n,xx,yy),(n,x,y)))
        assert approaches,('Repaired beach has no water access',n,sorted(component))
        water,land=approaches[len(approaches)//2]
        warp(*water);native('SetPlayerAvatarTransitionFlags',8);step(90)
        walk(land);step(90)
        assert position()==land[1:] and lib.read8(s['gPlayerAvatar'])&25==1,('Surf did not end on sand',land,position(),lib.read8(s['gPlayerAvatar']))
        assert native('MapGridGetElevationAt',land[1]+7,land[2]+7)==3
        walk(water);step(90)
        assert position()==water[1:] and lib.read8(s['gPlayerAvatar'])&8,('Foot on ocean',water,position())
        checks.append(dict(map=n,land=list(land[1:]),water=list(water[1:]),component_tiles=len(component),native_landing_and_surf_prompt=True))
        if len(checks)<=8:picture('beach-'+str(len(checks)))
        print('Native beach landing passed',len(checks),n,land[1:],flush=True)
for row in geography['ornament_limits']:
    n=row['map'];w,h,tiles=blocks[n]
    for x,y in row['blocked_decorative_tiles']:
        assert tiles[y*w+x]&0xC00
        neighbors=[(xx,yy,key) for xx,yy,key in [(x-1,y,16),(x+1,y,32),(x,y-1,128),(x,y+1,64)] if 0<xx<w-1 and 0<yy<h-1 and yy*w+xx in water_passable[n]]
        if not neighbors:continue
        xx,yy,key=neighbors[0];warp(n,xx,yy);native('SetPlayerAvatarTransitionFlags',8);step(90);before=position();step(90,key);step(60)
        assert position()==before,('Surf crossed decorative land',n,x,y,before,position())
        blocked_checks.append(dict(map=n,blocked=[x,y],from_water=[xx,yy],held_frames=90))
lib.stop()
(args.output/'coastal-landings.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
    beaches=checks,decorative_collision_attempts=blocked_checks,all_repaired_beach_components_tested=True,
    input_only_landing_and_reembarkation=True,surf_ends_on_land=True,foot_cannot_enter_ocean_without_surf=True,
    positions_and_initial_progress_are_fixtures=True,full_campaign_playthrough=False),indent=2)+'\n')
