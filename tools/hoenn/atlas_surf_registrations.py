"""Concrete, authored coast registrations against immutable atlas/source.

These are new physical design choices, not recovered layer172 coordinates.
Each finite choice follows a named native coast and sampled atlas ink; phase
search only fits its real mouth to the existing 8-tile/6-tile raster. It never
consults interpolated player GPS, paints new ink, or embeds a whole continent.
The resulting source plans still require geographic review, SCC and ROM travel.
"""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

from atlas_surf_adapters import _mouth, edge_pairs, plan_adapters
from atlas_surf_geometry import plan_geometry, chunk_water
from atlas_surf_source import CARDINAL, OPPOSITE, Source
from atlas_surf_truth import decode_atlas


# Coordinates below are explicit new design proposals, in atlas pixels. A
# tangent shift follows the visible shore before the final outward ray. The
# source mouth and all phases are independently checked below.
AUTHORED_COASTS = {
    ('BirthIsland_Exterior_Frlg',0): [('left',(196,107),'western approach on the horizontal Birth route')],
    ('BirthIsland_Harbor_Frlg',0): [('right',(200,107),'eastern harbor approach on the same Birth route')],
    ('CinnabarIsland_Frlg',0): [('down',(33,62),'blue stem immediately south of the Cinnabar icon')],
    ('EverGrandeCity',1): [('down',(141,98),'southeastern lower coast on the vertical route east of Ever Grande')],
    ('EverGrandeCity',2): [('right',(141,94),'upper eastern coast at the west end of the eastbound route')],
    ('FiveIsland_Frlg',0): [('left',(187,79),'western route segment approaching Five Island')],
    ('FourIsland_Frlg',0): [('left',(155,68),'southwestern shoreline where the westbound ink meets Four Island')],
    ('JourneyRoute12Shipyard',0): [('up',(96,38),'short northern inlet above the fixed Lavender Port icon')],
    ('JourneyRoute12Shipyard',1): [('down',(96,42),'southbound route directly below Lavender Port')],
    ('MossdeepCity',1): [('right',(132,82),'northeastern Mossdeep coast, above the southern water component')],
    ('MossdeepCity',4): [('right',(132,84),'southeastern Mossdeep coast on the horizontal ocean route')],
    ('NavelRock_Harbor_Frlg',0): [
        ('up',(176,70),'northern Navel Rock approach at the vertical ink above its icon'),
        ('down',(180,75),'southeastern Navel Rock approach where the southbound route leaves the east-west ink')],
    ('OneIsland_Frlg',1): [('left',(131,39),'westbound route immediately west of One Island')],
    ('OneIsland_TreasureBeach_Frlg',0): [('down',(135,48),'southbound route below the Treasure Beach shoreline')],
    ('Route105',0): [('left',(18,101),'westbound route west of the Route105 section anchor')],
    ('Route115',0): [('left',(16,77),'westbound ocean route outside the west coast of Route115')],
    ('Route124',0): [('up',(114,78),'northbound ocean route from the Route124 section')],
    ('Route125',0): [('right',(132,78),'eastbound route along the northeastern Route125 coast')],
    ('Route126',2): [('down',(114,92),'southern blue stem below the island centered on the Route126 anchor')],
    ('Route127',0): [('right',(127,89),'eastbound ink before the separately reviewed native coastal gap')],
    ('Route128',1): [('up',(128,94),'northbound eastern Hoenn route above the Route128 section')],
    ('Route129',0): [('down',(128,99),'southbound eastern Hoenn route below the Route129 section')],
    ('Route12_Frlg',1): [('right',(98,39),'eastbound route beside the upper Route12 coast')],
    ('Route12_Frlg',5): [('right',(97,49),'eastbound junction beside the separate lower Route12 inlet')],
    ('Route130',0): [('up',(114,98),'northbound western junction of the Route130 ocean line')],
    ('Route13_Frlg',0): [('down',(87,54),'southbound blue route directly below Route13')],
    ('Route14_Frlg',0): [('down',(81,54),'southbound blue route below the two-cell native southern mouth')],
    ('Route19_Frlg',1): [
        ('right',(73,60),'southern ocean line east of Route19, before its eastern vertical branch'),
        ('right',(76,60),'southern ocean line east of the Route19 offshore junction')],
    ('SevenIsland_Frlg',1): [('left',(159,102),'westbound route just west of Seven Island')],
    ('SevenIsland_TanobyRuins_Frlg',0): [('left',(163,105),'northwestern Tanoby shoreline on the westbound ink below Seven Island')],
    ('SixIsland_Frlg',1): [('left',(193,96),'western Six Island shoreline at the eastern end of the westbound ink')],
    ('ThreeIsland_Port_Frlg',1): [('left',(197,53),'western Three Island shoreline at the east end of the westbound route')],
    ('TwoIsland_Frlg',0): [('left',(163,43),'southwestern Two Island shoreline on the westbound route')],
}


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _banks(inputs, name):
    row = inputs.layout(name)
    return row['primary_tileset'], row['secondary_tileset'], row['layout_version']


def _donor(inputs, row):
    banks = _banks(inputs,row['native_map'])
    names = {w['retired_map'] for w in row['source_wet_edge_witnesses']}
    # Several old links used a foreign graphics bank even though the native
    # host has an authenticated matching connector elsewhere. The donor is
    # selected by the complete actual bank tuple, never by metatile number.
    names.update(name for name in inputs.maps if name.startswith('Journey'))
    names.add(row['native_map'])
    eligible = []
    for name in names:
        if _banks(inputs,name) != banks:
            continue
        layout = inputs.layout(name)
        words = inputs.words(name)
        blocked = Counter(word for word in words if word & 0xC00)
        if not blocked or not name.startswith('Journey') or len(blocked) != 1:
            continue
        reef_word = blocked.most_common(1)[0][0]
        reef = words.index(reef_word)
        wet = next((i for i,word in enumerate(words) if word >> 12 == 1
                    and inputs.water(name,i%layout['width'],i//layout['width'])),None)
        if wet is not None:
            donor = dict(map=name,water_tile=[wet%layout['width'],wet//layout['width']],
                         reef_tile=[reef%layout['width'],reef//layout['width']])
            evidence = dict(map=name,banks=list(banks),water_word=words[wet],reef_word=reef_word,
                            blockdata=layout['blockdata_filepath'],
                            blockdata_sha256=_sha(inputs.read(layout['blockdata_filepath'])),
                            reef_basis='blocked perimeter cell of the authenticated old coast connector',
                            visual_review_pending=True)
            eligible.append((not name.startswith('JourneySurfLink'),name,donor,evidence))
    if eligible:
        _,_,donor,evidence = min(eligible,key=lambda value:value[:2])
        return donor,evidence
    raise ValueError(('No bank-matched height1 water and blocked perimeter donor',row['native_map']))


def _mouths(inputs,row,direction):
    witnesses = sorted({tuple(w['native_tile']) for w in row['source_wet_edge_witnesses']
                        if OPPOSITE[w['direction']] == direction})
    axis = 1 if direction in ('left','right') else 0
    for width in range(6,0,-1):
        found = {}
        for anchor in witnesses:
            try:
                native,cells,proof = _mouth(inputs,row,dict(direction=direction,native_tile=anchor,mouth_width=width))
            except ValueError:
                continue
            key = tuple(cells)
            center = cells[0][axis]+width//2
            score = abs(native[axis]-center),native
            if key not in found or score < found[key][0]:
                found[key] = score,(native,cells,proof)
        if found:
            # A width below six is accepted only when no contiguous native
            # mouth of six (or any larger attempted width) exists here.
            middle = (min(p[axis] for p in witnesses)+max(p[axis] for p in witnesses))/2
            return sorted((value[1] for value in found.values()),
                          key=lambda value:(abs(value[0][axis]-middle),value[0]))
    return []


def _authenticate_witnesses(inputs,row):
    name = row['native_map']
    interfaces = {}
    for witness in row['source_wet_edge_witnesses']:
        key = witness['retired_map'],witness['direction'],witness['offset']
        if key not in interfaces:
            old,direction,offset = key
            native_link = dict(map=inputs.maps[name]['id'],direction=direction,offset=offset)
            old_link = dict(map=inputs.maps[old]['id'],direction=OPPOSITE[direction],offset=-offset)
            if (native_link not in (inputs.maps[old].get('connections') or [])
                    or old_link not in (inputs.maps[name].get('connections') or [])):
                raise ValueError(('Native coast witness lacks reciprocal source connections',name,key))
            pairs = edge_pairs(inputs,dict(native_map=name,retired_map=old,direction=direction,offset=offset))
            interfaces[key] = {tuple(p['native_tile']):p for p in pairs}
        real = interfaces[key].get(tuple(witness['native_tile']))
        if real is None or any(real[field] != witness[field] for field in real):
            raise ValueError(('Native coast edge witness differs from source terrain',name,witness))


def _patch(layout,mouth,direction):
    xs,ys = zip(*mouth)
    left,top,right,bottom = max(0,min(xs)-1),max(0,min(ys)-1),min(layout['width'],max(xs)+2),min(layout['height'],max(ys)+2)
    if direction == 'left': right = min(layout['width'],8)
    elif direction == 'right': left = max(0,layout['width']-8)
    elif direction == 'up': bottom = min(layout['height'],8)
    else: top = max(0,layout['height']-8)
    return [left,top,right,bottom]


def _fit(inputs,row,native,mouth,glob,direction,water):
    dx,dy = CARDINAL[direction]; axis = 1 if dx else 0
    origin = glob[0]-native[0],glob[1]-native[1]
    first = min(p[axis] for p in mouth)+origin[axis]-1
    if direction == 'left': rect = (glob[0]-8,first,glob[0],first+len(mouth)+2)
    elif direction == 'right': rect = (glob[0]+1,first,glob[0]+9,first+len(mouth)+2)
    elif direction == 'up': rect = (first,glob[1]-8,first+len(mouth)+2,glob[1])
    else: rect = (first,glob[1]+1,first+len(mouth)+2,glob[1]+9)
    contacts = {(x+origin[0]+dx,y+origin[1]+dy) for x,y in mouth}
    if not contacts <= water:
        return None
    cells = {(x,y) for y in range(rect[1],rect[3]) for x in range(rect[0],rect[2]) if (x,y) in water}
    layout = inputs.layout(row['native_map'])
    near,far = (glob[0]+dx,glob[0]+8*dx) if dx else (glob[1]+dy,glob[1]+8*dy)
    for x,y in cells:
        if (x if dx else y) != near:
            continue
        target = x-origin[0]-dx,y-origin[1]-dy
        if (0 <= target[0] < layout['width'] and 0 <= target[1] < layout['height']
                and inputs.water(row['native_map'],*target) and target not in mouth):
            return None
    outer = {p for p in cells if p[0 if dx else 1] == far}
    if not outer or not any((x+dx,y+dy) in water and not (rect[0] <= x+dx < rect[2] and rect[1] <= y+dy < rect[3]) for x,y in outer):
        return None
    seen = set(contacts);todo = list(contacts)
    for x,y in todo:
        for ax,ay in CARDINAL.values():
            target = x+ax,y+ay
            if target in cells and target not in seen:
                seen.add(target);todo.append(target)
    return (rect,origin) if cells == seen else None


def _path(first,last,direction):
    turn = (first[0],last[1]) if direction in ('left','right') else (last[0],first[1])
    result = [tuple(first)]
    for target in (turn,tuple(last)):
        while result[-1] != target:
            x,y = result[-1]
            result.append((x+(target[0]>x)-(target[0]<x),y+(target[1]>y)-(target[1]<y)))
    return result


def _evidence(truth,row,native,mouth,target,direction,basis,fixed):
    path = _path(fixed,target,direction)
    dx,dy = CARDINAL[direction]
    samples = set(path)
    samples.update((target[0]+ax,target[1]+ay) for ax,ay in CARDINAL.values())
    samples.update((target[0]+dx*i,target[1]+dy*i) for i in range(1,3))
    samples = sorted((p for p in samples if 0 <= p[0] < truth.width and 0 <= p[1] < truth.height),key=lambda p:(p[1],p[0]))
    return dict(art_sha256=dict(truth.array_sha256),
                fixed_anchor=dict(map=row['native_map'],atlas=list(fixed)),
                geographic_basis='Authored local access: '+basis+'. The fixed anchor locates the region; sampled shore/route ink selects this interface, not a uniform native-map scale.',
                native_coast_basis=f'Native component {row["component"]}, SHA256 {row["component_sha256"]}; authenticated outward {direction} border, mouth {list(mouth)}, anchor {list(native)}. All cells retain native collision and elevation.',
                sole_basis='authored-coast-with-fixed-art-and-native-border',
                authored_anchor_to_coast_path=[list(p) for p in path],
                art_samples=[dict(atlas=list(p),palette_index=truth.pixel(p)) for p in samples],
                geography_authored_not_recovered=True,independent_geographic_review_pending=True)


def _overlap(a,b):
    return max(a[0],b[0]) < min(a[2],b[2]) and max(a[1],b[1]) < min(a[3],b[3])


def _compatible(candidate,selected):
    rect,origin,patch = candidate['rect'],candidate['origin'],candidate['registration']['local_rect']
    for other in selected:
        if _overlap(rect,other['rect']):
            return False
        if (candidate['registration']['native_map'] == other['registration']['native_map']
                and _overlap(patch,other['registration']['local_rect']) and origin != other['origin']):
            return False
    return True


def _components(pixels):
    labels,sizes = {},[]
    for point in sorted(pixels,key=lambda p:(p[1],p[0])):
        if point in labels:
            continue
        label = len(sizes); todo = [point];labels[point] = label
        for x,y in todo:
            for dx,dy in CARDINAL.values():
                target = x+dx,y+dy
                if target in pixels and target not in labels:
                    labels[target] = label;todo.append(target)
        sizes.append(len(todo))
    return labels,sizes


def propose_registrations(inputs,component_inventory,truth,plan=None,*,authored=AUTHORED_COASTS):
    """Return all concrete registrations or explicit per-component conflicts.

    ``plan`` may supply the integration caller's classified affine raster.
    The default diagnostic plan uses real blue ink except the authenticated
    Shipyard icon center. No pixels are added by this module. Reservations
    include evidence ready for plan_reserved_geometry, and native ecology
    ownership remains on each native map. Nothing is staged or written.
    """
    current = decode_atlas(inputs.read('src/data/journey_world_map.h').decode())
    if dict(current.array_sha256) != dict(truth.array_sha256) or current.indices != truth.indices:
        raise ValueError('Registration truth differs from immutable source atlas')
    diagnostic = plan is None
    if plan is None:
        plan = plan_geometry(truth.blue_pixels-{(96,40)})
    water = {(c['origin'][0]+x,c['origin'][1]+y) for c in plan['chunks'] for x,y in chunk_water(c)}
    pixels = {tuple(p) for p in plan['route_pixels']}
    labels,sizes = _components(pixels)
    anchors = inputs.anchors()
    rows = component_inventory['adapters']
    keys = [(row['native_map'],row['component']) for row in rows]
    if len(set(keys)) != len(keys):
        raise ValueError('Duplicate native water component inventory')
    candidates,conflicts,donors = {},[],{}
    for row in sorted(rows,key=lambda row:(row['native_map'],row['component'])):
        key = row['native_map'],row['component'];name = key[0]
        _,components = inputs.water_components(name)
        cells = sorted(components[row['component']],key=lambda p:(p[1],p[0]))
        digest = _sha(';'.join(f'{x},{y}' for x,y in cells).encode())
        if digest != row['component_sha256'] or len(cells) != row['water_cells']:
            raise ValueError(('Native water component changed',key))
        _authenticate_witnesses(inputs,row)
        try:
            donor,donor_evidence = _donor(inputs,row)
        except ValueError as error:
            conflicts.append(dict(native_map=name,component=key[1],reason='bank-donor-unavailable',detail=str(error)))
            continue
        donors[key] = donor_evidence
        available = []
        for choice,(direction,target,basis) in enumerate(authored.get(key,())):
            if target not in pixels or truth.pixel(target) != 2 or target == (96,40):
                continue
            mouths = _mouths(inputs,row,direction)
            for mouth_index,(native,mouth,_) in enumerate(mouths):
                preferred = 7 if direction in ('left','up') else 0
                phases = sorted(((x,y) for y in range(8) for x in range(8)),key=lambda p:(abs(p[1 if direction in ('left','right') else 0]-4),abs(p[0 if direction in ('left','right') else 1]-preferred),p))
                for phase in phases:
                    glob = target[0]*8+phase[0],target[1]*8+phase[1]
                    fit = _fit(inputs,row,native,mouth,glob,direction,water)
                    if fit is None:
                        continue
                    rect,origin = fit
                    registration = dict(native_map=name,component=key[1],native_tile=list(native),
                        global_tile=list(glob),direction=direction,local_rect=_patch(inputs.layout(name),mouth,direction),
                        mouth_width=len(mouth),depth=8,donor=deepcopy(donor),
                        atlas_evidence=_evidence(truth,row,native,mouth,target,direction,basis,anchors[name]['atlas']))
                    available.append(dict(registration=registration,rect=rect,origin=origin,
                        choice=choice,mouth_index=mouth_index,phase=list(phase),
                        atlas_component=labels[target],atlas_component_pixels=sizes[labels[target]]))
        # Preserve alternatives that move along the native mouth as well as
        # phase alternatives; global collision resolution uses only these
        # explicit shoreline choices, never an arbitrary neighboring ocean.
        unique = {}
        for candidate in available:
            r = candidate['registration']
            identity = (tuple(candidate['rect']),tuple(candidate['origin']),tuple(r['local_rect']))
            unique.setdefault(identity,candidate)
        candidates[key] = list(unique.values())
        if not available:
            conflicts.append(dict(native_map=name,component=key[1],reason='no-eight-tile-returning-fit',
                attempted_choices=[dict(direction=d,atlas=list(p),geographic_basis=b) for d,p,b in authored.get(key,())],
                native_directions=sorted({OPPOSITE[w['direction']] for w in row['source_wet_edge_witnesses']}),
                alternatives='Review the explicit shoreline targets or source mouth; no raster water was added.'))
    selected = []
    unresolved = []
    # Most constrained first. Backtracking handles the few narrow native
    # mouths without silently shifting another city's geographic target.
    ordered = sorted((key for key,values in candidates.items() if values),key=lambda key:(len(candidates[key]),key))
    def assign(index):
        if index == len(ordered):
            return True
        for candidate in candidates[ordered[index]]:
            if _compatible(candidate,selected):
                selected.append(candidate)
                if assign(index+1): return True
                selected.pop()
        return False
    if not assign(0):
        for key in ordered:
            choice = next((c for c in candidates[key] if _compatible(c,selected)),None)
            if choice is None: unresolved.append(key)
            else: selected.append(choice)
        conflicts.extend(dict(native_map=name,component=component,reason='reservation-or-native-patch-overlap',
                              candidate_count=len(candidates[name,component])) for name,component in unresolved)
    registrations = sorted((c['registration'] for c in selected),key=lambda row:(row['native_map'],row['component']))
    adapter_plan = plan_adapters(inputs,component_inventory,plan,registrations,truth,require_complete=not conflicts)
    binding_by_name = {binding['adapter']:binding for binding in adapter_plan['bindings']}
    for reservation in adapter_plan['reservations']:
        binding = binding_by_name[reservation['name']]
        reservation['evidence'] = dict(kind='authored-local-native-coast',native_map=binding['native_map'],
            native_component=binding['component'],atlas_evidence=deepcopy(binding['atlas_evidence']),
            donor_evidence=donors[binding['native_map'],binding['component']])
    inputs.assert_unchanged()
    return dict(kind='atlas-concrete-coast-registration-proposals/v1',
        geography_authored_not_recovered=True,registrations=registrations,adapter_plan=adapter_plan,
        conflicts=conflicts,all_inventory_components_registered=not conflicts and len(registrations)==len(rows),
        component_inventory_count=len(rows),registered_component_count=len(registrations),
        diagnostic_all_blue_ink_plan=diagnostic,old_player_gps_used=False,
        generated_water_added=False,native_terrain_events_heights_changed=False,
        art_sha256=dict(truth.array_sha256),
        fitting_summary=[dict(native_map=c['registration']['native_map'],component=c['registration']['component'],
            direction=c['registration']['direction'],atlas=[v//8 for v in c['registration']['global_tile']],
            phase=c['phase'],native_tile=c['registration']['native_tile'],mouth_width=c['registration']['mouth_width'],
            rectangle=list(c['rect']),atlas_ink_component=c['atlas_component'],
            atlas_ink_component_pixels=c['atlas_component_pixels'],
            candidate_count=len(candidates[c['registration']['native_map'],c['registration']['component']]))
            for c in sorted(selected,key=lambda c:(c['registration']['native_map'],c['registration']['component']))],
        pending=['Independent review of authored geography and complete native donor graphics.',
                 'Merge with scenery/Dive/port reservations; reject footprint conflicts.',
                 'Global SCC including small real ink stubs and native land/Surf transitions.',
                 'Native ROM return travel, collision, heights, camera, animation and Save/Continue.'],
        input_sha256=dict(inputs.inputs),
        input_manifest_sha256=_sha(json.dumps(inputs.inputs,sort_keys=True,separators=(',',':')).encode()),
        source_written=False,native_rom_validated=False)


def diagnose_legacy_gps(inputs,proposal):
    """Measure old native/ocean GPS versus the already chosen new interface.

    This is deliberately separate from proposal generation. It cannot select
    or move a mouth. Source171's per-cell projections may have reconciled
    native coasts to its folded oceans; their cyan jump remains integration
    work, even when the new physical connection and atlas ink agree.
    """
    path = 'src/data/journey_world_position.h'
    raw = inputs.read(path)
    text = raw.decode()
    match = re.search(r'sWorldNavigationPixels\s*\[\s*\]\s*=\s*\{([^}]+)\}',text)
    body = re.search(r'sWorldTileGrids\s*\[\s*\]\s*=\s*\{(.*?)\};',text,re.S)
    if match is None or body is None:
        raise ValueError('Legacy GPS diagnostic needs the actual navigation arrays')
    pixels = [int(token.strip(),0) for token in match[1].split(',') if token.strip()]
    grids = {}
    for first,constant,width,height in re.findall(
            r'\{(\d+),\s*\(MAP_GROUP\((MAP_\w+)\)<<8\)\|MAP_NUM\(\2\),\s*(\d+),\s*(\d+)\}',body[1]):
        grids[constant] = int(first),int(width),int(height)
    anchors = inputs.anchors()
    def original(name,point):
        constant = inputs.maps[name]['id']
        if constant not in grids:
            return list(anchors[name]['atlas']), 'fixed-map-anchor-fallback'
        first,width,height = grids[constant]
        x,y = max(0,min(point[0],width-1)),max(0,min(point[1],height-1))
        packed = pixels[first+y*width+x]
        return [packed&255,packed>>8],'native-per-cell-navigation-grid'
    records = []
    for binding in proposal['adapter_plan']['bindings']:
        name,direction = binding['native_map'],binding['direction']
        dx,dy = CARDINAL[direction]
        native,glob = binding['native_tile'],binding['global_tile']
        origin = glob[0]-native[0],glob[1]-native[1]
        cells = []
        for witness in binding['source_wet_mouth']:
            point = witness['native_tile']
            old,mode = original(name,point)
            old_ocean,_ = original(witness['retired_map'],witness['retired_tile'])
            generated = [(point[0]+origin[0]+dx)//8,(point[1]+origin[1]+dy)//8]
            delta = [generated[i]-old[i] for i in range(2)]
            cells.append(dict(native_tile=point,legacy_native_atlas=old,legacy_native_mode=mode,
                legacy_ocean_map=witness['retired_map'],legacy_ocean_tile=witness['retired_tile'],
                legacy_ocean_atlas=old_ocean,new_adjacent_affine_atlas=generated,
                new_minus_legacy_native=delta,cyan_jump_manhattan_pixels=sum(abs(v) for v in delta),
                historical_seam_manhattan_pixels=sum(abs(old_ocean[i]-old[i]) for i in range(2))))
        records.append(dict(native_map=name,component=binding['component'],direction=direction,
            maximum_cyan_jump_manhattan_pixels=max(c['cyan_jump_manhattan_pixels'] for c in cells),
            cells=cells))
    inputs.assert_unchanged()
    return dict(kind='secondary-legacy-gps-interface-diagnostic/v1',used_to_select_or_move_mouths=False,
        navigation_header_sha256=_sha(raw),records=records,
        interfaces_with_cyan_delta=sum(r['maximum_cyan_jump_manhattan_pixels']>0 for r in records),
        maximum_cyan_jump_manhattan_pixels=max((r['maximum_cyan_jump_manhattan_pixels'] for r in records),default=0),
        native_gps_integration_pending=True,
        explanation='Old per-cell native GPS was reconciled to folded source171 oceans. These measured deltas are unresolved integration diagnostics, not evidence for changing the authored physical coast or for publishing a ROM.',
        native_rom_validated=False)


def render_review(truth,proposal,directory):
    """Export actual source art and a clearly annotated design overlay."""
    from PIL import Image,ImageDraw
    directory = Path(directory)
    directory.mkdir(parents=True,exist_ok=True)
    colors = [((c&31)*255//31,((c>>5)&31)*255//31,((c>>10)&31)*255//31) for c in truth.palette]
    original = Image.new('RGB',(truth.width,truth.height))
    original.putdata([colors[index] for index in truth.indices])
    scale = 6
    original = original.resize((truth.width*scale,truth.height*scale),Image.Resampling.NEAREST)
    source_path = directory/'atlas-source.png'; original.save(source_path)
    canvas = Image.new('RGB',(original.width+580,max(original.height,840)),(246,246,240))
    canvas.paste(original,(0,0));draw = ImageDraw.Draw(canvas)
    draw.text((original.width+12,12),'AUTHORED COAST PROPOSALS / SOURCE ART',fill=(0,0,0))
    draw.text((original.width+12,28),'Design overlay; no ROM or global SCC certificate.',fill=(0,0,0))
    for index,registration in enumerate(proposal['registrations'],1):
        evidence = registration['atlas_evidence']
        points = [(p[0]*scale+scale//2,p[1]*scale+scale//2) for p in evidence['authored_anchor_to_coast_path']]
        if len(points)>1: draw.line(points,fill=(255,242,0),width=1)
        x,y = (value//8 for value in registration['global_tile'])
        cx,cy = x*scale+scale//2,y*scale+scale//2
        dx,dy = CARDINAL[registration['direction']]
        draw.ellipse((cx-3,cy-3,cx+3,cy+3),outline=(255,0,255),width=2)
        draw.line((cx,cy,cx+dx*10,cy+dy*10),fill=(255,0,255),width=2)
        draw.text((cx+4,cy-8),str(index),fill=(0,0,0))
        draw.text((original.width+12,52+index*22),
                  f'{index:02} {registration["native_map"]} / c{registration["component"]}',fill=(0,0,0))
        draw.text((original.width+22,62+index*22),
                  f'{registration["direction"]} ({x},{y}), native {registration["native_tile"]}, mouth {registration["mouth_width"]}',fill=(40,40,40))
    annotated_path = directory/'coast-registrations.png'; canvas.save(annotated_path)
    return {path.name:dict(path=str(path),sha256=_sha(path.read_bytes())) for path in (source_path,annotated_path)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--inventory',type=Path,default=Path('docs/design/atlas-surf-layout/parent-inventory.json'))
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--review-directory',type=Path)
    args = parser.parse_args()
    inputs = Source(args.source)
    truth = decode_atlas(inputs.read('src/data/journey_world_map.h').decode())
    inventory = json.loads(args.inventory.read_bytes())
    report = propose_registrations(inputs,inventory['adapters'],truth)
    report['legacy_gps_diagnostic'] = diagnose_legacy_gps(inputs,report)
    if args.review_directory:
        report['source_art_review'] = render_review(truth,report,args.review_directory)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(registered=report['registered_component_count'],
                         inventory=report['component_inventory_count'],conflicts=report['conflicts'],
                         output=str(args.output)),indent=2))
