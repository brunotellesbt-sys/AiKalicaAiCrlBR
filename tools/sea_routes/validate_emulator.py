#!/usr/bin/env python3
"""Exercise real Surf boarding, sea-map seams and return paths in mGBA."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/unova'))
for flag_name, default in [('--directory', 'mods/sea-routes'),
                           ('--rom-name', 'LeafGreen-Journey-SeaRoutes'),
                           ('--output', 'mods/sea-routes/validation')]:
    if flag_name not in sys.argv: sys.argv.extend([flag_name, default])
# Reuse the established emulator/native-call helpers without executing the
# other release's full validation program.
helpers = ROOT / 'tools/unova/validate_emulator.py'
exec(compile(helpers.read_text().split('# Initialize through')[0], str(helpers), 'exec'))

step(180)
for _ in range(12): step(10, 8); step(120)
lib.write8(save() + abi['rival_name'], 255)
lib.write8(lib.read32(s['gSaveBlock2Ptr']), 255)
lib.write32(s['gMain'], 0)
lib.write8(s['gMain'] + abi['main_state'], 0)
lib.write32(s['gMain'] + 4, s['CB2_NewGame'] | 1)
step(300); tap(1); tap(128); tap(128); tap(1)
for _ in range(5): tap(1)
step(900)
for i in range(600): lib.write8(s['gPlayerParty'] + i, 0)
lib.write8(s['gPlayerPartyCount'], 0)
assert native('ScriptGiveMon', 7, 30, 0) == 0
for i in range(8): setflag(0x820 + i, False)
# Ticket/pass IDs in the pinned expanded engine (not the retail item table).
assert all(not native('CheckBagHasItem', item, 1) for item in (727, 728, 729, 730, 753, 754))

def cross(target, key):
    for _ in range(180):
        step(4, key)
        if location() == map_id(target):
            step(20)
            assert lib.read8(s['gPlayerAvatar']) & 8, ('Lost Surf', target)
            return
    raise AssertionError(('Sea seam did not connect', target, location(), position()))

routes = json.loads((directory / 'routes.json').read_text())['routes']
first = routes[1]
warp(first['port'], 7, 5)
step(20, 32)
assert not lib.read8(s['gPlayerAvatar']) & 8
assert position() == (7, 5), position()
record('sea-water-requires-surf')
native('ScriptSetMonMoveSlot', 0, 57, 0)
for route in routes[1:]:
    warp(route['port'], 7, 5)
    tap(32); tap(1); drain(); step(180)
    assert lib.read8(s['gPlayerAvatar']) & 8, (route['port'], position())
    cross(route['name'], 128)
    screenshot(route['name'] + '-surf')
    cross(route['port'], 64)
    assert lib.read8(s['gPlayerAvatar']) & 8
    record('port-sea-and-back-by-surf', port=route['port'], sea=route['name'])
    print('Port passed', route['port'], flush=True)
warp('VermilionCity', 33, 31)
assert lib.read8(s['gPlayerAvatar']) & 8
cross(routes[0]['name'], 128)
cross('VermilionCity', 64)
record('vermilion-sea-and-back-by-surf')

for i in range(len(routes) - 1):
    left, right = routes[i], routes[i + 1]
    warp(left['name'], 47, 12)
    cross(right['name'], 16)
    cross(left['name'], 32)
    record('sea-chain-bidirectional-connection', origin=left['name'], destination=right['name'])
record('sea-travel-with-no-badges-and-no-ticket')
lib.stop()
(args.output / 'results.json').write_text(json.dumps(dict(
    rom_sha256=__import__('hashlib').sha256((directory / (args.rom_name + '.gba')).read_bytes()).hexdigest(),
    checks=results), indent=2) + '\n')
print(f'{len(results)} real Surf checks passed', flush=True)
