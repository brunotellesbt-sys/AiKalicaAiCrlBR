"""Find coast interfaces by native water component, without choosing fake exits."""
from collections import defaultdict
import hashlib

from atlas_surf_source import compatible_height


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
