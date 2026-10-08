"""Exercise the standalone Singles PWT through native registration and battles.
Travel and high battle stats are fixtures, not a balance or campaign test.
"""
import argparse
import hashlib
import json
import re
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--library', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
options = parser.parse_args()
sys.argv = [sys.argv[0], '--source', str(options.source), '--library', str(options.library), '--output', str(options.output)]
exec(compile((ROOT / 'tools/hoenn/validate_abilities.py').read_text().split('\nability_field,')[0], str(ROOT / 'tools/hoenn/validate_abilities.py'), 'exec'))
with tempfile.TemporaryDirectory(prefix='pwt-abi-', dir='/tmp') as directory:
    out = Path(directory) / 'abi.s'
    subprocess.run([str(ROOT / '.local/arm-gcc/usr/bin/arm-none-eabi-gcc'), '-S', '-iquote', str(source / 'include'), '-include', str(source / 'src/journey_pwt.c'), '-D_(x)=x', '-DMODERN=1', '-DPOKEEMERALD', '-mthumb', '-march=armv4t', '-mabi=apcs-gnu', str(ROOT / 'tools/hoenn/fixture_pwt_abi.c'), '-o', str(out)], check=True, capture_output=True)
    table = out.read_text().split('gPWTFixtureABI:', 1)[1].split('.size', 1)[0]
    pabi = [int(n) for n in re.findall(r'\.word\s+(\d+)', table)]
assert len(pabi) == 22, pabi
state = s['sPWT']
party = s['gParties']
enemy = party + 6 * abi[2]
actions = {int(a, 16) for a, _, n in re.findall(r'^(\w+) (\w) (\S+)$', raw, re.M) if n == 'HandleInputChooseAction'}
moves = {int(a, 16) for a, _, n in re.findall(r'^(\w+) (\w) (\S+)$', raw, re.M) if n == 'HandleInputChooseMove'}

def special(name):
    native(name)
    return lib.read16(s['gSpecialVar_Result'])

def snapshot():
    return bytes(lib.read8(party + i) for i in range(6 * abi[2]))

def flags():
    return bytes(lib.read8(save() + 4720 + i) for i in range(872))

def points():
    return lib.read16(lib.read32(s['gSaveBlock2Ptr']) + pabi[6])

def money():
    return native('GetMoney', save() + pabi[7])

def until(predicate, limit=220):
    for _ in range(limit):
        if predicate(): return
        press(1)
    picture('pwt-failure')
    raise AssertionError(('PWT did not reach target', hex(lib.read32(s['gMain'] + 4)), location()))

def wait_yesno():
    until(lambda: task('Task_HandleYesNoInput'))
    step(12) # Script yes/no menus initially ignore input for five frames.

def idle():
    return (lib.read32(s['gMain'] + 4) & ~1) == s['CB2_Overworld'] and not lib.read8(s['sLockFieldControls'])

def event(label):
    lib.write16(s['gSpecialVar_LastTalked'], 1)
    script(b'\x05' + struct.pack('<I', s[label]), 45)

for i in range(6 * abi[2]): lib.write8(party + i, 0)
lib.write8(s['gPartiesCount'], 0)
species = [658, 149, 376, 121, 445, 637]
levels = [12, 75, 30, 5, 100, 20]
for i, (mon, level) in enumerate(zip(species, levels)):
    assert native('ScriptGiveMon', mon, level, 0) == 0
    for slot in range(4): native('ScriptSetMonMoveSlot', i, abi[142] if slot == 0 else 0, slot)
    # Legal moves and ability slots; battle stats alone will be boosted in RAM.
    scratch = s['gStringVar4'] + 800
    lib.write8(scratch, 2 if i == 0 else 0); native('SetMonData', party + i * abi[2], abi[65], scratch)
original = snapshot()
flags_before, money_before = flags(), money()
bp_before = points()

def enter(pool, cancel=False):
    warp('JourneyPWTLobby', 5, 11)
    step(4, 64); step(20); press(1) # Face and talk to the physical receptionist.
    wait_yesno()
    if pool != 0:
        press(128); press(1)
        wait_yesno()
        if pool == 2:
            press(128); press(1)
            wait_yesno()
    press(1)
    until(lambda: task('Task_HandleChooseMonInput'))
    step(120) # The task exists before the party-menu fade has finished.
    picture(f'pwt-{pool}-selection')
    if cancel:
        press(2); until(lambda: task('Task_HandleCancelChooseMonYesNoInput'))
        press(64); press(1); until(idle)
        assert not lib.read8(state + pabi[5])
        assert snapshot() == original
        return
    for index in range(6):
        until(lambda: task('Task_HandleChooseMonInput'))
        for _ in range(10):
            if lib.read8(s['gPartyMenu'] + abi[100]) == index: break
            press(128)
        assert lib.read8(s['gPartyMenu'] + abi[100]) == index
        press(1); until(lambda: task('Task_HandleSelectionMenuInput'))
        press(1)
        assert lib.read8(s['gSelectedOrderFromParty'] + index) == index + 1
    until(lambda: task('Task_HandleChooseMonInput'))
    assert lib.read8(s['gPartyMenu'] + abi[100]) == 6
    picture(f'pwt-{pool}-selected-six')
    press(1)
    wait_yesno()
    assert location() == map_id('JourneyPWTArena')
    assert lib.read8(state + pabi[5]) and lib.read8(state + pabi[2]) == 6
    leaves = [lib.read8(state + pabi[1] + i) for i in range(7, 15)]
    assert len(set(leaves)) == 8 and leaves.count(255) == 1
    allowed = set(range(8)) if pool == 0 else set(range(8, 16)) if pool == 1 else set(range(18))
    assert set(leaves) - {255} <= allowed
    picture(f'pwt-{pool}-quarterfinal-ready')
    return leaves

enter(0, cancel=True)
assert points() == bp_before and flags() == flags_before
records = []

def fight(round_number, test_bag=False, lose=False, forfeit=False):
    press(1)
    until(lambda: (lib.read32(s['gMain'] + 4) & ~1) == s['BattleMainCB2'])
    assert lib.read32(s['gBattleTypeFlags']) & (1 << 14)
    assert not lib.read32(s['gBattleTypeFlags']) & 1
    assert lib.read8(s['gPartiesCount']) == 6
    assert lib.read8(s['gPartiesCount'] + 1) == 6
    # Calling field specials during a battle is unsafe. Extract through the
    # battle-mon structure and party level fields; identity is audited in RAM
    # before entering via a separate helper matrix below.
    assert all(lib.read8(party + i * abi[2] + pabi[17]) == 50 for i in range(6))
    assert all(lib.read8(enemy + i * abi[2] + pabi[17]) == 50 for i in range(6))
    bag_checked = False
    forfeit_requested = ash_seen = False
    attacks = 0
    for tick in range(2400):
        cb = lib.read32(s['gMain'] + 4) & ~1
        if cb == s['BattleMainCB2']:
            ash_seen |= lib.read16(s['gBattleMons'] + abi[75]) == abi[69]
            # Stats in this fixture make tests quick; do not modify ROM parties.
            if lose:
                for i in range(6):
                    if lib.read16(party + i * abi[2] + abi[101]):
                        lib.write16(party + i * abi[2] + abi[101], 1)
                if lib.read16(s['gBattleMons'] + abi[102]):
                    lib.write16(s['gBattleMons'] + abi[102], 1)
                lib.write16(s['gBattleMons'] + abi[74] + pabi[15], 65535)
            else:
                lib.write16(s['gBattleMons'] + pabi[15], 16000)
                lib.write16(s['gBattleMons'] + pabi[16], 10000)
                lib.write16(s['gBattleMons'] + pabi[20], 30000)
                if lib.read16(s['gBattleMons'] + abi[102]):
                    lib.write16(s['gBattleMons'] + abi[102], 30000)
                for i in range(6):
                    lib.write16(party + i * abi[2] + pabi[8], 16000)
                    lib.write16(party + i * abi[2] + pabi[9], 10000)
                    lib.write16(party + i * abi[2] + pabi[21], 30000)
                    if lib.read16(party + i * abi[2] + abi[101]):
                        lib.write16(party + i * abi[2] + abi[101], 30000)
            ctrl = lib.read32(s['gBattlerControllerFuncs']) & ~1
            if ctrl in actions and forfeit and not forfeit_requested:
                press(128); press(16); press(1)
                forfeit_requested = True
            elif forfeit_requested:
                step(1, 64); step(8) # The native forfeit prompt defaults to No.
                press(1)
            elif ctrl in actions and test_bag and not bag_checked:
                press(16); press(1); step(120)
                assert (lib.read32(s['gMain'] + 4) & ~1) == s['BattleMainCB2']
                picture('pwt-bag-blocked')
                bag_checked = True
                press(1)
            elif ctrl in actions or ctrl in moves:
                step(1,64); step(8); step(1,32); step(8); press(1)
                attacks += ctrl in moves
            else: press(2)
        elif cb in {s['CB2_InitPartyMenu'], s['CB2_UpdatePartyMenu']}:
            if task('Task_HandleChooseMonInput'):
                available = []
                for slot in range(1, 6):
                    order = lib.read8(s['gBattlePartyCurrentOrder'] + slot // 2)
                    physical = (order & 15) if slot & 1 else order >> 4
                    if lib.read16(party + physical * abi[2] + abi[101]) > 0:
                        available.append(slot)
                assert available, 'No surviving tournament Pokémon available'
                desired = available[0]
                if lib.read8(s['gPartyMenu'] + abi[100]) != desired:
                    press(128)
                else: press(1)
            else: press(1)
        elif cb == s['CB2_Overworld']:
            assert lib.read8(s['gBattleOutcome']) == (pabi[18] if forfeit else 2 if lose else 1), (round_number, lib.read8(s['gBattleOutcome']))
            picture(f'pwt-round-{round_number}-' + ('forfeited' if forfeit else 'lost' if lose else 'won'))
            return dict(round=round_number, attacks=attacks, outcome=lib.read8(s['gBattleOutcome']), bag_blocked=bag_checked, ash_seen=ash_seen, forfeit=forfeit)
        else: press(1)
    picture('pwt-battle-failure')
    raise AssertionError(('PWT battle incomplete', round_number, attacks, hex(cb)))

for pool in range(3):
    leaves = enter(pool)
    wins = []
    for round_number in range(3):
        assert lib.read8(state + pabi[3]) == round_number
        wins.append(fight(round_number, test_bag=pool == 0 and round_number == 0))
        if round_number < 2:
            wait_yesno()
    until(idle)
    assert location() == map_id('JourneyPWTLobby')
    assert snapshot() == original
    assert points() == bp_before + 3 * (pool + 1)
    assert flags() == flags_before and money() == money_before
    assert special('JourneyPWTFinish') == 0
    assert points() == bp_before + 3 * (pool + 1)
    assert native('TrySavingData', 0, max_frames=6000) == 1
    assert native('LoadGameSave', 0, max_frames=6000) == 1
    step(30)
    assert snapshot() == original and points() == bp_before + 3 * (pool + 1)
    records.append(dict(pool=pool, leaves=leaves, wins=wins, original_party_byte_identical=True,
                        flags_and_money_unchanged=True, reward_bp=3, native_flash_save_reload=True))
    print('PWT full Singles tournament passed:', pool, flush=True)

enter(0)
press(128); press(1); until(idle)
assert snapshot() == original and points() == bp_before + 9
enter(1)
loss = fight(0, lose=True)
until(idle)
assert snapshot() == original and points() == bp_before + 9
assert flags() == flags_before and money() == money_before
enter(2)
forfeit = fight(0, forfeit=True)
until(idle)
assert snapshot() == original and points() == bp_before + 9
assert flags() == flags_before and money() == money_before

# Check entry guards independently, without awarding synthetic victories.
entry_guards = []
def setdata(mon, field, value, width=2):
    scratch = s['gStringVar4'] + 800
    for i in range(width): lib.write8(scratch + i, (value >> (8 * i)) & 255)
    native('SetMonData', mon, field, scratch)
catalog = json.loads((ROOT / 'tools/hoenn/catalog_metadata.json').read_text())
ids = {v['name']: int(k) for k, v in catalog['species'].items()}
for case in ['slot_out_of_range', 'same_slot', 'same_species', 'same_national_forms', 'same_item', 'egg', 'banned_mewtwo']:
    for i, value in enumerate(original): lib.write8(party + i, value)
    for i, value in enumerate([1, 2, 3, 4, 5, 6]): lib.write8(s['gSelectedOrderFromParty'] + i, value)
    if case == 'slot_out_of_range': lib.write8(s['gSelectedOrderFromParty'], 7)
    elif case == 'same_slot': lib.write8(s['gSelectedOrderFromParty'] + 1, 1)
    elif case == 'same_species':
        for i, value in enumerate(original[:abi[2]]): lib.write8(party + abi[2] + i, value)
    elif case == 'same_national_forms':
        setdata(party, abi[7], ids['SPECIES_ROTOM_HEAT'])
        setdata(party + abi[2], abi[7], ids['SPECIES_ROTOM_WASH'])
    elif case == 'same_item':
        for i in range(2): setdata(party + i * abi[2], abi[107], pabi[13])
    elif case == 'egg': setdata(party, pabi[12], 1, 1)
    elif case == 'banned_mewtwo': setdata(party, abi[7], 150)
    before = snapshot()
    assert special('JourneyPWTBegin') == 0 and snapshot() == before
    entry_guards.append(dict(case=case, refused=True, party_unchanged=True))
for i, value in enumerate(original): lib.write8(party + i, value)

# Inspect all 18 native opponent pools before battle entry. This is a roster
# fixture, not eighteen extra battle victories or a simulated championship.
rosters = []
for index in range(18):
    for i, value in enumerate([1, 2, 3, 4, 5, 6]): lib.write8(s['gSelectedOrderFromParty'] + i, value)
    assert special('JourneyPWTBegin') == 1
    node = lib.read8(state + pabi[4])
    sibling = node + 1 if node & 1 else node - 1
    lib.write8(state + pabi[1] + sibling, index)
    native('JourneyPWTPrepareBattle')
    mons = []
    for i in range(6):
        mon = enemy + i * abi[2]
        mons.append(dict(species=native('GetMonData2', mon, abi[7]), level=native('GetMonData2', mon, abi[6]),
                         item=native('GetMonData2', mon, abi[107]), move=native('GetMonData2', mon, pabi[19])))
    assert {m['level'] for m in mons} == {50}
    assert len({m['species'] for m in mons}) == len({m['item'] for m in mons}) == 6
    assert all(m['move'] for m in mons)
    trainer = lib.read16(s['sPWTTrainers'] + index * pabi[10])
    native('JourneyPWTFinish')
    assert snapshot() == original and points() == bp_before + 9
    rosters.append(dict(index=index, trainer=trainer, mons=mons))
assert any(w['ash_seen'] for r in records for w in r['wins'])
lib.stop()
result = dict(passed=True, rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
              tournaments=records, native_battle_victories=9, team_size=6, native_loss=loss,
              native_forfeit=forfeit, entry_guards=entry_guards, native_roster_teams=rosters,
              battle_bond_and_hidden_slot_restored=True, physical_receptionist_interaction=True,
              selection_cancel_restores_party=True, between_round_retirement_restores_party=True,
              defeat_restores_party_without_whiteout=True, no_bag_items=True,
              levels_normalized_to_50=True, battle_stats_and_travel_are_fixtures=True,
              full_campaign_playthrough=False, balance_validated=False)
(args.output / 'pwt.json').write_text(json.dumps(result, indent=2) + '\n')
print('Native PWT validation passed', flush=True)
