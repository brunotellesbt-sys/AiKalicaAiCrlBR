"""Read-only pattern census; native edges and dense forests need context review.

This complements whole-map images. It does not certify movement, animation or
all geological objects merely because known boulder/pine patterns are present.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct

from generated_world_marine import PRIMARY_FAMILIES, SURFACE_TYPES


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def audit(source, upstream):
    source, upstream = Path(source), Path(upstream)
    acquired = json.loads((source/'.source-acquired.json').read_text())
    old_hashes = {}
    def old_read(path):
        raw = (upstream/path).read_bytes()
        assert digest(raw) == acquired['sha256'][path], ('Upstream cache differs',path)
        old_hashes[path] = digest(raw)
        return raw
    layouts = {r['id']:r for r in json.loads((source/'data/layouts/layouts.json').read_text())['layouts']}
    old_layouts = {r['id']:r for r in json.loads(old_read('data/layouts/layouts.json'))['layouts']}
    maps = {p.parent.name:json.loads(p.read_text()) for p in (source/'data/maps').glob('*/map.json')}
    by_id = {m['id']:n for n,m in maps.items()}
    current, original, inputs = {}, {}, {}
    for layout in layouts.values():
        path = layout['blockdata_filepath']
        if path not in current:
            raw = (source/path).read_bytes()
            current[path] = struct.unpack('<'+'H'*(len(raw)//2),raw)
            inputs[path] = digest(raw)
    for layout in old_layouts.values():
        path = layout['blockdata_filepath']
        if path not in original and (upstream/path).exists():
            raw = old_read(path)
            original[path] = struct.unpack('<'+'H'*(len(raw)//2),raw)
    def locate(name,x,y,depth=0):
        layout = layouts[maps[name]['layout']]
        width,height = layout['width'],layout['height']
        if 0<=x<width and 0<=y<height:
            return name,x,y
        if depth>=2:
            return None
        direction = 'left' if x<0 else 'right' if x>=width else 'up' if y<0 else 'down'
        for row in maps[name].get('connections') or []:
            if row['direction']!=direction:
                continue
            other_name = by_id[row['map']]
            other = layouts[maps[other_name]['layout']]
            xx = x-row['offset'] if direction in ('up','down') else x+other['width'] if direction=='left' else x-width
            yy = y-row['offset'] if direction in ('left','right') else y+other['height'] if direction=='up' else y-height
            if 0<=xx<other['width'] and 0<=yy<other['height']:
                return locate(other_name,xx,yy,depth+1)
        return None
    def word(cell):
        name,x,y = cell
        layout = layouts[maps[name]['layout']]
        return current[layout['blockdata_filepath']][y*layout['width']+x]
    def old_word(cell):
        name,x,y = cell
        layout = old_layouts.get(maps[name]['layout'])
        if not layout or not(0<=x<layout['width'] and 0<=y<layout['height']):
            return None
        values = original.get(layout['blockdata_filepath'])
        return None if values is None else values[y*layout['width']+x]
    counters, complete, native_variants, unresolved, outer = Counter(), [], [], [], []
    seen = set()
    inspected = []
    for name,mapping in sorted(maps.items()):
        layout = layouts[mapping['layout']]
        if mapping['map_type'] not in SURFACE_TYPES or layout['primary_tileset'] not in PRIMARY_FAMILIES:
            continue
        inspected.append(name)
        quadrants,_ = PRIMARY_FAMILIES[layout['primary_tileset']]
        width = layout['width']
        anchors = set()
        # 0x108/0x109 combine a cliff foot with the upper boulder halves.
        # A previous Surf opening erased their 0x118/0x119 lower row, so
        # looking only for the standard quartet missed these orphan tops.
        cliff_tops = (0x108, 0x109) if layout['primary_tileset'] in (
            'gTileset_General_Frlg', 'gTileset_JourneySeviiSea') else ()
        for index,value in enumerate(current[layout['blockdata_filepath']]):
            if value&1023 in quadrants:
                q = quadrants.index(value&1023)
                anchors.add((index%width-q%2,index//width-q//2))
            elif value&1023 in cliff_tops:
                q = cliff_tops.index(value&1023)
                anchors.add((index%width-q,index//width))
        for x,y in sorted(anchors):
            cells = [locate(name,x+dx,y+dy) for dy in range(2) for dx in range(2)]
            if None in cells:
                visible = [cell for cell in cells if cell is not None]
                original_map = json.loads(old_read(f'data/maps/{name}/map.json'))
                old_layout = old_layouts[mapping['layout']]
                native_pixels = all(old_word(c) is not None and old_word(c)&1023==word(c)&1023
                                    for c in visible)
                native_border = (source/layout['border_filepath']).read_bytes() == old_read(old_layout['border_filepath'])
                outer.append(dict(map=name,anchor=[x,y],visible_fragment_tiles=len(visible),
                    native_visible_art_preserved=native_pixels,
                    native_border_and_connections_preserved=bool(native_border and
                        mapping.get('connections')==original_map.get('connections')),
                    requires_adjacent_or_native_border_review=True))
                continue
            key = tuple(sorted(cells))
            if key in seen:
                continue
            seen.add(key)
            words = [word(c) for c in cells]
            mids = [w&1023 for w in words]
            row = dict(map=name,anchor=[x,y],cells=[list(c) for c in cells],metatiles=mids)
            if mids==list(quadrants):
                complete.append(row)
            else:
                old = [old_word(c) for c in cells]
                if all(a is not None and a&1023==b for a,b in zip(old,mids)):
                    native_variants.append(dict(row,native_art_preserved=True,
                                                only_block_flags_differ=old!=words))
                else:
                    unresolved.append(row)
    # All known FRLG forest arrangements are sampled from the verified native
    # maps. Standalone 2x3 trees are one valid form among overlapping forests.
    native_pines = Counter()
    for layout in old_layouts.values():
        if layout['primary_tileset']!='gTileset_General_Frlg':
            continue
        values = original.get(layout['blockdata_filepath'])
        if values is None:
            continue
        width,height = layout['width'],layout['height']
        for y in range(height-2):
            for x in range(width-1):
                if values[y*width+x]&1023==0xE:
                    native_pines[tuple(values[(y+dy)*width+x+dx]&1023 for dy in range(3) for dx in range(2))] += 1
    pine_rows, pine_outer = [], []
    for name,mapping in sorted(maps.items()):
        layout = layouts[mapping['layout']]
        if mapping['map_type'] not in SURFACE_TYPES or layout['primary_tileset'] not in ('gTileset_General_Frlg','gTileset_JourneySeviiSea'):
            continue
        width,height = layout['width'],layout['height']
        values = current[layout['blockdata_filepath']]
        for index,value in enumerate(values):
            if value&1023!=0xE:
                continue
            x,y = index%width,index//width
            if x+1>=width or y+2>=height:
                cells = [locate(name,x+dx,y+dy) for dy in range(3) for dx in range(2)]
                available = [c for c in cells if c is not None]
                native_pixels = all(old_word(c) is not None and old_word(c)&1023==word(c)&1023
                                    for c in available)
                native_border = (source/layout['border_filepath']).read_bytes() == old_read(
                    old_layouts[mapping['layout']]['border_filepath'])
                original_map = json.loads(old_read(f'data/maps/{name}/map.json'))
                pine_outer.append(dict(map=name,anchor=[x,y],
                    neighboring_cells=[None if c is None else list(c) for c in cells],
                    neighboring_metatiles=[None if c is None else word(c)&1023 for c in cells],
                    native_visible_art_preserved=native_pixels,
                    native_border_and_connections_preserved=bool(native_border and
                        mapping.get('connections')==original_map.get('connections'))))
                continue
            mids = tuple(values[(y+dy)*width+x+dx]&1023 for dy in range(3) for dx in range(2))
            pine_rows.append(dict(map=name,anchor=[x,y],metatiles=list(mids),
                                  native_pattern_examples=native_pines[mids],
                                  native_pattern=mids in native_pines))
    return dict(kind='coastal-complete-object-pattern-census',source_rom_sha256=digest((source/'pokeemerald.gba').read_bytes()),
                inspected_surface_maps=inspected,boulders=dict(complete=complete,
                    native_variant_art=native_variants,unresolved_patterns=unresolved,
                    outer_border_continuations=outer),
                frlg_pines=dict(interior_objects=pine_rows,outer_continuations=pine_outer,
                                nonnative_patterns=[r for r in pine_rows if not r['native_pattern']]),
                upstream_commit=acquired['commit'],verified_upstream_file_count=len(old_hashes),
                inspected_blockdata_sha256=inputs,source_render_not_emulator=True,
                movement_or_animation_certified=False,
                note='A native pattern match is not an automatic quality seal; whole source maps and contextual borders were reviewed separately.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--upstream',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    report=audit(args.source,args.upstream)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(surface_maps=len(report['inspected_surface_maps']),
        complete_boulders=len(report['boulders']['complete']),
        native_boulder_variants=len(report['boulders']['native_variant_art']),
        unresolved_boulders=len(report['boulders']['unresolved_patterns']),
        nonnative_pines=len(report['frlg_pines']['nonnative_patterns']))))
