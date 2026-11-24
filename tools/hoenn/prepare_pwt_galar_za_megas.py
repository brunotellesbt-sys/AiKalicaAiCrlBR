"""Stage reviewed Galar teams and the PWT's native Z-A Mega Stone selection."""
import argparse
import json
from pathlib import Path
import re

from badge_story_layer import read
from candidate_layer import Layer
from prepare_pwt_official_parties import ACTOR, CATALOG, TRAINERS, replace_species
from prepare_pwt_official_parties import LAYER as PREVIOUS, PRIOR as PREVIOUS_LAYERS
from pwt_catalog import load
from review_pwt_official_parties import OUTPUT as PREVIOUS_REVIEW, species_catalog

HERE = Path(__file__).resolve().parent
REFERENCE = HERE / 'data/pwt-galar-party-review.json'
PRIOR = PREVIOUS_LAYERS + [PREVIOUS]
LAYER = 'pwt-galar-za-megas'


def load_review(path=REFERENCE):
    report = json.loads(path.read_bytes())
    previous = json.loads(PREVIOUS_REVIEW.read_bytes())
    roster = {row['key']: row for row in load()}
    national, _ = species_catalog()
    reviewed = {}
    for row in report['reviewed']:
        key = row['key']
        current = roster[key]
        if key in reviewed or key not in previous['remaining'] or current['generations'] != [8]:
            raise ValueError(('Galar review must cover existing, previously unreviewed identities', key))
        team = row['official'] + row['additions']
        if (row['name'] != current['name'] or len(row['official']) != 5
                or len(team) != 6 or len({national[mon] for mon in team}) != 6):
            raise ValueError(('Expected a distinct six-member Galar party and five reference species', key))
        reviewed[key] = dict(previous=current['species'], reference=team, gen1_4=None)
    if not reviewed or len(reviewed) != len(report['reviewed']):
        raise ValueError('Missing or repeated Galar review')
    return reviewed


def prepare(source):
    layer = Layer(source, LAYER, PRIOR)
    if existing := layer.existing():
        return existing
    reviewed = load_review()
    for path in CATALOG, TRAINERS:
        text = read(layer, path).decode()
        for key, row in reviewed.items():
            pattern = r'^.*\bTRAINER_JOURNEY_PWT_' + re.escape(key) + r'\b[^\n]*$'
            text, count = re.subn(pattern, lambda m: replace_species(m[0], row['previous'], row['reference']),
                                  text, flags=re.M)
            if count != 1:
                raise ValueError(('Missing or repeated Galar trainer row', path, key))
        layer.stage(path, text)

    code = read(layer, ACTOR).decode()
    includes = '#include "constants/items.h"'
    start = 'void JourneyPWTPrepareBattle(void)'
    selection = '    JourneyPWTOptimizeParty(gEnemyParty,PARTY_SIZE);'
    if any(code.count(anchor) != 1 for anchor in (includes, start, selection)):
        raise ValueError('Unrecognized PWT team preparation')
    code = code.replace(includes, includes + '\n#include "item.h"\n'
                        '#include "constants/form_change_types.h"\n#include "constants/hold_effects.h"')
    code = code.replace(start, (HERE / 'pwt_za_megas.c').read_text() + '\n' + start)
    code = code.replace(selection, '    GivePWTZAMegaStone();\n' + selection)
    layer.stage(ACTOR, code)
    return layer.finish(galar_teams=len(reviewed), entrant_ids_preserved=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('private_source', type=Path)
    args = parser.parse_args()
    result = prepare(args.private_source)
    print(result['galar_teams'], 'Galar teams and PWT Z-A Mega Stone selection')
