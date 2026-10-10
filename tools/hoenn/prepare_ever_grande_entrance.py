"""Open Ever Grande's eastern reef and align the Fuchsia coastal connector."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

LAYER = 'ever-grande-entrance'

def prepare(source):
    source = Path(source)
    marker = source / ('.journey-' + LAYER)
    if marker.exists():
        result = json.loads(marker.read_text())
        for path, digest in (result['prepared_sha256'] | result['preserved_native_sha256']).items():
            assert hashlib.sha256((source / path).read_bytes()).hexdigest() == digest, path
        return result
    preceding = json.loads((source / '.journey-eastern-sea-union').read_text())
    expected = preceding['prepared_sha256'] | preceding['preserved_native_sha256']
    layout_data = json.loads((source / 'data/layouts/layouts.json').read_text())
    layouts = layout_data['layouts']
    layout = next(l for l in layouts if l['id'] == 'LAYOUT_EVER_GRANDE_CITY')
    path = layout['blockdata_filepath']
    original = (source / path).read_bytes()
    assert hashlib.sha256(original).hexdigest() == expected[path]
    values = list(struct.unpack('<3200H', original))
    # Remove complete reef formations below the shore; no mountain, upper pool,
    # waterfall, event coordinate or League gate is part of these rectangles.
    patches = [[24, 72, 32, 80], [24, 70, 28, 72], [22, 78, 24, 80]]
    changed = []
    for x0, y0, x1, y1 in patches:
        for y in range(y0, y1):
            for x in range(x0, x1):
                i = y * 40 + x
                if values[i] != 0x1170:
                    changed.append(dict(x=x, y=y, before=values[i], after=0x1170))
                    values[i] = 0x1170
    preserved = {}
    for p in ['data/maps/EverGrandeCity/map.json', 'data/maps/EverGrandeCity/scripts.inc',
              'src/journey_campaign_gates.c', 'src/journey_gym_scaling.c']:
        digest = hashlib.sha256((source / p).read_bytes()).hexdigest()
        assert digest == expected[p]
        preserved[p] = digest
    raw = struct.pack('<3200H', *values)
    outputs = {path: raw}
    # Route19 extends six tiles below the previous 14-high connector. Complete
    # that connector so both native cities fit above Hoenn without overlap.
    f = next(l for l in layouts if l['id'] == 'LAYOUT_JOURNEYFUCHSIASEA')
    fp = f['blockdata_filepath']
    old = (source / fp).read_bytes()
    assert hashlib.sha256(old).hexdigest() == expected[fp]
    sea = list(struct.unpack('<' + 'H' * (48 * 14), old))
    for y in range(14, 20):
        sea.extend(0x112B if x < 46 else [0x510,0x511,0x518,0x519][(y % 2) * 2 + x % 2] for x in range(48))
    f['height'] = 20
    outputs[fp] = struct.pack('<' + 'H' * len(sea), *sea)
    lp = 'data/layouts/layouts.json'
    assert hashlib.sha256((source / lp).read_bytes()).hexdigest() == expected[lp]
    outputs[lp] = (json.dumps(layout_data, indent=2) + '\n').encode()
    result = dict(layer=LAYER, original_sha256={p: expected[p] for p in outputs},
                  prepared_sha256={p: hashlib.sha256(v).hexdigest() for p,v in outputs.items()},
                  rectangle_overrides=[dict(map='JourneyFuchsiaSea',x=142,y=-20,width=48,height=20)],
                  preserved_native_sha256=preserved, changed_tiles=changed,
                  patches=patches, waterfall_and_upper_pool_preserved=True,
                  map_events_and_league_gates_preserved=True)
    for p, v in outputs.items(): (source / p).write_bytes(v)
    marker.write_text(json.dumps(result, indent=2) + '\n')
    return result

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', required=True)
    print(json.dumps(prepare(p.parse_args().source), indent=2))
