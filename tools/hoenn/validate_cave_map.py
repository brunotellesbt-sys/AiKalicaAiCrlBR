"""Open native MAP inside each coastal cave and match its actual atlas icon."""
import hashlib, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
prefix = (ROOT / 'tools/hoenn/validate_world_route_chart.py').read_text().split('\nchecks=[]')[0]
exec(compile(prefix, __file__, 'exec'))
checks = []
for cave in r['cave_approaches']:
    n = cave['map']; by_location[map_id(n)] = n
    warp(n, 14, 17); native('SetPlayerAvatarTransitionFlags', 1); step(60)
    before=(location(),position());packed=native('JourneyWorldMapPosition');expected=[packed&255,packed>>8]
    ptr=open_map();xy=lambda:[lib.read8(ptr+2056),lib.read8(ptr+2057)]
    assert xy()==expected,(n,xy(),expected)
    picture('cave-map-'+n)
    press(16);press(4);assert xy()==expected
    press(256);step(60);assert xy()==expected;picture('cave-map-'+n+'-zoom')
    press(2);wait_for(lambda:callback()==s['CB2_Overworld']);step(120);press(2)
    assert (location(),position())==before
    check=dict(map=n,tile=list(position()),marker=expected,cursor_matches_native_world_position=True,recenter=True,zoom=True,return_preserves_position=True)
    assert check['marker'] == cave['position'], (n, check['marker'], cave['position'])
    checks.append(check)
    print('Native cave MAP icon and cursor passed:', n, flush=True)
assert len(checks) == 15
lib.stop()
(args.output / 'cave-map.json').write_text(json.dumps(dict(passed=True,
    rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(), caves=checks,
    native_map_open_zoom_and_return=True, all_cave_cursor_positions_match_visible_icons=True,
    independent_initial_room_placements_are_fixtures=True), indent=2) + '\n')
