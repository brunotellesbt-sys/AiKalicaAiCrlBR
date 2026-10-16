"""Walk the three user-positioned terminals and sail each to Pallet and back."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_sootopolis_harbor.py').read_text().split('\n# Disable Sootopolis')[0]
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_sootopolis_harbor.py'),'exec'))
from prepare_three_harbor_terminals import ARRIVAL

layout=json.loads((source/'.journey-three-harbor-terminals').read_text())
records=[]
for p in layout['ports']:
    name=p['exterior'];inside=p['interior'];tag=inside.removeprefix('Journey')
    city=json.loads((source/f'data/maps/{name}/map.json').read_text())
    room=json.loads((source/f'data/maps/{inside}/map.json').read_text())
    assert not any(o['script']=='Journey_FerryPort'+str(p['pid']) for o in city['object_events'])
    assert len(room['object_events'])==2
    warp(name,*p['start']);native('SetPlayerAvatarTransitionFlags',1);step(30)
    for xy in p['walk']:walk_to(*xy)
    assert not lib.read8(s['gPlayerAvatar']) & 8
    picture(tag+'-front')
    for x,y in p['outside_hull']:
        assert native('MapGridGetCollisionAt',x+7,y+7)!=0
        assert native('MetatileBehavior_IsSurfableWaterOrUnderwater',native('MapGridGetMetatileBehaviorAt',x+7,y+7))
    change_map(64,inside);picture(tag+'-entered');walk_to(*ARRIVAL)
    for x,y in p['inside_hull']:
        assert native('MapGridGetCollisionAt',x+7,y+7)!=0
        assert native('MetatileBehavior_IsSurfableWaterOrUnderwater',native('MapGridGetMetatileBehaviorAt',x+7,y+7))
    talk_up()
    if p['pid']==12:choose(0)  # World ports, preserving Briney's local service.
    choose(0);choose(2)  # Kanto, Pallet.
    trips=[voyage('JourneyPalletHarbor',ARRIVAL)]
    talk_up()
    if p['pid']==12:
        choose(1);choose(0);choose(2)  # Hoenn, west coast, Petalburg.
    else:
        choose(0);choose(2 if p['pid']==19 else 4)
    trips.append(voyage(inside,ARRIVAL))
    picture(tag+'-network-arrival')
    assert native('TrySavingData',0,max_frames=6000)==1;step(60)
    assert native('LoadGameSave',0,max_frames=6000)==1
    lib.write32(s['gMain']+4,s['CB2_ContinueSavedGame']|1);step(1500)
    assert location()==map_id(inside) and position()==ARRIVAL and idle()
    picture(tag+'-continue')
    walk_to(11,13);change_map(128,name)
    for xy in p['return_walk']:walk_to(*xy)
    assert not lib.read8(s['gPlayerAvatar']) & 8
    picture(tag+'-returned')
    if p.get('legacy'):
        old=json.loads((source/f'data/maps/{p["legacy"]}/map.json').read_text())
        exit=old['warp_events'][1];warp(p['legacy'],exit['x'],exit['y']-1)
        change_map(128,name)
        for xy in p['return_walk']:walk_to(*xy)
        picture(tag+'-legacy-exit')
    if p['pid']==12:
        # The same captain still gives access to Briney's unchanged native
        # room; its scripts and the door used by local sailings remain live.
        for xy in p['walk']:walk_to(*xy)
        change_map(64,inside);walk_to(*ARRIVAL);talk_up();choose(1)
        step(500)
        assert location()==map_id('Route104_MrBrineysHouse') and idle()
        picture('Petalburg-Briney-local-room')
        change_map(128,name)
        assert position()==(17,51)
        picture('Petalburg-Briney-exit')
    records.append(dict(name=p['name'],exterior=name,interior=inside,pid=p['pid'],terminal=p['terminal'],
        controller_entry_and_exit=True,quay_walked_without_surf=True,one_indoor_captain=True,
        medium_boat_hull_blocked_over_water=True,inside_ship_hull_blocked_over_water=True,
        captain_interacted_physically=True,network_arrival_inside=True,save_continue_inside=True,
        legacy_exit_preserved=bool(p.get('legacy')),briney_local_service_preserved=p['pid']==12,trips=trips))
lib.stop()
proof=dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),ports=records,
    initial_story_state_and_position_are_fixtures=True,full_campaign_playthrough=False)
(args.output/'three-harbors.json').write_text(json.dumps(proof,indent=2)+'\n')
print('Three terminals: exact bounds, physical doors, two ships, Pallet roundtrips, save/continue and Briney room passed.')
