"""Reproduce all ocean overlays from pinned original files and compare hashes.

Downloads source-only inputs to a temporary directory, never a full ROM, and
does not overwrite the candidate. This complements the real mGBA tests.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import tempfile
import urllib.request

from prepare_crossing import prepare as crossing_prepare
from prepare_worldsea import prepare as eastern_prepare
from prepare_westsea import prepare as western_prepare
from prepare_region_state import prepare as regional_prepare


def verify(source, output):
    source = Path(source)
    acquired = json.loads((source / '.source-acquired.json').read_text())
    markers = ['.journey-hoenn-crossing', '.journey-worldsea', '.journey-westsea', '.journey-region-state']
    reports = [json.loads((source / p).read_text()) for p in markers]
    original_paths = sorted({p for r in reports for p in r['original_sha256'] if p in acquired['sha256']})
    expected = {}
    for r in reports: expected.update(r['prepared_sha256'])
    with tempfile.TemporaryDirectory(prefix='hoenn-world-repro-', dir='/tmp') as directory:
        fresh = Path(directory)
        def fetch(path):
            url = f'https://raw.githubusercontent.com/eonlynx/pokecrossroads/{acquired["commit"]}/{path}'
            with urllib.request.urlopen(url, timeout=30) as response: raw = response.read()
            if hashlib.sha256(raw).hexdigest() != acquired['sha256'][path]:
                raise ValueError('Original source mismatch: ' + path)
            destination = fresh / path; destination.parent.mkdir(parents=True, exist_ok=True); destination.write_bytes(raw)
        with ThreadPoolExecutor(max_workers=4) as pool: list(pool.map(fetch, original_paths))
        (fresh / '.source-acquired.json').write_text(json.dumps(dict(commit=acquired['commit'],
            sha256={p: acquired['sha256'][p] for p in original_paths})))
        crossing_prepare(fresh)
        eastern_prepare(fresh)
        western = western_prepare(fresh)
        assert western_prepare(fresh) == json.loads(json.dumps(western))
        regional = regional_prepare(fresh)
        assert regional_prepare(fresh) == regional
        for path, digest in expected.items():
            if hashlib.sha256((fresh / path).read_bytes()).hexdigest() != digest:
                raise ValueError('Fresh overlay mismatch: ' + path)
            if hashlib.sha256((source / path).read_bytes()).hexdigest() != digest:
                raise ValueError('Candidate mismatch: ' + path)
        event_checks = 0
        for r in reports:
            for name, events in r.get('preserved_event_sha256', {}).items():
                actual = json.loads((fresh / f'data/maps/{name}/map.json').read_text())
                for key, digest in events.items():
                    assert hashlib.sha256(json.dumps(actual.get(key, []), sort_keys=True).encode()).hexdigest() == digest, (name, key)
                    event_checks += 1
        # Check every reciprocal edge and that parallel seams don't overlap.
        groups = json.loads((fresh / 'data/maps/map_groups.json').read_text())
        names = [n for group in groups['group_order'] for n in groups[group] if (fresh / f'data/maps/{n}/map.json').exists()]
        maps = {n: json.loads((fresh / f'data/maps/{n}/map.json').read_text()) for n in names}
        by_id = {m['id']: m for m in maps.values()}
        layouts = {l['id']: l for l in json.loads((fresh / 'data/layouts/layouts.json').read_text())['layouts']}
        opposite = dict(up='down', down='up', left='right', right='left')
        edge_count = 0
        for m in maps.values():
            spans = {d: [] for d in opposite}
            for c in m.get('connections') or []:
                other = by_id.get(c['map'])
                if other is None or c['direction'] not in opposite: continue
                assert any(back['map'] == m['id'] and back['direction'] == opposite[c['direction']]
                           and back['offset'] == -c['offset'] for back in other.get('connections') or []), (m['name'], c)
                axis = 'width' if c['direction'] in ['up', 'down'] else 'height'
                low = max(0, c['offset']); high = min(layouts[m['layout']][axis], c['offset'] + layouts[other['layout']][axis])
                for old_low, old_high in spans[c['direction']]:
                    assert high <= old_low or low >= old_high, ('Overlapping seam', m['name'], c)
                spans[c['direction']].append((low, high)); edge_count += 1
        result = dict(passed=True, source_commit=acquired['commit'], original_files=len(original_paths),
            prepared_files=len(expected), reciprocal_edges_checked=edge_count, idempotence=True,
            preserved_event_groups_checked=event_checks,
            full_story_validated=False, prepared_sha256=expected)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n')
    for name, r in zip(['crossing-preparation', 'eastern-ocean-preparation', 'western-ocean-preparation', 'regional-state-preparation'], reports):
        (output.parent / (name + '.json')).write_text(json.dumps(r, indent=2) + '\n')
    print(f'Reproduction passed: {len(expected)} files; {edge_count} reciprocal edges; no overlapping seams')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=Path('mods/hoenn/integration-validation/world-reproduction.json'))
    args = parser.parse_args(); verify(args.source, args.output)
