"""Native seven-terminal doors, dry piers and the restored Six Island Center."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_trainer_levels.py').read_text().split('\nchecks=[]')[0]
exec(compile(bootstrap,__file__,'exec'))
ports=json.loads((source/'.journey-sevii-harbors').read_text())['ports']
names=list(dict.fromkeys([p['exterior'] for p in ports]+[p['interior'] for p in ports]+['SixIsland_Frlg','SixIsland_PokemonCenter_1F_Frlg']))
allowed=set();walk_prefix='map-finishing';walk_transition_pictures=False;walk_cache_paths=True;walk_max_ticks=1200
native('RtcInitLocalTimeOffset',12,0)
native('VarSet',0x40FE,7);native('VarSet',0x40FF,4095);team([40,40,40]);native('ScriptSetMonMoveSlot',0,57,1)
for f in hoenn_flags+kanto_flags:rawflag(f,True)
constants=(source/'include/constants/vars.h').read_text()
for varname,value in [('VAR_MAP_SCENE_ONE_ISLAND_HARBOR',3),('VAR_MAP_SCENE_FOUR_ISLAND',1)]:
    native('VarSet',int(re.search(r'^#define\s+'+varname+r'\s+(0x\w+)',constants,re.M)[1],16),value)
exec(compile((ROOT/'tools/hoenn/native_water_walk.py').read_text(),'finishing-native-walker','exec'))
# Start on the real dry apron and walk to the pier. Spawning directly onto
# an elevation-zero bridge initializes a wildcard object elevation, which is
# a fixture artifact rather than an ordinary arrival from the terminal.
full_passable={n:valid.copy() for n,valid in passable.items()}
for n,(w,h,tiles) in blocks.items():
    passable[n]={i for i in passable[n] if not water_behaviors[behaviors[n][i]]}
dry_passable={n:valid.copy() for n,valid in passable.items()}
def player_priority():
    obj=s['gObjectEvents']+lib.read8(s['gPlayerAvatar']+5)*36
    sprite=s['gSprites']+lib.read8(obj+35)*68
    return (lib.read16(sprite+4)>>10)&3
checks=[];pier_save_continue=False
for p in ports:
    passable={n:valid.copy() for n,valid in dry_passable.items()}
    n=p['exterior'];inside=p['interior'];x=p['pier_x']
    warp(n,13,6);native('SetPlayerAvatarTransitionFlags',1);step(90)
    walk((n,x,10));step(60)
    assert player_priority()==1,('Pedestrian hidden under pier',n,player_priority())
    picture(n+'-pier-foot')
    # Probe an actual open water neighbor, rather than assuming the lower
    # map edge is water (Two Island has a native reef there).
    w,h,tiles=blocks[n]
    bridge,water,key=next(((n,xx,yy),(n,xx+dx,yy+dy),key)
        for yy in range(h) for xx in range(w) if tiles[yy*w+xx]>>12==15
        for dx,dy,key in [(1,0,16),(-1,0,32),(0,1,128),(0,-1,64)]
        if 0<xx+dx<w-1 and 0<yy+dy<h-1
        and not tiles[(yy+dy)*w+xx+dx]&0xC00
        and tiles[(yy+dy)*w+xx+dx]>>12==1
        and water_behaviors[behaviors[n][(yy+dy)*w+xx+dx]])
    walk(bridge);step(60)
    before=position();step(90,key);step(60)
    if position()!=before:picture('finishing-pier-failure')
    assert position()==before and lib.read8(s['gPlayerAvatar'])&25==1,('Foot walked into ocean',n,before,position())
    if p['island']=='One':
        assert native('TrySavingData',0,max_frames=6000)==1
        assert native('LoadGameSave',0,max_frames=6000)==1
        lib.write32(s['gMain']+4,s['CB2_ContinueSavedGame']|1);step(1500)
        assert location()==map_id(n) and position()==before
        assert lib.read8(s['gPlayerAvatar'])&25==1 and player_priority()==1
        step(90,key);step(60);assert position()==before
        picture('pier-save-continue');pier_save_continue=True
    walk((inside,16,13));step(60);assert lib.read8(s['gPlayerAvatar'])&25==1
    picture(n+'-inside')
    walk((n,13,6));step(60);assert lib.read8(s['gPlayerAvatar'])&25==1
    picture(n+'-outside')
    passable={n:valid.copy() for n,valid in full_passable.items()}
    warp(*water);native('SetPlayerAvatarTransitionFlags',8);step(90)
    walk(bridge);step(60)
    assert lib.read8(s['gPlayerAvatar'])&8 and player_priority()==2,('Surf drawn above pier',n,player_priority())
    walk(water);step(60);assert lib.read8(s['gPlayerAvatar'])&8
    checks.append(dict(map=n,terminal=inside,controller_door_roundtrip=True,foot_blocks_at_pier_end=True,foot_state_on_dry_terminal=True,
        foot_drawn_above_bridge=True,surf_drawn_below_bridge=True,under_pier_surf_roundtrip=True))
    print('Native terminal finishing passed',n,flush=True)
passable={n:valid.copy() for n,valid in dry_passable.items()}
warp('SixIsland_Frlg',9,12);native('SetPlayerAvatarTransitionFlags',1);step(90)
before=position();step(90,64);step(60);assert position()==before,('Restored Center wall is walkable',before,position())
walk(('SixIsland_Frlg',11,13));step(60)
walk(('SixIsland_PokemonCenter_1F_Frlg',7,7));step(60);picture('six-center-inside')
walk(('SixIsland_Frlg',11,13));step(60);assert lib.read8(s['gPlayerAvatar'])&25==1
walk(('SixIsland_Frlg',11,12));step(300);picture('six-center-restored')
# The old ferry roof is gone; the intact native ramp still reaches the only
# working terminal. Test the public approach and return with controller input.
walk(('SixIsland_Harbor_Frlg',13,6));step(60);picture('six-ramp-main-terminal')
walk(('SixIsland_Frlg',11,22));step(300);picture('six-ramp-without-old-roof')
width,height,tiles=blocks['SixIsland_Frlg']
assert all(tiles[y*width+x]==0x1273 for y in range(24,29) for x in range(8,15))
lib.stop()
(args.output/'map-finishing.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
    ports=checks,native_save_continue_on_pier=pier_save_continue,restored_center_wall_blocks_controller=True,center_door_roundtrip=True,
    six_obsolete_roof_removed=True,six_ramp_main_terminal_controller_roundtrip=True,
    fixture_initial_placements_and_progress=True,full_campaign_playthrough=False),indent=2)+'\n')
