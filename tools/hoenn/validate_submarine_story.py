"""Follow native Maxie -> Stern interview -> theft -> Aqua hideout -> Matt.
Initial badges/prior episodes, intercity travel, battle stats and healing are fixtures.
The scenes, local walking, hideout warps and trainer victories remain native.
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
for t in stories['trainers']:
    if t['mission'] == 'hoenn_rocket': rawflag(0x500 + t['id'], True)
native('VarSet', 0x40B3, 1); rawflag(0x500 + 32, True) # Earlier Shelly episode fixture.
rawflag(hoenn_flags[0], True) # Fifth arbitrary Hoenn badge.
for name in ['FLAG_GROUDON_AWAKENED_MAGMA_HIDEOUT', 'FLAG_HIDE_MAGMA_HIDEOUT_GRUNTS',
             'FLAG_HIDE_MAGMA_HIDEOUT_4F_GROUDON_ASLEEP', 'FLAG_MET_TEAM_AQUA_HARBOR',
             'FLAG_TEAM_AQUA_ESCAPED_IN_SUBMARINE', 'FLAG_HIDE_AQUA_HIDEOUT_GRUNTS',
             'FLAG_HIDE_AQUA_HIDEOUT_1F_GRUNT_1_BLOCKING_ENTRANCE',
             'FLAG_HIDE_AQUA_HIDEOUT_1F_GRUNT_2_BLOCKING_ENTRANCE']:
    rawflag(flag_id(name), False)
rawflag(flag_id('FLAG_HIDE_MAGMA_HIDEOUT_4F_GROUDON'), True)
for trainer in [601, 30, 2, 3, 4, 5, 27, 28, 192, 193]: rawflag(0x500 + trainer, False)
native('VarSet', 0x4058, 0); native('VarSet', 0x40A0, 0)
badges_before = [flag(f) for f in kanto_flags + hoenn_flags]
assert pending(False) == 4
warp('MagmaHideout_4F', 16, 22)
step(4, 64); step(30); press(1)
maxie = fight(dict(id=601, map='MagmaHideout_4F', mission='magma_hideout'))
assert flag(flag_id('FLAG_GROUDON_AWAKENED_MAGMA_HIDEOUT'))
assert native('VarGet', 0x4058) == 1 and native('VarGet', 0x40A0) == 1
assert not flag(flag_id('FLAG_HIDE_SLATEPORT_CITY_CAPTAIN_STERN'))
assert not flag(flag_id('FLAG_HIDE_SLATEPORT_CITY_GABBY_AND_TY'))
assert [flag(f) for f in kanto_flags + hoenn_flags] == badges_before
picture('maxie-victory-starts-stern-interview')
print('Native Maxie victory scheduled Stern interview', flush=True)

def continue_save():
    assert native('TrySavingData', 0, max_frames=6000) == 1
    assert native('LoadGameSave', 0, max_frames=6000) == 1
    lib.write32(s['gMain'] + 4, s['CB2_ContinueSavedGame'] | 1)
    step(1500); finish()
continue_save()
assert native('VarGet', 0x4058) == 1 and native('VarGet', 0x40A0) == 1
warp('SlateportCity', 28, 14) # Intercity travel fixture; the interview is native.
step(4, 64); step(30); press(1)
finish(limit=500)
assert location() == map_id('SlateportCity_Harbor'), (location(), position())
assert native('VarGet', 0x4058) == 2 and native('VarGet', 0x40A0) == 1
assert not flag(flag_id('FLAG_MET_TEAM_AQUA_HARBOR'))
picture('stern-interview-enters-harbor')
# Walk from the original arrival to the native trigger, not a script injection.
for _ in range(180):
    step(1, 64)
    if position()[1] == 13: break
step(30)
for _ in range(180):
    step(1, 32)
    if not idle(): break
step(30); picture('archie-steals-submarine')
finish(limit=500)
assert flag(flag_id('FLAG_MET_TEAM_AQUA_HARBOR'))
assert native('VarGet', 0x40A0) == 2
for i in [1, 2]: assert flag(flag_id(f'FLAG_HIDE_AQUA_HIDEOUT_1F_GRUNT_{i}_BLOCKING_ENTRANCE'))
assert not flag(flag_id('FLAG_TEAM_AQUA_ESCAPED_IN_SUBMARINE'))
assert [flag(f) for f in kanto_flags + hoenn_flags] == badges_before
picture('theft-opens-aqua-hideout')
continue_save()
assert flag(flag_id('FLAG_MET_TEAM_AQUA_HARBOR')) and native('VarGet', 0x40A0) == 2
print('Native Stern interview and submarine theft completed', flush=True)

rawflag(hoenn_flags[2], True) # Sixth arbitrary badge, not awarded by a story scene.
badges_before_matt = [flag(f) for f in kanto_flags + hoenn_flags]
assert pending(False) == 16 and pending(True) == 7
warp('LilycoveCity', 70, 6) # Travel/initial Surf position are fixtures.
native('SetPlayerAvatarTransitionFlags', 8); step(30)
assert lib.read8(s['gPlayerAvatar']) & 8
for _ in range(180):
    step(1, 64)
    if location() == map_id('AquaHideout_1F'): break
step(120)
assert location() == map_id('AquaHideout_1F'), (location(), position())
picture('surf-enters-aqua-hideout')

# Plan on the unchanged native layouts. All transitions below use directional
# input and their original stairs/teleport pads. No position or map writes.
map_names = ['AquaHideout_1F', 'AquaHideout_B1F', 'AquaHideout_B2F']
maps = {n: json.loads((source / f'data/maps/{n}/map.json').read_text()) for n in map_names}
by_id = {m['id']: n for n, m in maps.items()}
by_location = {map_id(n): n for n in maps}
blocks = {}
for n, m in maps.items():
    layout = layouts[m['layout']]
    blocks[n] = (layout['width'], layout['height'], struct.unpack('<' + 'H' * (layout['width'] * layout['height']), (source / layout['blockdata_filepath']).read_bytes()))
warp_tiles = {n: {(w['x'], w['y']): w for w in m['warp_events']} for n, m in maps.items()}
keys = [(1, 0, 16), (-1, 0, 32), (0, 1, 128), (0, -1, 64)]
blocked_edges, transitions, wins = set(), [], [maxie]
walked_tiles = 0

def live_objects():
    result = set()
    player_id = lib.read8(s['gPlayerAvatar'] + 5)
    for i in range(16):
        o = s['gObjectEvents'] + 36 * i
        if i != player_id and lib.read8(o) & 1:
            result.add((lib.read16(o + 16) - 7, lib.read16(o + 18) - 7))
    return result

def next_step(goal):
    start = (by_location[location()], *position())
    queue, visited = deque([start]), {start: None}
    occupied = live_objects()
    while queue:
        n, x, y = current = queue.popleft()
        if current == goal:
            while visited[current] and visited[current][0] != start:
                current = visited[current][0]
            return visited[current][1] if visited[current] else None
        width, height, tiles = blocks[n]
        for dx, dy, key in keys:
            xx, yy = x + dx, y + dy
            if not (0 <= xx < width and 0 <= yy < height): continue
            if tiles[yy * width + xx] & 0xC00: continue
            if n == start[0] and (xx, yy) in occupied: continue
            if (n, x, y, key) in blocked_edges: continue
            nxt = (n, xx, yy)
            event = warp_tiles[n].get((xx, yy))
            if event:
                if event['dest_map'] not in by_id: continue
                dest = by_id[event['dest_map']]
                endpoint = maps[dest]['warp_events'][int(event['dest_warp_id'])]
                nxt = (dest, endpoint['x'], endpoint['y'])
            if nxt not in visited:
                visited[nxt] = (current, key); queue.append(nxt)
    picture('hideout-path-failure')
    raise AssertionError(('No native hideout route', start, goal, sorted(blocked_edges), list(bytes(lib.read8(s['gPlayerAvatar'] + i) for i in range(20)))))

def handle_field():
    cb = lib.read32(s['gMain'] + 4) & ~1
    if cb == s['BattleMainCB2']:
        trainer = lib.read16(s['gTrainerBattleParameter'] + abi[13])
        assert trainer in [2, 3, 4, 5, 27, 28, 192, 193], trainer
        wins.append(fight(dict(id=trainer, map=by_location[location()], mission='aqua_hideout_route')))
        native('HealPlayerParty') # Fixture: restore PP for the extended round trip.
        print('Native route trainer defeated:', trainer, flush=True)
        return True
    if not idle():
        # A trainer approach or Matt's exclamation may still be running.
        press(1); return True
    return False

surf_prompts = []

def traverse(goal):
    global walked_tiles
    last_stable = (by_location[location()], *position())
    for turn in range(1200):
        if handle_field(): continue
        name = by_location[location()]
        current = (name, *position())
        if current != last_stable:
            walked_tiles += 1
            if current[0] != last_stable[0] or abs(current[1] - last_stable[1]) + abs(current[2] - last_stable[2]) > 1:
                transitions.append(dict(source=list(last_stable), destination=list(current)))
                picture('hideout-transition-' + str(len(transitions)))
            last_stable = current
        if (name, *position()) == goal: break
        key = next_step(goal)
        old = (name, *position())
        for _ in range(80):
            step(1, key)
            if location() != map_id(name) or position() != old[1:] or not idle(): break
        step(30)
        if handle_field(): continue
        step(12)
        new = (by_location[location()], *position())
        if old == new:
            dx, dy = next((dx, dy) for dx, dy, k in keys if k == key)
            behavior = native('MapGridGetMetatileBehaviorAt', old[1] + dx + 7, old[2] + dy + 7)
            if not lib.read8(s['gPlayerAvatar']) & 8 and native('MetatileBehavior_IsSurfableWaterOrUnderwater', behavior):
                press(1); finish(limit=500)
                assert lib.read8(s['gPlayerAvatar']) & 8, ('Surf prompt did not start Surf', old)
                surf_prompts.append(list(old))
                picture('native-surf-prompt-return')
            else:
                blocked_edges.add((*old, key))

    else: raise AssertionError(('Hideout traversal incomplete', goal, location(), position()))

traverse(('AquaHideout_B2F', 24, 19))
assert walked_tiles > 20 and transitions
outbound_walked_tiles = walked_tiles
outbound_transitions = list(transitions)
picture('native-hideout-path-reaches-matt')
step(4, 32); step(30); press(1)
wins.append(fight(dict(id=30, map='AquaHideout_B2F', mission='aqua_hideout')))
native('HealPlayerParty') # Battle duration/resource balance is outside this test.
assert flag(flag_id('FLAG_TEAM_AQUA_ESCAPED_IN_SUBMARINE'))
assert pending(False) == 0 and pending(True) == 7
assert [flag(f) for f in kanto_flags + hoenn_flags] == badges_before_matt
picture('matt-defeated-after-full-native-route')
continue_save()
assert flag(0x500 + 601) and flag(0x500 + 30)
assert flag(flag_id('FLAG_MET_TEAM_AQUA_HARBOR'))
assert native('VarGet', 0x4058) == 2 and native('VarGet', 0x40A0) == 2
assert flag(flag_id('FLAG_TEAM_AQUA_ESCAPED_IN_SUBMARINE'))
assert pending(False) == 0 and pending(True) == 7
# Return physically, including the ordinary A/Yes Surf prompt at the shore.
blocked_edges.clear()
traverse(('AquaHideout_1F', 13, 26))
assert surf_prompts and lib.read8(s['gPlayerAvatar']) & 8
for _ in range(200):
    step(1, 128)
    if location() == map_id('LilycoveCity'): break
step(150); finish()
assert location() == map_id('LilycoveCity'), (location(), position())
assert lib.read8(s['gPlayerAvatar']) & 8
assert [flag(f) for f in kanto_flags + hoenn_flags] == badges_before_matt
assert pending(False) == 0 and pending(True) == 7
picture('native-return-to-lilycove-after-matt')
continue_save()
assert location() == map_id('LilycoveCity') and lib.read8(s['gPlayerAvatar']) & 8
assert flag(flag_id('FLAG_TEAM_AQUA_ESCAPED_IN_SUBMARINE'))
assert pending(False) == 0 and pending(True) == 7
assert [flag(f) for f in kanto_flags + hoenn_flags] == badges_before_matt
picture('native-lilycove-return-after-continue')
lib.stop()
result = dict(passed=True, rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
              wins=wins, native_maxie_victory_schedules_interview=True,
              native_stern_interview_enters_harbor=True, native_theft_opens_hideout=True,
              native_surf_entrance=True, hideout_walked_steps=outbound_walked_tiles,
              original_hideout_transitions=outbound_transitions,
              return_walked_steps=walked_tiles - outbound_walked_tiles,
              original_return_transitions=transitions[len(outbound_transitions):],
              native_surf_prompts_on_return=surf_prompts,
              native_return_to_lilycove=True, native_continue_in_surf_after_return=True, no_hideout_position_or_event_entry_injections=True,
              native_matt_victory_and_submarine_departure=True,
              native_save_continue_after_maxie_theft_and_matt=True,
              regional_badges_and_kanto_missions_unchanged=True,
              prior_episodes_badges_intercity_travel_initial_surf_and_battle_stats_are_fixtures=True,
              healing_between_battles_is_fixture=True,
              full_campaign_playthrough=False, balance_validated=False)
(args.output / 'submarine-story.json').write_text(json.dumps(result, indent=2) + '\n')
print('Native Maxie/Stern/theft/hideout/Matt sequence passed', flush=True)
