"""Exercise regional league doors, early National Dex and champion flag isolation.

Badges and previous champion states are fixtures, not full Elite Four victories.
Door transitions, scripts and flash save/reload run in the compiled game.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', required=True, type=Path)
parser.add_argument('--library', required=True, type=Path)
parser.add_argument('--output', required=True, type=Path)
parser.add_argument('--baseline', action='store_true')
run_options = parser.parse_args()
sys.argv = [sys.argv[0], '--source', str(run_options.source), '--library', str(run_options.library),
            '--output', str(run_options.output)]
bootstrap = (ROOT / 'tools/hoenn/validate_abilities.py').read_text().split('\nability_field,')[0]
exec(compile(bootstrap, str(ROOT / 'tools/hoenn/validate_abilities.py'), 'exec'))


def raw_flag(flag, enabled):
    address = save() + 4720 + flag // 8
    value, mask = lib.read8(address), 1 << (flag & 7)
    lib.write8(address, value | mask if enabled else value & ~mask)


def bank(flags, mask):
    for i, flag in enumerate(flags):
        raw_flag(flag, bool(mask & (1 << i)))


def finish_dialogue():
    for _ in range(150):
        if not lib.read8(s['sLockFieldControls']) and lib.read8(s['sGlobalScriptContextStatus']) == 2:
            return
        press(1)
    picture('league-dialogue-incomplete')
    raise AssertionError(('Dialogue did not finish', location(), position()))


def walk_north(target, frames=200):
    for _ in range(frames // 4):
        step(4, 64)
        if location() == map_id(target):
            step(1000)
            finish_dialogue()
            return True
    return False


def routine(name):
    script(b'\x04' + struct.pack('<I', s[name]) + b'\x6b\x02', 10)


kanto = list(range(0x1AB0, 0x1AB8))
hoenn = [lib.read16(s['gBadgeFlags'] + i * 2) for i in range(8)]
champion = abi[111] - 0x2A + 0x1F
game_clear = abi[111] - 0x2A + 4
raw_flag(champion, False)
raw_flag(0x1AC2, False)
raw_flag(game_clear, False)
raw_flag(0x1AB8, False)
native('EnableNationalPokedex')
assert native('IsNationalPokedexEnabled')
bank(kanto, 255); bank(hoenn, 0)
warp('IndigoPlateau_PokemonCenter_1F_Frlg', 4, 4)
native('SetPlayerAvatarTransitionFlags', 1); step(30)
entered = walk_north('PokemonLeague_LoreleisRoom_Frlg')
picture('Kanto-eight-badges-blocked-baseline' if run_options.baseline else 'Kanto-eight-badges-national-dex')
if run_options.baseline:
    assert not entered and position() == (4, 3), 'Expected National Dex regression absent'
    warp('Route101', 10, 10)
    native('FlagSet', champion)
    warp('Route1_Frlg', 5, 12)
    leak = bool(native('FlagGet', champion))
    assert leak, 'Expected champion flag regression absent'
    result = dict(passed=True, baseline_regressions_reproduced=True,
                  eight_kanto_badges_blocked_with_national_dex=True, hoenn_champion_leaks_into_kanto=leak)
else:
    assert entered, 'All Kanto badges blocked by early National Dex'
    physical = [dict(region='Kanto', own_mask=255, other_mask=0, entered=True)]
    warp('Route1_Frlg', 5, 12)
    decisions = 0
    for mask in range(256):
        bank(kanto, mask); bank(hoenn, mask ^ 255)
        routine('IndigoPlateau_Journey_CheckBadges')
        assert lib.read16(s['gSpecialVar_Result']) == int(mask == 255), mask
        decisions += 1
    for mask in [0] + [255 ^ (1 << i) for i in range(8)]:
        bank(kanto, mask); bank(hoenn, 255)
        warp('IndigoPlateau_PokemonCenter_1F_Frlg', 4, 4)
        native('SetPlayerAvatarTransitionFlags', 1); step(30)
        assert not walk_north('PokemonLeague_LoreleisRoom_Frlg')
        assert position() == (4, 3), (mask, position())
        press(1); finish_dialogue()
        physical.append(dict(region='Kanto', own_mask=mask, other_mask=255, entered=False))
    print('Kanto: 256 subsets and ten physical entry cases passed', flush=True)
    for mask in [0] + [255 ^ (1 << i) for i in range(8)] + [255]:
        bank(kanto, 255 if mask != 255 else 0); bank(hoenn, mask)
        warp('EverGrandeCity_PokemonLeague_1F', 9, 4)
        native('SetPlayerAvatarTransitionFlags', 1); step(30)
        assert not walk_north('EverGrandeCity_Hall5', 40)
        press(1); finish_dialogue()
        entered = walk_north('EverGrandeCity_Hall5')
        assert entered == (mask == 255), (mask, entered, position())
        picture('Hoenn-eight-badges' if entered else 'Hoenn-missing-badge')
        physical.append(dict(region='Hoenn', own_mask=mask, other_mask=255 if mask != 255 else 0, entered=entered))
    print('Hoenn: ten physical guard cases passed', flush=True)
    # Execute the two original completion routines with no champion battle injected.
    warp('Route101', 10, 10)
    native('FlagClear', champion)
    native('FlagClear', game_clear)
    warp('Route1_Frlg', 5, 12)
    native('FlagClear', champion)
    native('FlagClear', game_clear)
    routine('EventScript_SetDefeatedEliteFourFlagsVars')
    finish_dialogue()
    assert native('FlagGet', champion) and not native('FlagGet', game_clear)
    warp('Route101', 10, 10)
    assert not native('FlagGet', champion) and not native('FlagGet', game_clear)
    routine('EverGrandeCity_HallOfFame_EventScript_SetGameClearFlags')
    finish_dialogue()
    assert native('FlagGet', champion) and not native('FlagGet', game_clear)
    # Ordinary game-clear operations remain independently banked too.
    native('FlagSet', game_clear)
    warp('Route1_Frlg', 5, 12)
    assert native('FlagGet', champion) and not native('FlagGet', game_clear)
    native('FlagSet', game_clear)
    assert native('TrySavingData', 0, max_frames=6000) == 1
    for flag in (champion, game_clear, 0x1AC2, 0x1AB8):
        raw_flag(flag, False)
    assert native('LoadGameSave', 0) == 1
    step(30)
    assert native('FlagGet', champion) and native('FlagGet', game_clear)
    warp('Route101', 10, 10)
    assert native('FlagGet', champion) and native('FlagGet', game_clear)
    native('FlagClear', champion)
    warp('Route1_Frlg', 5, 12)
    assert native('FlagGet', champion)
    result = dict(passed=True, kanto_badge_subsets=decisions, physical_entry_cases=physical,
                  early_national_dex_does_not_block_first_league=True,
                  other_region_badges_cannot_open_league=True, completion_scripts_executed=True,
                  champion_flags_independent=True, game_clear_flags_independent=True,
                  native_flash_save_reload=True)
result.update(rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
              states_are_fixtures=True, full_elite_four_victory=False, full_campaign_playthrough=False)
lib.stop()
(args.output / ('league-baseline.json' if run_options.baseline else 'league-access.json')).write_text(json.dumps(result,indent=2) + '\n')
print(result, flush=True)
