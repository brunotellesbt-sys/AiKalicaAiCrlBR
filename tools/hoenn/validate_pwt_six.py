"""Exercise PWT guards specifically in the new fifth and sixth selection slots."""
from pathlib import Path
import hashlib
import json
ROOT = Path(__file__).resolve().parents[2]
# Reuse native bootstrap, ABI and registration from the main validator. No fake
# battle outcomes are needed: retire before round one and inspect entry helpers.
exec(compile((ROOT / 'tools/hoenn/validate_pwt.py').read_text().split('\nenter(0, cancel=True)')[0], str(ROOT / 'tools/hoenn/validate_pwt.py'), 'exec'))
enter(0)
press(128); press(1); until(idle)
assert snapshot() == original

def restore():
    for i, value in enumerate(original): lib.write8(party + i, value)
    lib.write8(s['gPartiesCount'], 6)
    for i in range(6): lib.write8(s['gSelectedOrderFromParty'] + i, i + 1)
def setdata(mon, field, value, width=2):
    scratch = s['gStringVar4'] + 800
    for i in range(width): lib.write8(scratch + i, (value >> (8 * i)) & 255)
    native('SetMonData', mon, field, scratch)

cases = []
for case in ['only_five_party_members', 'only_five_selected', 'sixth_repeats_first_slot',
             'sixth_repeats_first_species', 'sixth_repeats_fifth_item', 'sixth_is_egg', 'sixth_is_banned']:
    restore()
    if case == 'only_five_party_members': lib.write8(s['gPartiesCount'], 5)
    elif case == 'only_five_selected': lib.write8(s['gSelectedOrderFromParty'] + 5, 0)
    elif case == 'sixth_repeats_first_slot': lib.write8(s['gSelectedOrderFromParty'] + 5, 1)
    elif case == 'sixth_repeats_first_species':
        for i, value in enumerate(original[:abi[2]]): lib.write8(party + 5 * abi[2] + i, value)
    elif case == 'sixth_repeats_fifth_item':
        for index in [4, 5]: setdata(party + index * abi[2], abi[107], pabi[13])
    elif case == 'sixth_is_egg': setdata(party + 5 * abi[2], pabi[12], 1, 1)
    elif case == 'sixth_is_banned': setdata(party + 5 * abi[2], abi[7], 150)
    before = snapshot()
    assert special('JourneyPWTBegin') == 0 and snapshot() == before
    assert not lib.read8(state + pabi[5])
    assert points() == bp_before
    cases.append(dict(case=case, refused=True, party_unchanged=True))
restore()
# A reversed full order is valid, and finishing restores the original order.
for i in range(6): lib.write8(s['gSelectedOrderFromParty'] + i, 6 - i)
assert special('JourneyPWTBegin') == 1
native('JourneyPWTPrepareBattle')
assert lib.read8(s['gPartiesCount']) == 6 and lib.read8(s['gPartiesCount'] + 1) == 6
actual = [native('GetMonData2', party + i * abi[2], abi[7]) for i in range(6)]
assert actual == list(reversed(species))
native('JourneyPWTFinish')
assert snapshot() == original and points() == bp_before
lib.stop()
result = dict(passed=True, rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
              team_size=6, guards=cases, reversed_order_preserved=True,
              original_party_restored=True, no_reward_for_helper_setup=True,
              helper_and_travel_fixtures=True, full_campaign_playthrough=False)
(args.output / 'pwt-six.json').write_text(json.dumps(result, indent=2) + '\n')
print('Native six-member PWT tail guards and ordering passed', flush=True)
