"""Win the native Steven/Maxie/Tabitha battle and preserve completion after the rival call.

The battle is entered through its original prompt and three-Pokemon selection
screen after fixture prerequisites.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
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
    return int(re.search(r'^#define\s+' + name + r'\s+(0x[0-9a-fA-F]+)', constants, re.M)[1], 16)
def raw_flag(flag, enabled):
    address = save() + 4720 + flag // 8
    value, mask = lib.read8(address), 1 << (flag & 7)
    lib.write8(address, value | mask if enabled else value & ~mask)
def peek_var(var):
    return lib.read16(save() + abi[108] + 2 * (var - 0x4000))
def field_idle():
    return (lib.read32(s['gMain'] + 4) & ~1 == s['CB2_Overworld']
            and lib.read8(s['sGlobalScriptContextStatus']) == 2
            and not lib.read8(s['sLockFieldControls']))
for kanto in [True, False]:
    badges = list(range(0x1AB0, 0x1AB8)) if kanto else [lib.read16(s['gBadgeFlags'] + i * 2) for i in range(8)]
    for i, flag in enumerate(badges):
        raw_flag(flag, i < 6 if kanto else i > 0)
for name in ['FLAG_HIDE_CELADON_ROCKETS', 'FLAG_HIDE_SAFFRON_ROCKETS',
             'FLAG_DEFEATED_EVIL_TEAM_MT_CHIMNEY', 'FLAG_GROUDON_AWAKENED_MAGMA_HIDEOUT']:
    raw_flag(flag_id(name), True)
raw_flag(flag_id('FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN'), False)
stories = json.loads((source / '.journey-team-stories').read_text())
for trainer in stories['trainers']:
    raw_flag(0x500 + trainer['id'], True)
raw_flag(abi[116], False)
native('VarSet', abi[115], 0)
assert native('JourneyPendingCampaignEvent', 0) == 5
party, scratch = s['gParties'], s['gStringVar4'] + 800
for i in range(6 * abi[2]):
    lib.write8(party + i, 0)
lib.write8(s['gPartiesCount'], 0)
species_list = [abi[68], 6, 9, 3, 25, 143]
identities = []
for i, species in enumerate(species_list):
    assert native('ScriptGiveMon', species, 100, 0) == 0
    lib.write8(scratch, 5)
    native('SetMonData', party + i * abi[2], abi[96], scratch)
    lib.write8(scratch, 2 if i == 0 else 0)
    native('SetMonData', party + i * abi[2], abi[65], scratch)
    for slot in range(4):
        native('ScriptSetMonMoveSlot', i, abi[104] if slot == 0 else 0, slot)
    identities.append(native('GetMonData2', party + i * abi[2], abi[105]))
warp('MossdeepCity', 37, 10)
native('JourneyStartSpaceCenterInvasion')
assert native('VarGet', abi[115]) == 1
warp('MossdeepCity_SpaceCenter_2F', 2, 8)
lib.write16(s['gSpecialVar_LastTalked'], 4)
script(b'\x05' + struct.pack('<I', s['MossdeepCity_SpaceCenter_2F_EventScript_ReadyForBattlePrompt']), 30)
def handlers(name):
    return {int(a, 16) for a, kind, n in re.findall(r'^(\w+) (\w) (\S+)$', raw, re.M) if n == name}
actions, moves = handlers('HandleInputChooseAction'), handlers('HandleInputChooseMove')
targets = set().union(*(handlers(name) for name in ['HandleInputChooseTarget', 'HandleInputShowTargets', 'HandleInputShowEntireFieldTargets']))
started = False
ash_seen = False
attacks = 0
selection_seen = False
for tick in range(800):
    if tick % 100 == 0:
        print('Progress:', tick, started, attacks, peek_var(abi[115]),
              hex(lib.read32(s['gMain'] + 4) & ~1),
              hex(lib.read32(s['gBattlerControllerFuncs']) & ~1),
              lib.read8(s['gPartiesCount']), flush=True)
    callback = lib.read32(s['gMain'] + 4) & ~1
    if callback in {s['CB2_InitPartyMenu'], s['CB2_UpdatePartyMenu']} and task('Task_HandleChooseMonInput'):
        selection_seen = True
        selected = sum(lib.read8(s['gSelectedOrderFromParty'] + i) != 0 for i in range(3))
        cursor = lib.read8(s['gPartyMenu'] + abi[100])
        if selected < 3 and cursor != selected:
            step(3, 128); step(20)
        else:
            press(1)
    elif callback == s['BattleMainCB2']:
        started = True
        assert lib.read32(s['gBattleTypeFlags']) & 0x8000
        assert lib.read8(s['gBattlersCount']) == 4
        assert lib.read16(s['gPartnerTrainerId']) == abi[112]
        assert lib.read16(s['gTrainerBattleParameter'] + abi[13]) == abi[113]
        opponent_b = s['gTrainerBattleParameter'] + abi[14]
        assert lib.read8(opponent_b) | lib.read8(opponent_b + 1) << 8 == abi[114]
        form = lib.read16(s['gBattleMons'] + abi[75])
        ash_seen |= form == abi[69]
        controller = lib.read32(s['gBattlerControllerFuncs']) & ~1
        if controller in actions:
            if form == abi[69] and attacks < 3:
                picture('Steven-Maxie-Tabitha-ash-battle')
            step(3, 64); step(12); step(3, 32); step(12); press(1)
        elif controller in moves:
            assert lib.read8(s['gMoveSelectionCursor']) == 0
            press(1)
            attacks += 1
        elif controller in targets:
            press(1)
        else:
            press(2)
    elif started and peek_var(abi[115]) == 3 and field_idle():
        break
    else:
        press(1)
else:
    picture('maxie-incomplete')
    raise AssertionError(('Native multi battle/aftermath incomplete', tick, hex(callback), attacks))
assert started and attacks > 0 and ash_seen and selection_seen
assert native('JourneyPendingCampaignEvent', 0) == 6
assert native('JourneyCanStartArchieAlliance') == 1
assert native('FlagGet', abi[116]) == 1
picture('SpaceCenter-after-real-victory')
# Run the actual rival phone call that consumes the old temporary flag.
warp('MossdeepCity', 22, 10)
script(b'\x05' + struct.pack('<I', s['MossdeepCity_SpaceCenter_2F_EventScript_RivalRayquazaCall']), 30)
for _ in range(300):
    press(1)
    if field_idle():
        break
else:
    raise AssertionError('Native rival phone call did not finish')
assert native('FlagGet', abi[116]) == 0
assert native('VarGet', abi[115]) == 3
assert native('JourneyPendingCampaignEvent', 0) == 6
assert native('JourneyCanStartArchieAlliance') == 1
assert lib.read8(s['gPartiesCount']) == 6
for i, species in enumerate(species_list):
    assert native('GetMonData2', party + i * abi[2], abi[7]) == species
    assert native('GetMonData2', party + i * abi[2], abi[105]) == identities[i]
assert native('GetMonData2', party, abi[65]) == 2
assert native('JourneyGymBadgeCount', 0) == 7 and native('JourneyGymBadgeCount', 1) == 6
assert native('TrySavingData', 0, max_frames=6000) == 1
native('VarSet', abi[115], 0)
assert native('LoadGameSave', 0) == 1
step(30)
assert native('VarGet', abi[115]) == 3
assert native('JourneyCanStartArchieAlliance') == 1
lib.stop()
result = dict(passed=True, rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
              real_steven_maxie_tabitha_battle=True, native_victory_and_aftermath=True,
              native_space_center_invasion=True, ash_after_ko=True, player_attacks=attacks,
              six_owned_pokemon_and_personalities_restored=True, hidden_slot_preserved=True,
              native_rival_call_consumes_legacy_flag=True, completion_state_remains_three=True,
              archie_permission_survives_call=True, remaining_gym_stays_gated_by_archie=True,
              regional_badges_unchanged=True, native_save_preserves_completion=True,
              party_selection_screen_validated=True, prerequisites_are_initial_state_fixtures=True,
              full_campaign_playthrough=False)
(args.output / 'maxie-aftermath.json').write_text(json.dumps(result, indent=2) + '\n')
print(result, flush=True)
