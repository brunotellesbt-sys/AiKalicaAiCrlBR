"""Native seven-terminal doors, dry piers and the restored Six Island Center."""
import hashlib,json,re
from pathlib import Path
from extra_gym_landscape import OBSOLETE_FERRIES,TWO_RAMP_COAST
ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_trainer_levels.py').read_text().split('\nchecks=[]')[0]
exec(compile(bootstrap,__file__,'exec'))
ports=json.loads((source/'.journey-sevii-harbors').read_text())['ports']
landscape=json.loads((source/'.journey-extra-gyms').read_text())['landscape_review']
removals={r['island']:r for r in landscape if r.get('obsolete_ferry_roof_removed')}
coast_marker=source/'.journey-dewford-coast-safety'
piers=json.loads(coast_marker.read_text()).get('piers',{}) if coast_marker.exists() else {}
extended_bridges={r['island']:r for r in piers.get('town_bridges',[])}
deck_cells={(seg['map'],x,y) for r in extended_bridges.values() for seg in r['deck_segments']
            for x in range(seg['footprint'][0],seg['footprint'][0]+seg['footprint'][2])
            for y in range(seg['footprint'][1],seg['footprint'][1]+seg['footprint'][3])}
assert set(removals)=={f['island'] for f in OBSOLETE_FERRIES} and len(removals)==7
names=list(dict.fromkeys([p['exterior'] for p in ports]+[p['interior'] for p in ports]
                       +[f['town'] for f in OBSOLETE_FERRIES]
                       +[e['map'] for f in OBSOLETE_FERRIES for e in f.get('connected_remnants',[])]
                       +['SixIsland_PokemonCenter_1F_Frlg']))
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
    if piers:
        before=position();step(90,{16:32,32:16,64:128,128:64}[key]);step(60)
        assert position()==before and lib.read8(s['gPlayerAvatar'])&8,('Surf entered low pier',n,before,position())
        assert player_priority()==2
        picture(n+'-low-pier-surf-blocked')
    else:
        walk(bridge);step(60)
        assert lib.read8(s['gPlayerAvatar'])&8 and player_priority()==2,('Surf drawn above pier',n,player_priority())
        walk(water);step(60);assert lib.read8(s['gPlayerAvatar'])&8
    checks.append(dict(map=n,terminal=inside,controller_door_roundtrip=True,foot_blocks_at_pier_end=True,foot_state_on_dry_terminal=True,
        foot_drawn_above_bridge=True,surf_drawn_below_bridge=not bool(piers),under_pier_surf_roundtrip=not bool(piers),
        surf_entry_blocked_on_low_deck=bool(piers),
        low_pier_surf_entry_blocked=bool(piers)))
    print('Native terminal finishing passed',n,flush=True)
passable={n:valid.copy() for n,valid in dry_passable.items()}
warp('SixIsland_Frlg',9,12);native('SetPlayerAvatarTransitionFlags',1);step(90)
before=position();step(90,64);step(60);assert position()==before,('Restored Center wall is walkable',before,position())
walk(('SixIsland_Frlg',11,13));step(60)
walk(('SixIsland_PokemonCenter_1F_Frlg',7,7));step(60);picture('six-center-inside')
walk(('SixIsland_Frlg',11,13));step(60);assert lib.read8(s['gPlayerAvatar'])&25==1
walk(('SixIsland_Frlg',11,12));step(300);picture('six-center-restored')
# Every town keeps the native ramp behavior and a matching return. Layer
# 161 extends the ramps and can use private wooden art at their endpoints.
# Placements occur before each roundtrip only.
def assert_cleared_water(name,footprint,water,loaded=False):
    width,height,tiles=blocks[name];x,y,w,h=footprint
    if loaded:assert location()==map_id(name)
    for yy in range(y,y+h):
        for xx in range(x,x+w):
            if (name,xx,yy) in deck_cells:
                assert tiles[yy*width+xx]>>12==3 and not tiles[yy*width+xx]&0xc00
                continue
            assert tiles[yy*width+xx]==water,(name,xx,yy,'Obsolete terminal or water pad remains')
            assert water_behaviors[behaviors[name][yy*width+xx]]
            if loaded:
                assert native('MapGridGetMetatileIdAt',xx+7,yy+7)==water&1023
                assert native('MapGridGetElevationAt',xx+7,yy+7)==1
                assert native('MapGridGetCollisionAt',xx+7,yy+7)==0
ramp_checks=[]
two_coast=next(r for r in landscape if r.get('two_ramp_coast_finished'))
assert two_coast['dry_corridor_unchanged'] and two_coast['western_and_southern_surf_connected']
assert two_coast['model_ramp_to_center_before'] and two_coast['model_ramp_to_center_after']
for ferry in OBSOLETE_FERRIES:
    passable={n:valid.copy() for n,valid in dry_passable.items()}
    town=ferry['town'];harbor=ferry['island']+'Island_Harbor_Frlg';rx,ry=ferry['ramp']
    removal=removals[ferry['island']]
    assert removal['map']==town and removal['roof_footprint']==ferry['roof']
    assert removal['cleared_footprint']==ferry['clear'] and removal['replacement_water_metatile']==ferry['water']
    assert removal['connected_remnants']==ferry.get('connected_remnants',[])
    assert removal['ramp']==ferry['ramp'] and removal['ramp_warp_id']==ferry['ramp_warp']
    assert removal['ramp_warp_unchanged'] and removal['harbor']==harbor
    extension_bridge=extended_bridges.get(ferry['island'])
    endpoint_map,ex,ey=extension_bridge['end'] if extension_bridge else (town,rx,ry)
    endpoint_id=extension_bridge['endpoint_warp_id'] if extension_bridge else ferry['ramp_warp']
    outward=maps[endpoint_map]['warp_events'][endpoint_id];back=maps[harbor]['warp_events'][0]
    assert [outward['x'],outward['y']]==[ex,ey] and outward['elevation']==3
    assert outward['dest_map']==maps[harbor]['id'] and outward['dest_warp_id']=='0'
    assert [back['x'],back['y']]==[8,2] and back['elevation']==3
    assert back['dest_map']==maps[endpoint_map]['id'] and back['dest_warp_id']==str(endpoint_id)
    width,height,tiles=blocks[town]
    ew,eh,et=blocks[endpoint_map]
    expected_endpoint=(extension_bridge['endpoint_metatiles'] if extension_bridge
                       else removal['ramp_metatiles'])
    assert list(et[ey*ew+ex-1:ey*ew+ex+2])==expected_endpoint
    assert arrows[behaviors[endpoint_map][ey*ew+ex]]==128
    hw,hh,ht=blocks[harbor];assert ht[2*hw+8]==0x33fa and arrows[behaviors[harbor][2*hw+8]]==64
    start=(town,21,8) if ferry['island']=='Two' else (town,rx,ry-1)
    warp(*start);native('SetPlayerAvatarTransitionFlags',1);step(90)
    assert position()==start[1:] and lib.read8(s['gPlayerAvatar'])&25==1
    walk((harbor,13,6));step(60)
    assert location()==map_id(harbor) and lib.read8(s['gPlayerAvatar'])&25==1
    assert native('MapGridGetMetatileBehaviorAt',8+7,2+7)==0x64
    picture(ferry['island'].lower()+'-ramp-main-terminal')
    walk(start);step(300)
    assert location()==map_id(town) and position()==start[1:] and lib.read8(s['gPlayerAvatar'])&25==1
    if not extension_bridge:assert native('MapGridGetMetatileBehaviorAt',rx+7,ry+7)==0x65
    assert_cleared_water(town,ferry['clear'],ferry['water'],loaded=True)
    if ferry['island']=='Two':
        assert lib.read8(s['gPlayerAvatar'])&25==1
        picture('two-center-terminal-roundtrip')
        for xx,yy,tile in TWO_RAMP_COAST:
            assert tiles[yy*width+xx]==tile
            assert native('MapGridGetMetatileIdAt',xx+7,yy+7)==tile&1023
            assert native('MapGridGetElevationAt',xx+7,yy+7)==1
            assert native('MapGridGetCollisionAt',xx+7,yy+7)!=0
        walk((town,15,10));step(60);before_position=position();step(90,32);step(60)
        assert position()==before_position and lib.read8(s['gPlayerAvatar'])&25==1
        picture('two-ramp-coast-foot-blocks')
        walk((town,rx,ry-1));step(60)
    for extension in ferry.get('connected_remnants',[]):
        assert_cleared_water(extension['map'],extension['footprint'],extension['water'])
        assert any(r.get('obsolete_ferry_extension_removed') and r['map']==extension['map']
                   and r['cleared_footprint']==extension['footprint'] and r['original_water_connection_preserved']
                   and r['events_and_warps_unchanged'] for r in landscape)
    picture(ferry['island'].lower()+'-ramp-without-old-roof')
    ramp_checks.append(dict(island=ferry['island'],town=town,harbor=harbor,departure=list(start[1:]),
        roof_footprint=ferry['roof'],cleared_footprint=ferry['clear'],replacement_water_metatile=ferry['water'],
        town_ramp=[rx,ry],town_ramp_warp_id=ferry['ramp_warp'],harbor_return=[8,2],harbor_return_warp_id=0,
        obsolete_roof_absent=True,local_ocean_texture_preserved=True,cleared_tiles_native_water_height_one=True,
        native_ramp_tiles_and_warp_ids_preserved=(expected_endpoint==removal['ramp_metatiles']
            and endpoint_map==town and endpoint_id==ferry['ramp_warp']),
        native_ramp_behaviors_and_roundtrip_preserved=True,
        wooden_endcap_without_metal=bool(piers.get('wooden_endcaps')),native_north_arrow_return=True,
        connected_remnants_removed=ferry.get('connected_remnants',[]),
        controller_outbound_to_main_terminal=True,controller_return_to_town=True,foot_state_preserved=True,
        center_terminal_roundtrip=ferry['island']=='Two',
        native_ramp_side_coast_collision_checked=ferry['island']=='Two',
        extended_bridge_endpoint=[endpoint_map,ex,ey],extended_bridge_warp_id=endpoint_id,
        one_ferry_warp_transferred=bool(extension_bridge and ferry['island']=='One')))
    print('Native town ramp and obsolete roof removal passed',town,flush=True)
# Surf remains west of the complete cliff outline and cannot enter the new
# blocking margin. The remaining west/south ocean is checked by the full
# marine-link validator; this probe exercises the edited edge itself.
passable={n:{i for i in valid if water_behaviors[behaviors[n][i]] and not blocks[n][2][i]&0xc00}
          if n=='TwoIsland_Frlg' else set() for n,valid in full_passable.items()}
warp('TwoIsland_Frlg',13,10);native('SetPlayerAvatarTransitionFlags',8);step(90)
before_position=position();step(90,16);step(60)
assert position()==before_position and lib.read8(s['gPlayerAvatar'])&8
walk(('TwoIsland_Frlg',12,13));step(60);assert lib.read8(s['gPlayerAvatar'])&8
picture('two-ramp-coast-surf-blocks')
# The old One Island terminal crossed the map boundary into Treasure Beach.
# Preserve that legitimate water connection and visit its now-clear complete
# footprint by Surf in both directions, without a midtrip placement or warp.
one=OBSOLETE_FERRIES[0];extension=one['connected_remnants'][0]
assert dict(map=maps[extension['map']]['id'],offset=0,direction='down') in maps[one['town']]['connections']
assert dict(map=maps[one['town']]['id'],offset=0,direction='up') in maps[extension['map']]['connections']
passable={n:{i for i in valid if water_behaviors[behaviors[n][i]] and not blocks[n][2][i]&0xc00}
          if n in [one['town'],extension['map']] else set() for n,valid in full_passable.items()}
start=(one['town'],10,18);destination=(extension['map'],10,3)
warp(*start);native('SetPlayerAvatarTransitionFlags',8);step(90);before=len(transitions)
walk(destination);step(60);assert lib.read8(s['gPlayerAvatar'])&8
assert_cleared_water(extension['map'],extension['footprint'],extension['water'],loaded=True)
picture('one-treasure-beach-without-old-terminal')
walk(start);step(60);assert lib.read8(s['gPlayerAvatar'])&8
assert len(transitions)==before+2,('Treasure Beach connection did not cross directly both ways',transitions[before:])
lib.stop()
(args.output/'map-finishing.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
    ports=checks,native_save_continue_on_pier=pier_save_continue,restored_center_wall_blocks_controller=True,center_door_roundtrip=True,
    six_obsolete_roof_removed=True,six_ramp_main_terminal_controller_roundtrip=True,
    all_seven_obsolete_roofs_removed=True,all_seven_ramp_main_terminal_controller_roundtrips=True,ramp_roundtrips=ramp_checks,
    wooden_town_endcaps=bool(piers.get('wooden_endcaps')),
    two_ramp_coast_finished=True,two_center_terminal_controller_roundtrip=True,
    two_ramp_coast_blocks_foot_and_surf=True,two_western_surf_preserved=True,
    one_treasure_beach_obsolete_terminal_completely_removed=True,one_treasure_beach_surf_controller_roundtrip=True,
    fixture_initial_placements_and_progress=True,full_campaign_playthrough=False),indent=2)+'\n')
