"""Sail between Hoenn, all seven native Sevii towns and Kanto using input only."""
import ctypes,hashlib,json,subprocess,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
prefix=(ROOT/'tools/hoenn/validate_surf_repairs.py').read_text().split('\nlast_map=None')[0]
exec(compile(prefix,__file__,'exec'))
native('VarSet',0x40FF,4095)
native('ScriptSetMonMoveSlot',0,57,1)
for f in hoenn_flags+kanto_flags:rawflag(f,True)
towns=[r['town'] for r in json.loads((source/'.journey-sevii-surf-connections').read_text())['seamless_connections']]
coasts=set(towns+['MossdeepCity','LavenderTown_Frlg','JourneyLavenderApproach'])
for n,(w,h,tiles) in blocks.items():
    passable[n]={i for i in range(w*h) if not tiles[i]&0xC00 and (n in coasts or water_behaviors[behaviors[n][i]])}
    warps[n]={}
def nearest(n,x,y,wet):
    w,h,_=blocks[n];_,yy,xx=min((abs(xx-x)+abs(yy-y),yy,xx) for yy in range(1,h-1) for xx in range(1,w-1) if yy*w+xx in passable[n] and water_behaviors[behaviors[n][yy*w+xx]]==wet)
    return n,xx,yy
visited=[];samples=0

def walk_observer(before,after):
    global samples
    n,x,y=after;w,h,_=blocks[n]
    if not(0<=x<w and 0<=y<h):return
    # Object coordinates publish the landing tile before the Surf-to-foot
    # animation clears its flag. Wait for that native animation to finish;
    # persistent Surf on land still fails after 30 frames without input.
    wet=water_behaviors[behaviors[n][y*w+x]]
    if bool(lib.read8(s['gPlayerAvatar'])&8)!=wet and not bridge_behaviors.get(behaviors[n][y*w+x],False):step(30)
    if lib.read8(s['gPlayerAvatar'])&8:assert wet,('Surf on dry land after landing settled',after)
    elif wet:assert bridge_behaviors.get(behaviors[n][y*w+x],False),('Foot on water after landing settled',after)
    if not visited or visited[-1]!=n:visited.append(n)
    samples+=1
start=nearest('MossdeepCity',33,18,True);warp(*start);native('SetPlayerAvatarTransitionFlags',8);step(90)
checks=[];encoder=None
if True:
    video=(args.output/'debug.mp4') if os.environ.get('MARINE_DEBUG') else ROOT/'docs/videos/surf-connections-repaired.mp4';video.parent.mkdir(parents=True,exist_ok=True)
    logfile=(args.output/'ffmpeg.log').open('w')
    encoder=subprocess.Popen(['ffmpeg','-y','-hide_banner','-loglevel','warning','-filter_threads','1','-f','rawvideo','-pixel_format','rgba','-video_size','240x160','-framerate','30','-i','pipe:0','-an','-vf','scale=720:480:flags=neighbor','-c:v','libx264','-preset','fast','-threads','1','-crf','23','-pix_fmt','yuv420p','-movflags','+faststart',str(video)],stdin=subprocess.PIPE,stderr=logfile)
    original_step=step;pending=0;recording=True
    def step(n,keys=0):
        global pending
        if not recording:return original_step(n,keys)
        while n:
            chunk=min(n,2-pending);original_step(chunk,keys);pending+=chunk;n-=chunk
            if pending==2:encoder.stdin.write(ctypes.string_at(lib.image(),240*160*4));pending=0
for i,town in enumerate(towns if not os.environ.get('MARINE_DEBUG') else []):
    m=maps[town];w=next(v for v in m['warp_events'] if 'HARBOR' in v['dest_map'])
    land=nearest(town,w['x'],w['y']-1,False)
    walk(land);step(90);assert lib.read8(s['gPlayerAvatar'])&25==1,(town,position())
    picture(town+'-land-arrival');checks.append(dict(town=town,land=list(position()),native_disembark=True))
    print('Hoenn/Sevii native arrival',town,flush=True)
    if i==0:
        recording=False;encoder.stdin.close();assert encoder.wait()==0;encoder=None
# Return through the native network, then walk Kanto -> One Island -> Kanto.
if os.environ.get('MARINE_DEBUG'):walk(nearest('JourneyMossdeepOuterSea',1,11,True))
walk(start);assert lib.read8(s['gPlayerAvatar'])&8
if os.environ.get('MARINE_DEBUG'):raise SystemExit('Debug return completed')
kanto=nearest('JourneyLavenderApproach',10,10,True);walk(kanto);picture('kanto-arrival')
one=nearest(towns[0],4,12,True);walk(one);picture('kanto-to-one')
walk(kanto);picture('one-to-kanto');assert lib.read8(s['gPlayerAvatar'])&8
lib.stop()
(args.output/'marine-network.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
    all_seven_islands_reached_from_mossdeep=True,kanto_to_one_island_and_back=True,returned_to_mossdeep=True,
    controller_movement_only=True,no_midtrip_warps_or_coordinate_writes=True,all_surf_samples_on_water=True,
    samples=samples,maps_visited=visited,towns=checks,initial_party_progress_and_position_are_fixtures=True,
    video_sha256=hashlib.sha256(video.read_bytes()).hexdigest(),full_campaign_playthrough=False),indent=2)+'\n')
