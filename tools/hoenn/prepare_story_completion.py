"""Keep Space Center victory permanent after the native rival's Rayquaza call."""
import argparse
import hashlib
import json
from pathlib import Path
from prepare_crossing import PIN
from prepare_free_access import LAYERS


def prepare(source):
    source = Path(source)
    marker = source / '.journey-story-completion'
    if marker.exists():
        report = json.loads(marker.read_text())
        for path, digest in report['prepared_sha256'].items():
            assert hashlib.sha256((source / path).read_bytes()).hexdigest() == digest, path
        return report
    acquired = json.loads((source / '.source-acquired.json').read_text())
    assert acquired['commit'] == PIN
    expected = dict(acquired['sha256'])
    for layer in LAYERS + ['free-access', 'blue-gym', 'road-access', 'mach-bike', 'yellow-stairs', 'story-access']:
        expected.update(json.loads((source / f'.journey-{layer}').read_text())['prepared_sha256'])
    inputs, originals, outputs = {}, {}, {}

    def read(path):
        raw = (source / path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected[path], path
        if path in acquired['sha256']:
            inputs[path] = acquired['sha256'][path]
        return raw

    def stage(path, body):
        originals[path] = hashlib.sha256(read(path)).hexdigest()
        outputs[path] = body.encode()

    # Native state 3 is committed by the victorious Steven/Maxie/Tabitha scene.
    # The legacy flag is transient: the rival consumes it for a one-time call.
    path = 'src/journey_campaign_gates.c'
    body = read(path).decode()
    needle = 'RegionalFlag(FLAG_DEFEATED_MAGMA_SPACE_CENTER)'
    assert body.count(needle) == 3
    body = body.replace(needle, 'JourneySpaceCenterComplete()')
    anchor = 'static bool32 JourneyMissionComplete('
    assert body.count(anchor) == 1
    body = body.replace(anchor, '''static bool32 JourneySpaceCenterComplete(void)
{
    // Do not use the temporary flag consumed by the rival's Rayquaza call.
    return VarGet(VAR_MOSSDEEP_SPACE_CENTER_STATE) == 3;
}

''' + anchor)
    stage(path, body)
    path = 'src/field_move.c'
    body = read(path).decode()
    needle = 'FlagGet(FLAG_DEFEATED_MAGMA_SPACE_CENTER)'
    assert body.count(needle) == 1
    body = body.replace(needle, '(VarGet(VAR_MOSSDEEP_SPACE_CENTER_STATE) == 3)')
    assert '#include "constants/vars.h"' not in body
    body = body.replace('#include "constants/party_menu.h"',
                        '#include "constants/party_menu.h"\n#include "constants/vars.h"')
    stage(path, body)
    preserved = {}
    for path in ['data/maps/MossdeepCity_SpaceCenter_2F/scripts.inc', 'src/field_specials.c',
                 'data/maps/MossdeepCity_StevensHouse/scripts.inc']:
        preserved[path] = hashlib.sha256(read(path)).hexdigest()
    # Retain the original Meteor Falls scene while explaining how to reach it.
    path = 'data/scripts/journey_campaign_gates.inc'
    body = read(path).decode()
    needle = '\t.string "Please help at the summit!$"'
    assert body.count(needle) == 1
    body = body.replace(needle, '''\t.string "Please help at the summit!\\p"
\t.string "First visit METEOR FALLS,\\n"
\t.string "on ROUTE 114 or 115.\\p"
\t.string "MAGMA is after COZMO's\\n"
\t.string "meteorite there!$"''')
    stage(path, body)
    for path, raw in outputs.items():
        (source / path).write_bytes(raw)
    report = dict(status='permanent_space_center_completion_candidate', source_commit=PIN,
                  completion_state='VAR_MOSSDEEP_SPACE_CENTER_STATE == 3',
                  legacy_flag='FLAG_DEFEATED_MAGMA_SPACE_CENTER',
                  legacy_flag_is_transient=True, native_rayquaza_call_unchanged=True,
                  dive_permission_survives_call=True, archie_permission_survives_call=True,
                  new_flags_allocated=False, native_steven_dive_gift_unchanged=True,
                  meteor_falls_quest_preserved=True, full_story_validated=False,
                  preserved_native_sha256=preserved, input_sha256=inputs, original_sha256=originals,
                  prepared_sha256={p: hashlib.sha256(v).hexdigest() for p, v in outputs.items()})
    marker.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source), indent=2))
