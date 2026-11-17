"""Move retired AREA references to exact, reachable current species triggers.

Habitat owners changed with the physical ocean replacement. An old owner no
longer identifies a current route. This explicit migration uses the compiled
per-species/cap census and the actual graph, leaving encounters untouched.
"""
import hashlib
import re

from atlas_surf_ecology import DEX_ROW


def relocate(header,before,after,plan,catalog):
    if any(r.get('schema')!='atlas-surf-ecology-source-v1' or not r.get('native_c_compiled') for r in (before,after)):
        raise ValueError('Both compiled ecology censuses are required')
    if not after.get('graph_reachable_cells_supplied') or before.get('retired_maps'):
        raise ValueError('Current triggers need graph witnesses; historical triggers must remain visible')
    if plan.get('scale')!=8:
        raise ValueError('AREA relocation requires the physical scale8 plan')
    retired=set(after['retired_maps']);old_names={v:k for k,v in before['map_constants'].items()}
    species={int(k):v['name'] for k,v in catalog.items()}
    chunks={r['name']:r for r in plan['chunks']}
    if len(chunks)!=len(plan['chunks']):
        raise ValueError('Duplicate physical map')
    active=set()
    for row in before['map_areas']:
        for cap,members in row['species'].items():
            active.update((row['map'],species[s],4 if int(cap)==493 else 9) for s in members)
    witnesses={}
    for row in after['map_areas']:
        if row['map'] not in chunks or not any(row['species'].values()):
            continue
        chunk=chunks[row['map']]
        if row['map'] in retired or after['aliases'].get(row['map'])!=row['owner']:
            raise ValueError('Current habitat identity differs from compiled alias')
        if chunk['id']!=after['map_constants'][row['map']]:
            raise ValueError('AREA map constant differs from physical map')
        if not row['trigger_sample'] or row['terrain_trigger_cells']<=0 or not row['native_header_present']:
            raise ValueError('No actual reachable encounter trigger')
        x,y=row['trigger_sample'][0]
        if not (0<=x<chunk['width'] and 0<=y<chunk['height']):
            raise ValueError('Trigger outside its real map')
        ax,ay=((chunk['origin'][0]+x)//8,(chunk['origin'][1]+y)//8)
        if not (0<=ax<224 and 0<=ay<112):
            raise ValueError('Trigger projects outside native atlas')
        for cap,members in row['species'].items():
            for sid in members:
                key=species[sid],4 if int(cap)==493 else 9
                witnesses.setdefault(key,[]).append(dict(map=row['map'],constant=chunk['id'],owner=row['owner'],
                    tile=[x,y],atlas=[ax,ay],area=row['area'],field=row['field']))
    matches=list(DEX_ROW.finditer(header))
    if not matches or header.count('sWorldDexLocations')!=1:
        raise ValueError('Missing or ambiguous AREA array')
    unchanged={m[0] for m in matches if old_names.get(m[2]) not in retired}
    emitted=set(unchanged);relocations=[];dead=[]
    def replace(match):
        name,constant=match[1],match[2];old=old_names.get(constant)
        if old not in retired:
            return match[0]
        x,y,fixed,cap=map(int,match.groups()[2:])
        if fixed:
            raise ValueError('Fixed event on retired map needs its own event migration')
        if (old,name,cap) not in active:
            dead.append(dict(map=old,species=name,cap=cap));return ''
        choices=witnesses.get((name,cap))
        if not choices:
            raise ValueError(('Previously catchable species has no reachable current trigger',old,name,cap))
        target=min(choices,key=lambda r:(r['owner']!=old,abs(r['atlas'][0]-x)+abs(r['atlas'][1]-y),r['map'],r['area'],r['tile']))
        replacement='{'+','.join(map(str,(name,target['constant'],*target['atlas'],0,cap)))+'}'
        relocations.append(dict(old_map=old,species=name,cap=cap,old_atlas=[x,y],witness=target,
            owner_changed=target['owner']!=old,replacement=replacement))
        if replacement in emitted:
            return ''
        emitted.add(replacement);return replacement
    rewritten=DEX_ROW.sub(replace,header)
    # A removed initializer must lose its comma as well.
    rewritten=re.sub(r'^\s*,\s*\n','',rewritten,flags=re.M)
    if any(old_names.get(m[2]) in retired for m in DEX_ROW.finditer(rewritten)):
        raise ValueError('Retired AREA reference remains')
    if not unchanged<={m[0] for m in DEX_ROW.finditer(rewritten)}:
        raise ValueError('A native or fixed current AREA row changed')
    return rewritten,dict(kind='retired-habitat-AREA-relocation',passed=True,
        before_header_sha256=hashlib.sha256(header.encode()).hexdigest(),
        after_header_sha256=hashlib.sha256(rewritten.encode()).hexdigest(),
        before_census_manifest_sha256=before['source_manifest_sha256'],
        current_census_manifest_sha256=after['source_manifest_sha256'],
        relocated=relocations,removed_historically_ineffective=dead,
        exact_species_and_generation_cap_and_reachable_trigger_required=True,
        native_and_fixed_rows_preserved=True,encounter_content_changed=False,compiled_ROM_validated=False)
