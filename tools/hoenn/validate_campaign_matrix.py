"""Exercise regional mission gates for all 256 badge subsets in each region.

Flags are initial-state fixtures, not simulated battle victories or campaign playthroughs.
The gate decisions execute the actual ROM's ARM functions.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--library', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
options = parser.parse_args()
sys.argv = [sys.argv[0], '--source', str(options.source), '--library', str(options.library),
            '--output', str(options.output)]
bootstrap = (ROOT / 'tools/hoenn/validate_abilities.py').read_text().split('\nability_field,')[0]
exec(compile(bootstrap, str(ROOT / 'tools/hoenn/validate_abilities.py'), 'exec'))
constants = (source / 'include/constants/flags.h').read_text()
def flag_id(name):
    if name == 'FLAG_SYS_WEATHER_CTRL':
        return abi[111]
    return int(re.search(r'^#define\s+' + name + r'\s+(0x[0-9a-fA-F]+)', constants, re.M)[1], 16)
def raw_flag(flag, enabled):
    address = save() + 4720 + flag // 8
    value, mask = lib.read8(address), 1 << (flag & 7)
    lib.write8(address, value | mask if enabled else value & ~mask)
def bank(flags, mask):
    for i, flag in enumerate(flags):
        raw_flag(flag, bool(mask & 1 << i))
stories = json.loads((source / '.journey-team-stories').read_text())
trainer_ids = {t['key']: t['id'] for t in stories['trainers']}
kanto_badges = list(range(0x1AB0, 0x1AB8))
hoenn_badges = [lib.read16(s['gBadgeFlags'] + i * 2) for i in range(8)]
completion = ['FLAG_HIDE_CELADON_ROCKETS', 'FLAG_HIDE_SAFFRON_ROCKETS',
              'FLAG_DEFEATED_EVIL_TEAM_MT_CHIMNEY', 'FLAG_GROUDON_AWAKENED_MAGMA_HIDEOUT',
              'FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN']
scenarios = [(True, 'complete', 0, 0, None), (False, 'complete', 0, 0, None),
             (True, 'rocket_hideout', 2, 1, completion[0]),
             (True, 'silph', 6, 2, completion[1]),
             (False, 'chimney', 2, 3, completion[2]),
             (False, 'magma_hideout', 5, 4, completion[3]),
             (False, 'space_center', 7, 5, 'space_center'),
             (False, 'giovanni_required', 7, 13, completion[1]),
             (False, 'archie', 7, 6, completion[4])]
if (source / '.journey-story-aftermath').exists():
    scenarios.append((False, 'weather_crisis', 7, 14, 'weather_crisis'))
for mission in stories['missions']:
    scenarios.append((mission['kanto'], mission['key'], mission['badge_count'],
                      mission['event'], 0x500 + trainer_ids[mission['trainers'][0]]))
checks = []
for kanto, name, threshold, event, missing in scenarios:
    raw_flag(flag_id('FLAG_SYS_WEATHER_CTRL'), False)
    for flag in completion:
        raw_flag(flag_id(flag), True)
    native('VarSet', 0x409F, 3)
    for trainer in stories['trainers']:
        raw_flag(0x500 + trainer['id'], True)
    if missing == 'weather_crisis':
        raw_flag(flag_id('FLAG_SYS_WEATHER_CTRL'), True)
    elif missing == 'space_center':
        native('VarSet', 0x409F, 0)
    elif isinstance(missing, str):
        raw_flag(flag_id(missing), False)
    elif missing is not None:
        raw_flag(missing, False)
    own, other = (kanto_badges, hoenn_badges) if kanto else (hoenn_badges, kanto_badges)
    for mask in range(256):
        bank(own, mask)
        count = mask.bit_count()
        # Reverse the other region's advancement, including both extreme cases.
        bank(other, mask ^ 255)
        assert native('JourneyGymBadgeCount', int(kanto)) == count
        expected = event if event and count >= threshold else 0
        actual = native('JourneyPendingCampaignEvent', int(kanto))
        assert actual == expected, (name, mask, count, expected, actual)
    checks.append(dict(region='kanto' if kanto else 'hoenn', scenario=name,
                       badge_subsets=256, threshold=threshold, pending_event=event))
    print('All badge subsets passed:', name, flush=True)
# Permissions test the cross-region prerequisite separately from pending-door choice.
for count in range(9):
    bank(kanto_badges, (1 << count) - 1)
    bank(hoenn_badges, (1 << count) - 1)
    for flag in completion:
        raw_flag(flag_id(flag), True)
    for trainer in stories['trainers']:
        raw_flag(0x500 + trainer['id'], True)
    native('VarSet', 0x409F, 3)
    assert native('JourneyCanChallengeSilph') == int(count >= 6)
    assert native('JourneyCanStartArchieAlliance') == int(count >= 7)
    raw_flag(flag_id('FLAG_HIDE_SAFFRON_ROCKETS'), False)
    assert not native('JourneyCanStartArchieAlliance')
    raw_flag(flag_id('FLAG_HIDE_SAFFRON_ROCKETS'), True)
    native('VarSet', 0x409F, 1)
    assert not native('JourneyCanStartArchieAlliance')
lib.stop()
result = dict(passed=True, rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
              native_gate_decisions=True, checks=checks, gate_cases=len(checks) * 256,
              permission_cases=9 * 4, all_regional_badge_subsets=True,
              other_region_badges_cannot_bypass_gate=True, giovanni_and_space_center_required=True,
              flags_are_initial_state_fixtures=True, full_campaign_playthrough=False)
(args.output / 'campaign-matrix.json').write_text(json.dumps(result, indent=2) + '\n')
print(result, flush=True)
