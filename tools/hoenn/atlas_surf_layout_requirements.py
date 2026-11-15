"""Bind complete source-audit obligations to the staged final map identities.

Inventory names never become teleport destinations or invented graph edges.
Every cave return, Dive coordinate, port seed and native mixed-pixel witness
is resolved through the actual staged maps and registered local rectangles.
"""
from atlas_surf_source import CARDINAL


def build_requirements(inputs,metadata,parent_inventory,native_census,*,bank_pairs=()):
    plan=metadata['geometry_plan'];by_name={r['name']:r for r in plan['chunks']}
    generated=set(by_name);retired={r['map'] for r in metadata['expected_retired_maps']}
    result=dict(complete=True,ports=[],caves=[],dives=[],adapters=[],native_pixels=[],
                authenticated_bank_pairs=[list(p) for p in bank_pairs])
    for port in parent_inventory['pois']['integrated_ports']:
        result['ports'].append(dict(key=port['island'],dry=port['boarding']['dry'],water=port['boarding']['water']))
    relocations={(r['source_map'],r['field'],r['source_index']):r
                 for r in metadata['objects']['relocated_events']}
    for cave in parent_inventory['pois']['surface_caves']:
        row=relocations[cave['surface'],'warp_events',cave['surface_warp']]
        result['caves'].append(dict(key=cave['interior'],surface=row['target_map'],
                                   surface_warp=row['target_index'],interior=cave['interior'],
                                   interior_warp=cave['interior_warp']))
    def owner(x,y):
        found=[r for r in plan['chunks'] if r['origin'][0]<=x<r['origin'][0]+r['width']
               and r['origin'][1]<=y<r['origin'][1]+r['height']]
        if len(found)!=1:raise ValueError(('Source obligation lacks one physical owner',x,y))
        return found[0]
    for site in metadata['dives']['sites']:
        x,y,w,h=site['global_rect'];surface=owner(x,y)
        if any(owner(gx,gy)['name']!=surface['name'] for gy in range(y,y+h) for gx in range(x,x+w)):
            raise ValueError('Fixed native Dive patch spans unexpected physical owners')
        ox,oy=surface['origin']
        result['dives'].append(dict(key=site['name'],surface=surface['name'],depth=site['depth'],
            model='atlas-affine',surface_origin=[ox,oy],depth_origin=site['depth_origin'],
            points=[[gx-ox,gy-oy] for gy in range(y,y+h) for gx in range(x,x+w)]))
    for binding in metadata['adapter_plan']['bindings']:
        row=by_name[binding['adapter']];dx,dy=CARDINAL[binding['direction']]
        x,y=binding['global_tile'];ox,oy=row['origin']
        point=[row['name'],x+dx-ox,y+dy-oy]
        if not inputs.water(*point):raise ValueError(('Native coast obligation is not actual adapter water',point))
        result['adapters'].append(dict(key=f"{binding['native_map']}:{binding['component']}",point=point))
    for pixel in native_census['pixels']:
        cells=[r for r in pixel['cells'] if r['expected_component_water']]
        if not cells:raise ValueError(('Registered chart pixel has no real native water witness',pixel['atlas']))
        cell=cells[0];name=cell['native_map'];component=cell['registered_component']
        matches=[i for i,r in enumerate(plan['native_regions'])
                 if r['native_map']==name and r['component']==component]
        if len(matches)!=1:raise ValueError('Native witness lacks one actual registered coast region')
        result['native_pixels'].append(dict(key=','.join(map(str,pixel['atlas'])),
            point=[name,*cell['native_tile']],atlas=pixel['atlas'],authenticated=True,
            native_region_index=matches[0]))
    # Include actual native sea connections needed by this ocean audit. A
    # country-wide road closure would pull unrelated inland maps into scope;
    # this proof does not certify a complete campaign or every city street.
    names={r['native_map'] for r in metadata['adapter_plan']['bindings']}
    names.update(p[0] for row in result['ports'] for p in (row['dry'],row['water']))
    for row in result['caves']:names.add(row['interior'])
    for site in metadata['dives']['sites']:names.update((site['depth'],site['sanctuary']))
    todo=list(names)
    def wet_border(first,second,direction,offset):
        a,b=inputs.layout(first),inputs.layout(second)
        axis='height' if direction in ('left','right') else 'width'
        for value in range(max(0,offset),min(a[axis],offset+b[axis])):
            source=((a['width']-1 if direction=='right' else 0),value) if axis=='height' else (value,a['height']-1 if direction=='down' else 0)
            target=((0 if direction=='right' else b['width']-1),value-offset) if axis=='height' else (value-offset,0 if direction=='down' else b['height']-1)
            if inputs.water(first,*source) and inputs.water(second,*target):return True
        return False
    for name in todo:
        if name in retired:raise ValueError('Source obligation still enters an obsolete map')
        for connection in inputs.maps[name].get('connections') or []:
            if connection['direction'] not in CARDINAL:continue
            target=inputs.by_id[connection['map']]
            if target in retired:raise ValueError(('Active native connection still enters retired geometry',name,target))
            if target not in names and target not in generated:
                if not wet_border(name,target,connection['direction'],int(connection['offset'])):continue
                if target not in inputs.identities:raise ValueError('Native transit map is absent from compiled registry')
                names.add(target);todo.append(target)
    result['transit_maps']=sorted(names-generated)
    result['native_transit_expansion']='actual-native-Surf-border-pairs-plus-required-dry-port-and-cave-maps'
    result['inventory_counts']={key:len(result[key]) for key in ('ports','caves','dives','adapters','native_pixels')}
    inputs.assert_unchanged()
    return result
