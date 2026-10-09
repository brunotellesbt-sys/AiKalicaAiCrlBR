"""Native altar capture, escape/retry and real Continue on the current ROM.
Party, badges, Master Ball and initial surface position are explicit fixtures.
The chamber entry, interaction, battle actions and return use native controls.
"""
from pathlib import Path
import argparse
import sys
import hashlib
import json
import re
import subprocess

selector = argparse.ArgumentParser(add_help=False)
selector.add_argument('--national-dex', type=int, default=1025)
selection, remaining = selector.parse_known_args()
sys.argv = [sys.argv[0], *remaining]
ROOT = Path(__file__).resolve().parents[2]
exec(compile((ROOT / 'tools/hoenn/validate_team_missions.py').read_text().split('\nwins, completed =')[0],
             str(ROOT / 'tools/hoenn/validate_team_missions.py'), 'exec'))
r = json.loads((source / '.journey-sanctuaries').read_text())
cap = next(c for c in r['captures'] if c['national_dex'] == selection.national_dex)
site = next(c for c in r['sites'] if c['theme'] == cap['site'])
depth = 'JourneyDepth' + site['theme']
names = [site['surface'], cap['map']] + ([depth] if site['access'] == 'dive' else [])
allowed = set()
walk_prefix = 'special-capture'
exec(compile((ROOT / 'tools/hoenn/native_water_walk.py').read_text(),
             str(ROOT / 'tools/hoenn/native_water_walk.py'), 'exec'))
action_handlers = actions
compiled = subprocess.run([str(ROOT / '.local/arm-gcc/usr/bin/arm-none-eabi-gcc'), '-S',
    '-iquote', str(source / 'include'), '-x', 'c', '-', '-o', '-'], input='''
#include "constants/flags.h"
const unsigned clear_flags[] = {FLAG_SYS_GAME_CLEAR, FLAG_KANTO_GAME_CLEAR};
''', text=True, capture_output=True, check=True).stdout
clear_flags = [int(n) for n in re.findall(r'\.word\s+(\d+)', compiled.split('clear_flags:', 1)[1].split('.size', 1)[0])]
assert len(clear_flags) == 2
for f in clear_flags: rawflag(f, False)
for i in range(6 * abi[2]): lib.write8(party + i, 0)
lib.write8(s['gPartiesCount'], 0)
assert native('ScriptGiveMon', 150, 100, 0) == 0
native('ScriptSetMonMoveSlot', 0, abi[142], 0)
native('ScriptSetMonMoveSlot', 0, abi[76], 1)
native('ScriptSetMonMoveSlot', 0, 291, 2)
assert native('GetSetPokedexFlag', cap['national_dex'], 1) == 0
native('FlagSet', abi[50]); assert native('AddBagItem', abi[64], 1)
mapdata = json.loads((source / 'data/maps' / cap['map'] / 'map.json').read_text())
local_id = next(i + 1 for i, obj in enumerate(mapdata['object_events']) if obj.get('flag') == cap['flag'])
def altar_present():
    group, num = map_id(cap['map'])
    return native('GetObjectEventIdByLocalIdAndMap', local_id, num, group) < 16

def badges(k, h):
    for count, bank in [(k, kanto_flags), (h, hoenn_flags)]:
        for i, f in enumerate(bank): rawflag(f, i < count)

def talk():
    x, y = cap['position']
    walk((cap['map'], x, y + 1))
    assert altar_present()
    step(4, 64); step(30)
    lib.write16(s['gSpecialVar_Result'], 0xFFFF)
    press(1)

badges(8, 7)
cx, cy = site['entry']
start = (cx, cy + 9) if site['access'] == 'surf' else (cx + 1, cy + 1)
def water_change(target, emerge=False):
    assert native('TrySetDiveWarp') == (1 if emerge else 2)
    if emerge: press(2)
    for _ in range(160):
        press(1)
        if location() == map_id(target): break
    step(120); finish()
    assert location() == map_id(target)
warp(site['surface'], *start)
native('SetPlayerAvatarTransitionFlags', 8); step(30)
if site['access'] == 'dive': water_change(depth)
walk((cap['map'], 14, 17))
talk(); picture('special-locked'); finish()
assert not native('JourneySpecialUnlocked')
assert not native('GetSetPokedexFlag', cap['national_dex'], 1)
assert altar_present()
badges(8, 8)
assert native('JourneySpecialUnlocked')
assert not any(flag(f) for f in clear_flags)
def start_battle():
    talk()
    for _ in range(160):
        cb = lib.read32(s['gMain'] + 4) & ~1
        if cb == s['BattleMainCB2']: break
        press(1)
    else:
        picture('battle-start-failure')
        raise AssertionError(('No native battle', hex(cb), lib.read16(s['gSpecialVar_Result'])))
    step(400)
    print('Battle start:',hex(lib.read32(s['gBattleTypeFlags'])),hex(lib.read32(s['gMain']+4)&~1),flush=True)
    for _ in range(80):
        if (lib.read32(s['gBattlerControllerFuncs'])&~1) in action_handlers:break
        press(2)
    assert (lib.read32(s['gBattlerControllerFuncs'])&~1) in action_handlers
    step(1,64);step(10);step(1,32);step(10)
    assert lib.read8(s['gActionSelectionCursor'])==0
    picture('special-battle')
    assert (lib.read32(s['gMain']+4)&~1)==s['BattleMainCB2']
    assert not lib.read32(s['gBattleTypeFlags'])&abi[10]
    assert lib.read16(s['gBattleMons'] + abi[74] + abi[75]) == cap['id']
start_battle()
# Action menu: Fight / Bag / Pokemon / Run; Run is lower-right.
step(1,128);step(10);step(1,16);step(10);assert lib.read8(s['gActionSelectionCursor'])==3
step(1,1);step(300)
for _ in range(30):
    if location()==map_id(cap['map']) and (lib.read32(s['gMain']+4)&~1)==s['CB2_Overworld']:break
    press(2)
print('Escape callback:',hex(lib.read32(s['gMain']+4)&~1),flush=True)
assert (lib.read32(s['gMain']+4)&~1)==s['CB2_Overworld']
step(200)
assert lib.read8(s['gBattleOutcome']) == 4
assert native('GetSetPokedexFlag',cap['national_dex'],1)==0
assert not native('FlagGet',cap['flag_id'])
# Defeat without catching, then retry the same physical NPC.
start_battle()
attacks = 0
for _ in range(900):
    cb = lib.read32(s['gMain'] + 4) & ~1
    if cb == s['BattleMainCB2']:
        lib.write16(s['gBattleMons'] + pabi[15], 16000) # KO-only attack fixture.
        controller = lib.read32(s['gBattlerControllerFuncs']) & ~1
        if controller in actions | moves:
            step(1,64); step(10); step(1,32); step(10); press(1)
            attacks += controller in moves
        else: press(2)
    elif cb == s['CB2_Overworld']:
        finish(); break
    else: press(1)
else: raise AssertionError('Native knockout did not finish')
assert attacks and lib.read8(s['gBattleOutcome']) == 1
assert not native('GetSetPokedexFlag', cap['national_dex'], 1)
assert not flag(cap['flag_id']) and altar_present()
assert lib.read8(s['gPartiesCount']) == 1
native('HealPlayerParty')
picture('special-after-knockout')
start_battle()
step(1,16);step(10);assert lib.read8(s['gActionSelectionCursor'])==1
step(1,1);step(90);picture('special-bag')
# With Master Ball as the only usable item, choose its pocket and use it.
step(1,16);step(120);picture('special-ball-pocket')
step(1,1);step(60);picture('special-item-choice')
step(1,1);step(300)
for _ in range(100):
    if (lib.read32(s['gMain']+4)&~1)==s['CB2_Overworld']:break
    press(2)
picture('special-after-capture')
print('Capture callback:',hex(lib.read32(s['gMain']+4)&~1),flush=True)
assert (lib.read32(s['gMain']+4)&~1)==s['CB2_Overworld']
step(200)
assert lib.read8(s['gBattleOutcome']) == 7
assert native('GetSetPokedexFlag',cap['national_dex'],1)
assert native('FlagGet',cap['flag_id'])
assert lib.read8(s['gPartiesCount']) == 2
assert not altar_present()

def state():
    return dict(map=by_location[location()], position=list(position()),
                mode=lib.read8(s['gPlayerAvatar']) & 25,
                kanto_badges=native('JourneyGymBadgeCount', 1), hoenn_badges=native('JourneyGymBadgeCount', 0),
                league_clear=[flag(f) for f in clear_flags], caught_dex=bool(native('GetSetPokedexFlag', cap['national_dex'], 1)),
                capture_flag=flag(cap['flag_id']), party_count=lib.read8(s['gPartiesCount']),
                captured_species=native('GetMonData2', party + abi[2], abi[7]),
                captured_personality=native('GetMonData2', party + abi[2], abi[105]),
                captured_ot=native('GetMonData2', party + abi[2], abi[106]))

saves = []
def checkpoint(label):
    before = state()
    assert before['captured_species'] == cap['id'] and before['caught_dex'] and before['capture_flag']
    assert before['league_clear'] == [False, False]
    assert native('TrySavingData', 0, max_frames=6000) == 1
    assert native('LoadGameSave', 0, max_frames=6000) == 1
    lib.write32(s['gMain'] + 4, s['CB2_ContinueSavedGame'] | 1)
    step(1500); finish()
    after = state(); assert before == after, (label, before, after)
    saves.append(dict(label=label, before=before, after=after))
    picture(label + '-after-continue')

checkpoint('captured-chamber')
assert not altar_present()
# Interact again at the former altar: no NPC, battle or duplicate party member.
x, y = cap['position']
walk((cap['map'], x, y + 1)); step(4, 64); step(30)
for _ in range(12):
    press(1)
    assert lib.read32(s['gMain'] + 4) & ~1 not in [s['CB2_InitBattle'], s['BattleMainCB2']]
assert lib.read8(s['gPartiesCount']) == 2
walk(((depth if site['access'] == 'dive' else site['surface']), *start))
if site['access'] == 'dive':
    checkpoint('captured-underwater-return')
    water_change(site['surface'], emerge=True)
checkpoint('captured-surf-return')
if site['access'] == 'dive': water_change(depth)
walk((cap['map'], x, y + 1))
assert not altar_present() and flag(cap['flag_id'])
assert native('GetSetPokedexFlag', cap['national_dex'], 1) and lib.read8(s['gPartiesCount']) == 2
picture('captured-altar-absent-after-reentry')
lib.stop()
(args.output / 'special-capture-continue.json').write_text(json.dumps(dict(
    passed=True, rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
    species=cap['species'], species_id=cap['id'], national_dex=cap['national_dex'], access=site['access'],
    locked_with_15_badges=True, unlocked_with_16_before_leagues=True,
    real_escape_and_retry=True, escape_outcome=4, capture_outcome=7, real_knockout_and_retry=True, knockout_outcome=1, knockout_attacks=attacks, real_master_ball_capture=True,
    native_surface_entry_return_and_reentry=True, no_internal_warps_or_script_entries=True,
    captured_npc_absent_after_continue_and_reentry=True, no_duplicate_after_continue=True,
    save_continue=saves, position_changes=walked, transitions=transitions,
    party_badges_ball_and_initial_surface_position_are_fixtures=True, knockout_attack_boost_is_fixture=True,
    wild_encounters_disabled=True, full_campaign_playthrough=False, balance_validated=False,
    all_special_species_captures_validated=False), indent=2) + '\n')
print('Native capture, escape/KO retries and', len(saves), 'real Continues passed', flush=True)
