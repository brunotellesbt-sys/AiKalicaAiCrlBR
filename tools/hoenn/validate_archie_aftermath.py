"""Win the real Giovanni/Archie/Shelly battle and execute its entire aftermath.

Badges and preceding missions are initial-state fixtures. Victory, scenes,
party restoration and native save/reload are exercised in the compiled game.
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
    if name == 'FLAG_SYS_WEATHER_CTRL':
        return abi[111]
    return int(re.search(r'^#define\s+' + name + r'\s+(0x[0-9a-fA-F]+)', constants, re.M)[1], 16)
def raw_flag(flag, enabled):
    address = save() + 4720 + flag // 8
    value, mask = lib.read8(address), 1 << (flag & 7)
    lib.write8(address, value | mask if enabled else value & ~mask)
for kanto, count in [(True, 6), (False, 7)]:
    badges = list(range(0x1AB0, 0x1AB8)) if kanto else [lib.read16(s['gBadgeFlags'] + i * 2) for i in range(8)]
    for i, flag in enumerate(badges):
        raw_flag(flag, i < count if kanto else i > 0)
for name in ['FLAG_HIDE_CELADON_ROCKETS', 'FLAG_HIDE_SAFFRON_ROCKETS',
             'FLAG_DEFEATED_EVIL_TEAM_MT_CHIMNEY', 'FLAG_GROUDON_AWAKENED_MAGMA_HIDEOUT']:
    raw_flag(flag_id(name), True)
stories = json.loads((source / '.journey-team-stories').read_text())
ids = {t['key']: t['id'] for t in stories['trainers']}
for mission in stories['missions']:
    for trainer in mission['trainers']:
        raw_flag(0x500 + ids[trainer], True)
for trainer in ['TRAINER_JOURNEY_ARCHIE_ALLIANCE', 'TRAINER_JOURNEY_SHELLY_ALLIANCE']:
    raw_flag(0x500 + ids[trainer], False)
native('VarSet', 0x409F, 3)
completion = flag_id('FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN')
raw_flag(completion, False)
assert native('JourneyCanStartArchieAlliance') == 1
assert native('JourneyPendingCampaignEvent', 0) == 6
party, scratch = s['gParties'], s['gStringVar4'] + 800
for i in range(6 * abi[2]):
    lib.write8(party + i, 0)
lib.write8(s['gPartiesCount'], 0)
species_list = [abi[68], 6, 9, 3, 25, 143]
for index, species in enumerate(species_list):
    assert native('ScriptGiveMon', species, 100, 0) == 0
    lib.write8(scratch, 5)
    native('SetMonData', party + index * abi[2], abi[96], scratch)
    lib.write8(scratch, 2 if index == 0 else 0)
    native('SetMonData', party + index * abi[2], abi[65], scratch)
    for slot in range(4):
        native('ScriptSetMonMoveSlot', index, abi[104] if slot == 0 else 0, slot)  # Dark Pulse, legal for Greninja.
identities = [dict(personality=native('GetMonData2', party + i * abi[2], abi[105]),
                   trainer_id=native('GetMonData2', party + i * abi[2], abi[106])) for i in range(6)]
warp('RustboroCity', 27, 20)
native('SetPlayerAvatarTransitionFlags', 1)
step(30)
assert native('JourneyCurrentGymGate') == 6
for _ in range(40):
    step(4, 64)
assert location() == map_id('RustboroCity'), 'Final gym accessible before Archie'
for _ in range(80):
    press(2)
warp('SeafloorCavern_Room9', 17, 43)
native('SetPlayerAvatarTransitionFlags', 1)
step(30)
script(b'\x05' + struct.pack('<I', s['SeafloorCavern_Room9_EventScript_ArchieAwakenKyogre']), 30)
def handlers(name):
    return {int(a, 16) for a, kind, n in re.findall(r'^(\w+) (\w) (\S+)$', raw, re.M) if n == name}
actions, moves = handlers('HandleInputChooseAction'), handlers('HandleInputChooseMove')
targets = set().union(*(handlers(name) for name in ['HandleInputChooseTarget', 'HandleInputShowTargets', 'HandleInputShowEntireFieldTargets']))
started = False
ash_seen = False
partner_seen = False
attacks = 0
for tick in range(2400):
    callback = lib.read32(s['gMain'] + 4) & ~1
    if callback == s['BattleMainCB2']:
        started = True
        flags = lib.read32(s['gBattleTypeFlags'])
        assert flags & 0x8000 and flags & 0x40
        assert lib.read8(s['gBattlersCount']) == 4
        assert lib.read16(s['gPartnerTrainerId']) == abi[15]
        assert lib.read16(s['gTrainerBattleParameter'] + abi[13]) == ids['TRAINER_JOURNEY_ARCHIE_ALLIANCE']
        # The packed second-opponent field is not halfword aligned.
        opponent_b = s['gTrainerBattleParameter'] + abi[14]
        assert lib.read8(opponent_b) | (lib.read8(opponent_b + 1) << 8) == ids['TRAINER_JOURNEY_SHELLY_ALLIANCE']
        partner_seen |= lib.read16(s['gBattleMons'] + 2 * abi[74] + abi[75]) != 0
        form = lib.read16(s['gBattleMons'] + abi[75])
        ash_seen |= form == abi[69]
        controller = lib.read32(s['gBattlerControllerFuncs']) & ~1
        if controller in actions:
            if form == abi[69] and attacks < 3:
                picture('Giovanni-Archie-Shelly-ash-battle')
            step(3, 64); step(12); step(3, 32); step(12); press(1)
        elif controller in moves:
            assert lib.read8(s['gMoveSelectionCursor']) == 0
            press(1)
            attacks += 1
        elif controller in targets:
            press(1)
        else:
            press(2)
    elif started and callback == s['CB2_Overworld']:
        break
    else:
        press(1)
if not started or callback != s['CB2_Overworld']:
    picture('archie-incomplete')
    print('Incomplete:', tick, hex(callback), attacks, ash_seen, flush=True)
assert started and callback == s['CB2_Overworld'] and attacks > 0
assert ash_seen and partner_seen
# The original orb scene, Maxie arrival and Route 128 warp must complete naturally.
for tick in range(1400):
    press(1)
    if location() == map_id('Route128'):
        break
else:
    picture('archie-aftermath-incomplete')
    raise AssertionError('Victory did not finish the original Kyogre scene and Route128 arrival')
for _ in range(30):
    press(1)
assert native('FlagGet', completion)
assert native('JourneyPendingCampaignEvent', 0) == 14
assert native('JourneyGymBadgeCount', 0) == 7 and native('JourneyGymBadgeCount', 1) == 6
# Special multi battles use the quest's completion flag, rather than the
# regular trainerbattle callback that sets individual trainer flags.
assert lib.read8(s['gPartiesCount']) == 6
for i, species in enumerate(species_list):
    assert native('GetMonData2', party + i * abi[2], abi[7]) == species
    assert native('GetMonData2', party + i * abi[2], abi[65]) == (2 if i == 0 else 0)
    assert native('GetMonData2', party + i * abi[2], abi[105]) == identities[i]['personality']
    assert native('GetMonData2', party + i * abi[2], abi[106]) == identities[i]['trainer_id']
picture('Route128-after-Archie-victory')
def peek_var(var):
    return lib.read16(save() + abi[108] + 2 * (var - 0x4000))
def field_idle():
    return (lib.read32(s['gMain'] + 4) & ~1 == s['CB2_Overworld']
            and lib.read8(s['sGlobalScriptContextStatus']) == 2
            and not lib.read8(s['sLockFieldControls']))
# Exercise the new guide and actual locked door during the climate mission.
warp('RustboroCity', 27, 20)
native('SetPlayerAvatarTransitionFlags', 1)
step(30)
assert native('JourneyCurrentGymGate') == 14
for _ in range(40):
    step(4, 64)
assert location() == map_id('RustboroCity')
assert lib.read16(s['gSpecialVar_Result']) == 14
step(160)  # Finish printing this page before recording the screenshot.
picture('Climate-mission-gym-guide')
for _ in range(100):
    press(1)
    if field_idle():
        break
else:
    raise AssertionError('Climate guide did not release field controls')
# Let the city's original legendary clash run before travelling to the summit.
warp('SootopolisCity', 43, 32)
for _ in range(800):
    press(1)
    if peek_var(abi[109]) == 2 and field_idle():
        break
else:
    raise AssertionError('Original Sootopolis clash did not finish')
assert native('JourneyPendingCampaignEvent', 0) == 14
# Verify the starting residence's actual door remains usable during the crisis.
city = json.loads((source / 'data/maps/SootopolisCity/map.json').read_text())
door = next(w for w in city['warp_events'] if w['dest_map'] == 'MAP_SOOTOPOLIS_CITY_HOUSE1')
warp('SootopolisCity', door['x'], door['y'] + 1)
native('SetPlayerAvatarTransitionFlags', 1)
step(30)
for _ in range(200):
    step(4, 64)
    if location() == map_id('SootopolisCity_House1'):
        break
else:
    picture('family-door-incomplete')
    raise AssertionError('Starting family home closed during the crisis')
step(200)
picture('Family-house-during-climate-crisis')
warp('SkyPillar_Top', 10, 15)
script(b'\x05' + struct.pack('<I', s['SkyPillar_Top_EventScript_AwakenRayquaza']), 30)
for _ in range(600):
    press(1)
    if peek_var(abi[110]) == 1 and field_idle():
        break
else:
    raise AssertionError('Native Rayquaza awakening did not finish')
step(200)
assert native('JourneyPendingCampaignEvent', 0) == 14, 'Awakening alone skipped the return scene'
warp('SootopolisCity', 43, 32)
for _ in range(1000):
    press(1)
    if peek_var(abi[110]) == 3 and field_idle():
        break
else:
    picture('rayquaza-scene-incomplete')
    raise AssertionError('Native Rayquaza peace scene did not finish')
step(200)
assert native('JourneyPendingCampaignEvent', 0) == 0
picture('Sootopolis-after-Rayquaza-peace')
# The originally first gym is now last, without changing the badge fixture.
warp('RustboroCity', 27, 20)
native('SetPlayerAvatarTransitionFlags', 1)
step(30)
assert native('JourneyCurrentGymGate') == 0
for _ in range(200):
    step(4, 64)
    if location() == map_id('RustboroCity_Gym'):
        break
else:
    picture('eighth-gym-incomplete')
    raise AssertionError('Actual gym door remained blocked after the peace scene')
step(200)
picture('Eighth-gym-after-Rayquaza-peace')
assert native('TrySavingData', 0, max_frames=6000) == 1
raw_flag(completion, False)
raw_flag(flag_id('FLAG_SYS_WEATHER_CTRL'), True)
assert native('LoadGameSave', 0) == 1
step(30)
assert native('FlagGet', completion) and native('JourneyPendingCampaignEvent', 0) == 0
lib.stop()
result = dict(passed=True, rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
              real_giovanni_archie_shelly_battle=True, native_victory=True, player_attacks=attacks,
              ash_after_ko=True, ai_partner_present=True, original_kyogre_scene_completed=True,
              actual_route128_arrival=True, canonical_quest_completion_flag=True,
              eighth_hoenn_gym_gate_cleared=True, physical_gym_blocked_before_victory=True,
              physical_gym_open_after_victory=True, physical_gym_blocked_during_climate_crisis=True,
              native_guide_weather_mission=True, six_owned_pokemon_restored=True,
              owned_personalities_and_trainer_ids_preserved=True,
              hidden_slot_preserved=True, regional_badges_unchanged=True,
              native_save_preserves_completion=True, original_rayquaza_awakening=True,
              original_rayquaza_peace_scene=True, awakening_alone_keeps_gym_gate=True,
              family_house_accessible_during_crisis=True,
 prerequisites_are_initial_state_fixtures=True,
              full_campaign_playthrough=False)
(args.output / 'archie-aftermath.json').write_text(json.dumps(result, indent=2) + '\n')
print(result, flush=True)
