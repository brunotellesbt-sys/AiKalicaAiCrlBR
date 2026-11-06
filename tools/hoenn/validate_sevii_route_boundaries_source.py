"""Independently check layer 169 terrain, GPS, immutable inputs and ROM bytes."""
import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess

import sevii_route_boundaries_contract as contract

ROOT = Path(__file__).resolve().parents[2]
CARDINAL = {'left', 'right', 'up', 'down'}
BEACH = 'OneIsland_TreasureBeach_Frlg'
TOWN = 'OneIsland_Frlg'
LINK = 'JourneySurfLink05000'
PRIMARY_SMALL = {'gTileset_General': 0x1F9, 'gTileset_General_Frlg': 0x243,
                 'gTileset_JourneySeviiSea': 0x243}
RUNTIME_SYMBOLS = ('MapGridGetMetatileIdAt', 'NewGameInitData', 'CopyPartyAndObjectsFromSave')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def safe_relative(name):
    path = Path(name)
    assert isinstance(name, str) and name and not path.is_absolute() and '..' not in path.parts, name
    return path


class Inputs:
    def __init__(self, source):
        self.source = Path(source)
        self.layouts = {r['id']: r for r in json.loads((self.source/'data/layouts/layouts.json').read_bytes())['layouts']}
        self.maps = {p.parent.name: json.loads(p.read_bytes()) for p in (self.source/'data/maps').glob('*/map.json')}
        self.by_id = {m['id']: n for n, m in self.maps.items()}
        self.grids, self.attributes = {}, {}
        self.headers = (self.source/'src/data/tilesets/headers.h').read_text()
        self.definitions = (self.source/'src/data/tilesets/metatiles.h').read_text()
        enum = (self.source/'include/constants/metatile_behaviors.h').read_text()
        enum = re.sub(r'/\*.*?\*/|//[^\n]*', '', enum, flags=re.S).split('enum {', 1)[1].split('}', 1)[0]
        assert '=' not in enum
        behavior_ids = {v: i for i, v in enumerate(re.findall(r'\b(?:MB_\w+|NUM_METATILE_BEHAVIORS)\b', enum))}
        flags = (self.source/'src/metatile_behavior.c').read_text()
        self.water = {behavior_ids[n] for n, expr in re.findall(r'\[(MB_\w+)\]\s*=\s*([^,\n]+)', flags)
                      if 'TILE_FLAG_SURFABLE' in expr}

    def layout(self, name):
        return self.layouts[self.maps[name]['layout']]

    def grid(self, name):
        l = self.layout(name)
        path = l['blockdata_filepath']
        if path not in self.grids:
            raw = (self.source/path).read_bytes()
            assert len(raw) == 2*l['width']*l['height'], (name, len(raw))
            self.grids[path] = struct.unpack('<'+'H'*(len(raw)//2), raw)
        return self.grids[path]

    def word(self, name, x, y):
        l = self.layout(name)
        assert 0 <= x < l['width'] and 0 <= y < l['height'], (name, x, y)
        return self.grid(name)[y*l['width']+x]

    def behavior(self, name, word):
        l = self.layout(name)
        cutoff, size = (640, 4) if l['layout_version'] == 'frlg' else (512, 2)
        mid = word & 1023
        bank = l['primary_tileset' if mid < cutoff else 'secondary_tileset']
        if (bank, size) not in self.attributes:
            body = re.search(r'const struct Tileset '+re.escape(bank)+r'\s*=\s*\{(.*?)\};', self.headers, re.S)[1]
            symbol = re.search(r'\.metatileAttributes\s*=\s*(\w+)', body)[1]
            path = re.search(r'\b'+symbol+r'\[\].*?"([^"]+)"', self.definitions)[1]
            raw = (self.source/path).read_bytes()
            self.attributes[bank, size] = [int.from_bytes(raw[i:i+size], 'little') for i in range(0, len(raw), size)]
        return self.attributes[bank, size][mid if mid < cutoff else mid-cutoff] & (511 if size == 4 else 255)

    def perimeter(self, name):
        l = self.layout(name)
        for x in range(l['width']):
            yield x, 0, 'up', x, -1
            yield x, l['height']-1, 'down', x, l['height']
        for y in range(l['height']):
            yield 0, y, 'left', -1, y
            yield l['width']-1, y, 'right', l['width'], y

    def target(self, name, direction, x, y):
        l = self.layout(name)
        for c in self.maps[name].get('connections') or []:
            if c['direction'] != direction:
                continue
            other = self.by_id[c['map']]
            z = self.layout(other)
            xx = x-c['offset'] if direction in ('up', 'down') else x+z['width'] if direction == 'left' else x-l['width']
            yy = y-c['offset'] if direction in ('left', 'right') else y+z['height'] if direction == 'up' else y-l['height']
            if 0 <= xx < z['width'] and 0 <= yy < z['height']:
                return other, xx, yy
        return None


def marine_scope(inputs):
    towns = {n+'Island_Frlg' for n in ('One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven')}
    names = []
    for n, m in inputs.maps.items():
        if inputs.layout(n)['primary_tileset'] not in PRIMARY_SMALL:
            continue
        ocean = m['map_type'] == 'MAP_TYPE_OCEAN_ROUTE' and (n.startswith('Journey') or 'Island_Harbor' in n)
        if ocean or n in towns or (n.startswith('OneIsland_') and m['map_type'] == 'MAP_TYPE_ROUTE') or n == 'ThreeIsland_Port_Frlg':
            names.append(n)
    assert len(names) == 284, ('Unexpected marine audit scope', len(names))
    return sorted(names)


def check_boundaries(current, old, names):
    open_count = changed_reefs = 0
    for n in names:
        l = current.layout(n)
        small = PRIMARY_SMALL[l['primary_tileset']]
        expected_border = struct.pack('<4H', *([0x1400 | small]*4))
        assert (current.source/l['border_filepath']).read_bytes() == expected_border, ('Incomplete repeated reef border', n)
        assert (l['border_width'], l['border_height']) == (2, 2)
        openings = {(x, y) for x, y, d, xx, yy in current.perimeter(n) if current.target(n, d, xx, yy)}
        for x, y, d, xx, yy in current.perimeter(n):
            if (x, y) in openings:
                continue
            word = current.word(n, x, y)
            if current.behavior(n, word) in current.water:
                assert word == (0x1400 | small), ('Unconnected water edge lacks complete reef', n, x, y, hex(word))
        for x, y, d, xx, yy in old.perimeter(n):
            # A connection's rectangle can contain blocked reef endpoints.
            # Preserve its existing usable openings; the separately checked
            # southern rail intentionally opens eight previously blocked cells.
            if old.target(n, d, xx, yy) is not None and not old.word(n, x, y)&0xC00:
                nx = x+8 if n == BEACH else x
                assert current.word(n, nx, y) == old.word(n, x, y), ('Existing connected opening changed', n, x, y)
                open_count += 1
        if n == BEACH:
            continue
        before, after = old.grid(n), current.grid(n)
        assert len(before) == len(after)
        for at, (a, b) in enumerate(zip(before, after)):
            if a == b:
                continue
            x, y = at % l['width'], at // l['width']
            if n == LINK and y == 12 and 8 <= x < 16:
                assert (a & 1023) == 0x243 and a & 0xC00 and b == 0x112B
                continue
            assert x in (0, l['width']-1) or y in (0, l['height']-1), ('Interior terrain changed', n, x, y)
            assert (x, y) not in openings, ('Connected terrain changed', n, x, y)
            assert old.behavior(n, a) in old.water and b == (0x1400 | small), ('Dry geology/object changed', n, x, y)
            changed_reefs += 1
    return dict(maps=len(names), map_names=names, unconnected_water_edges=0,
                connected_openings_preserved=True, connected_openings_checked=open_count,
                complete_small_reefs=True, independently_checked_reef_replacements=changed_reefs)


def check_geography(current, old):
    a, b = old.layout(BEACH), current.layout(BEACH)
    assert (a['width'], a['height']) == (24, 40)
    assert (b['width'], b['height']) == (40, 48)
    for y in range(40):
        assert [current.word(BEACH, x+8, y) for x in range(24)] == [old.word(BEACH, x, y) for x in range(24)], ('Old Treasure terrain moved/overwritten', y)
    for key in ('object_events', 'warp_events', 'coord_events', 'bg_events'):
        expected = copy.deepcopy(old.maps[BEACH].get(key, []))
        for event in expected:
            event['x'] += 8
        assert current.maps[BEACH].get(key, []) == expected, ('Event/warp identity or placement changed', key)
    assert current.maps[BEACH]['connections'] == [
        dict(map=old.maps[TOWN]['id'], offset=8, direction='up'),
        dict(map=old.maps[LINK]['id'], offset=-8, direction='up')]
    for n in current.maps:
        if n == BEACH:
            continue
        for key in ('object_events', 'warp_events', 'coord_events', 'bg_events'):
            assert current.maps[n].get(key, []) == old.maps[n].get(key, []), ('Unrelated events changed', n, key)
    # Confirm the added cliff is a whole native face with side walls and a water
    # toe; its donors and all old geology remain byte-identical above this row.
    closure = {(7, 37): 0x051F, (32, 37): 0x0517, (6, 40): 0x112C,
               (33, 40): 0x1120, (33, 41): 0x1131}
    for y in (38, 39):
        closure.update({(7, y): 0x0473, (6, y): 0x112C, (32, y): 0x0475, (33, y): 0x112A})
    for x in range(7, 33):
        closure[x, 40] = 0x047B if x == 7 else 0x047D if x == 32 else 0x047C
        closure[x, 41] = 0x1123
    for (x, y), word in closure.items():
        assert current.word(BEACH, x, y) == word, ('Incomplete native mountain closure', x, y)
    return dict(old_dimensions=[24, 40], dimensions=[40, 48], old_cells_preserved=960,
                offset=[8, 0], objects_and_warps_preserved=True, geology_preserved=True,
                complete_native_cliff_cells_checked=len(closure))


def gps(source):
    text = (Path(source)/'src/data/journey_world_position.h').read_text()
    values = list(map(int, re.search(r'sWorldNavigationPixels\[\] = \{([^}]+)', text)[1].split(',')))
    descriptors = {ident: (int(first), int(w), int(h)) for first, ident, w, h in re.findall(
        r'\{(\d+), \(MAP_GROUP\((\w+)\)<<8\)\|MAP_NUM\(\2\), (\d+), (\d+)\}', text)}
    grids = {ident: (w, h, values[first:first+w*h]) for ident, (first, w, h) in descriptors.items()}
    assert all(len(words) == w*h for w, h, words in grids.values())
    return values, grids


def check_projection(current, old):
    values, grids = gps(current.source)
    old_values, old_grids = gps(old.source)
    assert grids.keys() == old_grids.keys()
    ident = current.maps[BEACH]['id']
    ow, oh, before = old_grids[ident]
    width, height, after = grids[ident]
    assert (ow, oh, width, height) == (24, 40, 40, 48)
    assert values[:len(old_values)] == old_values, 'Old packed GPS array changed'
    for y in range(40):
        assert after[y*40+8:y*40+32] == before[y*24:(y+1)*24]
    for key in grids:
        if key != ident:
            assert grids[key] == old_grids[key], ('Other logical GPS grid changed', key)
    lw, lh, link = grids[current.maps[LINK]['id']]
    assert (lw, lh) == (16, 13) and after[:8] == link[12*16+8:13*16]
    step = lambda a, b: max(abs((a & 255)-(b & 255)), abs((a >> 8)-(b >> 8)))
    maximum = max(step(after[y*40+x], after[yy*40+xx]) for y in range(48) for x in range(40)
                  for xx, yy in ((x+1, y), (x, y+1)) if xx < 40 and yy < 48)
    assert maximum <= 2, ('GPS snaps within extended beach', maximum)
    shared = []
    for x, y, d, xx, yy in current.perimeter(BEACH):
        target = current.target(BEACH, d, xx, yy)
        if target:
            n, tx, ty = target
            tw, th, other = grids[current.maps[n]['id']]
            shared.append(step(after[y*40+x], other[ty*tw+tx]))
    assert shared and max(shared) <= 2, ('GPS snaps across connected beach border', max(shared, default=-1))
    return dict(dimensions=[40, 48], old_logical_pixels_preserved=960,
                other_logical_grids_preserved=True, logical_grids_checked=len(grids),
                shared_border_maximum_step=max(shared), closed_loop_neighbor_maximum_step=maximum), values


def graph_limitations(inputs):
    """Report ambiguous projected graph corners; do not claim world certification."""
    from sevii_boundary_camera import translate_block
    def adjacent(name):
        l = inputs.layout(name)
        for c in inputs.maps[name].get('connections') or []:
            n = inputs.by_id[c['map']]
            z = inputs.layout(n)
            d = c['direction']
            if d == 'left': yield n, -z['width'], c['offset']
            elif d == 'right': yield n, l['width'], c['offset']
            elif d == 'up': yield n, c['offset'], -z['height']
            elif d == 'down': yield n, c['offset'], l['height']
    names = {n for n in inputs.maps if n.startswith('JourneySurfLink')}
    for n in list(names):
        names.update(q for q, x, y in adjacent(n))
    conflicts = Counter()
    for n in sorted(names):
        l = inputs.layout(n)
        w, h = l['width'], l['height']
        direct = list(adjacent(n))
        candidates = [(r, nx+rx, ny+ry) for q, nx, ny in direct for r, rx, ry in adjacent(q) if r != n]
        for y in range(-7, h+7):
            for x in range(-7, w+8):
                if 0 <= x < w and 0 <= y < h:
                    continue
                if any(0 <= x-dx < inputs.layout(q)['width'] and 0 <= y-dy < inputs.layout(q)['height'] for q, dx, dy in direct):
                    continue
                mids = set()
                for q, dx, dy in candidates:
                    z = inputs.layout(q)
                    xx, yy = x-dx, y-dy
                    if 0 <= xx < z['width'] and 0 <= yy < z['height']:
                        mids.add(translate_block(inputs.word(q, xx, yy), z['layout_version'] == 'frlg', l['layout_version'] == 'frlg') & 1023)
                if len(mids) > 1:
                    conflicts[n] += 1
    return dict(full_world_camera_certified=False, ambiguous_graph_cells=sum(conflicts.values()),
                ambiguous_graph_maps=sorted(conflicts),
                ambiguous_graph_map_counts=dict(sorted(conflicts.items())))


def symbols(source):
    raw = subprocess.check_output([str(ROOT/'.local/arm-binutils/usr/bin/arm-none-eabi-nm'),
                                   '-S', '--defined-only', str(source/'pokeemerald.elf')], text=True)
    return {name: (int(address, 16), int(size, 16) if size else 0) for address, size, name in re.findall(
        r'^([\da-fA-F]+)\s+(?:([\da-fA-F]+)\s+)?\w\s+(\S+)$', raw, re.M)}


def elf_rom_bytes(elf, rom):
    """Check each file-backed ARM ELF32 LOAD segment against its ROM load address."""
    assert elf[:7] == b'\x7fELF\x01\x01\x01'
    offset = struct.unpack_from('<I', elf, 28)[0]
    stride, count = struct.unpack_from('<HH', elf, 42)
    segments = 0
    for i in range(count):
        kind, at, virtual, physical, length, memory, flags, alignment = struct.unpack_from('<8I', elf, offset+i*stride)
        if kind != 1 or length == 0:
            continue
        assert 0x08000000 <= physical and physical+length <= 0x0A000000
        assert elf[at:at+length] == rom[physical-0x08000000:physical-0x08000000+length], ('ELF/ROM load segment differs', hex(physical), length)
        segments += 1
    assert segments >= 1
    return segments


def compiled_bindings(source, inputs, names, gps_values):
    rom = (source/'pokeemerald.gba').read_bytes()
    elf = (source/'pokeemerald.elf').read_bytes()
    assert len(rom) == 33554432 and rom[-4096:] == b'\xff'*4096
    assert rom[0xBD] == (-sum(rom[0xA0:0xBD])-0x19) & 255
    segments = elf_rom_bytes(elf, rom)
    table = symbols(source)
    def read_rom(address, size):
        offset = address-0x08000000
        assert 0 <= offset <= len(rom)-size, (hex(address), size)
        return rom[offset:offset+size]
    def binary(path, address):
        raw = (source/path).read_bytes()
        assert read_rom(address, len(raw)) == raw, ('Compiled spatial bytes differ', path)
        return dict(file=path, address=address, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    rows = []
    for n in names:
        l = inputs.layout(n)
        assert l['name'] in table
        address, size = table[l['name']]
        raw = read_rom(address, 28)
        width, height, border, blocks, primary, secondary, frlg, bw, bh, padding = struct.unpack('<iiIIIIBBBB', raw)
        expected_size = (l['border_width'],l['border_height']) if frlg else (0,0)
        assert (width, height, frlg, bw, bh) == (l['width'], l['height'], int(l['layout_version'] == 'frlg'), *expected_size), n
        assert primary == table[l['primary_tileset']][0] and secondary == table[l['secondary_tileset']][0], n
        rows.append(dict(map=n, layout=l['id'], symbol=l['name'], address=address,
                         width=width, height=height, primary_pointer=primary, secondary_pointer=secondary,
                         is_frlg=bool(frlg), border_width=bw if frlg else 2, border_height=bh if frlg else 2,
                         stored_border_width=bw,stored_border_height=bh,
                         blockdata=binary(l['blockdata_filepath'], blocks), borderdata=binary(l['border_filepath'], border),
                         compiled_layout_bytes_match=True))
    runtime = []
    for symbol in RUNTIME_SYMBOLS:
        address, size = table[symbol]
        assert size > 0
        raw = read_rom(address, size)
        runtime.append(dict(symbol=symbol, address=address, bytes=size, sha256=hashlib.sha256(raw).hexdigest()))
    address, size = table['sWorldNavigationPixels']
    raw = struct.pack('<'+'H'*len(gps_values), *gps_values)
    assert size == len(raw) and read_rom(address, len(raw)) == raw
    return rows, runtime, dict(symbol='sWorldNavigationPixels', address=address, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()), segments


def validate(source, baseline, output, preflight=False, gallery=False):
    from candidate_layer import Layer
    from prepare_sevii_route_boundaries import PRIOR, LAYER, stage_repairs, verify_parent
    source, baseline, output = map(Path, (source, baseline, output))
    assert source.resolve() != baseline.resolve()
    expected = verify_parent(baseline)
    marker = json.loads((source/('.journey-'+contract.SCOPE)).read_bytes())
    changes = marker['prepared_sha256']
    assert changes and marker['parent_rom_sha256'] == contract.PARENT_ROM_SHA256
    if not preflight or contract.PREPARED_SHA256:
        assert contract.PREPARED_SHA256 and changes == contract.PREPARED_SHA256, 'Pin the exact reviewed layer169 inputs'
    assert marker['layer'] == LAYER and len(PRIOR) == 168
    for name, sha in changes.items():
        safe_relative(name)
        assert sha != expected.get(name), ('No-op staged source file', name)
    for name, sha in (expected | changes).items():
        assert digest(source/name) == sha, ('Source scope/bytes differ from layer169 replay', name)
    prefix = ['.source-acquired.json', *['.journey-'+name for name in PRIOR]]
    for name in prefix:
        assert (source/name).read_bytes() == (baseline/name).read_bytes(), ('Historical marker changed', name)
    replay = Layer(baseline, LAYER, PRIOR)
    metadata = stage_repairs(replay)
    replay_hashes = {name: hashlib.sha256(raw).hexdigest() for name, raw in replay.outputs.items()}
    result = dict(layer=LAYER, **metadata, original_sha256=replay.originals, prepared_sha256=replay_hashes)
    assert json.loads(json.dumps(result)) == marker, 'Independent in-memory repair replay differs'
    assert set(replay.outputs) == set(changes)
    for name, raw in replay.outputs.items():
        assert (source/name).read_bytes() == raw, ('Replayed overlay output differs', name)
    protected = [name for name in expected if name.endswith('/scripts.inc') or name.startswith('graphics/')
                 or name in ('src/data/journey_world_map.h', 'src/data/region_map/region_map_sections.json',
                             'src/data/tilesets/headers.h', 'src/data/tilesets/metatiles.h')]
    assert not set(protected).intersection(changes), ('Scripts/atlas/tileset art changed', set(protected).intersection(changes))
    current, old = Inputs(source), Inputs(baseline)
    assert current.maps.keys() == old.maps.keys() and current.layouts.keys() == old.layouts.keys()
    for ident, layout in current.layouts.items():
        before = old.layouts[ident]
        ignored = {'border_filepath', 'border_width', 'border_height'}
        if ident == current.maps[BEACH]['layout']:
            ignored.update(('width', 'height'))
        assert {k: v for k, v in layout.items() if k not in ignored} == {k: v for k, v in before.items() if k not in ignored}, ('Unrelated layout fields/banks changed', ident)
    names = marine_scope(current)
    spatial_paths = {current.layout(n)['blockdata_filepath'] for n in names}
    spatial_paths.update(current.layout(n)['border_filepath'] for n in names)
    assert {name for name in changes if name.endswith('.bin')} <= spatial_paths, 'Unreviewed binary overlay input'
    for n in set(current.maps)-set(names):
        assert current.layout(n) == old.layout(n), ('Indirect unrelated map layout changed', n)
        assert current.grid(n) == old.grid(n), ('Indirect unrelated map terrain changed', n)
    boundary = check_boundaries(current, old, names)
    geography = check_geography(current, old)
    projection, gps_values = check_projection(current, old)
    limitations = graph_limitations(current)
    layouts, runtime, compiled_gps, segments = [], [], None, 0
    rom_sha = elf_sha = None
    if not preflight:
        layouts, runtime, compiled_gps, segments = compiled_bindings(source, current, names, gps_values)
        rom_sha, elf_sha = digest(source/'pokeemerald.gba'), digest(source/'pokeemerald.elf')
        assert rom_sha != contract.PARENT_ROM_SHA256
    captures = []
    if gallery:
        from render_sea_maps import MapRenderer
        renderer = MapRenderer(source)
        selected = {n for n in names if current.layout(n)['blockdata_filepath'] in changes}
        selected.update('JourneySurfLink035%02d'%i for i in range(1, 5))
        directory = output.parent/'source-gallery'
        directory.mkdir(parents=True, exist_ok=True)
        for n in sorted(selected):
            image, mapping = renderer.render(n, npcs=True)
            path = directory/(n+'.png')
            image.save(path)
            captures.append(dict(file=path.relative_to(output.parent).as_posix(), sha256=digest(path), map=n,
                                 width_tiles=current.layout(n)['width'], height_tiles=current.layout(n)['height'], npcs=True))
    report = dict(kind='sevii-route-boundaries-source', passed=not preflight, preflight=bool(preflight), compiled_rom=not preflight,
                  layers=PRIOR+[contract.SCOPE], parent_rom_sha256=contract.PARENT_ROM_SHA256,
                  prepared_sha256=changes, changed_files=sorted(changes), rom_sha256=rom_sha, elf_sha256=elf_sha,
                  source_hashes_checked=len(expected | changes), independent_replay=True, prefix_markers_unchanged=True,
                  unrelated_source_files_unchanged=True, scripts_and_atlas_art_unchanged=True,
                  boundary_audit=boundary, geography=geography, projection=projection, camera_limitations=limitations,
                  compiled_layouts=layouts, compiled_runtime=runtime, runtime_export_names=list(RUNTIME_SYMBOLS),
                  compiled_gps=compiled_gps, elf_rom_load_segments_checked=segments,
                  captures=captures, source_gallery_rendered=bool(gallery),
                  native_controller_and_scanout_have_separate_proof=True, full_campaign_playthrough=False)
    verify_parent(baseline)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--preflight', action='store_true')
    parser.add_argument('--gallery', action='store_true')
    args = parser.parse_args()
    print(json.dumps(validate(args.source, args.baseline, args.output, args.preflight, args.gallery), indent=2))
