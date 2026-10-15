"""Visit all seven native Sevii shores from the world sea using controller Surf.

One starting placement, party, defeated trainers and Repel are fixtures. Travel,
disembarking, the return and Save/Continue are native. No port changes are made.
"""
import ctypes,hashlib,json,re,struct
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
exec(compile((ROOT/'tools/hoenn/validate_team_missions.py').read_text().split('\nassert pending(True) == 7')[0],__file__,'exec'))
report=json.loads((source/'.journey-sevii-surf-connections').read_text())
allmaps={p.parent.name:json.loads(p.read_text()) for p in (source/'data/maps').glob('*/map.json')}
names=sorted(n for n,m in allmaps.items() if m['map_type'] in ['MAP_TYPE_ROUTE','MAP_TYPE_CITY','MAP_TYPE_TOWN','MAP_TYPE_OCEAN_ROUTE'] or 'Harbor' in n and m.get('connections'))
allowed=set();walk_prefix='sevii';walk_cache_paths=True;walk_max_ticks=3000;walk_transition_pictures=False
native('VarSet',0x40FE,7);rawflag(lib.read16(s['gBadgeFlags'])-7,True)
for tid in range(1,1589):rawflag(0x500+tid,True)
native('ScriptSetMonMoveSlot',0,57,1);native('AddBagItem',102,999);native('AddBagItem',116,999)
native('VarSet',0x4021,65535);native('VarSet',0x4120,65535)
scene=int(re.search(r'#define\s+VAR_MAP_SCENE_ONE_ISLAND_HARBOR\s+(0x\w+)',(source/'include/constants/vars.h').read_text())[1],16)
native('VarSet',scene,1)
exec(compile((ROOT/'tools/hoenn/native_water_walk.py').read_text(),'native-surf-walker','exec'))
towns={r['town'] for r in report['seamless_connections']};harbors={r['harbor'] for r in report['seamless_connections']}
for n,(w,h,tiles) in blocks.items():
    # The journey cannot take a door or an invisible old ferry warp shortcut.
    passable[n]={i for i in passable[n] if not tiles[i]&0xC00 and (n in towns or water_behaviors[behaviors[n][i]]) and not ((i%w,i//w) in warps[n] and step_warps.get(behaviors[n][i],False))}
    warps[n]={}

def wet(n,x,y):
    w,h,t=blocks[n];return 0<=x<w and 0<=y<h and y*w+x in passable[n] and water_behaviors[behaviors[n][y*w+x]]

def nearest(n,x,y,water):
    w,h,t=blocks[n]
    _,yy,xx=min((abs(xx-x)+abs(yy-y),yy,xx) for yy in range(1,h-1) for xx in range(1,w-1) if yy*w+xx in passable[n] and water_behaviors[behaviors[n][yy*w+xx]]==water)
    return n,xx,yy

geometry=json.loads((source/'.journey-navigated-sea-atlas').read_text());gps={}
for i,p in enumerate(geometry['projections']):
    at=s['sWorldTileGrids']+12*i;gps[map_id(p['map'])]=(lib.read32(at),lib.read16(at+6),lib.read16(at+8))
def marker():
    first,w,h=gps[location()];x,y=position();assert 0<=x<w and 0<=y<h,(location(),x,y)
    packed=lib.read16(s['sWorldNavigationPixels']+2*(first+y*w+x));return[packed&255,packed>>8]

start=nearest('JourneyWorldSea01',32,8,True);warp(*start);native('SetPlayerAvatarTransitionFlags',8);step(30)
assert idle() and (by_location[location()],*position())==start
samples=[dict(map=start[0],tile=list(start[1:]),marker=marker())];visited=[];seam_frames={r['town']:[] for r in report['seamless_connections']};observed_seams=[]
monitor=True;frame_count=0;active_fade_frames=0
original_step=step
def step(n,keys=0):
    global frame_count,active_fade_frames
    current=by_location.get(location());x,y=position();near=current in towns and x<=4 or current in harbors and x>=blocks[current][0]-5
    if not monitor or not near:return original_step(n,keys)
    for _ in range(n):
        original_step(1,keys);frame_count+=1
        # This pinned PaletteFadeControl word packs active in bit 31.
        active_fade_frames+=bool(lib.read32(s['gPaletteFade']+12)&0x80000000)
        current=by_location.get(location());town=next((r['town'] for r in report['seamless_connections'] if current in [r['town'],r['harbor']]),None)
        if town and frame_count%8==0 and len(seam_frames[town])<110:
            pixels=ctypes.string_at(lib.image(),240*160*4);im=Image.frombytes('RGBA',(240,160),pixels).convert('RGB')
            assert np.asarray(im).max()>32,('Black screen at Surf seam',current,position())
            seam_frames[town].append(im)

def walk_observer(before,after):
    p=marker();assert max(abs(a-b) for a,b in zip(samples[-1]['marker'],p))<=2,(before,after,samples[-1]['marker'],p)
    samples.append(dict(map=after[0],tile=list(after[1:]),marker=p))
    if before[0]!=after[0] and (before[0] in towns or after[0] in towns):
        assert lib.read8(s['gPlayerAvatar'])&8,('Surf mode lost at island seam',before,after)
        observed_seams.append(dict(source=list(before),destination=list(after),surf_preserved=True))

for r in report['seamless_connections']:
    town,harbor=r['town'],r['harbor'];hw=blocks[harbor][0]
    ys=[y for y in r['shared_water_rows'] if wet(harbor,hw-1,y) and wet(town,0,y-r['offset'])]
    assert ys,('Blocked native island seam',town)
    y=ys[len(ys)//2];shore=(town,1,y-r['offset'])
    try:walk(shore)
    except AssertionError:
        current=by_location[location()];w,h,_=blocks[current]
        print('Blocked coast native tiles:',current,position(),[(yy,hex(native('MapGridGetMetatileIdAt',8,yy+7)),native('MapGridGetCollisionAt',8,yy+7)) for yy in range(h)],flush=True)
        raise
    picture(town+'-surf-arrival')
    # Reach actual native dry land rather than stopping in the adjacent ocean.
    native_harbor=next(w for w in maps[town]['warp_events'] if w['dest_map']==maps[harbor]['id'])
    land=nearest(town,native_harbor['x'],native_harbor['y']-1,False);walk(land)
    assert lib.read8(s['gPlayerAvatar'])&25==1,(town,'Did not disembark',position())
    picture(town+'-native-land');visited.append(dict(map=town,land=list(position()),surf_arrival=list(shore[1:]),native_disembark=True))
    walk((harbor,hw-2,y));assert lib.read8(s['gPlayerAvatar'])&8
    print('Continuous Surf visit and return:',town,flush=True)
walk(start);assert (by_location[location()],*position())==start
assert active_fade_frames==0,('Screen fade at an island coast',active_fade_frames)
assert native('VarGet',scene)==3,'First-arrival ferry warp was not suppressed for Surf'
monitor=False
before=(location(),position(),lib.read8(s['gPlayerAvatar'])&25)
assert native('TrySavingData',0,max_frames=6000)==1 and native('LoadGameSave',0,max_frames=6000)==1
lib.write32(s['gMain']+4,s['CB2_ContinueSavedGame']|1);step(1500);finish()
assert before==(location(),position(),lib.read8(s['gPlayerAvatar'])&25);picture('saved-world-sea-return')
for town,frames in seam_frames.items():
    assert frames,town
    frames[0].save(args.output/(town+'-seamless-surf.gif'),save_all=True,append_images=frames[1:],duration=133,loop=0)
assert len(observed_seams)==14,observed_seams
lib.stop();(args.output/'sevii-surf-connections.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),islands=visited,seams=observed_seams,walked_tiles=walked,transitions=transitions,marker_samples=samples,observed_seam_frames=frame_count,active_screen_fade_frames=active_fade_frames,controller_roundtrip=True,native_disembark=True,no_midroute_warps_or_coordinate_writes=True,save_continue_preserves_location=True,first_arrival_surf_does_not_trigger_ferry_cutscene=True,initial_party_flags_and_position_are_fixtures=True,full_campaign_playthrough=False),indent=2)+'\n')
print('Seven native island coasts passed:',walked,'controller tiles;',frame_count,'seam frames',flush=True)
