"""Build missing Surf passages and an unlabeled, orthogonal native world chart."""
import argparse
import hashlib
import json
import re
from pathlib import Path

from PIL import Image
from candidate_layer import Layer
from world_marine_links import PASSAGES, prepare_links
from prepare_connected_sea_chart import route
from prepare_complete_marine_atlas import SURF_ROUTES, point_line
from prepare_sevii_arrival_layout import PRIOR, LAYER as PREVIOUS
from prepare_world_dex_map import decode, encode, PAT

LAYER = 'world-route-chart'
PRIOR = PRIOR + [PREVIOUS]


def prepare(source):
    layer = Layer(source, LAYER, PRIOR)
    if old := layer.existing():
        return old
    s = layer.source
    maps = {p.parent.name:json.loads(p.read_text()) for p in (s/'data/maps').glob('*/map.json')}
    geometry = json.loads((s/'.journey-pallet-harbor').read_text())
    reference = json.loads((Path(__file__).parent/'data/world-coast-reference.json').read_text())
    layouts = {l['id']:l for l in json.loads((s/'data/layouts/layouts.json').read_text())['layouts']}
    for n,r in reference['maps'].items():
        assert hashlib.sha256((s/layouts[maps[n]['layout']]['blockdata_filepath']).read_bytes()).hexdigest()==r['terrain_sha256'],n
    layouts, changed_tiles, gps = prepare_links(layer,maps,geometry,reference)
    by_id = {m['id']:n for n,m in maps.items()}
    coords = {p['map']:tuple(p['center']) for p in geometry['projections']}
    names_custom = {p['map']:p['name'] for p in PASSAGES}
    # Shared straight trunks replace the small parallel offsets at the green
    # annotations. Native towns retain their original geographic positions.
    chart_coords = dict(coords)
    for n,(x,y) in coords.items():
        if n.startswith('Journey') and n not in names_custom:
            x = 134 if x in (134,135) else 149 if x in (145,147,149) else x
            y = 86 if y in (83,84,86,89) else y
            chart_coords[n] = (x,y)
    path = 'src/data/journey_world_map.h'
    header = (s/path).read_text()
    before = decode(header)
    image = before.copy()
    for y in range(112):
        for x in range(224):
            if image.getpixel((x,y)) == 2:
                image.putpixel((x,y),1)
    # Include every existing marine route and native Surf coast. Edges come
    # directly from the final map headers, including the connected Sevii towns.
    def marine(n):
        m = maps[n]
        return m['map_type']=='MAP_TYPE_OCEAN_ROUTE' or n in SURF_ROUTES or (
            n.startswith('Journey') and m['map_type']=='MAP_TYPE_ROUTE') or (
            'Harbor' in n and bool(m.get('connections')))
    edges = {}
    for n,m in sorted(maps.items()):
        for c in m.get('connections') or []:
            other = by_id.get(c['map'])
            if c['direction'] not in ('up','down','left','right') or n not in coords or other not in coords:
                continue
            if not (marine(n) or marine(other)):
                continue
            key = tuple(sorted((n,other)))
            edges.setdefault(key,dict(source=n,destination=other,direction=c['direction'],offset=c['offset']))
    sea = {(x,y) for y in range(112) for x in range(224) if image.getpixel((x,y)) in (1,14)}
    records, cache = [], {}
    for pair,link in sorted(edges.items()):
        a,b = pair
        endpoints = tuple(sorted((chart_coords[a],chart_coords[b])))
        if endpoints not in cache:
            try:
                pixels,corners = route(image,image,*endpoints,sea)
            except ValueError:
                # Some native town inlets are enclosed at atlas resolution.
                # Their real connection still gets an orthogonal path; land
                # pixels and town icons retain their original native artwork.
                start,end = endpoints
                corners = [start,(end[0],start[1]),end]
                pixels = []
                for u,v in zip(corners,corners[1:]):
                    dx=(v[0]>u[0])-(v[0]<u[0]);dy=(v[1]>u[1])-(v[1]<u[1])
                    pixels.extend((u[0]+dx*i,u[1]+dy*i) for i in range(abs(v[0]-u[0])+abs(v[1]-u[1])+1))
            cache[endpoints] = pixels,corners
        pixels,corners = cache[endpoints]
        for xy in pixels:
            if image.getpixel(xy) in (1,2):
                image.putpixel(xy,2)
        assert all(u[0]==v[0] or u[1]==v[1] for u,v in zip(corners,corners[1:]))
        records.append(dict(**link,polyline=[list(p) for p in corners],actual_connection=True))
    # Consolidate local parallel lines in the exact areas marked in green.
    # Boundary contacts are retained, so this changes the chart, not adjacency.
    rectifications = []
    windows = [(105,58,116,61,'horizontal'),(131,56,137,63,'vertical'),
               (146,64,151,80,'vertical'),(132,78,137,85,'vertical'),
               (127,84,136,90,'horizontal'),(136,84,151,89,'horizontal'),
               (141,99,149,104,'horizontal'),(157,98,162,105,'vertical'),
               (175,76,186,83,'horizontal'),(188,92,198,99,'rectangle')]
    def ink(a,b):
        assert a[0]==b[0] or a[1]==b[1]
        dx=(b[0]>a[0])-(b[0]<a[0]);dy=(b[1]>a[1])-(b[1]<a[1])
        for i in range(abs(a[0]-b[0])+abs(a[1]-b[1])+1):
            q=(a[0]+dx*i,a[1]+dy*i)
            if image.getpixel(q) in (1,2):image.putpixel(q,2)
    for l,t,rr,bb,kind in windows:
        contacts = sorted({(x,y) for y in range(t,bb+1) for x in range(l,rr+1)
                           if (x in (l,rr) or y in (t,bb)) and image.getpixel((x,y))==2})
        if len(contacts)<2:continue
        for y in range(t,bb+1):
            for x in range(l,rr+1):
                if image.getpixel((x,y))==2:image.putpixel((x,y),1)
        cx,cy=(l+rr)//2,(t+bb)//2
        segments=[]
        if kind=='rectangle':
            points=[(l,t),(rr,t),(rr,bb),(l,bb),(l,t)]
            segments.extend(zip(points,points[1:]))
        else:
            segments.append(((l,cy),(rr,cy)) if kind=='horizontal' else ((cx,t),(cx,bb)))
            for q in contacts:
                target=(q[0],cy) if kind=='horizontal' else (cx,q[1])
                segments.append((q,target))
        for a,b in segments:ink(a,b)
        rectifications.append(dict(box=[l,t,rr,bb],shape=kind,contacts=contacts,segments=list(segments)))
    def readable(label):
        label = re.sub(r' FRLG$', '', label)
        label = re.sub(r'(SEA|CHANNEL)(\d+)',r'\1 \2',label)
        match = re.fullmatch(r'SEVII REEF(\d+)(CAP|RIGHT)',label)
        return f'SEVII REEF {match[1]} '+('NORTH' if match[2]=='CAP' else 'EAST') if match else label
    header = re.sub(PAT,lambda m:m[0].replace('"'+m[5]+'"','"'+readable(m[5])+'"'),header)
    names = {by_id[m[1]]:m[5] for m in re.finditer(PAT,header) if m[1] in by_id}
    nodes = sorted({r[k] for r in records for k in ('source','destination')})
    for n in nodes:
        if n not in names:
            label = maps[n]['region_map_section'].removeprefix('MAPSEC_').replace('_',' ')
            label = re.sub(r'ROUTE(\d+)',r'ROUTE \1',label)
            label = names_custom.get(n,label)
            names[n] = label
    # Give the new marine network geographic names, selectable in MAP; no
    # labels are painted on the atlas itself.
    sea_names = ['NORTH SEVII SEA','ONE ISLAND SEA','TWO ISLAND SEA','THREE ISLAND SEA',
                 'FOUR ISLAND SEA','FIVE ISLAND SEA','SOUTHWEST SEVII SEA',
                 'SEVEN ISLAND SEA','BIRTH ISLAND SEA','NAVEL ROCK SEA']
    for n in nodes:
        label = names_custom.get(n)
        if re.fullmatch(r'JourneyWorldSea\d\d',n):label=sea_names[int(n[-2:])]
        match=re.fullmatch(r'JourneyWorld(Lane|Fill)([123])([01])(Cap|Right)?',n)
        if match:
            island={('1','0'):'FOUR',('1','1'):'SIX',('2','0'):'FIVE',('2','1'):'SEVEN',('3','0'):'BIRTH',('3','1'):'NAVEL'}[(match[2],match[3])]
            label=island+' '+('WEST CHANNEL' if match[1]=='Lane' else 'NORTH REEF' if match[4]=='Cap' else 'EAST REEF')
        if label and names.get(n)!=label:
            ident=maps[n]['id']
            header=re.sub(r'(MAP_NUM\('+ident+r'\), MAPSEC_\w+, \d+, \d+, COMPOUND_STRING\(")[^"]+',lambda m:m[1]+label,header)
            names[n]=label
    end = header.index('};',header.index('sWorldPoints'))
    header = header[:end]+''.join(point_line(maps[n],coords[n],names[n]) for n in nodes if n not in {by_id[m[1]] for m in re.finditer(PAT,header) if m[1] in by_id})+header[end:]
    assert all(before.getpixel((x,y))==image.getpixel((x,y))
               for y in range(112) for x in range(224) if before.getpixel((x,y)) not in (1,2))
    # Zoom uses the same consolidated coast/route drawing, preserving the
    # native extra land pixels from the 2x atlas.
    detail_bytes=list(map(int,re.search(r'sWorldDetailPixels\[\] = \{([^}]+)',header)[1].split(',')))
    detail=Image.new('P',(448,224))
    for y in range(224):
        for x in range(448):detail.putpixel((x,y),(detail_bytes[y*224+x//2]>>((x&1)*4))&15)
    for y in range(112):
        for x in range(224):
            for dy in (0,1):
                for dx in (0,1):
                    q=(2*x+dx,2*y+dy)
                    if detail.getpixel(q) in (1,2):
                        detail.putpixel(q,2 if image.getpixel((x,y))==2 else 1)
    packed=bytes(detail.getpixel((x,y))|(detail.getpixel((x+1,y))<<4) for y in range(224) for x in range(0,448,2))
    header=re.sub(r'(sWorldDetailPixels\[\] = \{)[^}]+',lambda m:m[1]+','.join(map(str,packed)),encode(header,image))
    layer.stage(path,header)
    return layer.finish(routes=records,nodes=[dict(map=n,name=names[n],position=list(coords[n])) for n in nodes],
                        actual_connections_only=True,all_segments_orthogonal=True,
                        passages=PASSAGES,green_rectifications=rectifications,gps=gps,projections=geometry['projections'],
                        native_land_and_town_art_preserved=True,route_names_selectable_in_game=True,
                        map_size=[224,112],native_land_and_events_preserved=True,zoom_matches_overview=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    print(json.dumps(prepare(parser.parse_args().source),indent=2))
