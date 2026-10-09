"""Native Dive and Continue for both genders from Kanto and Hoenn.
Origin/gender, travel and a Pokemon knowing Surf/Dive are fixtures.
Movement modes, Dive prompts and save/Continue are native.
"""
from pathlib import Path
import hashlib
import json
ROOT = Path(__file__).resolve().parents[2]
exec(compile((ROOT / 'tools/hoenn/validate_team_missions.py').read_text().split('\nwins, completed =')[0],
             str(ROOT / 'tools/hoenn/validate_team_missions.py'), 'exec'))
for f in kanto_flags + hoenn_flags: rawflag(f, False)
native('ScriptSetMonMoveSlot', 0, 291, 2)
rows = []
candidate = (source / '.journey-water-continue').exists()

def snapshot():
    return dict(map=list(location()), position=list(position()), mode=lib.read8(s['gPlayerAvatar']) & 25,
                region=lib.read8(lib.read32(s['gSaveBlock2Ptr']) + abi[45]),
                gender=lib.read8(lib.read32(s['gSaveBlock2Ptr']) + abi[32]),
                kanto_badges=native('JourneyGymBadgeCount', 1), hoenn_badges=native('JourneyGymBadgeCount', 0))

def check(label, mode):
    before = snapshot(); assert before['mode'] == mode, (label, before)
    assert native('TrySavingData', 0, max_frames=6000) == 1
    assert native('LoadGameSave', 0, max_frames=6000) == 1
    lib.write32(s['gMain'] + 4, s['CB2_ContinueSavedGame'] | 1)
    step(1500); finish()
    after = snapshot()
    assert before['map'] == after['map'] and before['position'] == after['position']
    assert before['region'] == after['region'] and before['gender'] == after['gender']
    assert after['kanto_badges'] == after['hoenn_badges'] == 0
    if candidate: assert before == after, (label, before, after)
    rows.append(dict(label=label, before=before, after=after, mode_preserved=before['mode'] == after['mode']))
    picture(label + '-after-continue')

for region_name, region in [('kanto', abi[46]), ('hoenn', abi[51])]:
    for gender in [0, 1]:
        save2 = lib.read32(s['gSaveBlock2Ptr'])
        lib.write8(save2 + abi[45], region); lib.write8(save2 + abi[32], gender)
        prefix = region_name + '-' + str(gender)
        warp('Route1_Frlg', 5, 12)
        native('SetPlayerAvatarTransitionFlags', 1); step(30)
        check(prefix + '-foot', 1)
        warp('Route128', 38, 27)
        native('SetPlayerAvatarTransitionFlags', 8); step(30)
        check(prefix + '-surf', 8)
        assert native('TrySetDiveWarp') == 2
        for _ in range(160):
            press(1)
            if location() == map_id('Underwater_Route128'): break
        step(120); finish()
        assert location() == map_id('Underwater_Route128')
        check(prefix + '-underwater', 16)
        # Baseline can resume Surf underwater; the real B prompt must still
        # be exercised rather than fixing its mode manually for the test.
        assert native('TrySetDiveWarp') == 1
        press(2)
        for _ in range(160):
            press(1)
            if location() == map_id('Route128'): break
        step(120); finish()
        assert location() == map_id('Route128')
        check(prefix + '-resurfaced', 8)
        print('Native water Continue cases:', prefix, flush=True)
lib.stop()
wrong = [r['label'] for r in rows if not r['mode_preserved']]
assert wrong == ([] if candidate else ['kanto-0-underwater', 'kanto-1-underwater']), wrong
result = dict(passed=True, rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
              candidate=candidate, rows=rows, wrong_mode_cases=wrong, native_dive_and_resurface=True,
              origins_genders_badges_travel_and_known_moves_are_fixtures=True,
              full_campaign_playthrough=False, balance_validated=False)
(args.output / 'water-continue.json').write_text(json.dumps(result, indent=2) + '\n')
print('Native water Continue matrix passed', flush=True)
