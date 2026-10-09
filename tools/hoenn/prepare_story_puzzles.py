"""Open the three terrestrial move puzzle doors by reading their inscriptions.

Keep Dive access, the inner chamber's party riddle and special capture gates.
"""
import argparse
import hashlib
import json
from pathlib import Path
from prepare_crossing import PIN
from prepare_family import LAYERS_BEFORE

PUZZLES = [
    ('DesertRuins', 'CaveEntranceMiddle', 'CaveEntranceSide',
     'FLAG_SYS_REGIROCK_PUZZLE_COMPLETED', 7, 19),
    ('AncientTomb', 'CaveEntranceMiddle', 'CaveEntranceSide',
     'FLAG_SYS_REGISTEEL_PUZZLE_COMPLETED', 7, 19),
    ('SealedChamber_OuterRoom', 'InnerRoomEntranceWall', 'BrailleDigHere',
     'FLAG_SYS_BRAILLE_DIG', 9, 1),
]

def prepare(source):
    source = Path(source)
    marker = source / '.journey-story-puzzles'
    if marker.exists():
        report = json.loads(marker.read_text())
        for path, digest in report['prepared_sha256'].items():
            if hashlib.sha256((source / path).read_bytes()).hexdigest() != digest:
                raise ValueError('Modified puzzle output: ' + path)
        return report
    acquired = json.loads((source / '.source-acquired.json').read_text())
    if acquired['commit'] != PIN:
        raise ValueError('Unexpected source revision')
    expected = dict(acquired['sha256'])
    for layer in LAYERS_BEFORE + ['family', 'travel-rules', 'birth', 'wild', 'habitats',
                                 'sanctuaries', 'ecology', 'abilities', 'mega-art', 'story-aftermath',
                                 'league-access', 'league-completion', 'league-history',
                                 'league-display', 'family-postgame', 'pwt', 'frontier-travel']:
        expected.update(json.loads((source / ('.journey-' + layer)).read_text())['prepared_sha256'])
    originals, inputs, outputs, preserved = {}, {}, {}, {}

    def read(path):
        raw = (source / path).read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected[path]:
            raise ValueError('Unreviewed puzzle input: ' + path)
        if path in acquired['sha256']:
            inputs[path] = acquired['sha256'][path]
        return raw.decode()

    for name, middle, side, flag, x, y in PUZZLES:
        path = f'data/maps/{name}/scripts.inc'
        body = read(path)
        originals[path] = expected[path]
        label = f'{name}_EventScript_{middle}::\n'
        begin = body.index(label)
        end = body.index('\n\n', begin)
        old = body[begin:end]
        target = (f'{name}_EventScript_BigHoleInWall' if name != 'SealedChamber_OuterRoom'
                  else f'{name}_EventScript_HoleInWall')
        door = []
        for dy, parts in enumerate([['TopLeft', 'TopMid', 'TopRight'],
                                    ['BottomLeft', 'BottomMid', 'BottomRight']]):
            for dx, part in enumerate(parts):
                collision = 'FALSE' if dy == 0 or dx == 1 else 'TRUE'
                door.append(f'\tsetmetatile {x + dx}, {y + dy}, METATILE_Cave_SealedChamberEntrance_{part}, {collision}\n')
        new = (label + '\tlockall\n' + f'\tgoto_if_set {flag}, {target}\n'
               + '\tmsgbox Journey_PuzzleInscription, MSGBOX_DEFAULT\n\tclosemessage\n'
               + ''.join(door) + f'\tsetflag {flag}\n'
               + '\tplayse SE_BANG\n\tspecial DrawWholeMapView\n\twaitse\n\treleaseall\n\tend')
        body = body[:begin] + new + body[end:]
        label = f'{name}_EventScript_{side}::\n'
        begin = body.index(label)
        end = body.index('\n\n', begin)
        body = body[:begin] + label + f'\tgoto {name}_EventScript_{middle}\n\tend' + body[end:]
        outputs[path] = body.encode()
    path = 'data/scripts/journey_campaign_gates.inc'
    body = read(path)
    originals[path] = expected[path]
    outputs[path] = (body + '''
Journey_PuzzleInscription:
\t.string "You read the ancient inscription.\\p"
\t.string "The stone door begins to open!$"
''').encode()
    # Neither opening doors nor inspecting inscriptions completes a villain
    # mission, grants badges, unlocks captures or changes the native Regice walk.
    for path in ['data/maps/SealedChamber_InnerRoom/scripts.inc',
                 'data/maps/IslandCave/scripts.inc', 'src/journey_special.c',
                 'src/journey_campaign_gates.c', 'src/journey_gym_scaling.c',
                 'src/journey_pwt.c', 'src/field_move.c', 'include/constants/flags.h']:
        read(path)
        preserved[path] = expected[path]
    report = dict(status='terrestrial_puzzle_doors_candidate', source_commit=PIN,
                  doors=[dict(map=n, flag=f, formerly=m, opening='read center or side inscription')
                         for (n, _, _, f, _, _), m in zip(PUZZLES, ['Rock Smash', 'Flash', 'Dig'])],
                  dive_access_retained=True, inner_party_riddle_retained=True,
                  regice_walking_puzzle_retained=True, sixteen_badges_capture_gate_retained=True,
                  new_flags_allocated=False, save_layout_unchanged=True,
                  full_campaign_validated=False, input_sha256=inputs,
                  original_sha256=originals, preserved_native_sha256=preserved,
                  prepared_sha256={p: hashlib.sha256(raw).hexdigest() for p, raw in outputs.items()})
    for path, raw in outputs.items():
        (source / path).write_bytes(raw)
    marker.write_text(json.dumps(report, indent=2) + '\n')
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    print(json.dumps(prepare(parser.parse_args().source), indent=2))
