"""Partition one affine ocean around exclusive whole-scenery reservations.

Reservations describe their complete native footprint. Ordinary rectangles
are cut around them; scenery is never cropped to fit a 32-tile storage grid.
This plans ownership only. Terrain/event/native audits still certify the result.
"""
from collections import defaultdict
from copy import deepcopy
import re

from atlas_surf_geometry import rasterize, _runs


KINDS = {'stamp','cave','adapter','dive','port'}


def _rectangle(row):
    x,y=row['origin'];w,h=row['width'],row['height']
    if any(type(v) is not int for v in (x,y,w,h)) or not 1<=w<=127 or not 1<=h<=127:
        raise ValueError(('Reservation must fit native signed coordinates',row))
    if (w+15)*(h+14)>10240:
        raise ValueError('Whole reservation exceeds the native map backup buffer')
    if not -32768<=x<=32767-w or not -32768<=y<=32767-h:
        raise ValueError('Reservation exceeds signed physical world coordinates')
    if row.get('kind') not in KINDS or not row.get('evidence'):
        raise ValueError('Whole reservation needs a known kind and explicit source evidence')
    return x,y,x+w,y+h


def _inside(point, rectangle):
    x,y=point;a,b,c,d=rectangle
    return a<=x<c and b<=y<d


def _free_rectangles(left,top,size,rectangles):
    """Sweep row intervals; merge only identical free intervals vertically."""
    active={};result=[]
    for y in range(top,top+size):
        blocked=set()
        for a,b,c,d in rectangles:
            if b<=y<d:blocked.update(range(max(left,a),min(left+size,c)))
        intervals=[];start=None
        for x in range(left,left+size+1):
            free=x<left+size and x not in blocked
            if free and start is None:start=x
            if not free and start is not None:intervals.append((start,x));start=None
        next_active={}
        for interval in intervals:
            row=active.pop(interval,None)
            next_active[interval]=row if row is not None else [interval[0],y,interval[1],y]
            next_active[interval][3]=y+1
        result.extend(active.values());active=next_active
    return result+list(active.values())


def plan_reserved_geometry(pixels, reservations=(), *, native_regions=(),chunk_tiles=32, prefix='JourneyAtlasSea'):
    if type(chunk_tiles) is not int or chunk_tiles<8 or chunk_tiles>127 or chunk_tiles%8:
        raise ValueError('Ordinary storage rectangles must divide atlas pixels and fit s8')
    pixels=frozenset(tuple(p) for p in pixels)
    route_water=rasterize(pixels)
    reservations=[deepcopy(r) for r in reservations]
    rectangles=[_rectangle(r) for r in reservations]
    native_regions=deepcopy(list(native_regions));native_rectangles=[]
    for row in native_regions:
        if not row.get('native_map') or not row.get('evidence'):
            raise ValueError('Native exclusion needs a real registered map and source evidence')
        local=row.get('local_rect',[]);origin=row.get('origin',[]);rect=row.get('global_rect',[])
        if (len(local)!=4 or len(origin)!=2 or len(rect)!=4
                or any(type(v) is not int for v in local+origin+rect)
                or not 0<=local[0]<local[2] or not 0<=local[1]<local[3]
                or rect!=[origin[0]+local[0],origin[1]+local[1],origin[0]+local[2],origin[1]+local[3]]):
            raise ValueError('Native exclusion differs from its authenticated local registration')
        native_rectangles.append(tuple(rect))
    for i,a in enumerate(native_rectangles):
        for b in native_rectangles[i+1:]:
            if max(a[0],b[0])<min(a[2],b[2]) and max(a[1],b[1])<min(a[3],b[3]):
                raise ValueError('Registered native terrain owners overlap')
    for i,a in enumerate(rectangles):
        for b in rectangles[i+1:]:
            if max(a[0],b[0])<min(a[2],b[2]) and max(a[1],b[1])<min(a[3],b[3]):
                raise ValueError('Whole native reservations overlap; relocate or authenticate a merged object')
    for a in rectangles:
        for b in native_rectangles:
            if max(a[0],b[0])<min(a[2],b[2]) and max(a[1],b[1])<min(a[3],b[3]):
                raise ValueError('Whole generated reservation overlaps registered native terrain')
    all_rectangles=rectangles+native_rectangles
    native_route_cells={p for p in route_water if any(_inside(p,r) for r in native_rectangles)}
    ownership={};chunks=[];extra_water=set();native_obstructions=set()
    for i,(row,rect) in enumerate(zip(reservations,rectangles)):
        route_cells={p for p in route_water if _inside(p,rect)}
        cells=set(route_cells)
        additional=set()
        policy=row.get('reserved_water_policy','route')
        if policy not in ('route','native'):
            raise ValueError('Unknown reserved terrain water policy')
        runs=row.get('water_runs',[]) if policy=='native' else row.get('additional_water_runs',[])
        for y,start,end in runs:
            if any(type(v) is not int for v in (y,start,end)) or not 0<=y<row['height'] or not 0<=start<end<=row['width']:
                raise ValueError('Reserved native water is outside the complete footprint')
            additional.update((rect[0]+x,rect[1]+y) for x in range(start,end))
        if (policy=='native' or additional-route_water) and not row.get('native_water_evidence'):
            raise ValueError('Water outside route ink needs authenticated native footprint evidence')
        if policy=='native':
            missing=route_cells-additional
            if missing and not row.get('route_obstruction_evidence'):
                raise ValueError('Native scenery obstructs the six-tile route; move the whole stamp or authenticate its endpoint')
            native_obstructions|=missing
            cells=additional
        else:cells|=additional
        extra_water|=additional-route_water
        chunk={k:deepcopy(v) for k,v in row.items() if k not in ('additional_water_runs',)}
        chunk.update(reservation_index=i,reserved_terrain=True,water_runs=_runs(cells,tuple(row['origin'])))
        chunks.append(chunk)
        for p in cells:ownership[p]=chunk
    buckets=defaultdict(set)
    for p in route_water:
        if not any(_inside(p,r) for r in all_rectangles):
            buckets[p[0]//chunk_tiles,p[1]//chunk_tiles].add(p)
    # Only storage buckets containing route ink need ordinary maps. Explicit
    # reservations remain complete even when all their terrain is dry.
    for (cx,cy),cells in sorted(buckets.items(),key=lambda item:(item[0][1],item[0][0])):
        left,top=cx*chunk_tiles,cy*chunk_tiles
        nearby=[r for r in all_rectangles if max(left,r[0])<min(left+chunk_tiles,r[2])
                and max(top,r[1])<min(top+chunk_tiles,r[3])]
        for a,b,c,d in _free_rectangles(left,top,chunk_tiles,nearby):
            selected={p for p in cells if a<=p[0]<c and b<=p[1]<d}
            if not selected:continue
            x0=max(a,min(p[0] for p in selected)-1);y0=max(b,min(p[1] for p in selected)-1)
            x1=min(c,max(p[0] for p in selected)+2);y1=min(d,max(p[1] for p in selected)+2)
            chunk=dict(origin=[x0,y0],width=x1-x0,height=y1-y0,kind='ordinary',
                       water_runs=_runs(selected,(x0,y0)),reserved_terrain=False)
            chunks.append(chunk)
            for p in selected:
                if p in ownership:raise AssertionError('Duplicate ownership after reservation sweep')
                ownership[p]=chunk
    if set(ownership)!=((route_water-native_obstructions-native_route_cells)|extra_water):
        raise AssertionError('Reservation partition omitted physical route water')
    chunks.sort(key=lambda c:(c['origin'][1],c['origin'][0],c.get('name','')))
    names=set()
    for number,chunk in enumerate(chunks):
        name=chunk.get('name',f'{prefix}{number:03}')
        if name in names or not re.fullmatch('[A-Za-z][A-Za-z0-9_]*',name):
            raise ValueError('Duplicate or unsafe reserved map identity')
        names.add(name)
        chunk.update(name=name,id='MAP_'+name.upper(),group=f'JourneyAtlasSeas{number//100}',
                     number=number%100,connections=[])
    pairs=set()
    for (x,y),source in ownership.items():
        for dx,dy,direction,reverse in [(1,0,'right','left'),(0,1,'down','up')]:
            target=ownership.get((x+dx,y+dy))
            if target is None or target is source:continue
            if dx:
                adjacent=source['origin'][0]+source['width']==target['origin'][0]
                axis=1
            else:
                adjacent=source['origin'][1]+source['height']==target['origin'][1]
                axis=0
            if not adjacent:raise AssertionError('Water owners do not share their actual rectangle face')
            key=source['name'],target['name'],direction
            if key in pairs:continue
            pairs.add(key)
            offset=target['origin'][axis]-source['origin'][axis]
            source['connections'].append(dict(direction=direction,map=target['id'],offset=offset))
            target['connections'].append(dict(direction=reverse,map=source['id'],offset=-offset))
    for chunk in chunks:chunk['connections'].sort(key=lambda c:(c['direction'],c['map'],c['offset']))
    # A reserved beach or cave may meet water as dry terrain. Keep the true
    # rectangle adjacency; the native word/height audit decides traversability.
    for i,a in enumerate(chunks):
        ax,ay=a['origin'];ar,ab=ax+a['width'],ay+a['height']
        for b in chunks[i+1:]:
            if not (a['reserved_terrain'] or b['reserved_terrain']):continue
            bx,by=b['origin'];br,bb=bx+b['width'],by+b['height']
            contact=None
            if max(ay,by)<min(ab,bb):
                if ar==bx:contact=('right','left',by-ay)
                elif br==ax:contact=('left','right',by-ay)
            if max(ax,bx)<min(ar,br):
                if ab==by:contact=('down','up',bx-ax)
                elif bb==ay:contact=('up','down',bx-ax)
            if contact is not None:
                direction,reverse,offset=contact
                first=dict(direction=direction,map=b['id'],offset=offset)
                second=dict(direction=reverse,map=a['id'],offset=-offset)
                if first not in a['connections']:a['connections'].append(first)
                if second not in b['connections']:b['connections'].append(second)
    for chunk in chunks:chunk['connections'].sort(key=lambda c:(c['direction'],c['map'],c['offset']))
    return dict(schema='atlas-surf-reserved-geometry/v1',scale=8,corridor_width=6,chunk_tiles=chunk_tiles,
                maps_per_group=100,chunks=chunks,map_count=len(chunks),group_count=(len(chunks)+99)//100,
                route_pixels=[list(p) for p in sorted(pixels,key=lambda p:(p[1],p[0]))],
                water_tiles=len(ownership),ordinary_route_water_tiles=len(route_water),
                route_water_replaced_by_authenticated_native_terrain=len(native_obstructions),
                reserved_additional_water_tiles=len(extra_water),whole_reservations=len(reservations),
                native_regions=native_regions,
                route_raster_cells_owned_by_registered_native_terrain=len(native_route_cells),
                affine_projection='floor((origin_global_tile + local_tile) / 8)',
                source_certified=False,native_certified=False,art_changed=False,per_cell_gps_arrays=False)
