"""Exercise native Hidden Ability slots, inheritance and a real Brock KO battle."""
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
parser.add_argument('--ability-slot', type=int, choices=[0, 1, 2], default=2)
parser.add_argument('--event-form', action='store_true', help='Validate the retained event Greninja with slot zero')
parser.add_argument('--pre-evolution', action='store_true', help='Validate that Froakie cannot transform')
options = parser.parse_args()
assert not (options.event_form and options.pre_evolution)
assert not options.event_form or options.ability_slot == 0
assert not options.pre_evolution or options.ability_slot == 2
sys.argv = [sys.argv[0], '--source', str(options.source), '--library', str(options.library),
            '--output', str(options.output), '--water-hms', '--westsea']
exec(compile((ROOT / 'tools/hoenn/validate_crossing.py').read_text().split('\nstep(900)\n')[0],
             str(ROOT / 'tools/hoenn/validate_crossing.py'), 'exec'))


def press(key=2):
    step(1, key)
    step(35)


def task(name):
    return any(lib.read8(s['gTasks'] + i * 40 + 4)
               and lib.read32(s['gTasks'] + i * 40) & ~1 == s[name] for i in range(16))


step(900)
save2 = lib.read32(s['gSaveBlock2Ptr'])
lib.write8(save2, 255)
lib.write8(save2 + 8, 255)
lib.write8(save2 + abi[45], abi[46])
lib.write32(s['gMain'], 0)
lib.write8(s['gMain'] + 0x438, 0)
lib.write32(s['gMain'] + 4, s['CB2_NewGame'] | 1)
step(300)
for _ in range(100):
    if task('Task_HandleMultichoiceGridInput'):
        break
    press(1)
assert task('Task_HandleMultichoiceGridInput')
press(1)
step(1500)
warp('Route1_Frlg', 5, 12)
native('DisableWildEncounters', 1)
ability_field, froakie, frogadier, greninja, ash, event = abi[65:71]
torrent, protean, bond = abi[71:74]
mon_size, species_offset, surf, shuriken, end_method, faint_method = abi[74:80]
scratch = s['gStringVar4'] + 800
party = s['gParties']
enemy = party + 6 * abi[2]


def set_slot(mon, slot):
    lib.write8(scratch, slot)
    native('SetMonData', mon, ability_field, scratch)


for species in [froakie, frogadier, greninja]:
    assert [native('GetSpeciesAbility', species, slot) for slot in range(3)] == [torrent, protean, bond]

wild_hidden = 0
rolls = options.ability_slot == 2 and not options.pre_evolution
if rolls:
    for _ in range(200):
        native('CreateWildMon', froakie, 10)
        slot = native('GetMonData2', enemy, ability_field)
        assert slot in [0, 1, 2]
        wild_hidden += slot == 2
    assert 1 <= wild_hidden <= 30, wild_hidden
    # Gastly has no native Hidden Ability; the roll must never create one.
    assert native('GetSpeciesAbility', 92, 2) == 0
    for _ in range(30):
        native('CreateWildMon', 92, 10)
        assert native('GetMonData2', enemy, ability_field) < 2
    for i in range(6 * abi[2]):
        lib.write8(party + i, 0)
    lib.write8(s['gPartiesCount'], 0)
    for _ in range(3):
        assert native('ScriptGiveMon', froakie, 10, 0) == 0
    set_slot(party + 2 * abi[2], 2)
    inherited = 0
    for _ in range(100):
        set_slot(party, 0)
        native('InheritAbility', party, party + abi[2], party + 2 * abi[2])
        inherited += native('GetMonData2', party, ability_field) == 2
    assert 35 <= inherited <= 85, inherited
    print('Hidden Ability rolls and inheritance passed:', wild_hidden, inherited, flush=True)
else:
    inherited = None

for i in range(6 * abi[2]):
    lib.write8(party + i, 0)
lib.write8(s['gPartiesCount'], 0)
initial_species = event if options.event_form else froakie if options.pre_evolution else greninja
expected_ability = bond if options.event_form else [torrent, protean, bond][options.ability_slot]
assert native('ScriptGiveMon', initial_species, 100, 0) == 0
# Keep the ordinary Gen9 obedience rule: train an owned low-level gift,
# rather than introducing a newly received level-100 Pokemon before badges.
lib.write8(scratch, 5)
native('SetMonData', party, abi[96], scratch)
assert native('GetMonData2', party, abi[96]) == 5
assert native('GetMonData2', party, abi[6]) == 100
assert native('GetMonData2', party, ability_field) < 2
set_slot(party, options.ability_slot)
assert native('GetMonAbility', party) == expected_ability
native('ScriptSetMonMoveSlot', 0, surf, 0)
assert native('TrySavingData', 0, max_frames=6000) == 1
set_slot(party, 0)
assert native('LoadGameSave', 0) == 1
step(30)
assert native('GetMonData2', party, ability_field) == options.ability_slot
assert native('GetMonData2', party, abi[96]) == 5

warp('PewterCity_Gym_Frlg', 4, 3)
script(b'\x05' + struct.pack('<I', s['PewterCity_Gym_EventScript_Brock']), 30)
handlers = {int(addr, 16) for addr, kind, name in re.findall(r'^(\w+) (\w) (\S+)$', raw, re.M)
            if name == 'HandleInputChooseAction'}
move_handlers = {int(addr, 16) for addr, kind, name in re.findall(r'^(\w+) (\w) (\S+)$', raw, re.M)
                 if name == 'HandleInputChooseMove'}
seen_ash = False
ash_rendered_at_action_menu = False
battle_started = False
attacks = 0
for tick in range(1200):
    in_battle = (lib.read32(s['gMain'] + 4) & ~1) == s['BattleMainCB2']
    if in_battle:
        battle_started = True
        species = lib.read16(s['gBattleMons'] + species_offset)
        if species == ash:
            if not seen_ash:
                picture('battle-bond-ash-after-ko')
            seen_ash = True
        controller = lib.read32(s['gBattlerControllerFuncs']) & ~1
        if controller in handlers:
            if species == ash and not ash_rendered_at_action_menu:
                picture('battle-bond-' + ('event' if options.event_form else 'hidden') + '-ash-ready')
                ash_rendered_at_action_menu = True
            # Wait for each native menu instead of assuming its animation duration.
            step(1, 64); step(8); step(1, 32); step(8)
            press(1)
        elif controller in move_handlers:
            step(1, 64); step(8); step(1, 32); step(8)
            press(1)
            attacks += 1
        else:
            press(2)
    elif battle_started and (lib.read32(s['gMain'] + 4) & ~1) == s['CB2_Overworld']:
        break
    else:
        press(2)
assert battle_started and attacks > 0
assert seen_ash == (options.event_form or (options.ability_slot == 2 and not options.pre_evolution)), (options.ability_slot, seen_ash)
assert ash_rendered_at_action_menu == seen_ash
if (lib.read32(s['gMain'] + 4) & ~1) != s['CB2_Overworld']:
    picture('battle-bond-incomplete')
    print('Incomplete battle:', attacks, hex(lib.read32(s['gMain'] + 4) & ~1),
          hex(lib.read32(s['gBattlescriptCurrInstr'])),
          [hex(lib.read32(s['gBattlerControllerFuncs'] + i * 4) & ~1) for i in range(4)], flush=True)
assert (lib.read32(s['gMain'] + 4) & ~1) == s['CB2_Overworld']
step(200)
restored = native('GetMonData2', party, abi[7])
assert restored == initial_species, ('Reversion', restored, initial_species)
assert native('GetMonData2', party, ability_field) == options.ability_slot
assert native('GetMonAbility', party) == expected_ability
lib.stop()
result = dict(passed=True, rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
              ability_slot=options.ability_slot, wild_hidden_observed=wild_hidden,
              wild_samples=200 if rolls else 0,
              hidden_inherited=inherited, inheritance_samples=100 if inherited is not None else 0,
              native_save_preserves_slot=True, real_brock_battle=True,
              ash_after_ko=seen_ash, normal_species_and_ability_restored=True,
              ash_rendered_at_action_menu=ash_rendered_at_action_menu,
              event_form=options.event_form, pre_evolution=options.pre_evolution)
result['fixture_met_level'] = 5
suffix = 'event' if options.event_form else 'froakie' if options.pre_evolution else 'slot-' + str(options.ability_slot)
(args.output / ('abilities-' + suffix + '.json')).write_text(json.dumps(result, indent=2) + '\n')
print(result, flush=True)
