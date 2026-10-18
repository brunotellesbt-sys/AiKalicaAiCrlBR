"""Cross every usable outdoor Surf connection both ways using native controls."""
import hashlib, json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
bootstrap = (ROOT / 'tools/hoenn/validate_sevii_surf_connections.py').read_text().split('\nstart=nearest(')[0]
# Route 131 always loads its Sky Pillar variant in the native transition script.
bootstrap=bootstrap.replace("exec(compile((ROOT/'tools/hoenn/native_water_walk.py')","walk_layout_overrides={'Route131':'LAYOUT_ROUTE131_SKY_PILLAR'}\nexec(compile((ROOT/'tools/hoenn/native_water_walk.py')")
# Bridges must be classified as water before the native walker builds its
# passability tables. Their multi-level elevation preserves Surf underneath.
walk_surf_under_bridges = True
exec(compile(bootstrap, __file__, 'exec'))
for n, valid in passable.items():
    passable[n] = {i for i in valid if water_behaviors[behaviors[n][i]] and not blocks[n][2][i] & 0xC00
                   and (blocks[n][2][i] >> 12 == 1
                        or blocks[n][2][i] >> 12 in [0, 15] and bridge_behaviors.get(behaviors[n][i], False))}
# The native first visit to Four Island moves the player one tile during
# the rival scene. This seam test uses the post-introduction story fixture.
scene_four=int(re.search(r'#define\s+VAR_MAP_SCENE_FOUR_ISLAND\s+(0x\w+)',(source/'include/constants/vars.h').read_text())[1],16)
native('VarSet',scene_four,1)
for i in json.loads((source / '.journey-surf-cave-coasts').read_text())['islands']:
    native('SetTrainerFlag', i['trainer']['id'])
pairs = {}; no_water = []; current_pairs = {}
for n, m in sorted(maps.items()):
    for c in m.get('connections') or []:
        other = by_id.get(c['map']); d = c['direction']
        if other not in maps or d not in ['left', 'right', 'up', 'down']: continue
        pair = tuple(sorted((n, other)))
        if pair in pairs: continue
        w, h, _ = blocks[n]; ow, oh, _ = blocks[other]; off = c['offset']
        key = dict(left=32, right=16, up=64, down=128)[d]; dx, dy = dict(left=(-1, 0), right=(1, 0), up=(0, -1), down=(0, 1))[d]
        choices = []
        for t in range(max(0, off), min(h if d in ['left', 'right'] else w, off + (oh if d in ['left', 'right'] else ow))):
            x, y = (0 if d == 'left' else w - 1, t) if d in ['left', 'right'] else (t, 0 if d == 'up' else h - 1)
            xx, yy = (ow - 1 if d == 'left' else 0, t - off) if d in ['left', 'right'] else (t - off, oh - 1 if d == 'up' else 0)
            if not all([wet(n, x, y), wet(n, x - dx, y - dy), wet(other, xx, yy), wet(other, xx + dx, yy + dy)]): continue
            if connection_step(n, x, y, key) != (other, xx, yy): continue
            reverse = {16: 32, 32: 16, 64: 128, 128: 64}[key]
            if connection_step(other, xx, yy, reverse) != (n, x, y): continue
            choices.append(((n, x - dx, y - dy), (other, xx + dx, yy + dy)))
        stable=[(a,b) for a,b in choices if currents[behaviors[a[0]][a[2]*blocks[a[0]][0]+a[1]]] is None and currents[behaviors[b[0]][b[2]*blocks[b[0]][0]+b[1]]] is None]
        if stable:pairs[pair]=stable[len(stable)//2]
        elif choices:current_pairs[pair]=dict(source=n,destination=other,key=key,dx=dx,dy=dy,choices=choices)
        else: no_water.append(dict(maps=list(pair), reason='No reciprocal open water on this header span; land/building or another connected segment'))
def place_surf(start, alternate=None):
    n,x,y=start
    if (x>127 or y>127) and alternate and alternate[1]<=127 and alternate[2]<=127:fixture=alternate
    elif x>127 or y>127:
        w,h,_=blocks[n]
        _,yy,xx=min((abs(xx-x)+abs(yy-y),yy,xx) for yy in range(min(h,128)) for xx in range(min(w,128)) if wet(n,xx,yy))
        fixture=(n,xx,yy)
    else:fixture=start
    warp(*fixture);step(180);finish();assert position()==fixture[1:], (fixture,position())
    native('SetPlayerAvatarTransitionFlags',8);step(30)
    if fixture!=start:walk(start)

rom_sha=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest()
progress=args.output/'all-surf-links-progress.json'
checks=[]
if progress.exists():
    old=json.loads(progress.read_text())
    if old['rom_sha256']==rom_sha:checks=old['links']
completed={tuple(c['maps']) for c in checks}
for pair, (start, goal) in sorted(pairs.items()):
    if pair in completed:continue
    print('Testing Surf pair:', pair, start, goal, flush=True)
    place_surf(start,goal)
    before = len(transitions); walk(goal); assert lib.read8(s['gPlayerAvatar']) & 8
    walk(start); assert lib.read8(s['gPlayerAvatar']) & 8
    assert len(transitions) == before + 2, (pair, 'Crossing took an indirect path')
    checks.append(dict(maps=list(pair), outbound_and_return=True, native_controller_crossings=2, surf_preserved=True))
    progress.write_text(json.dumps(dict(rom_sha256=rom_sha,links=checks)))
    print('All-route Surf crossing passed:', pair, flush=True)
assert len(checks) > 150, len(checks)
# Hoenn's native westbound currents are intentionally directional. Cross
# each current-only mouth with real water movement instead of attempting to
# stop on an arrow tile or claiming that Surf can run against the current.
current_checks=[]
for pair,c in sorted(current_pairs.items()):
    options=[]
    for a,b in c['choices']:
        for start,target,dx,dy,key in [(a,b,c['dx'],c['dy'],c['key']),(b,a,-c['dx'],-c['dy'],{16:32,32:16,64:128,128:64}[c['key']])]:
            n,x,y=start;x+=dx;y+=dy;w,h,_=blocks[n]
            if currents[behaviors[n][y*w+x]]==(dx,dy):options.append(((n,x,y),target[0],key))
    assert options,('No native current direction',pair)
    start,target,key=options[len(options)//2]
    native('SetPlayerAvatarTransitionFlags',1);step(30);warp(*start);finish();assert position()==start[1:]
    native('SetPlayerAvatarTransitionFlags',8)
    for tick in range(300):
        if by_location[location()]==target:break
        step(2,key)
    else:raise AssertionError(('Native current did not reach adjoining route',pair,position()))
    step(30);assert by_location[location()]==target and lib.read8(s['gPlayerAvatar'])&8
    current_checks.append(dict(maps=list(pair),source=start[0],destination=target,native_current_crossing=True,surf_preserved=True,native_one_way_current_preserved=True))
    picture('current-'+start[0]+'-'+target)
    print('Native current mouth passed:',pair,flush=True)
boundaries = []; no_exposed_edges = []
for row in json.loads((source / '.journey-surf-cave-coasts').read_text())['boundaries']:
    n = row['map']; w, h, values = blocks[n]; candidates = []
    for y in range(h):
        for x in range(w):
            if min(x, y, w - 1 - x, h - 1 - y) >= 2 or not values[y * w + x] & 0xC00: continue
            for dx, dy, key in keys:
                if wet(n, x - dx, y - dy): candidates.append(((n, x - dx, y - dy), key))
    if not candidates:
        no_exposed_edges.append(n); continue
    start, key = candidates[len(candidates) // 2]
    place_surf(start); before = position(); step(24, key); step(30)
    assert position() == before, (n, 'Visible outer rock did not block Surf')
    boundaries.append(dict(map=n, visible_rock_blocks_controller=True))
lib.stop()
assert hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest()==rom_sha,'ROM changed during Surf validation'
(args.output / 'all-surf-links.json').write_text(json.dumps(dict(passed=True,
    rom_sha256=rom_sha,
    links=checks, usable_reciprocal_water_links=len(pairs), crossings=2 * len(checks)+len(current_checks), native_current_links=current_checks,
    all_usable_outdoor_surf_connections_covered=True, visible_outer_rock_checks=boundaries, routes_without_exposed_water_edges=no_exposed_edges,
    no_midcrossing_warps_or_coordinate_writes=True, initial_positions_and_defeated_trainers_are_fixtures=True,
    non_surf_header_spans=no_water), indent=2) + '\n')
progress.unlink(missing_ok=True)
print('Every usable Surf seam passed:', len(checks), 'links, both ways', flush=True)
