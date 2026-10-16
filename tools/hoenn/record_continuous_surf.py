"""Record real controller-driven Mossdeep -> One Island Surf on release ROM."""
import ctypes, hashlib, json, re, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/hoenn'))
bootstrap=(ROOT/'tools/hoenn/validate_sevii_surf_connections.py').read_text().split('\nstart=nearest(')[0]
bootstrap=bootstrap.replace('(n in towns or water_behaviors','(n in towns or n == "MossdeepCity" or water_behaviors')
exec(compile(bootstrap,__file__,'exec'))
# Only the departure city and the destination island can be walked on.
# All other maps are crossed on collision-free native Surf water/low bridges.
for n,valid in passable.items():
    if n not in ['MossdeepCity','OneIsland_Frlg']:
        passable[n]={i for i in valid if water_behaviors[behaviors[n][i]] and
            (blocks[n][2][i]>>12==1 or blocks[n][2][i]>>12==0 and bridge_behaviors[behaviors[n][i]])}
start=nearest('MossdeepCity',28,18,False)
land=nearest('OneIsland_Frlg',12,17,False)
center=nearest('OneIsland_Frlg',14,7,False)
water=nearest('MossdeepCity',16,28,True)
port=nearest('OneIsland_Harbor_Frlg',15,12,True)
native('VarSet',scene,1)
warp(*start);native('SetPlayerAvatarTransitionFlags',1);step(60)
assert idle() and (by_location[location()],*position())==start
assert not lib.read8(s['gPlayerAvatar'])&8
print('Itinerary:',start,water,port,land,center,flush=True)
# Preserve the native planner/controller walker while avoiding its test-only
# 42-frame idle pause after every tile. All movement is ordinary held D-pad.
walker=(ROOT/'tools/hoenn/native_water_walk.py').read_text().split('\ndef walk(goal):',1)[1]
walker='def walk(goal):'+walker
walker=walker.replace('step(30)','step(2)').replace('step(12)','step(1)')
exec(compile(walker,'continuous-controller-walker','exec'))
video=args.output/'mossdeep-one-island-surf.mp4'
log=(args.output/'ffmpeg.log').open('w')
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
filters=("scale=960:640:flags=neighbor,pad=960:736:0:48:color=0x111827,"
         f"drawtext=fontfile={font}:text='Mossdeep → One Island  |  Surf':fontcolor=white:fontsize=24:x=(w-tw)/2:y=12,"
         f"drawtext=fontfile={font}:text='Hoenn · Kanto · Sevii | Oceano contínuo':fontcolor=0xcbd5e1:fontsize=19:x=(w-tw)/2:y=690")
encoder=subprocess.Popen(['ffmpeg','-y','-hide_banner','-loglevel','warning','-f','rawvideo','-pixel_format','rgba',
    '-video_size','240x160','-framerate','30','-i','pipe:0','-an','-vf',filters,'-c:v','libx264','-preset','fast',
    '-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(video)],stdin=subprocess.PIPE,stderr=log)
base_step=step
native_frames=0;pending_capture=0;captured=0;route=[];samples=[];surf_frames=0
seam_palettes=[];last_frame_map=start[0];last_frame_colors=None;recording=True
def water_colors():
    indices=[3,4,5,7]
    return [lib.read16(0x05000000+2*(4*16+i)) for i in indices]
last_frame_colors=water_colors()
last_map=None

def capture():
    global captured
    if not recording:return
    encoder.stdin.write(ctypes.string_at(lib.image(),240*160*4));captured+=1

def step(n,keys=0):
    global native_frames,pending_capture,surf_frames,last_frame_map,last_frame_colors
    while n:
        chunk=min(n,2-pending_capture)
        base_step(chunk,keys);native_frames+=chunk;pending_capture+=chunk;n-=chunk
        name=by_location.get(location());colors=water_colors()
        if name!=last_frame_map:
            assert last_frame_colors==colors,('Ocean palette changed at map seam',last_frame_map,name,last_frame_colors,colors)
            assert not lib.read32(s['gPaletteFade']+12)&0x80000000
            seam_palettes.append(dict(source=last_frame_map,destination=name,before=last_frame_colors,after=colors,frame=native_frames))
        last_frame_map,last_frame_colors=name,colors
        if lib.read8(s['gPlayerAvatar'])&8:surf_frames+=chunk
        if pending_capture==2:capture();pending_capture=0

def walk_observer(before,after):
    global last_map
    current=by_location[location()]
    sample=dict(frame=native_frames,seconds=round(native_frames/60,3),map=current,tile=list(position()),surf=bool(lib.read8(s['gPlayerAvatar'])&8))
    samples.append(sample)
    if current!=last_map:
        route.append(sample);last_map=current
        print('Video arrival:',sample,flush=True)
    if before[0]!=after[0]:
        assert lib.read8(s['gPlayerAvatar'])&8,('Map seam lost Surf',before,after)

capture();picture('departure-mossdeep');step(120)
walk_observer(start,start)
failed=True
try:
    walk(water);step(45)
    assert lib.read8(s['gPlayerAvatar'])&8
    picture('mossdeep-surf-departure')
    walk(nearest('Route124',46,0,True))
    walk(nearest('JourneyNorthHoennStrait',14,1,True))
    walk(port);step(90)
    assert lib.read8(s['gPlayerAvatar'])&8
    picture('one-island-harbor-surf-arrival')
    walk(land);step(60)
    assert lib.read8(s['gPlayerAvatar'])&25==1
    picture('one-island-disembarked')
    walk(center);step(180)
    assert (by_location[location()],*position())==center and idle()
    assert lib.read8(s['gPlayerAvatar'])&25==1
    picture('arrival-one-island')
    assert surf_prompts,'Surf was not activated through the native controller prompt'
    assert surf_frames>100 and transitions
    proof=dict(passed=True,
        rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),departure=list(start),
        arrival=[by_location[location()],*position()],route=route,transitions=transitions,walked_tiles=walked,
        native_frames=native_frames,captured_frames=captured,video_fps=30,video_seconds=captured/30,
        surf_frames=surf_frames,surf_prompts=surf_prompts,native_surf_and_disembark=True,
        controller_movement_only=True,no_midroute_warps_or_coordinate_writes=True,seam_palette_samples=seam_palettes,all_seam_ocean_colors_identical=True,
        initial_party_story_and_departure_are_fixtures=True,continuous_video=True,audio=False,samples=samples)
    failed=False
finally:
    encoder.stdin.close();rc=encoder.wait();log.close();lib.stop()
    assert rc==0,('Video encoding failed',rc)
if not failed:
    proof['video_sha256']=hashlib.sha256(video.read_bytes()).hexdigest()
    (args.output/'continuous-ocean.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
    print('Recorded continuous native Surf:',video,round(proof['video_seconds'],2),'seconds',flush=True)
