"""Open ordinary Hoenn cave passages without requiring the regional League."""
import argparse
import hashlib
import json
from pathlib import Path
from prepare_crossing import PIN
from prepare_family import LAYERS_BEFORE

def prepare(source):
    source = Path(source)
    marker = source / '.journey-cave-access'
    if marker.exists():
        report = json.loads(marker.read_text())
        for path, digest in report['prepared_sha256'].items():
            if hashlib.sha256((source / path).read_bytes()).hexdigest() != digest:
                raise ValueError('Modified cave access output: ' + path)
        return report
    acquired = json.loads((source / '.source-acquired.json').read_text())
    if acquired['commit'] != PIN: raise ValueError('Unexpected source revision')
    expected = dict(acquired['sha256'])
    for layer in LAYERS_BEFORE + ['family', 'travel-rules', 'birth', 'wild', 'habitats',
                                 'sanctuaries', 'ecology', 'abilities', 'mega-art', 'story-aftermath',
                                 'league-access', 'league-completion', 'league-history', 'league-display',
                                 'family-postgame', 'pwt', 'frontier-travel', 'story-puzzles', 'aqua-episodes',
                                 'seafloor-access', 'water-continue']:
        expected.update(json.loads((source / ('.journey-' + layer)).read_text())['prepared_sha256'])
    def checked(path):
        raw = (source / path).read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected[path]:
            raise ValueError('Unreviewed cave access input: ' + path)
        return raw
    outputs = {}
    path = 'data/maps/Route103/scripts.inc'
    body = checked(path).decode()
    old = '\tcall_if_set FLAG_SYS_GAME_CLEAR, Route103_EventScript_OpenAlteringCave\n'
    if body.count(old) != 1: raise ValueError('Ambiguous Altering Cave gate')
    outputs[path] = body.replace(old, '\tcall Route103_EventScript_OpenAlteringCave\n').encode()
    path = 'data/maps/Route114_FossilManiacsTunnel/scripts.inc'
    body = checked(path).decode()
    old = '\tcall_if_set FLAG_SYS_GAME_CLEAR, Route114_FossilManiacsTunnel_EventScript_MoveFossilManiac\n'
    if body.count(old) != 1: raise ValueError('Ambiguous fossil maniac placement')
    body = body.replace(old, '\tcall Route114_FossilManiacsTunnel_EventScript_MoveFossilManiac\n')
    old = '\tcall_if_unset FLAG_SYS_GAME_CLEAR, Route114_FossilManiacsTunnel_EventScript_CloseDesertUnderpass\n'
    if body.count(old) != 1: raise ValueError('Ambiguous Desert Underpass gate')
    body = body.replace(old, '')
    old = '\t.string "It\'s not safe that way…\\p"'
    if body.count(old) != 1: raise ValueError('Ambiguous old cave-in warning')
    body = body.replace(old, '\t.string "The passage is safe now…\\p"')
    outputs[path] = body.encode()
    preserved = {}
    for other in ['data/maps/DesertUnderpass/scripts.inc', 'data/maps/AlteringCave/map.json',
                  'data/maps/Route103/map.json', 'data/maps/Route114_FossilManiacsTunnel/map.json',
                  'data/layouts/Route103/map.bin', 'data/layouts/Route114_FossilManiacsTunnel/map.bin',
                  'src/journey_campaign_gates.c', 'src/journey_gym_scaling.c',
                  'src/journey_special.c', 'src/journey_wild.c', 'include/journey_habitat_data.h',
                  'src/field_player_avatar.c', 'include/constants/flags.h']:
        checked(other); preserved[other] = expected[other]
    report = dict(status='ordinary_cave_access_candidate', source_commit=PIN,
                  altering_cave_open_before_league=True, desert_underpass_open_before_league=True,
                  fossil_maniac_uses_original_postgame_position=True, cave_in_dialogue_updated=True,
                  fossil_rewards_and_landmark_script_preserved=True,
                  gym_missions_scaling_and_special_capture_gate_preserved=True,
                  map_layouts_and_warps_unchanged=True, new_flags_allocated=False,
                  full_campaign_validated=False,
                  original_sha256={p: expected[p] for p in outputs}, preserved_native_sha256=preserved,
                  prepared_sha256={p: hashlib.sha256(v).hexdigest() for p, v in outputs.items()})
    for path, output in outputs.items(): (source / path).write_bytes(output)
    marker.write_text(json.dumps(report, indent=2) + '\n')
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source), indent=2))
