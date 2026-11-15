"""Place complete native scenery beside the fixed atlas sea corridors.

The old map's fixed logical anchor supplies a decoration region, never a
player GPS sample. Every accepted relocation preserves native words, events
and water masks. Dry objects stay outside the six-tile travel corridor. The
five old deep-water squares are explicitly replaced by the fixed Dive patches.
This is a source plan; SCC, rendering and native travel must still certify it.
"""
from collections import defaultdict
from copy import deepcopy

from atlas_surf_dives import OLD_SURFACES, patch_specs
from atlas_surf_geometry import rasterize
from atlas_surf_scenery import _runs
from atlas_surf_scenery import bind_native_water, placement
from atlas_surf_truth import ATLAS_WIDTH, ATLAS_HEIGHT, OCEAN_INDEX, ROUTE_INDEX


def _cells(runs):
    return {(x,y) for y,start,end in runs for x in range(start,end)}


def _rect(row):
    x,y=row['origin']
    return x,y,x+row['width'],y+row['height']


class _Occupied:
    def __init__(self, rows=()):
        self.rows=[];self.buckets=defaultdict(set)
        for row in rows:self.add(row)

    @staticmethod
    def keys(rect):
        x,y,r,b=rect
        return ((cx,cy) for cy in range(y//32,(b-1)//32+1)
                for cx in range(x//32,(r-1)//32+1))

    def overlaps(self, rect):
        x,y,r,b=rect
        possible=set().union(*(self.buckets[key] for key in self.keys(rect)))
        return any(max(x,a)<min(r,c) and max(y,d)<min(b,e)
                   for a,d,c,e in (self.rows[i] for i in possible))

    def add(self, row):
        rect=_rect(row)
        if self.overlaps(rect):
            raise ValueError(('Whole scenery reservation overlaps an existing feature',row['name']))
        index=len(self.rows);self.rows.append(rect)
        for key in self.keys(rect):self.buckets[key].add(index)


def fixed_dive_reservations(inventory, route_water, *, halo=9):
    """Replace only the five authenticated obsolete Dive surface squares.

    The Depth layouts/portals are untouched. The surface's original 5x5 deep
    water marker becomes the explicit 5x3 native Dive patch of the new design;
    no unrelated decoration or actor is discarded.
    """
    result=[];replacements=[]
    for site in patch_specs():
        candidates=[s for s in inventory['stamps']
                    if s['parent_map']==OLD_SURFACES[site['name']]
                    and s['source_anchor']==site['portal']
                    and s['source_rect'][2:]==[5,5]
                    and len(set(s['words']))==1
                    and s['kind']=='water-decoration' and not s['events']]
        if len(candidates)!=1:
            raise ValueError(('Fixed Dive feature lacks its complete original stamp',site['name']))
        stamp=candidates[0]
        if set(_cells(stamp['native_water_runs']))!={(x,y) for y in range(5) for x in range(5)}:
            raise ValueError('Obsolete Dive marker contains non-water terrain')
        x,y,w,h=site['global_rect'];origin=[x-halo,y-halo]
        row=dict(name='JourneyAtlasDive'+site['name'],kind='dive',origin=origin,
                 width=w+2*halo,height=h+2*halo,camera_halo=halo,
                 donor='JourneyHoennNorthSea',ecology_owner=stamp['parent_map'],
                 preferred_donor_banks=deepcopy(site['preferred_donor_banks']),dive_site=deepcopy(site),
                 additional_water_runs=[[halo+dy,halo,halo+w] for dy in range(h)],
                 native_water_evidence=dict(original_stamp=stamp['key'],
                                            stamp_sha256=stamp['stamp_sha256'],
                                            fixed_dive_patch=site['global_rect']),
                 evidence=dict(original_stamp=stamp['key'],stamp_sha256=stamp['stamp_sha256'],
                               fixed_atlas=site['atlas'],surface_feature_replaced='5x5 deep water to 5x3 Dive patch'))
        result.append(row)
        replacements.append(dict(stamp=stamp['key'],stamp_sha256=stamp['stamp_sha256'],
                                 reservation=row['name'],site=site['name'],
                                 original_shape=[5,5],replacement_shape=[5,3],events_preserved=0))
    return dict(reservations=result,replaced_stamps=replacements,native_validated=False)


def _candidate_origins(stamp, pixels, anchor, radius):
    """Keep the complete object on either side of an authentic route pixel."""
    water=_cells(stamp['native_water_runs'])
    w,h=stamp['source_rect'][2:]
    dry={(x,y) for y in range(h) for x in range(w)}-water
    # An actor's water cell remains water, but its footprint cannot obstruct the
    # main channel. Sprite dimensions are authenticated by extraction/render.
    protected=dry or {tuple(p) for p in stamp['core_cells']}
    minx=min(x for x,y in protected);maxx=max(x for x,y in protected)
    miny=min(y for x,y in protected);maxy=max(y for x,y in protected)
    nearby=sorted((p for p in pixels if abs(p[0]-anchor[0])+abs(p[1]-anchor[1])<=radius),
                  key=lambda p:(abs(p[0]-anchor[0])+abs(p[1]-anchor[1]),p[1],p[0]))
    seen=set()
    for px,py in nearby:
        # The protected six cells occupy offsets1..6. Start dry scenery at7
        # or finish it at0; native beach water may touch the channel itself.
        for phase in (4,3,5,2,6,1,7,0):
            candidates=((px*8+phase-stamp['anchor_offset'][0],py*8+7-miny),
                        (px*8+phase-stamp['anchor_offset'][0],py*8-maxy),
                        (px*8+7-minx,py*8+phase-stamp['anchor_offset'][1]),
                        (px*8-maxx,py*8+phase-stamp['anchor_offset'][1]))
            for origin in candidates:
                if origin not in seen:
                    seen.add(origin);yield origin,(px,py)


def pack_scenery(inputs, truth, inventory, route_pixels, *, fixed=(), existing=(),
                 replaced_stamps=(), radius=8, halo=9):
    """Produce deterministic, exclusive whole-object relocations or conflicts.

    No fallback cuts an object, opens ocean or moves a cave icon. Unplaced
    scenery is returned explicitly and makes source preparation incomplete.
    """
    if type(radius) is not int or radius<0 or type(halo) is not int or halo<0:
        raise ValueError('Scenery radius and camera halo must be non-negative integers')
    pixels=frozenset(tuple(p) for p in route_pixels);route_water=rasterize(pixels)
    occupied=_Occupied(existing)
    result=[];seen=set();replaced=set(replaced_stamps)
    by_key={s['key']:s for s in inventory['stamps']}
    for row in fixed:
        if row['stamp'] not in by_key or row['stamp'] in seen or row['stamp'] in replaced:
            raise ValueError('Fixed scenery duplicates or invents a native stamp')
        occupied.add(row);result.append(deepcopy(row));seen.add(row['stamp'])
    if not replaced<=by_key.keys():raise ValueError('Unknown replaced Dive stamp')
    pending=[s for s in inventory['stamps'] if s['key'] not in seen|replaced]
    if any(s['kind']=='portal-scenery' for s in pending):
        raise ValueError('Every cave needs its fixed icon reservation before scenery packing')
    # Large, irreplaceable land/grass reserves get first choice. Pure decorative
    # actors are small and can occupy gaps. Sorting is stable across machines.
    pending.sort(key=lambda s:(not s['has_dry_terrain'],
                               -(s['source_rect'][2]+2*halo)*(s['source_rect'][3]+2*halo),s['key']))
    anchors=inputs.anchors();conflicts=[];counts=defaultdict(int)
    for stamp in pending:
        anchor=anchors.get(stamp['parent_map'])
        if anchor is None:raise ValueError(('Missing fixed logical scenery region',stamp['parent_map']))
        w,h=stamp['source_rect'][2:];native_water=_cells(stamp['native_water_runs'])
        dry={(x,y) for y in range(h) for x in range(w)}-native_water
        protected=dry or {tuple(p) for p in stamp['core_cells']}
        accepted=None
        for (left,top),nearby in _candidate_origins(stamp,pixels,anchor['atlas'],radius):
            rect=(left-halo,top-halo,left+w+halo,top+h+halo)
            if occupied.overlaps(rect):counts['overlap']+=1;continue
            if any((left+x,top+y) in route_water for x,y in protected):
                counts['corridor_obstruction']+=1;continue
            # Generic scenery stays in actual sea pixels; native continent and
            # cave icons are reserved separately and never overwritten here.
            art={( (left+x)//8, (top+y)//8) for y in range(h) for x in range(w)}
            if any(not (0<=x<ATLAS_WIDTH and 0<=y<ATLAS_HEIGHT)
                   or truth.indices[y*ATLAS_WIDTH+x] not in (OCEAN_INDEX,ROUTE_INDEX) for x,y in art):
                counts['non_ocean_art']+=1;continue
            wet={(left+x,top+y) for x,y in (native_water or protected)}
            if not any(p in route_water or any((p[0]+dx,p[1]+dy) in route_water
                       for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))) for p in wet):
                counts['isolated_native_water']+=1;continue
            global_anchor=[left+stamp['anchor_offset'][0],top+stamp['anchor_offset'][1]]
            row=placement(stamp,global_anchor,name=f'JourneyAtlasScenery{len(result):03}',halo=halo)
            row=bind_native_water(row,stamp,route_water)
            if row['route_water_obstructed']:
                raise AssertionError('Candidate predicate allowed dry terrain inside travel corridor')
            row['evidence']['authored_decoration_region']=dict(fixed_logical_map_anchor=anchor,
                nearby_route_pixel=list(nearby),maximum_manhattan_radius_pixels=radius,
                original_player_gps_used=False)
            accepted=row;break
        if accepted is None:
            conflicts.append(dict(stamp=stamp['key'],source_map=stamp['parent_map'],
                                  fixed_logical_anchor=anchor['atlas'],radius=radius,
                                  complete_native_shape=[w,h],reason='no safe whole placement beside existing route'))
        else:
            occupied.add(accepted);result.append(accepted);seen.add(stamp['key'])
    inputs.assert_unchanged()
    return dict(schema='atlas-whole-scenery-placement/v1',reservations=result,
                placed_native_stamps=len(result),replaced_native_dive_stamps=sorted(replaced),
                unplaced_stamps=conflicts,complete=not conflicts,
                rejected_candidate_counts=dict(counts),art_changed=False,
                original_player_gps_used=False,source_routing_proven=False,native_validated=False)


def pack_grouped_scenery(inputs, truth, inventory, route_pixels, *, fixed=(), existing=(),
                         replaced_stamps=(), radius=8, halo=9):
    """Share camera margins only among whole objects of the same native owner.

    A group's graphics bank AND ecology owner must match. Numeric NPC local
    identities may not collide. All native core rectangles remain disjoint;
    the enclosing map is a signed-coordinate-safe rectangle with an authentic
    native water mask. Fixed caves/coasts/Dive keep their own reservations.
    """
    if type(radius) is not int or radius<0 or type(halo) is not int or halo<0:
        raise ValueError('Scenery radius and camera halo must be non-negative integers')
    pixels=frozenset(tuple(p) for p in route_pixels);route_water=rasterize(pixels)
    occupied=_Occupied(list(existing)+list(fixed))
    blocked=list(occupied.rows)
    groups=[];replaced=set(replaced_stamps);by_key={s['key']:s for s in inventory['stamps']}
    seen={r['stamp'] for r in fixed}
    if len(seen)!=len(fixed) or not (seen|replaced)<=by_key.keys() or seen&replaced:
        raise ValueError('Fixed/replaced scenery duplicates or invents a native stamp')
    pending=[s for s in inventory['stamps'] if s['key'] not in seen|replaced]
    if any(s['kind']=='portal-scenery' for s in pending):
        raise ValueError('Every cave needs its fixed icon reservation before scenery packing')
    pending.sort(key=lambda s:(not s['has_dry_terrain'],
                               -(s['source_rect'][2]+2*halo)*(s['source_rect'][3]+2*halo),s['key']))
    anchors=inputs.anchors();conflicts=[];counts=defaultdict(int)
    def overlaps(a,b):
        return max(a[0],b[0])<min(a[2],b[2]) and max(a[1],b[1])<min(a[3],b[3])
    for stamp in pending:
        anchor=anchors.get(stamp['parent_map'])
        if anchor is None:raise ValueError(('Missing fixed logical scenery region',stamp['parent_map']))
        w,h=stamp['source_rect'][2:];native_water=_cells(stamp['native_water_runs'])
        dry={(x,y) for y in range(h) for x in range(w)}-native_water
        protected=dry or {tuple(p) for p in stamp['core_cells']}
        local_ids={e.get('source_local_id',e['source_index']+1) for e in stamp['events']
                   if e['field']=='object_events'}
        accepted=None
        for (left,top),nearby in _candidate_origins(stamp,pixels,anchor['atlas'],radius):
            rect=(left-halo,top-halo,left+w+halo,top+h+halo)
            if any(overlaps(rect,r) for r in blocked):counts['fixed_feature_overlap']+=1;continue
            if any((left+x,top+y) in route_water for x,y in protected):
                counts['corridor_obstruction']+=1;continue
            art={((left+x)//8,(top+y)//8) for y in range(h) for x in range(w)}
            if any(not (0<=x<ATLAS_WIDTH and 0<=y<ATLAS_HEIGHT)
                   or truth.indices[y*ATLAS_WIDTH+x] not in (OCEAN_INDEX,ROUTE_INDEX) for x,y in art):
                counts['non_ocean_art']+=1;continue
            # A complete blocked reef has no traversable water in its own
            # bounding rectangle. Its perimeter may border the channel; it
            # does not need an invented wet cell inside the rock itself.
            wet={(left+x,top+y) for x,y in (native_water or protected)}
            if not any(p in route_water or any((p[0]+dx,p[1]+dy) in route_water
                       for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))) for p in wet):
                counts['isolated_native_water']+=1;continue
            touching=[i for i,g in enumerate(groups) if overlaps(rect,g['rect'])]
            if any(groups[i]['owner']!=stamp['parent_map'] or groups[i]['bank']!=stamp['bank_signature']
                   or groups[i]['local_ids']&local_ids for i in touching):
                counts['foreign_owner_or_local_id_overlap']+=1;continue
            members=[m for i in touching for m in groups[i]['members']]
            # Preserve a separating water row, as in the extracted connected
            # components. Core rectangles include all native fringe pixels.
            expanded=(left-1,top-1,left+w+1,top+h+1)
            if any(overlaps(expanded,m['core']) for m in members):
                counts['whole_core_overlap']+=1;continue
            rects=[rect]+[groups[i]['rect'] for i in touching]
            merged=(min(r[0] for r in rects),min(r[1] for r in rects),
                    max(r[2] for r in rects),max(r[3] for r in rects))
            if merged[2]-merged[0]>127 or merged[3]-merged[1]>127:
                counts['signed_native_extent']+=1;continue
            if (merged[2]-merged[0]+15)*(merged[3]-merged[1]+14)>10240:
                counts['native_map_backup_buffer']+=1;continue
            if any(overlaps(merged,r) for r in blocked) or any(
                overlaps(merged,g['rect']) for i,g in enumerate(groups) if i not in touching):
                counts['merged_corner_overlap']+=1;continue
            combined_ids=set(local_ids)
            duplicate=False
            for i in touching:
                if combined_ids&groups[i]['local_ids']:duplicate=True;break
                combined_ids|=groups[i]['local_ids']
            if duplicate:
                counts['numeric_object_identity_collision']+=1;continue
            if len(combined_ids)>64:
                counts['native_object_template_capacity']+=1;continue
            accepted=(left,top,nearby,touching,members,merged,combined_ids);break
        if accepted is None:
            conflicts.append(dict(stamp=stamp['key'],source_map=stamp['parent_map'],
                                  fixed_logical_anchor=anchor['atlas'],radius=radius,
                                  complete_native_shape=[w,h],reason='no safe grouped whole placement beside existing route'))
            continue
        left,top,nearby,touching,members,merged,combined_ids=accepted
        row=placement(stamp,[left+stamp['anchor_offset'][0],top+stamp['anchor_offset'][1]],
                      name='PendingGroupedMap',halo=halo)
        row['evidence']['authored_decoration_region']=dict(fixed_logical_map_anchor=anchor,
            nearby_route_pixel=list(nearby),maximum_manhattan_radius_pixels=radius,
            original_player_gps_used=False)
        members.append(dict(stamp=stamp,placement=row,core=(left,top,left+w,top+h)))
        groups=[g for i,g in enumerate(groups) if i not in touching]
        groups.append(dict(rect=merged,owner=stamp['parent_map'],bank=stamp['bank_signature'],
                           local_ids=combined_ids,members=members))
    reservations=list(deepcopy(fixed));placements=list(deepcopy(fixed))
    for index,group in enumerate(sorted(groups,key=lambda g:(g['rect'][1],g['rect'][0],g['owner']))):
        x,y,r,b=group['rect'];name=f'JourneyAtlasScene{index:03}'
        cells={p for p in route_water if x<=p[0]<r and y<=p[1]<b}
        evidence=[]
        for member in group['members']:
            stamp=member['stamp'];a,d,c,e=member['core']
            cells.difference_update((xx,yy) for yy in range(d,e) for xx in range(a,c))
            cells.update((a+xx,d+yy) for xx,yy in _cells(stamp['native_water_runs']))
            row=member['placement'];row.update(name=name,origin=[x,y],width=r-x,height=b-y,
                stamp_offset=[a-x,d-y],shared_reservation=True,component_global_rect=[a,d,c-a,e-d])
            evidence.append(deepcopy(row['evidence']));placements.append(row)
        reservations.append(dict(name=name,origin=[x,y],width=r-x,height=b-y,kind='stamp',
            donor=group['owner'],ecology_owner=group['owner'],bank_signature=group['bank'],
            reserved_water_policy='native',water_runs=_runs((px-x,py-y) for px,py in cells),
            native_water_evidence=dict(whole_components=evidence,camera_halo_water_is_atlas_only=True),
            evidence=dict(whole_components=evidence,shared_native_owner=group['owner'],camera_halo=halo),
            member_stamps=[m['stamp']['key'] for m in group['members']],reserved_terrain=True))
    inputs.assert_unchanged()
    return dict(schema='atlas-grouped-whole-scenery-placement/v1',reservations=reservations,
                placements=placements,placed_native_stamps=len(placements),
                grouped_decorative_maps=len(groups),replaced_native_dive_stamps=sorted(replaced),
                unplaced_stamps=conflicts,complete=not conflicts,rejected_candidate_counts=dict(counts),
                art_changed=False,original_player_gps_used=False,source_routing_proven=False,native_validated=False)


def preserve_native_water_collars(inputs,inventory,plan):
    """Keep the actual native water fringe around a complete object.

    Copying only the object's bounding rectangle can strand its wet corners in
    tiny artificial pools. Fixed cave islands need three native water tiles
    to meet the pixel's real six-tile channel across its margin. Other scenery
    keeps one tile. Each added cell has an exact adjacent native
    source word and a collision-zero Surf witness; no invented ocean path is
    permitted. Nine camera tiles already reserve this fringe's physical owner.
    """
    result=deepcopy(plan);stamps={s['key']:s for s in inventory['stamps']}
    maps={r['name']:r for r in result['reservations']};witnesses=[]
    words_by_map=defaultdict(dict)
    for row in result['placements']:
        stamp=stamps[row['stamp']];name=stamp['parent_map'];layout=inputs.layout(name)
        left,top,w,h=stamp['source_rect'];sx,sy=row['stamp_offset']
        radius=3 if row['kind']=='cave' else 1
        proof=[]
        for yy in range(-radius,h+radius):
            for xx in range(-radius,w+radius):
                if 0<=xx<w and 0<=yy<h:continue
                px,py=left+xx,top+yy
                if not (0<=px<layout['width'] and 0<=py<layout['height']):continue
                if not inputs.water(name,px,py):continue
                x,y=sx+xx,sy+yy
                if not (0<=x<row['width'] and 0<=y<row['height']):
                    raise ValueError('Whole native water fringe escaped its camera reservation')
                if not (0<=row['origin'][0]+x<ATLAS_WIDTH*8
                        and 0<=row['origin'][1]+y<ATLAS_HEIGHT*8):
                    continue
                word=inputs.word(name,px,py);key=x,y
                previous=words_by_map[row['name']].get(key,word)
                if previous!=word:raise ValueError('Shared native water collars disagree on a full metatile word')
                words_by_map[row['name']][key]=word
                proof.append(dict(source_tile=[px,py],target_tile=[x,y],word=word))
        witnesses.append(dict(stamp=stamp['key'],target_map=row['name'],native_map=name,radius=radius,cells=proof))
    for name,words in words_by_map.items():
        row=maps[name]
        if row.get('reserved_water_policy')!='native':
            raise ValueError('Native water collar requires an authoritative whole-object water mask')
        cells=_cells(row['water_runs']);cells.update(words)
        row['water_runs']=_runs(cells)
        row.setdefault('native_water_evidence',{})['authenticated_native_fringe']=[w for w in witnesses if w['target_map']==name]
        row['native_water_word_overrides']=[dict(tile=list(tile),word=word) for tile,word in sorted(words.items(),key=lambda p:(p[0][1],p[0][0]))]
        # The original obstruction census predates the native fringe. Terrain
        # remains authoritative and the integration recalculates its final SCC.
    result['native_water_collar_witnesses']=witnesses
    result['native_water_collar_cells']=sum(len(w) for w in words_by_map.values())
    inputs.assert_unchanged()
    return result


def stage_native_water_collars(layer,plan):
    """Apply the authenticated full words after geometry and whole cores."""
    import json,struct
    from badge_story_layer import read
    layouts={r['id']:r for r in json.loads(read(layer,'data/layouts/layouts.json'))['layouts']}
    counts={}
    for row in plan['reservations']:
        overrides=row.get('native_water_word_overrides',[])
        if not overrides:continue
        mapping=json.loads(read(layer,f'data/maps/{row["name"]}/map.json'))
        layout=layouts[mapping['layout']];path=layout['blockdata_filepath'];raw=read(layer,path)
        words=list(struct.unpack('<'+'H'*(len(raw)//2),raw))
        for cell in overrides:
            x,y=cell['tile'];word=cell['word']
            if not (0<=x<layout['width'] and 0<=y<layout['height']) or word&0xc00:
                raise ValueError('Invalid authenticated native water fringe cell')
            words[y*layout['width']+x]=word
        layer.stage(path,struct.pack('<'+'H'*len(words),*words));counts[row['name']]=len(overrides)
    return dict(kind='whole-native-water-fringe',maps=len(counts),cells=sum(counts.values()),native_validated=False)
