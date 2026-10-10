"""Native sixteen-badge permissions, League dialogue and physical entrances.
Badge/story states, party and travel are fixtures; no complete campaign is claimed.
"""
from pathlib import Path
import hashlib
import json
ROOT = Path(__file__).resolve().parents[2]
exec(compile((ROOT / 'tools/hoenn/validate_campaign_matrix.py').read_text().split('\nchecks = []')[0],
             str(ROOT / 'tools/hoenn/validate_campaign_matrix.py'), 'exec'))
assert native('ScriptGiveMon', 7, 40, 0) == 0

def complete():
    reset_aqua(); reset_native()
    for f in completion: raw_flag(flag_id(f), True)
    raw_flag(flag_id('FLAG_SYS_WEATHER_CTRL'), False)
    native('VarSet', 0x409F, 3)
    for t in stories['trainers']: raw_flag(0x500 + t['id'], True)

def permission(kanto):
    native('JourneyKantoLeaguePermission' if kanto else 'JourneyHoennLeaguePermission')
    return lib.read16(s['gSpecialVar_Result'])

def finish():
    for _ in range(300):
        if not lib.read8(s['sLockFieldControls']): return
        step(1, 1); step(35)
    raise AssertionError(('Stuck League dialogue', location(), position()))

complete()
if not (source / '.journey-sixteen-badge-leagues').exists():
    baseline = []
    for kanto_count, hoenn_count in [(8, 0), (0, 8), (8, 7), (7, 8)]:
        bank(kanto_badges, (1 << kanto_count) - 1)
        bank(hoenn_badges, (1 << hoenn_count) - 1)
        observed = [permission(True), permission(False)]
        assert observed == [int(kanto_count == 8), int(hoenn_count == 8)]
        baseline.append(dict(kanto=kanto_count, hoenn=hoenn_count, allowed=observed))
    lib.stop()
    (args.output / 'baseline.json').write_text(json.dumps(dict(expected_old_rule_reproduced=True,
        rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
        cases=baseline, story_completions_and_badges_are_fixtures=True), indent=2) + '\n')
    raise SystemExit(0)
cases = 0
for own_kanto in [True, False]:
    for other in [0, 255]:
        for mask in range(256):
            bank(kanto_badges if own_kanto else hoenn_badges, mask)
            bank(hoenn_badges if own_kanto else kanto_badges, other)
            for league in [True, False]:
                assert permission(league) == int(mask == other == 255), (own_kanto, mask, other, league)
                cases += 1

# All sixteen badges are the League rule. Story checkpoints stay in gyms.
bank(kanto_badges, 255); bank(hoenn_badges, 255)
raw_flag(flag_id('FLAG_RESCUED_MR_FUJI'), False)
assert native('JourneyPendingCampaignEvent', 1) == 19
assert permission(True) == permission(False) == 1
complete()

physical = []
for kanto in [True, False]:
    name = 'IndigoPlateau_PokemonCenter_1F_Frlg' if kanto else 'EverGrandeCity_PokemonLeague_1F'
    x = 4 if kanto else 9
    for own, other, entered in [(8, 0, False), (8, 7, False), (8, 7, True), (7, 8, True)]:
        bank(kanto_badges if kanto else hoenn_badges, (1 << own) - 1)
        bank(hoenn_badges if kanto else kanto_badges, (1 << other) - 1)
        raw_flag(flag_id('FLAG_ENTERED_ELITE_FOUR'), entered)
        # A pending story must not produce the gym-leader message at a League.
        raw_flag(flag_id('FLAG_RESCUED_MR_FUJI'), False)
        warp(name, x, 3)
        assert permission(kanto) == 0
        step(40, 64)
        assert location() == map_id(name) and position()[1] >= 3
        step(1, 1); step(240)
        if own == 8 and other == 7 and not entered:
            picture(('kanto' if kanto else 'hoenn') + '-league-sixteen-required')
            step(1, 1); step(240)
            picture(('kanto' if kanto else 'hoenn') + '-league-both-regions')
        finish()
        assert location() == map_id(name)
        assert native('TrySavingData', 0, max_frames=6000) == 1
        step(60)  # Finish the flash call before installing the next ARM fixture.
        bank(kanto_badges, 255); bank(hoenn_badges, 255)
        assert native('LoadGameSave', 0, max_frames=6000) == 1
        step(30)
        assert permission(kanto) == 0
        bank(kanto_badges, 255); bank(hoenn_badges, 255)
        assert permission(kanto) == 1
        reset_native()
        warp(name, x, 3)
        if not kanto and not entered:
            step(8, 64); step(20); step(1, 1); step(60); finish()
        for _ in range(240):
            step(1, 64)
            if location() != map_id(name): break
        assert location() != map_id(name), ('Sixteen badges did not open physical entrance', kanto, entered, location(), position())
        step(180)
        physical.append(dict(region='Kanto' if kanto else 'Hoenn', own_badges=own, other_badges=other,
            old_elite_entry_flag=entered, physical_denial=True, native_save_roundtrip=True,
            physical_entry_after_sixteen=True))
complete()
lib.stop()
(args.output / 'sixteen-badge-leagues.json').write_text(json.dumps(dict(passed=True,
    rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
    required_badges=dict(kanto=8, hoenn=8), permission_cases=cases, physical_cases=physical,
    gym_story_requirement_not_reused_as_league_dialogue=True,
    badges_are_only_league_permission=True, gym_story_requirement_is_preserved=True,
    initial_badges_story_party_and_warps_are_fixtures=True, full_campaign_playthrough=False), indent=2) + '\n')
print('Native sixteen-badge League permissions and physical entry passed.', flush=True)
