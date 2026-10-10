"""Open the sea-level reef east of Ever Grande's original waterfall approach."""
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
    layouts = json.loads((source / 'data/layouts/layouts.json').read_text())['layouts']
    layout = next(l for l in layouts if l['id'] == 'LAYOUT_EVER_GRANDE_CITY')
    path = layout['blockdata_filepath']
    original = (source / path).read_bytes()
    assert hashlib.sha256(original).hexdigest() == expected[path]
    values = list(struct.unpack('<3200H', original))
    # Remove complete reef formations below the shore; no mountain, upper pool,
    # waterfall, event coordinate or League gate is part of these rectangles.
    patches = [[24, 72, 32, 80], [24, 70, 28, 72]]
    changed = []
    for x0, y0, x1, y1 in patches:
        for y in range(y0, y1):
            for x in range(x0, x1):
                i = y * 40 + x
                if values[i] != 0x1170:
                    changed.append(dict(x=x, y=y, before=values[i], after=0x1170))
                    values[i] = 0x1170
    preserved = {}
    for p in ['data/layouts/layouts.json', 'data/maps/EverGrandeCity/map.json', 'data/maps/EverGrandeCity/scripts.inc',
              'src/journey_campaign_gates.c', 'src/journey_gym_scaling.c']:
        digest = hashlib.sha256((source / p).read_bytes()).hexdigest()
        assert digest == expected[p]
        preserved[p] = digest
    raw = struct.pack('<3200H', *values)
    result = dict(layer=LAYER, original_sha256={path: expected[path]},
                  prepared_sha256={path: hashlib.sha256(raw).hexdigest()},
                  preserved_native_sha256=preserved, changed_tiles=changed,
                  patches=patches, waterfall_and_upper_pool_preserved=True,
                  map_events_and_league_gates_preserved=True)
    (source / path).write_bytes(raw)
    marker.write_text(json.dumps(result, indent=2) + '\n')
    return result

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', required=True)
    print(json.dumps(prepare(p.parse_args().source), indent=2))
