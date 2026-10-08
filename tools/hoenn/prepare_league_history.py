"""Preserve the shared Hall of Fame when winning another region's League."""
import argparse
import hashlib
import json
from pathlib import Path
from prepare_crossing import PIN
from prepare_family import LAYERS_BEFORE


def prepare(source):
    source = Path(source)
    marker = source / '.journey-league-history'
    if marker.exists():
        report = json.loads(marker.read_text())
        for path, digest in report['prepared_sha256'].items():
            assert hashlib.sha256((source / path).read_bytes()).hexdigest() == digest, path
        return report
    acquired = json.loads((source / '.source-acquired.json').read_text())
    assert acquired['commit'] == PIN
    expected = dict(acquired['sha256'])
    for layer in LAYERS_BEFORE + ['family', 'travel-rules', 'birth', 'wild', 'habitats',
                                 'sanctuaries', 'ecology', 'abilities', 'mega-art', 'story-aftermath',
                                 'league-access', 'league-completion']:
        expected.update(json.loads((source / ('.journey-' + layer)).read_text())['prepared_sha256'])
    originals, inputs, outputs = {}, {}, {}

    def read(path):
        raw = (source / path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected[path], path
        originals[path] = expected[path]
        if path in acquired['sha256']:
            inputs[path] = acquired['sha256'][path]
        return raw.decode()

    path = 'src/post_battle_event_funcs.c'
    body = read(path)
    needle = '''    if (FlagGet(FLAG_SYS_GAME_CLEAR) == TRUE)
    {
        gHasHallOfFameRecords = TRUE;
        gHasHallOfFameRecordsFrlg = TRUE;
    }
    else
    {
        gHasHallOfFameRecords = FALSE;
        gHasHallOfFameRecordsFrlg = FALSE;
        FlagSet(FLAG_SYS_GAME_CLEAR);
    }'''
    assert body.count(needle) == 2
    replacement = '''    // Both regions write to the same archive. Regional clear flags cannot
    // tell whether the other League has already saved a Hall of Fame team.
    gHasHallOfFameRecords = GetGameStat(GAME_STAT_ENTERED_HOF) != 0;
    gHasHallOfFameRecordsFrlg = gHasHallOfFameRecords;
    FlagSet(FLAG_SYS_GAME_CLEAR);'''
    outputs[path] = body.replace(needle, replacement).encode()
    path = 'include/hall_of_fame.h'
    body = read(path)
    needle = '#define GUARD_HALL_OF_FAME_H\n'
    assert body.count(needle) == 1
    outputs[path] = body.replace(needle, needle + '\n// One archive is shared by both regional Hall of Fame screens.\n#define HALL_OF_FAME_MAX_TEAMS 50\n').encode()
    for path, limit in [('src/hall_of_fame.c', 30), ('src/hall_of_fame_frlg.c', 50)]:
        body = read(path)
        needle = f'#define HALL_OF_FAME_MAX_TEAMS {limit}\n'
        assert body.count(needle) == 1
        outputs[path] = body.replace(needle, '').encode()
    report = dict(status='shared_hall_of_fame_candidate', source_commit=PIN,
                  shared_archive_capacity=50, shared_saved_team_stat_controls_history=True,
                  save_layout_unchanged=True, regional_clear_and_champion_flags_independent=True,
                  full_campaign_validated=False, input_sha256=inputs, original_sha256=originals,
                  prepared_sha256={p: hashlib.sha256(raw).hexdigest() for p, raw in outputs.items()})
    for path, raw in outputs.items():
        (source / path).write_bytes(raw)
    marker.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    print(json.dumps(prepare(parser.parse_args().source), indent=2))
