"""Restore native Surf corridors and anchor cave icons to compiled entrances."""
import argparse,json,re
from pathlib import Path
from PIL import Image,ImageDraw
from candidate_layer import Layer
from prepare_offscreen_rival_entrances import PRIOR,LAYER as PREVIOUS
from prepare_world_dex_map import decode,encode,PAT,COLORS
from prepare_connected_sea_chart import route

ROOT=Path(__file__).resolve().parents[2]
LAYER='complete-marine-atlas';PRIOR=PRIOR+[PREVIOUS]
SURF_ROUTES={'Route19_Frlg','Route20_Frlg','Route21_North_Frlg','Route21_South_Frlg',
             'Route104',*[f'Route{i}' for i in range(105,110)],
             *[f'Route{i}' for i in range(124,135)]}

def position(geometry,name,x,y):
    p=next(p for p in geometry['projections'] if p['map']==name)
    sx=sy=total=0
    for a,b,c,d,xx,yy in geometry['anchors'][p['first']:p['first']+p['count']+1]:
        dx=a-x if x<a else x-c if x>c else 0
        dy=b-y if y<b else y-d if y>d else 0
        distance=dx*dx+dy*dy
        if not distance:return xx,yy
        weight=1048576//distance
        sx+=xx*weight;sy+=yy*weight;total+=weight
    return (sx+total//2)//total,(sy+total//2)//total

def point_line(m,xy,label):
    return '    {(MAP_GROUP('+m['id']+')<<8)|MAP_NUM('+m['id']+'), '+m['region_map_section']+', '+str(xy[0])+', '+str(xy[1])+', COMPOUND_STRING("'+label+'")},\n'

def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if old:=layer.existing():return old
    s=layer.source;maps={p.parent.name:json.loads(p.read_text()) for p in (s/'data/maps').glob('*/map.json')}
    byid={m['id']:n for n,m in maps.items()}
    geometry=json.loads((s/'.journey-connected-sea-chart').read_text())
    coords={p['map']:tuple(p['center']) for p in geometry['projections']}
    header=(s/'src/data/journey_world_map.h').read_text();before=decode(header)
    im=before.copy();points={byid[m[1]]:(int(m[3]),int(m[4])) for m in re.finditer(PAT,header)}
    # Erase only the old generic sanctuary squares and sea-route ink.
    for n,xy in points.items():
        if n.startswith('JourneySanctuary'):
            for y in range(xy[1]-1,xy[1]+2):
                for x in range(xy[0]-1,xy[0]+2):
                    if im.getpixel((x,y)) in [1,2,14]:im.putpixel((x,y),1)
    for y in range(112):
        for x in range(224):
            if im.getpixel((x,y))==2:im.putpixel((x,y),1)
    # All water components are eligible: native Route 21 is enclosed by land.
    sea={(x,y) for y in range(112) for x in range(224) if im.getpixel((x,y)) in [1,14]}
    edges={tuple(sorted((r['source'],r['destination']))) for r in geometry['orthogonal_marine_paths']
           if not any(n.startswith('JourneySanctuary') for n in [r['source'],r['destination']])}
    for n in SURF_ROUTES:
        for c in maps[n].get('connections') or []:
            o=byid[c['map']]
            if c['direction'] in ['up','down','left','right'] and o in coords:
                edges.add(tuple(sorted((n,o))))
    paths=[]
    for a,b in sorted(edges):
        try:p,corners=route(im,before,coords[a],coords[b],sea)
        except ValueError:
            # A city endpoint can face an enclosed Surf inlet. Use the actual
            # axis-aligned shore corridor; draw water pixels only, never land.
            start,end=coords[a],coords[b];corners=[start,(end[0],start[1]),end];p=[]
            for u,v in zip(corners,corners[1:]):
                dx=(v[0]>u[0])-(v[0]<u[0]);dy=(v[1]>u[1])-(v[1]<u[1])
                p.extend((u[0]+dx*i,u[1]+dy*i) for i in range(abs(v[0]-u[0])+abs(v[1]-u[1])+1))
        for xy in p:
            if im.getpixel(xy) in [1,2]:im.putpixel(xy,2)
        paths.append(dict(source=a,destination=b,polyline=corners,actual_connection=True))
    caves=[]
    for site in json.loads((s/'.journey-sanctuaries').read_text())['sites']:
        surface=site['surface'];access=surface
        if site['access']=='dive':access=byid[next(c['map'] for c in maps[surface]['connections'] if c['direction']=='dive')]
        entrances=[w for w in maps[access]['warp_events'] if byid.get(w['dest_map'])==site['map']]
        assert len(entrances)==1,site['map']
        w=entrances[0];xy=position(geometry,surface,w['x'],w['y']);n=site['map'];coords[n]=xy
        old=points[n];ident=maps[n]['id']
        header,count=re.subn(r'(\{\(MAP_GROUP\('+ident+r'\).*?, MAPSEC_\w+, )\d+, \d+,',lambda m:m[1]+f'{xy[0]}, {xy[1]},',header);assert count==1
        caves.append(dict(map=n,surface=surface,access_map=access,entry=[w['x'],w['y']],position=list(xy),old_position=list(old)))
    # Seafoam belongs to Route 20, including all of its underground floors.
    entrances=[w for w in maps['Route20_Frlg']['warp_events'] if byid[w['dest_map']]=='SeafoamIslands_1F_Frlg']
    seafoam_positions=[position(geometry,'Route20_Frlg',w['x'],w['y']) for w in entrances]
    xy=tuple((sum(p[i] for p in seafoam_positions)+len(entrances)//2)//len(entrances) for i in [0,1])
    extra=''
    for n,m in sorted(maps.items()):
        if m['region_map_section']=='MAPSEC_SEAFOAM_ISLANDS':
            assert n not in points;coords[n]=xy;extra+=point_line(m,xy,'SEAFOAM ISLANDS')
    end=header.rfind('};');header=header[:end]+extra+header[end:]
    caves.append(dict(map='SeafoamIslands_1F_Frlg',surface='Route20_Frlg',entries=[[w['x'],w['y']] for w in entrances],entrance_positions=[list(p) for p in seafoam_positions],position=list(xy)))
    for c in caves:
        parent=coords[c['surface']];entry=tuple(c['position'])
        p,corners=route(im,before,parent,entry,sea)
        for point in p:
            if im.getpixel(point) in [1,2]:im.putpixel(point,2)
        paths.append(dict(source=c['surface'],destination=c['map'],polyline=corners,actual_entrance=True))
    ink={(x,y) for y in range(112) for x in range(224) if im.getpixel((x,y))==2}
    # A small rock arch identifies a cave, instead of a floating white square.
    for c in caves:
        x,y=c['position']
        for dx,dy,color in [(0,-1,15),(-1,0,15),(0,0,0),(1,0,15)]:im.putpixel((x+dx,y+dy),color)
    # Keep city/island markers; restore city blues lost to the old broad ocean
    # color filter. Regional art also supplies true extra pixels for 2x zoom.
    panels=json.loads((s/'.journey-coastal-world-map').read_text())['panels']
    detail=im.resize((448,224),Image.Resampling.NEAREST);native_land=set()
    palette=Image.new('P',(1,1));palette.putpalette([v for c in COLORS for v in c]+[0]*720)
    waters={(164,180,255),(156,213,255),(74,156,230),(41,131,230),(82,148,213),(90,172,230)}
    for name,box in panels.items():
        x,y,w,h=box;native=Image.open(ROOT/'web/atlas'/(name+'.png')).convert('RGB')
        for yy in range(native.height):
            for xx in range(native.width):
                if native.getpixel((xx,yy)) in waters:native.putpixel((xx,yy),COLORS[1])
        if name!='hoenn':
            # Remove only the native region-selector component, not islands.
            todo=[(native.width-1,yy) for yy in range(native.height-24,native.height) if native.getpixel((native.width-1,yy))!=COLORS[1]];seen=set()
            while todo:
                xx,yy=todo.pop()
                if (xx,yy) in seen or not(native.width-16<=xx<native.width and native.height-24<=yy<native.height) or native.getpixel((xx,yy))==COLORS[1]:continue
                seen.add((xx,yy));native.putpixel((xx,yy),COLORS[1]);todo.extend([(xx-1,yy),(xx+1,yy),(xx,yy-1),(xx,yy+1)])
        overview=native.resize((w,h),Image.Resampling.NEAREST).quantize(palette=palette,dither=Image.Dither.NONE)
        for yy in range(h):
            for xx in range(w):
                if x+xx<224 and y+yy<112 and overview.getpixel((xx,yy))!=1:
                    im.putpixel((x+xx,y+yy),overview.getpixel((xx,yy)))
        art=native.resize((2*w,2*h),Image.Resampling.NEAREST).quantize(palette=palette,dither=Image.Dither.NONE)
        for yy in range(2*h):
            for xx in range(2*w):
                gx,gy=2*x+xx,2*y+yy
                if gx>=448 or gy>=224:continue
                pixel=art.getpixel((xx,yy))
                if pixel!=1:detail.putpixel((gx,gy),pixel);native_land.add((gx,gy))
    # Ink and cave icons retain exactly the same geographic anchors in zoom.
    for y in range(112):
        for x in range(224):
            if (x,y) in ink:
                for dx in [0,1]:
                    for dy in [0,1]:
                        if (2*x+dx,2*y+dy) not in native_land:detail.putpixel((2*x+dx,2*y+dy),2)
    for c in caves:
        x,y=c['position'];d=ImageDraw.Draw(detail)
        for dx,dy,color in [(0,-1,15),(-1,0,15),(0,0,0),(1,0,15)]:im.putpixel((x+dx,y+dy),color)
        d.rectangle((2*x-2,2*y-2,2*x+3,2*y+1),fill=15)
        d.rectangle((2*x,2*y-1,2*x+1,2*y+1),fill=0)
    header=encode(header,im)
    packed=bytes(detail.getpixel((x,y))|(detail.getpixel((x+1,y))<<4) for y in range(224) for x in range(0,448,2))
    header+='\nstatic const u8 sWorldDetailPixels[] = {'+','.join(map(str,packed))+'};\n'
    layer.stage('src/data/journey_world_map.h',header)
    # Synchronize fixed cave anchors, the native player point and Dex AREA.
    anchors=geometry['anchors'];projections=geometry['projections']
    for c in caves:
        n=c['map'];p=next((p for p in projections if p['map']==n),None)
        if p:assert p['count']==0;anchors[p['first']][4:6]=c['position'];p['center']=c['position']
    for n in sorted(coords):
        if maps[n]['region_map_section']!='MAPSEC_SEAFOAM_ISLANDS':continue
        layout=next(l for l in json.loads((s/'data/layouts/layouts.json').read_text())['layouts'] if l['id']==maps[n]['layout'])
        first=len(anchors);anchors.append([layout['width']//2,layout['height']//2,layout['width']//2,layout['height']//2,*xy])
        projections.append(dict(map=n,id=maps[n]['id'],first=first,count=0,width=layout['width'],height=layout['height'],center=list(xy)))
    pos='struct JourneyWorldAnchor { s16 left, top, right, bottom; u8 x, y; };\nstruct JourneyWorldProjection { u32 first; u16 map, count; };\nstatic const struct JourneyWorldAnchor sWorldAnchors[] = {\n'+''.join('{'+','.join(map(str,a))+'},\n' for a in anchors)+'};\nstatic const struct JourneyWorldProjection sWorldProjections[] = {\n'+''.join('{'+str(p['first'])+', (MAP_GROUP('+p['id']+')<<8)|MAP_NUM('+p['id']+'), '+str(p['count'])+'},\n' for p in projections)+'};\n'
    layer.stage('src/data/journey_world_position.h',pos)
    dex=(s/'src/data/journey_world_dex_locations.h').read_text()
    for c in caves:
        ident=maps[c['map']]['id'];cx,cy=c['position']
        dex=re.sub(r'(\{SPECIES_\w+,'+ident+r',)\d+,\d+,',lambda m:m[1]+f'{cx},{cy},',dex)
    # Event families were removed from grass after the original AREA export.
    # Their obtainable evolutions/forms share the real gift/workshop site.
    events=json.loads((s/'.journey-special-encounter-workshop').read_text())
    families={f['root']:f for f in events['event_families']};event_names={p['name'] for f in families.values() for p in f['species']}
    dex=re.sub(r'\{(SPECIES_\w+),MAP_\w+,\d+,\d+,\d+,\d+\},\n',lambda m:'' if m[1] in event_names else m[0],dex)
    section_points={m[2]:(int(m[3]),int(m[4])) for m in re.finditer(PAT,header)}
    def event_place(name):
        if name in coords:return coords[name]
        section=maps[name]['region_map_section']
        if section in section_points:return section_points[section]
        queue=[name];seen={name}
        for current in queue:
            for warp in maps[current].get('warp_events') or []:
                other=byid.get(warp['dest_map'])
                if other in coords:return coords[other]
                if other and other not in seen:seen.add(other);queue.append(other)
        raise ValueError(('Event site has no atlas exit',name))
    event_rows=[]
    for destination in events['destinations']:
        ident=destination['map'];n=byid[ident];m=maps[n]
        place=event_place(n)
        for pokemon in families[destination['root']]['species']:
            end=dex.rfind('};');dex=dex[:end]+f"{{{pokemon['name']},{ident},{place[0]},{place[1]},1,0}},\n"+dex[end:]
        event_rows.append(dict(map=n,position=list(place),family=destination['root']))
    for n,m in maps.items():
        if m['region_map_section']=='MAPSEC_SEAFOAM_ISLANDS':
            dex=re.sub(r'(\{SPECIES_\w+,'+m['id']+r',)\d+,\d+,',lambda match:match[1]+f'{xy[0]},{xy[1]},',dex)
    layer.stage('src/data/journey_world_dex_locations.h',dex)
    zoom=(s/'include/journey_atlas_zoom.inc').read_text()
    start=zoom.index('            u32 sx=*left+x/2');end=zoom.index('            u32 index=',start)
    zoom=zoom[:start]+'''            u32 sx=2*(*left)+x,sy=2*(*top)+y;
            u32 pixel=(sWorldDetailPixels[sy*224+sx/2]>>((sx&1)*4))&15;
'''+zoom[end:]
    layer.stage('include/journey_atlas_zoom.inc',zoom)
    return layer.finish(orthogonal_marine_paths=paths,cave_entrances=caves,event_dex_locations=event_rows,original_surf_routes_included=sorted(SURF_ROUTES),detail_size=[448,224],detail_bytes=len(packed),zoom_uses_native_extra_pixels=True,no_terrain_or_ports_changed=True,**{k:geometry[k] for k in ['anchors','projections','seams','boundary_nodes','maximum_neighbor_pixel_step']})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);print(prepare(p.parse_args().source)['layer'])
