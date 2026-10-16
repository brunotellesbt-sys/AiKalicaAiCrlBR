"""Build the six yellow atlas requests as real open-water connections."""
import argparse,copy,json,re,struct
from pathlib import Path
import numpy as np
from PIL import Image
from candidate_layer import Layer
from prepare_continuous_ocean import PRIOR,LAYER as PREVIOUS
from prepare_complete_marine_atlas import point_line
from prepare_world_dex_map import decode,encode
from sevii_navigation_grid import reconcile
from world_grid_updates import rebuild

LAYER='annotated-world-links';PRIOR=PRIOR+[PREVIOUS]
OPPOSITE=dict(left='right',right='left',up='down',down='up')
REQUESTS=[
 dict(map='JourneyLavenderOneSea',name='LAVENDER-ONE SEA',center=[116,39],size=[128,24],
      paths=[[[97,39],[134,39]]],axis='x',
      definition='Ligação direta de Surf entre Lavender Port e o porto de One Island.',
      links=[('JourneyRoute12Shipyard','left',-36),('OneIsland_Harbor_Frlg','right',0)]),
 dict(map='JourneyOneTwoPassage',name='ONE-TWO PASSAGE',center=[161,43],size=[64,40],
      paths=[[[157,43],[166,43]]],axis='x',
      definition='Canal de navegação entre o mar de One Island e o porto de Two Island.',
      links=[('JourneyWorldSea01','down',-41),('TwoIsland_Harbor_Frlg','right',12)]),
 dict(map='JourneyTwoThreeMouth',name='TWO-THREE SEA MOUTH',center=[181,52],size=[64,24],
      paths=[[[181,50],[181,53],[180,53]]],axis='y',
      definition='Abertura do canal Two-Three para o mar de Two Island e o acesso de Lavender.',
      links=[('JourneyTwoThreePassage','up',0),('JourneyWorldSea02','down',-24),('JourneyLavenderApproachSouth','left',-41)]),
 dict(map='JourneySootopolisSouthChannel',name='SOOTOPOLIS SOUTH CHANNEL',center=[114,95],size=[24,40],
      paths=[[[114,91],[114,99]]],axis='y',theme='emerald',
      definition='Passagem marítima direta da Rota 126 para a Rota 130, ao sul de Sootopolis.',
      links=[('Route126','up',-28),('Route130','down',-28)]),
 dict(map='JourneySouthwestSeviiPassage',name='SOUTHWEST SEVII PASSAGE',center=[162,105],size=[64,24],
      paths=[[[159,105],[164,105]]],axis='x',
      definition='Passagem do mar sudoeste de Sevii até a costa oeste de Tanoby Ruins.',
      links=[('JourneyWorldSea06','up',16),('SevenIsland_TanobyRuins_Frlg','right',0)]),
]


def path_pixels(points):
    pixels=[]
    for a,b in zip(points,points[1:]):
        assert a[0]==b[0] or a[1]==b[1]
        dx=(b[0]>a[0])-(b[0]<a[0]);dy=(b[1]>a[1])-(b[1]<a[1])
        pixels.extend((a[0]+dx*i,a[1]+dy*i) for i in range(abs(a[0]-b[0])+abs(a[1]-b[1])+1))
    return pixels


def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if old:=layer.existing():return old
    s=layer.source
    maps={p.parent.name:json.loads(p.read_text()) for p in (s/'data/maps').glob('*/map.json')};before=copy.deepcopy(maps)
    ld=json.loads((s/'data/layouts/layouts.json').read_text());layouts={l['id']:l for l in ld['layouts']}
    groups=json.loads((s/'data/maps/map_groups.json').read_text());group=next(g for g in groups['group_order'] if 'JourneyWorldSea01' in groups[g])
    chart=copy.deepcopy(json.loads((s/'.journey-continuous-ocean').read_text())['chart']);old_projections=copy.deepcopy(chart['projections'])
    scripts=(s/'data/event_scripts.s').read_text();changed={};openings=[]
    def remove(a,b):
        assert any(c['map']==maps[b]['id'] for c in maps[a]['connections']),(a,b)
        for n,other in [(a,b),(b,a)]:maps[n]['connections']=[c for c in maps[n]['connections'] if c['map']!=maps[other]['id']]
    # The new northern junction replaces the old long shortcut. Its western
    # approach has enough actual ocean tiles to cross the distance on MAP.
    old_link=next(r for r in chart['routes'] if {r['source'],r['destination']}=={'JourneyKantoEasternChannel','JourneyWorldSea01'})
    transit_path=copy.deepcopy(old_link['polyline'])
    origin=next(n['position'] for n in chart['nodes'] if n['map']=='JourneyKantoEasternChannel')
    if sum(abs(a-b) for a,b in zip(transit_path[0],origin))>sum(abs(a-b) for a,b in zip(transit_path[-1],origin)):transit_path.reverse()
    if transit_path[-1]!=[157,43]:
        if transit_path[-1][0]!=157:transit_path.append([157,transit_path[-1][1]])
        transit_path.append([157,43])
    extra=[
        dict(map='JourneyKantoSeviiJunction',name='KANTO-SEVII JUNCTION',center=transit_path[0],size=[23,16],paths=[[transit_path[0],transit_path[0]]],axis='x',
             definition='Junção aberta entre o canal leste de Kanto e a travessia para Sevii.',links=[('JourneyKantoEasternChannel','up',0)]),
        dict(map='JourneyKantoSeviiTransit',name='KANTO-SEVII OPEN SEA',center=transit_path[len(transit_path)//2],size=[112,24],paths=[transit_path],axis='x',
             definition='Travessia contínua do litoral leste de Kanto até os canais de One e Two Island.',links=[('JourneyKantoSeviiJunction','left',0),('JourneyOneTwoPassage','right',0)]),
    ]
    passages=copy.deepcopy(REQUESTS)+extra
    for a,b in [('OneIsland_Harbor_Frlg','JourneyKantoCoastalBand'),('JourneyKantoEasternChannel','JourneyWorldSea01'),('JourneyLavenderApproachSouth','JourneyWorldSea02')]:remove(a,b)
    # The original eastern channel compresses the northern junction and
    # One Island into a few steps. Lengthen this real ocean approach so MAP
    # can track the new eastern passage without jumping at a shared corner.
    channel='JourneyKantoEasternChannel';l=layouts[maps[channel]['layout']]
    assert l['height']==20
    raw=(s/l['blockdata_filepath']).read_bytes()
    changed[channel]=list(struct.unpack('<'+'H'*(l['width']*l['height']),raw))+[0x112B]*(8*l['width'])
    l['height']=28
    next(p for p in chart['projections'] if p['map']==channel)['height']=28
    for p in passages:
        n=p['map'];assert n not in maps
        template_name='Route126' if p.get('theme')=='emerald' else 'JourneyWorldSea01'
        m=copy.deepcopy(maps[template_name]);m.update(id='MAP_'+n.upper(),name=n,layout='LAYOUT_'+n.upper(),map_type='MAP_TYPE_OCEAN_ROUTE',music='MUS_SURF',connections=[],object_events=[],warp_events=[],coord_events=[],bg_events=[],show_map_name=True)
        maps[n]=m
        l=copy.deepcopy(layouts[maps[template_name]['layout']]);w,h=p['size']
        l.update(id=m['layout'],name=n+'_Layout',width=w,height=h,blockdata_filepath=f'data/layouts/{n}/map.bin',border_filepath=f'data/layouts/{n}/border.bin')
        layouts[l['id']]=l;ld['layouts'].append(l);groups[group].append(n)
        layer.stage(f'data/maps/{n}/scripts.inc',n+'_MapScripts::\n\t.byte 0\n');scripts+=f'\n\t.include "data/maps/{n}/scripts.inc"\n'
        chart['projections'].append(dict(map=n,id=m['id'],width=w,height=h,center=p['center'],first=0,count=w*h))
    assert len(groups[group])<256
    for p in passages:
        n=p['map']
        for other,d,off in p['links']:
            maps[n]['connections'].append(dict(map=maps[other]['id'],direction=d,offset=off))
            maps[other]['connections']=(maps[other].get('connections') or [])+[dict(map=maps[n]['id'],direction=OPPOSITE[d],offset=-off)]
    # Reject overlapping destinations: a visible mouth must have one real,
    # reciprocal destination, not an order-dependent hidden fork.
    byid={m['id']:n for n,m in maps.items()}
    touched={p['map'] for p in passages}|{n for n in maps if before.get(n)!=maps[n]}
    def spans(n):
        l=layouts[maps[n]['layout']];result={d:{} for d in OPPOSITE}
        for c in maps[n].get('connections') or []:
            d=c['direction'];other=byid.get(c['map'])
            if d not in result or other not in maps:continue
            q=layouts[maps[other]['layout']];limit=l['height'] if d in ['left','right'] else l['width'];length=q['height'] if d in ['left','right'] else q['width']
            for t in range(max(0,c['offset']),min(limit,c['offset']+length)):
                assert t not in result[d],('Overlapping sea mouths',n,d,t,result[d].get(t),other)
                result[d][t]=other
        return result
    # Original coastal-band overlaps are pre-existing; new maps and changed
    # mouths themselves must never add another overlapping destination.
    for p in passages:spans(p['map'])
    def terrain(n):
        if n not in changed:
            l=layouts[maps[n]['layout']];path=s/l['blockdata_filepath']
            changed[n]=list(struct.unpack('<'+'H'*(l['width']*l['height']),path.read_bytes())) if path.exists() else [0x1170 if l['layout_version']=='emerald' else 0x112B]*(l['width']*l['height'])
        return changed[n]
    def clear_edge(n,d,off,length):
        l=layouts[maps[n]['layout']];w,h=l['width'],l['height'];v=terrain(n);water=0x1170 if l['layout_version']=='emerald' else 0x112B;cells=[]
        limit=h if d in ['left','right'] else w
        for t in range(max(0,off),min(limit,off+length)):
            for depth in (0,1):
                x,y=(depth if d=='left' else w-1-depth,t) if d in ['left','right'] else (t,depth if d=='up' else h-1-depth)
                i=y*w+x
                if v[i]>>12<=1:
                    if v[i]!=water:cells.append([x,y,v[i]])
                    v[i]=water
        openings.append(dict(map=n,direction=d,span=[off,length],changed_cells=cells))
    for p in passages:
        n=p['map'];terrain(n)
        for other,d,off in p['links']:
            l=layouts[maps[n]['layout']];q=layouts[maps[other]['layout']]
            clear_edge(other,OPPOSITE[d],-off,l['height'] if d in ['left','right'] else l['width'])
    # Close only unconnected outer spans. Connected passages have open water
    # across both sides; complete 2x2 rocks identify every outside limit.
    limits=[]
    for n in sorted(touched):
        l=layouts[maps[n]['layout']];w,h=l['width'],l['height'];v=terrain(n);open_spans={d:set() for d in OPPOSITE}
        for c in maps[n].get('connections') or []:
            d=c['direction'];other=byid.get(c['map'])
            if d not in open_spans or other not in maps:continue
            q=layouts[maps[other]['layout']];limit=h if d in ['left','right'] else w;length=q['height'] if d in ['left','right'] else q['width']
            open_spans[d].update(range(max(0,c['offset']),min(limit,c['offset']+length)))
        rocks=[0x1550,0x551,0x558,0x1559] if l['layout_version']=='emerald' else [0x510,0x511,0x518,0x519]
        count=0
        for y in range(h):
            for x in range(w):
                outside=(x<2 and y not in open_spans['left'] or x>=w-2 and y not in open_spans['right'] or y<2 and x not in open_spans['up'] or y>=h-2 and x not in open_spans['down'])
                if outside and v[y*w+x]>>12<=1:
                    v[y*w+x]=rocks[y%2*2+x%2];count+=1
        if n in {p['map'] for p in passages}:layer.stage(l['border_filepath'],struct.pack('<4H',*rocks))
        layer.stage(l['blockdata_filepath'],struct.pack('<'+'H'*len(v),*v));limits.append(dict(map=n,closed_outer_cells=count))
    # Native island harbor borders use a blank indoor tile. Replace that
    # black corner apron with visible, collision-blocked ocean rocks.
    layer.stage('data/layouts/Island_Harbor_Frlg/border.bin',struct.pack('<4H',0x510,0x511,0x518,0x519))
    for n,m in maps.items():
        if before.get(n)!=m:
            if n in before:assert all(m[k]==before[n][k] for k in ['object_events','warp_events','coord_events','bg_events'])
            layer.stage(f'data/maps/{n}/map.json',json.dumps(m,indent=2)+'\n')
    layer.stage('data/layouts/layouts.json',json.dumps(ld,indent=2)+'\n');layer.stage('data/maps/map_groups.json',json.dumps(groups,indent=2)+'\n');layer.stage('data/event_scripts.s',scripts)
    # The fifth yellow mark already has a working reciprocal sea connection.
    reused=dict(map='JourneyWorldSea07',name='SEVEN-TANOBY APPROACH',paths=[[[178,97],[178,100],[176,100]]],
                definition='Acesso já existente do mar de Seven Island ao mar de Tanoby.',existing_link=['JourneyWorldSea07','JourneyTanobyDawnSea'])
    assert any(c['map']==maps['JourneyTanobyDawnSea']['id'] for c in maps['JourneyWorldSea07']['connections'])
    annotations=[dict(map=p['map'],name=p['name'],paths=p['paths'],new_map=True) for p in REQUESTS]
    annotations.insert(4,dict(**reused,new_map=False))
    # The overview and zoom use the same six new orthogonal line segments.
    path='src/data/journey_world_map.h';header=(s/path).read_text();image=decode(header);original=image.copy();visible=[]
    for p in annotations:
        pixels=set()
        for points in p['paths']:
            for x,y in path_pixels(points):
                if image.getpixel((x,y)) in (1,2):image.putpixel((x,y),2);pixels.add((x,y))
        assert pixels,p['map'];visible.append(dict(map=p['map'],paths=p['paths'],blue_pixels=[list(point) for point in sorted(pixels)]))
    detail_bytes=list(map(int,re.search(r'sWorldDetailPixels\[\] = \{([^}]+)',header)[1].split(',')));detail=Image.new('P',(448,224))
    for y in range(224):
        for x in range(448):detail.putpixel((x,y),(detail_bytes[y*224+x//2]>>((x&1)*4))&15)
    for item in visible:
        for x,y in item['blue_pixels']:
            for dy in (0,1):
                for dx in (0,1):
                    q=(2*x+dx,2*y+dy)
                    if detail.getpixel(q) in (1,2):detail.putpixel(q,2)
    packed=bytes(detail.getpixel((x,y))|(detail.getpixel((x+1,y))<<4) for y in range(224) for x in range(0,448,2))
    header=re.sub(r'(sWorldDetailPixels\[\] = \{)[^}]+',lambda m:m[1]+','.join(map(str,packed)),encode(header,image))
    end=header.index('};',header.index('sWorldPoints'));header=header[:end]+''.join(point_line(maps[p['map']],p['center'],p['name']) for p in passages)+header[end:]
    layer.stage(path,header)
    nodes={n['map']:n for n in chart['nodes']}
    for p in passages:nodes[p['map']]=dict(map=p['map'],name=p['name'],position=p['center'])
    records={}
    for r in chart['routes']:
        if any(c['map']==maps[r['destination']]['id'] and c['direction']==r['direction'] and c['offset']==r['offset'] for c in maps[r['source']].get('connections') or []):records[tuple(sorted((r['source'],r['destination'])))]=r
    for p in passages:
        for c in maps[p['map']]['connections']:
            other=byid[c['map']];key=tuple(sorted((p['map'],other)))
            records[key]=dict(source=p['map'],destination=other,direction=c['direction'],offset=c['offset'],polyline=p['paths'][0],actual_connection=True,authored_passage=p['map'])
    chart.update(routes=list(records.values()),nodes=list(nodes.values()),visible_passages=chart['visible_passages']+visible)
    authored={}
    # The previous Two-Three cursor used a diagonal interpolation inside a
    # rectangular bound. Give its new southern mouth the actual elbow on the
    # drawn route, while retaining its northern and eastern destinations.
    old_passage=next(p for p in chart['passages'] if p['map']=='JourneyTwoThreePassage')
    route=list(dict.fromkeys(path_pixels(old_passage['chart_paths'][0])))
    w,h=old_passage['size'];yy,xx=np.indices((h,w))
    lower=np.full((h,w),-10000);upper=np.full((h,w),10000)
    for box,target in [((0,0,23,0),0),((w-1,0,w-1,12),len(route)-1),((0,h-1,w-1,h-1),route.index((181,50)))]:
        left,top,right,bottom=box
        distance=np.maximum(left-xx,0)+np.maximum(xx-right,0)+np.maximum(top-yy,0)+np.maximum(yy-bottom,0)
        lower=np.maximum(lower,target-2*distance);upper=np.minimum(upper,target+2*distance)
    assert np.all(lower<=upper),'Two-Three mouth coordinates are inconsistent'
    progress=np.floor((lower+upper)/2+0.5).astype(int).clip(0,len(route)-1)
    coords=np.array(route)[progress]
    authored['JourneyTwoThreePassage']=(coords[:,:,0]|(coords[:,:,1]<<8)).ravel().tolist()
    for p in passages:
        w,h=p['size'];points=path_pixels(p['paths'][0])
        if not points:points=[tuple(p['center'])]
        yy,xx=np.indices((h,w));progress=xx/max(1,w-1) if p['axis']=='x' else yy/max(1,h-1)
        indices=np.rint(progress*(len(points)-1)).astype(int);coords=np.array(points)[indices]
        authored[p['map']]=(coords[:,:,0]|(coords[:,:,1]<<8)).ravel().tolist()
        bounds=[min(x for x,y in points),min(y for x,y in points),max(x for x,y in points),max(y for x,y in points)]
        chart['passages'].append(dict(map=p['map'],name=p['name'],center=p['center'],size=p['size'],chart_paths=p['paths'],chart_bounds=bounds,definition=p['definition'],links=[list(link) for link in p['links']]))
    path='src/data/journey_world_position.h';gps_header=rebuild((s/path).read_text(),old_projections,chart['projections'],authored)
    gps_header,gps=reconcile(gps_header,chart['projections'],maps,fixed_maps=[p['map'] for p in chart['passages']])
    layer.stage(path,gps_header)
    return layer.finish(chart=chart,annotations=annotations,new_maps=[p['map'] for p in passages],openings=openings,
                        outer_limits=limits,gps=gps,new_route_names_selectable=True,original_events_and_port_placements_preserved=True,
                        rocks_only_on_unconnected_outer_spans=True,interior_seas_open=True,existing_tanoby_link_reused=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);print(json.dumps(prepare(p.parse_args().source),indent=2))
