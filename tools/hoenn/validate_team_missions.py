"""Win the 28 added villain encounters and check regional mission progression.
Initial badges/prior episodes, travel and script entry are fixtures. Wins are
native battles with boosted player stats, not synthetic trainer flags.
"""
from pathlib import Path
import hashlib
import json
import re
import struct
ROOT = Path(__file__).resolve().parents[2]
exec(compile((ROOT / 'tools/hoenn/validate_pwt.py').read_text().split('\ndef enter(pool')[0], str(ROOT / 'tools/hoenn/validate_pwt.py'), 'exec'))
stories = json.loads((source / '.journey-team-stories').read_text())
trainers = {t['key']: t for t in stories['trainers']}
missions = stories['missions']
constants = (source / 'include/constants/flags.h').read_text()
def flag_id(name): return int(re.search(r'^#define\s+' + name + r'\s+(0x\w+)', constants, re.M)[1], 16)
def rawflag(flag, enabled):
    address = save() + 4720 + flag // 8
    value, mask = lib.read8(address), 1 << (flag & 7)
    lib.write8(address, value | mask if enabled else value & ~mask)
def flag(flag): return bool(lib.read8(save() + 4720 + flag // 8) & (1 << (flag & 7)))
kanto_flags = list(range(0x1AB0, 0x1AB8))
hoenn_flags = [lib.read16(s['gBadgeFlags'] + i * 2) for i in range(8)]
for own, chosen in [(kanto_flags, {0, 2, 4, 7}), (hoenn_flags, {1, 3, 4, 7})]:
    for i, f in enumerate(own): rawflag(f, i in chosen)
for name in ['FLAG_HIDE_CELADON_ROCKETS', 'FLAG_DEFEATED_EVIL_TEAM_MT_CHIMNEY']:
    rawflag(flag_id(name), True)
for name in ['FLAG_HIDE_SAFFRON_ROCKETS', 'FLAG_GROUDON_AWAKENED_MAGMA_HIDEOUT', 'FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN']:
    rawflag(flag_id(name), False)
rawflag(abi[111], False)
native('VarSet', 0x409F, 0)
for t in stories['trainers']: rawflag(0x500 + t['id'], False)
for i in range(6 * abi[2]): lib.write8(party + i, 0)
lib.write8(s['gPartiesCount'], 0)
for i, mon in enumerate([658, 149, 376]):
    assert native('ScriptGiveMon', mon, 100, 0) == 0
    for slot in range(4): native('ScriptSetMonMoveSlot', i, abi[142] if slot == 0 else abi[76] if slot == 1 else 0, slot)
scratch = s['gStringVar4'] + 800
lib.write8(scratch, 2); native('SetMonData', party, abi[65], scratch)
badges_before = [flag(f) for f in kanto_flags + hoenn_flags]

def pending(kanto): return native('JourneyPendingCampaignEvent', int(kanto))
def done(kanto): return native('JourneyRegionalMissionsComplete', int(kanto))
def finish(limit=240):
    for _ in range(limit):
        if idle(): return
        press(1)
    picture('mission-dialogue-failure')
    raise AssertionError(('Mission dialogue stuck', location(), position()))
def door_probe(city, blocked):
    c = next(c for c in json.loads((source / '.journey-campaign-gates').read_text())['cities'] if c['map'] == city)
    x, y = c['door']['x'], c['door']['y']
    warp(city, x, y + 1)
    assert native('JourneyCurrentGymGate') == (pending(c['kanto']) if blocked else 0)
    for _ in range(160):
        step(1, 64)
        if location() != map_id(city): break
    if blocked:
        assert location() == map_id(city)
        picture(city + '-mission-door-blocked')
        finish()
    else:
        target = next(json.loads(p.read_text())['name'] for p in (source / 'data/maps').glob('*/map.json') if json.loads(p.read_text())['id'] == c['door']['dest_map'])
        assert location() == map_id(target), (city, target, location())
        step(120)
        picture(city + '-mission-door-opened')
    return dict(city=city, blocked=blocked, physical_door=True)

assert pending(True) == 7 and pending(False) == 12
assert not done(True) and not done(False)
doors = [door_probe('CinnabarIsland_Frlg', True), door_probe('FortreeCity', True)]

def enter_trainer(t):
    native('HealPlayerParty')
    # The Rocket groups have overlapping sight lines. Starting beside one
    # would also queue a second trainer encounter before our script fixture.
    x, y = (12, 12) if t['mission'] == 'hoenn_rocket' else (t['x'] + 1, t['y'])
    warp(t['map'], x, y)
    data = json.loads((source / 'data/maps' / t['map'] / 'map.json').read_text())
    local_id = next(i + 1 for i, o in enumerate(data['object_events']) if o.get('script') == f"JourneyTeam_Trainer{t['id']}")
    lib.write16(s['gSpecialVar_LastTalked'], local_id)
    # Existing NPC script; travel/script entry, rather than interacting A, is
    # explicitly a fixture. Outcome and defeated trainer flags stay native.
    script(b'\x05' + struct.pack('<I', s[f"JourneyTeam_Trainer{t['id']}"]), 30)

def fight(t):
    targets = {int(a, 16) for a, _, n in re.findall(r'^(\w+) (\w) (\S+)$', raw, re.M)
               if n in ['HandleInputChooseTarget', 'HandleInputShowTargets', 'HandleInputShowEntireFieldTargets']}
    started = ash_seen = False
    double_battle = False
    second_trainer = None
    attacks = 0
    for tick in range(1800):
        cb = lib.read32(s['gMain'] + 4) & ~1
        if cb == s['BattleMainCB2']:
            started = True
            actual = lib.read16(s['gTrainerBattleParameter'] + abi[13])
            assert actual == t['id'], (t, actual)
            assert lib.read32(s['gBattleTypeFlags']) & abi[10]
            double_battle |= lib.read8(s['gBattlersCount']) == 4
            if lib.read32(s['gBattleTypeFlags']) & 0x8000:
                address = s['gTrainerBattleParameter'] + abi[14]
                second_trainer = lib.read8(address) | lib.read8(address + 1) << 8
            ash_seen |= lib.read16(s['gBattleMons'] + abi[75]) == abi[69]
            if t.get('fixture_clear_status'):
                for battler in ([0, 2] if double_battle else [0]):
                    lib.write32(s['gBattleMons'] + battler * abi[74] + abi[95], 0)
            lib.write16(s['gBattleMons'] + pabi[15], 16000)
            lib.write16(s['gBattleMons'] + pabi[16], 10000)
            lib.write16(s['gBattleMons'] + pabi[20], 30000)
            if lib.read16(s['gBattleMons'] + abi[102]): lib.write16(s['gBattleMons'] + abi[102], 30000)
            for i in range(3):
                lib.write16(party + i * abi[2] + pabi[8], 16000)
                lib.write16(party + i * abi[2] + pabi[9], 10000)
                lib.write16(party + i * abi[2] + pabi[21], 30000)
                if lib.read16(party + i * abi[2] + abi[101]): lib.write16(party + i * abi[2] + abi[101], 30000)
            controllers = {lib.read32(s['gBattlerControllerFuncs'] + 4 * i) & ~1 for i in range(4)}
            if controllers & targets:
                press(1)
            elif controllers & (actions | moves):
                step(1, 64); step(8); step(1, 32); step(8); press(1)
                attacks += bool(controllers & moves)
            else: press(2)
        elif started and cb == s['CB2_Overworld']:
            assert lib.read8(s['gBattleOutcome']) == 1
            finish()
            assert native('FlagGet', 0x500 + t['id']) == 1
            assert attacks > 0
            if second_trainer is not None:
                assert native('FlagGet', 0x500 + second_trainer) == 1
            return dict(trainer=t['id'], map=t['map'], mission=t['mission'], attacks=attacks, outcome=1, ash_seen=ash_seen, native_defeated_flag=True, double_battle=double_battle, second_trainer=second_trainer, second_native_defeated_flag=second_trainer is not None)
        else: press(1)
    picture('mission-battle-failure')
    raise AssertionError(('Mission battle incomplete', t, attacks, hex(cb)))

wins, completed = [], []
for index, m in enumerate(missions):
    assert pending(m['kanto']) == m['event']
    other_before = pending(not m['kanto'])
    for j, key in enumerate(m['trainers']):
        t = trainers[key]
        assert not flag(0x500 + t['id'])
        enter_trainer(t)
        win = fight(t)
        own_pending = pending(m['kanto'])
        expected = m['event'] if j + 1 < len(m['trainers']) else next((later['event'] for later in missions[index + 1:] if later['kanto'] == m['kanto']), 0)
        assert own_pending == expected, (m, j, expected, own_pending)
        assert pending(not m['kanto']) == other_before
        assert [flag(f) for f in kanto_flags + hoenn_flags] == badges_before
        assert native('GetMonData2', party, abi[7]) == 658
        assert native('GetMonData2', party, abi[65]) == 2
        win['next_pending_event'] = own_pending
        win['other_region_event_unchanged'] = True
        wins.append(win)
    picture(m['key'] + '-mission-complete')
    mission_flags = [flag(0x500 + t['id']) for t in stories['trainers']]
    assert native('TrySavingData', 0, max_frames=6000) == 1
    assert native('LoadGameSave', 0, max_frames=6000) == 1
    lib.write32(s['gMain'] + 4, s['CB2_ContinueSavedGame'] | 1)
    step(1500); finish()
    assert [flag(0x500 + t['id']) for t in stories['trainers']] == mission_flags
    assert pending(m['kanto']) == expected and pending(not m['kanto']) == other_before
    assert [flag(f) for f in kanto_flags + hoenn_flags] == badges_before
    completed.append(dict(mission=m['key'], region='kanto' if m['kanto'] else 'hoenn', wins=len(m['trainers']), next_event=expected, native_save_reload_continue=True))
    if index == 4:
        assert done(True) and not done(False)
        doors.append(door_probe('CinnabarIsland_Frlg', False))
        doors.append(door_probe('FortreeCity', True))
    print('Native mission completed:', m['key'], len(m['trainers']), flush=True)
assert done(True) and done(False)
doors.append(door_probe('FortreeCity', False))
# A defeated representative in each region must stay defeated after Continue.
revisits = []
for key in [missions[0]['trainers'][-1], missions[-1]['trainers'][-1]]:
    t = trainers[key]; enter_trainer(t)
    for _ in range(160):
        assert (lib.read32(s['gMain'] + 4) & ~1) != s['BattleMainCB2']
        if idle(): break
        press(1)
    else: raise AssertionError(('Defeated NPC revisit stuck', t))
    assert native('FlagGet', 0x500 + t['id']) == 1
    revisits.append(dict(trainer=t['id'], dialogue_only=True, no_new_battle=True))
assert [flag(f) for f in kanto_flags + hoenn_flags] == badges_before
assert len(wins) == 28
lib.stop()
result = dict(passed=True, rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
              wins=wins, missions=completed, doors=doors, defeated_npc_revisits=revisits,
              native_victories=28, kanto_victories=19, hoenn_victories=9,
              badges_unchanged=True, independent_regional_mission_tracking=True, hidden_and_battle_bond_retained=True,
              initial_badges_prior_events_travel_script_entry_and_battle_stats_are_fixtures=True,
              balance_validated=False, full_campaign_playthrough=False)
(args.output / 'team-missions.json').write_text(json.dumps(result, indent=2) + '\n')
print('Native connected missions and gym door progression passed', flush=True)
