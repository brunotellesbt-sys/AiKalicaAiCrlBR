"""Walk the Seafloor Cavern from a real Dive prompt with zero badges.
Initial story/badge state, ocean position, party/stats and healing are fixtures.
No internal warps or trainer/script entry; victories and boss checks are native.
"""
from collections import deque
from pathlib import Path
import hashlib
import json
import struct

ROOT = Path(__file__).resolve().parents[2]
exec(compile((ROOT / 'tools/hoenn/validate_team_missions.py').read_text().split('\nwins, completed =')[0],
             str(ROOT / 'tools/hoenn/validate_team_missions.py'), 'exec'))
assert (source / '.journey-aqua-episodes').exists()
for f in kanto_flags + hoenn_flags: rawflag(f, False)
native('ScriptSetMonMoveSlot', 0, 291, 2) # Dive; the party also knows Surf.
for name in ['FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN', 'FLAG_SYS_WEATHER_CTRL']:
    rawflag(abi[111] if name == 'FLAG_SYS_WEATHER_CTRL' else flag_id(name), False)
native('VarSet', 0x409F, 0)
opponents = (source / 'include/constants/opponents.h').read_text()
allowed = {int(value) for name, value in re.findall(r'^#define\s+(TRAINER_\w+)\s+(\d+)\s*$', opponents, re.M)
           if 'SEAFLOOR_CAVERN' in name}
assert {6, 7, 8, 14, 33, 567} <= allowed
for trainer in allowed: rawflag(0x500 + trainer, False)
assert flag(flag_id('FLAG_HIDE_JOURNEY_LAND_OBSTACLES'))
assert native('JourneyCanStartArchieAlliance') == 0
assert native('JourneyGymBadgeCount', 0) == native('JourneyGymBadgeCount', 1) == 0

ocean = json.loads((source / 'data/maps/Route128/map.json').read_text())
layout = layouts[ocean['layout']]
tiles = struct.unpack('<' + 'H' * (layout['width'] * layout['height']), (source / layout['blockdata_filepath']).read_bytes())
warp('Route128', 38, 28) # Only the initial ocean travel is a fixture.
candidates = sorted(((x, y) for y in range(layout['height']) for x in range(layout['width'])
                     if not tiles[y * layout['width'] + x] & 0xC00 and tiles[y * layout['width'] + x] >> 12 == 1),
                    key=lambda p: abs(p[0] - 38) + abs(p[1] - 26))
dive_point = next(p for p in candidates if native('MetatileBehavior_IsDiveable', native('MapGridGetMetatileBehaviorAt', p[0] + 7, p[1] + 7)))
warp('Route128', *dive_point)
native('SetPlayerAvatarTransitionFlags', 8); step(30)
assert native('TrySetDiveWarp') == 2
for _ in range(160):
    press(1)
    if location() == map_id('Underwater_Route128'): break
step(120); finish()
assert location() == map_id('Underwater_Route128'), ('Dive failed', location())
picture('zero-badge-dive-route128')
print('Native zero-badge Dive entered Underwater Route128', flush=True)

names = ['Underwater_Route128', 'Underwater_SeafloorCavern', 'SeafloorCavern_Entrance'] + [f'SeafloorCavern_Room{i}' for i in range(1, 10)]
maps = {n: json.loads((source / f'data/maps/{n}/map.json').read_text()) for n in names}
by_id = {m['id']: n for n, m in maps.items()}
by_location = {map_id(n): n for n in maps}
blocks = {}
passable = {}
water_behaviors = {}
behaviors, currents, arrows = {}, {}, {}
for n, m in maps.items():
    layout = layouts[m['layout']]
    blocks[n] = (layout['width'], layout['height'], struct.unpack('<' + 'H' * (layout['width'] * layout['height']), (source / layout['blockdata_filepath']).read_bytes()))
    assert layout['layout_version'] == 'emerald'
    primary = s[layout['primary_tileset'].replace('gTileset_', 'gMetatileAttributes_')]
    secondary = s[layout['secondary_tileset'].replace('gTileset_', 'gMetatileAttributes_')]
    valid = set()
    behaviors[n] = []
    for i, tile in enumerate(blocks[n][2]):
        tid = tile & 1023
        behavior = lib.read16((primary if tid < 512 else secondary) + 2 * (tid if tid < 512 else tid - 512)) & 255
        behaviors[n].append(behavior)
        if behavior not in currents:
            currents[behavior] = next(((dx, dy) for direction, dx, dy in [('East', 1, 0), ('West', -1, 0), ('North', 0, -1), ('South', 0, 1)]
                                      if native('MetatileBehavior_Is' + direction + 'wardCurrent', behavior)), None)
            arrows[behavior] = next((key for direction, key in [('East', 16), ('West', 32), ('North', 64), ('South', 128)]
                                     if native('MetatileBehavior_Is' + direction + 'ArrowWarp', behavior)), None)
        if not tile & 0xC00: valid.add(i); continue
        if tile & 0xC00 != 0x400: continue
        if behavior not in water_behaviors:
            water_behaviors[behavior] = bool(native('MetatileBehavior_IsSurfableWaterOrUnderwater', behavior))
        if water_behaviors[behavior]: valid.add(i)
    passable[n] = valid
warps = {n: {(w['x'], w['y']): w for w in m['warp_events']} for n, m in maps.items()}
keys = [(1, 0, 16), (-1, 0, 32), (0, 1, 128), (0, -1, 64)]
blocked, transitions, wins, surf_prompts = set(), [], [], []
walked = 0

def occupied():
    result = set()
    player = lib.read8(s['gPlayerAvatar'] + 5)
    for i in range(16):
        o = s['gObjectEvents'] + 36 * i
        if i != player and lib.read8(o) & 1:
            result.add((lib.read16(o + 16) - 7, lib.read16(o + 18) - 7))
    return result

def next_key(goal):
    start = (by_location[location()], *position())
    queue, visited, objects = deque([start]), {start: None}, occupied()
    while queue:
        n, x, y = current = queue.popleft()
        if current == goal:
            while visited[current] and visited[current][0] != start: current = visited[current][0]
            return visited[current][1] if visited[current] else None
        width, height, tiles = blocks[n]
        standing_warp = warps[n].get((x, y))
        arrow_key = arrows[behaviors[n][y * width + x]]
        if standing_warp and arrow_key and standing_warp['dest_map'] in by_id:
            dest = by_id[standing_warp['dest_map']]
            endpoint = maps[dest]['warp_events'][int(standing_warp['dest_warp_id'])]
            nxt = (dest, endpoint['x'], endpoint['y'])
            if nxt not in visited:
                visited[nxt] = (current, arrow_key); queue.append(nxt)
        for dx, dy, key in keys:
            xx, yy = x + dx, y + dy
            if not (0 <= xx < width and 0 <= yy < height): continue
            if yy * width + xx not in passable[n]: continue
            if n == start[0] and (xx, yy) in objects: continue
            if (*current, key) in blocked: continue
            # A current forces movement through its arrows. Plan its landing
            # tile rather than treating each arrow as a place to change course.
            flow_seen = set()
            while (xx, yy) not in flow_seen:
                flow_seen.add((xx, yy))
                direction = currents[behaviors[n][yy * width + xx]]
                if direction is None: break
                fx, fy = xx + direction[0], yy + direction[1]
                if not (0 <= fx < width and 0 <= fy < height) or fy * width + fx not in passable[n]: break
                xx, yy = fx, fy
            else: continue # Avoid a closed current loop.
            nxt = (n, xx, yy)
            event = warps[n].get((xx, yy))
            if event and arrows[behaviors[n][yy * width + xx]] is None:
                if event['dest_map'] not in by_id: continue
                dest = by_id[event['dest_map']]
                endpoint = maps[dest]['warp_events'][int(event['dest_warp_id'])]
                nxt = (dest, endpoint['x'], endpoint['y'])
            if nxt not in visited:
                visited[nxt] = (current, key); queue.append(nxt)
    picture('seafloor-path-failure')
    raise AssertionError(('No native route', start, goal, sorted(blocked)))

def field():
    if lib.read32(s['gMain'] + 4) & ~1 == s['BattleMainCB2']:
        trainer = lib.read16(s['gTrainerBattleParameter'] + abi[13])
        assert trainer in allowed, trainer
        wins.append(fight(dict(id=trainer, map=by_location[location()], mission='seafloor_route', fixture_clear_status=True)))
        native('HealPlayerParty') # Fixture; difficulty/PP balance is not tested.
        print('Native seafloor trainer defeated:', trainer, flush=True)
        return True
    if not idle(): press(1); return True
    return False

def walk(goal):
    global walked
    blocked.clear()
    last = (by_location[location()], *position())
    for tick in range(600):
        if field(): continue
        now = (by_location[location()], *position())
        if now != last:
            walked += 1
            if now[0] != last[0]:
                transitions.append(dict(source=list(last), destination=list(now)))
                picture('seafloor-transition-' + str(len(transitions)))
            last = now
        if now == goal: return
        if tick % 100 == 0: print('Native route progress:', tick, now, flush=True)
        key = next_key(goal)
        arrow = arrows[behaviors[now[0]][now[2] * blocks[now[0]][0] + now[1]]]
        if arrow == key and (now[1], now[2]) in warps[now[0]]:
            facing = {128: 1, 64: 2, 32: 3, 16: 4}[arrow]
            if native('GetPlayerFacingDirection') != facing:
                # Approach the arrow from behind, so the directional exit
                # sees the correct facing before the player leaves its tile.
                key = {16: 32, 32: 16, 64: 128, 128: 64}[arrow]
        for _ in range(80):
            step(1, key)
            if (by_location[location()], *position()) != now or not idle(): break
        step(30)
        if field(): continue
        step(12)
        for _ in range(500):
            current_name = by_location[location()]
            x, y = position()
            width = blocks[current_name][0]
            if currents[behaviors[current_name][y * width + x]] is None: break
            step(4)
        if (by_location[location()], *position()) == now:
            dx, dy = next((dx, dy) for dx, dy, k in keys if k == key)
            behavior = native('MapGridGetMetatileBehaviorAt', now[1] + dx + 7, now[2] + dy + 7)
            if (not lib.read8(s['gPlayerAvatar']) & 8
                and native('MetatileBehavior_IsSurfableWaterOrUnderwater', behavior)
                and native('IsPlayerFacingSurfableFishableWater')):
                press(1); finish(limit=500)
                assert lib.read8(s['gPlayerAvatar']) & 8
                surf_prompts.append(list(now))
            else: blocked.add((*now, key))
    picture('seafloor-walk-failure')
    raise AssertionError(('Walk incomplete', goal, location(), position()))

walk(('Underwater_SeafloorCavern', 6, 6))
assert native('TrySetDiveWarp') == 1
press(2)
for _ in range(160):
    press(1)
    if location() == map_id('SeafloorCavern_Entrance'): break
step(120); finish()
assert location() == map_id('SeafloorCavern_Entrance')
picture('native-emerge-seafloor-entrance')
print('Native resurface entered Seafloor Cavern', flush=True)
if not (source / '.journey-seafloor-access').exists():
    walk(('SeafloorCavern_Entrance', 10, 3))
    step(100, 64); step(30)
    assert location() == map_id('SeafloorCavern_Entrance') and position() == (10, 3)
    press(1); picture('native-entrance-guard-blocks-passage'); finish()
    step(100, 64); step(30)
    assert location() == map_id('SeafloorCavern_Entrance') and position() == (10, 3)
    assert not flag(flag_id('FLAG_HIDE_SEAFLOOR_CAVERN_ENTRANCE_AQUA_GRUNT'))
    lib.stop()
    (args.output / 'seafloor-baseline.json').write_text(json.dumps(dict(
        passed=True, rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
        native_zero_badge_dive=True, native_resurface_into_cavern=True,
        native_entrance_guard_blocks_passage=True, position=[10, 3],
        guard_visibility_not_faked=True, full_campaign_playthrough=False), indent=2) + '\n')
    print('Native baseline guard blocks the only entrance', flush=True)
    raise SystemExit(0)
walk(('SeafloorCavern_Entrance', 10, 3))
step(4, 16); step(30); press(1)
picture('native-relocated-grunt-dialogue'); finish()
assert native('VarGet', 0x40D9) == 1
assert not flag(flag_id('FLAG_HIDE_SEAFLOOR_CAVERN_ENTRANCE_AQUA_GRUNT'))
walk(('SeafloorCavern_Room9', 16, 42))
picture('native-seafloor-route-before-archie')
assert not native('JourneyCanStartArchieAlliance')
# Step onto the real boss trigger. Permission must reject at zero badges.
for _ in range(80):
    step(1, 16)
    if not idle(): break
step(30); picture('native-archie-trigger-refuses-zero-badges'); finish()
assert position() == (17, 42), position()
assert lib.read16(s['gSpecialVar_Result']) == 0
assert not flag(flag_id('FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN'))
assert not native('JourneyCanStartArchieAlliance')
assert native('JourneyGymBadgeCount', 0) == native('JourneyGymBadgeCount', 1) == 0
assert native('TrySavingData', 0, max_frames=6000) == 1
assert native('LoadGameSave', 0, max_frames=6000) == 1
lib.write32(s['gMain'] + 4, s['CB2_ContinueSavedGame'] | 1)
step(1500); finish()
assert location() == map_id('SeafloorCavern_Room9')
assert not flag(flag_id('FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN'))
assert native('JourneyGymBadgeCount', 0) == native('JourneyGymBadgeCount', 1) == 0
if not (source / '.journey-water-continue').exists():
    # Retain the previous layer's outbound-only reproduction. Its underwater
    # Continue regression is reproduced separately by validate_water_continue.
    lib.stop()
    result = dict(passed=True, rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
                  dive_point=list(dive_point), native_zero_badge_dive=True, native_resurface_into_cavern=True,
                  walked_steps=walked, original_map_transitions=transitions, wins=wins, surf_prompts=surf_prompts,
                  reaches_archie_without_strength_rock_smash_flash_or_acro=True,
                  relocated_grunt_visible_and_native_dialogue_retained=True,
                  native_boss_trigger_refuses_missing_missions=True, native_save_continue_preserves_zero_badges=True,
                  no_internal_position_warps_or_event_entries=True, starting_ocean_party_stats_healing_are_fixtures=True,
                  in_battle_status_recovery_is_fixture=True,
                  wild_encounters_disabled=True, full_campaign_playthrough=False, balance_validated=False)
    (args.output / 'seafloor-route.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Native outbound Seafloor Cavern route passed', flush=True)
    raise SystemExit(0)
outbound_walked = walked
outbound_transitions = list(transitions)
outbound_surf_prompts = list(surf_prompts)

def water_state():
    return dict(map=next(n for n in ['Route128'] + names if location() == map_id(n)),
                position=list(position()), avatar_mode=lib.read8(s['gPlayerAvatar']) & 25,
                kanto_badges=native('JourneyGymBadgeCount', 1),
                hoenn_badges=native('JourneyGymBadgeCount', 0),
                kyogre_escaped=flag(flag_id('FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN')),
                archie_permission=bool(native('JourneyCanStartArchieAlliance')))

continues = []
def continue_water():
    before = water_state()
    assert native('TrySavingData', 0, max_frames=6000) == 1
    assert native('LoadGameSave', 0, max_frames=6000) == 1
    lib.write32(s['gMain'] + 4, s['CB2_ContinueSavedGame'] | 1)
    step(1500); finish()
    after = water_state()
    assert before == after, (before, after)
    continues.append(dict(before=before, after=after))

# Retrace native passages and currents, without internal map/position writes.
walk(('SeafloorCavern_Entrance', 10, 17))
assert native('TrySetDiveWarp') == 2
for _ in range(160):
    press(1)
    if location() == map_id('Underwater_SeafloorCavern'): break
step(120); finish()
assert location() == map_id('Underwater_SeafloorCavern')
picture('native-return-dive-underwater-cavern')
continue_water()
picture('native-underwater-return-after-continue')
walk(('Underwater_Route128', *dive_point))
assert native('TrySetDiveWarp') == 1
continue_water()
press(2)
for _ in range(160):
    press(1)
    if location() == map_id('Route128'): break
step(120); finish()
assert location() == map_id('Route128') and lib.read8(s['gPlayerAvatar']) & 8
picture('native-return-surface-route128')
continue_water()
picture('native-route128-return-after-continue')
lib.stop()
result = dict(passed=True, rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
              dive_point=list(dive_point), native_zero_badge_dive=True, native_resurface_into_cavern=True,
              walked_steps=outbound_walked, original_map_transitions=outbound_transitions, wins=wins, surf_prompts=outbound_surf_prompts,
              return_walked_steps=walked - outbound_walked, return_map_transitions=transitions[len(outbound_transitions):],
              return_surf_prompts=surf_prompts[len(outbound_surf_prompts):],
              native_dive_out_and_return_to_route128=True, water_save_continues=continues,
              in_battle_status_recovery_is_fixture=True,
              reaches_archie_without_strength_rock_smash_flash_or_acro=True,
              relocated_grunt_visible_and_native_dialogue_retained=True,
              native_boss_trigger_refuses_missing_missions=True, native_save_continue_preserves_zero_badges=True,
              no_internal_position_warps_or_event_entries=True, starting_ocean_party_stats_healing_are_fixtures=True,
              wild_encounters_disabled=True, full_campaign_playthrough=False, balance_validated=False)
(args.output / 'seafloor-route.json').write_text(json.dumps(result, indent=2) + '\n')
print('Native Seafloor Cavern route passed', flush=True)
