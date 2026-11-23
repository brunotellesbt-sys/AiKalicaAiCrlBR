"""Install the reviewed official PWT parties on the Atlas route-pruning build."""
import argparse
import json
from pathlib import Path
import re

from badge_story_layer import read
from candidate_layer import Layer
from prepare_atlas_route_pruning import LAYER as PREVIOUS, PRIOR as PREVIOUS_LAYERS
from pwt_catalog import eligible, load
from review_pwt_official_parties import LEAGUE_CAP4_REPLACEMENTS, OUTPUT, species_catalog

LAYER = 'pwt-official-parties'
PRIOR = PREVIOUS_LAYERS + [PREVIOUS]
CATALOG = 'src/data/journey_pwt_catalog.h'
TRAINERS = 'src/data/journey_pwt_trainers.h'
ACTOR = 'src/journey_pwt.c'
CAPS = 'src/data/journey_pwt_cap4_review.h'


def replace_species(line, previous, updated):
    matches = list(re.finditer(r'\bSPECIES_(\w+)\b', line))
    if [match[1] for match in matches] != previous:
        raise ValueError('Source roster differs from its expected previous party')
    for match, species in zip(reversed(matches), reversed(updated)):
        line = line[:match.start(1)] + species + line[match.end(1):]
    return line


def validate_review(report):
    rows = load()
    current = {row['key']: row for row in rows}
    cap4 = {row['key'] for row in eligible(rows, 4)}
    national, _ = species_catalog()
    official = report['reviewed']
    league = report['league_reviewed']
    reviewed = {record['key']: record for record in official + league}
    if (report['kind'] != 'pwt-and-league-party-references' or len(official) != 54 or len(league) != 14
            or len(reviewed) != len(official) + len(league)
            or set(reviewed) & set(report['remaining'])
            or set(reviewed) | set(report['remaining']) != set(current)):
        raise ValueError('Official and other PWT entries must account for the current roster exactly')
    for key, record in reviewed.items():
        prior = current[key]
        full = record['reference']
        limit = record['gen1_4']
        if record['previous'] != prior['species'] or record['name'] != prior['name']:
            raise ValueError(('Reviewed entry does not match its historical identity', key))
        # Agatha's documented rematch uses two Gengar.
        distinct = 5 if key == 'AGATHA' else 6
        if len(full) != 6 or len({national[mon] for mon in full}) != distinct:
            raise ValueError(('Unexpected reference party composition', key))
        if key in cap4:
            if len(limit) != 6 or len({national[mon] for mon in limit}) != distinct:
                raise ValueError(('Unexpected Gen 1–4 party composition', key))
            replacements = LEAGUE_CAP4_REPLACEMENTS.get(prior['name'], {})
            required = {mon for mon in full if national[mon] <= 493 and mon not in replacements}
            if any(national[mon] > 493 for mon in limit) or not required <= set(limit):
                raise ValueError(('Gen 1–4 adaptation must retain legal reference species', key))
            if 'battle' in record and limit != [replacements.get(mon, mon) for mon in full]:
                raise ValueError(('Gen 1–4 League party differs from the reviewed adaptation', key))
        elif limit is not None:
            raise ValueError(('Gen 1–4 party supplied for an ineligible trainer', key))
    return reviewed


def prepare(source, reference=OUTPUT):
    layer = Layer(source, LAYER, PRIOR)
    if existing := layer.existing():
        return existing
    reference = Path(reference)
    report = json.loads(reference.read_bytes())
    reviewed = validate_review(report)

    for path in (CATALOG, TRAINERS):
        source_text = read(layer, path).decode()
        for key, row in reviewed.items():
            selector = r'^.*\bTRAINER_JOURNEY_PWT_' + re.escape(key) + r'\b[^\n]*$'

            def replace(match):
                return replace_species(match[0], row['previous'], row['reference'])

            source_text, count = re.subn(selector, replace, source_text, flags=re.M)
            if count != 1:
                raise ValueError(('Missing or repeated roster line', path, key))
        layer.stage(path, source_text)

    available = [r for r in reviewed.values() if r['gen1_4'] is not None]
    cap_rows = ''.join('    [JOURNEY_PWT_' + r['key'] + '] = {'
                       + ', '.join('SPECIES_' + mon for mon in r['gen1_4']) + '},\n'
                       for r in available)
    layer.stage(CAPS, 'static const u16 sPWTReviewedGen4[ARRAY_COUNT(sPWTTrainers)][PARTY_SIZE] = {\n'
                + cap_rows + '};\n')
    code = read(layer, ACTOR).decode()
    include = '#include "data/journey_pwt_catalog.h"'
    anchor = '    // Ash\'s generation-four entry uses his strongest eligible anime reserves.'
    if code.count(include) != 1 or code.count(anchor) != 1:
        raise ValueError('Unrecognized PWT cap-selection source')
    code = code.replace(include, include + '\n#include "data/journey_pwt_cap4_review.h"')
    code = code.replace(anchor,
        '    if (JourneyPWTMaxGeneration() == 4 && sPWTReviewedGen4[trainer][slot] != SPECIES_NONE)\n'
        '        return sPWTReviewedGen4[trainer][slot];\n' + anchor)
    layer.stage(ACTOR, code)
    return layer.finish(official_teams=len(report['reviewed']), league_teams=len(report['league_reviewed']),
                        gen4_teams=len(available),
                        entrant_ids_preserved=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('private_source', type=Path)
    args = parser.parse_args()
    result = prepare(args.private_source)
    print(result['official_teams'], 'PWT teams,', result['league_teams'], 'League teams,',
          result['gen4_teams'], 'Gen 1–4 teams')
