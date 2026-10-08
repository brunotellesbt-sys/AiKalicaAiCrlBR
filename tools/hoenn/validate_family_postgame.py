"""Native selected-family rewards and exclusion of roaming route encounters.

Champion flags and travel warps are fixtures, not a complete campaign.
"""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--library', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--baseline', action='store_true')
options = parser.parse_args()
baseline_mode = options.baseline
sys.argv = [sys.argv[0], '--source', str(options.source), '--library', str(options.library), '--output', str(options.output)]
bootstrap = (ROOT / 'tools/hoenn/validate_abilities.py').read_text().split('\nability_field,')[0]
exec(compile(bootstrap, str(ROOT / 'tools/hoenn/validate_abilities.py'), 'exec'))

def special(name):
    native(name)
    return lib.read16(s['gSpecialVar_Result'])

def rawflag(flag, value):
    ptr = save() + 4720 + flag // 8
    old = lib.read8(ptr)
    lib.write8(ptr, old | (1 << (flag % 8)) if value else old & ~(1 << (flag % 8)))

hoenn_clear = abi[111] - 0x2A + 4
kanto_clear = 0x1AB8
ticket_flag, news_flag, ticket_item = 0x123, 0xFF, 727
homes = json.loads((source / '.journey-birth').read_text())['homes']

# Force an active native Latias into the current route, then exercise the real
# encounter dispatcher repeatedly. The old candidate starts random battles.
native('DeactivateAllRoamers')
assert native('TryAddRoamer', 380, 40) == 1
warp('Route101', 5, 8)
for i, value in enumerate(location()):
    lib.write8(s['sRoamerLocation'] + i, value)
assert native('IsRoamerAt', 0, *location()) == 1
encounters = sum(native('TryStartRoamerEncounter') == 1 for _ in range(100))
assert encounters > 0 if baseline_mode else encounters == 0, encounters
result = dict(passed=True, rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
              forced_active_latias=True, native_roamer_attempts=100, native_roamer_encounters=encounters,
              championship_and_warps_are_fixtures=True, full_campaign_playthrough=False)
if baseline_mode:
    lib.stop()
    (args.output / 'family-postgame-baseline.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Baseline roaming encounters:', encounters, flush=True)
    sys.exit(0)

cases = []
for current_region, map_name in [('kanto', 'Route1_Frlg'), ('hoenn', 'Route101')]:
    warp(map_name, 5, 8)
    for home in homes:
        native('VarSet', 0x40F7, home['index'])
        native('RemoveBagItem', ticket_item, 1)
        rawflag(ticket_flag, False); rawflag(news_flag, False)
        for kanto, hoenn in [(False, False), (True, False), (False, True), (True, True)]:
            rawflag(kanto_clear, kanto); rawflag(hoenn_clear, hoenn)
            assert special('JourneyFamilyPostgamePending') == (3 if hoenn else 0)
            if not hoenn:
                assert special('JourneyFamilyGiveSSTicket') == 0
                assert native('CheckBagHasItem', ticket_item, 1) == 0
            cases.append(dict(home=home['city'], index=home['index'], current_region=current_region,
                              kanto_clear=kanto, hoenn_clear=hoenn, pending=3 if hoenn else 0))
        assert special('JourneyFamilyGiveSSTicket') == 1
        assert native('CountTotalItemQuantityInBag', ticket_item) == 1
        assert special('JourneyFamilyGiveSSTicket') == 0
        assert native('CountTotalItemQuantityInBag', ticket_item) == 1
        assert special('JourneyFamilyPostgamePending') == 2
        rawflag(news_flag, True)
        assert special('JourneyFamilyPostgamePending') == 0
        # An existing ticket with an unset receipt flag must never be duplicated.
        rawflag(ticket_flag, False)
        assert special('JourneyFamilyPostgamePending') == 1
        assert special('JourneyFamilyGiveSSTicket') == 1
        assert native('CountTotalItemQuantityInBag', ticket_item) == 1
        assert special('JourneyFamilyPostgamePending') == 0
    print('All 31 family reward helpers passed in', current_region, flush=True)

for invalid in [0, 32, 65535]:
    native('VarSet', 0x40F7, invalid)
    assert special('JourneyFamilyPostgamePending') == 0
    assert special('JourneyFamilyGiveSSTicket') == 0

# Physically occupied key-item slots, set using the native encrypted-slot
# writer. Repeated Mach Bikes are a bag fixture, not obtainable gameplay.
native('VarSet', 0x40F7, 2)
native('RemoveBagItem', ticket_item, 1)
rawflag(ticket_flag, False); rawflag(news_flag, False)
pocket = s['gBagPockets'] + 4 * 8
slots, capacity = lib.read32(pocket), lib.read16(pocket + 4) & 1023
bag_before = bytes(lib.read8(slots + i) for i in range(capacity * 4))
for i in range(capacity):
    native('BagPocket_SetSlotData', pocket, i, abi[56] | (1 << 16))
assert native('AddBagItem', ticket_item, 1) == 0
assert special('JourneyFamilyGiveSSTicket') == 2
assert special('JourneyFamilyPostgamePending') == 3
for i, value in enumerate(bag_before):
    lib.write8(slots + i, value)
assert special('JourneyFamilyGiveSSTicket') == 1
assert special('JourneyFamilyPostgamePending') == 2

def finish(limit=200):
    for _ in range(limit):
        if not lib.read8(s['sLockFieldControls']):
            return
        press(1)
    picture('family-postgame-failure')
    raise AssertionError(('Mother dialogue did not finish', location()))

maps = {json.loads(p.read_text())['id']: p.parent.name for p in (source / 'data/maps').glob('*/map.json')}
dialogues = []
for index, gender, color in [(1, 0, 0), (2, 1, 1), (17, 0, 0), (17, 1, 1), (20, 1, 0), (31, 0, 1)]:
    home = homes[index - 1]
    lib.write8(lib.read32(s['gSaveBlock2Ptr']) + abi[32], gender)
    native('VarSet', 0x40F7, index)
    native('VarSet', 0x40F8, 7)
    # HOF preparation must suppress the fixed Norman choreography.
    script(b'\x04' + struct.pack('<I', s['EverGrandeCity_HallOfFame_EventScript_ReadyReceiveSSTicketEvent']) + b'\x6b\x02', 30)
    assert native('VarGet', 0x4082) == 4 and native('VarGet', 0x408C) == 4
    room = 'LittlerootTown_MaysHouse_1F' if index == 17 and gender else maps[home['living_map']]
    native('RemoveBagItem', ticket_item, 1)
    rawflag(ticket_flag, False); rawflag(news_flag, False)
    warp(room, 8, 5)
    lib.write16(s['gSpecialVar_LastTalked'], 1)
    # Execute the real mother's script with the current room/object context.
    script(b'\x05' + struct.pack('<I', s['Journey_Family']), 45)
    for _ in range(180):
        if task('Task_HandleMultichoiceInput'):
            break
        press(1)
    assert task('Task_HandleMultichoiceInput'), (index, gender)
    picture(f'family-{index:02d}-{gender}-news-choice')
    if color:
        press(128)
    press(1)
    finish()
    assert native('VarGet', 0x40D5) == color
    assert native('CountTotalItemQuantityInBag', ticket_item) == 1
    assert special('JourneyFamilyPostgamePending') == 0
    assert native('TrySavingData', 0, max_frames=6000) == 1
    assert native('LoadGameSave', 0, max_frames=6000) == 1
    step(30)
    assert native('VarGet', 0x40D5) == color
    assert native('CountTotalItemQuantityInBag', ticket_item) == 1
    assert special('JourneyFamilyPostgamePending') == 0
    script(b'\x05' + struct.pack('<I', s['Journey_Family']), 45)
    finish()
    assert native('CountTotalItemQuantityInBag', ticket_item) == 1
    dialogues.append(dict(home=home['city'], index=index, gender=gender, color=color, room=room,
                          ticket_quantity=1, news_completed=True, repeat_no_duplicate=True,
                          native_flash_save_reload=True))
    print('Native family dialogue passed:', home['city'], gender, color, flush=True)

# Even a completed two-region campaign cannot produce roaming route legends.
warp('Route101', 5, 8)
rawflag(hoenn_clear, True); rawflag(kanto_clear, True)
for flag in list(range(abi[63], abi[63] + 8)) + list(range(0x1AB0, 0x1AB8)):
    rawflag(flag, True)
for i, value in enumerate(location()):
    lib.write8(s['sRoamerLocation'] + i, value)
assert native('IsRoamerAt', 0, *location()) == 1
assert all(native('TryStartRoamerEncounter') == 0 for _ in range(100))
lib.stop()
result.update(helper_cases=cases, dialogues=dialogues, invalid_homes_no_reward=True,
              full_key_pocket_retries_without_losing_reward=True, duplicate_bikes_are_bag_fixture=True,
              existing_ticket_repairs_receipt_without_duplicate=True,
              all_sixteen_badges_set_for_final_roamer_check=True,
              completed_campaign_roamer_attempts=100, completed_campaign_roamer_encounters=0)
(args.output / 'family-postgame.json').write_text(json.dumps(result, indent=2) + '\n')
print('Native postgame validation passed:', len(cases), 'helper states and', len(dialogues), 'mother dialogues', flush=True)
