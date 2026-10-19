"""Walk all seven extended Sevii decks and exclude Surf from their low piers."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
bootstrap = (ROOT / 'tools/hoenn/validate_trainer_levels.py').read_text().split('\nchecks=[]')[0]
exec(compile(bootstrap, __file__, 'exec'))
initial_sha = hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest()
piers = json.loads((source / '.journey-dewford-coast-safety').read_text())['piers']
ports = json.loads((source / '.journey-sevii-harbors').read_text())['ports']
all_maps = {p.parent.name: json.loads(p.read_text()) for p in (source / 'data/maps').glob('*/map.json')}
all_by_id = {m['id']: n for n, m in all_maps.items()}
names = list(dict.fromkeys([r['town'] for r in piers['town_bridges']]
             + [r['map'] for r in piers['low_piers']]
             + [s['map'] for r in piers['town_bridges'] for s in r['deck_segments']]
             + [p['interior'] for p in ports]
             + [all_by_id[c['map']] for r in piers['low_piers'] for c in r['surface_connections']]))
allowed = set()
walk_prefix = 'coastal-pier-safety'
walk_transition_pictures = False
walk_cache_paths = True
walk_max_ticks = 1200
walk_surf_under_bridges = True
native('RtcInitLocalTimeOffset', 12, 0)
native('VarSet', 0x40FE, 7)
native('VarSet', 0x40FF, 4095)
team([40, 40, 40])
native('ScriptSetMonMoveSlot', 0, 57, 1)
for f in hoenn_flags + kanto_flags:
    rawflag(f, True)
constants = (source / 'include/constants/vars.h').read_text()
for varname, value in [('VAR_MAP_SCENE_ONE_ISLAND_HARBOR', 3), ('VAR_MAP_SCENE_FOUR_ISLAND', 1)]:
    native('VarSet', int(re.search(r'^#define\s+' + varname + r'\s+(0x\w+)', constants, re.M)[1], 16), value)
exec(compile((ROOT / 'tools/hoenn/native_water_walk.py').read_text(), 'pier-native-walker', 'exec'))
full_passable = {n: v.copy() for n, v in passable.items()}
low_cells = {(r['map'], x, y) for r in piers['collision_rectangles']
             for y in range(r['bounds'][1], r['bounds'][3] + 1)
             for x in range(r['bounds'][0], r['bounds'][2] + 1)}
dry = {n: {i for i in valid if not water_behaviors[behaviors[n][i]] or
           (n, i % blocks[n][0], i // blocks[n][0]) in low_cells}
       for n, valid in full_passable.items()}
wet = {n: {i for i in valid if water_behaviors[behaviors[n][i]]
           and not blocks[n][2][i] & 0xC00
           and (n, i % blocks[n][0], i // blocks[n][0]) not in low_cells}
       for n, valid in full_passable.items()}


def state():
    obj = s['gObjectEvents'] + lib.read8(s['gPlayerAvatar'] + 5) * 36
    sprite = s['gSprites'] + lib.read8(obj + 35) * 68
    return dict(map=by_location[location()], position=list(position()),
                surfing=bool(lib.read8(s['gPlayerAvatar']) & 8),
                elevation=native('PlayerGetElevation'),
                priority=(lib.read16(sprite + 4) >> 10) & 3,
                sprite_visible=not bool(lib.read16(sprite + 0x3E) & 4))


def assert_foot():
    value = state()
    assert not value['surfing'] and value['elevation'] == 3 and value['priority'] == 1, value
    assert value['sprite_visible'], value
    return value


def assert_surf():
    value = state()
    assert value['surfing'] and value['elevation'] == 1 and value['priority'] == 2, value
    return value


visited = []


def walk_observer(before, after):
    visited.append(after)


town_checks = []
for row in piers['town_bridges']:
    passable = {n: v.copy() for n, v in dry.items()}
    start = tuple(row['start'])
    # Two starts at its Center as well as traversing the entire new gangway.
    if row['island'] == 'Two':
        start = (row['town'], 21, 8)
    warp(*start)
    native('SetPlayerAvatarTransitionFlags', 1)
    step(90)
    assert_foot()
    first = len(visited)
    walked_rows = []
    for segment in row['deck_segments']:
        n = segment['map']
        x, y, width, height = segment['footprint']
        for yy in range(y, y + height):
            goal = (n, x + 1, yy)
            walk(goal)
            step(15)
            assert_foot()
            walked_rows.append(list(goal))
    end_map, ex, ey = row['end']
    picture(row['island'].lower() + '-extended-town-deck')
    # Keep the same trip: the native south-arrow warp reaches the real main
    # terminal, then the north-arrow returns to the new endpoint.
    walk((row['harbor'], 13, 6))
    step(60)
    assert_foot()
    picture(row['island'].lower() + '-town-deck-main-terminal')
    walk((end_map, ex, ey - 1))
    step(60)
    assert_foot()
    walk(start)
    step(60)
    assert_foot()
    assert (by_location[location()], *position()) == start
    # Probe the side of a new middle row, outside any warp or endpoint.
    segment = row['deck_segments'][-1]
    n = segment['map']
    x, y, width, height = segment['footprint']
    side = (n, x, y + min(1, height - 2))
    walk(side)
    step(60)
    before = (location(), position())
    assert native('MetatileBehavior_IsSurfableWaterOrUnderwater',
                  native('MapGridGetMetatileBehaviorAt', side[1] - 1 + 7, side[2] + 7))
    step(90, 32)
    step(60)
    assert (location(), position()) == before, (row['island'], before, state())
    assert_foot()
    picture(row['island'].lower() + '-extended-deck-foot-blocks-water')
    town_checks.append(dict(island=row['island'], town=row['town'], harbor=row['harbor'],
                            start=list(start), endpoint=row['end'], walked_rows=walked_rows,
                            controller_terminal_return=True, all_deck_rows_walked=True,
                            foot_elevation_3=True, foot_above_boards=True,
                            foot_blocks_water=True, one_beach_seam_crossed=row['island'] == 'One',
                            no_midtrip_coordinate_or_elevation_writes=True))
    print('Native extended Sevii town deck passed:', row['island'], flush=True)

low_checks = []
for row in piers['low_piers']:
    n = row['map']
    w, h, tiles = blocks[n]
    passable = {name: v.copy() for name, v in wet.items()}
    # Test a multi-level plank directly from neighboring open water. This is
    # the exact entry that previously hid the surfer's head under the dock.
    candidates = []
    for x, y in row['blocked_cells']:
        if tiles[y * w + x] >> 12 != 15:
            continue
        for dx, dy, key in keys:
            sx, sy = x - dx, y - dy
            if 0 <= sx < w and 0 <= sy < h and sy * w + sx in wet[n]:
                candidates.append((sx, sy, key, x, y))
    assert candidates, n
    probes = []
    for sx, sy, key, tx, ty in candidates[:1]:
        warp(n, sx, sy)
        native('SetPlayerAvatarTransitionFlags', 8)
        step(90)
        assert_surf()
        before = (location(), position())
        step(90, key)
        step(60)
        assert (location(), position()) == before, (n, before, state())
        assert_surf()
        picture(row['island'].lower() + '-low-pier-surf-blocked')
        probes.append(dict(source=[n, sx, sy], target=[n, tx, ty], blocked=True))
    # Open west water is a navigable bypass in both directions. No low deck,
    # boat or hull is used as a shortcut in this route planner.
    start = (n, 1, 1)
    end = (n, 1, h - 2)
    assert start[2] * w + start[1] in wet[n] and end[2] * w + end[1] in wet[n]
    warp(*start)
    native('SetPlayerAvatarTransitionFlags', 8)
    step(90)
    walk(end)
    assert_surf()
    walk(start)
    assert_surf()
    picture(row['island'].lower() + '-open-sea-bypass')
    seam_checks = []
    for connection in row['surface_connections']:
        dest = all_by_id[connection['map']]
        dw, dh, _ = blocks[dest]
        direction, offset = connection['direction'], connection['offset']
        options = []
        if direction in ('left', 'right'):
            for y in range(h):
                yy = y - offset
                sx = 1 if direction == 'left' else w - 2
                tx = dw - 2 if direction == 'left' else 1
                edge = 0 if direction == 'left' else w - 1
                incoming = dw - 1 if direction == 'left' else 0
                if (0 <= yy < dh and y*w+sx in wet[n] and y*w+edge in wet[n]
                    and yy*dw+incoming in wet[dest] and yy*dw+tx in wet[dest]):
                    options.append(((n, sx, y), (dest, tx, yy)))
        else:
            for x in range(w):
                xx = x - offset
                sy = 1 if direction == 'up' else h - 2
                ty = dh - 2 if direction == 'up' else 1
                edge = 0 if direction == 'up' else h - 1
                incoming = dh - 1 if direction == 'up' else 0
                if (0 <= xx < dw and sy*w+x in wet[n] and edge*w+x in wet[n]
                    and incoming*dw+xx in wet[dest] and ty*dw+xx in wet[dest]):
                    options.append(((n, x, sy), (dest, xx, ty)))
        assert options, (n, connection)
        departure, arrival = options[0]
        warp(*departure)
        native('SetPlayerAvatarTransitionFlags', 8)
        step(90)
        before = len(transitions)
        walk(arrival)
        assert_surf()
        walk(departure)
        assert_surf()
        trip = transitions[before:]
        assert len(trip) == 2 and trip[0]['destination'][0] == dest and trip[1]['destination'][0] == n, trip
        seam_checks.append(dict(direction=direction, destination=dest, controller_roundtrip=True,
                                transitions=trip, source=list(departure), target=list(arrival)))
    assert len(seam_checks) == 4
    # The east border intersects the front low plank: explicitly try to
    # enter from the connected sea before CameraMove switches map headers.
    east = next(c for c in row['surface_connections'] if c['direction'] == 'right')
    dest = all_by_id[east['map']]
    probes_from_seam = []
    for yy in (7, 6):
        ty = yy - east['offset']
        if ty * blocks[dest][0] in wet[dest]:
            warp(dest, 0, ty)
            native('SetPlayerAvatarTransitionFlags', 8)
            step(90)
            before = (location(), position())
            step(90, 32)
            step(60)
            assert (location(), position()) == before, (n, dest, yy, state())
            assert_surf()
            probes_from_seam.append(dict(source=[dest, 0, ty], target=[n, 16, yy], blocked=True))
    assert probes_from_seam, (n, 'No Surfable east seam low-pier probe')
    low_checks.append(dict(island=row['island'], map=n, blocked_probes=probes,
                          seam_blocked_probes=probes_from_seam, surf_entry_blocked=True,
                          connected_map_entry_blocked=True, open_sea_bypass_bidirectional=True,
                          four_surface_seams_controller_roundtrip=True, seams=seam_checks,
                          no_midtrip_coordinate_or_elevation_writes=True))
    print('Native low pier and four surface seams passed:', row['island'], flush=True)

assert len(town_checks) == len(low_checks) == 7
assert hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest() == initial_sha
review = bool(lib.read8(s['gJourneyReviewMode']))
lib.stop()
result = dict(passed=True, rom_sha256=initial_sha, review_mode=review,
              town_bridges=town_checks, low_piers=low_checks,
              native_controller_town_bridge_terminal_return=True,
              walked_all_extended_deck_rows=True, native_foot_elevation_3=True,
              foot_blocks_water=True, surf_entry_blocked_on_low_deck=True,
              open_sea_bypass_bidirectional=True, all_seven_surface_seams_preserved=True,
              no_midtrip_coordinate_or_elevation_writes=True,
              placements_progress_party_are_fixtures=True, full_campaign_playthrough=False)
(args.output / 'coastal-pier-safety.json').write_text(json.dumps(result, indent=2) + '\n')
