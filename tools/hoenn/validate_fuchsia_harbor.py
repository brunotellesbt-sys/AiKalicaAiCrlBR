"""Walk Fuchsia's new quay, enter its terminal and sail to Pallet and back."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_sootopolis_harbor.py').read_text().split('\n# Disable Sootopolis')[0]
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_sootopolis_harbor.py'),'exec'))
from prepare_fuchsia_harbor import ARRIVAL,CAPTAIN,DOOR,EXTERIOR,HARBOR

layout=json.loads((source/'.journey-fuchsia-harbor').read_text())
city=json.loads((source/f'data/maps/{EXTERIOR}/map.json').read_text())
interior=json.loads((source/f'data/maps/{HARBOR}/map.json').read_text())
assert not any(o['script']=='Journey_FerryPort20' for o in city['object_events'])
assert len(interior['object_events'])==2
assert len([o for o in interior['object_events'] if o['script']=='Journey_FerryPort20'])==1
warp(EXTERIOR,11,13)
native('SetPlayerAvatarTransitionFlags',1)
step(30)
walk_to(8,13)
walk_to(8,16)
walk_to(DOOR[0],16)
assert not lib.read8(s['gPlayerAvatar']) & 8
picture('terminal-front-walked')
# The medium ferry is solid over actual ocean, without covering the footway.
for x,y in layout['outside_hull']:
    assert native('MapGridGetCollisionAt',x+7,y+7)!=0
    assert native('MetatileBehavior_IsSurfableWaterOrUnderwater',native('MapGridGetMetatileBehaviorAt',x+7,y+7))
graphics=s['gObjectEventGraphicsInfo_Seagallop']
assert [lib.read16(graphics+8),lib.read16(graphics+10)]==[64,64]
change_map(64,HARBOR)
picture('terminal-entered')
walk_to(*ARRIVAL)
for x,y in layout['hull']:
    assert native('MapGridGetCollisionAt',x+7,y+7)!=0
    assert native('MetatileBehavior_IsSurfableWaterOrUnderwater',native('MapGridGetMetatileBehaviorAt',x+7,y+7))
graphics=s['gObjectEventGraphicsInfo_SSTidal']
assert [lib.read16(graphics+8),lib.read16(graphics+10)]==[96,40]
talk_up()
picture('fuchsia-world-port-menu')
choose(0)  # Kanto.
choose(2)  # Pallet, with current Fuchsia omitted.
trips=[voyage('JourneyPalletHarbor',ARRIVAL)]
talk_up()
choose(0)
choose(3)  # Fuchsia, with current Pallet omitted.
trips.append(voyage(HARBOR,ARRIVAL))
picture('network-arrival-inside')
assert native('TrySavingData',0,max_frames=6000)==1
step(60)
assert native('LoadGameSave',0,max_frames=6000)==1
lib.write32(s['gMain']+4,s['CB2_ContinueSavedGame']|1)
step(1500)
assert location()==map_id(HARBOR) and position()==ARRIVAL and idle()
picture('continue-inside-terminal')
walk_to(11,13)
change_map(128,EXTERIOR)
walk_to(8,16)
walk_to(8,18)
picture('medium-boat-beside-pier')
walk_to(8,13)
walk_to(11,13)
assert not lib.read8(s['gPlayerAvatar']) & 8
picture('returned-to-original-beach')
# An old save inside the cottage can still exit to the new working quay.
warp('JourneyRoute19PortLodge',4,6)
change_map(128,EXTERIOR)
walk_to(8,16)
walk_to(8,13)
walk_to(11,13)
picture('legacy-lodge-exit')
report=dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
    controller_entry_and_exit=True,quay_walked_without_surf=True,
    outside_captain_removed=True,one_indoor_captain=True,captain_interacted_physically=True,
    medium_boat_sprite_size=[64,64],medium_boat_hull_blocked_over_water=True,
    ship_sprite_size=[96,40],ship_hull_blocked_over_water=True,
    network_arrivals_inside_terminal=True,save_continue_inside_terminal=True,
    returned_to_original_beach=True,old_lodge_exit_walked=True,trips=trips,
    initial_story_state_and_first_placement_are_fixtures=True,full_campaign_playthrough=False)
lib.stop()
(args.output/'fuchsia-harbor.json').write_text(json.dumps(report,indent=2)+'\n')
print('Fuchsia: doors, quay, two ships, indoor captain, Pallet roundtrip and save/continue passed.')
