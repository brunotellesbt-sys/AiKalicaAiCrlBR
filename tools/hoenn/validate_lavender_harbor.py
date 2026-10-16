"""Walk Lavender's new terminal and sail Pallet roundtrip using native controls."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
bootstrap = (ROOT/'tools/hoenn/validate_sootopolis_harbor.py').read_text().split('\n# Disable Sootopolis')[0]
exec(compile(bootstrap, str(ROOT/'tools/hoenn/validate_sootopolis_harbor.py'), 'exec'))
from prepare_lavender_harbor import ARRIVAL, CAPTAIN, DOOR, EXTERIOR, HARBOR

layout = json.loads((source/'.journey-lavender-harbor').read_text())
city = json.loads((source/f'data/maps/{EXTERIOR}/map.json').read_text())
interior = json.loads((source/f'data/maps/{HARBOR}/map.json').read_text())
assert not any(o['script']=='Journey_FerryPort0' for o in city['object_events'])
assert len([o for o in interior['object_events'] if o['script']=='Journey_FerryPort0'])==1
assert len(interior['object_events'])==2
assert [o for o in interior['object_events'] if o['script']=='Journey_FerryPort0'][0]['x']==CAPTAIN[0]
warp(EXTERIOR, 12, 44)
native('SetPlayerAvatarTransitionFlags', 1)
step(30)
walk_to(DOOR[0],44)
walk_to(DOOR[0],DOOR[1]+1)
picture('terminal-front-walked')
change_map(64,HARBOR)
picture('terminal-entered')
walk_to(*ARRIVAL)
assert not lib.read8(s['gPlayerAvatar']) & 8
for x,y in layout['hull']:
    assert native('MapGridGetCollisionAt',x+7,y+7)!=0
    assert native('MetatileBehavior_IsSurfableWaterOrUnderwater', native('MapGridGetMetatileBehaviorAt',x+7,y+7))
graphics = s['gObjectEventGraphicsInfo_SSTidal']
assert [lib.read16(graphics+8),lib.read16(graphics+10)]==[96,40]
talk_up()
picture('lavender-world-port-menu')
choose(0)  # KANTO, with current Lavender omitted.
choose(1)  # PALLET.
trips = [voyage('JourneyPalletHarbor',ARRIVAL)]
talk_up()
choose(0)
choose(0)  # LAVENDER, with current Pallet omitted.
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
walk_to(13,44)
walk_to(7,44)
assert not lib.read8(s['gPlayerAvatar']) & 8
picture('returned-to-original-pier')
# An old save inside the replaced cottage must still have a working exit.
warp('JourneyRoute12SailorsLodge',5,9)
change_map(128,EXTERIOR)
walk_to(DOOR[0],44)
assert not lib.read8(s['gPlayerAvatar']) & 8
picture('legacy-lodge-exit')
report = dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
              controller_entry_and_exit=True, captain_interacted_physically=True,
              outside_captain_removed=True, one_indoor_captain=True,
              ship_sprite_size=[96,40],ship_hull_blocked_over_water=True,
              network_arrivals_inside_terminal=True,save_continue_inside_terminal=True,
              returned_to_original_pier=True,old_lodge_exit_walked=True,trips=trips,
              initial_story_state_and_first_placement_are_fixtures=True,full_campaign_playthrough=False)
lib.stop()
(args.output/'lavender-harbor.json').write_text(json.dumps(report,indent=2)+'\n')
print('Lavender: pier, terminal doors, ship, indoor captain, Pallet roundtrip and save/continue passed.')
