"""Authenticate regional artwork and classify physically registered native water.

Native ownership is not inferred from the revision171 player GPS, map-section
rectangles, nearest names, or a requested pixel count. The regional overlay is
reproduced from its authenticated PNGs for visual provenance. A *physical*
native ownership additionally requires a supplied local interface registration
and real water connected to its native mouth. Six-wide cores belong to the
generated geometry; narrow native channels retain their original terrain.

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


def _raster_cell(point, blue):
    """Independent six-wide generated raster, including its two-tile joins."""
    x,y = point
    ax,ay,dx,dy = x//8,y//8,x%8,y%8
    if (ax,ay) not in blue:
        return False
    if 1 <= dx <= 6 and 1 <= dy <= 6:
        return True
    if 1 <= dy <= 6:
        return dx == 0 and (ax-1,ay) in blue or dx == 7 and (ax+1,ay) in blue
    if 1 <= dx <= 6:
        return dy == 0 and (ax,ay-1) in blue or dy == 7 and (ax,ay+1) in blue
    return False


def _authenticate_registration(inputs,row,truth):
    evidence = row['atlas_evidence']
    if evidence.get('art_sha256') != dict(truth.array_sha256):
        raise ValueError(('Registration does not bind the actual immutable atlas',row['native_map']))
    anchor = evidence['fixed_anchor']
    if anchor['map'] != row['native_map'] or inputs.anchors()[row['native_map']]['atlas'] != anchor['atlas']:
        raise ValueError(('Registration fixed anchor differs from source',row['native_map']))
    if 'gps' in evidence.get('sole_basis','').lower():
        raise ValueError('Player GPS cannot establish physical native ownership')
    path = evidence['authored_anchor_to_coast_path']
    target = [v//8 for v in row['global_tile']]
    if not path or path[0] != anchor['atlas'] or path[-1] != target:
        raise ValueError(('Authored coast path does not bind its actual interface',row['native_map'],target))
    if any(sum(abs(a-b) for a,b in zip(first,second)) != 1 for first,second in zip(path,path[1:])):
        raise ValueError(('Non-cardinal authored registration path',row['native_map']))
    samples = evidence['art_samples']
    for sample in samples:
        if truth.pixel(tuple(sample['atlas'])) != sample['palette_index']:
            raise ValueError(('Registration art sample changed',row['native_map'],sample))
    if truth.pixel(tuple(target)) != 2:
        raise ValueError(('Registered coast mouth is outside route ink',row['native_map'],target))
    return dict(immutable_art_bound=True,fixed_anchor_bound=True,
                exact_art_samples_checked=len(samples),cardinal_authored_path=True,
                geographic_registration_authored_not_recovered=True,
                independent_geographic_review_pending=evidence.get('independent_geographic_review_pending',True))


def census_native_bounds(inputs, registration_report):
    """Audit actual terrain under all proposed native patch exclusions.

    Pixel ownership can be mixed. The six-wide footprint belongs to generated
    geometry; an authentic native channel can be one tile wide. Consequently
    *any* real water of the registered component is recorded as a native
    witness, while full/partial core coverage remains a separate diagnostic.
    Rectangular native exclusions preserve dry/blocked native cells too.
    This proves source ownership of local patches, not global SCC or controls.
    """
    truth = decode_atlas(inputs.read('src/data/journey_world_map.h').decode())
    icons = protected_icon_witnesses(inputs,truth)
    blue = truth.blue_pixels-set(icons)
    rows = registration_report['registrations']
    _normalize_registrations(inputs,rows)
    by_key = {(r['native_map'],r['component']):r for r in rows}
    bounds = registration_report['adapter_plan']['native_bounds']
    if len(by_key) != len(rows) or {(b['native_map'],b['component']) for b in bounds} != set(by_key):
        raise ValueError('Native bounds and registrations do not cover the same unique components')
    all_pixels,patches,exclusions,owners = {},[],set(),{}
    for bound in bounds:
        name,component = bound['native_map'],bound['component']
        registration = by_key[name,component]
        authentication = _authenticate_registration(inputs,registration,truth)
        ox,oy = bound['origin']
        expected_origin = [registration['global_tile'][i]-registration['native_tile'][i] for i in (0,1)]
        if [ox,oy] != expected_origin or bound['local_rect'] != registration['local_rect']:
            raise ValueError(('Native patch differs from its authored interface',name,component))
        left,top,right,bottom = bound['local_rect']
        if bound['global_rect'] != [left+ox,top+oy,right+ox,bottom+oy]:
            raise ValueError(('Native global rectangle translation is inconsistent',name,component))
        labels,_ = inputs.water_components(name)
        cells,core_pixels,occupied_pixels = [],set(),set()
        for ny in range(top,bottom):
            for nx in range(left,right):
                gx,gy = ox+nx,oy+ny
                if (gx,gy) in owners:
                    raise ValueError(('Two native local frames claim the same physical tile',name,component,(gx,gy)))
                owners[gx,gy] = (name,component)
                point = gx//8,gy//8
                if point not in blue:
                    continue
                word = inputs.word(name,nx,ny)
                behavior = inputs.behavior(name,word)
                water = inputs.water(name,nx,ny)
                actual_component = labels.get((nx,ny))
                core = 1 <= gx%8 <= 6 and 1 <= gy%8 <= 6
                raster = _raster_cell((gx,gy),blue)
                matched = water and actual_component == component
                sample = dict(global_tile=[gx,gy],native_tile=[nx,ny],native_map=name,
                    registered_component=component,actual_component=actual_component,
                    word=word,metatile=word&1023,collision=(word>>10)&3,
                    elevation=word>>12,behavior=behavior,surfable_passable=water,
                    expected_component_water=matched,generated_core_cell=core,
                    generated_raster_cell=raster)
                cells.append(sample)
                pixel = all_pixels.setdefault(point,dict(atlas=list(point),cells=[]))
                pixel['cells'].append(sample)
                if core:
                    core_pixels.add(point)
                if raster:
                    exclusions.add((gx,gy));occupied_pixels.add(point)
        patches.append(dict(native_map=name,component=component,origin=[ox,oy],
            local_rect=list(bound['local_rect']),global_rect=list(bound['global_rect']),
            registration_authentication=authentication,
            blue_pixels_touched=_ordered({tuple(c['global_tile'][i]//8 for i in (0,1)) for c in cells}),
            blue_core_pixels_touched=_ordered(core_pixels),
            blue_raster_pixels_touched=_ordered(occupied_pixels),
            raster_cells_to_preserve_as_native=sum(c['generated_raster_cell'] for c in cells),
            raster_water_cells_of_expected_component=sum(c['generated_raster_cell'] and c['expected_component_water'] for c in cells),
            native_higher_water_requires_runtime_proof=any(c['elevation'] not in (0,1,15) and c['expected_component_water'] for c in cells),
            cells=cells))
    pixels_out=[]
    for point,pixel in sorted(all_pixels.items(),key=lambda pair:(pair[0][1],pair[0][0])):
        cells=pixel['cells'];core=[c for c in cells if c['generated_core_cell']]
        core_water=[c for c in core if c['expected_component_water']]
        raster=[c for c in cells if c['generated_raster_cell']]
        witnesses=[c for c in cells if c['expected_component_water']]
        pixel.update(native_core_cells=len(core),native_core_water_cells=len(core_water),
            native_raster_cells=len(raster),native_water_witness_cells=len(witnesses),
            full_generated_core_is_native_water=len(core_water)==36,
            source_native_witness_proven=bool(witnesses),
            ownership='mixed-native-and-generated' if len(core_water)<36 else 'complete-core-native-water',
            water_heights=sorted({c['elevation'] for c in witnesses}),
            global_scc_return_proven=False,native_controls_proven=False)
        pixels_out.append(pixel)
    core_rows=[p for p in pixels_out if p['native_core_cells']]
    raster_rows=[p for p in pixels_out if p['native_raster_cells']]
    full=[p['atlas'] for p in core_rows if p['full_generated_core_is_native_water']]
    partial=[p['atlas'] for p in core_rows if not p['full_generated_core_is_native_water']]
    inputs.assert_unchanged()
    return dict(kind='atlas-native-local-ownership-source-preview/v1',
        ownership_model='Exact native terrain under authored local interface frames; mixed pixels allowed',
        art_sha256=dict(truth.array_sha256),patch_count=len(patches),
        blue_pixel_count=len(truth.blue_pixels),icon_pixels=_ordered(icons),
        blue_core_overlap_pixel_count=len(core_rows),blue_raster_overlap_pixel_count=len(raster_rows),
        blue_any_patch_overlap_pixel_count=len(pixels_out),
        native_core_water_cell_count=sum(p['native_core_water_cells'] for p in core_rows),
        native_core_nonwater_or_other_component_cell_count=sum(p['native_core_cells']-p['native_core_water_cells'] for p in core_rows),
        fully_native_core_pixels=full,partially_native_core_pixels=partial,
        native_candidate_pixels=[p['atlas'] for p in pixels_out if p['source_native_witness_proven']],
        indeterminate_pixels=[p['atlas'] for p in pixels_out if not p['source_native_witness_proven']],
        remove_generated_global_cells=_ordered(exclusions),
        removal_policy='Exclude complete native global rectangles, retaining native water AND blocked/dry cells',
        patches=patches,pixels=pixels_out,
        old_player_gps_used=False,native_scale_8_assumed=False,
        six_by_six_native_core_required_for_witness=False,
        source_local_component_membership_verified=True,
        global_scc_return_proven=False,native_controls_proven=False,
        geographic_registrations_independent_review_complete=False,
        physical_classification_complete=False,final_release_validated=False,
        pending=['Independent geographic review of authored interface locations',
                 'Directed global SCC and return through the actual native adapter mouths',
                 'Native control proof, especially height3 EverGrande and narrow mouths'],
        input_sha256=dict(inputs.inputs))


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
    """Locate native witnesses without imposing generated width on native maps.

    A witnessed pixel can have mixed owners. ``native_pixels`` therefore names
    pixels with a source witness, not a license to delete a whole six-wide
    generated footprint. Integration must use the exact native patch bounds
    and prove its real mouth/return in the final network. Use
    ``census_native_bounds`` for the per-cell exclusion evidence.
    """
    truth = decode_atlas(inputs.read('src/data/journey_world_map.h').decode())
    water, rows, seams = registered_water(inputs,registrations)
    witnesses, partial, incompatible = {}, [], []
    for point in sorted(truth.blue_pixels,key=lambda p:(p[1],p[0])):
        x,y = point
        core = {(x*8+dx,y*8+dy) for dy in range(1,7) for dx in range(1,7)}
        footprint = {(x*8+dx,y*8+dy) for dy in range(8) for dx in range(8)}
        covered = footprint & water.keys()
        if not covered:
            continue
        records = [water[p] for p in sorted(covered,key=lambda p:(p[1],p[0]))]
        covered_core = core & covered
        # Native height3 Surf is retained, but its generated approach and
        # actual avatar mode still need independent native movement proof.
        bad = [r for r in records if r['word'] >> 12 not in (0,1,15)]
        if bad:
            incompatible.append(dict(atlas=list(point),cells=bad))
        witnesses[point] = [dict(**record,atlas=list(point),surfable=True)
                            for record in records]
        if covered_core != core:
            partial.append(dict(atlas=list(point),native_cells=len(covered_core),
                                core_cells=36,cells=records,
                                missing_global_cells=_ordered(core-covered_core),
                                nonstandard_native_height_cells=len(bad)))
    icons = protected_icon_witnesses(inputs,truth) if icon_witnesses is None else icon_witnesses
    result = classify_pixels(truth,native_witnesses=witnesses,
                             icon_witnesses=icons,accesses=accesses)
    expected = {(row['native_map'],row['component']) for row in expected_components}
    registered = {(row['map'],component) for row in rows for component in row['components']}
    missing = sorted(expected-registered)
    result.update(kind='atlas-registered-native-classification',registrations=rows,
                  native_registration_seams=seams,partial_native_pixel_coverage=partial,
                  native_water_heights_require_runtime_proof=incompatible,
                  all_native_pixel_cores_physically_covered=not partial,
                  authored_registrations_read_from_external_plan=True,
                  registration_geography_independently_certified=False,
                  partial_pixels_require_exclusive_game_tile_ownership=bool(partial),
                  native_pixel_list_is_witness_inventory_not_full_pixel_exclusion=True,
                  native_core_width_six_required=False,
                  global_scc_return_proven=False,
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
        if 'adapter_plan' in data and 'native_bounds' in data['adapter_plan']:
            report = census_native_bounds(source,data)
        else:
            report['classification'] = classify_registered_native(source,data['registrations'],
                accesses=data.get('accesses',()),expected_components=data.get('expected_components',()))
        report['registration_file_sha256'] = hashlib.sha256(args.registrations.read_bytes()).hexdigest()
    report['tool_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report['input_sha256'] = dict(source.inputs)
    source.assert_unchanged()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    summary = dict(physical_classification_complete=False,output=str(args.output))
    if 'regional_art' in report:
        summary['regional_art_blue_pixels'] = report['regional_art']['surviving_native_art_blue_count']
    else:
        summary.update(core_pixels=report['blue_core_overlap_pixel_count'],
                       raster_pixels=report['blue_raster_overlap_pixel_count'],
                       complete_native_cores=len(report['fully_native_core_pixels']),
                       partial_native_cores=len(report['partially_native_core_pixels']))
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
