"""Walk all seven terminals, sail to Kanto/Hoenn and preserve native ferry exits."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_sootopolis_harbor.py').read_text().split('\n# Disable Sootopolis')[0]
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_sootopolis_harbor.py'),'exec'))
from prepare_sevii_harbors import ARRIVAL

layout=json.loads((source/'.journey-sevii-harbors').read_text());records=[]
scene=int(re.search(r'#define\s+VAR_MAP_SCENE_ONE_ISLAND_HARBOR\s+(0x\w+)',(source/'include/constants/vars.h').read_text())[1],16)
native('VarSet',scene,3)  # Completed initial native ferry arrival: test fixture.
for i,p in enumerate(layout['ports']):
    name,inside=p['exterior'],p['interior'];tag=p['island']
    city=json.loads((source/f'data/maps/{name}/map.json').read_text())
    room=json.loads((source/f'data/maps/{inside}/map.json').read_text())
    assert city['object_events']==[p['outside_boat'],p['medium_boat']]
    assert len(room['object_events'])==2 and len([o for o in room['object_events'] if o['script']=='Journey_FerryPort'+str(p['pid'])])==1
    warp(name,8,2);native('SetPlayerAvatarTransitionFlags',1);step(30)
    walk_to(7,2);walk_to(7,7);walk_to(13,7);walk_to(13,6)
    assert not lib.read8(s['gPlayerAvatar'])&8
    walk_to(9,6);walk_to(p['pier_x'],7);walk_to(p['pier_x'],10)
    walk_to(p['pier_x']+1,10);walk_to(p['pier_x']+1,7);walk_to(13,7);walk_to(13,6)
    for hull in p['outside_hulls']:
        assert min(y for x,y in hull)>=9
        for x in {x for x,y in hull}:
            assert native('MapGridGetCollisionAt',x+7,8+7)==0
            assert native('MetatileBehavior_IsSurfableWaterOrUnderwater',native('MapGridGetMetatileBehaviorAt',x+7,8+7))
        for x,y in hull:
            assert native('MapGridGetCollisionAt',x+7,y+7)!=0
            assert native('MetatileBehavior_IsSurfableWaterOrUnderwater',native('MapGridGetMetatileBehaviorAt',x+7,y+7))
    picture(tag+'-front')
    change_map(64,inside);picture(tag+'-entered');walk_to(*ARRIVAL)
    for x,y in p['hull']:
        assert native('MapGridGetCollisionAt',x+7,y+7)!=0
        assert native('MetatileBehavior_IsSurfableWaterOrUnderwater',native('MapGridGetMetatileBehaviorAt',x+7,y+7))
    talk_up();choose(0);choose(2)  # Kanto -> Pallet.
    trips=[voyage('JourneyPalletHarbor',ARRIVAL)]
    talk_up();choose(2);choose(i)  # Sevii -> the island being tested.
    trips.append(voyage(inside,ARRIVAL));picture(tag+'-network-arrival')
    assert native('TrySavingData',0,max_frames=6000)==1;step(60)
    assert native('LoadGameSave',0,max_frames=6000)==1
    lib.write32(s['gMain']+4,s['CB2_ContinueSavedGame']|1);step(1500)
    assert location()==map_id(inside) and position()==ARRIVAL and idle()
    picture(tag+'-continue')
    walk_to(11,13);change_map(128,name)
    walk_to(13,7);walk_to(7,7);walk_to(7,2);walk_to(8,2)
    assert not lib.read8(s['gPlayerAvatar'])&8
    picture(tag+'-returned')
    # Existing ferry saves inside the former lodge still have a usable exit.
    legacy='Journey'+tag+'IslandHarborPortLodge'
    old=json.loads((source/f'data/maps/{legacy}/map.json').read_text());exit=old['warp_events'][0]
    warp(legacy,exit['x'],exit['y']-1);change_map(128,name)
    walk_to(13,7);walk_to(7,7);walk_to(7,2)
    picture(tag+'-legacy-exit')
    # The complete bottom water row stays clear below both boats and piers.
    warp(name,2,12);native('SetPlayerAvatarTransitionFlags',8);step(30)
    walk_to(15,12);walk_to(2,12)
    assert lib.read8(s['gPlayerAvatar'])&8
    picture(tag+'-south-surf-lane')
    records.append(dict(island=tag,pid=p['pid'],exterior=name,interior=inside,
        controller_entry_and_exit=True,quay_walked_without_surf=True,small_boat_graphics_preserved=True,
        bridge_extended_three_tiles_and_walked=True,old_boat_gap_filled_and_walked=True,
        boats_clear_of_upper_quay=True,
        medium_boat_hull_blocked_over_water=True,small_boat_hull_blocked_over_water=True,
        one_indoor_captain=True,outside_captain_removed=True,captain_interacted_physically=True,
        ship_hull_blocked_over_water=True,network_arrival_inside=True,save_continue_inside=True,
        old_lodge_exit_preserved=True,south_surf_lane_crossed=True,trips=trips))
    print('Sevii terminal passed:',tag,flush=True)
# A real voyage also links the same terminal network to Hoenn.
one=layout['ports'][0]['interior'];warp(one,*ARRIVAL);native('SetPlayerAvatarTransitionFlags',1);step(30)
talk_up();choose(1);choose(0);choose(0)
hoenn=[voyage('SlateportCity_Harbor',(16,14))]
talk_up();choose(2);choose(0);hoenn.append(voyage(one,ARRIVAL))
picture('hoenn-roundtrip-return')
warp('CinnabarIsland_Frlg',16,16);native('SetPlayerAvatarTransitionFlags',8);step(30)
walk_to(16,15);walk_to(8,15);walk_to(8,19)
assert lib.read8(s['gPlayerAvatar'])&8
change_map(128,'JourneyCinnabarSouthSea')
picture('cinnabar-south-sea-under-pier')
change_map(64,'CinnabarIsland_Frlg')
walk_to(8,15);walk_to(16,15);walk_to(16,16)
assert lib.read8(s['gPlayerAvatar'])&8
warp('CinnabarIsland_Frlg',11,14);native('SetPlayerAvatarTransitionFlags',1);step(30)
walk_to(11,15);walk_to(7,15);change_map(64,'JourneyCinnabarHarbor')
walk_to(11,13);change_map(128,'CinnabarIsland_Frlg')
picture('cinnabar-quay-walked-above')
report=dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
            ports=records,hoenn_roundtrip=hoenn,ship_sprite_size=[96,40],
            cinnabar_surf_under_pier_roundtrip=True,cinnabar_quay_walked_above=True,
            initial_placements_and_story_state_are_fixtures=True,full_campaign_playthrough=False)
lib.stop();(args.output/'sevii-harbors.json').write_text(json.dumps(report,indent=2)+'\n')
print('Seven terminals, seven Kanto roundtrips, Hoenn voyage and local Surf lanes passed.')
