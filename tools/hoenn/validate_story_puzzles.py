"""Read inscriptions and physically cross three native puzzle doors without moves.

Travel warps and capture-gate badge combinations are fixtures. Door activation,
walking, save/Continue and the below-sixteen-badges refusal use native events.
"""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import tempfile
ROOT = Path(__file__).resolve().parents[2]
exec(compile((ROOT / 'tools/hoenn/validate_abilities.py').read_text().split('\nability_field,')[0],
             str(ROOT / 'tools/hoenn/validate_abilities.py'), 'exec'))
fixed = (source / '.journey-story-puzzles').exists()
with tempfile.TemporaryDirectory(prefix='story-puzzle-abi-', dir='/tmp') as directory:
    out = Path(directory) / 'abi.s'
    subprocess.run([str(ROOT / '.local/arm-gcc/usr/bin/arm-none-eabi-gcc'), '-S',
                    '-iquote', str(source / 'include'), '-DMODERN=1', '-DPOKEEMERALD',
                    '-mthumb', '-march=armv4t', '-mabi=apcs-gnu',
                    str(ROOT / 'tools/hoenn/fixture_story_puzzles_abi.c'), '-o', str(out)],
                   check=True, capture_output=True)
    table = out.read_text().split('gStoryPuzzleABI:', 1)[1].split('.size', 1)[0]
    puzzle_abi = [int(n) for n in re.findall(r'\.word\s+(\d+)', table)]
assert len(puzzle_abi) == 8
flag_ids = dict(zip(['FLAG_SYS_REGIROCK_PUZZLE_COMPLETED', 'FLAG_SYS_REGISTEEL_PUZZLE_COMPLETED',
                     'FLAG_SYS_BRAILLE_DIG', 'FLAG_REGI_DOORS_OPENED'], puzzle_abi[4:]))
def flag_id(name): return flag_ids[name]
def flag(f): return bool(lib.read8(save() + 4720 + f // 8) & (1 << (f & 7)))
def rawflag(f, enabled):
    address = save() + 4720 + f // 8
    value, mask = lib.read8(address), 1 << (f & 7)
    lib.write8(address, value | mask if enabled else value & ~mask)
def idle():
    return (lib.read32(s['gMain'] + 4) & ~1) == s['CB2_Overworld'] and not lib.read8(s['sLockFieldControls'])
def finish():
    for _ in range(160):
        assert (lib.read32(s['gMain'] + 4) & ~1) != s['BattleMainCB2']
        if idle(): return
        press(1)
    picture('puzzle-dialogue-failure')
    raise AssertionError(('Puzzle dialogue stuck', location(), position()))
def walk_into(target, start):
    for _ in range(140):
        step(1, 64)
        if location() != map_id(start) or (start != 'SealedChamber_OuterRoom' and position()[1] < 15): break
    step(100)
    if start == 'SealedChamber_OuterRoom':
        return location() == map_id(target)
    return location() == map_id(start) and position()[1] < 15

# A move-less owned Pokemon; no badge, HM, key item or puzzle completion added.
assert native('ScriptGiveMon', 7, 5, 0) == 0
for slot in range(4): native('ScriptSetMonMoveSlot', 0, 0, slot)
assert all(native('GetMonData2', s['gParties'], field) == 0 for field in puzzle_abi[:4])
kanto = list(range(0x1AB0, 0x1AB8))
hoenn = [lib.read16(s['gBadgeFlags'] + i * 2) for i in range(8)]
assert not any(flag(f) for f in kanto + hoenn)
before = [flag(f) for f in kanto + hoenn]
cases = [('DesertRuins', 'FLAG_SYS_REGIROCK_PUZZLE_COMPLETED', 8, 21, 'DesertRuins'),
         ('AncientTomb', 'FLAG_SYS_REGISTEEL_PUZZLE_COMPLETED', 8, 21, 'AncientTomb'),
         ('SealedChamber_OuterRoom', 'FLAG_SYS_BRAILLE_DIG', 10, 3, 'SealedChamber_InnerRoom')]
checks = []
for name, flag_name, x, y, target in cases:
    f = flag_id(flag_name)
    assert not flag(f)
    warp(name, x, y)
    step(4, 64); step(30); press(1); step(40)
    picture(name + '-inscription')
    finish()
    assert flag(f) == fixed
    crossed = walk_into(target, name)
    assert crossed == fixed, (name, crossed, location(), position())
    picture(name + ('-door-crossed' if fixed else '-door-blocked'))
    assert [flag(f) for f in kanto + hoenn] == before
    checks.append(dict(map=name, completion_flag=flag_name, opened_by_inscription=flag(f),
                       physical_crossing=crossed, no_moves_or_badges=True))
    if fixed:
        assert native('TrySavingData', 0, max_frames=6000) == 1
        assert native('LoadGameSave', 0, max_frames=6000) == 1
        lib.write32(s['gMain'] + 4, s['CB2_ContinueSavedGame'] | 1)
        step(1500); finish()
        assert flag(f)
        warp(name, x, y)
        assert walk_into(target, name)
        checks[-1]['native_save_reload_continue_and_recross'] = True
    print('Puzzle door checked:', name, fixed, flush=True)
guards = []
if fixed:
    # Opening the stone passage never awards capture permission or opens the
    # three external Regi sites; the original inner-room party riddle remains.
    assert not flag(flag_id('FLAG_REGI_DOORS_OPENED'))
    for own_kanto, own_hoenn in [(0, 0), (8, 0), (0, 8), (8, 8)]:
        for i, f in enumerate(kanto): rawflag(f, i < own_kanto)
        for i, f in enumerate(hoenn): rawflag(f, i < own_hoenn)
        assert native('JourneySpecialUnlocked') == int(own_kanto == own_hoenn == 8)
        guards.append(dict(kanto_badges=own_kanto, hoenn_badges=own_hoenn,
                           capture_permission=own_kanto == own_hoenn == 8))
    for f in kanto + hoenn: rawflag(f, False)
    for name in ['DesertRuins', 'AncientTomb']:
        warp(name, 8, 8)
        step(4, 64); step(30); press(1)
        for _ in range(100):
            assert (lib.read32(s['gMain'] + 4) & ~1) != s['BattleMainCB2']
            press(1)
        finish()
        picture(name + '-legendary-refused-before-sixteen')
    assert not flag(flag_id('FLAG_REGI_DOORS_OPENED'))
    assert [flag(f) for f in kanto + hoenn] == before
lib.stop()
result = dict(passed=True, rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
              overlay_installed=fixed, doors=checks, capture_guard_combinations=guards,
              original_inner_party_riddle_not_awarded=True, badges_not_awarded=True,
              travel_and_capture_badge_combinations_are_fixtures=True,
              full_campaign_playthrough=False)
(args.output / 'story-puzzles.json').write_text(json.dumps(result, indent=2) + '\n')
