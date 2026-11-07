"""Remove four native reef fragments left beneath integrated Sevii terminals.

The Surf boarding cell and the ships cut only part of larger native objects.
Keep the existing One boarding opening, the Four coast passages and every
terminal/ship cell. One retains its blocked cells; Five's two decorative
water cells become complete blocked pebbles only after proving that all
remaining water components and all seam cells retain their connectivity.
"""
import copy
import json
import re
import struct
from collections import deque
from pathlib import Path

from sevii_route_boundaries import Terrain


BEACH = 'OneIsland_TreasureBeach_Frlg'
FOUR = 'FourIsland_Frlg'
FIVE = 'FiveIsland_Frlg'
SEVEN_FRONT = 'SevenIsland_SevaultCanyon_Entrance_Frlg'
SMALL = 0x243
PURE_WATER_WORDS = (0x41C6, 0x41C7, 0x41C7, 0x41C6, 0, 0, 0, 0)
SEVEN_LIMIT = tuple((23, y) for y in range(2, 9))
SIX = 'SixIsland_Frlg'
SIX_BOARDING = (2, 29)
VISIBLE_LIMITS = {
    'ThreeIsland_Port_Frlg': ((44, 0),),
    FOUR: tuple((x, 39) for x in range(3, 8))+((33, 39),),
    SIX: ((0, 2),),
    SEVEN_FRONT: SEVEN_LIMIT+tuple((0,y) for y in (*range(1,8),*range(10,19),*range(21,37)))
                 +tuple((x,39) for x in range(6)),
}
FAMILIES = {
    'standard': (0x110, 0x111, 0x118, 0x119),
    'round': (0x1CB, 0x1CC, 0x1D3, 0x1D4),
    'angled': (0x212, 0x213, 0x21A, 0x21B),
    'secondary': (0x244, 0x245, 0x24C, 0x24D),
    'cliff_merged': (0x25E, 0x25F, 0x24C, 0x24D),
}
PORT_MAPS = ('OneIsland_Frlg', BEACH, 'TwoIsland_Frlg',
             'ThreeIsland_Port_Frlg', FOUR, FIVE, 'SixIsland_Frlg',
             'SevenIsland_Frlg', 'SevenIsland_SevaultCanyon_Entrance_Frlg')
# The acquired One Island has this whole low/submerged reef variant. Its
# right-hand pair is shared with the standard boulder; the left-hand pair is
# intentionally different. It is not a clipped standard object.
NATIVE_COMPLETE_VARIANTS = {
    ('OneIsland_Frlg', (22, 1)): (0x112, 0x111, 0x11A, 0x119),
}
# Expected IDs cover the entire original object, including water or roof
# replacing a former quarter. Only the listed remaining quarters are changed.
REPAIRS = (
    dict(map=BEACH, anchor=[19, 7], family='round',
         expected=(0x1CB, 0x12B, 0x1D3, 0x1D4), quarters=(0, 2, 3),
         target=SMALL, block=True, cause='boarding-water-overwrote-upper-right'),
    dict(map=FOUR, anchor=[1, 27], family='secondary',
         expected=(0x244, 0x245, 0x24C, 0x31A), quarters=(0, 1, 2),
         target=0x273, block=False, cause='terminal-roof-overwrote-lower-right'),
    dict(map=FOUR, anchor=[7, 35], family='secondary',
         expected=(0x273, 0x245, 0x273, 0x273), quarters=(1,),
         target=0x273, block=False, cause='ship-water-left-one-upper-right-quarter'),
    dict(map=FIVE, anchor=[5, 14], family='round',
         expected=(0x1CB, 0x1CC, 0x12B, 0x12B), quarters=(0, 1),
         target=SMALL, block=True, cause='ship-clearance-overwrote-lower-row'),
)


def _cell(terrain, name, x, y):
    """Read a real adjacent owner before calling an edge-spanning reef cut."""
    layout = terrain.layout(name)
    width, height = layout['width'], layout['height']
    if not (0 <= x < width and 0 <= y < height):
        directions = ([('left', x < 0), ('right', x >= width),
                       ('up', y < 0), ('down', y >= height)])
        matches = [direction for direction, outside in directions if outside]
        if len(matches) != 1:
            return None
        target = terrain.neighbor(name, x, y, matches[0])
        if target is None:
            return None
        name, x, y = target
        layout = terrain.layout(name)
    return dict(map=name, cell=[x, y], block=terrain.grid(name)[y*layout['width']+x])


def census(terrain, names=PORT_MAPS):
    """Inventory all five families; a heuristic candidate is not a repair."""
    rows = []
    for name in names:
        layout = terrain.layout(name)
        assert layout['layout_version'] == 'frlg'
        assert layout['primary_tileset'] == 'gTileset_JourneySeviiSea'
        width = layout['width']
        candidates = {}
        for family, expected in FAMILIES.items():
            anchors = {(i % width-expected.index(word & 1023) % 2,
                        i // width-expected.index(word & 1023) // 2)
                       for i, word in enumerate(terrain.grid(name)) if word & 1023 in expected}
            for x, y in sorted(anchors):
                cells = [_cell(terrain, name, x+q % 2, y+q // 2) for q in range(4)]
                actual = [None if cell is None else cell['block'] & 1023 for cell in cells]
                matches = sum(a == b for a, b in zip(actual, expected))
                variant = NATIVE_COMPLETE_VARIANTS.get((name, (x, y)))
                native_variant = variant is not None and tuple(actual) == variant
                row = dict(map=name, anchor=[x, y], family=family,
                           expected_metatiles=list(expected), actual_metatiles=actual,
                           matched_quarters=matches, complete=matches == 4 or native_variant,
                           native_complete_variant=list(variant) if native_variant else None,
                           all_cells_resolved=all(cell is not None for cell in cells),
                           connected_map_parts=any(cell and cell['map'] != name for cell in cells),
                           cells=cells)
                # Secondary and cliff-merged objects share their bottom pair.
                # Prefer the full native composition actually present above it.
                old = candidates.get((x, y))
                if old is None or matches > old['matched_quarters']:
                    candidates[x, y] = row
        rows.extend(candidates[key] for key in sorted(candidates))
    return dict(kind='all-sevii-port-reef-families', maps=list(names),
                families={key:list(value) for key, value in FAMILIES.items()},
                objects=rows, incomplete=[row for row in rows if not row['complete']],
                source_inspection_not_native_proof=True)


def current_ports(source):
    """Translate historical integrated-port metadata to the current beach."""
    source = Path(source)
    ports = copy.deepcopy(json.loads((source/'.journey-sevii-integrated-piers').read_bytes())['harbors']['ports'])
    approach = json.loads((source/'.journey-sevii-route-boundaries').read_bytes())['boundaries']['approach']
    assert approach['map'] == BEACH and approach['original_terrain_offset'] == [8, 0]
    for port in ports:
        for key in ('dry', 'water'):
            if port['boarding'][key][0] == BEACH:
                port['boarding'][key][1] += 8
    return ports


def boarding_census(source, terrain=None):
    terrain = terrain or Terrain(source)
    all_objects = census(terrain)
    rows = []
    for port in current_ports(source):
        name, x, y = port['boarding']['water']
        nearby = [row for row in all_objects['objects'] if row['map'] == name
                  and any(cell and abs(cell['cell'][0]-x) <= 4 and abs(cell['cell'][1]-y) <= 4
                          for cell in row['cells'])]
        rows.append(dict(island=port['island'], boarding=port['boarding'],
                         water_cell=_cell(terrain, name, x, y), nearby_objects=nearby))
    return dict(ports=rows, all_port_maps=all_objects)


def protected_port_cells(source, terrain):
    """Protect real boarding and complete source-sized boat sprite bounds."""
    boarding={(port['boarding']['water'][0],tuple(port['boarding']['water'][1:]))
              for port in current_ports(source)}
    declarations=(Path(source)/'src/data/object_events/object_event_graphics_info.h').read_text()
    graphics={'OBJ_EVENT_GFX_SEAGALLOP':'Seagallop',
              'OBJ_EVENT_GFX_JOURNEYSEVIIBOAT':'JourneySeviiBoat'}
    sizes={}
    for identifier,symbol in graphics.items():
        body=re.search(r'const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_'+symbol+r' = \{(.*?)\};',
                       declarations,re.S)[1]
        sizes[identifier]=tuple(int(re.search(r'\.'+key+r'\s*=\s*(\d+)',body)[1]) for key in ('width','height'))
    assert sizes=={'OBJ_EVENT_GFX_SEAGALLOP':(64,64),'OBJ_EVENT_GFX_JOURNEYSEVIIBOAT':(32,32)}
    cells,boats=set(),[]
    for name in PORT_MAPS:
        for event in terrain.maps[name].get('object_events',[]):
            if event.get('graphics_id') not in sizes:continue
            width,height=sizes[event['graphics_id']]
            # Native object placement adds (8,16-height/2), then OAM uses
            # centerToCorner=(-width/2,-height/2). Include every overlapped tile.
            left=event['x']*16+8-width//2;top=event['y']*16+16-height
            footprint=[(x,y) for y in range(top//16,(top+height-1)//16+1)
                       for x in range(left//16,(left+width-1)//16+1)]
            cells.update((name,cell) for cell in footprint)
            boats.append(dict(map=name,event_cell=[event['x'],event['y']],
                graphics_id=event['graphics_id'],source_sprite_size=[width,height],
                pixel_bounds=[left,top,width,height],all_intersected_cells=[list(c) for c in footprint]))
    return dict(boarding=boarding,boats=cells,report=dict(
        boarding_water=[dict(map=n,cell=list(c)) for n,c in sorted(boarding)],boat_footprints=boats))


def outer_limit_census(terrain, names=PORT_MAPS, protected=None):
    rows = []
    for name in names:
        layout, words = terrain.layout(name), terrain.grid(name)
        width = layout['width']
        openings = {(x, y) for x, y, direction, xx, yy in terrain.perimeter(name)
                    if terrain.neighbor(name, xx, yy, direction) is not None}
        unsealed,pure,eligible = {},{},{}
        definitions=terrain.renderer.tileset(layout['primary_tileset'])[2]
        for x, y, direction, xx, yy in terrain.perimeter(name):
            word = words[y*width+x]
            if (x, y) not in openings and not word & 0xC00 and terrain.water(name, word):
                if protected is None or (name,(x,y)) not in protected['boarding']:
                    unsealed[x, y] = dict(cell=[x, y], direction=direction, block=word)
            mid=word&1023
            if ((x,y) not in openings and mid<640
                    and tuple(definitions[mid*8:(mid+1)*8])==PURE_WATER_WORDS):
                reason=('boarding-water' if protected and (name,(x,y)) in protected['boarding'] else
                        'complete-boat-sprite' if protected and (name,(x,y)) in protected['boats'] else None)
                row=dict(cell=[x,y],direction=direction,block=word,collision=(word>>10)&3,
                         definition_words=list(PURE_WATER_WORDS),protected_reason=reason)
                pure[x,y]=row
                if reason is None:eligible[x,y]=row
        rows.append(dict(map=name, unsealed_water_limits=[unsealed[key] for key in sorted(unsealed)],
                         pure_water_outer_limits=[pure[key] for key in sorted(pure)],
                         eligible_visible_reef_limits=[eligible[key] for key in sorted(eligible)],
                         actual_connection_span_cells=[list(cell) for cell in sorted(openings)]))
    return dict(maps=rows, unsealed_water_cells=sum(len(row['unsealed_water_limits']) for row in rows),
                invisible_pure_water_limits=sum(len(row['eligible_visible_reef_limits']) for row in rows))


def water_components(terrain, name, words):
    width = terrain.layout(name)['width']
    remaining = {i for i, word in enumerate(words) if not word & 0xC00 and terrain.water(name, word)}
    components = []
    while remaining:
        start = remaining.pop()
        queue, seen = deque([start]), {start}
        while queue:
            index = queue.popleft()
            x, y = index % width, index // width
            for nx, ny in ((x-1, y), (x+1, y), (x, y-1), (x, y+1)):
                target = ny*width+nx
                if 0 <= nx < width and 0 <= target < len(words) and target in remaining:
                    remaining.remove(target)
                    seen.add(target)
                    queue.append(target)
        components.append(frozenset(seen))
    return components


def check_water_connectivity(terrain, name, before, after, touched, permitted_outer_limits=(), permitted_water_openings=()):
    removed = {i for i in touched if not before[i] & 0xC00 and after[i] & 0xC00}
    old = {component-removed for component in water_components(terrain, name, before)}-{frozenset()}
    new = set(water_components(terrain, name, after))
    added={i for i in touched if before[i]&0xC00 and not after[i]&0xC00}
    assert added==set(permitted_water_openings)
    if added:
        assert set().union(*new)==set().union(*old)|added
        assert all(any(component<=target for target in new) for component in old), ('Scenery splits old Surf route',name)
    else:
        assert old == new, ('Scenery closes an existing Surf route', name)
    width, height = (terrain.layout(name)[key] for key in ('width', 'height'))
    edges = {y*width+x for y in range(height) for x in range(width)
             if x in (0, width-1) or y in (0, height-1)}
    allowed = {y*width+x for x, y in permitted_outer_limits}
    assert all(before[index] == after[index] for index in edges-allowed)
    for x, y, direction, xx, yy in terrain.perimeter(name):
        if terrain.neighbor(name, xx, yy, direction) is not None:
            assert before[y*width+x] == after[y*width+x], ('Actual seam opening changed', name, x, y)
    return dict(before_component_sizes=sorted(map(len, water_components(terrain, name, before))),
                after_component_sizes=sorted(map(len, new)), newly_blocked_cells=[
                    [i % width, i // width] for i in sorted(removed)],
                every_remaining_local_water_component_preserved=True,
                all_map_edge_cells_unchanged=not bool(touched & edges),
                all_actual_seam_openings_unchanged=True,
                intentionally_restored_water_cells=[[i%width,i//width] for i in sorted(added)],
                global_connectivity_preserved_by_local_components_and_unchanged_seams=True)


def repair(layer):
    terrain = Terrain(layer.source, layer)
    protected=protected_port_cells(layer.source,terrain)
    before_census = census(terrain)
    before_limits = outer_limit_census(terrain,protected=protected)
    expected_cuts = {(case['map'], tuple(case['anchor'])) for case in REPAIRS}
    assert {(row['map'], tuple(row['anchor'])) for row in before_census['incomplete']} == expected_cuts
    assert {(row['map'], tuple(cell['cell'])) for row in before_limits['maps']
            for cell in row['unsealed_water_limits']} == {(SEVEN_FRONT, cell) for cell in SEVEN_LIMIT}
    assert {(row['map'],tuple(cell['cell'])) for row in before_limits['maps']
            for cell in row['eligible_visible_reef_limits']}=={
                (name,cell) for name,cells in VISIBLE_LIMITS.items() for cell in cells}, 'Unexpected limit or non-water upper artwork'
    staged, reports, by_map = [], [], {}
    # Validate every whole footprint before staging any map.
    for case in REPAIRS:
        name = case['map']
        layout = terrain.layout(name)
        width = layout['width']
        if name not in by_map:
            original = terrain.grid(name).copy()
            by_map[name] = (original, original.copy(), set())
        before, after, touched = by_map[name]
        x, y = case['anchor']
        indices = [(y+q // 2)*width+x+q % 2 for q in range(4)]
        observed = tuple(before[index] & 1023 for index in indices)
        assert observed == case['expected'], ('Unreviewed port reef footprint', name, x, y, observed)
        events = {(event['x'], event['y']) for key in ('object_events', 'warp_events', 'coord_events', 'bg_events')
                  for event in terrain.maps[name].get(key, [])}
        changes = []
        for quarter in case['quarters']:
            index = indices[quarter]
            xx, yy = index % width, index // width
            assert (xx, yy) not in events, ('Scenery intersects an event', name, xx, yy)
            old = before[index]
            new = (old & ~1023) | case['target']
            if case['block']:
                new = (new & ~0xC00) | 0x400
            assert old >> 12 == new >> 12
            after[index] = new
            touched.add(index)
            changes.append(dict(cell=[xx, yy], before=old, after=new,
                                elevation_preserved=True,
                                collision_changed=(old & 0xC00) != (new & 0xC00),
                                blocked_pebble=case['block']))
        reports.append(dict(map=name, anchor=case['anchor'], dimensions=[2, 2],
                            family=case['family'], cause=case['cause'],
                            whole_footprint_before=[before[index] for index in indices],
                            whole_footprint_after=[after[index] for index in indices],
                            changed_cells=changes, roof_boat_and_boarding_cells_preserved=True))
    # This terminal also occupies the canyon's northern coast. The old limit
    # selector skipped that route header, leaving seven actual outer cells
    # open. Assert all eight words: 0x273 in another bank can include cliff art.
    layout = terrain.layout(SEVEN_FRONT)
    assert (layout['width'], layout['height']) == (24, 40)
    primary = terrain.renderer.tileset(layout['primary_tileset'])[2]
    water_words = tuple(primary[0x273*8:0x274*8])
    small_words = tuple(primary[SMALL*8:(SMALL+1)*8])
    assert water_words == PURE_WATER_WORDS, 'Seven port limit contains non-water upper artwork'
    assert small_words[:4] == PURE_WATER_WORDS[:4] and small_words[4:] == (0x41E2, 0x41E3, 0x41E4, 0x41E5)
    boundary_changes = []
    for name,cells in VISIBLE_LIMITS.items():
        if name not in by_map:
            old=terrain.grid(name).copy();by_map[name]=(old,old.copy(),set())
        before,after,touched=by_map[name];width=terrain.layout(name)['width']
        definitions=terrain.renderer.tileset(terrain.layout(name)['primary_tileset'])[2]
        for x,y in cells:
            index=y*width+x;mid=before[index]&1023
            assert (name,(x,y)) not in protected['boarding']|protected['boats']
            assert tuple(definitions[mid*8:(mid+1)*8])==PURE_WATER_WORDS
            after[index]=(before[index]&~1023)|SMALL
            if (name,(x,y)) in {(SEVEN_FRONT,c) for c in SEVEN_LIMIT}:
                assert before[index]==0x1273
                after[index]=(after[index]&~0xC00)|0x400
            else:assert before[index]&0xC00==0x400
            touched.add(index)
            boundary_changes.append(dict(map=name,cell=[x,y],before=before[index],after=after[index],
                water_definition_words=list(PURE_WATER_WORDS),source_sprite_and_boarding_guards_clear=True))
    before,after,touched=by_map[SIX]
    index=SIX_BOARDING[1]*terrain.layout(SIX)['width']+SIX_BOARDING[0]
    assert before[index]==0x1673 and (SIX,SIX_BOARDING) in protected['boarding']
    after[index]=0x1273;touched.add(index)
    boarding_fix=dict(map=SIX,cell=list(SIX_BOARDING),before=before[index],after=after[index],
                      original_boarding_restored=True,artwork_and_elevation_unchanged=True)
    connectivity = []
    for name, (before, after, touched) in sorted(by_map.items()):
        allowed=VISIBLE_LIMITS.get(name,())+((SIX_BOARDING,) if name==SIX else ())
        opened={SIX_BOARDING[1]*terrain.layout(SIX)['width']+SIX_BOARDING[0]} if name==SIX else set()
        connectivity.append(dict(map=name, **check_water_connectivity(terrain, name, before, after, touched, allowed,opened)))
        assert all(a == b for i, (a, b) in enumerate(zip(before, after)) if i not in touched)
        path = terrain.layout(name)['blockdata_filepath']
        blob = struct.pack('<'+'H'*len(after), *after)
        staged.append((path, blob))
        terrain.blocks[path] = after
    after_census = census(terrain)
    assert not after_census['incomplete'], after_census['incomplete']
    after_limits = outer_limit_census(terrain,protected=protected)
    assert after_limits['unsealed_water_cells'] == 0
    assert after_limits['invisible_pure_water_limits']==0
    donor = terrain.grid('OneIsland_KindleRoad_Frlg')[19*24+23]
    assert donor & 1023 == SMALL and donor & 0xC00
    assert terrain.grid(FOUR)[36*48+8] == 0x1273
    for path, blob in staged:
        layer.stage(path, blob)
    return dict(kind='complete-integrated-port-reef-scenery', objects=reports,
                changed_art_cells=sum(len(row['changed_cells']) for row in reports),
                newly_blocked_cells=sum(cell['collision_changed'] for row in reports for cell in row['changed_cells']),
                water_connectivity=connectivity,
                census_before=before_census, census_after=after_census,
                outer_limit_census_before=before_limits, outer_limit_census_after=after_limits,
                visible_actual_outer_limits=dict(changed_cells=boundary_changes,
                    changed_art_cells=len(boundary_changes),newly_blocked_cells=7,
                    existing_invisible_barriers_made_visible=46,
                    all_elevations_preserved=True,all_other_collisions_preserved=True),
                six_boarding_water=boarding_fix,protected_port_cells=protected['report'],
                seven_actual_outer_limits=dict(map=SEVEN_FRONT, changed_cells=[c for c in boundary_changes if c['map']==SEVEN_FRONT and tuple(c['cell']) in SEVEN_LIMIT],
                    water_metatile=0x273, water_definition_words=list(water_words),
                    pebble_metatile=SMALL, pebble_definition_words=list(small_words),
                    primary_tileset=layout['primary_tileset'], pure_water_upper_words_empty=True,
                    actual_right_connection_offset=20, existing_right_connection_span_unchanged=True,
                    native_complete_single_cell_reef=True),
                native_small_reef_donor=dict(map='OneIsland_KindleRoad_Frlg', cell=[23, 19],
                    block=donor, primary_tileset='gTileset_JourneySeviiSea'),
                native_four_water_donor=dict(map=FOUR, cell=[8, 36], block=0x1273),
                source_paths=[path for path, blob in staged],
                all_other_cells_events_connections_dimensions_and_graphics_unchanged=True,
                source_inspection_not_native_movement_proof=True)
