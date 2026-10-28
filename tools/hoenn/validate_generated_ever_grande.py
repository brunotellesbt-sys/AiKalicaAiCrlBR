"""Walk the added Ever Grande houses and market through their native doors.

Initial city placement, party and cleared one-time gift flags are fixtures.
Movement, gifts, their repeat protection and shop interaction use controllers.
"""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
from validate_badge_qualifier import compiled_probe
bootstrap = (ROOT / 'tools/hoenn/validate_team_missions.py').read_text().split('\nassert pending(True) == 7')[0]
exec(compile(bootstrap, str(ROOT / 'tools/hoenn/validate_team_missions.py'), 'exec'))
rom_sha = hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest()
items = compiled_probe(source, '#include "global.h"\n#include "constants/items.h"',
                       ['ITEM_FULL_RESTORE', 'ITEM_MAX_REVIVE'])
names = ['EverGrandeCity', 'JourneyEverGrandeHouse1', 'JourneyEverGrandeHouse2']
allowed = set()
walk_prefix = 'generated-ever-grande'
walk_max_ticks = 1500
walk_transition_pictures = True
exec(compile((ROOT / 'tools/hoenn/native_water_walk.py').read_text(), 'generated-ever-grande-walk', 'exec'))
native('DisableWildEncounters', 1)
native('SetPlayerAvatarTransitionFlags', 1)
step(30)
warp('EverGrandeCity', 27, 49)
step(60)


def interact(key):
    step(3, key)
    step(20)
    press(1)
    step(20)


gifts = []
for number, (x, y, key, item, flag_name, outside_x) in enumerate([
    (6, 5, 64, items['ITEM_FULL_RESTORE'], 'FLAG_JOURNEY_EVER_FULL_RESTORE', 14),
    (8, 4, 32, items['ITEM_MAX_REVIVE'], 'FLAG_JOURNEY_EVER_MAX_REVIVE', 21),
], 1):
    name = 'JourneyEverGrandeHouse' + str(number)
    rawflag(flag_id(flag_name), False)
    before = native('CountTotalItemQuantityInBag', item)
    walk((name, x, y))
    step(30)
    interact(key)
    finish()
    after = native('CountTotalItemQuantityInBag', item)
    assert after == before + 1 and flag(flag_id(flag_name)), (name, before, after)
    picture('ever-grande-house-' + str(number) + '-gift')
    interact(key)
    finish()
    assert native('CountTotalItemQuantityInBag', item) == after
    walk(('EverGrandeCity', outside_x, 49))
    step(30)
    picture('ever-grande-house-' + str(number) + '-return')
    gifts.append(dict(map=name, item=item, before=before, after=after,
                      physical_door_entry_and_exit=True, native_gift_once=True,
                      repeat_conversation_does_not_duplicate=True))

walk(('EverGrandeCity', 26, 53))
interact(64)
for _ in range(240):
    if task('Task_ShopMenu'):
        break
    press(1)
else:
    picture('ever-grande-market-timeout')
    raise AssertionError('Could not interact with the Mega Stone seller after walking from the Center')
step(20)
picture('ever-grande-market-open')
press(2)
finish()
assert location() == map_id('EverGrandeCity') and position() == (26, 53)
assert hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest() == rom_sha
captures = [dict(file=p.name, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
            for p in sorted(args.output.glob('*.png'))]
lib.stop()
report = dict(passed=True, kind='generated-ever-grande', rom_sha256=rom_sha,
              native_validation_performed=True, compiled_rom=True,
              gifts=gifts, physical_market_access_and_native_shop=True,
              shop_closed_without_purchase=True, captures=captures,
              initial_city_party_and_gift_flags_are_fixtures=True,
              full_campaign_playthrough=False)
(args.output / 'generated-ever-grande.json').write_text(json.dumps(report, indent=2)+'\n')
print('Both native house doors, one-time gifts and Mega Stone market passed.', flush=True)
