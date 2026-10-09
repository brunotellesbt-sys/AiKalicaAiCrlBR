"""Native early gifts and original item-giver continuations in mGBA.

City choice and mother interaction use player input. Warps, direct C calls,
bag capacity, story state and original giver script entries are test fixtures.
This is not a full campaign or an original boss battle playthrough.
"""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[2]
exec(compile((ROOT / 'tools/hoenn/validate_family.py').read_text().split('\nwater =')[0],
             str(ROOT / 'tools/hoenn/validate_family.py'), 'exec'))
assert city in [1, 17]
tools = [752, 735, 720]
flags = (source / 'include/constants/flags.h').read_text()
tracked = ['FLAG_RECEIVED_DEVON_SCOPE', 'FLAG_RECEIVED_WAILMER_PAIL',
    'FLAG_HIDE_CELADON_ROCKETS', 'FLAG_GOT_POKE_FLUTE', 'FLAG_HIDE_SILPH_SCOPE',
    'FLAG_HIDE_ROUTE_120_STEVEN', 'FLAG_HIDE_ROUTE_120_KECLEON_BRIDGE']
def flag_id(name):
    return int(re.search(r'^#define\s+' + name + r'\s+(0x[0-9a-fA-F]+)', flags, re.M)[1], 16)
def quantities():
    return [native('CountTotalItemQuantityInBag', i) for i in tools]
def original_flags():
    return {name: native('FlagGet', flag_id(name)) for name in tracked}
def remove_tools():
    for item in tools:
        native('RemoveBagItem', item, native('CountTotalItemQuantityInBag', item))
def talk_mother():
    obj = next(o for o in living['object_events'] if o['script'] == 'Journey_Family')
    warp(home['house'], obj['x'], obj['y'] + 1)
    step(8, 64); step(30); press(1)

before = original_flags()
talk_mother()
step(240); picture('early-story-tools-mother')
def scope_in_bag():
    pocket = s['gBagPockets'] + 4 * 8
    slots = lib.read32(pocket)
    return any(lib.read16(slots + i * 4) == tools[0] for i in range(lib.read16(pocket + 4) & 1023))
advance_until(scope_in_bag)
step(240); picture('early-story-tool-silph-dialogue')
finish()
assert quantities() == [1, 1, 1]
assert original_flags() == before
assert native('CountTotalItemQuantityInBag', 724) == 0
assert native('JourneyGymBadgeCount', 0) == native('JourneyGymBadgeCount', 1) == 0
talk_mother(); finish()
assert quantities() == [1, 1, 1]

# All 31 selected homes share the new special, including the two original ones.
all_homes = []
for index in range(1, 32):
    native('VarSet', 0x40F7, index)
    remove_tools()
    lib.write16(s['gSpecialVar_LastTalked'], 2)
    native('JourneyFamilyGiveStoryTool')
    assert lib.read16(s['gSpecialVar_Result']) == 0 and quantities() == [0, 0, 0]
    for expected in [[1, 0, 0], [1, 1, 0], [1, 1, 1]]:
        lib.write16(s['gSpecialVar_LastTalked'], 1)
        native('JourneyFamilyGiveStoryTool')
        result = lib.read16(s['gSpecialVar_Result'])
        observed = quantities()
        assert result == 1 and observed == expected, (index, expected, result, observed, lib.read16(s['gSpecialVar_LastTalked']), var(0x40F7))
    lib.write16(s['gSpecialVar_LastTalked'], 1)
    native('JourneyFamilyGiveStoryTool')
    assert lib.read16(s['gSpecialVar_Result']) == 0 and quantities() == [1, 1, 1]
    all_homes.append(index)
assert original_flags() == before
native('VarSet', 0x40F7, city + 1)

# PC ownership is also checked when revisiting mother.
assert native('AddPCItem', tools[0], 1)
native('RemoveBagItem', tools[0], 1)
talk_mother(); finish()
assert quantities() == [0, 1, 1] and native('CheckPCHasItem', tools[0], 1)
# Remove the fixture PC slot using the native API (the initial PC holds a Potion).
# Find the slot through the save struct ABI, not a guessed offset.
with tempfile.TemporaryDirectory(prefix='story-tools-abi-', dir='/tmp') as directory:
    temp = Path(directory)
    (temp / 'abi.c').write_text('#include "global.h"\nconst u32 values[] = {offsetof(struct SaveBlock1, pcItems)};\n')
    subprocess.run([str(ROOT / '.local/arm-gcc/usr/bin/arm-none-eabi-gcc'), '-S', '-iquote', str(source / 'include'),
        '-DMODERN=1', '-DPOKEEMERALD', '-mthumb', '-march=armv4t', '-mabi=apcs-gnu', str(temp / 'abi.c'), '-o', str(temp / 'abi.s')], check=True)
    pc_offset = int(re.search(r'\.word\s+(\d+)', (temp / 'abi.s').read_text())[1])
    pc_base = save() + pc_offset
pc_index = next(i for i in range(50) if lib.read16(pc_base + i * 4) == tools[0])
native('RemovePCItem', pc_index, 1)
assert not native('CheckPCHasItem', tools[0], 1)

# Full key-item pocket and partial retries use valid encrypted slot fixtures.
pocket = s['gBagPockets'] + 4 * 8
capacity = lib.read16(pocket + 4) & 1023
slots = lib.read32(pocket)
saved_slots = bytes(lib.read8(slots + i) for i in range(capacity * 4))
for i in range(capacity * 4): lib.write8(slots + i, 0)
assert native('AddBagItem', 733, 1)
filler = bytes(lib.read8(slots + i) for i in range(4))
for index in range(capacity):
    for i, byte in enumerate(filler): lib.write8(slots + index * 4 + i, byte)
event('Journey_Family'); finish()
assert quantities() == [0, 0, 0]
for i in range(4): lib.write8(slots + (capacity - 1) * 4 + i, 0)
event('Journey_Family'); finish()
assert quantities() == [1, 0, 0]
for index in range(capacity - 3, capacity - 1):
    for i in range(4): lib.write8(slots + index * 4 + i, 0)
event('Journey_Family'); finish()
assert quantities() == [1, 1, 1], ('partial retry', quantities(), [(lib.read16(slots + i * 4), lib.read16(slots + i * 4 + 2)) for i in range(capacity - 4, capacity)])
assert original_flags() == before
for i, byte in enumerate(saved_slots): lib.write8(slots + i, byte)
event('Journey_Family'); finish()
assert quantities() == [1, 1, 1]

# Native save roundtrip preserves ownership; the next visit adds no copies.
assert native('TrySavingData', 0, max_frames=6000) == 1
remove_tools()
assert native('LoadGameSave', 0) == 1
step(30)
talk_mother(); finish()
assert quantities() == [1, 1, 1] and original_flags() == before

# Original owners still finish their original events, both with a tool in the
# bag and with that tool stored in the PC. No boss victories are injected here.
owners = [
    ('Route104_PrettyPetalFlowerShop', 'Route104_PrettyPetalFlowerShop_EventScript_WailmerPailGirl', 720, 'FLAG_RECEIVED_WAILMER_PAIL'),
    ('RocketHideout_B4F_Frlg', 'RocketHideout_B4F_EventScript_SilphScope', 752, 'FLAG_HIDE_SILPH_SCOPE'),
    ('Route120', 'Route120_EventScript_StevenGiveDeconScope', 735, 'FLAG_RECEIVED_DEVON_SCOPE'),
]
owner_cases = []
for name, entry, item, received in owners:
    for storage in ['bag', 'pc', 'missing']:
        if not native('CheckBagHasItem', item, 1): assert native('AddBagItem', item, 1)
        if storage == 'missing': native('RemoveBagItem', item, 1)
        if storage == 'pc':
            assert native('AddPCItem', item, 1)
            native('RemoveBagItem', item, 1)
        native('FlagClear', flag_id(received))
        if name == 'Route120': native('FlagClear', flag_id('FLAG_HIDE_ROUTE_120_STEVEN'))
        data = json.loads((source / f'data/maps/{name}/map.json').read_text())
        obj = next(o for o in data['object_events'] if o['script'] == ('Route120_EventScript_Steven' if name == 'Route120' else entry))
        warp(name, obj['x'], obj['y'] + 1)
        event(entry, int(obj['local_id']) if str(obj.get('local_id')).isdigit() else next(i+1 for i,o in enumerate(data['object_events']) if o == obj))
        finish()
        assert native('FlagGet', flag_id(received))
        assert native('CountTotalItemQuantityInBag', item) == int(storage != 'pc')
        if storage == 'pc':
            assert native('CheckPCHasItem', item, 1)
            pc_base = save() + pc_offset
            pc_index = next(i for i in range(50) if lib.read16(pc_base + i * 4) == item)
            native('RemovePCItem', pc_index, 1)
        owner_cases.append(dict(map=name, script=entry, storage=storage, original_receipt_flag_set=True, duplicate=False))

# The original dropped Scope must remain collectable when the key pocket is full.
native('FlagClear', flag_id('FLAG_HIDE_SILPH_SCOPE'))
warp('RocketHideout_B4F_Frlg', 10, 3)
pocket = s['gBagPockets'] + 4 * 8
capacity = lib.read16(pocket + 4) & 1023
slots = lib.read32(pocket)
saved_slots = bytes(lib.read8(slots + i) for i in range(capacity * 4))
for i in range(capacity * 4): lib.write8(slots + i, 0)
assert native('AddBagItem', 733, 1)
filler = bytes(lib.read8(slots + i) for i in range(4))
for index in range(capacity):
    for i, byte in enumerate(filler): lib.write8(slots + index * 4 + i, byte)
event('RocketHideout_B4F_EventScript_SilphScope'); finish()
assert not native('FlagGet', flag_id('FLAG_HIDE_SILPH_SCOPE'))
assert native('CountTotalItemQuantityInBag', 752) == 0
for i in range(4): lib.write8(slots + (capacity - 1) * 4 + i, 0)
event('RocketHideout_B4F_EventScript_SilphScope'); finish()
assert native('FlagGet', flag_id('FLAG_HIDE_SILPH_SCOPE'))
assert native('CountTotalItemQuantityInBag', 752) == 1
for i, byte in enumerate(saved_slots): lib.write8(slots + i, byte)
lib.stop()
(args.output / 'early-story-tools.json').write_text(json.dumps(dict(passed=True,
    rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
    city=home['city'], region='Hoenn' if hoenn else 'Kanto', real_city_choice_and_mother_input=True,
    all_selected_homes_native_special=all_homes, mother_only=True, zero_badges=True,
    original_quest_flags_preserved_by_mother=True, poke_flute_not_given_at_start=True,
    pc_ownership_prevents_duplicates=True, full_bag_and_partial_retries=True,
    native_save_roundtrip=True, original_item_giver_continuations=owner_cases,
    silph_scope_pickup_full_bag_retry=True,
    fixtures=['warps', 'all-home C calls', 'encrypted pocket capacity and mother script entries', 'owner scene states and entries'],
    full_campaign_playthrough=False, original_boss_battles_played=False), indent=2) + '\n')
print('Native early story tools passed:', home['city'], flush=True)
