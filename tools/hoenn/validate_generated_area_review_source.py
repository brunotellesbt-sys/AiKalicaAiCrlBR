"""Independently replay layer 171 and bind reviewed geometry to the final ROM."""
import argparse
import copy
import struct
from collections import deque
import hashlib
import json
from pathlib import Path
import re

import generated_area_review_contract as contract
from validate_sevii_route_boundaries_source import Inputs, digest, safe_relative, gps, symbols
from validate_coast_scenery_review_source import compiled_bindings, check_boulders

CAMERA_PATH = 'src/fieldmap.c'
RUNTIME_SYMBOLS = ('MapGridGetMetatileIdAt', 'NewGameInitData',
                   'CopyPartyAndObjectsFromSave', 'TrySpawnObjectEvents')
CARDINAL = {'up', 'down', 'left', 'right'}
BEACH, SEA, PASSAGE = 'OneIsland_TreasureBeach_Frlg', 'JourneyKantoSeviiTransit', 'JourneyOneSouthPassage'
PORT_MAPS = {'OneIsland_Frlg', BEACH, 'TwoIsland_Frlg', 'ThreeIsland_Port_Frlg',
             'FourIsland_Frlg', 'FiveIsland_Frlg', 'SixIsland_Frlg', 'SevenIsland_Frlg',
             'SevenIsland_SevaultCanyon_Entrance_Frlg'}
MOUTHS = {(BEACH,x,47) for x in range(1,7)} | {(SEA,x,y) for x in range(63,69) for y in (0,1)}
CLIFF = {(BEACH,7,37):(0x051F,0x0517),(BEACH,6,38):(0x112C,0x1128),
         (BEACH,32,37):(0x0517,0x051F),(BEACH,33,38):(0x112A,0x1129)}
CLIFF_DONORS = (('SevenIsland_TrainerTower_Frlg',39,36,0x0517),
    ('SevenIsland_TrainerTower_Frlg',39,37,0x0473),
    ('SevenIsland_TrainerTower_Frlg',38,37,0x0128),
    ('SevenIsland_TrainerTower_Frlg',38,38,0x012C),
    ('OneIsland_KindleRoad_Frlg',6,135,0x051F),
    ('OneIsland_KindleRoad_Frlg',6,136,0x0475),
    ('OneIsland_KindleRoad_Frlg',7,136,0x1129),
    ('OneIsland_KindleRoad_Frlg',7,137,0x112A))
BOAT_SIZES = {'OBJ_EVENT_GFX_SEAGALLOP':(64,64),
              'OBJ_EVENT_GFX_JOURNEYSEVIIBOAT':(32,32)}
BOARDING_POINTS = {'One':(BEACH,(20,6),(20,7)), 'Two':('TwoIsland_Frlg',(10,14),(10,15)),
    'Three':('ThreeIsland_Port_Frlg',(13,17),(14,17)), 'Four':('FourIsland_Frlg',(10,34),(10,35)),
    'Five':('FiveIsland_Frlg',(11,15),(10,15)), 'Six':('SixIsland_Frlg',(3,29),(2,29)),
    'Seven':('SevenIsland_SevaultCanyon_Entrance_Frlg',(14,1),(13,1))}
BOAT_EVENTS = {(BEACH,17,10,'OBJ_EVENT_GFX_JOURNEYSEVIIBOAT'),(BEACH,27,10,'OBJ_EVENT_GFX_SEAGALLOP'),
    ('TwoIsland_Frlg',13,18,'OBJ_EVENT_GFX_JOURNEYSEVIIBOAT'),('TwoIsland_Frlg',5,18,'OBJ_EVENT_GFX_SEAGALLOP'),
    ('ThreeIsland_Port_Frlg',16,17,'OBJ_EVENT_GFX_JOURNEYSEVIIBOAT'),('ThreeIsland_Port_Frlg',22,17,'OBJ_EVENT_GFX_SEAGALLOP'),
    ('FourIsland_Frlg',13,37,'OBJ_EVENT_GFX_JOURNEYSEVIIBOAT'),('FourIsland_Frlg',5,38,'OBJ_EVENT_GFX_SEAGALLOP'),
    ('FiveIsland_Frlg',8,17,'OBJ_EVENT_GFX_JOURNEYSEVIIBOAT'),('FiveIsland_Frlg',4,18,'OBJ_EVENT_GFX_SEAGALLOP'),
    ('SevenIsland_SevaultCanyon_Entrance_Frlg',12,4,'OBJ_EVENT_GFX_JOURNEYSEVIIBOAT'),
    ('SevenIsland_SevaultCanyon_Entrance_Frlg',20,7,'OBJ_EVENT_GFX_SEAGALLOP')}
PORT_QUARTERS = ((BEACH,(19,7),(0x1CB,0x12B,0x1D3,0x1D4),(0,2,3),0x243,True),
    ('FourIsland_Frlg',(1,27),(0x244,0x245,0x24C,0x31A),(0,1,2),0x273,False),
    ('FourIsland_Frlg',(7,35),(0x273,0x245,0x273,0x273),(1,),0x273,False),
    ('FiveIsland_Frlg',(5,14),(0x1CB,0x1CC,0x12B,0x12B),(0,1),0x243,True))
VISIBLE_LIMITS = {('ThreeIsland_Port_Frlg',44,0)} | {('FourIsland_Frlg',x,39) for x in (*range(3,8),33)} | {('SixIsland_Frlg',0,2)} | {('SevenIsland_SevaultCanyon_Entrance_Frlg',23,y) for y in range(2,9)} | {('SevenIsland_SevaultCanyon_Entrance_Frlg',0,y) for y in (*range(1,8),*range(10,19),*range(21,37))} | {('SevenIsland_SevaultCanyon_Entrance_Frlg',x,39) for x in range(6)}
OUTER_WORDS = {key:((0x1273,0x1643) if key[0]=='SevenIsland_SevaultCanyon_Entrance_Frlg' and key[1]==23
                   else (0x0676,0x0643) if key[0]=='SevenIsland_SevaultCanyon_Entrance_Frlg'
                   else (0x1673,0x1643)) for key in VISIBLE_LIMITS}
EXTENSION_PATHS = {'data/layouts/layouts.json','data/maps/map_groups.json',
    'data/event_scripts.s','src/data/journey_world_position.h','src/data/journey_world_map.h',
    'src/data/wild_encounters.json',f'data/maps/{BEACH}/map.json',f'data/maps/{SEA}/map.json',
    f'data/maps/{PASSAGE}/map.json',f'data/maps/{PASSAGE}/scripts.inc',
    f'data/layouts/{PASSAGE}/map.bin',f'data/layouts/{PASSAGE}/border.bin'}
# Independent native donor authentication, deliberately not taken from repair logs.
HORIZONTE = 'JourneyCaveHorizonte'
HORIZONTE_CLOSURES = (
    (tuple((x, y) for y in (18, 19) for x in range(14, 17)) + ((13, 19),),
     'ShoalCave_LowTideInnerRoom', (7, 0), 0x0619),
    (tuple((x, y) for y in (24, 25) for x in range(29, 32)),
     'ShoalCave_LowTideInnerRoom', (7, 0), 0x0619),
    (tuple((x, 30) for x in range(33, 36)),
     'ShoalCave_LowTideInnerRoom', (29, 30), 0x0609),
    (tuple((x, 34) for x in range(39, 42)),
     'ShoalCave_LowTideInnerRoom', (29, 30), 0x0609),
    (((19, 14),), HORIZONTE, (18, 14), 0x4211),
)


def adjacent(inputs, name):
    layout = inputs.layout(name)
    if inputs.maps[name].get('connections_no_include',False):
        return
    for connection in inputs.maps[name].get('connections') or []:
        direction = connection['direction']
        if direction not in CARDINAL:
            continue
        other = inputs.by_id[connection['map']]
        target = inputs.layout(other)
        if direction == 'left': origin = -target['width'], connection['offset']
        elif direction == 'right': origin = layout['width'], connection['offset']
        elif direction == 'up': origin = connection['offset'], -target['height']
        else: origin = connection['offset'], layout['height']
        yield other, *origin


def physical_target(inputs,name,direction,x,y):
    # mapjson deliberately emits a NULL header pointer for this native flag.
    if inputs.maps[name].get('connections_no_include',False):
        return None
    return inputs.target(name,direction,x,y)


def network_scope(inputs, names):
    names = set(names)
    pending = list(names)
    # Include incoming edges as well, including asymmetric historical links.
    links = {name: set() for name in inputs.maps}
    for name in inputs.maps:
        for other, _, _ in adjacent(inputs, name):
            links[name].add(other)
            links[other].add(name)
    while pending:
        for other in links[pending.pop()]:
            if other not in names:
                names.add(other)
                pending.append(other)
    return sorted(names)


def water(inputs, name, x, y):
    word = inputs.word(name, x, y)
    return not word & 0xC00 and inputs.behavior(name, word) in inputs.water


def land(inputs, name, x, y):
    word = inputs.word(name, x, y)
    return not word & 0xC00 and inputs.behavior(name, word) not in inputs.water


def components(inputs, name, predicate):
    layout = inputs.layout(name)
    free = {(x, y) for y in range(layout['height']) for x in range(layout['width'])
            if predicate(inputs, name, x, y)}
    labels, sizes = {}, []
    while free:
        start = free.pop()
        label, size = len(sizes), 0
        labels[start] = label
        pending = deque([start])
        while pending:
            x, y = pending.popleft()
            size += 1
            for point in ((x-1,y), (x+1,y), (x,y-1), (x,y+1)):
                if point in free:
                    free.remove(point)
                    labels[point] = label
                    pending.append(point)
        sizes.append(size)
    return labels, sizes


def check_navigation(current, old, names, predicate, allowed_removed=(), allowed_added=(), allowed_merge_maps=()):
    names = sorted(set(network_scope(old, set(names)&old.maps.keys())) | (set(current.maps)-set(old.maps)))
    allowed_removed, allowed_added = set(allowed_removed), set(allowed_added)
    labels, sizes = [], []
    for inputs in (old, current):
        pair = {name: components(inputs, name, predicate) if name in inputs.maps else ({},[]) for name in names}
        labels.append({name: row[0] for name, row in pair.items()})
        sizes.append({name: row[1] for name, row in pair.items()})
    for name in names:
        added = {(name,*cell) for cell in labels[1][name].keys()-labels[0][name].keys()}
        assert added <= allowed_added, ('Unreviewed new navigation passage',name,sorted(added-allowed_added)[:5])
        removed = {(name, *cell) for cell in labels[0][name].keys()-labels[1][name].keys()}
        assert removed <= allowed_removed, ('Unreviewed navigable cells removed', name, sorted(removed-allowed_removed)[:5])

    def joined(inputs, index):
        parent = {(name, i): (name, i) for name in names for i in range(len(sizes[index][name]))}
        graph={node:set() for node in parent}
        def find(node):
            while parent[node] != node:
                parent[node] = parent[parent[node]]
                node = parent[node]
            return node
        for name in names:
            if name not in inputs.maps:
                continue
            for x, y, direction, xx, yy in inputs.perimeter(name):
                target = physical_target(inputs,name,direction,xx,yy)
                if target is None or target[0] not in labels[index]:
                    continue
                other, tx, ty = target
                if (x,y) in labels[index][name] and (tx,ty) in labels[index][other]:
                    source_node=(name,labels[index][name][x,y])
                    target_node=(other,labels[index][other][tx,ty])
                    graph[source_node].add(target_node)
                    a = find(source_node)
                    b = find(target_node)
                    parent[b] = a
        # Keep one-way native links directed. An undirected detour alone cannot
        # prove that the player can return from a map with a NULL seam pointer.
        seen,order=set(),[]
        for start in graph:
            if start in seen:continue
            seen.add(start);pending=[(start,iter(graph[start]))]
            while pending:
                node,targets=pending[-1]
                try:target=next(targets)
                except StopIteration:
                    order.append(node);pending.pop();continue
                if target not in seen:
                    seen.add(target);pending.append((target,iter(graph[target])))
        reverse={node:set() for node in graph}
        for node,targets in graph.items():
            for target in targets:reverse[target].add(node)
        directed={}
        for start in reversed(order):
            if start in directed:continue
            directed[start]=start;pending=[start]
            while pending:
                for target in reverse[pending.pop()]:
                    if target not in directed:
                        directed[target]=start;pending.append(target)
        return {node: find(node) for node in parent},directed
    joined_pairs=[joined(old,0),joined(current,1)]
    roots=[pair[0] for pair in joined_pairs]
    directed=[pair[1] for pair in joined_pairs]
    survivors = {root: set() for root in roots[0].values()}
    removed_roots = {root: set() for root in roots[0].values()}
    for name in names:
        for point, label in labels[0][name].items():
            before = roots[0][name, label]
            if point in labels[1][name]:
                survivors[before].add(roots[1][name, labels[1][name][point]])
            else:
                removed_roots[before].add((name, *point))
    assert all(len(v) == 1 or (not v and removed_roots[k] <= allowed_removed)
               for k, v in survivors.items()), 'Global navigation component split or removed'
    merged={}
    for before,after in survivors.items():
        for root in after:merged.setdefault(root,set()).add(before)
    allowed_roots={roots[0][name,label] for name in allowed_merge_maps if name in labels[0]
                   for label in set(labels[0][name].values())}
    merges=[value for value in merged.values() if len(value)>1]
    assert all(value<=allowed_roots for value in merges), 'Unreviewed old navigation components merged'
    assert set(roots[1].values())<=set(merged), 'New isolated navigation component'
    directed_survivors={root:set() for root in directed[0].values()}
    directed_removed={root:set() for root in directed[0].values()}
    for name in names:
        for point,label in labels[0][name].items():
            root=directed[0][name,label]
            if point in labels[1][name]:directed_survivors[root].add(directed[1][name,labels[1][name][point]])
            else:directed_removed[root].add((name,*point))
    assert all(len(v)==1 or (not v and directed_removed[k]<=allowed_removed)
               for k,v in directed_survivors.items()), 'Directed navigation component split or removed'
    seams = []
    for name in names:
        openings = [set(),set()]
        for index,inputs in enumerate((old,current)):
            if name not in inputs.maps:
                continue
            for x,y,direction,xx,yy in inputs.perimeter(name):
                target = physical_target(inputs,name,direction,xx,yy)
                if target is None:
                    continue
                other,tx,ty = target
                if (x,y) in labels[index][name] and (tx,ty) in labels[index][other]:
                    openings[index].add((direction,other,x,y,tx,ty))
        assert openings[0] <= openings[1], ('Physical connection opening changed',name)
        extra = openings[1]-openings[0]
        assert all((name == PASSAGE or row[1] == PASSAGE) for row in extra), ('Unreviewed new physical opening',name)
        if openings[0]:
            rows = [list(key) for key in sorted(openings[0])]
            seams.append(dict(map=name,openings=len(rows),
                              openings_sha256=hashlib.sha256(json.dumps(rows).encode()).hexdigest()))
    removed = sorted((name, *cell) for name in names
                     for cell in labels[0][name].keys()-labels[1][name].keys())
    return dict(network_maps=names, network_maps_checked=len(names),
                global_components_before=len(set(roots[0].values())),
                global_components_after=len(set(roots[1].values())),
                all_surviving_cells_retain_global_connectivity=True,
                directed_connectivity_preserved=True,native_disabled_connection_flags_honored=True,
                directed_components_before=len(set(directed[0].values())),directed_components_after=len(set(directed[1].values())),
                only_explicitly_reviewed_new_passages=True, every_physical_opening_preserved=True,
                allowed_merge_maps=sorted(allowed_merge_maps),old_component_merges=len(merges),
                removed_cells=[list(row) for row in removed],
                added_cells=[list(row) for row in sorted((name,*cell) for name in names for cell in labels[1][name].keys()-labels[0][name].keys())],
                physical_connections=seams, physical_connections_checked=len(seams))


def check_portals(current, old):
    names, allowed, rows = set(), set(), []
    for cells, donor_name, donor_cell, expected in HORIZONTE_CLOSURES:
        names.add(HORIZONTE)
        layout, donor = old.layout(HORIZONTE), old.layout(donor_name)
        assert all(layout[k] == donor[k] for k in ('primary_tileset', 'secondary_tileset', 'layout_version'))
        assert old.word(donor_name, *donor_cell) == expected, ('Native closure donor changed', donor_name, donor_cell)
        assert all(current.word(HORIZONTE, *cell) == expected for cell in cells), ('Incomplete unused portal/stair closure', cells)
        assert not any((event['x'], event['y']) in cells
                       for group in ('warp_events', 'object_events', 'coord_events', 'bg_events')
                       for event in old.maps[HORIZONTE].get(group, [])), 'Active event overwritten by portal closure'
        changed = []
        for x, y in cells:
            a, b = old.word(HORIZONTE,x,y), current.word(HORIZONTE,x,y)
            assert a != b, ('No-op closure footprint cell', x, y)
            allowed.add((HORIZONTE,x,y))
            changed.append(dict(cell=[x,y], before=a, after=b))
        rows.append(dict(map=HORIZONTE, cells=changed, native_donor_map=donor_name,
                         native_donor_cell=list(donor_cell), native_word=expected,
                         whole_footprint=True, active_events_unchanged=True))
    labels,_=components(current,HORIZONTE,land)
    entry=labels[14,32]
    assert labels[14,33]==entry, 'Active cave exit disconnected'
    for obj in current.maps[HORIZONTE]['object_events']:
        x,y=obj['x'],obj['y']
        assert any(labels.get(point)==entry for point in ((x-1,y),(x+1,y),(x,y-1),(x,y+1))), ('NPC approach disconnected',obj)
    return dict(objects=rows, reviewed_maps=sorted(names), changed_cells=len(allowed),
                active_exit_and_all_npc_approaches_connected=True,
                complete_native_closures=True, active_entry_exit_events_preserved=True), allowed


def metatile_words(inputs,name,word):
    layout=inputs.layout(name)
    cutoff=640 if layout['layout_version']=='frlg' else 512
    mid=word&1023
    bank=layout['primary_tileset' if mid<cutoff else 'secondary_tileset']
    body=re.search(r'const struct Tileset '+re.escape(bank)+r'\s*=\s*\{(.*?)\};',inputs.headers,re.S)[1]
    symbol=re.search(r'\.metatiles\s*=\s*(\w+)',body)[1]
    path=re.search(r'\b'+symbol+r'\[\].*?"([^"]+)"',inputs.definitions)[1]
    return struct.unpack_from('<8H',(inputs.source/path).read_bytes(),16*(mid if mid<cutoff else mid-cutoff))


def check_port_objects(current,old):
    allowed,rows={},[]
    for name,(x,y),family,quarters,target,block in PORT_QUARTERS:
        before=[old.word(name,x+q%2,y+q//2) for q in range(4)]
        assert tuple(word&1023 for word in before)==family, ('Unreviewed port object footprint',name,x,y)
        after=[]
        for q,word in enumerate(before):
            expected=word
            if q in quarters:
                expected=(word&~1023)|target
                if block: expected=(expected&~0xC00)|0x400
                allowed[name,x+q%2,y+q//2]=(word,expected)
            assert current.word(name,x+q%2,y+q//2)==expected, ('Partial port scenery repair',name,x,y,q)
            after.append(expected)
        rows.append(dict(map=name,anchor=[x,y],before=before,after=after,whole_footprint=True))
    return dict(objects=rows,whole_objects=len(rows),changed_art_cells=len(allowed),whole_native_objects=True),allowed


def check_geometry(current,old,allowed_portals,port_cells):
    changes,changed_maps,removed,added=[],[],set(),set()
    outer=[]
    for name in sorted(old.maps):
        layout=current.layout(name)
        path=layout['border_filepath']
        assert (current.source/path).read_bytes()==(old.source/path).read_bytes(),('Repeated border changed',name)
        before,after=old.grid(name),current.grid(name)
        assert len(before)==len(after)
        cells=[]
        for at,(a,b) in enumerate(zip(before,after)):
            if a==b: continue
            x,y=at%layout['width'],at//layout['width']
            key=name,x,y
            if key in allowed_portals: pass
            elif key in port_cells: assert (a,b)==port_cells[key]
            elif key in MOUTHS: assert (a,b)==(0x1643,0x112B),('New passage mouth differs',key)
            elif key in CLIFF: assert (a,b)==CLIFF[key],('Cliff donor repair differs',key)
            elif name=='SixIsland_Frlg' and (a,b)==(0x1673,0x1273):
                # Exactly the declared native boarding water is restored.
                from port_boundary_scenery import current_ports
                point=next(p['boarding']['water'] for p in current_ports(old.source) if p['island']=='Six')
                assert [name,x,y]==point,('Unexpected Six boarding cell',key)
            else:
                assert OUTER_WORDS.get(key)==(a,b) and old.behavior(name,a) in old.water,('Unreviewed terrain/object changed',key,hex(a),hex(b))
                assert x in (0,layout['width']-1) or y in (0,layout['height']-1),('Boundary stone inside map',key)
                assert not any(physical_target(old,name,d,xx,yy) is not None for xx0,yy0,d,xx,yy in old.perimeter(name) if (xx0,yy0)==(x,y)),('Boundary stone closes actual connection',key)
                words=metatile_words(old,name,a)
                assert words[:4]==(0x41C6,0x41C7,0x41C7,0x41C6) and words[4:]==(0,0,0,0),('Composite shore painted as water',key)
                assert a&0xF000==b&0xF000 and b&0xC00==0x400
                outer.append(dict(map=name,cell=[x,y],before=a,after=b,pure_water_words=list(words)))
            if water(old,name,x,y) and not water(current,name,x,y): removed.add(key)
            if not water(old,name,x,y) and water(current,name,x,y): added.add(key)
            cells.append(dict(map=name,cell=[x,y],before=a,after=b))
        if cells: changed_maps.append(name);changes.extend(cells)
    assert VISIBLE_LIMITS=={(r['map'],*r['cell']) for r in outer}, 'Incomplete outer reef review'
    assert MOUTHS|set(CLIFF)|set(port_cells)|allowed_portals <= {(r['map'],*r['cell']) for r in changes}
    added|={(PASSAGE,x,y) for y in range(32) for x in range(1,7)}
    assert ('SixIsland_Frlg',2,29) in {(r['map'],*r['cell']) for r in changes}, 'Six boarding restoration missing'
    return dict(maps=len(current.maps),map_names=sorted(current.maps),changed_maps=sorted(changed_maps+[PASSAGE]),
                changed_cells=len(changes),cells=changes,outer_boundary_cells=outer,
                all_old_map_metadata_preserved_except_two_appended_connections=True,
                all_old_layout_metadata_unchanged=True,all_old_borders_unchanged=True,
                only_reviewed_native_geometry_changed=True),removed,added


def check_extension(current,old):
    assert set(current.maps)==set(old.maps)|{PASSAGE}
    newmap=current.maps[PASSAGE]
    for name,before in old.maps.items():
        expected=copy.deepcopy(before)
        if name in (BEACH,SEA):
            expected['connections'].append(dict(map='MAP_'+PASSAGE.upper(),direction='down' if name==BEACH else 'up',offset=0 if name==BEACH else 62))
        assert current.maps[name]==expected,('Old map/event/warp changed',name)
    expected=copy.deepcopy(old.maps[SEA])
    expected.update(id='MAP_'+PASSAGE.upper(),name=PASSAGE,layout='LAYOUT_'+PASSAGE.upper(),
        region_map_section='MAPSEC_ONE_ISLAND',object_events=[],warp_events=[],coord_events=[],bg_events=[],
        connections=[dict(map=old.maps[BEACH]['id'],direction='up',offset=0),dict(map=old.maps[SEA]['id'],direction='down',offset=-62)])
    assert newmap==expected,'Unexpected passage metadata'
    assert set(current.layouts)==set(old.layouts)|{newmap['layout']}
    assert all(current.layouts[key]==value for key,value in old.layouts.items()),'Old layout changed'
    layout=copy.deepcopy(old.layout(BEACH))
    layout.update(id=newmap['layout'],name=PASSAGE+'_Layout',width=8,height=32,
        blockdata_filepath=f'data/layouts/{PASSAGE}/map.bin',border_filepath=f'data/layouts/{PASSAGE}/border.bin',border_width=2,border_height=2)
    assert current.layout(PASSAGE)==layout
    assert list(current.grid(PASSAGE))==[0x1643 if x in (0,7) else 0x112B for y in range(32) for x in range(8)]
    assert (current.source/layout['border_filepath']).read_bytes()==struct.pack('<4H',*([0x1643]*4))
    groups=[json.loads((inputs.source/'data/maps/map_groups.json').read_bytes()) for inputs in (old,current)]
    before=copy.deepcopy(groups[0]);group=next(key for key in before['group_order'] if SEA in before[key])
    old_number=len(before[group]);before[group].append(PASSAGE)
    assert before==groups[1],'Existing map IDs changed'
    scripts='data/event_scripts.s'
    assert (current.source/scripts).read_text()==(old.source/scripts).read_text()+f'\n\t.include "data/maps/{PASSAGE}/scripts.inc"\n'
    assert (current.source/f'data/maps/{PASSAGE}/scripts.inc').read_text()==PASSAGE+'_MapScripts::\n\t.byte 0\n'
    wild='src/data/wild_encounters.json'
    before=json.loads((old.source/wild).read_bytes())
    matches=[(family,row) for family in before['wild_encounter_groups'] for row in family['encounters'] if row.get('map')==old.maps[SEA]['id']]
    assert len(matches)==1
    family,row=matches[0];addition=copy.deepcopy(row)
    addition.update(map=newmap['id'],base_label='gCoastalEcology_'+PASSAGE)
    family['encounters'].append(addition)
    assert json.loads((current.source/wild).read_bytes())==before,'Old encounter family changed'
    from prepare_complete_marine_atlas import point_line
    points='src/data/journey_world_map.h'
    before=(old.source/points).read_text();at=before.index('};',before.index('sWorldPoints'))
    assert (current.source/points).read_text()==before[:at]+point_line(newmap,[135,47],'ONE SOUTH PASSAGE')+before[at:],'Unexpected world chart change'
    old_values,old_grids=gps(old.source);values,grids=gps(current.source)
    assert values[:len(old_values)]==old_values and len(values)==len(old_values)+256,'Old packed GPS changed'
    assert set(grids)==set(old_grids)|{newmap['id']} and all(grids[k]==v for k,v in old_grids.items()),'Old GPS grid changed'
    w,h,cells=grids[newmap['id']]
    assert (w,h)==(8,32)
    assert cells[:8]==old_grids[old.maps[BEACH]['id']][2][47*40:47*40+8]
    assert cells[-8:]==old_grids[old.maps[SEA]['id']][2][62:70]
    maximum=max(max(abs((a&255)-(b&255)),abs((a>>8)-(b>>8))) for y in range(32) for x in range(8) for xx,yy in ((x+1,y),(x,y+1)) if xx<8 and yy<32 for a,b in [(cells[y*8+x],cells[yy*8+xx])])
    assert maximum<=1,'New passage GPS snaps'
    donors=[]
    for name,x,y,word in CLIFF_DONORS:
        assert old.layout(name)['primary_tileset']==old.layout(BEACH)['primary_tileset']
        assert old.word(name,x,y)==current.word(name,x,y)==word, ('Native cliff family donor changed',name,x,y)
        donors.append(dict(map=name,cell=[x,y],word=word))
    # Inspect the whole cap/side/foam context, not just the four replaced IDs.
    cliff_context={(7,37):0x0517,(7,38):0x0473,(7,39):0x0473,(6,38):0x1128,(6,39):0x112C,
                   (32,37):0x051F,(32,38):0x0475,(32,39):0x0475,(33,38):0x1129,(33,39):0x112A}
    assert all(current.word(BEACH,x,y)==word for (x,y),word in cliff_context.items()), 'Incomplete native cliff context'
    return dict(map=PASSAGE,dimensions=[8,32],old_map_count=len(old.maps),new_map_count=len(current.maps),
                map_group=group,appended_map_number=old_number,existing_mouth_cells=len(MOUTHS),
                native_cliff_cells=len(CLIFF),gps_values_appended=256,old_gps_values_unchanged=True,
                old_map_ids_events_warps_coordinates_and_atlas_art_preserved=True,
                two_reciprocal_connections=True,shared_gps_seams_exact=True,maximum_gps_step=maximum,
                new_water_cells=192,only_empty_map_script_added=True,native_encounter_family_preserved=True,
                native_cliff_donors=donors,complete_cliff_context=[dict(cell=list(cell),word=word) for cell,word in sorted(cliff_context.items())])


def check_port_guards(current,old,port_cells):
    """Authenticate all seven boarding pairs and all twelve complete boat bounds."""
    ports=copy.deepcopy(json.loads((old.source/'.journey-sevii-integrated-piers').read_bytes())['harbors']['ports'])
    approach=json.loads((old.source/'.journey-sevii-route-boundaries').read_bytes())['boundaries']['approach']
    assert approach['map']==BEACH and approach['original_terrain_offset']==[8,0]
    assert {p['island'] for p in ports}=={'One','Two','Three','Four','Five','Six','Seven'} and len(ports)==7
    boarding=[]
    for port in ports:
        pair={}
        for kind in ('dry','water'):
            name,x,y=port['boarding'][kind]
            if name==BEACH:x+=8
            before,after=old.word(name,x,y),current.word(name,x,y)
            expected=0x1273 if (name,x,y)==('SixIsland_Frlg',2,29) and kind=='water' else before
            assert after==expected, ('Boarding cell changed',port['island'],kind,name,x,y)
            assert (land if kind=='dry' else water)(current,name,x,y), ('Boarding terrain blocked',port['island'],kind)
            assert after>>12==(3 if kind=='dry' else 1), ('Boarding elevation changed',port['island'],kind)
            pair[kind]=dict(map=name,cell=[x,y],before=before,after=after)
        assert pair['dry']['map']==pair['water']['map']
        assert sum(abs(a-b) for a,b in zip(pair['dry']['cell'],pair['water']['cell']))==1
        expected_map,dry,wet=BOARDING_POINTS[port['island']]
        assert (pair['dry']['map'],pair['dry']['cell'],pair['water']['cell'])==(expected_map,list(dry),list(wet))
        boarding.append(dict(island=port['island'],**pair))
    declarations=(old.source/'src/data/object_events/object_event_graphics_info.h').read_text()
    for gfx,size in BOAT_SIZES.items():
        symbol={'OBJ_EVENT_GFX_SEAGALLOP':'Seagallop','OBJ_EVENT_GFX_JOURNEYSEVIIBOAT':'JourneySeviiBoat'}[gfx]
        body=re.search(r'const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_'+symbol+r' = \{(.*?)\};',declarations,re.S)[1]
        actual=tuple(int(re.search(r'\.'+key+r'\s*=\s*(\d+)',body)[1]) for key in ('width','height'))
        assert actual==size, ('Native boat size changed',gfx)
    boats=[]
    for name in sorted(PORT_MAPS):
        for event in old.maps[name].get('object_events',[]):
            gfx=event.get('graphics_id')
            if gfx not in BOAT_SIZES:continue
            width,height=BOAT_SIZES[gfx]
            left,top=16*event['x']+8-width//2,16*event['y']+16-height
            cells=[(x,y) for y in range(top//16,(top+height-1)//16+1)
                   for x in range(left//16,(left+width-1)//16+1)]
            changes=[]
            for x,y in cells:
                before,after=old.word(name,x,y),current.word(name,x,y)
                if before!=after:
                    assert port_cells.get((name,x,y))==(before,after), ('Boat footprint terrain changed',name,x,y)
                    assert before&0xFC00==after&0xFC00 and water(current,name,x,y), ('Boat clearance obstructed',name,x,y)
                    changes.append(dict(cell=[x,y],before=before,after=after))
            boats.append(dict(map=name,event_cell=[event['x'],event['y']],graphics_id=gfx,
                source_sprite_size=[width,height],pixel_bounds=[left,top,width,height],
                all_intersected_cells=[list(c) for c in cells],reviewed_art_changes=changes))
    assert len(boats)==12, ('Boat inventory changed',len(boats))
    assert {(r['map'],*r['event_cell'],r['graphics_id']) for r in boats}==BOAT_EVENTS
    return dict(boarding_pairs=boarding,boarding_pairs_checked=7,boat_footprints=boats,boat_footprints_checked=12,
                boarding_water_and_dry_elevations_valid=True,only_six_blocked_boarding_water_restored=True,
                complete_native_sprite_bounds_checked=True,no_new_boat_obstacles=True)


def _without_comments(text):
    return re.sub(r'/\*.*?\*/|//[^\n]*', '', text, flags=re.S)


def _marine_functions(text):
    spans = []
    for match in re.finditer(r'(?:static\s+)?(?:bool8|u16|void|s32)\s+(JourneyMarine\w+)\s*\([^;{}]*\)\s*\{', text):
        depth, end = 1, match.end()
        while depth and end < len(text):
            depth += (text[end] == '{')-(text[end] == '}')
            end += 1
        assert depth == 0
        spans.append((match.start(),end,match[1]))
    return spans


def check_camera_runtime(current, old):
    texts = [_without_comments((inputs.source/CAMERA_PATH).read_text()) for inputs in (old,current)]
    functions, stripped = [], []
    for text in texts:
        spans = _marine_functions(text)
        functions.append({name: re.sub(r'\s+','',text[a:b]) for a,b,name in spans})
        for a,b,name in reversed(spans):
            text = text[:a]+text[b:]
        stripped.append(re.sub(r'\s+','',text))
    assert stripped[0] == stripped[1], 'Non-drawing camera, collision, elevation or movement runtime changed'
    modified = sorted(name for name in functions[0].keys() | functions[1].keys()
                      if functions[0].get(name) != functions[1].get(name))
    assert modified, 'No expanded camera repair'
    assert set(modified) <= {'JourneyMarineViewMap','JourneyMarineCornerMetatile','JourneyMarineRectangleDistance','JourneyMarineApronMetatile'}
    return dict(modified_functions=modified, visual_queries_only=True,
                collision_elevation_movement_and_undefined_grid_unchanged=True,
                native_compatibility_checks_preserved=functions[0]['JourneyMarineViewCompatible'] == functions[1]['JourneyMarineViewCompatible'])


def check_cameras(current, old):
    # Audit scoped aperture policies separately from the raw graph census.
    from generated_coast_cameras import audit_source
    result = audit_source(current, old)
    assert result['unresolved_cells'] == 0
    return result


def compiled_map_bindings(source,inputs,names):
    """Read live map tables, headers, seam records and GPS descriptors from ROM."""
    rom=(source/'pokeemerald.gba').read_bytes()
    table=symbols(source)
    def read(address,size):
        offset=address-0x08000000
        assert 0<=offset<=len(rom)-size, ('Compiled map pointer outside ROM',address,size)
        return rom[offset:offset+size]
    def u32(address):return struct.unpack('<I',read(address,4))[0]
    groups=json.loads((source/'data/maps/map_groups.json').read_bytes())
    ids={name:(group,num) for group,key in enumerate(groups['group_order']) for num,name in enumerate(groups[key])}
    directions={'down':1,'up':2,'left':3,'right':4,'dive':5,'emerge':6}
    maps=[]
    for name in names:
        mapping=inputs.maps[name]
        group,num=ids[name]
        group_pointer=u32(table['gMapGroups'][0]+4*group)
        pointer=u32(group_pointer+4*num)
        assert pointer==table[name][0], ('Compiled map ID/table differs',name)
        layout,events,scripts,connections=struct.unpack('<4I',read(pointer,16))
        assert layout==table[inputs.layout(name)['name']][0], ('Compiled map layout differs',name)
        assert events==table[name+'_MapEvents'][0] and scripts==table[name+'_MapScripts'][0]
        counts=list(read(events,4))
        assert counts==[len(mapping.get(key,[])) for key in ('object_events','warp_events','coord_events','bg_events')], ('Compiled event counts differ',name)
        disabled=mapping.get('connections_no_include',False)
        expected=[] if disabled else mapping.get('connections') or []
        rows=[]
        raw=b''
        if expected:
            assert connections==table[name+'_MapConnections'][0], ('Compiled connection pointer differs',name,connections,table[name+'_MapConnections'][0])
            count,list_pointer=struct.unpack('<iI',read(connections,8))
            assert count==len(expected), ('Compiled connection count differs',name)
            raw=read(list_pointer,12*count)
            for index,row in enumerate(expected):
                direction,offset,target_group,target_num=struct.unpack_from('<B3xiBB2x',raw,12*index)
                target=inputs.by_id[row['map']]
                assert (direction,offset,target_group,target_num)==(directions[row['direction']],row['offset'],*ids[target]), ('Compiled physical connection differs',name,index)
                rows.append(dict(direction=row['direction'],offset=offset,target=target,map_group=target_group,map_number=target_num))
        else:
            assert connections==0, ('Unexpected compiled connection',name)
            list_pointer=0
        maps.append(dict(map=name,map_group=group,map_number=num,map_table_address=group_pointer+4*num,
            address=pointer,layout_pointer=layout,events_pointer=events,scripts_pointer=scripts,event_counts=counts,
            connection_pointer=connections,connection_list_pointer=list_pointer,connection_bytes=len(raw),
            connection_sha256=hashlib.sha256(raw).hexdigest(),connections=rows,connections_disabled=bool(disabled),
            compiled_header_and_connections_match=True))
    text=(source/'src/data/journey_world_position.h').read_text()
    descriptors=re.findall(r'\{(\d+), \(MAP_GROUP\((\w+)\)<<8\)\|MAP_NUM\(\2\), (\d+), (\d+)\}',text)
    raw=b''.join(struct.pack('<IHHH2x',int(first),(ids[inputs.by_id[ident]][0]<<8)|ids[inputs.by_id[ident]][1],int(w),int(h)) for first,ident,w,h in descriptors)
    address,size=table['sWorldTileGrids']
    assert size==len(raw) and read(address,size)==raw, 'Compiled GPS descriptors differ'
    return maps,dict(symbol='sWorldTileGrids',address=address,bytes=size,sha256=hashlib.sha256(raw).hexdigest(),
                     grids=len(descriptors),compiled_all_map_ids_dimensions_and_offsets_match=True)


def render_gallery(current, baseline, source, output, reviewed):
    from PIL import Image, ImageDraw
    from render_sea_maps import MapRenderer
    captures = []
    old_names={p.parent.name for p in (baseline/'data/maps').glob('*/map.json')}
    for phase,target in (('before',baseline),('after',source)):
        renderer = MapRenderer(target)
        directory = output.parent/'source-gallery'/phase
        directory.mkdir(parents=True,exist_ok=True)
        for name in reviewed:
            exists=name in (current.maps if phase=='after' else old_names)
            if exists:
                rendered,_ = renderer.render(name,npcs=True)
            else:
                assert phase=='before' and name==PASSAGE
                rendered=Image.new('RGB',(8*16,32*16),'#15232c')
                ImageDraw.Draw(rendered).text((6,10),'Map absent in parent',fill='white')
            image = Image.new('RGB',(max(rendered.width,480),rendered.height+38),'#15232c')
            image.paste(rendered,(0,38))
            draw = ImageDraw.Draw(image)
            draw.text((6,4),phase.upper()+' '+name,fill='white')
            draw.text((6,20),'Native asset source render with NPCs - not emulator capture',fill='#d6e6eb')
            path = directory/(name+'.png')
            image.save(path)
            layout = current.layout(name)
            captures.append(dict(file=path.relative_to(output.parent).as_posix(),sha256=digest(path),map=name,
                                 phase=phase,width_tiles=layout['width'],height_tiles=layout['height'],
                                 full_map=True,npcs=True,source_render_not_emulator=True,label_present=True,
                                 map_exists=exists,absent_parent_panel=not exists))
    return captures


def validate(source,baseline,output,preflight=False,gallery=False):
    from candidate_layer import Layer
    from prepare_generated_area_review import PRIOR,LAYER,stage_repairs,verify_parent
    source,baseline,output = map(Path,(source,baseline,output))
    assert source.resolve() != baseline.resolve()
    assert preflight or gallery, 'Final source proof requires the before/after full-map gallery'
    expected = verify_parent(baseline)
    marker = json.loads((source/('.journey-'+contract.SCOPE)).read_bytes())
    changes = marker['prepared_sha256']
    assert changes and marker['layer'] == LAYER and len(PRIOR) == 170
    assert marker['parent_rom_sha256'] == contract.PARENT_ROM_SHA256
    if not preflight or contract.PREPARED_SHA256:
        assert contract.PREPARED_SHA256 and changes == contract.PREPARED_SHA256, 'Pin exact reviewed layer171 inputs'
    for name,sha in changes.items():
        safe_relative(name)
        assert sha != expected.get(name), ('No-op staged source file',name)
    for name,sha in (expected | changes).items():
        assert digest(source/name) == sha, ('Unchanged input or reviewed overlay differs',name)
    for name in ['.source-acquired.json',*['.journey-'+name for name in PRIOR]]:
        assert (source/name).read_bytes() == (baseline/name).read_bytes(), ('Historical marker changed',name)
    replay = Layer(baseline,LAYER,PRIOR)
    metadata = stage_repairs(replay)
    replay_hashes = {name:hashlib.sha256(raw).hexdigest() for name,raw in replay.outputs.items()}
    result = dict(layer=LAYER,**metadata,original_sha256=replay.originals,prepared_sha256=replay_hashes)
    assert json.loads(json.dumps(result)) == marker, 'Independent in-memory repair replay differs'
    assert set(replay.outputs) == set(changes)
    for name,raw in replay.outputs.items():
        assert (source/name).read_bytes() == raw, ('Replayed overlay output differs',name)
    current,old = Inputs(source),Inputs(baseline)
    block_paths = {current.layout(name)['blockdata_filepath'] for name in current.maps}
    assert set(changes) <= block_paths | {CAMERA_PATH} | EXTENSION_PATHS, ('Unreviewed source, events, GPS, tilesets or atlas input',sorted(set(changes)-block_paths-{CAMERA_PATH}-EXTENSION_PATHS))
    assert CAMERA_PATH in changes
    extension=check_extension(current,old)
    portals,allowed_portals=check_portals(current,old)
    ports,port_cells=check_port_objects(current,old)
    port_guards=check_port_guards(current,old,port_cells)
    geometry,removed_water,added_water=check_geometry(current,old,allowed_portals,port_cells)
    camera_runtime = check_camera_runtime(current,old)
    assert camera_runtime['native_compatibility_checks_preserved']
    cameras = check_cameras(current,old)
    affected=set(cameras['map_names'])|set(geometry['changed_maps'])|PORT_MAPS
    water_navigation = check_navigation(current,old,affected,water,removed_water,added_water,(BEACH,SEA))
    land_removed = {(name,x,y) for name,x,y in allowed_portals if land(old,name,x,y) and not land(current,name,x,y)}
    assert land_removed == {(HORIZONTE,15,19),(HORIZONTE,30,25)}, ('Unexpected unused portal floor removed',land_removed)
    land_navigation = check_navigation(current,old,affected,land,land_removed)
    census_names = sorted(name for name in affected&old.maps.keys()
        if current.layout(name)['primary_tileset'] in {'gTileset_General','gTileset_General_Frlg','gTileset_JourneySeviiSea'})
    boulders = check_boulders(current,old,census_names)
    reviewed = set(geometry['changed_maps']) | set(cameras['changed_camera_maps'])
    reviewed |= {other for name in list(reviewed) for other,_,_ in adjacent(current,name)}
    reviewed = sorted(reviewed)
    compiled_names = sorted(set(cameras['map_names']) | set(reviewed) | set(water_navigation['network_maps']) | set(land_navigation['network_maps']))
    layouts,runtime,projection,segments = [],[],None,0
    headers,grids=[],None
    rom_sha = elf_sha = None
    if not preflight:
        layouts,runtime,projection,segments = compiled_bindings(source,current,compiled_names)
        headers,grids=compiled_map_bindings(source,current,compiled_names)
        rom_sha,elf_sha = digest(source/'pokeemerald.gba'),digest(source/'pokeemerald.elf')
        assert rom_sha != contract.PARENT_ROM_SHA256 and elf_sha != contract.PARENT_ELF_SHA256
    captures = render_gallery(current,baseline,source,output,reviewed) if gallery else []
    for name,sha in (expected | changes).items():
        assert digest(source/name)==sha, ('Source changed while proof was reading it',name)
    for name in ['.source-acquired.json',*['.journey-'+name for name in PRIOR]]:
        assert (source/name).read_bytes()==(baseline/name).read_bytes(), ('Historical marker changed during source proof',name)
    assert json.loads((source/('.journey-'+contract.SCOPE)).read_bytes())==marker, 'Layer marker changed during source proof'
    if not preflight:
        assert (digest(source/'pokeemerald.gba'),digest(source/'pokeemerald.elf'))==(rom_sha,elf_sha), 'ROM or ELF changed during source proof'
    report = dict(kind='generated-area-review-source',passed=not preflight,preflight=bool(preflight),
        compiled_rom=not preflight,independent_replay=True,layers=PRIOR+[LAYER],
        parent_rom_sha256=contract.PARENT_ROM_SHA256,prepared_sha256=changes,changed_files=sorted(changes),
        rom_sha256=rom_sha,elf_sha256=elf_sha,source_hashes_checked=len(expected | changes),
        prefix_markers_unchanged=True,unrelated_source_files_unchanged=True,scripts_and_atlas_art_unchanged=True,
        stable_source_rechecked=True,stable_rom_elf_rechecked=not preflight,
        geometry_audit=geometry,portal_audit=portals,port_object_audit=ports,port_guards=port_guards,south_passage_audit=extension,camera_runtime=camera_runtime,camera_audit=cameras,
        boulder_census=boulders,surface_navigation=water_navigation,land_navigation=land_navigation,
        compiled_map_names=compiled_names,compiled_layouts=layouts,compiled_runtime=runtime,compiled_gps=projection,
        compiled_map_headers=headers,compiled_gps_grids=grids,
        runtime_export_names=list(RUNTIME_SYMBOLS),elf_rom_load_segments_checked=segments,
        reviewed_maps=reviewed,captures=captures,source_gallery_rendered=bool(gallery),
        source_gallery_not_emulator=True,full_campaign_playthrough=False)
    verify_parent(baseline)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--baseline',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--preflight',action='store_true')
    parser.add_argument('--gallery',action='store_true')
    args=parser.parse_args()
    print(json.dumps(validate(args.source,args.baseline,args.output,args.preflight,args.gallery),indent=2))
