"""Replace short marine shortcuts and foreign-bank shore seams with real water.

The atlas image is immutable. New rectangles trace its existing orthogonal
polylines; only tile-position projections are extended to describe real travel.
"""
import copy
import json
import math
import re
import struct
import subprocess
from pathlib import Path
import numpy as np
from render_sea_maps import MapRenderer
from prepare_world_dex_map import PAT
from world_grid_updates import rebuild
from sevii_navigation_grid import reconcile
ROOT=Path(__file__).resolve().parents[2]
OPP=dict(left='right',right='left',up='down',down='up')
VEC=dict(left=(-1,0),right=(1,0),up=(0,-1),down=(0,1))


def repair(layer):
    s=layer.source
    def raw(p):return layer.outputs[p] if p in layer.outputs else (s/p).read_bytes()
    def js(p):return json.loads(raw(p))
    def put(p,obj):layer.stage(p,json.dumps(obj,indent=2)+'\n')
    ld=js('data/layouts/layouts.json');ls={l['id']:l for l in ld['layouts']}
    groups=js('data/maps/map_groups.json')
    maps={p.parent.name:js(str(p.relative_to(s))) for p in (s/'data/maps').glob('*/map.json')}
    for p,b in layer.outputs.items():
        if re.fullmatch(r'data/maps/[^/]+/map.json',p):maps[p.split('/')[2]]=json.loads(b)
    oldmaps=copy.deepcopy(maps);byid={m['id']:n for n,m in maps.items()}
    blocks={}
    def vals(n):
        l=ls[maps[n]['layout']]
        if n not in blocks:blocks[n]=list(struct.unpack('<'+'H'*(l['width']*l['height']),raw(l['blockdata_filepath'])))
        return blocks[n]
    behavior_source=(s/'src/metatile_behavior.c').read_text()
    names=re.findall(r'\[(MB_\w+)\]\s*=\s*[^,\n]*TILE_FLAG_SURFABLE[^,\n]*',behavior_source)
    code='#include "constants/metatile_behaviors.h"\nconst unsigned short probe[]={'+','.join(names)+'};'
    asm=subprocess.check_output([str(ROOT/'.local/arm-gcc/usr/bin/arm-none-eabi-gcc'),'-S','-iquote',str(s/'include'),'-x','c','-','-o','-'],input=code,text=True)
    water_behaviors={int(v) for v in re.findall(r'\.short\s+(\d+)',asm)}
    renderer=MapRenderer(s);attrs={}
    def attr(bank,fr):
        key=bank,fr
        if key not in attrs:
            h=re.search(r'const struct Tileset '+bank+r'\s*=\s*\{(.*?)\};',renderer.headers,re.S)[1]
            symbol=re.search(r'\.metatileAttributes\s*=\s*(\w+)',h)[1]
            p=re.search(r'\b'+symbol+r'\[\].*?"([^"]+)"',renderer.metas)[1]
            b=raw(p);size=4 if fr else 2;attrs[key]=[int.from_bytes(b[i:i+size],'little')&(511 if fr else 255) for i in range(0,len(b),size)]
        return attrs[key]
    def wet(n,x,y):
        l=ls[maps[n]['layout']];fr=l['layout_version']=='frlg';cut=640 if fr else 512
        if not(0<=x<l['width'] and 0<=y<l['height']):return False
        v=vals(n)[y*l['width']+x];mid=v&1023
        return not v&0xC00 and attr(l['primary_tileset'] if mid<cut else l['secondary_tileset'],fr)[mid if mid<cut else mid-cut] in water_behaviors
    # Imported beach edge art inherited the ocean elevation. The avatar only
    # ends Surf when crossing to native ground elevation 3, so all outdoor
    # sand tiles must agree with the adjacent island interior and its NPCs.
    beach_elevations=[];bridge_elevations=[]
    for n,m in maps.items():
        l=ls[m['layout']]
        if m['map_type'] not in ['MAP_TYPE_ROUTE','MAP_TYPE_CITY','MAP_TYPE_TOWN','MAP_TYPE_OCEAN_ROUTE'] or l['primary_tileset'] not in ['gTileset_General','gTileset_General_Frlg']:continue
        v=vals(n);fr=l['layout_version']=='frlg';cut=640 if fr else 512;changed=[];bridges=[]
        for i,tile in enumerate(v):
            if tile>>12 not in [0,1]:continue
            mid=tile&1023
            behavior=attr(l['primary_tileset'] if mid<cut else l['secondary_tileset'],fr)[mid if mid<cut else mid-cut]
            if tile>>12==0 and behavior==0x71: # MB_BRIDGE_OVER_OCEAN
                v[i]=tile|0xF000;bridges.append([i%l['width'],i//l['width']])
            if tile>>12==1 and behavior==0x21: # MB_SAND; dry ground, not a Surf water behavior.
                v[i]=(tile&0xFFF)|0x3000;changed.append([i%l['width'],i//l['width']])
        if changed or bridges:layer.stage(l['blockdata_filepath'],struct.pack('<'+'H'*len(v),*v))
        if bridges:bridge_elevations.append(dict(map=n,bridge_tiles=bridges,from_elevation=0,to_elevation=15))
        if changed:
            beach_elevations.append(dict(map=n,land_tiles=changed,from_elevation=1,to_elevation=3))
    beach_elevations.sort(key=lambda row:row["map"])
    bridge_elevations.sort(key=lambda row:row["map"])
    # Native Mossdeep rocket gantries contain dry, passable elevation-1
    # decoration. New coastal access makes their backs reachable by Surf.
    # Block those ornaments without changing a pixel or any dry-land path.
    ornament_limits=[]
    for n in ['MossdeepCity','JourneyMossdeepOuterSea','JourneyMossdeepOuterEastSea','OneIsland_Frlg','EverGrandeCity','SlateportCity','Route107','Route110','VermilionCity_Frlg','Route12_Frlg','BattleFrontier_OutsideEast']:
        l=ls[maps[n]['layout']];v=vals(n);changed=[]
        for i,tile in enumerate(v):
            if tile>>12==1 and not tile&0xC00 and not wet(n,i%l['width'],i//l['width']):
                fr=l['layout_version']=='frlg';cut=640 if fr else 512;mid=tile&1023
                behavior=attr(l['primary_tileset'] if mid<cut else l['secondary_tileset'],fr)[mid if mid<cut else mid-cut]
                if not n.startswith(('Mossdeep','JourneyMossdeep')) and behavior!=0:continue
                v[i]=tile|0x400;changed.append([i%l['width'],i//l['width']])
        if changed:
            layer.stage(l['blockdata_filepath'],struct.pack('<'+'H'*len(v),*v))
            ornament_limits.append(dict(map=n,blocked_decorative_tiles=changed,graphics_unchanged=True))
    def edge(n,d,t,depth=0):
        l=ls[maps[n]['layout']];w,h=l['width'],l['height']
        return (depth if d=='left' else w-1-depth,t) if d in ['left','right'] else (t,depth if d=='up' else h-1-depth)
    chart=js('.journey-surf-review')['chart']
    positions={p['map']:list(p['position']) for p in chart['nodes']}
    header=raw('src/data/journey_world_map.h').decode()
    for m in re.finditer(PAT,header):
        n=byid.get(m[1])
        if n:positions.setdefault(n,[int(m[3]),int(m[4])])
    records={tuple(sorted([row['source'],row['destination']])):row for row in chart['routes']}
    candidates=[];seen=set();excluded=[]
    for n,m in sorted(maps.items()):
        for c in m.get('connections') or []:
            o=byid.get(c['map']);d=c['direction']
            if d not in OPP or o not in maps:continue
            pair=tuple(sorted([n,o]))
            if pair in seen:continue
            seen.add(pair)
            if n not in positions or o not in positions:continue
            if not (n.startswith('Journey') or o.startswith('Journey') or 'Harbor' in n or 'Harbor' in o):continue
            a,b=ls[m['layout']],ls[maps[o]['layout']]
            if a['primary_tileset'] not in ['gTileset_General','gTileset_General_Frlg'] or b['primary_tileset'] not in ['gTileset_General','gTileset_General_Frlg']:continue
            limit=a['height' if d in ['left','right'] else 'width'];size=b['height' if d in ['left','right'] else 'width'];off=c['offset']
            lo,hi=max(0,off),min(limit,off+size)
            available=[t for t in range(lo,hi) if wet(n,*edge(n,d,t)) and wet(o,*edge(o,OPP[d],t-off))]
            if not available:continue # Land/bridge connections stay native.
            path=copy.deepcopy(records.get(pair,{}).get('polyline',[positions[n],[positions[o]]]))
            if len(path)<2:path=[positions[n],positions[o]]
            if sum(abs(path[0][k]-positions[n][k]) for k in range(2))>sum(abs(path[-1][k]-positions[n][k]) for k in range(2)):path.reverse()
            # A passage record describes its complete route on both adjacent
            # edges. Use the two actual map centres when it is not an endpoint.
            if path[0]!=positions[n] or path[-1]!=positions[o]:
                aa,bb=positions[n],positions[o]
                path=[aa,[bb[0],aa[1]],bb]
            path=[p for j,p in enumerate(path) if j==0 or p!=path[j-1]]
            length=sum(abs(x[0]-y[0])+abs(x[1]-y[1]) for x,y in zip(path,path[1:]))
            physical=(a['width' if d in ['left','right'] else 'height']+b['width' if d in ['left','right'] else 'height'])//2
            long=length*4>physical+64
            foreign=a['primary_tileset']!=b['primary_tileset']
            if not foreign and a['secondary_tileset']!=b['secondary_tileset']:
                for name,dr,start in [(n,d,0),(o,OPP[d],off)]:
                    l=ls[maps[name]['layout']];cut=640 if l['layout_version']=='frlg' else 512
                    if any(vals(name)[yy*l['width']+xx]&1023>=cut for t in range(lo,hi) for depth in range(min(7,l['width' if dr in ['left','right'] else 'height'])) for xx,yy in [edge(name,dr,t-start,depth)]):foreign=True
            if not(long or foreign):continue
            span=min(18,hi-lo);mid=available[len(available)//2];start=max(lo,min(hi-span,mid-span//2))
            candidates.append(dict(source=n,destination=o,direction=d,old_offset=off,span=span,start=start,target_start=start-off,
                chart_path=path,chart_pixels=length,old_center_steps=physical,extra_steps=max(0,length*4-physical),foreign_bank=foreign,shortened_geography=long))
    # Each approach is a genuine map connection. Its first/last bank matches
    # the adjacent coast, so foreign secondary IDs never reach the shoreline.
    created=[];projections=copy.deepcopy(chart['projections']);oldprojections=copy.deepcopy(projections)
    # Existing cities enlarged for gyms keep their coordinates and old grids.
    for p in projections:
        l=ls[maps[p['map']]['layout']];p.update(width=l['width'],height=l['height'])
    nav=raw('src/data/journey_world_position.h').decode();nav=rebuild(nav,oldprojections,projections)
    authored={};newnames=[]
    for index,record in enumerate(candidates):
        n,o,d=record['source'],record['destination'],record['direction'];span=record['span']
        source_layout=ls[maps[n]['layout']];target_layout=ls[maps[o]['layout']]
        rawsegments=[(d,16)]
        if record['shortened_geography']:
            factor=max(1,(record['extra_steps']-32)/max(1,record['chart_pixels']))
            for aa,bb in zip(record['chart_path'],record['chart_path'][1:]):
                dx,dy=bb[0]-aa[0],bb[1]-aa[1];direction='right' if dx>0 else 'left' if dx<0 else 'down' if dy>0 else 'up'
                length=max(16,round((abs(dx)+abs(dy))*factor));rawsegments.append((direction,length))
        rawsegments.append((d,16))
        # Opposite headings need a visible two-corner turn, not a reversal
        # through the entry connection. Every bend stays orthogonal.
        segments=[]
        for direction,length in rawsegments:
            if segments and direction==OPP[segments[-1][0]]:
                side='right' if direction in ['up','down'] else 'up'
                segments.append((side,span+8))
            while length>112:segments.append((direction,112));length-=112
            segments.append((direction,max(16,length)))
        nodes=[];total=sum(max(1,length-span//2) for _,length in segments);travelled=0
        # Parameterize the unchanged chart path by distance; rectangles have
        # matching real distances even when an approach requires a short bend.
        def point(fraction):
            path=record['chart_path'];distance=record['chart_pixels']*fraction
            for aa,bb in zip(path,path[1:]):
                length=abs(aa[0]-bb[0])+abs(aa[1]-bb[1])
                if distance<=length and length:return [round(aa[k]+(bb[k]-aa[k])*distance/length) for k in range(2)]
                distance-=length
            return path[-1]
        for j,(direction,length) in enumerate(segments):
            name=f'JourneySurfLink{index:03}{j:02}'
            label=('KANTO-SEVII' if max(positions[n][0],positions[o][0])>125 and min(positions[n][1],positions[o][1])<65 else 'HOENN-SEVII' if max(positions[n][0],positions[o][0])>125 else 'COASTAL')+f' SEA {index+1:02}'
            layout=copy.deepcopy(source_layout if j<len(segments)//2 else target_layout)
            w,h=(length,span) if direction in ['left','right'] else (span,length)
            layout.update(id='LAYOUT_'+name.upper(),name=name+'_Layout',width=w,height=h,border_filepath=f'data/layouts/{name}/border.bin',blockdata_filepath=f'data/layouts/{name}/map.bin')
            ld['layouts'].append(layout);ls[layout['id']]=layout
            m=copy.deepcopy(maps[n]);m.update(id='MAP_'+name.upper(),name=name,layout=layout['id'],map_type='MAP_TYPE_OCEAN_ROUTE',connections=[],warp_events=[],object_events=[],coord_events=[],bg_events=[],allow_cycling=False,allow_running=False,show_map_name=True,weather='WEATHER_SUNNY',requires_flash=False)
            maps[name]=m;byid[m['id']]=name
            group='JourneySurfLinks'+str(len(newnames)//100)
            if group not in groups:groups['group_order'].append(group);groups[group]=[]
            groups[group].append(name);newnames.append(name)
            fr=layout['layout_version']=='frlg';water=0x112B if fr else 0x1170;rock=0x1643 if fr else 0x15F9
            blocks[name]=[water]*(w*h)
            layer.stage(layout['border_filepath'],struct.pack('<4H',*([rock]*4)))
            pixels=[]
            for yy in range(h):
                for xx in range(w):
                    u=xx if direction=='right' else w-1-xx if direction=='left' else yy if direction=='down' else h-1-yy
                    fraction=(travelled+u/max(1,length-1)*max(1,length-span//2))/total
                    p=point(fraction);pixels.append(p[0]|p[1]<<8)
            authored[name]=np.array(pixels,dtype=np.int32).reshape(h,w)
            center=point((travelled+max(1,length-span//2)/2)/total)
            projections.append(dict(map=name,id=m['id'],width=w,height=h,center=center))
            nodes.append((name,direction,w,h));travelled+=max(1,length-span//2)
            created.append(dict(map=name,name=label,source=n,destination=o,heading=direction,size=[w,h],primary=layout['primary_tileset'],secondary=layout['secondary_tileset'],chart_position=center))
        # Remove exactly the old reciprocal edge and retain every other link.
        maps[n]['connections']=[c for c in maps[n]['connections'] if not(c['map']==maps[o]['id'] and c['direction']==d)]
        maps[o]['connections']=[c for c in maps[o]['connections'] if not(c['map']==maps[n]['id'] and c['direction']==OPP[d])]
        def link(a,b,direction,offset):
            maps[a]['connections'].append(dict(map=maps[b]['id'],direction=direction,offset=offset))
            maps[b]['connections'].append(dict(map=maps[a]['id'],direction=OPP[direction],offset=-offset))
        link(n,nodes[0][0],d,record['start'])
        for current,nxt in zip(nodes,nodes[1:]):
            a,heading,w,h=current;b,nextheading,_,_=nxt
            offset=0 if heading==nextheading else w-span if heading=='right' else h-span if heading=='down' else 0
            link(a,b,nextheading,offset)
        link(nodes[-1][0],o,d,-record['target_start'])
        record.update(segments=[v[0] for v in nodes],new_real_center_steps=sum(max(1,v[2] if v[1] in ['left','right'] else v[3]) for v in nodes),native_ports_and_cave_warps_preserved=True)
    # A whole single-tile boulder defines a closed boundary. Open every real
    # connection span and never leave an unreachable water strip outside it.
    for n in newnames:
        l=ls[maps[n]['layout']];w,h=l['width'],l['height'];v=blocks[n];fr=l['layout_version']=='frlg';rock=0x1643 if fr else 0x15F9
        spans={d:set() for d in OPP}
        for c in maps[n]['connections']:
            other=ls[maps[byid[c['map']]]['layout']];limit=h if c['direction'] in ['left','right'] else w
            length=other['height' if c['direction'] in ['left','right'] else 'width']
            spans[c['direction']].update(range(max(0,c['offset']),min(limit,c['offset']+length)))
        for yy in range(h):
            for xx in range(w):
                if xx==0 and yy not in spans['left'] or xx==w-1 and yy not in spans['right'] or yy==0 and xx not in spans['up'] or yy==h-1 and xx not in spans['down']:v[yy*w+xx]=rock
    for n,m in maps.items():
        if n not in oldmaps or m!=oldmaps[n]:put(f'data/maps/{n}/map.json',m)
    for n in newnames:
        l=ls[maps[n]['layout']];layer.stage(l['blockdata_filepath'],struct.pack('<'+'H'*len(blocks[n]),*blocks[n]))
    # New names/positions are metadata; all existing atlas image arrays remain
    # byte-for-byte identical. Existing cities and cave icons never move.
    rows=[]
    for row in created:
        m=maps[row['map']];x,y=row['chart_position'];rows.append('    {(MAP_GROUP('+m['id']+')<<8)|MAP_NUM('+m['id']+'), '+m['region_map_section']+f', {x}, {y}, COMPOUND_STRING("'+row['name']+'")},\n')
    start=header.index('static const struct JourneyWorldPoint sWorldPoints[]');end=header.index('\n};',start)
    layer.stage('src/data/journey_world_map.h',header[:end]+'\n'+''.join(rows)+header[end:])
    nav=rebuild(nav,projections[:len(oldprojections)],projections,authored=authored)
    # Geometry now has room for the previously collapsed long journeys. Keep
    # native city markers fixed and reconcile the full tile graph at each seam.
    nav,gps=reconcile(nav,projections,maps)
    layer.stage('src/data/journey_world_position.h',nav)
    put('data/layouts/layouts.json',ld);put('data/maps/map_groups.json',groups)
    # Every new header needs its no-op script table.
    layer.stage('data/maps/JourneySurfLinks.inc',''.join(n+'_MapScripts::\n\t.byte 0\n' for n in newnames))
    layer.stage('data/event_scripts.s',raw('data/event_scripts.s').decode()+'\n\t.include "data/maps/JourneySurfLinks.inc"\n')
    return dict(repaired_links=candidates,new_segments=created,new_segment_count=len(created),atlas_graphics_unchanged=True,
        proportional_tiles_per_chart_pixel=4,closed_edges_use_whole_boulders=True,beach_land_elevations=beach_elevations,bridge_multilevel_elevations=bridge_elevations,ornament_limits=ornament_limits,native_ports_caves_events_and_land_preserved=True,
        foreign_bank_changes_happen_in_open_water=True,gps=gps)
