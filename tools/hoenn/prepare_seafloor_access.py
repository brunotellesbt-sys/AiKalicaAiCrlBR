"""Move the Seafloor entrance grunt off the only passage; retain his story."""
import argparse
import hashlib
import json
from pathlib import Path
from prepare_crossing import PIN
from prepare_family import LAYERS_BEFORE

def prepare(source):
    source = Path(source)
    marker = source / '.journey-seafloor-access'
    if marker.exists():
        report = json.loads(marker.read_text())
        for path, digest in report['prepared_sha256'].items():
            if hashlib.sha256((source / path).read_bytes()).hexdigest() != digest:
                raise ValueError('Modified Seafloor access output: ' + path)
        return report
    acquired = json.loads((source / '.source-acquired.json').read_text())
    if acquired['commit'] != PIN: raise ValueError('Unexpected source revision')
    expected = dict(acquired['sha256'])
    for layer in LAYERS_BEFORE + ['family', 'travel-rules', 'birth', 'wild', 'habitats',
                                 'sanctuaries', 'ecology', 'abilities', 'mega-art', 'story-aftermath',
                                 'league-access', 'league-completion', 'league-history', 'league-display',
                                 'family-postgame', 'pwt', 'frontier-travel', 'story-puzzles', 'aqua-episodes']:
        expected.update(json.loads((source / ('.journey-' + layer)).read_text())['prepared_sha256'])
    def checked(path):
        raw = (source / path).read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected[path]:
            raise ValueError('Unreviewed Seafloor access input: ' + path)
        return raw
    path = 'data/maps/SeafloorCavern_Entrance/map.json'
    data = json.loads(checked(path))
    grunt = data['object_events'][0]
    assert grunt['local_id'] == 'LOCALID_SEAFLOOR_CAVERN_ENTRANCE_GRUNT'
    assert (grunt['x'], grunt['y']) == (10, 2)
    grunt['x'], grunt['y'] = 11, 3
    output = (json.dumps(data, indent=2) + '\n').encode()
    preserved = {}
    for other in ['data/maps/SeafloorCavern_Entrance/scripts.inc',
                  'data/maps/MossdeepCity_StevensHouse/scripts.inc',
                  'data/maps/SeafloorCavern_Room9/scripts.inc', 'src/field_move.c',
                  'src/journey_campaign_gates.c', 'src/journey_gym_scaling.c',
                  'include/constants/flags.h', 'data/layouts/SeafloorCavern_Entrance/map.bin']:
        checked(other); preserved[other] = expected[other]
    report = dict(status='seafloor_passage_candidate', source_commit=PIN,
                  guard=dict(map='SeafloorCavern_Entrance', local_id=grunt['local_id'],
                             before=[10, 2], after=[11, 3], script=grunt['script'], flag=grunt['flag']),
                  guard_dialogue_visibility_and_steven_event_retained=True,
                  only_guard_coordinates_changed=True, native_dive_surf_and_boss_missions_retained=True,
                  badge_scaling_and_save_layout_unchanged=True, new_flags_allocated=False,
                  full_campaign_validated=False, original_sha256={path: expected[path]},
                  preserved_native_sha256=preserved, prepared_sha256={path: hashlib.sha256(output).hexdigest()})
    (source / path).write_bytes(output)
    marker.write_text(json.dumps(report, indent=2) + '\n')
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source), indent=2))
