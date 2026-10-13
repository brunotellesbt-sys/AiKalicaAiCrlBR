"""Explicit PWT identities and reference teams; additions never hide originals."""
from pathlib import Path
import json
import re

HERE = Path(__file__).resolve().parent
ROLES = {'leader', 'captain', 'elite', 'champion', 'rival', 'guest'}

def load(path=None):
    path = Path(path) if path else HERE/'data/pwt-rosters.tsv'
    rows = []
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip() or line.startswith('#'):
            continue
        fields = line.split('|')
        assert len(fields) == 7, (number, 'Expected seven columns')
        generations, name, roles, original, added, game, portrait = fields
        token = re.sub(r'[^A-Z0-9]+', '_', name.upper()).strip('_')
        gens = [int(x) for x in generations.split(',')]
        original = original.split(',') if original else []
        added = added.split(',') if added else []
        row = dict(id=len(rows), key=token, name=name, generations=gens,
                   roles=roles.split(','), original=original, additions=added,
                   species=original+added, source_game=game, portrait=portrait,
                   reference_audit='pending')
        assert 0 < len(original) <= 6 and len(row['species']) == 6, (number, name, row['species'])
        assert set(row['roles']) <= ROLES and row['roles'], (number, roles)
        assert gens and all(0 <= x <= 9 for x in gens), (number, generations)
        assert all(re.fullmatch(r'[A-Z0-9_]+', x) for x in row['species']), (number, name)
        assert token not in {x['key'] for x in rows}, (number, 'Duplicate identity', name)
        rows.append(row)
    assert len(rows)+1 <= 256
    assert {g for row in rows for g in row['generations'] if g} == set(range(1,10))
    assert {'EREN','LUFFY','ASH'} <= {row['key'] for row in rows}
    references_path = HERE/'data/pwt/sources.json'
    if references_path.exists():
        references = {r['key']:r for r in json.loads(references_path.read_text())['party_references']}
        for row in rows:
            if row['key'] in references:
                ref = references[row['key']]
                team = [p['species'].removeprefix('SPECIES_') for p in ref['party']]
                assert row['original'] == team, (row['key'], 'Reference party mismatch')
                row['reference_audit'] = 'pinned_original_data'
                row['reference_commit'] = ref['commit']
                row['reference_path'] = ref['path']
    return rows

def eligible(rows, max_generation, generation=0):
    assert max_generation in (4,9) and 0 <= generation <= max_generation
    return [row for row in rows if row['generations'] == [0]
            or (generation in row['generations'] if generation else min(row['generations']) <= max_generation)]

if __name__ == '__main__':
    rows = load()
    print('Distinct catalog identities:',len(rows))
    for cap in (4,9):
        print('Version generation cap:',cap,'World Cup entrants:',len(eligible(rows,cap))+1)
        for gen in range(1,cap+1):
            print('Generation',gen,'entrants:',len(eligible(rows,cap,gen))+1)
