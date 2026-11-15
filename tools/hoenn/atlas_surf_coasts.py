"""Inventory the old physical marine mesh and stage the exact Route114 closure.

An inventory preserves old identities and event records. It neither removes
maps nor supplies guessed relocations; applying the final replacement needs
explicit POI, actor, adapter and save destinations and a new graph audit.
"""
import hashlib
import json
import struct

from atlas_surf_source import CARDINAL, OPPOSITE
from atlas_surf_truth import decode_atlas
from badge_story_layer import read


ISLANDS = ('One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven')
EVENT_FIELDS = ('object_events', 'warp_events', 'coord_events', 'bg_events')
PROTECTED_PORT = 'JourneyRoute12Shipyard'


def retirement_scope(inputs):
    """Derive active generated oceans, preserving the authenticated shipyard.

    The isolated, event-free prototype is already inactive. Seven old harbor
    exteriors now contain only water/connections, while their integrated town
    terminals and interior actors remain outside the replacement scope.
    No target count determines membership.
    """
    candidates, inactive, protected = set(), [], []
    for name, mapping in sorted(inputs.maps.items()):
        if not name.startswith('Journey') or mapping['map_type'] != 'MAP_TYPE_OCEAN_ROUTE':
            continue
        live = any(c['direction'] in CARDINAL for c in mapping.get('connections') or [])
        if not live and not any(mapping.get(field) for field in EVENT_FIELDS):
            inactive.append(dict(map=name, reason='isolated event-free historical prototype'))
        elif name != PROTECTED_PORT:
            candidates.add(name)
    if PROTECTED_PORT in inputs.maps:
        mapping = inputs.maps[PROTECTED_PORT]
        anchor = inputs.anchors().get(PROTECTED_PORT)
        if anchor is None or anchor['atlas'] != [96, 40] or not mapping['object_events'] or not mapping['warp_events']:
            raise ValueError('Protected shipyard identity or port events changed')
        truth = decode_atlas(inputs.read('src/data/journey_world_map.h').decode())
        pattern = [truth.pixel((96+dx, 40+dy)) for dy in (-1, 0, 1) for dx in (-1, 0, 1)]
        if pattern != [14, 14, 14, 14, 2, 14, 14, 14, 14]:
            raise ValueError('Protected shipyard blue center is no longer the authenticated port icon')
        protected.append(dict(map=PROTECTED_PORT, atlas=anchor['atlas'],
                              reason='complete active port; its blue icon center is not a sea route',
                              actors=len(mapping['object_events']), warps=len(mapping['warp_events'])))
    for island in ISLANDS:
        name = island+'Island_Harbor_Frlg'
        if name not in inputs.maps:
            raise ValueError(('Missing historical harbor exterior', name))
        mapping = inputs.maps[name]
        if mapping['map_type'] != 'MAP_TYPE_OCEAN_ROUTE' or any(mapping.get(field) for field in EVENT_FIELDS):
            raise ValueError(('Cannot retire an exterior with remaining events', name))
        candidates.add(name)
    return sorted(candidates), inactive, protected


def inventory(inputs):
    names, inactive, protected = retirement_scope(inputs)
    retired = set(names)
    rows, interfaces, external_warps = [], [], []
    for name in names:
        mapping = inputs.maps[name]
        layout = inputs.layout(name)
        path = f'data/maps/{name}/map.json'
        rows.append(dict(map=name, id=mapping['id'], packed_id=inputs.identities[name],
                         dimensions=[layout['width'], layout['height']], layout=mapping['layout'],
                         banks=[layout['primary_tileset'], layout['secondary_tileset']],
                         map_sha256=hashlib.sha256(inputs.read(path)).hexdigest(),
                         blockdata=layout['blockdata_filepath'],
                         blockdata_sha256=hashlib.sha256(inputs.read(layout['blockdata_filepath'])).hexdigest(),
                         events={field: mapping.get(field, []) for field in EVENT_FIELDS}))
        for index, connection in enumerate(mapping.get('connections') or []):
            direction = connection['direction']
            if direction not in CARDINAL:
                continue
            native = inputs.by_id[connection['map']]
            if native in retired:
                continue
            reverse = [row for row in inputs.maps[native].get('connections') or []
                       if row['map'] == mapping['id'] and row['direction'] == OPPOSITE[direction]
                       and row['offset'] == -connection['offset']]
            interfaces.append(dict(retired_map=name, native_map=native, direction=direction,
                                   offset=connection['offset'], connection_index=index,
                                   reciprocal=len(reverse) == 1, reverse_matches=len(reverse)))
        for number, warp in enumerate(mapping.get('warp_events') or []):
            destination = inputs.by_id[warp['dest_map']]
            if destination not in retired:
                external_warps.append(dict(surface=name, surface_warp=number, interior=destination,
                                           interior_warp=int(warp['dest_warp_id']),
                                           entry=[warp['x'], warp['y']], elevation=warp['elevation']))
    return dict(kind='atlas-parent-coast-inventory', retired_maps=rows, inactive_maps=inactive,
                protected_maps=protected, native_interfaces=interfaces,
                external_warps=external_warps, historical_ids_preserved=True,
                replacement_applied=False, migration_destinations_assigned=False,
                native_runtime_policy_evaluated=False, final_source_audit=False,
                native_validated=False)


def stage_route114_closure(layer):
    """Close only the two approved false-ocean cells; preserve row16 and events."""
    mapping = json.loads(read(layer, 'data/maps/Route114/map.json'))
    layouts = json.loads(read(layer, 'data/layouts/layouts.json'))['layouts']
    layout = next(row for row in layouts if row['id'] == mapping['layout'])
    if layout['layout_version'] != 'emerald' or layout['primary_tileset'] != 'gTileset_General':
        raise ValueError('Route114 donor bank changed; metatile IDs cannot be assumed universal')
    path = layout['blockdata_filepath']
    original = read(layer, path)
    width, height = layout['width'], layout['height']
    if width < 1 or height <= 18 or len(original) != 2*width*height:
        raise ValueError('Route114 dimensions changed')
    values = list(struct.unpack('<'+'H'*(width*height), original))
    changes = []
    for x, y in ((0, 17), (0, 18)):
        index = y*width+x
        if values[index] != 0x1170:
            raise ValueError(('False ocean mouth is not the expected native water', x, y, values[index]))
        changes.append(dict(cell=[x, y], before=values[index], after=0x15F9))
        values[index] = 0x15F9
    result = struct.pack('<'+'H'*len(values), *values)
    if original[16*width*2:17*width*2] != result[16*width*2:17*width*2]:
        raise AssertionError('Native lagoon-margin row16 changed')
    layer.stage(path, result)
    return dict(kind='route114-false-ocean-mouth-closure', map='Route114', cells=changes,
                before_sha256=hashlib.sha256(original).hexdigest(),
                after_sha256=hashlib.sha256(result).hexdigest(),
                row16_lagoon_margin_and_all_other_cells_preserved=True,
                events_npcs_connections_and_atlas_unchanged=True,
                native_validated=False)


def stage_closed_native_connections(layer,inputs,retired_maps,*,route114_closure):
    """Remove obsolete, blocked native faces and the authorized Route114 link.

    Live wet or walkable interfaces cannot silently disappear. The Route114
    exception is the user's explicit removal of an inland lagoon's false ocean
    connection; its two-cell repair must already exist and row16 stays intact.
    This changes connections only, preserving all native events and terrain.
    """
    retired={r['map'] if isinstance(r,dict) else r for r in retired_maps}
    by_id=inputs.by_id;outputs={};removed=[]
    layouts={r['id']:r for r in json.loads(read(layer,'data/layouts/layouts.json'))['layouts']}
    for name in sorted(set(inputs.maps)-retired):
        path=f'data/maps/{name}/map.json';mapping=json.loads(read(layer,path))
        remaining=[];old_connections=mapping.get('connections') or []
        for connection in old_connections:
            old=by_id.get(connection['map'])
            if old not in retired:
                remaining.append(connection);continue
            direction=connection['direction'];offset=int(connection['offset'])
            if direction not in ('left','right','up','down'):
                raise ValueError(('Unresolved non-cardinal retired native connection',name,connection))
            a,b=layouts[mapping['layout']],inputs.layout(old)
            raw=read(layer,a['blockdata_filepath']);native_words=struct.unpack('<'+'H'*(len(raw)//2),raw)
            axis='height' if direction in ('left','right') else 'width';pairs=[]
            for value in range(max(0,offset),min(a[axis],offset+b[axis])):
                source=((a['width']-1 if direction=='right' else 0),value) if axis=='height' else (value,a['height']-1 if direction=='down' else 0)
                target=((0 if direction=='right' else b['width']-1),value-offset) if axis=='height' else (value-offset,0 if direction=='down' else b['height']-1)
                first=native_words[source[1]*a['width']+source[0]];second=inputs.word(old,*target)
                pairs.append(dict(native_tile=list(source),old_tile=list(target),words=[first,second]))
            lagoon=name=='Route114'
            if lagoon:
                if (route114_closure.get('kind')!='route114-false-ocean-mouth-closure'
                        or route114_closure.get('map')!='Route114'
                        or [r['cell'] for r in route114_closure['cells']]!=[[0,17],[0,18]]
                        or any(native_words[y*a['width']]!=0x15f9 for y in (17,18))):
                    raise ValueError('Route114 false-ocean disconnection lacks its exact authorized repair')
            elif any(not (r['words'][0]&0xc00 or r['words'][1]&0xc00) for r in pairs):
                raise ValueError(('Obsolete native face still has an unreplaced traversable pair',name,old))
            removed.append(dict(native_map=name,old_map=old,connection=connection,
                                native_edge_pairs=pairs,
                                reason='explicitly rejected Route114 inland-lagoon ocean access' if lagoon
                                       else 'every actual boundary pair blocked before retirement'))
        if remaining!=old_connections:
            mapping['connections']=remaining;outputs[path]=(json.dumps(mapping,indent=2)+'\n').encode()
    for path,raw in outputs.items():layer.stage(path,raw)
    inputs.assert_unchanged()
    return dict(kind='retired-closed-native-faces',removed=removed,
                native_terrain_and_events_unchanged=True,native_validated=False)
