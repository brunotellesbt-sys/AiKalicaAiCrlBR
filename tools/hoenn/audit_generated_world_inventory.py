"""Inventory the final generated world; this is scope, not visual/native proof.

Collapse every prepared layer over the acquired upstream hashes, then compare
actual current map/layout/event files. Original spatial inputs are independently
hash-checked, so a later layer restoring an upstream file is not a false edit.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import tarfile
import urllib.request


ROOT = Path(__file__).resolve().parents[2]
SPATIAL_PREFIXES = ('data/maps/', 'data/layouts/', 'data/tilesets/', 'src/data/tilesets/')
SCRIPT_LABEL = re.compile(r'^(\w+)::?\s*$', re.M)
TOKEN = re.compile(r'\b[A-Za-z_]\w*\b')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def fetch_spatial_inputs(source, output):
    acquired = read_json(Path(source) / '.source-acquired.json')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    wanted = {p for p in acquired['sha256'] if p.startswith(SPATIAL_PREFIXES)}
    kept = {}
    url = 'https://codeload.github.com/' + acquired['repository'] + '/tar.gz/' + acquired['commit']
    with urllib.request.urlopen(url, timeout=50) as response, tarfile.open(fileobj=response, mode='r|gz') as archive:
        for member in archive:
            if not member.isfile() or '/' not in member.name:
                continue
            name = member.name.split('/', 1)[1]
            if name not in wanted:
                continue
            raw = archive.extractfile(member).read()
            assert digest(raw) == acquired['sha256'][name], name
            path = output / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            kept[name] = digest(raw)
    assert set(kept) == wanted
    metadata = dict(repository=acquired['repository'], commit=acquired['commit'], sha256=kept)
    (output / '.original-spatial-inputs.json').write_text(json.dumps(metadata, indent=2) + '\n')


def collapse(source, layers):
    acquired = read_json(source / '.source-acquired.json')
    final = dict(acquired['sha256'])
    owners = defaultdict(list)
    for layer in layers:
        marker = read_json(source / ('.journey-' + layer))
        for name, sha in marker['prepared_sha256'].items():
            final[name] = sha
            owners[name].append(layer)
    for name in owners:
        assert digest((source / name).read_bytes()) == final[name], ('Prepared source differs', name)
    changed = {p: sha for p, sha in final.items() if acquired['sha256'].get(p) != sha}
    restored = sorted(p for p in owners if p in acquired['sha256'] and p not in changed)
    return acquired, final, changed, owners, restored


def bounds(points):
    return ([min(p[0] for p in points), min(p[1] for p in points),
             max(p[0] for p in points), max(p[1] for p in points)] if points else None)


def terrain_delta(source, upstream, layout, old_layout, changed):
    path = layout['blockdata_filepath']
    result = dict(changed=path in changed, changed_cells=0, changed_bounds=None)
    if path not in changed:
        return result
    width, height = layout['width'], layout['height']
    new = (source / path).read_bytes()
    assert len(new) == width * height * 2, path
    old_path = upstream / path
    if old_layout is None or not old_path.exists():
        return result | dict(changed_cells=width * height,
                             changed_bounds=[0, 0, width-1, height-1], created_surface=True)
    old = old_path.read_bytes()
    if (width, height) != (old_layout['width'], old_layout['height']):
        return result | dict(changed_cells=None, changed_bounds=[0, 0, width-1, height-1],
                             original_dimensions=[old_layout['width'], old_layout['height']],
                             dimensions_changed=True)
    points = [(i//2 % width, i//2 // width) for i in range(0, len(new), 2)
              if old[i:i+2] != new[i:i+2]]
    return result | dict(changed_cells=len(points), changed_bounds=bounds(points))


def category(name, mapping):
    kind = mapping['map_type']
    if kind == 'MAP_TYPE_UNDERWATER': return 'underwater'
    if kind == 'MAP_TYPE_UNDERGROUND': return 'cave'
    if name.endswith('Gym') or name == 'JourneyOakBasementGym': return 'gym'
    if 'PWT' in name: return 'stadium'
    if any(term in name for term in ('Harbor', '_Port_', 'Shipyard')): return 'port'
    if kind == 'MAP_TYPE_OCEAN_ROUTE': return 'marine_route'
    if kind == 'MAP_TYPE_ROUTE': return 'land_route'
    if kind in ('MAP_TYPE_TOWN', 'MAP_TYPE_CITY'): return 'town_city'
    if any(term in name for term in ('Galactic', 'Rocket', 'Sanctuary', 'Paradox')): return 'event_interior'
    return 'interior'


def bank_folders(source):
    headers = (source / 'src/data/tilesets/headers.h').read_text()
    metas = (source / 'src/data/tilesets/metatiles.h').read_text()
    result = {}
    for name, body in re.findall(r'const struct Tileset (\w+)\s*=\s*\{(.*?)\};', headers, re.S):
        symbol = re.search(r'\.metatiles\s*=\s*(\w+)', body)
        if not symbol: continue
        path = re.search(r'\b' + re.escape(symbol[1]) + r'\[\].*?"([^"]+)"', metas)
        if path: result[name] = Path(path[1]).parent.as_posix()
    return result


def shared_script_dependencies(source, changed):
    """Find changed shared labels reachable from unchanged map-local scripts.

    This reports conservative event review scope. It does not certify runtime
    feasibility, nor classify shared text/command changes as terrain changes.
    """
    files = [*sorted((source / 'data/scripts').rglob('*.inc')),
             *sorted((source / 'data/maps').glob('*.inc'))]
    label_file, references = {}, {}
    for path in files:
        name = path.relative_to(source).as_posix()
        text = path.read_text()
        labels = list(SCRIPT_LABEL.finditer(text))
        for index, label in enumerate(labels):
            label_file[label[1]] = name
            end = labels[index+1].start() if index+1 < len(labels) else len(text)
            code = '\n'.join(line.split('@', 1)[0] for line in text[label.end():end].splitlines()
                             if '.string' not in line)
            references[label[1]] = set(TOKEN.findall(code))
    affected = {label: {name} for label, name in label_file.items() if name in changed}
    while True:
        added = False
        for label, refs in references.items():
            reach = set().union(*(affected.get(ref, set()) for ref in refs)) if refs else set()
            if reach - affected.get(label, set()):
                affected.setdefault(label, set()).update(reach)
                added = True
        if not added: break
    return affected


def inventory(source, upstream, layers):
    source, upstream = Path(source).resolve(), Path(upstream).resolve()
    acquired, final, changed, owners, restored = collapse(source, layers)
    spatial = read_json(upstream / '.original-spatial-inputs.json')
    assert spatial['commit'] == acquired['commit']
    assert spatial['repository'] == acquired['repository']
    for name, sha in spatial['sha256'].items():
        assert sha == acquired['sha256'][name] == digest((upstream / name).read_bytes()), name
    layouts = {row['id']: row for row in read_json(source / 'data/layouts/layouts.json')['layouts']}
    original_layouts = {row['id']: row for row in read_json(upstream / 'data/layouts/layouts.json')['layouts']}
    folders = bank_folders(source)
    bank_changes = {name: sorted(p for p in changed if p.startswith(folder + '/'))
                    for name, folder in folders.items()}
    changed_shared = shared_script_dependencies(source, changed)
    maps, indirect = [], []
    for path in sorted((source / 'data/maps').glob('*/map.json')):
        name = path.parent.name
        relative = path.relative_to(source).as_posix()
        mapping = read_json(path)
        layout = layouts[mapping['layout']]
        original = read_json(upstream / relative) if relative in acquired['sha256'] else None
        old_layout = original_layouts.get(mapping['layout'])
        local = sorted(p for p in changed if p.startswith('data/maps/' + name + '/'))
        paths = sorted(set(local + [p for p in (layout['blockdata_filepath'], layout['border_filepath']) if p in changed]))
        metadata_changed = old_layout != layout
        header_fields = sorted(key for key in mapping if original is None or mapping[key] != original.get(key))
        scripts = sorted(path.parent.glob('*.inc'))
        tokens = set(TOKEN.findall(json.dumps(mapping)))
        for script in scripts: tokens.update(TOKEN.findall(script.read_text()))
        shared = sorted(set().union(*(changed_shared.get(token, set()) for token in tokens)))
        banks = {field: layout[field] for field in ('primary_tileset', 'secondary_tileset')}
        dependencies = sorted(set().union(*(set(bank_changes.get(bank, [])) for bank in banks.values())))
        row = dict(map=name, map_id=mapping['id'], category=category(name, mapping),
                   type=mapping['map_type'], created=original is None,
                   dimensions=[layout['width'], layout['height']], layout=mapping['layout'],
                   layout_metadata_changed=metadata_changed, tilesets=banks,
                   layout_definition_source='data/layouts/layouts.json',
                   layout_registry_last_layer=owners['data/layouts/layouts.json'][-1],
                   changed_layout_fields=sorted(k for k in layout if old_layout is None or layout[k] != old_layout.get(k)),
                   source_paths=paths, changed_header_fields=header_fields,
                   terrain=terrain_delta(source, upstream, layout, old_layout, changed),
                   layers=[layer for layer in layers if any(layer in owners[p] for p in paths)],
                   shared_changed_scripts=shared,
                   potentially_changed_tileset_files=dependencies,
                   connections=mapping.get('connections') or [],
                   warps=[[e['x'], e['y'], e['dest_map'], e['dest_warp_id']] for e in mapping.get('warp_events', [])],
                   event_counts={key:len(mapping.get(key, [])) for key in ('object_events', 'warp_events', 'coord_events', 'bg_events')})
        if paths or metadata_changed:
            row['review_scope'] = 'direct'
            row['script_only'] = not row['terrain']['changed'] and not metadata_changed and set(header_fields) <= {'object_events','coord_events','bg_events','warp_events'}
            maps.append(row)
        elif shared or dependencies:
            row['review_scope'] = 'indirect_shared_dependency'
            row['note'] = 'A changed shared bank/label is a review dependency, not proof that a used tile or runtime scene changed.'
            indirect.append(row)
    tilesets = [dict(symbol=name, folder=folders[name], changed_files=paths,
                     consumers=[row['map'] for row in maps+indirect if name in row['tilesets'].values()])
                for name, paths in sorted(bank_changes.items()) if paths]
    return dict(kind='generated-world-inventory', inventory_only=True,
                visual_review_performed=False, native_validation_performed=False,
                source_commit=acquired['commit'], source_repository=acquired['repository'],
                source_rom_sha256=digest((source/'pokeemerald.gba').read_bytes()),
                layers=layers, final_prepared_source_files=len(final),
                final_changed_source_files=len(changed), layer_touched_but_upstream_restored_files=restored,
                total_current_maps=len(list((source/'data/maps').glob('*/map.json'))),
                direct_map_count=len(maps), direct_category_counts=dict(sorted(Counter(r['category'] for r in maps).items())),
                created_maps=sum(r['created'] for r in maps), terrain_maps=sum(r['terrain']['changed'] for r in maps),
                script_or_event_only_maps=sum(r['script_only'] for r in maps),
                indirect_shared_dependency_maps=len(indirect),
                upstream_spatial_files_verified=len(spatial['sha256']),
                maps=maps, indirect_maps=indirect, changed_tilesets=tilesets,
                changed_shared_script_files=sorted(p for p in changed if p.startswith('data/scripts/')),
                changed_runtime_sources=sorted(p for p in changed if p.startswith('src/') and p.endswith(('.c','.h'))),
                changed_files=[dict(file=p, sha256=sha, original_sha256=acquired['sha256'].get(p),
                                    last_layer=owners[p][-1], layers=owners[p]) for p, sha in sorted(changed.items())])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--upstream', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--release-manifest', type=Path, default=ROOT/'mods/hoenn/versions/versions.json')
    parser.add_argument('--append-layer', action='append', default=[])
    parser.add_argument('--fetch-upstream', action='store_true')
    args = parser.parse_args()
    if args.fetch_upstream: fetch_spatial_inputs(args.source, args.upstream)
    layers = read_json(args.release_manifest)['integration_layers'] + args.append_layer
    report = inventory(args.source, args.upstream, layers)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({key:report[key] for key in ('direct_map_count', 'direct_category_counts',
          'created_maps', 'terrain_maps', 'script_or_event_only_maps', 'indirect_shared_dependency_maps')}, indent=2))
