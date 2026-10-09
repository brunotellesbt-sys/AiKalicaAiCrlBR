"""Conservative static map-to-script traversal of fixed wild encounters.
Follows named script references, including shared scripts; does not evaluate
flags/conditions, dynamic jumps, macros or variable-selected species.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

LABEL = re.compile(r'^([A-Za-z_]\w*)::?\s*\n(.*?)(?=^[A-Za-z_]\w*::?\s*\n|\Z)', re.M | re.S)
TOKEN = re.compile(r'\b[A-Za-z_]\w*\b')
WILD = re.compile(r'^\s*setwildbattle\s+([A-Za-z_]\w*)\b', re.M)

def audit(source):
    source = Path(source)
    ecology = json.loads((source / '.journey-ecology').read_text())
    inputs = ['.journey-ecology']
    for layer in ['lostelle-habitats', 'tower-habitats']:
        marker = source / ('.journey-' + layer)
        if marker.exists():
            ecology.update(json.loads(marker.read_text()))
            inputs.append(marker.name)
    owned = {m['name']: dict(root=f['root'], family=f['name'], section=h['section'])
             for h in ecology['locations_data'] for f in h['families'] for m in f['species']}
    blocks, duplicates = {}, []
    paths = sorted(set((source / 'data/maps').glob('*/scripts.inc')) | set((source / 'data/scripts').glob('*.inc')))
    for path in paths:
        for name, body in LABEL.findall(path.read_text()):
            if name in blocks: duplicates.append(name)
            blocks[name] = (path.relative_to(source).as_posix(), body)
    # Strip comments per line, not the rest of a multi-line block.
    clean = {n: '\n'.join(line.split('@', 1)[0] for line in b.splitlines()) for n, (_, b) in blocks.items()}
    edges = {n: sorted(set(TOKEN.findall(b)) & blocks.keys()) for n, b in clean.items()}
    callbacks = {}
    item_use = source / 'src/item_use.c'
    if item_use.exists() and 'ScriptContext_SetupScript(BattleFrontier_OutsideEast_EventScript_WaterSudowoodo);' in item_use.read_text():
        callbacks['BattleFrontier_OutsideEast'] = ['BattleFrontier_OutsideEast_EventScript_WaterSudowoodo']
        inputs.append('src/item_use.c')
    records, dynamic, unresolved = [], [], []
    maps = sorted((source / 'data/maps').glob('*/map.json'))
    for path in maps:
        data = json.loads(path.read_text())
        roots = {e['script'] for key in ['object_events', 'coord_events', 'bg_events'] for e in data.get(key, []) if e.get('script')}
        roots.add(path.parent.name + '_MapScripts')
        roots.update(callbacks.get(path.parent.name, []))
        pending = [(n, [n]) for n in sorted(roots) if n in blocks]
        unresolved += [dict(map=path.parent.name, script=n) for n in sorted(roots - blocks.keys()) if n != 'NULL']
        visited = set()
        while pending:
            name, route = pending.pop()
            if name in visited: continue
            visited.add(name)
            script_path, body = blocks[name]
            for species in sorted(set(WILD.findall(clean[name]))):
                if not species.startswith('SPECIES_'):
                    dynamic.append(dict(map=path.parent.name, script=name, operand=species))
                    continue
                family = owned.get(species)
                records.append(dict(map=path.parent.name, map_id=data['id'], section=data['region_map_section'],
                    script=name, path=script_path, script_chain=route, species=species,
                    ordinary_family=family, matches_random_habitat=None if family is None else family['section'] == data['region_map_section']))
            pending += [(n, route + [n]) for n in edges[name] if n not in visited]
    mismatches = [r for r in records if r['matches_random_habitat'] is False]
    report = dict(status='static_fixed_encounter_inventory', records=records, ordinary_habitat_mismatches=mismatches,
        dynamic_species=dynamic, unresolved_event_roots=unresolved, duplicate_label_names=sorted(set(duplicates)),
        source_selected_callbacks=callbacks, maps_scanned=len(maps), script_files_scanned=len(paths), conditions_and_flags_evaluated=False,
        native_event_reachability_verified=False, full_fixed_encounter_coverage=False,
        input_sha256={p: hashlib.sha256((source / p).read_bytes()).hexdigest() for p in inputs})
    if (source / 'pokeemerald.gba').exists(): report['rom_sha256'] = hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest()
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); report = audit(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(dict(records=len(report['records']), mismatches=len(report['ordinary_habitat_mismatches']),
               dynamic_species=len(report['dynamic_species']), unresolved_roots=len(report['unresolved_event_roots'])))
