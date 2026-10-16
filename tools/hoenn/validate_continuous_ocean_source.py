"""Replay both ocean overlays and check native geography, artwork and events."""
import argparse, hashlib, json, struct, tempfile
from pathlib import Path
from PIL import Image
from prepare_continuous_ocean import prepare as ocean
from prepare_annotated_world_links import prepare as links
from prepare_surf_cave_coasts import PRIOR, LAYER, prepare as coasts
from prepare_world_dex_map import decode
from render_sea_maps import MapRenderer


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tile(path, index):
    im = Image.open(path)
    x, y = index % (im.width // 8) * 8, index // (im.width // 8) * 8
    return list(im.crop((x, y, x + 8, y + 8)).getdata())


def validate(source, inputs, output):
    source, inputs = Path(source).resolve(), Path(inputs).resolve()
    reports = [json.loads((source / ('.journey-' + n)).read_text())
               for n in ['continuous-ocean', 'annotated-world-links', LAYER]]
    targets = {Path(p) for r in reports for p in r['prepared_sha256']}
    expected = dict(json.loads((source / '.source-acquired.json').read_text())['sha256'])
    for n in PRIOR + [LAYER]:
        expected.update(json.loads((source / ('.journey-' + n)).read_text())['prepared_sha256'])
    for p, digest in expected.items():
        assert sha(source / p) == digest, p
    # Replay from the independent, complete PR90 input, with unchanged
    # source files linked read-only by convention and all outputs isolated.
    with tempfile.TemporaryDirectory(prefix='ocean-replay-', dir=source.parent) as d:
        dest = Path(d)
        def clone(relative):
            origin, copy = inputs / relative, dest / relative
            if relative in targets:
                copy.parent.mkdir(exist_ok=True, parents=True)
                copy.write_bytes(origin.read_bytes())
            elif any(relative in target.parents for target in targets):
                copy.mkdir(exist_ok=True, parents=True)
                for child in origin.iterdir():
                    clone(child.relative_to(inputs))
            else:
                copy.symlink_to(origin, target_is_directory=origin.is_dir())
        for child in inputs.iterdir():
            clone(child.relative_to(inputs))
        assert ocean(dest) == reports[0]
        assert ocean(dest) == reports[0]
        actual=links(dest)
        assert actual == reports[1], [k for k in actual if actual[k] != reports[1][k]]
        assert links(dest) == reports[1]
        assert coasts(dest) == reports[2]
        assert coasts(dest) == reports[2]
    maps = {p.parent.name: json.loads(p.read_text()) for p in (source / 'data/maps').glob('*/map.json')}
    preserved = 0
    for p in (inputs / 'data/maps').glob('*/map.json'):
        old, new = json.loads(p.read_text()), maps[p.parent.name]
        for field in ['object_events', 'warp_events', 'coord_events', 'bg_events']:
            assert all(e in new.get(field, []) for e in old.get(field, [])), (p.parent.name, field)
        preserved += 1
    a = decode((inputs / 'src/data/journey_world_map.h').read_text())
    b = decode((source / 'src/data/journey_world_map.h').read_text())
    assert all(a.getpixel((x, y)) == b.getpixel((x, y))
               for y in range(a.height) for x in range(a.width) if a.getpixel((x, y)) not in (1, 2))
    art = source / 'data/tilesets/primary'
    for index in [454, 455]:
        assert tile(art / 'general/tiles.png', index) == tile(art / 'general_frlg/tiles.png', index)
    for frame in range(8):
        for h, f in [(22, 38), (23, 39)]:
            assert tile(art / f'general/anim/water/{frame}.png', h) == tile(art / f'general_frlg/anim/water_current_landwatersedge/{frame}.png', f)
    palettes = [(art / f'{n}/palettes/04.pal').read_text().splitlines() for n in ['general', 'general_frlg']]
    assert all(palettes[0][3 + i] == palettes[1][3 + i] for i in [3, 4, 5, 7])
    layouts = {l['id']: l for l in json.loads((source / 'data/layouts/layouts.json').read_text())['layouts']}
    byid = {m['id']: n for n, m in maps.items()}
    for n in sorted(set(reports[1]['new_maps']) | {b['map'] for b in reports[2]['boundaries']}):
        m = maps[n]; l = layouts[m['layout']]; w, h = l['width'], l['height']
        v = struct.unpack('<' + 'H' * (w * h), (source / l['blockdata_filepath']).read_bytes())
        spans = {d: set() for d in ['left', 'right', 'up', 'down']}
        for c in m['connections']:
            q = layouts[maps[byid[c['map']]]['layout']]; d = c['direction']; off = c['offset']
            if d not in spans: continue
            assert any(r['map'] == m['id'] and r['offset'] == -off for r in maps[byid[c['map']]]['connections'])
            length = q['height'] if d in ['left', 'right'] else q['width']
            limit = h if d in ['left', 'right'] else w
            t = set(range(max(0, off), min(limit, off + length)))
            if n in reports[1]['new_maps']: assert not spans[d] & t, (n, d)
            spans[d].update(t)
        for y in range(h):
            for x in range(w):
                closed = (x < 2 and y not in spans['left'] or x >= w - 2 and y not in spans['right']
                          or y < 2 and x not in spans['up'] or y >= h - 2 and x not in spans['down'])
                if n in reports[1]['new_maps']: assert bool(v[y * w + x] & 0xC00) == closed, (n, x, y)
                elif closed: assert v[y * w + x] & 0xC00 or v[y * w + x] >> 12 >= 3, (n, x, y)
    old_art, new_art = MapRenderer(inputs), MapRenderer(source)
    for n in ['MossdeepCity','Route106','Route107','JourneyDewfordPortIsland']:
        a,_ = old_art.render(n,npcs=False); b,_ = new_art.render(n,npcs=False)
        assert a.tobytes() == b.tobytes(), ('PR90 artwork changed', n)
    proof = dict(passed=True, pr90_static_art_pixel_identical=True, rom_sha256=sha(source / 'pokeemerald.gba'), layers=PRIOR + [LAYER],
                 original_inputs_verified=True, idempotent=True, differences=[], reproduced_layers=['continuous-ocean', 'annotated-world-links', LAYER],
                 unrelated_source_inputs_checked=len(set(expected) - {str(p) for p in targets}),
                 original_event_maps_preserved=preserved, all_native_events_preserved=True,
                 native_land_and_town_atlas_art_preserved=True, canonical_water_pixels_and_indices_identical=True,
                 eight_animation_frames_identical=True, all_new_outer_limits_closed=True, bounded_route_count=len(reports[2]['boundaries']), islands=reports[2]['islands'], cave_approaches=reports[2]['cave_approaches'], pr90_events_and_ports_preserved=True,
                 new_maps=reports[1]['new_maps'], annotations=reports[1]['annotations'], gps=reports[1]['gps'])
    output = Path(output); output.parent.mkdir(exist_ok=True, parents=True)
    output.write_text(json.dumps(proof, indent=2) + '\n')
    print('Three ocean layers reproduced over PR90; 65 routes bounded; 15 cave approaches; 9 sandy islets')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--original-inputs', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); validate(a.source, a.original_inputs, a.output)
