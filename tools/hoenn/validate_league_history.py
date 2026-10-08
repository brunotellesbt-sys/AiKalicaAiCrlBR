"""Win both complete Leagues sequentially in one native save and read the archive.
Levels, badges and healing are fixtures; battles, Hall of Fame, credits, Continue
and flash reload run through the existing native League-completion validator.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--library', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--first-region', choices=['kanto', 'hoenn'], required=True)
parser.add_argument('--baseline', action='store_true')
configuration = parser.parse_args()
first_region = configuration.first_region
expect_baseline = configuration.baseline
sys.argv = [sys.argv[0], '--source', str(configuration.source), '--library', str(configuration.library),
            '--output', str(configuration.output), '--region', first_region]
program = (ROOT / 'tools/hoenn/validate_league_completion.py').read_text()
initialization, sequence = program.split("\nentry='IndigoPlateau", 1)
sequence = "entry='IndigoPlateau" + sequence
sequence = sequence.replace('lib.stop()', '')
sequence = sequence.replace('assert not any(raw_get(f) for f in other_flags)',
                            'assert all(raw_get(f) == second_league for f in other_flags)')
sequence = sequence.replace('and not any(raw_get(f) for f in other_flags)',
                            'and all(raw_get(f) == second_league for f in other_flags)')
sequence = sequence.replace('other_region_uncompleted=True', 'other_region_uncompleted=not second_league')
exec(compile(initialization, str(ROOT / 'tools/hoenn/validate_league_completion.py'), 'exec'))
# Unlock both regional doors without granting either championship.
for flag in range(0x1AB0, 0x1AB8): raw_flag(flag, True)
for i in range(8): raw_flag(lib.read16(s['gBadgeFlags'] + 2*i), True)
assert native('GetGameStat', 10) == 0


def archive():
    # The shared on-flash struct is 24 bytes per mon, six mons per team.
    pointer = native('AllocZeroed_', 8192, 0)
    assert pointer
    assert lib.read32(s['gHoFSaveBuffer']) == 0
    lib.write32(s['gHoFSaveBuffer'], pointer)
    try:
        assert native('LoadGameSave', 3, max_frames=6000) == 1
        records = []
        for index in range(50):
            start = pointer + index * 144
            if lib.read16(start + 8) >> 1 == 0: break
            records.append(bytes(lib.read8(start + i) for i in range(144)))
        return records
    finally:
        lib.write32(s['gHoFSaveBuffer'], 0)
        native('Free', pointer)


sequences, archives = [], []
for iteration, region in enumerate([first_region, 'hoenn' if first_region == 'kanto' else 'kanto']):
    second_league = iteration == 1
    run_options.region = region
    kanto = region == 'kanto'
    exec(compile(sequence, str(ROOT / 'tools/hoenn/validate_league_completion.py'), 'exec'))
    sequences.append(result.copy())
    records = archive()
    assert native('GetGameStat', 10) == iteration + 1
    expected = 1 if expect_baseline and second_league else iteration + 1
    assert len(records) == expected, (region, len(records), expected)
    if second_league and not expect_baseline:
        assert records[0] == previous[0], 'First championship archive changed'
    previous = records
    archives.append(dict(region=region, records=len(records),
                         records_sha256=[hashlib.sha256(r).hexdigest() for r in records]))
    print('Shared archive', archives[-1], flush=True)
lib.stop()
report = dict(passed=True, rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
              first_region=first_region, sequences=sequences, archives=archives,
              same_native_save=True, baseline_erases_first_record=expect_baseline,
              ten_native_battle_victories=True, both_champion_flags_persist=True,
              shared_archive_preserved=not expect_baseline, full_campaign_playthrough=False,
              levels_badges_and_healing_are_fixtures=True)
name = 'history-baseline' if expect_baseline else first_region+'-first-history'
(args.output/(name+'.json')).write_text(json.dumps(report, indent=2)+'\n')
print('Sequential League history passed:', name, flush=True)
