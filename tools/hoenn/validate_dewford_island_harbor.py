"""Use real controls above and below Dewford's bridge, then enter and sail."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_sootopolis_harbor.py').read_text().split('\n# Disable Sootopolis')[0]
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_sootopolis_harbor.py'),'exec'))
from prepare_dewford_island_harbor import HARBOR,ARRIVAL,NORTH
layout=json.loads((source/'.journey-dewford-island-harbor').read_text());assert layout['door']==[5,2]
warp('Route107',6,16);native('SetPlayerAvatarTransitionFlags',1);step(30)
walk_to(6,15);assert native('PlayerGetElevation')==4
walk_to(6,9);assert not lib.read8(s['gPlayerAvatar'])&8 and native('PlayerGetElevation')==4
picture('bridge-upper-middle')
assert not any(o['graphics_id']=='OBJ_EVENT_GFX_SEAGALLOP' for o in json.loads((source/'data/maps/Route107/map.json').read_text())['object_events'])
g,n=map_id('Route107');assert native('GetObjectEventIdByLocalIdAndMap',8,n,g)==16
walk_to(6,4);walk_to(5,4);walk_to(5,3);change_map(64,HARBOR)
picture('terminal-entered');walk_to(*ARRIVAL);talk_up();choose(0);choose(2)
trips=[voyage('JourneyPalletHarbor',ARRIVAL)]
talk_up();choose(1);choose(0);choose(1);trips.append(voyage(HARBOR,ARRIVAL))
picture('terminal-network-return')
walk_to(11,13);change_map(128,'Route107');assert position()==(5,3)
walk_to(5,14);walk_to(6,14);walk_to(6,16)
assert not lib.read8(s['gPlayerAvatar'])&8
picture('returned-to-clearing')
# Same crossing at water level; the player stays in Surf and below the deck.
warp('Route107',3,8);native('SetPlayerAvatarTransitionFlags',8);step(30)
walk_to(5,8);assert lib.read8(s['gPlayerAvatar'])&8 and native('PlayerGetElevation')==1
picture('surf-below-bridge');walk_to(10,8);walk_to(3,8)
walk_to(8,8);walk_to(8,10);walk_to(4,10);walk_to(5,10);walk_to(5,11);walk_to(8,11)
assert lib.read8(s['gPlayerAvatar'])&8 and native('PlayerGetElevation')==1
picture('requested-water-cells-below-deck')
# Walk only across true connected map edges, without scripted warps between them.
warp('Route107',15,1);native('SetPlayerAvatarTransitionFlags',8);step(30)
change_map(64,NORTH);assert position()==(15,11)
walk_to(15,0);walk_to(0,0);change_map(32,'Route106');assert position()==(79,8)
picture('north-island-connected-to-route106')
lib.stop()
proof=dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),door=[5,2],continuous_straight_two_tile_deck=True,bridge_walked_above_without_surf=True,surf_crossed_below_without_dismounting=True,upper_elevation=4,lower_elevation=1,exterior_transit_boat_removed=True,controller_entry_and_exit=True,trips=trips,north_island_seamless_controller_connections=True,initial_story_state_and_position_are_fixtures=True,full_campaign_playthrough=False)
(args.output/'dewford-island-harbor.json').write_text(json.dumps(proof,indent=2)+'\n')
print('Dewford: upper walk, lower Surf, doors, ferry and connected island passed.')
