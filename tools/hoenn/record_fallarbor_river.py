"""Record the actual Western River seam, Waterfall climb and Fallarbor arrival."""
import ctypes
import hashlib
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_sevii_surf_connections.py').read_text().split('\ntowns=')[0]
exec(compile(bootstrap,__file__,'exec'))
permitted={'JourneyWestRiver','Route114','FallarborTown','JourneyCinnabarSouthSea','JourneyRustboroCoast'}
for n in passable:
    if n not in permitted:passable[n]=set()
    else:
        w,h,tiles=blocks[n]
        passable[n]={i for i in passable[n] if not ((i%w,i//w) in warps[n] and step_warps.get(behaviors[n][i],False))}
for f in hoenn_flags:rawflag(f,True)
native('ScriptSetMonMoveSlot',0,57,1)
native('ScriptSetMonMoveSlot',0,127,2)
falls=[(i%blocks['Route114'][0],i//blocks['Route114'][0]) for i,b in enumerate(behaviors['Route114']) if b==19]
assert falls
x=sorted(x for x,y in falls)[len(falls)//2]
bottom=max(y for xx,y in falls if xx==x);top=min(y for xx,y in falls if xx==x)
front=('Route114',x,bottom+1)
for xx,yy in falls:passable['Route114'].discard(yy*blocks['Route114'][0]+xx)
start=('JourneyWestRiver',12,8)
assert not water_behaviors[behaviors[start[0]][start[2]*blocks[start[0]][0]+start[1]]]
native('RtcInitLocalTimeOffset',12,0)  # Daylight is a presentation fixture.
warp(*start);native('SetPlayerAvatarTransitionFlags',1);step(90);assert idle()

walker=(ROOT/'tools/hoenn/native_water_walk.py').read_text().split('\ndef walk(goal):',1)[1]
walker='def walk(goal):'+walker
walker=walker.replace('step(30)','step(2)').replace('step(12)','step(1)')
walker=walker.replace('        if tick % 100 == 0:',
    '        width,height,_=blocks[now[0]]\n'
    '        if not (0<=now[1]<width and 0<=now[2]<height):\n'
    '            step(1)\n'
    '            continue\n'
    '        if tick % 100 == 0:')
exec(compile(walker,'river-controller-walker','exec'))
video=ROOT/'docs/videos/western-river-fallarbor.mp4';video.parent.mkdir(parents=True,exist_ok=True)
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
filters=("scale=960:640:flags=neighbor,pad=960:736:0:48:color=0x111827,"
    f"drawtext=fontfile={font}:text='Western River → Rota 114 → Fallarbor':fontcolor=white:fontsize=23:x=(w-tw)/2:y=12,"
    f"drawtext=fontfile={font}:text='Surf e Waterfall | Captura real em mGBA':fontcolor=0xcbd5e1:fontsize=20:x=(w-tw)/2:y=690")
log=(args.output/'ffmpeg.log').open('w')
encoder=subprocess.Popen(['ffmpeg','-y','-hide_banner','-loglevel','warning','-filter_threads','1','-f','rawvideo','-pixel_format','rgba',
    '-video_size','240x160','-framerate','30','-i','pipe:0','-an','-vf',filters,'-c:v','libx264','-preset','fast',
    '-threads','1','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(video)],stdin=subprocess.PIPE,stderr=log)
base_step=step;frames=captured=pending_capture=0;recording=True;samples=[];route=[]
def capture():
    global captured
    encoder.stdin.write(ctypes.string_at(lib.image(),240*160*4));captured+=1
def step(n,keys=0):
    global frames,pending_capture
    while n:
        chunk=min(n,2-pending_capture);base_step(chunk,keys);frames+=chunk;pending_capture+=chunk;n-=chunk
        if pending_capture==2:capture();pending_capture=0
def walk_observer(before,after):
    sample=dict(frame=frames,map=by_location[location()],tile=list(position()),surf=bool(lib.read8(s['gPlayerAvatar'])&8))
    samples.append(sample)
    if sample['surf']:
        w,h,tiles=blocks[sample['map']];i=sample['tile'][1]*w+sample['tile'][0]
        if 0<=sample['tile'][0]<w and 0<=sample['tile'][1]<h:
            assert water_behaviors[behaviors[sample['map']][i]], ('Surf over dry land',sample)
    if not route or route[-1]['map']!=sample['map']:route.append(sample);print('River arrival:',sample,flush=True)

capture();step(90);picture('river-departure');walk_observer(start,start)
failed=True
try:
    walk(('JourneyWestRiver',25,7));step(90)
    assert surf_prompts and lib.read8(s['gPlayerAvatar'])&8
    walk((front[0],front[1],front[2]+1));walk(front)
    assert lib.read8(s['gPlayerAvatar'])&8;picture('waterfall-below');step(90)
    below=position()
    press(1);picture('waterfall-dialogue')
    for _ in range(400):
        if idle() and position()[1]<top:break
        press(1)
    else:
        picture('waterfall-climb-failed')
        raise AssertionError(('Waterfall climb did not complete',position(),front,top,bottom))
    above=position();assert above[1]<top and below[1]>bottom;picture('waterfall-above');step(120)
    # The upper pool is a side visit. Descend the same real waterfall, then
    # use the main river shore to reach Fallarbor's existing road.
    for _ in range(700):
        if position()[1]>bottom and idle():break
        step(2,128)
    else:raise AssertionError(('Waterfall descent did not complete',position()))
    step(60);picture('waterfall-returned')
    walk(('Route114',20,13));step(120);picture('route114-disembarked')
    assert not lib.read8(s['gPlayerAvatar'])&8
    for n in ['Route114','FallarborTown']:
        passable[n]={i for i in passable[n] if not water_behaviors[behaviors[n][i]]}
    walk(('FallarborTown',14,8));step(180);picture('fallarbor-arrival')
    assert idle() and location()==map_id('FallarborTown') and not lib.read8(s['gPlayerAvatar'])&8
    assert any(t['source'][0]=='JourneyWestRiver' and t['destination'][0]=='Route114' for t in transitions)
    proof=dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
        departure=list(start),arrival=['FallarborTown',*position()],route=route,transitions=transitions,
        waterfall_front=list(front),waterfall_below=list(below),waterfall_above=list(above),
        departure_on_walkable_beach=True,native_surf_prompt=True,native_disembark_before_city=True,
        native_waterfall_climb_and_descent=True,continuous_video=True,
        all_observed_surf_tiles_are_water=True,city_walk_excludes_water_tiles=True,
        river_seam_enters_below_waterfall=True,upper_pool_is_side_visit=True,
        controller_movement_only=True,no_midroute_warps_or_coordinate_writes=True,
        initial_party_badges_story_and_departure_are_fixtures=True,native_frames=frames,
        daylight_clock_fixture=True,
        captured_frames=captured,video_fps=30,video_seconds=captured/30,samples=samples)
    failed=False
finally:
    encoder.stdin.close();rc=encoder.wait();log.close();lib.stop();assert rc==0
if not failed:
    proof['video_sha256']=hashlib.sha256(video.read_bytes()).hexdigest()
    (args.output/'fallarbor-river.json').write_text(json.dumps(proof,indent=2)+'\n')
    print('Fallarbor Surf/Waterfall video:',video,proof['video_seconds'],flush=True)
