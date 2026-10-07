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
from prepare_east_coast import prepare as coast_prepare
from prepare_gym_scaling import prepare as gym_prepare
from prepare_campaign_gates import prepare as campaign_prepare
from prepare_team_stories import prepare as stories_prepare
from prepare_free_access import prepare as access_prepare
from prepare_blue_gym import prepare as blue_prepare
from prepare_road_access import prepare as road_prepare
from prepare_mach_bike import prepare as bike_prepare
from prepare_yellow_stairs import prepare as yellow_prepare


def verify(source, output):
    source = Path(source)
    acquired = json.loads((source / '.source-acquired.json').read_text())
    markers = ['.journey-hoenn-crossing', '.journey-worldsea', '.journey-westsea', '.journey-region-state']
    if (source / '.journey-east-coast').exists(): markers.append('.journey-east-coast')
    if (source / '.journey-gym-scaling').exists(): markers.append('.journey-gym-scaling')
    if (source / '.journey-campaign-gates').exists(): markers.append('.journey-campaign-gates')
    if (source / '.journey-team-stories').exists(): markers.append('.journey-team-stories')
    if (source / '.journey-free-access').exists(): markers.append('.journey-free-access')
    if (source / '.journey-blue-gym').exists(): markers.append('.journey-blue-gym')
    if (source / '.journey-road-access').exists(): markers.append('.journey-road-access')
    if (source / '.journey-mach-bike').exists(): markers.append('.journey-mach-bike')
    if (source / '.journey-yellow-stairs').exists(): markers.append('.journey-yellow-stairs')
    reports = [json.loads((source / p).read_text()) for p in markers]
    original_paths = sorted({p for r in reports for p in (r['original_sha256'] | r.get('input_sha256', {})) if p in acquired['sha256']})
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
        if '.journey-east-coast' in markers:
            coast = coast_prepare(fresh); assert coast_prepare(fresh) == json.loads(json.dumps(coast))
        if '.journey-gym-scaling' in markers:
            gym = gym_prepare(fresh); assert gym_prepare(fresh) == gym
        if '.journey-campaign-gates' in markers:
            campaign = campaign_prepare(fresh); assert campaign_prepare(fresh) == campaign
        if '.journey-team-stories' in markers:
            stories = stories_prepare(fresh); assert stories_prepare(fresh) == json.loads(json.dumps(stories))
        if '.journey-free-access' in markers:
            access=access_prepare(fresh);assert access_prepare(fresh)==access
        if '.journey-blue-gym' in markers:
            blue=blue_prepare(fresh);assert blue_prepare(fresh)==blue
        if '.journey-road-access' in markers:
            road=road_prepare(fresh);assert road_prepare(fresh)==road
        if '.journey-mach-bike' in markers:
            bike=bike_prepare(fresh);assert bike_prepare(fresh)==bike
        if '.journey-yellow-stairs' in markers:
            yellow=yellow_prepare(fresh);assert yellow_prepare(fresh)==yellow
        for path, digest in expected.items():
            if hashlib.sha256((fresh / path).read_bytes()).hexdigest() != digest:
                raise ValueError('Fresh overlay mismatch: ' + path)
            if hashlib.sha256((source / path).read_bytes()).hexdigest() != digest:
                raise ValueError('Candidate mismatch: ' + path)
        event_checks = 0
        for r in reports:
            for name, events in r.get('preserved_event_sha256', {}).items():
                actual = json.loads((fresh / f'data/maps/{name}/map.json').read_text())
                for later in reversed(reports):
                    for change in reversed(later.get('event_changes',[])):
                        if change['map']==name:
                            if 'path' in change:
                                node=actual
                                for key in change['path'][:-1]:node=node[key]
                                key=change['path'][-1]
                                assert node[key]==change['after'], ('Unexpected event field',name,change['path'])
                                node[key]=change['before']
                            else:
                                assert actual==change['after'], ('Unexpected event modification',name)
                                actual=change['before']
                for key, digest in events.items():
                    values = actual.get(key, [])
                    # Later overlays append guides, opponents and one casino
                    # warp. Match a prefix to retain native implicit local IDs.
                    assert any(hashlib.sha256(json.dumps(values[:n],sort_keys=True).encode()).hexdigest()==digest
                               for n in range(len(values)+1)), (name,key)
                    event_checks += 1
        # Check every reciprocal edge and that parallel seams don't overlap.
        groups = json.loads((fresh / 'data/maps/map_groups.json').read_text())
        names = [n for group in groups['group_order'] for n in groups[group] if (fresh / f'data/maps/{n}/map.json').exists()]
        maps = {n: json.loads((fresh / f'data/maps/{n}/map.json').read_text()) for n in names}
        by_id = {m['id']: m for m in maps.values()}
        layouts = {l['id']: l for l in json.loads((fresh / 'data/layouts/layouts.json').read_text())['layouts']}
        opposite = dict(up='down', down='up', left='right', right='left')
        edge_count = 0
        ocean_maps={name for report in reports for name in report.get('connections',{})}
        for m in maps.values():
            if m['name'] not in ocean_maps: continue
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
        eastern_connected = None
        if '.journey-east-coast' in markers:
            pending = ['MAP_JOURNEYWORLDSEA00']; visited=set()
            while pending:
                ident=pending.pop()
                if ident in visited: continue
                visited.add(ident)
                if ident in by_id:
                    pending.extend(c['map'] for c in by_id[ident].get('connections') or [] if c['direction'] in opposite)
            required={f'MAP_ROUTE{n}' for n in range(124,132)} | {'MAP_ROUTE19','MAP_JOURNEYWORLDSEA06','MAP_JOURNEYWORLDSEA07'}
            assert required <= visited, ('Disconnected eastern sea',required-visited)
            eastern_connected=True
        result = dict(passed=True, source_commit=acquired['commit'], original_files=len(original_paths),
            prepared_files=len(expected), reciprocal_edges_checked=edge_count, idempotence=True,
            preserved_event_groups_checked=event_checks,
            entire_eastern_sea_connected=eastern_connected,
            full_story_validated=False, prepared_sha256=expected)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n')
    for name, r in zip(['crossing-preparation', 'eastern-ocean-preparation', 'western-ocean-preparation', 'regional-state-preparation', 'east-coast-preparation', 'gym-scaling-preparation', 'campaign-gates-preparation', 'team-stories-preparation', 'free-access-preparation', 'blue-gym-preparation', 'road-access-preparation', 'mach-bike-preparation', 'yellow-stairs-preparation'], reports):
        (output.parent / (name + '.json')).write_text(json.dumps(r, indent=2) + '\n')
    print(f'Reproduction passed: {len(expected)} files; {edge_count} reciprocal edges; no overlapping seams')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=Path('mods/hoenn/integration-validation/world-reproduction.json'))
    args = parser.parse_args(); verify(args.source, args.output)
