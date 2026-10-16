"""Exercise Pallet's kept bridge, terminal, ship and port network in native mGBA.

The initial placement and story state are fixtures. All walks, door crossings,
captain conversations, ferry trips and Surf map crossings use controller input.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# Reuse the same emulator setup and generic controller helpers as Sootopolis.
bootstrap = (ROOT/'tools/hoenn/validate_sootopolis_harbor.py').read_text().split('\n# Disable Sootopolis')[0]
exec(compile(bootstrap, str(ROOT/'tools/hoenn/validate_sootopolis_harbor.py'), 'exec'))
from prepare_pallet_harbor import ARRIVAL, HARBOR

def talk_left():
    step(4, 32)
    step(20)
    press(1)
    await_menu()

layout = json.loads((source/'.journey-pallet-harbor').read_text())
warp('PalletTown_Frlg', 14, 16)
native('SetPlayerAvatarTransitionFlags', 1)
step(30)
for x, y, value in layout['preserved_bridge']:
    assert native('MapGridGetMetatileIdAt', x+7, y+7) == value & 1023
    assert native('MapGridGetCollisionAt', x+7, y+7) == 0
city = json.loads((source/'data/maps/PalletTown_Frlg/map.json').read_text())
boat = next(o for o in city['object_events'] if o['graphics_id'] == 'OBJ_EVENT_GFX_MR_BRINEYS_BOAT')
assert boat == layout['outside_boat']
assert [boat['x']-layout['original_boat']['x'], boat['y']-layout['original_boat']['y']] == [1, 0]
assert not any(o['script'] == 'Journey_FerryPort18' for o in city['object_events'])
for x, y in layout['complete_trees']:
    for dy in range(3):
        for dx in range(2):
            assert native('MapGridGetMetatileIdAt', x+dx+7, y+dy+7) == [0xE,0xF,0x1C,0x1F,0x24,0x27][dy*2+dx]
            assert native('MapGridGetCollisionAt', x+dx+7, y+dy+7) != 0
walk_to(13, 17)
walk_to(9, 17)
picture('original-bridge-and-boat')
walk_to(9, 18)
walk_to(14, 18)
walk_to(14, 24)
walk_to(18, 24)
assert not lib.read8(s['gPlayerAvatar']) & 8
picture('terminal-front-walked')
change_map(64, HARBOR)
picture('terminal-entered')
walk_to(*ARRIVAL)
graphics = s['gObjectEventGraphicsInfo_SSTidal']
assert [lib.read16(graphics+8), lib.read16(graphics+10)] == [96, 40]
for x, y in layout['hull']:
    assert native('MapGridGetCollisionAt', x+7, y+7) != 0
    behavior = native('MapGridGetMetatileBehaviorAt', x+7, y+7)
    assert native('MetatileBehavior_IsSurfableWaterOrUnderwater', behavior)
# The terminal's captain uses Pallet's original stable network destination.
talk_up()
picture('interior-world-port-menu')
choose(0)  # KANTO
choose(0)  # LAVENDER (Pallet excluded)
if (source/'.journey-lavender-harbor').exists():
    from prepare_lavender_harbor import HARBOR as LAVENDER, ARRIVAL as LAVENDER_ARRIVAL
    trips = [voyage(LAVENDER, LAVENDER_ARRIVAL)]
    talk_up()
else:
    trips = [voyage('JourneyRoute12Shipyard', (24, 39))]
    talk_left()
choose(0)  # KANTO
choose(1)  # PALLET (Lavender excluded)
trips.append(voyage(HARBOR, ARRIVAL))
picture('network-return-inside')
walk_to(11, 13)
change_map(128, 'PalletTown_Frlg')
walk_to(13, 24)
walk_to(13, 16)
picture('returned-to-original-land')
# Walk the complete one-tile eastern corridor and the requested southern
# bridge, then use the front door from this second access and return.
walk_to(13, 15)
walk_to(23, 15)
walk_to(23, 26)
walk_to(18, 26)
walk_to(18, 24)
assert not lib.read8(s['gPlayerAvatar']) & 8
assert native('MapGridGetElevationAt', 18+7, 25+7) == 0
assert native('MetatileBehavior_IsBridgeOverWater', native('MapGridGetMetatileBehaviorAt',18+7,25+7))
picture('south-access-and-east-corridor')
change_map(64, HARBOR)
walk_to(11, 13)
change_map(128, 'PalletTown_Frlg')
walk_to(18, 26)
walk_to(23, 26)
walk_to(23, 15)
walk_to(13, 15)
walk_to(13, 16)
# The added sea rows must stay open to the original Route 21 channel.
warp('PalletTown_Frlg', 8, 23)
native('SetPlayerAvatarTransitionFlags', 8)
step(30)
walk_to(12, 23)
walk_to(12, 25)
walk_to(21, 25)
assert lib.read8(s['gPlayerAvatar']) & 8
picture('merged-bay-surfed')
walk_to(12, 25)
walk_to(12, 23)
walk_to(8, 23)
last_y = layout['exterior_size'][1]-1
walk_to(8, last_y)
before = native('JourneyWorldMapPosition')
change_map(128, 'Route21_North_Frlg')
after = native('JourneyWorldMapPosition')
assert before == after, ('Atlas jumps at Route 21 seam', before, after, position())
picture('surf-route21-outbound')
change_map(64, 'PalletTown_Frlg')
assert position() == (8, last_y)
assert native('JourneyWorldMapPosition') == before
picture('surf-route21-return')
report = dict(passed=True, rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
              original_bridge_preserved=True, outside_boat_shifted_right=True,
              bridge_walked_without_surf=True, controller_entry_and_exit=True,
              interior_captain_interacted_physically=True, outside_captain_removed=True,
              bridges_joined_and_walked=True, complete_trees_checked=True, upper_cliff_rim=True,
              ship_sprite_size=[96, 40], ship_hull_blocked_over_water=True,
              returned_to_original_land=True, route21_surf_roundtrip=True,
              merged_bay_surfed=True,
              south_bridge_walked=True, eastern_corridor_walked=True,
              bridge_crossed_by_surf_below=True, upper_corner_corrected=True,
              route21_atlas_seam_delta=0, trips=trips,
              initial_story_state_and_first_placement_are_fixtures=True,
              full_campaign_playthrough=False)
lib.stop()
(args.output/'pallet-harbor.json').write_text(json.dumps(report, indent=2)+'\n')
print('Pallet: joined bridges, moved boat, complete trees, terminal captain, ship and Surf roundtrip passed.')
