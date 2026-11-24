"""Install the final documented parties for the existing PWT entrants."""
import argparse
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from badge_story_layer import read
from candidate_layer import Layer
from prepare_pwt_galar_za_megas import LAYER as PREVIOUS, PRIOR as PREVIOUS_LAYERS, load_review as load_galar
from prepare_pwt_official_parties import ACTOR, CAPS, CATALOG, TRAINERS, replace_species, validate_review
from pwt_catalog import eligible, load
from review_pwt_official_parties import OUTPUT, species_catalog

HERE = Path(__file__).resolve().parent
REFERENCE = HERE / 'data/pwt-complete-roster-review.json'
LAYER = 'pwt-complete-rosters'
PRIOR = PREVIOUS_LAYERS + [PREVIOUS]


def load_review():
    data = json.loads(REFERENCE.read_bytes())
    if data['kind'] != 'pwt-complete-roster-review':
        raise ValueError('Expected the complete roster review')
    rows = load()
    original = {row['key']: row for row in rows}
    cap4 = {row['key'] for row in eligible(rows, 4)}
    official = validate_review(json.loads(OUTPUT.read_bytes()))
    galar = load_galar()
    pinned = {row['key'] for row in rows if row['reference_audit'] == 'pinned_original_data'}
    guests = {row['key'] for row in rows if row['generations'] == [0]}
    previously_reviewed = set(official) | set(galar) | pinned | guests
    remaining = set(original) - previously_reviewed
    national, _ = species_catalog()
    result = {}
    for record in data['reviewed']:
        key = record['key']
        source = urlsplit(record['source'])
        if key not in remaining or key in result:
            raise ValueError(('Expected an existing, outstanding roster', key))
        if (source.scheme != 'https' or source.netloc not in {'www.serebii.net', 'bulbapedia.bulbagarden.net'}
                or not re.fullmatch(r'[0-9a-f]{64}', record['source_sha256']) or not record['battle']):
            raise ValueError(('Missing documented battle provenance', key))
        prior = original[key]
        reference, adapted = record['reference'], record['gen1_4']
        additions = [entry['species'] for entry in record['additions']]
        if (record['previous'] != prior['species'] or record['name'] != prior['name']
                or reference != record['documented'] + additions or len(reference) != 6
                or len({national[mon] for mon in reference}) != 6):
            raise ValueError(('Expected the full documented party and its roster additions', key))
        if key in cap4:
            substitutions = record['cap_replacements']
            expected = [substitutions.get(mon, mon) for mon in reference]
            if (adapted != expected or len({national[mon] for mon in adapted}) != 6
                    or any(national[mon] > 493 for mon in adapted)
                    or set(substitutions) != {mon for mon in reference if national[mon] > 493}):
                raise ValueError(('Invalid Gen 1–4 adaptation', key))
        elif adapted is not None:
            raise ValueError(('Gen 1–4 team supplied for an ineligible entrant', key))
        result[key] = record
    if result.keys() != remaining or len(result) != 73:
        raise ValueError(('The catalog review must account for every slot', sorted(remaining - result.keys())))
    return result


def prepare(source):
    layer = Layer(source, LAYER, PRIOR)
    if existing := layer.existing():
        return existing
    reviewed = load_review()
    for name in CATALOG, TRAINERS:
        contents = read(layer, name).decode()
        for key, record in reviewed.items():
            pattern = r'^.*\bTRAINER_JOURNEY_PWT_' + re.escape(key) + r'\b[^\n]*$'
            contents, count = re.subn(pattern, lambda m: replace_species(
                m[0], record['previous'], record['reference']), contents, flags=re.M)
            if count != 1:
                raise ValueError(('Missing or repeated roster row', name, key))
        layer.stage(name, contents)

    cap4_teams = {key: record['gen1_4'] for key, record in reviewed.items() if record['gen1_4'] is not None}
    caps = read(layer, CAPS).decode()
    if not caps.endswith('};\n') or any(f'[JOURNEY_PWT_{key}]' in caps for key in cap4_teams):
        raise ValueError('Unrecognized Gen 1–4 roster table')
    entries = ''.join(f'    [JOURNEY_PWT_{key}] = {{'
                      + ', '.join(f'SPECIES_{mon}' for mon in team) + '},\n'
                      for key, team in cap4_teams.items())
    layer.stage(CAPS, caps.removesuffix('};\n') + entries + '};\n')

    actor = read(layer, ACTOR).decode()
    anchor = '        JourneyPrepareCompetitiveMon(&build, 100);\n'
    if actor.count(anchor) != 1:
        raise ValueError('Unrecognized competitive build step')
    # Gladion's documented Water-form Silvally needs its matching Memory.
    layer.stage(ACTOR, actor.replace(anchor, anchor + '        if (build.species == SPECIES_SILVALLY_WATER)\n'
                                     '            build.heldItem = ITEM_WATER_MEMORY;\n'))
    return layer.finish(reviewed_teams=len(reviewed), gen1_4_teams=len(cap4_teams),
                        catalog_complete=True, entrant_ids_preserved=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('private_source', type=Path)
    args = parser.parse_args()
    result = prepare(args.private_source)
    print(result['reviewed_teams'], 'reviewed teams complete the PWT catalog')
