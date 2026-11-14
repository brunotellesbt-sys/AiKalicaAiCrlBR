"""Inventory actual portals, fixed cave anchors, Dive and current Sevii piers.

All records refer to the immutable parent. No warp, actor or cave is moved by
this inventory. Explicit final destinations and controller proofs still have
to be supplied by the replacement layer.
"""
import copy


def terrain(inputs, name, point):
    word = inputs.word(name, *point)
    return dict(map=name, tile=list(point), word=word, metatile=word & 1023,
                height=word >> 12, collision=(word >> 10) & 3,
                behavior=inputs.behavior(name, word), surfable=inputs.water(name, *point),
                banks=[inputs.layout(name)['primary_tileset'], inputs.layout(name)['secondary_tileset']])


def _portal(inputs, surface, number, interior, interior_number, anchors):
    entry = inputs.maps[surface]['warp_events'][number]
    target_events = inputs.maps[interior].get('warp_events') or []
    if not 0 <= interior_number < len(target_events):
        raise ValueError(('Portal destination warp missing', surface, number, interior, interior_number))
    target = target_events[interior_number]
    if target['dest_map'] != inputs.maps[surface]['id'] or int(target['dest_warp_id']) != number:
        raise ValueError(('Portal lacks its reciprocal source warp', surface, number, interior, interior_number))
    if interior not in anchors:
        raise ValueError(('Cave has no authenticated fixed atlas anchor', interior))
    return dict(surface=surface, surface_warp=number, interior=interior, interior_warp=interior_number,
                fixed_atlas=anchors[interior]['atlas'],
                surface_entry=terrain(inputs, surface, [entry['x'], entry['y']]),
                interior_warp_tile=terrain(inputs, interior, [target['x'], target['y']]),
                surface_event=copy.deepcopy(entry), interior_event=copy.deepcopy(target),
                reciprocal_events=True, destination_assigned=False,
                actual_native_spawn_position_and_return_pending=True)


def current_ports(inputs):
    """Use version1's recorded +8x once when reading the old port metadata."""
    rows = copy.deepcopy(inputs.js('.journey-sevii-integrated-piers')['harbors']['ports'])
    approach = inputs.js('.journey-sevii-route-boundaries')['boundaries']['approach']
    if approach['map'] != 'OneIsland_TreasureBeach_Frlg' or approach['original_terrain_offset'] != [8, 0]:
        raise ValueError('Historical Treasure Beach translation changed')
    result = []
    for port in rows:
        boarding = port['boarding']
        for key in ('dry', 'water'):
            if boarding[key][0] == approach['map']:
                boarding[key][1] += 8
        dry_map, dx, dy = boarding['dry']; wet_map, wx, wy = boarding['water']
        dry, wet = terrain(inputs, dry_map, [dx, dy]), terrain(inputs, wet_map, [wx, wy])
        if dry['collision'] or dry['height'] != 3 or dry['surfable'] or not wet['surfable']:
            raise ValueError(('Integrated boarding seed no longer matches dry/Surf terrain', port['island']))
        result.append(dict(island=port['island'], town=port['town'], interior=port['interior'],
                           exterior=port['map'], boarding=boarding,
                           dry_terrain=dry, water_terrain=wet,
                           boat_events=[dict(map=name, event=copy.deepcopy(event))
                                        for name in sorted({port['map'], wet_map, dry_map})
                                        for event in inputs.maps[name].get('object_events', [])
                                        if 'BOAT' in event.get('graphics_id', '') or 'SEAGALLOP' in event.get('graphics_id', '')],
                           current_ferry_arrivals_repointed=False,
                           native_boarding_roundtrip_pending=True))
    return result


def inventory(inputs, coast_inventory):
    anchors = inputs.anchors()
    surfaces = [_portal(inputs, row['surface'], row['surface_warp'], row['interior'],
                         row['interior_warp'], anchors) for row in coast_inventory['external_warps']]
    dives = []
    for site in inputs.js('.journey-sanctuaries')['sites']:
        if site['access'] != 'dive':
            continue
        surface = site['surface']
        links = [row for row in inputs.maps[surface].get('connections') or [] if row['direction'] == 'dive']
        if len(links) != 1:
            raise ValueError(('Dive surface needs one explicit Depth connection', surface))
        depth = inputs.by_id[links[0]['map']]
        events = [(i, row) for i, row in enumerate(inputs.maps[depth]['warp_events'])
                  if row['dest_map'] == inputs.maps[site['map']]['id']]
        if len(events) != 1:
            raise ValueError(('Depth needs one real sanctuary portal', depth))
        number, event = events[0]
        portal = _portal(inputs, depth, number, site['map'], int(event['dest_warp_id']), anchors)
        emerge = [row for row in inputs.maps[depth].get('connections') or [] if row['direction'] == 'emerge']
        if len(emerge) != 1 or emerge[0]['map'] != inputs.maps[surface]['id']:
            raise ValueError(('Depth emerge reference is not its real surface', depth))
        portal.update(theme=site['theme'], old_surface=surface, depth=depth,
                      depth_events_and_layout_preserved=True,
                      new_dive_patch_reserved=False, native_dive_emerge_pending=True)
        dives.append(portal)
    return dict(kind='atlas-parent-poi-inventory', surface_caves=surfaces, dive_sites=dives,
                integrated_ports=current_ports(inputs),
                fixed_cave_anchors_read_from_source=True,
                old_interpolated_player_gps_used=False,
                replacement_warps_created=False, global_reachability_proven=False,
                native_validated=False)
