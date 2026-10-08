"""Audit static map destinations; does not certify collision or story reachability."""
import argparse
import hashlib
import json
from pathlib import Path


def audit(source):
    source = Path(source)
    paths = sorted((source / 'data/maps').glob('*/map.json'))
    maps = {d['id']: d for p in paths for d in [json.loads(p.read_text())]}
    layouts = {d['id']: d for d in json.loads((source / 'data/layouts/layouts.json').read_text())['layouts']}
    homes = json.loads((source / '.journey-birth').read_text())['homes']
    contexts = {h[k]: h for h in homes if h['original_map'] != h['living_map']
                for k in ('bedroom_map', 'living_map')}
    errors, dynamic, aliases, bounds_review = [], [], [], []
    warps = connections = 0
    for map_id, data in maps.items():
        layout = layouts[data['layout']]
        for index, warp in enumerate(data.get('warp_events', [])):
            warps += 1
            if not (0 <= warp['x'] < layout['width'] and 0 <= warp['y'] < layout['height']):
                bounds_review.append(dict(map=map_id, warp=index, x=warp['x'], y=warp['y'],
                                          width=layout['width'], height=layout['height']))
            target = warp['dest_map']
            if target == 'MAP_DYNAMIC':
                dynamic.append(dict(map=map_id, warp=index))
                continue
            home = contexts.get(map_id)
            if home and target == home['original_map']:
                target = home['living_map']
                aliases.append(dict(map=map_id, warp=index, original=home['original_map'], effective=target))
            destination = maps.get(target)
            try:
                warp_id = int(warp['dest_warp_id'])
            except ValueError:
                errors.append(dict(map=map_id, warp=index, error='unresolved warp constant'))
                continue
            if destination is None or not 0 <= warp_id < len(destination.get('warp_events', [])):
                errors.append(dict(map=map_id, warp=index, target=target, target_warp=warp_id, error='missing destination'))
        for connection in data.get('connections') or []:
            connections += 1
            if connection['map'] not in maps:
                errors.append(dict(map=map_id, connection=connection, error='missing connection map'))
    # Bind the audit to source inputs and the candidate without modifying either.
    digest = hashlib.sha256()
    inputs = paths + [source / 'data/layouts/layouts.json', source / '.journey-birth', source / 'src/journey_family.c']
    for path in sorted(inputs):
        digest.update(str(path.relative_to(source)).encode() + b'\0' + path.read_bytes() + b'\0')
    result = dict(passed=not errors, maps=len(maps), warps=warps, connections=connections,
                  conditional_home_destinations=aliases, dynamic_destinations_not_statically_resolved=dynamic,
                  origin_bounds_requiring_runtime_review=bounds_review,
                  errors=errors, source_inputs_sha256=digest.hexdigest(),
                  scope='Passed checks cover destination map/warp indices and connection targets. Out-of-layout origins are reported separately: legacy scripted warps may be unused. Dynamic warps, collision, route design and full campaign reachability require runtime review.')
    rom = source / 'pokeemerald.gba'
    if rom.exists():
        result['rom_sha256'] = hashlib.sha256(rom.read_bytes()).hexdigest()
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = audit(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('passed', 'maps', 'warps', 'connections', 'errors')}))
    raise SystemExit(0 if result['passed'] else 1)
