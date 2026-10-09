"""Keep the Sevii Surf channel open in Route 131's native Sky Pillar layout."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from prepare_crossing import PIN
from prepare_english_text import PRIOR

def prepare(source):
    source = Path(source)
    marker = source / '.journey-route131-sea-access'
    if marker.exists():
        report = json.loads(marker.read_text())
        for path, digest in (report['prepared_sha256'] | report['preserved_native_sha256']).items():
            if hashlib.sha256((source / path).read_bytes()).hexdigest() != digest:
                raise ValueError('Modified Route131 sea access output: ' + path)
        return report
    acquired = json.loads((source / '.source-acquired.json').read_text())
    if acquired['commit'] != PIN: raise ValueError('Unexpected source revision')
    expected = dict(acquired['sha256'])
    for layer in PRIOR + ['english-text', 'special-ball']:
        expected.update(json.loads((source / ('.journey-' + layer)).read_text())['prepared_sha256'])
    layouts = 'data/layouts/layouts.json'
    map_path = 'data/maps/Route131/map.json'
    script = 'data/maps/Route131/scripts.inc'
    base = 'data/layouts/Route131/map.bin'
    path = 'data/layouts/Route131_SkyPillar/map.bin'
    preserved = {}
    for p in [layouts, map_path, script, base, path]:
        digest = hashlib.sha256((source / p).read_bytes()).hexdigest()
        if digest != expected[p]: raise ValueError('Unreviewed Route131 sea access input: ' + p)
        if p != path: preserved[p] = digest
    definitions = {l['id']: l for l in json.loads((source / layouts).read_text())['layouts']}
    for key in ['LAYOUT_ROUTE131', 'LAYOUT_ROUTE131_SKY_PILLAR']:
        l = definitions[key]
        if (l['width'], l['height']) != (60, 40): raise ValueError('Unexpected Route131 dimensions')
    data = json.loads((source / map_path).read_text())
    for kind in ['object_events', 'warp_events', 'coord_events', 'bg_events']:
        if any(48 <= e['x'] < 60 and 33 <= e['y'] < 40 for e in data[kind]):
            raise ValueError('Channel intersects Route131 event')
    old = (source / path).read_bytes()
    tiles = list(struct.unpack('<2400H', old))
    opened = struct.unpack('<2400H', (source / base).read_bytes())
    modified = []
    for y in range(33, 40):
        for x in range(48, 60):
            i = y * 60 + x
            if tiles[i] != opened[i]: modified.append([x, y, tiles[i], opened[i]])
            tiles[i] = opened[i]
    if not modified: raise ValueError('Route131 alternate layout already open without marker')
    output = struct.pack('<2400H', *tiles)
    report = dict(status='route131_sky_pillar_sevii_channel_candidate', source_commit=PIN,
        modified_tiles=modified, channel=[48, 33, 60, 40],
        native_layout_switch_and_sky_pillar_entrance_preserved=True,
        all_events_and_map_connections_preserved=True, save_layout_unchanged=True,
        original_sha256={path: expected[path]}, preserved_native_sha256=preserved,
        prepared_sha256={path: hashlib.sha256(output).hexdigest()}, full_campaign_validated=False)
    (source / path).write_bytes(output)
    marker.write_text(json.dumps(report, indent=2) + '\n')
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source), indent=2))
