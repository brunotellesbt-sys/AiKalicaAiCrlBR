"""Find coast interfaces by native water component, without choosing fake exits."""
from collections import defaultdict
import copy
import hashlib
import json
import struct

from atlas_surf_source import compatible_height, CARDINAL, OPPOSITE
from atlas_surf_geometry import chunk_water


def edge_pairs(inputs, interface):
    old, native = interface['retired_map'], interface['native_map']
    direction, offset = interface['direction'], interface['offset']
    a, b = inputs.layout(old), inputs.layout(native)
    axis = 'height' if direction in ('left', 'right') else 'width'
    for value in range(max(0, offset), min(a[axis], offset+b[axis])):
        source = ((a['width']-1 if direction == 'right' else 0), value) if direction in ('left', 'right') else (value, a['height']-1 if direction == 'down' else 0)
        target = ((0 if direction == 'right' else b['width']-1), value-offset) if direction in ('left', 'right') else (value-offset, 0 if direction == 'down' else b['height']-1)
        if inputs.water(old, *source) and inputs.water(native, *target):
            first, second = inputs.word(old, *source), inputs.word(native, *target)
            yield dict(retired_tile=list(source), native_tile=list(target), words=[first, second],
                       height_compatible=compatible_height(first, second))


def inventory(inputs, coast_inventory):
    """Group every existing wet border by *real native terrain* component.

    Different edges may reach the same native sea; separate pools remain
    separate. Route114's explicitly rejected interior-lagoon exit is recorded
    but never promoted to an ocean adapter. This does not create connections.
    """
    groups = defaultdict(list)
    closed, dry = [], []
    for interface in coast_inventory['native_interfaces']:
        cells = list(edge_pairs(inputs, interface))
        if interface['native_map'] == 'Route114':
            closed.append(dict(**interface, wet_pairs=cells,
                               reason='explicitly rejected interior-lagoon ocean link; close cells(0,17)/(0,18)'))
            continue
        if not cells:
            dry.append(dict(**interface, reason='no passable Surf pair on this existing border'))
            continue
        if not interface['reciprocal']:
            raise ValueError(('Unreciprocated wet coast must be diagnosed before adapting', interface))
        name = interface['native_map']
        labels, components = inputs.water_components(name)
        for cell in cells:
            component = labels[tuple(cell['native_tile'])]
            groups[name, component].append(dict(**cell, retired_map=interface['retired_map'],
                                                direction=interface['direction'], offset=interface['offset']))
    rows = []
    for (name, index), witnesses in sorted(groups.items()):
        labels, components = inputs.water_components(name)
        cells = sorted(components[index], key=lambda p: (p[1], p[0]))
        encoded = ';'.join(f'{x},{y}' for x, y in cells).encode()
        rows.append(dict(native_map=name, component=index, seed=list(cells[0]),
                         water_cells=len(cells), component_sha256=hashlib.sha256(encoded).hexdigest(),
                         source_wet_edge_witnesses=witnesses,
                         traversable_contact_count=sum(row['height_compatible'] for row in witnesses),
                         boundary_height_review_required=not any(row['height_compatible'] for row in witnesses),
                         native_height_zero_transitions_preserved=True,
                         destination_assigned=False))
    return dict(kind='atlas-native-water-component-interfaces', adapters=rows,
                native_hosts=sorted({row['native_map'] for row in rows}),
                closed_lagoon_links=closed, existing_dry_interfaces=dry,
                source_terrain_components_only=True,
                currently_height_compatible_components=sum(not r['boundary_height_review_required'] for r in rows),
                runtime_bridge_and_connection_policy_certified=False,
                global_reachability_proven=False, native_validated=False)


def _point(value, label):
    if (not isinstance(value, (list, tuple)) or len(value) != 2
            or any(type(v) is not int for v in value)):
        raise ValueError(('Expected integer coordinate pair', label, value))
    return tuple(value)


def _rect(value, label):
    if (not isinstance(value, (list, tuple)) or len(value) != 4
            or any(type(v) is not int for v in value)
            or value[0] >= value[2] or value[1] >= value[3]):
        raise ValueError(('Expected exclusive rectangle', label, value))
    return tuple(value)


def _overlap(a, b):
    return max(a[0], b[0]) < min(a[2], b[2]) and max(a[1], b[1]) < min(a[3], b[3])


def _banks(inputs, name):
    layout = inputs.layout(name)
    return [layout['primary_tileset'], layout['secondary_tileset'], layout['layout_version']]


def _edge_point(layout, point, direction):
    x, y = point
    return ((direction == 'left' and x == 0) or
            (direction == 'right' and x == layout['width']-1) or
            (direction == 'up' and y == 0) or
            (direction == 'down' and y == layout['height']-1))


def native_edge_witnesses(row):
    return row['source_wet_edge_witnesses']+row.get('authored_native_edge_witnesses',[])


def _water(plan):
    result = set()
    for chunk in plan['chunks']:
        ox, oy = chunk['origin']
        result.update((ox+x, oy+y) for x, y in chunk_water(chunk))
    return result


def _runs(cells, origin):
    rows = defaultdict(list)
    for x, y in cells:
        rows[y-origin[1]].append(x-origin[0])
    runs = []
    for y, xs in sorted(rows.items()):
        xs.sort()
        first = previous = xs[0]
        for x in xs[1:]:
            if x != previous+1:
                runs.append([y, first, previous+1]); first = x
            previous = x
        runs.append([y, first, previous+1])
    return runs


def _art_registration(inputs, truth, registration):
    """Bind an explicit local registration to fixed art and a source anchor.

    This verifies reproducible evidence, not the semantic choice of a city
    shoreline. That choice remains visible in the registration for independent
    geographic review; an old interpolated player GPS is never sufficient.
    """
    evidence = registration['atlas_evidence']
    if evidence.get('art_sha256') != dict(truth.array_sha256):
        raise ValueError('Adapter registration is not bound to the immutable atlas')
    fixed = evidence.get('fixed_anchor', {})
    anchors = inputs.anchors()
    if (fixed.get('map') not in anchors or fixed.get('atlas') != anchors[fixed['map']]['atlas']
            or not evidence.get('geographic_basis') or not evidence.get('native_coast_basis')):
        raise ValueError('Adapter needs an authenticated fixed anchor and explicit coastal evidence')
    if evidence.get('sole_basis') in ('old-gps', 'nearest-gps', 'map-center'):
        raise ValueError('An interpolated GPS or arbitrary map center is not coastal proof')
    samples = evidence.get('art_samples')
    if not samples:
        raise ValueError('Adapter registration needs actual sampled coast/route pixels')
    positions = set()
    for sample in samples:
        point = _point(sample['atlas'], 'art sample')
        if sample['palette_index'] != truth.pixel(point):
            raise ValueError(('Atlas coast sample differs from immutable art', point))
        positions.add(point)
    global_tile = _point(registration['global_tile'], 'global_tile')
    pixel = global_tile[0]//8, global_tile[1]//8
    if pixel not in positions or truth.pixel(pixel) != 2:
        raise ValueError('Native interface must have a sampled blue-route registration')
    return copy.deepcopy(evidence)


def _mouth(inputs, row, registration):
    name, direction = row['native_map'], registration['direction']
    anchor = _point(registration['native_tile'], 'native_tile')
    layout = inputs.layout(name)
    if direction not in CARDINAL or not _edge_point(layout, anchor, direction):
        raise ValueError(('Adapter must leave the real native map edge', name, direction, anchor))
    witnesses = {tuple(w['native_tile']): w for w in native_edge_witnesses(row)
                 if OPPOSITE[w['direction']] == direction}
    if anchor not in witnesses:
        raise ValueError(('Adapter anchor is not an authenticated old wet edge', name, anchor))
    labels, _ = inputs.water_components(name)
    if labels.get(anchor) != row['component']:
        raise ValueError('Adapter anchor belongs to another native water component')
    axis = 1 if direction in ('left', 'right') else 0
    available = {p[axis]: p for p in witnesses
                 if labels.get(p) == row['component']
                 and compatible_height(inputs.word(name, *anchor), inputs.word(name, *p))}
    center = anchor[axis]
    left = right = center
    while left-1 in available: left -= 1
    while right+1 in available: right += 1
    width = registration.get('mouth_width', 6)
    if type(width) is not int or not 1 <= width <= 6 or right-left+1 < width:
        raise ValueError(('Native coast lacks the requested contiguous wet mouth', name, width))
    start = max(left, min(center-width//2, right-width+1))
    cells = [available[value] for value in range(start, start+width)]
    return anchor, cells, [copy.deepcopy(witnesses[p]) for p in cells]


def face_witnesses(inputs,row,mouth,origin,direction,cells,near,*,allow_extensions=False):
    """Authenticate the whole real face, including wet raster corner cells.

    A six-wide core can have an eight-wide face at an atlas junction. Those
    extra contacts retain the same actual native water component/elevation.
    Reopening a blocked old-ocean corner additionally requires an explicit
    authored opt-in, the bounded reciprocal old interface and hashes/words of
    both terrains. Unknown openings still fail; native terrain is not edited.
    """
    name=row['native_map'];layout=inputs.layout(name);dx,dy=CARDINAL[direction]
    known={tuple(w['native_tile']):w for w in native_edge_witnesses(row)
           if OPPOSITE[w['direction']]==direction}
    labels,_=inputs.water_components(name);result={p:copy.deepcopy(known[p]) for p in mouth}
    base=inputs.word(name,*mouth[0])
    for x,y in cells:
        if (x if dx else y)!=near:continue
        p=x-origin[0]-dx,y-origin[1]-dy
        if not(0<=p[0]<layout['width'] and 0<=p[1]<layout['height']) or not inputs.water(name,*p):continue
        if labels.get(p)!=row['component'] or not compatible_height(base,inputs.word(name,*p)):
            raise ValueError(('Unregistered native water opening beside adapter mouth',name,p))
        if p in known:result[p]=copy.deepcopy(known[p]);continue
        if not allow_extensions or not hasattr(inputs,'read'):
            raise ValueError(('Unregistered native water opening beside adapter mouth',name,p))
        # The old ocean can have a blocked corner next to a genuine native
        # water cell. A newly authored blue-ink junction may reopen that corner;
        # authenticate BOTH old words and preserve the native map unchanged.
        matches=[]
        for old,d,offset in sorted({(w['retired_map'],w['direction'],w['offset'])
                                    for w in row['source_wet_edge_witnesses'] if OPPOSITE[w['direction']]==direction}):
            old_layout=inputs.layout(old)
            q=(old_layout['width']-1 if dx<0 else 0,p[1]+offset) if dx else (p[0]+offset,old_layout['height']-1 if dy<0 else 0)
            if not(0<=q[0]<old_layout['width'] and 0<=q[1]<old_layout['height']):continue
            word=inputs.word(name,*p);old_word=inputs.word(old,*q)
            matches.append(dict(native_tile=list(p),retired_tile=list(q),retired_map=old,
                direction=d,offset=offset,words=[old_word,word],height_compatible=compatible_height(old_word,word),
                newly_authored_corner_contact=True,old_neighbor_passable=inputs.water(old,*q),
                native_word_preserved=True,
                native_blockdata_sha256=hashlib.sha256(inputs.read(layout['blockdata_filepath'])).hexdigest(),
                old_blockdata_sha256=hashlib.sha256(inputs.read(old_layout['blockdata_filepath'])).hexdigest()))
        if not matches:
            raise ValueError(('Native corner extension lacks a bounded historical neighbor',name,p))
        result[p]=matches[0]
    return [result[p] for p in sorted(result,key=lambda p:(p[1],p[0]))]


def plan_adapters(inputs, component_inventory, plan, registrations, truth, *, require_complete=True):
    """Place real coast interfaces using independently reviewed local records.

    Registration schema: native_map/component, native_tile on the real edge,
    global_tile for that exact cell, outward direction, local_rect [l,t,r,b]
    of the authenticated native patch, atlas_evidence and a bank-specific donor
    {map, water_tile, reef_tile}. ``depth`` defaults to eight generated tiles.

    Native continents retain their own maps/projections. An interface origin
    is LOCAL to its registered patch; it is not a fabricated global embedding
    of an entire native city. Every adapter is straight and uses only water
    already in the affine route plan. Missing/ambiguous records fail closed.
    """
    if plan['scale'] != 8 or plan['corridor_width'] != 6:
        raise ValueError('Adapter scale differs from the affine ocean contract')
    rows = {(r['native_map'], r['component']): r for r in component_inventory['adapters']}
    supplied = [(r['native_map'], r['component']) for r in registrations]
    if len(set(supplied)) != len(supplied) or not set(supplied) <= set(rows):
        raise ValueError('Duplicate or unknown native component registration')
    if require_complete and set(supplied) != set(rows):
        raise ValueError(('Missing native coast registrations', sorted(set(rows)-set(supplied))))
    water = _water(plan)
    reservations, bounds, bindings = [], [], []
    for number, registration in enumerate(sorted(registrations, key=lambda r: (r['native_map'], r['component']))):
        key = registration['native_map'], registration['component']
        row = rows[key]; name, component = key
        if name == 'Route114':
            raise ValueError('The rejected Route114 lagoon cannot become an ocean adapter')
        native, mouth, witnesses = _mouth(inputs, row, registration)
        evidence = _art_registration(inputs, truth, registration)
        glob = _point(registration['global_tile'], 'global_tile')
        origin = glob[0]-native[0], glob[1]-native[1]
        patch = _rect(registration['local_rect'], 'native patch')
        layout = inputs.layout(name)
        if not (0 <= patch[0] < patch[2] <= layout['width'] and
                0 <= patch[1] < patch[3] <= layout['height'] and
                all(patch[0] <= x < patch[2] and patch[1] <= y < patch[3] for x,y in mouth)):
            raise ValueError(('Native patch must contain the registered mouth', name, patch))
        for prior in bounds:
            if prior['native_map'] == name and _overlap(patch, prior['local_rect']) and list(origin) != prior['origin']:
                raise ValueError('Overlapping native patches cannot have conflicting local registrations')
        direction = registration['direction']; dx, dy = CARDINAL[direction]
        depth = registration.get('depth', 8)
        if type(depth) is not int or not 8 <= depth <= 120:
            raise ValueError('Adapter needs a bounded eight-tile native graphics apron')
        tangent = 1 if dx else 0
        first = min(p[tangent] for p in mouth)+origin[tangent]-1
        if direction == 'left': rect = (glob[0]-depth, first, glob[0], first+len(mouth)+2)
        elif direction == 'right': rect = (glob[0]+1, first, glob[0]+1+depth, first+len(mouth)+2)
        elif direction == 'up': rect = (first, glob[1]-depth, first+len(mouth)+2, glob[1])
        else: rect = (first, glob[1]+1, first+len(mouth)+2, glob[1]+1+depth)
        for prior in reservations:
            other = (*prior['origin'], prior['origin'][0]+prior['width'], prior['origin'][1]+prior['height'])
            if _overlap(rect, other):
                raise ValueError(('Native adapter reservations overlap', name, prior['name']))
        cells = {p for p in water if rect[0] <= p[0] < rect[2] and rect[1] <= p[1] < rect[3]}
        contacts = {(x+origin[0]+dx,y+origin[1]+dy) for x,y in mouth}
        if not contacts <= cells:
            raise ValueError(('Native mouth does not meet the existing affine route water', name,
                              sorted(contacts-cells)))
        # All generated water at this native face must refer to the same
        # authenticated source component/contact, including padded corners.
        near = glob[0]+dx if dx else glob[1]+dy
        witnesses=face_witnesses(inputs,row,mouth,origin,direction,cells,near,
                                 allow_extensions=registration.get('allow_extended_native_contacts',False))
        far = glob[0]+depth*dx if dx else glob[1]+depth*dy
        far_cells = {p for p in cells if p[0 if dx else 1] == far}
        if not far_cells or not any((x+dx,y+dy) in water and not (rect[0] <= x+dx < rect[2] and rect[1] <= y+dy < rect[3])
                                    for x,y in far_cells):
            raise ValueError(('Adapter does not return to the existing route at its outer face', name))
        # Do not admit a disconnected decoration pool or a path that turns
        # behind the native edge inside this short bridge.
        seen = set(contacts); todo = list(contacts)
        for x,y in todo:
            for ax,ay in CARDINAL.values():
                target = x+ax,y+ay
                if target in cells and target not in seen:
                    seen.add(target); todo.append(target)
        if seen != cells or not far_cells <= seen:
            raise ValueError('Adapter raster is not one returning water component')
        donor = copy.deepcopy(registration['donor'])
        if _banks(inputs, donor['map']) != _banks(inputs, name):
            raise ValueError(('Adapter donor has foreign native banks', name, donor['map']))
        wet = inputs.word(donor['map'], *_point(donor['water_tile'], 'water donor'))
        reef = inputs.word(donor['map'], *_point(donor['reef_tile'], 'reef donor'))
        if not inputs.water(donor['map'], *donor['water_tile']) or wet >> 12 != 1 or not reef & 0xC00:
            raise ValueError('Adapter needs real height1 water and a blocked reef in its own banks')
        heights = {inputs.word(name,*w['native_tile']) >> 12 for w in witnesses}
        selected = next((h for h in (1,3,0,15) if h in heights), None)
        if selected is None or not all(compatible_height(h<<12,selected<<12) for h in heights):
            raise ValueError(('Mouth has incompatible native elevations', name, heights))
        adapter_height = 3 if selected == 3 else 1
        overrides = []
        lateral_transitions=[]
        if adapter_height != 1:
            for x,y in sorted(cells, key=lambda p:(p[1],p[0])):
                distance = (x-glob[0])*dx+(y-glob[1])*dy
                height = 1 if distance == depth else 0 if distance == depth-1 else adapter_height
                # A route can also meet a SIDE of the new adapter at an ink
                # junction. Preserve the complete native face at height3;
                # only new water at least one step away from it can receive
                # the same transition already used at the far ocean face.
                if 2<=distance<depth-1 and any((x+ax,y+ay) in water
                        and not(rect[0]<=x+ax<rect[2] and rect[1]<=y+ay<rect[3])
                        for ax,ay in CARDINAL.values()):
                    height=0;lateral_transitions.append([x-rect[0],y-rect[1]])
                if height != 1:
                    overrides.append(dict(tile=[x-rect[0],y-rect[1]],word=(wet&0xFFF)|(height<<12)))
        adapter_name = f'JourneyAtlasCoast{number:02}'
        adapter_id = 'MAP_'+adapter_name.upper()
        offset = rect[tangent]-origin[tangent]
        reservation = dict(name=adapter_name,id=adapter_id,origin=list(rect[:2]),
                           width=rect[2]-rect[0],height=rect[3]-rect[1],kind='adapter',
                           water_runs=_runs(cells,rect[:2]),donor=donor,ecology_owner=name,
                           banks=_banks(inputs,name),word_overrides=overrides,
                           native_component=component)
        reservations.append(reservation)
        bounds.append(dict(native_map=name,component=component,origin=list(origin),local_rect=list(patch),
                           global_rect=[patch[0]+origin[0],patch[1]+origin[1],patch[2]+origin[0],patch[3]+origin[1]],
                           interface_local_only=True,banks=_banks(inputs,name)))
        bindings.append(dict(native_map=name,component=component,native_tile=list(native),global_tile=list(glob),
                             adapter=adapter_name,adapter_id=adapter_id,direction=direction,
                             native_connection=dict(direction=direction,map=adapter_id,offset=offset),
                             adapter_connection=dict(direction=OPPOSITE[direction],map=inputs.maps[name]['id'],offset=-offset),
                             source_wet_mouth=witnesses,native_heights=sorted(heights),
                             adapter_height=adapter_height,transition_height_zero_only_in_new_adapter=bool(overrides),
                             lateral_height_transitions=lateral_transitions,
                             atlas_evidence=evidence))
    return dict(kind='atlas-local-native-adapter-plan/v1',reservations=reservations,native_bounds=bounds,
                bindings=bindings,complete_component_coverage=set(supplied)==set(rows),
                native_terrain_events_and_heights_unchanged=True,old_player_gps_used_as_proof=False,
                generated_water_not_added_or_redirected=True,geographic_registration_requires_independent_review=True,
                source_prepared=False,native_validated=False)


def stage_bindings(layer, adapter_plan, *, retired_maps):
    """Install reciprocal coast links and new-adapter height transitions only.

    Call after chunk/reservation materialization. Retiring the old oceans,
    scenery, ecology, save migration and native control proofs are separate.
    """
    from badge_story_layer import read
    if not adapter_plan['complete_component_coverage']:
        raise ValueError('Refusing to stage a partial native coast replacement')
    retired = {name if name.startswith('MAP_') else
               json.loads(read(layer,f'data/maps/{name}/map.json'))['id']
               for name in retired_maps}
    bindings = adapter_plan['bindings']
    native_maps = {}
    preserved = {}
    for name in sorted({row['native_map'] for row in bindings}):
        path = f'data/maps/{name}/map.json'
        value = json.loads(read(layer,path)); native_maps[name] = value
        preserved[name] = {key:copy.deepcopy(value.get(key,[])) for key in
                           ('object_events','warp_events','coord_events','bg_events')}
        value['connections'] = [row for row in value.get('connections') or []
                                if row.get('map') not in retired]
    for binding in bindings:
        native = native_maps[binding['native_map']]
        connection = binding['native_connection']
        if any(c == connection for c in native['connections']):
            raise ValueError('Native adapter link already installed')
        native['connections'].append(copy.deepcopy(connection))
        path = f"data/maps/{binding['adapter']}/map.json"
        mapping = json.loads(read(layer,path))
        if mapping['id'] != binding['adapter_id']:
            raise ValueError('Materialized coast ID differs from its plan')
        mapping['connections'].append(copy.deepcopy(binding['adapter_connection']))
        layer.stage(path,json.dumps(mapping,indent=2)+'\n')
    for name,value in native_maps.items():
        if any(value.get(k,[]) != v for k,v in preserved[name].items()):
            raise ValueError('Native actor or event changed while connecting its coast')
        layer.stage(f'data/maps/{name}/map.json',json.dumps(value,indent=2)+'\n')
    layouts = {r['id']:r for r in json.loads(read(layer,'data/layouts/layouts.json'))['layouts']}
    for reservation in adapter_plan['reservations']:
        if not reservation['word_overrides']: continue
        mapping = json.loads(read(layer,f"data/maps/{reservation['name']}/map.json"))
        layout = layouts[mapping['layout']]
        path = layout['blockdata_filepath']; raw = read(layer,path)
        words = list(struct.unpack('<'+'H'*(len(raw)//2),raw))
        for override in reservation['word_overrides']:
            x,y = override['tile']; at = y*layout['width']+x
            if not (0 <= x < layout['width'] and 0 <= y < layout['height']) or words[at]&0xC00:
                raise ValueError('Height transition must be inside new passable adapter water')
            if words[at]&0xFFF != override['word']&0xFFF:
                raise ValueError('Adapter transition cannot change metatile or collision')
            words[at] = override['word']
        layer.stage(path,struct.pack('<'+'H'*len(words),*words))
    return dict(kind='atlas-native-adapter-links-staged',bindings=len(bindings),
                native_maps=len(native_maps),native_actors_events_preserved=True,
                native_blockdata_not_modified=True,retirement_and_native_validation_pending=True)
