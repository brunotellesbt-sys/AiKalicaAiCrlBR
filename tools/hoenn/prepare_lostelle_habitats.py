"""Keep Drowzee/Hypno in Berry Forest, including the original Lostelle event."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
from prepare_crossing import PIN
from prepare_english_text import PRIOR
from prepare_ecology import FIELDS, LAND_RATES, WATER_RATES, weighted_slots


def prepare(source):
    source = Path(source)
    marker = source / '.journey-lostelle-habitats'
    if marker.exists():
        report = json.loads(marker.read_text())
        for path, digest in (report['prepared_sha256'] | report['preserved_native_sha256']).items():
            if hashlib.sha256((source / path).read_bytes()).hexdigest() != digest:
                raise ValueError('Modified Lostelle habitat output: ' + path)
        return report
    acquired = json.loads((source / '.source-acquired.json').read_text())
    if acquired['commit'] != PIN:
        raise ValueError('Unexpected source revision')
    expected = dict(acquired['sha256'])
    for layer in PRIOR + ['english-text', 'special-ball', 'route131-sea-access']:
        expected.update(json.loads((source / ('.journey-' + layer)).read_text())['prepared_sha256'])
    paths = ['src/data/wild_encounters.json', 'include/journey_wild_data.h', 'include/journey_habitat_data.h']
    preserved_paths = ['data/maps/ThreeIsland_BerryForest_Frlg/scripts.inc', 'src/journey_wild.c',
                       'src/journey_habitats.c', 'src/pokedex_area_screen.c', 'src/script_pokemon_util.c']
    original, preserved = {}, {}
    for path in paths + preserved_paths:
        digest = hashlib.sha256((source / path).read_bytes()).hexdigest()
        if digest != expected[path]:
            raise ValueError('Unreviewed Lostelle habitat input: ' + path)
        (original if path in paths else preserved)[path] = digest
    ecology = copy.deepcopy(json.loads((source / '.journey-ecology').read_text()))
    habitats = {h['section']: h for h in ecology['locations_data']}
    forest, mountain = [habitats[s] for s in ['MAPSEC_BERRY_FOREST', 'MAPSEC_MT_PYRE']]
    old_families = {f['root']: f for h in [forest, mountain] for f in h['families']}
    assert 96 in {f['root'] for f in mountain['families']}
    assert 451 in {f['root'] for f in forest['families']}
    for habitat, outgoing, incoming in [(forest, 451, 96), (mountain, 96, 451)]:
        habitat['families'] = sorted([f for f in habitat['families'] if f['root'] != outgoing]
                                    + [old_families[incoming]], key=lambda f: f['root'])
        assert len(habitat['families']) == habitat['family_count']
    catalog = json.loads((Path(__file__).parent / 'catalog_metadata.json').read_text())
    species = {int(k): v for k, v in catalog['species'].items()}
    by_map = {m: h for h in [forest, mountain] for m in h['maps']}
    encounters = json.loads((source / paths[0]).read_text())
    pools = {(p['map'], p['area']): p for p in ecology['pools']}
    for row in encounters['wild_encounter_groups'][0]['encounters']:
        if row['map'] not in by_map:
            continue
        habitat = by_map[row['map']]
        for area, field in enumerate(FIELDS):
            if field not in row or field in ['water_mons', 'fishing_mons']:
                continue
            rates = (LAND_RATES if field in ['land_mons', 'hidden_mons'] else WATER_RATES)[:len(row[field]['mons'])]
            roots = weighted_slots(habitat['families'][:len(rates)], rates)
            for mon, root in zip(row[field]['mons'], roots):
                mon['species'] = species[root]['name']
            ecology['field_slots'][row['map']][field]['slots'] = [species[r]['name'] for r in roots]
            pools[row['map'], area]['roots'] = weighted_slots(habitat['families'], LAND_RATES)
        ecology['map_species'][row['map']] = sorted(m['id'] for f in habitat['families'] for m in f['species'])
    wild = (source / paths[1]).read_text()
    for (m, area), pool in pools.items():
        if m not in by_map or area in [1, 3]:
            continue
        line = '{' + ', '.join([m, str(area), str(len(pool['roots'])),
                '{' + ', '.join(species[r]['name'] for r in pool['roots']) + '}']) + '}'
        wild, count = re.subn(r'^\{' + m + ', ' + str(area) + r',[^\n]+\}(?=,?$)',
                              lambda _: line, wild, flags=re.M)
        assert count == 1, (m, area)
    dex = (source / paths[2]).read_text()
    for m in by_map:
        ids = ecology['map_species'][m]
        line = '{' + m + ', ' + str(len(ids)) + ', {' + ', '.join(species[i]['name'] for i in ids) + '}}'
        dex, count = re.subn(r'^\{' + m + r',[^\n]+\}(?=,?$)', lambda _: line, dex, flags=re.M)
        assert count == 1, m
    roots = [f['root'] for h in ecology['locations_data'] for f in h['families']]
    assert len(roots) == len(set(roots)) == 444
    outputs = dict(zip(paths, [(json.dumps(encounters, indent=2) + '\n').encode(), wild.encode(), dex.encode()]))
    report = dict(status='lostelle_unique_family_habitats_candidate', source_commit=PIN,
        swapped_roots=[96, 451], locations_data=ecology['locations_data'], map_species=ecology['map_species'],
        pools=ecology['pools'], field_slots=ecology['field_slots'],
        original_hypno_rescue_script_preserved=True, evolution_and_level_rules_preserved=True,
        aquatic_encounters_preserved=True, original_sha256=original, preserved_native_sha256=preserved,
        prepared_sha256={p: hashlib.sha256(v).hexdigest() for p, v in outputs.items()}, full_campaign_validated=False)
    for path, raw in outputs.items():
        (source / path).write_bytes(raw)
    marker.write_text(json.dumps(report, indent=2) + '\n')
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    print(json.dumps(prepare(parser.parse_args().source), indent=2))
