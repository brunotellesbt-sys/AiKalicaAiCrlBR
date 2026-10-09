"""Native awakening permissions across all regional badge subsets and prerequisites.
Every badge and prior-event state is a fixture; this is not a campaign run.
"""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
exec(compile((ROOT / 'tools/hoenn/validate_team_missions.py').read_text().split('\nwins, completed =')[0],
             str(ROOT / 'tools/hoenn/validate_team_missions.py'), 'exec'))
assert (source / '.journey-sky-pillar-access').exists()
regional_trainer = next(t['id'] for t in stories['trainers'] if t['mission'] == 'hoenn_rocket')
checks = []
scenarios = [('clash-' + str(state), state, None, True) for state in [2, 3, 4]]
scenarios += [('city-state-' + str(state), state, None, False) for state in [0, 1, 5, 6]]
scenarios += [(key, 2, key, False) for key in [
    'already-awakened', 'weather-clear', 'archie', 'giovanni', 'space-center',
    'shelly', 'matt', 'submarine', 'institute', 'regional-mission']]
for label, city_state, missing, ready in scenarios:
    for t in stories['trainers']: rawflag(0x500 + t['id'], True)
    for trainer in [32, 30]: rawflag(0x500 + trainer, True)
    for name in ['FLAG_HIDE_SAFFRON_ROCKETS', 'FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN',
                 'FLAG_TEAM_AQUA_ESCAPED_IN_SUBMARINE']:
        rawflag(flag_id(name), True)
    rawflag(abi[111], True)
    native('VarSet', 0x409F, 3)
    native('VarSet', 0x40B3, 1)
    native('VarSet', 0x405E, city_state)
    native('VarSet', 0x40CA, 0)
    if missing == 'already-awakened': native('VarSet', 0x40CA, 1)
    if missing == 'weather-clear': rawflag(abi[111], False)
    if missing == 'archie': rawflag(flag_id('FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN'), False)
    if missing == 'giovanni': rawflag(flag_id('FLAG_HIDE_SAFFRON_ROCKETS'), False)
    if missing == 'space-center': native('VarSet', 0x409F, 0)
    if missing == 'shelly': rawflag(0x500 + 32, False)
    if missing == 'matt': rawflag(0x500 + 30, False)
    if missing == 'submarine': rawflag(flag_id('FLAG_TEAM_AQUA_ESCAPED_IN_SUBMARINE'), False)
    if missing == 'institute': native('VarSet', 0x40B3, 0)
    if missing == 'regional-mission': rawflag(0x500 + regional_trainer, False)
    for mask in range(256):
        for i, f in enumerate(hoenn_flags): rawflag(f, bool(mask & 1 << i))
        for i, f in enumerate(kanto_flags): rawflag(f, not bool(mask & 1 << i))
        expected = int(ready and mask.bit_count() >= 7)
        assert native('JourneyCanAwakenRayquaza') == expected, (label, mask, expected)
    checks.append(dict(scenario=label, all_badge_subsets=256, ready=ready, city_state=city_state))
    print('Native awakening subsets:', label, flush=True)
lib.stop()
(args.output / 'rayquaza-permission.json').write_text(json.dumps(dict(
    passed=True, rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
    cases=len(checks) * 256, checks=checks, regional_badge_threshold=7,
    other_region_badges_do_not_bypass=True, initial_badges_and_event_flags_are_fixtures=True,
    full_campaign_playthrough=False), indent=2) + '\n')
