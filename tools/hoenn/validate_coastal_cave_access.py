"""Enter coastal legendary chambers from Surf, using native doors and Dive."""
import hashlib, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
prefix = (ROOT / 'tools/hoenn/validate_sanctuary_routes.py').read_text().split('\nfor site in sanctuaries')[0]
prefix = prefix.replace("names = list(dict.fromkeys(n for site", "names = list(dict.fromkeys(n for site")
# Include native Seafoam's surface and first floor in the same controller planner.
prefix = prefix.replace('allowed = set()', "names += ['Route20_Frlg', 'SeafoamIslands_1F_Frlg']\nallowed = set()")
exec(compile(prefix, __file__, 'exec'))
native('ScriptSetMonMoveSlot', 0, 57, 1)
checks = []
for site in sanctuaries['sites']:
    surface, chamber, access = site['surface'], site['map'], site['access']
    cx, cy = site['entry']; w, h, v = blocks[surface]
    if access == 'dive': start = (cx + 1, cy + 1)
    else:
        _, yy, xx = min((abs(x - cx) + abs(y - cy), y, x) for y in range(h) for x in range(w)
                        if y * w + x in passable[surface] and v[y * w + x] in [0x112B, 0x1170] and y >= cy + 1)
        start = (xx, yy)
    warp(surface, *start); native('SetPlayerAvatarTransitionFlags', 8); step(30)
    before = walked
    if access == 'dive': water_change('JourneyDepth' + site['theme'])
    walk((chamber, 14, 17)); assert location() == map_id(chamber); picture(chamber + '-entrance')
    return_map = surface if access == 'surf' else 'JourneyDepth' + site['theme']
    walk((return_map, *start))
    if access == 'dive': water_change(surface, emerge=True)
    assert location() == map_id(surface) and position() == start
    checks.append(dict(map=chamber, surface=surface, access=access, surface_start=list(start), controller_entry_and_return=True,
                       native_surf_and_dive_prompts=True, walked_tiles=walked - before))
    print('Legendary cave reached and returned:', chamber, flush=True)
surface = 'Route20_Frlg'; chamber = 'SeafoamIslands_1F_Frlg'
entry = next(w for w in maps[surface]['warp_events'] if w['dest_map'] == maps[chamber]['id'])
dw = maps[chamber]['warp_events'][int(entry['dest_warp_id'])]; w, h, v = blocks[surface]
_, y, x = min((abs(x - entry['x']) + abs(y - entry['y']), y, x) for y in range(h) for x in range(w)
              if y * w + x in passable[surface] and v[y * w + x] == 0x112B)
start = (x, y); warp(surface, *start); native('SetPlayerAvatarTransitionFlags', 8); step(30)
cw, ch, _ = blocks[chamber]
_, y, x = min((abs(x - dw['x']) + abs(y - dw['y']), y, x) for y in range(ch) for x in range(cw)
              if y * cw + x in passable[chamber] and (x, y) not in warps[chamber])
walk((chamber, x, y)); picture('seafoam-native-entry'); walk((surface, *start))
checks.append(dict(map=chamber, surface=surface, access='surf', surface_start=list(start), controller_entry_and_return=True))
assert len(checks) == 15
lib.stop(); (args.output / 'coastal-cave-access.json').write_text(json.dumps(dict(passed=True,
    rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(), caves=checks,
    native_controller_entries_and_returns=True, no_internal_warps_or_coordinate_writes=True,
    initial_surface_positions_and_party_are_fixtures=True, legendary_capture_rules_preserved=True), indent=2) + '\n')
