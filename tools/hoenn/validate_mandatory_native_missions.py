"""Native story gates, physical gym/League guards and Devon trigger.

Completion bits, badges, warps and postbattle entry are initial-state fixtures.
This verifies requirements, not wins in every original quest or a full campaign.
"""
from pathlib import Path
import hashlib
import json
import struct
ROOT = Path(__file__).resolve().parents[2]
exec(compile((ROOT / 'tools/hoenn/validate_campaign_matrix.py').read_text().split('\nchecks = []')[0],
             str(ROOT / 'tools/hoenn/validate_campaign_matrix.py'), 'exec'))

def complete():
    reset_aqua(); reset_native()
    for f in completion: raw_flag(flag_id(f), True)
    raw_flag(flag_id('FLAG_SYS_WEATHER_CTRL'), False)
    native('VarSet', 0x409F, 3)
    for t in stories['trainers']: raw_flag(0x500 + t['id'], True)

def finish():
    for _ in range(300):
        if not lib.read8(s['sLockFieldControls']): return
        step(1, 1); step(35)
    raise AssertionError(('Stuck dialogue', location(), position()))

def event(label, talked=1):
    lib.write16(s['gSpecialVar_LastTalked'], talked)
    script(b'\x05' + struct.pack('<I', s[label]), 30)

def missing(q):
    if q['trainers']: raw_flag(0x500 + quest_ids[q['trainers'][0]], False)
    elif q['flags']: raw_flag(quest_ids[q['flags'][0]], False)
    else: native('VarSet', quest_ids[q['variables'][0][0]], 0)

def permission(kanto):
    native('JourneyKantoLeaguePermission' if kanto else 'JourneyHoennLeaguePermission')
    return lib.read16(s['gSpecialVar_Result'])

def set_badges(kanto, count):
    bank(kanto_badges if kanto else hoenn_badges, (1 << count) - 1)

def letter_visit(label):
    raw_flag(flag_id('FLAG_HIDE_GRANITE_CAVE_STEVEN'), False)
    warp('GraniteCave_StevensRoom', 7, 9)
    step(8, 64); step(30); step(1, 1); step(200)
    picture(label); finish()

if not native_quests:
    complete(); set_badges(True, 8); set_badges(False, 8)
    raw_flag(flag_id('FLAG_DELIVERED_STEVEN_LETTER'), False)
    assert not native('CheckBagHasItem', 732, 1)
    letter_visit('baseline-steven-without-letter')
    assert native('FlagGet', flag_id('FLAG_DELIVERED_STEVEN_LETTER'))
    raw_flag(flag_id('FLAG_RESCUED_MR_FUJI'), False)
    assert native('JourneyPendingCampaignEvent', 1) == 0
    warp('IndigoPlateau_PokemonCenter_1F_Frlg', 4, 3)
    step(80, 64); step(150)
    assert location() != map_id('IndigoPlateau_PokemonCenter_1F_Frlg'), ('Expected missing-Fuji baseline bypass', location(), position())
    picture('baseline-league-without-fuji')
    lib.stop()
    (args.output / 'baseline.json').write_text(json.dumps(dict(expected_bypass_reproduced=True,
        rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
        fuji_rescue_missing=True, pending_event=0, physical_league_entry_allowed=True,
        steven_accepts_missing_letter=True,
        completion_and_badges_are_fixtures=True), indent=2) + '\n')
    raise SystemExit(0)

complete()
raw_flag(quest_ids['FLAG_DELIVERED_STEVEN_LETTER'], False)
assert not native('CheckBagHasItem', 732, 1)
letter_visit('steven-letter-missing')
assert not native('FlagGet', quest_ids['FLAG_DELIVERED_STEVEN_LETTER'])
assert native('AddBagItem', 732, 1)
letter_visit('steven-letter-delivered')
assert native('FlagGet', quest_ids['FLAG_DELIVERED_STEVEN_LETTER'])
assert not native('CheckBagHasItem', 732, 1)

doors, league_cases = [], []
assert native('ScriptGiveMon', 7, 40, 0) == 0
gym_cities = json.loads((source / '.journey-campaign-gates').read_text())['cities']
for q in native_quests:
    complete(); set_badges(q['kanto'], q['badges']); set_badges(not q['kanto'], 8); missing(q)
    name = 'CinnabarIsland_Frlg' if q['kanto'] else 'FortreeCity'
    city_data = next(c for c in gym_cities if c['map'] == name)
    x, y = city_data['door']['x'], city_data['door']['y']
    warp(name, x, y + 1)
    assert native('JourneyCurrentGymGate') == q['event']
    for _ in range(160): step(1, 64)
    assert location() == map_id(name)
    picture(q['key'] + '-gym-blocked'); finish()
    reset_native()
    assert native('JourneyCurrentGymGate') == 0
    for _ in range(160):
        step(1, 64)
        if location() != map_id(name): break
    assert location() != map_id(name)
    step(180)
    doors.append(dict(quest=q['key'], event=q['event'], physical_block=True, opens_after_completion=True))

    # Eight own-region badges do not excuse an unfinished mission, even with
    # the other region fully completed and the old Elite Four entry flag set.
    complete(); set_badges(True, 8); set_badges(False, 8); missing(q)
    name = 'IndigoPlateau_PokemonCenter_1F_Frlg' if q['kanto'] else 'EverGrandeCity_PokemonLeague_1F'
    native('FlagSet', flag_id('FLAG_ENTERED_ELITE_FOUR'))
    warp(name, 4 if q['kanto'] else 9, 3)
    assert permission(q['kanto']) == 0
    step(40, 64)
    assert location() == map_id(name) and position()[1] >= 3
    step(1, 1); step(200)
    picture(q['key'] + '-league-guide'); finish()
    assert native('JourneyPendingCampaignEvent', int(q['kanto'])) == q['event']
    assert native('TrySavingData', 0, max_frames=6000) == 1
    reset_native()
    assert native('LoadGameSave', 0) == 1
    step(30)
    assert permission(q['kanto']) == 0
    reset_native()
    assert permission(q['kanto']) == 1
    league_cases.append(dict(quest=q['key'], own_badges=8, other_badges=8,
        physical_guard=True, old_elite_entry_flag_cannot_bypass=True, native_save_roundtrip=True,
        opens_after_completion=True))

complete()
for kanto in [False, True]:
    for mask in range(256):
        bank(kanto_badges if kanto else hoenn_badges, mask)
        bank(hoenn_badges if kanto else kanto_badges, mask ^ 255)
        assert permission(kanto) == int(mask == 255)

# Any first Hoenn badge enables the original Rustboro theft once Woods ends.
# It must not synthesize a win, package recovery or letter delivery.
devon = []
for bit in range(8):
    complete(); bank(hoenn_badges, 1 << bit)
    vars_text = (source / 'include/constants/vars.h').read_text()
    rustboro = int(re.search(r'^#define\s+VAR_RUSTBORO_CITY_STATE\s+(0x[0-9A-Fa-f]+)', vars_text, re.M)[1], 16)
    native('VarSet', rustboro, 0)
    raw_flag(quest_ids['FLAG_RECOVERED_DEVON_GOODS'], False)
    raw_flag(0x500 + quest_ids['TRAINER_GRUNT_RUSTURF_TUNNEL'], False)
    warp('RustboroCity', 12, 12)
    assert native('VarGet', rustboro) == 1
    assert not native('FlagGet', quest_ids['FLAG_RECOVERED_DEVON_GOODS'])
    for state in [4, 7]:
        native('VarSet', rustboro, state)
        native('JourneyUpdateGymGate')
        assert native('VarGet', rustboro) == state
    devon.append(dict(first_badge=bit + 1, theft_started=True, no_synthetic_recovery=True, late_revisit_keeps_state=True))

# Run Roxanne's real postbattle script with already completed Devon states.
complete(); set_badges(False, 8)
warp('RustboroCity_Gym', 5, 12)
roxanne_cases = []
for state in [4, 7]:
    native('VarSet', rustboro, state)
    event('RustboroCity_Gym_EventScript_RoxanneDefeated'); finish()
    assert native('VarGet', rustboro) == state
    roxanne_cases.append(state)
lib.stop()
(args.output / 'mandatory-missions.json').write_text(json.dumps(dict(passed=True,
    rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
    gym_doors=doors, league_guards=league_cases, league_badge_subset_cases=512,
    devon_first_badge_cases=devon, roxanne_postbattle_preserved_states=roxanne_cases,
    actual_steven_interaction_requires_and_consumes_letter=True,
    completion_badges_travel_and_postbattle_entries_are_fixtures=True,
    original_quest_battles_played=False, full_campaign_playthrough=False), indent=2) + '\n')
print('Native mandatory mission doors, League guards and Devon trigger passed.', flush=True)
