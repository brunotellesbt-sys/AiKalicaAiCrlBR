"""Keep Hoenn's last free-order gym gated until the original climate crisis ends."""
import argparse
import hashlib
import json
from pathlib import Path
from prepare_crossing import PIN
from prepare_family import LAYERS_BEFORE


def prepare(source):
    source = Path(source)
    marker = source / '.journey-story-aftermath'
    if marker.exists():
        report = json.loads(marker.read_text())
        for path, digest in report['prepared_sha256'].items():
            assert hashlib.sha256((source / path).read_bytes()).hexdigest() == digest, path
        return report
    acquired = json.loads((source / '.source-acquired.json').read_text())
    assert acquired['commit'] == PIN
    expected = dict(acquired['sha256'])
    for layer in LAYERS_BEFORE + ['family', 'travel-rules', 'birth', 'wild', 'habitats',
                                 'sanctuaries', 'ecology', 'abilities', 'mega-art']:
        expected.update(json.loads((source / ('.journey-' + layer)).read_text())['prepared_sha256'])
    inputs, originals, outputs = {}, {}, {}
    def read(path):
        raw = (source / path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected[path], path
        originals[path] = expected[path]
        if path in acquired['sha256']:
            inputs[path] = acquired['sha256'][path]
        return raw.decode()
    path = 'src/journey_campaign_gates.c'
    body = read(path)
    needle = '        if (count >= 7 && !RegionalFlag(FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN))\n            return 6;'
    assert body.count(needle) == 1
    body = body.replace(needle, needle + '''
        // Archie starts the crisis; Rayquaza's original Sootopolis scene
        // clears this flag. Preserve that mission for every final gym choice.
        if (count >= 7 && RegionalFlag(FLAG_SYS_WEATHER_CTRL))
            return 14;''')
    outputs[path] = body.encode()
    path = 'data/scripts/journey_campaign_gates.inc'
    body = read(path)
    needle = '\tgoto_if_eq VAR_RESULT, 13, Journey_GymGuide_Event13'
    assert body.count(needle) == 1
    body = body.replace(needle, needle + '\n\tgoto_if_eq VAR_RESULT, 14, Journey_GymGuide_Event14')
    body += '''
Journey_GymGuide_Event14::
\tmsgbox Journey_GymGuide_Text14, MSGBOX_DEFAULT
\trelease
\tend

Journey_GymGuide_Text14::
\t.string "The GYM LEADER is helping\\n"
\t.string "with the climate crisis!\\p"
\t.string "TEAM AQUA and TEAM MAGMA\\n"
\t.string "awakened the ancient POKEMON.\\p"
\t.string "Meet WALLACE in the CAVE OF\\n"
\t.string "ORIGIN in SOOTOPOLIS.\\p"
\t.string "Wake RAYQUAZA at SKY PILLAR,\\n"
\t.string "north of ROUTE 131.\\p"
\t.string "Return to SOOTOPOLIS so it\\n"
\t.string "can stop the clash!$"
'''
    outputs[path] = body.encode()
    path = 'data/maps/SootopolisCity/scripts.inc'
    body = read(path)
    needle = '\tcall_if_unset FLAG_SOOTOPOLIS_ARCHIE_MAXIE_LEAVE, SootopolisCity_EventScript_LockHouseDoors\n'
    assert body.count(needle) == 1
    body = body.replace(needle, '\t@ Homes remain accessible during the crisis, including the selected family home.\n')
    outputs[path] = body.encode()
    preserved = {}
    for path in ['data/maps/SeafloorCavern_Room9/scripts.inc', 'data/maps/SkyPillar_Top/scripts.inc',
                 'data/maps/MossdeepCity_SpaceCenter_2F/scripts.inc']:
        raw = (source / path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected[path], path
        preserved[path] = expected[path]
    report = dict(status='original_hoenn_climate_aftermath_candidate', source_commit=PIN,
                  gate=14, hoenn_badge_threshold=7, completion='original scene clears FLAG_SYS_WEATHER_CTRL',
                  kanto_gates_unchanged=True, native_rayquaza_scene_preserved=True,
                  rayquaza_capture_not_required=True, no_new_roadblocks=True,
                  homes_accessible_during_crisis=True, new_flags_allocated=False,
                  full_campaign_validated=False, preserved_native_sha256=preserved,
                  input_sha256=inputs, original_sha256=originals,
                  prepared_sha256={p: hashlib.sha256(data).hexdigest() for p, data in outputs.items()})
    for path, raw in outputs.items():
        (source / path).write_bytes(raw)
    marker.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    print(json.dumps(prepare(parser.parse_args().source), indent=2))
