"""Eleventh overlay: nonblocking Aqua patrols; bicycle quest gates retained.

Keep event IDs, visibility flags, dialogue and mission completion unchanged.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from prepare_crossing import PIN
from prepare_free_access import LAYERS


def prepare(source):
    source = Path(source)
    marker = source / '.journey-road-access'
    if marker.exists():
        result = json.loads(marker.read_text())
        for path, digest in result['prepared_sha256'].items():
            if hashlib.sha256((source / path).read_bytes()).hexdigest() != digest:
                raise ValueError('Modified road access output: ' + path)
        return result
    acquired = json.loads((source / '.source-acquired.json').read_text())
    assert acquired['commit'] == PIN
    expected = dict(acquired['sha256'])
    for layer in LAYERS + ['free-access', 'blue-gym']:
        expected.update(json.loads((source / f'.journey-{layer}').read_text())['prepared_sha256'])
    inputs, originals, outputs = {}, {}, {}

    def read(path):
        if path in outputs:
            return outputs[path]
        raw = (source / path).read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected[path]:
            raise ValueError('Unreviewed road input: ' + path)
        if path in acquired['sha256']:
            inputs[path] = acquired['sha256'][path]
        return raw

    def stage(path, body):
        if path not in originals:
            originals[path] = hashlib.sha256(read(path)).hexdigest()
        outputs[path] = body if isinstance(body, bytes) else body.encode()

    layouts = {l['id']: l for l in json.loads(read('data/layouts/layouts.json'))['layouts']}
    relocations, changes = [], []
    requests = {
        'Route110': [(f'Route110_EventScript_AquaGrunt{i}', 7, 79 + i) for i in range(1, 5)]
                    + [('0x0', 7, 84)],
        'Route119': [('Route119_EventScript_BridgeAquaGrunt1', 10, 32),
                     ('Route119_EventScript_BridgeAquaGrunt2', 10, 35)],
    }
    for name, moves in requests.items():
        path = f'data/maps/{name}/map.json'
        data = json.loads(read(path))
        layout = layouts[data['layout']]
        raw = read(layout['blockdata_filepath'])
        tiles = struct.unpack('<' + 'H' * (len(raw) // 2), raw)
        for label, x, y in moves:
            matches = [(i, o) for i, o in enumerate(data['object_events'])
                       if o['script'] == label and o['flag'] == f'FLAG_HIDE_ROUTE_{name[5:]}_TEAM_AQUA']
            assert len(matches) == 1, (name, label)
            i, obj = matches[0]
            tile = tiles[y * layout['width'] + x]
            assert not tile & 0xC00 and tile >> 12 == obj['elevation'], (name, x, y)
            assert not any((e['x'], e['y']) == (x, y) for key in
                           ['object_events', 'warp_events', 'coord_events', 'bg_events']
                           for e in data.get(key, [])), (name, x, y)
            before = [obj['x'], obj['y']]
            for key, value in [('x', x), ('y', y)]:
                changes.append(dict(map=name, path=['object_events', i, key], before=obj[key], after=value))
                obj[key] = value
            relocations.append(dict(map=name, local_id=i + 1, script=label, before=before, after=[x, y]))
        stage(path, json.dumps(data, indent=2) + '\n')
    for path, raw in outputs.items():
        (source / path).write_bytes(raw)
    result = dict(status='road_access_candidate_not_full_campaign_validation', source_commit=PIN,
                  cycling_gates='preserved_pending_bike_missions', relocations=relocations, event_changes=changes,
                  mission_flags_unchanged=True, snorlax_unchanged=True, requires_new_save=True,
                  full_story_validated=False, input_sha256=inputs, original_sha256=originals,
                  prepared_sha256={p: hashlib.sha256(raw).hexdigest() for p, raw in outputs.items()})
    marker.write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source), indent=2))
