"""Authenticate regional artwork and classify physically registered native water.

Native ownership is not inferred from the revision171 player GPS, map-section
rectangles, nearest names, or a requested pixel count. The regional overlay is
reproduced from its authenticated PNGs for visual provenance. A *physical*
native exclusion additionally requires a supplied global registration and an
entire six-by-six corridor core covered by real, compatible native water.

Registrations are authored integration inputs: this reader checks their real
terrain and mutual geometry, but does not invent their atlas positions. Reports
retain that distinction and never claim controller or release certification.
"""
from collections import defaultdict
import argparse
import hashlib
import json
from pathlib import Path

from atlas_surf_truth import decode_atlas, classify_pixels


ROOT = Path(__file__).resolve().parents[2]
COLORS = ((16,24,32),(112,184,232),(48,104,176),(24,112,0),
          (48,152,0),(80,200,0),(120,224,0),(184,240,64),
          (216,248,112),(184,120,8),(224,168,16),(248,208,56),
          (248,232,136),(248,72,24),(248,248,240),(96,80,72))
REGIONAL_OCEAN_COLORS = frozenset(((164,180,255),(156,213,255),
    (74,156,230),(41,131,230),(82,148,213),(90,172,230)))
VECTORS = {'left': (-1,0), 'right': (1,0), 'up': (0,-1), 'down': (0,1)}


def _ordered(points):
    return [list(point) for point in sorted(points, key=lambda p: (p[1],p[0]))]


def regional_art_evidence(inputs, assets_root=ROOT):
    """Reproduce only the native regional artwork, without any player GPS.

    The source marker authenticates the PNGs and panel transforms. This is
    pixel provenance, not a declaration that a whole native map owns every
    colored pixel in its section rectangle.
    """
    from PIL import Image
    marker = inputs.js('.journey-coastal-world-map')
    truth = decode_atlas(inputs.read('src/data/journey_world_map.h').decode())
    palette = Image.new('P',(1,1))
    palette.putpalette([v for color in COLORS for v in color]+[0]*720)
    records, coverage, hashes = [], defaultdict(list), {}
    for name, rectangle in marker['panels'].items():
        relative = f'web/atlas/{name}.png'
        raw = (Path(assets_root)/relative).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if marker['asset_sha256'].get(relative) != digest:
            raise ValueError(('Regional atlas asset differs from authenticated parent', relative))
        hashes[relative] = digest
        left, top, width, height = rectangle
        with Image.open(Path(assets_root)/relative) as original:
            native = original.convert('RGB')
        for y in range(native.height):
            for x in range(native.width):
                if native.getpixel((x,y)) in REGIONAL_OCEAN_COLORS:
                    native.putpixel((x,y),COLORS[1])
        # The original generator removed the regional selector in this exact
        # corner. It never removes a whole town or guesses a land mask.
        if name != 'hoenn':
            pending = [(native.width-1,y) for y in range(native.height-24,native.height)
                       if native.getpixel((native.width-1,y)) != COLORS[1]]
            seen = set()
            while pending:
                x,y = pending.pop()
                if (x,y) in seen or not (native.width-16 <= x < native.width
                     and native.height-24 <= y < native.height) or native.getpixel((x,y)) == COLORS[1]:
                    continue
                seen.add((x,y))
                native.putpixel((x,y),COLORS[1])
                pending.extend(((x-1,y),(x+1,y),(x,y-1),(x,y+1)))
        overview = native.resize((width,height),Image.Resampling.NEAREST).quantize(
            palette=palette,dither=Image.Dither.NONE)
        blue = {(left+x,top+y) for y in range(height) for x in range(width)
                if overview.getpixel((x,y)) == 2
                and 0 <= left+x < truth.width and 0 <= top+y < truth.height}
        surviving = blue & truth.blue_pixels
        for point in surviving:
            coverage[point].append(name)
        records.append(dict(panel=name,rectangle=list(rectangle),asset=relative,
                            asset_sha256=digest,regional_blue_pixels=_ordered(blue),
                            surviving_current_blue_pixels=_ordered(surviving)))
    inputs.assert_unchanged()
    return dict(kind='atlas-authenticated-regional-art-provenance',
                art_sha256=dict(truth.array_sha256),asset_sha256=hashes,panels=records,
                surviving_native_art_blue_pixels=_ordered(coverage),
                surviving_native_art_blue_count=len(coverage),
                surviving_pixel_panels=[dict(atlas=list(p),panels=coverage[p])
                    for p in sorted(coverage,key=lambda p:(p[1],p[0]))],
                player_gps_used=False,map_section_rectangles_used_for_ownership=False,
                physical_native_ownership_proven=False,native_validated=False)


def protected_icon_witnesses(inputs, truth=None):
    """Authenticate the active shipyard's blue center as an icon, not water."""
    name = 'JourneyRoute12Shipyard'
    if name not in inputs.maps:
        return {}
    truth = truth or decode_atlas(inputs.read('src/data/journey_world_map.h').decode())
    anchor = inputs.anchors().get(name)
    mapping = inputs.maps[name]
    if anchor is None or anchor['atlas'] != [96,40]:
        raise ValueError('Shipyard fixed icon anchor changed')
    if not mapping.get('object_events') or not mapping.get('warp_events'):
        raise ValueError('Shipyard no longer contains its complete active port events')
    expected = [14,14,14,14,2,14,14,14,14]
    actual = [truth.pixel((96+dx,40+dy)) for dy in (-1,0,1) for dx in (-1,0,1)]
    if actual != expected:
        raise ValueError('Shipyard blue center no longer has its authenticated white icon surround')
    return {(96,40):dict(owner=name,
        reason='Authenticated center of the complete active port icon; eight white neighbors, real port actors and warp',
        actors=len(mapping['object_events']),warps=len(mapping['warp_events']))}


def _normalize_registrations(inputs, registrations):
    normalized = []
    seen = set()
    for item in registrations:
        name = item.get('native_map',item.get('map'))
        key = item.get('name',f'{name}:{len(normalized)}')
        if name not in inputs.maps or key in seen:
            raise ValueError(('Unknown native map or duplicated registration',name,key))
        seen.add(key)
        layout = inputs.layout(name)
        if 'native_tile' in item or 'global_tile' in item:
            native_tile,global_tile = item.get('native_tile'),item.get('global_tile')
            if any(not isinstance(value,(tuple,list)) or len(value) != 2
                   or any(type(v) is not int for v in value) for value in (native_tile,global_tile)):
                raise ValueError(('Interface needs integer native/global tile witnesses',name))
            direction = item.get('direction')
            if direction not in VECTORS or not inputs.water(name,*native_tile):
                raise ValueError(('Interface witness must be real water with cardinal heading',name))
            x,y = native_tile
            if not ((direction == 'left' and x == 0)
                    or (direction == 'right' and x == layout['width']-1)
                    or (direction == 'up' and y == 0)
                    or (direction == 'down' and y == layout['height']-1)):
                raise ValueError(('Interface witness is not on its stated native boundary',name,direction,native_tile))
            origin = [global_tile[i]-native_tile[i] for i in (0,1)]
        else:
            origin = item['origin']
        if not isinstance(origin,(list,tuple)) or len(origin) != 2 or any(type(v) is not int for v in origin):
            raise ValueError(('Global native origin must be an integer pair',name))
        evidence = item.get('atlas_evidence',item.get('registration_evidence'))
        if not evidence:
            raise ValueError(('Native atlas registration needs explicit authored evidence',name))
        labels, components = inputs.water_components(name)
        selected = item.get('components',[item['component']] if 'component' in item else list(range(len(components))))
        if not selected or len(set(selected)) != len(selected):
            raise ValueError(('Native water components missing or duplicated',name))
        if any(type(value) is not int or not 0 <= value < len(components) for value in selected):
            raise ValueError(('Unknown native water component',name,selected))
        if 'native_tile' in item and labels[tuple(item['native_tile'])] not in selected:
            raise ValueError(('Boundary witness belongs to another native component',name))
        rect = item.get('local_rect',[0,0,layout['width'],layout['height']])
        if not isinstance(rect,(list,tuple)) or len(rect) != 4 or any(type(v) is not int for v in rect):
            raise ValueError(('Native ownership patch must be an integer half-open rectangle',name))
        if not (0 <= rect[0] < rect[2] <= layout['width'] and 0 <= rect[1] < rect[3] <= layout['height']):
            raise ValueError(('Native ownership patch exceeds original terrain',name,rect))
        normalized.append(dict(name=key,map=name,origin=list(origin),components=sorted(selected),
                               local_rect=list(rect),registration_evidence=evidence,
                               native_frame=item.get('native_frame'),
                               native_tile=item.get('native_tile'),global_tile=item.get('global_tile'),
                               direction=item.get('direction')))
    return normalized


def registered_water(inputs, registrations):
    """Return actual global water ownership and fail on conflicting maps."""
    rows = _normalize_registrations(inputs,registrations)
    water = {}
    by_frame = {(row['native_frame'],row['map']):row for row in rows if row['native_frame'] is not None}
    if len(by_frame) != sum(row['native_frame'] is not None for row in rows):
        raise ValueError('One native map has conflicting registrations in the same native frame')
    for row in rows:
        name = row['map']
        ox,oy = row['origin']
        _, components = inputs.water_components(name)
        for component in row['components']:
            for x,y in components[component]:
                left,top,right,bottom = row['local_rect']
                if not (left <= x < right and top <= y < bottom):
                    continue
                # Elevations0/15 are transition contexts, not proof that a
                # saved surfer can stand there at elevation1. Keep their
                # words in evidence; a full core requires compatible heights.
                point = ox+x,oy+y
                record = dict(map=name,tile=[x,y],component=component,
                              word=inputs.word(name,x,y),origin=list(row['origin']),registration=row['name'])
                if point in water:
                    previous = water[point]
                    if any(previous[field] != record[field] for field in ('map','tile','word','component')):
                        raise ValueError(('Native global water reservations overlap',point,
                                          water[point]['map'],name))
                    continue  # Identical physical cell witnessed by two interfaces.
                water[point] = record
    seams = []
    for row in rows:
        name = row['map']
        width,height = (inputs.layout(name)[key] for key in ('width','height'))
        ox,oy = row['origin']
        for connection in inputs.maps[name].get('connections') or []:
            direction = connection['direction']
            target = inputs.by_id[connection['map']]
            frame = row['native_frame']
            if direction not in VECTORS or frame is None or (frame,target) not in by_frame:
                continue
            other = by_frame[frame,target]
            target_width,target_height = (inputs.layout(target)[key] for key in ('width','height'))
            offset = connection['offset']
            if direction == 'left': expected = ox-target_width,oy+offset
            elif direction == 'right': expected = ox+width,oy+offset
            elif direction == 'up': expected = ox+offset,oy-target_height
            else: expected = ox+offset,oy+height
            if tuple(other['origin']) != expected:
                raise ValueError(('Preserved native connection contradicts physical registration',
                                  name,target,direction,other['origin'],expected))
            seams.append(dict(source=name,destination=target,direction=direction,offset=offset,frame=frame))
    inputs.assert_unchanged()
    return water,rows,seams


def classify_registered_native(inputs, registrations, *, icon_witnesses=None, accesses=(), expected_components=()):
    """Exclude a blue pixel only when its entire core is actual native water.

    Partial ownership is reported at game-tile resolution. It must be handled
    by exclusive physical reservation/clipping; silently excluding a whole
    atlas pixel on a single native-water witness would leave a missing route.
    Conversely, filling it without clipping would duplicate native water.
    """
    truth = decode_atlas(inputs.read('src/data/journey_world_map.h').decode())
    water, rows, seams = registered_water(inputs,registrations)
    witnesses, partial, incompatible = {}, [], []
    for point in sorted(truth.blue_pixels,key=lambda p:(p[1],p[0])):
        x,y = point
        core = {(x*8+dx,y*8+dy) for dy in range(1,7) for dx in range(1,7)}
        covered = core & water.keys()
        if not covered:
            continue
        records = [water[p] for p in sorted(covered,key=lambda p:(p[1],p[0]))]
        # A corridor can cross a native0/15 transition; height3 water does not
        # establish a surfer's valid core and must remain a reported conflict.
        bad = [r for r in records if r['word'] >> 12 not in (0,1,15)]
        if bad:
            incompatible.append(dict(atlas=list(point),cells=bad))
        if covered == core and not bad:
            witnesses[point] = [dict(**record,atlas=list(point),surfable=True)
                                for record in records]
        else:
            partial.append(dict(atlas=list(point),native_cells=len(covered),
                                core_cells=36,cells=records,
                                missing_global_cells=_ordered(core-covered),
                                incompatible_height_cells=len(bad)))
    icons = protected_icon_witnesses(inputs,truth) if icon_witnesses is None else icon_witnesses
    result = classify_pixels(truth,native_witnesses=witnesses,
                             icon_witnesses=icons,accesses=accesses)
    expected = {(row['native_map'],row['component']) for row in expected_components}
    registered = {(row['map'],component) for row in rows for component in row['components']}
    missing = sorted(expected-registered)
    result.update(kind='atlas-registered-native-classification',registrations=rows,
                  native_registration_seams=seams,partial_native_pixel_coverage=partial,
                  incompatible_native_water_heights=incompatible,
                  all_native_pixel_cores_physically_covered=True,
                  authored_registrations_read_from_external_plan=True,
                  registration_geography_independently_certified=False,
                  partial_pixels_require_exclusive_game_tile_ownership=bool(partial),
                  expected_components_supplied=bool(expected),
                  missing_component_registrations=[dict(native_map=name,component=component)
                                                   for name,component in missing],
                  all_expected_native_components_registered=bool(expected) and not missing,
                  old_player_gps_used=False,native_validated=False,
                  final_release_validated=False)
    inputs.assert_unchanged()
    return result


def main():
    from atlas_surf_source import Source
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--registrations',type=Path,
                        help='Authored local interface registration JSON; omitted means provenance-only investigation')
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    source = Source(args.source)
    report = dict(kind='atlas-surf-classification-investigation',
                  regional_art=regional_art_evidence(source),
                  physical_classification_complete=False,native_validated=False,
                  final_release_validated=False)
    if args.registrations:
        data = json.loads(args.registrations.read_text())
        report['classification'] = classify_registered_native(source,data['registrations'],
            accesses=data.get('accesses',()),expected_components=data.get('expected_components',()))
        report['registration_file_sha256'] = hashlib.sha256(args.registrations.read_bytes()).hexdigest()
    report['input_sha256'] = dict(source.inputs)
    source.assert_unchanged()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(regional_art_blue_pixels=report['regional_art']['surviving_native_art_blue_count'],
                         physical_classification_complete=False,output=str(args.output))))


if __name__ == '__main__':
    main()
