"""Shared native input walker. Loaded in a validator context with names/allowed.
Plans map tiles; movement, collisions, Surf prompts and warps run in mGBA.
"""
from collections import deque
import json
import struct

walk_prefix = globals().get('walk_prefix', 'seafloor')
maps = {n: json.loads((source / f'data/maps/{n}/map.json').read_text()) for n in names}
by_id = {m['id']: n for n, m in maps.items()}
by_location = {map_id(n): n for n in maps}
blocks = {}
passable = {}
water_behaviors = {}
behaviors, currents, arrows = {}, {}, {}
step_warps = {}
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
        if any(w['x'] == i % blocks[n][0] and w['y'] == i // blocks[n][0]
               for w in m['warp_events']) and behavior not in step_warps:
            step_warps[behavior] = any(native('MetatileBehavior_Is' + kind, behavior) for kind in [
                'WarpDoor', 'Ladder', 'Escalator', 'NonAnimDoor', 'LavaridgeB1FWarp',
                'Lavaridge1FWarp', 'AquaHideoutWarp', 'MtPyreHole', 'MossdeepGymWarp', 'UnionRoomWarp'])
        if behavior not in currents:
            currents[behavior] = next(((dx, dy) for direction, dx, dy in [('East', 1, 0), ('West', -1, 0), ('North', 0, -1), ('South', 0, 1)]
                                      if native('MetatileBehavior_Is' + direction + 'wardCurrent', behavior)), None)
            arrows[behavior] = next((key for direction, key in [('East', 16), ('West', 32), ('North', 64), ('South', 128)]
                                     if native('MetatileBehavior_Is' + direction + 'ArrowWarp', behavior)), None)
        if not tile & 0xC00: valid.add(i); continue
        if tile & 0xC00 != 0x400: continue
        if any(w['x'] == i % blocks[n][0] and w['y'] == i // blocks[n][0]
               and w['dest_map'] in by_id for w in m['warp_events']) and native('MetatileBehavior_IsWarpDoor', behavior):
            valid.add(i); continue
        if behavior not in water_behaviors:
            water_behaviors[behavior] = bool(native('MetatileBehavior_IsSurfableWaterOrUnderwater', behavior))
        if water_behaviors[behavior]: valid.add(i)
    passable[n] = valid
warps = {n: {(w['x'], w['y']): w for w in m['warp_events']} for n, m in maps.items()}
keys = [(1, 0, 16), (-1, 0, 32), (0, 1, 128), (0, -1, 64)]
blocked, transitions, wins, surf_prompts = set(), [], [], []
walked = 0

def refresh_loaded_warp_tiles():
    """Observe entrances changed by native OnLoad scripts, not raw map.bin."""
    n = by_location[location()]
    width = blocks[n][0]
    for x, y in warps[n]:
        index = y * width + x
        behavior = native('MapGridGetMetatileBehaviorAt', x + 7, y + 7)
        collision = native('MapGridGetCollisionAt', x + 7, y + 7)
        behaviors[n][index] = behavior
        currents[behavior] = next(((dx, dy) for direction, dx, dy in [
            ('East', 1, 0), ('West', -1, 0), ('North', 0, -1), ('South', 0, 1)]
            if native('MetatileBehavior_Is' + direction + 'wardCurrent', behavior)), None)
        arrows[behavior] = next((key for direction, key in [
            ('East', 16), ('West', 32), ('North', 64), ('South', 128)]
            if native('MetatileBehavior_Is' + direction + 'ArrowWarp', behavior)), None)
        step_warps[behavior] = any(native('MetatileBehavior_Is' + kind, behavior) for kind in [
            'WarpDoor', 'Ladder', 'Escalator', 'NonAnimDoor', 'LavaridgeB1FWarp',
            'Lavaridge1FWarp', 'AquaHideoutWarp', 'MtPyreHole', 'MossdeepGymWarp', 'UnionRoomWarp'])
        if collision == 0 or (collision == 1 and native('MetatileBehavior_IsWarpDoor', behavior)):
            passable[n].add(index)
        else:
            passable[n].discard(index)

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
            if event and arrows[behaviors[n][yy * width + xx]] is None and step_warps.get(behaviors[n][yy * width + xx], False):
                if event['dest_map'] not in by_id: continue
                dest = by_id[event['dest_map']]
                endpoint = maps[dest]['warp_events'][int(event['dest_warp_id'])]
                nxt = (dest, endpoint['x'], endpoint['y'])
            if nxt not in visited:
                visited[nxt] = (current, key); queue.append(nxt)
    picture(walk_prefix + '-path-failure')
    raise AssertionError(('No native route', start, goal, sorted(blocked)))

def field():
    if lib.read32(s['gMain'] + 4) & ~1 == s['BattleMainCB2']:
        trainer = lib.read16(s['gTrainerBattleParameter'] + abi[13])
        assert trainer in allowed, trainer
        wins.append(fight(dict(id=trainer, map=by_location[location()], mission='seafloor_route', fixture_clear_status=True)))
        native('HealPlayerParty') # Fixture; difficulty/PP balance is not tested.
        print('Native route trainer defeated:', trainer, flush=True)
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
                picture(walk_prefix + '-transition-' + str(len(transitions)))
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
    picture(walk_prefix + '-walk-failure')
    raise AssertionError(('Walk incomplete', goal, location(), position()))
