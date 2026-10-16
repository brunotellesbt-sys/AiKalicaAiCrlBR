"""Finish ocean scenery, eight annotated cave branches and an isolated review mode."""
import argparse, copy, io, json, re, struct
from pathlib import Path
import numpy as np
from PIL import Image
from candidate_layer import Layer
from prepare_surf_cave_coasts import PRIOR, LAYER as PREVIOUS
from prepare_world_dex_map import decode, encode, PAT
from prepare_complete_marine_atlas import point_line
from prepare_connected_sea_chart import route
from world_grid_updates import rebuild
from sevii_navigation_grid import reconcile

LAYER='surf-review'; PRIOR=PRIOR+[PREVIOUS]
# The annotation is the 224 x 112 atlas enlarged to 1216 x 608.
MARKS=[('Farol',[110,49]),('Brisa',[170,48]),('Horizonte',[211,65]),('Coral',[173,79]),
       ('Alvorada',[211,86]),('Espuma',[129,108]),('Ocaso',[140,110]),('Mare',[199,110])]
OPP=dict(left='right',right='left',up='down',down='up')

def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if old:=layer.existing():return old
    s=layer.source
    maps={p.parent.name:json.loads(p.read_text()) for p in (s/'data/maps').glob('*/map.json')}
    ld=json.loads((s/'data/layouts/layouts.json').read_text()); ls={l['id']:l for l in ld['layouts']}
    groups=json.loads((s/'data/maps/map_groups.json').read_text())
    groups['group_order'].append('JourneyReviewCaves');groups['JourneyReviewCaves']=[]
    chart=copy.deepcopy(json.loads((s/'.journey-surf-cave-coasts').read_text())['chart']);oldproj=copy.deepcopy(chart['projections'])
    sanct=copy.deepcopy(json.loads((s/'.journey-sanctuaries').read_text()))
    h=(s/'src/data/journey_world_map.h').read_text(); atlas=decode(h);before=atlas.copy()
    nav=(s/'src/data/journey_world_position.h').read_text()
    packed=list(map(int,re.search(r'sWorldNavigationPixels\[\] = \{([^}]+)',nav)[1].split(',')))
    grids={};at=0
    for p in oldproj:
        w,hh=p['width'],p['height'];grids[p['map']]=np.array(packed[at:at+w*hh]).reshape(hh,w);at+=w*hh
    terrain={};art=[];scripts=(s/'data/event_scripts.s').read_text()
    def vals(n):
        l=ls[maps[n]['layout']]
        if n not in terrain:
            b=(s/l['blockdata_filepath']).read_bytes();terrain[n]=list(struct.unpack('<'+'H'*(len(b)//2),b))
        return terrain[n]
    def spans(n):
        l=ls[maps[n]['layout']];sp={d:set() for d in OPP};byid={m['id']:n for n,m in maps.items()}
        for c in maps[n].get('connections') or []:
            d=c['direction']
            if d not in sp:continue
            q=ls[maps[byid[c['map']]]['layout']];limit=l['height'] if d in ['left','right'] else l['width']
            length=q['height'] if d in ['left','right'] else q['width']
            sp[d].update(range(max(0,c['offset']),min(limit,c['offset']+length)))
        return sp
    # Complete one-tile boulders have no phase/alignment dependence at odd
    # map widths, signed offsets or the end of a neighboring connection.
    # Only unused primary graphics/metatiles are reserved; animated water is
    # the bottom layer, with a transparent rock over it.
    from render_sea_maps import MapRenderer
    renderer=MapRenderer(s);rocks={}
    for fr,prim,example,mid,slots,quad in [
        (True,'gTileset_General_Frlg','JourneyWorldSea00',0x243,[482,483,484,485],[0x510,0x511,0x518,0x519]),
        (False,'gTileset_General','JourneyHoennSouthSea',0x1F9,[504,505,506,507],[0x1550,0x551,0x558,0x1559])]:
        header=re.search(r'const struct Tileset '+prim+r'\s*=\s*\{(.*?)\};',renderer.headers,re.S)[1]
        symbol=re.search(r'\.metatiles\s*=\s*(\w+)',header)[1]
        meta=re.search(r'\b'+symbol+r'\[\].*?"([^"]+)"',renderer.metas)[1];folder=Path(meta).parent
        words=list(struct.unpack('<'+'H'*((s/meta).stat().st_size//2),(s/meta).read_bytes()))
        used=set()
        for l in ls.values():
            if l['primary_tileset']!=prim:continue
            for key in ['blockdata_filepath','border_filepath']:
                b=(s/l[key]).read_bytes();assert all((v&1023)!=mid for v in struct.unpack('<'+'H'*(len(b)//2),b)),('Reserved metatile in use',l['id'],mid)
            try:ww=renderer.tileset(l['secondary_tileset'])[2]
            except TypeError:continue
            used.update(v&1023 for v in ww)
        used.update(v&1023 for v in words);assert not set(slots)&used
        original=renderer.render(example,values=quad,dimensions=(2,2),npcs=False)[0]
        small=original.resize((16,16),Image.Resampling.NEAREST)
        tileimg=Image.open(s/folder/'tiles.png').copy();pal=renderer.tileset(prim)[1][4]
        # Water is blue; preserve the neutral gray native rock pixels only.
        for y in range(16):
            for x in range(16):
                rgb=small.getpixel((x,y));r,g,b=rgb
                ci=0 if b>r+70 else min(range(1,16),key=lambda i:sum((a-c)**2 for a,c in zip(pal[i],rgb)))
                slot=slots[(y//8)*2+x//8];tileimg.putpixel((slot%16*8+x%8,slot//16*8+y%8),ci)
        output=io.BytesIO();tileimg.save(output,format='PNG');layer.stage((folder/'tiles.png').as_posix(),output.getvalue())
        water=0x12B if fr else 0x170;bottom=words[water*8:water*8+4]
        words[mid*8:mid*8+8]=bottom+[0x4000+t for t in slots]
        layer.stage(meta,struct.pack('<'+'H'*len(words),*words))
        attrsym=re.search(r'\.metatileAttributes\s*=\s*([^,\n]+)',header)[1].strip()
        attrhead=(s/'src/data/tilesets/metatiles.h').read_text()
        attr=re.search(r'\b'+attrsym+r'\[\].*?"([^"]+)"',attrhead)[1]
        raw=bytearray((s/attr).read_bytes());size=4 if fr else 2
        raw[mid*size:(mid+1)*size]=raw[water*size:(water+1)*size]
        layer.stage(attr,raw);rocks[fr]=0x1400|mid
        art.append(dict(primary=prim,metatile=mid,graphics=slots,animated_water_underlay=True,complete_single_tile_rock=True))
    bounded=copy.deepcopy(json.loads((s/'.journey-surf-cave-coasts').read_text())['boundaries'])
    from prepare_complete_marine_atlas import SURF_ROUTES
    existing={r['map'] for r in bounded}
    for n,m in sorted(maps.items()):
        if n in existing or ls[m['layout']]['primary_tileset'] not in ['gTileset_General','gTileset_General_Frlg']:continue
        if n in SURF_ROUTES or m['map_type']=='MAP_TYPE_OCEAN_ROUTE':bounded.append(dict(map=n))
    # Replace the old four quadrants together on route rims. Interior native
    # scenery, beach trainers, ports and their events retain their locations.
    rims=[]
    for row in bounded:
        n=row['map'];maps[n]['show_map_name']=True;l=ls[maps[n]['layout']];w,hh=l['width'],l['height'];v=vals(n);sp=spans(n);fr=l['layout_version']=='frlg'
        oldrocks={0x510,0x511,0x518,0x519} if fr else {0x1550,0x551,0x558,0x1559}
        count=0
        for y in range(hh):
            for x in range(w):
                closed=(x<2 and y not in sp['left'] or x>=w-2 and y not in sp['right'] or y<2 and x not in sp['up'] or y>=hh-2 and x not in sp['down'])
                if v[y*w+x] in oldrocks or closed and v[y*w+x]>>12<=1 and not v[y*w+x]&0xC00:v[y*w+x]=rocks[fr];count+=1
        l['border_filepath']=f'data/layouts/{n}/review-limits.bin';layer.stage(l['border_filepath'],struct.pack('<4H',*[rocks[fr]]*4))
        rims.append(dict(map=n,replaced_boundary_tiles=count))
    mountain_repairs=[]
    for site in sanct['sites']:
        if site['access']!='surf':continue
        n=site['surface'];cx,cy=site['entry'];v=vals(n);w=ls[maps[n]['layout']]['width']
        for y in range(cy-6,cy-3):
            for x in range(cx-3,cx+4):v[y*w+x]=0x3115
        for yy,row in enumerate([[0x498,0x499,0x49A],[0x4A0,0x4A1,0x4A2],[0x4A8,0x30A9,0x4AA]]):
            for xx,t in enumerate(row):v[(cy-6+yy)*w+cx-1+xx]=t
        mountain_repairs.append(dict(map=n,entry=[cx,cy-4],complete_native_cave_shell=True))
    # Native route entry banners must use the actual map's registered name,
    # not the section of the sea map originally used as a template.
    p='src/journey_world_map.c';text=(s/p).read_text();anchor='u16 JourneyWorldMapPlayerPoint(void)'
    text=text.replace(anchor,'''const u8 *JourneyCurrentMapName(void)
{
    u16 i, map = (gSaveBlock1Ptr->location.mapGroup << 8) | gSaveBlock1Ptr->location.mapNum;
    for (i = 0; i < ARRAY_COUNT(sWorldPoints); i++)
        if (sWorldPoints[i].map == map) return sWorldPoints[i].name;
    return NULL;
}

'''+anchor);layer.stage(p,text)
    p='include/journey_world_map.h';layer.stage(p,(s/p).read_text().replace('#include "main.h"','#include "global.h"\n#include "main.h"').replace('void JourneyWorldMapOpen(', 'const u8 *JourneyCurrentMapName(void);\nvoid JourneyWorldMapOpen('))
    p='include/map_name_popup.h';layer.stage(p,(s/p).read_text().replace('#define MAP_POPUP_STRING_BUFFER_LENGTH 27','#define MAP_POPUP_STRING_BUFFER_LENGTH 96'))
    p='src/map_name_popup.c';text=(s/p).read_text();text='#include "journey_world_map.h"\n'+text
    text=text.replace('    if (IsCeladonDeptStore(mapHeader))','    const u8 *journeyName = JourneyCurrentMapName();\n    if (journeyName != NULL)\n        StringCopy(dest, journeyName);\n    else if (IsCeladonDeptStore(mapHeader))');layer.stage(p,text)
    p='src/overworld.c';text=(s/p).read_text().replace('if (gMapHeader.regionMapSectionId != sLastMapSectionId)','if (gMapHeader.showMapName || gMapHeader.regionMapSectionId != sLastMapSectionId)');layer.stage(p,text)
    # Render shared coast features in a foreign bank's visible apron too.
    # Filling all foreign blocks with water made whole rock walls pop into
    # view exactly when the map ID changed.
    p='src/fieldmap.c';text=(s/p).read_text()
    old='            for (j = 0; j < width; j++)\n                dest[j] = water;'
    new='            for (j = 0; j < width; j++)\n            {\n                u16 id = src[j] & 0x3FF;\n                u16 translated = water | (src[j] & 0xC00);\n                bool8 currentFrlg = gMapHeader.mapLayout->isFrlg;\n                if (id == (currentFrlg ? 0x1F9 : 0x243))\n                    translated = (src[j] & ~0x3FF) | (currentFrlg ? 0x243 : 0x1F9);\n                else if (!currentFrlg && ((id >= 0x10C && id <= 0x10E) || (id >= 0x114 && id <= 0x116) || (id >= 0x11C && id <= 0x11E)))\n                    translated = (src[j] & ~0x3FF) | (id + 15);\n                else if (currentFrlg && ((id >= 0x11B && id <= 0x11D) || (id >= 0x123 && id <= 0x125) || (id >= 0x12B && id <= 0x12D)))\n                    translated = (src[j] & ~0x3FF) | (id - 15);\n                dest[j] = translated;\n            }'
    assert old in text;layer.stage(p,text.replace(old,new,1))
    # A ROM record rather than a saved flag keeps review-only behavior out of
    # normal editions and prevents it leaking via Save/Continue.
    layer.stage('include/journey_review.h','#ifndef GUARD_JOURNEY_REVIEW_H\n#define GUARD_JOURNEY_REVIEW_H\n#include "global.h"\nextern const u8 gJourneyReviewMode;\n#endif\n')
    layer.stage('src/journey_review.c','#include "global.h"\nconst u8 gJourneyReviewMode = 0;\n')
    p='src/trainer_see.c';text='#include "journey_review.h"\n'+(s/p).read_text();text=text.replace('    if (FlagGet(OW_FLAG_NO_TRAINER_SEE))','    if (gJourneyReviewMode || FlagGet(OW_FLAG_NO_TRAINER_SEE))');layer.stage(p,text)
    p='src/wild_encounter.c';text='#include "journey_review.h"\n'+(s/p).read_text();text=text.replace('if (sWildEncountersDisabled == TRUE)','if (gJourneyReviewMode || sWildEncountersDisabled == TRUE)')
    text=text.replace('    PlayerGetDestCoords(&x, &y);\n    headerId = GetCurrentMapWildMonHeaderId();','    if (gJourneyReviewMode) return FALSE;\n    PlayerGetDestCoords(&x, &y);\n    headerId = GetCurrentMapWildMonHeaderId();')
    text=text.replace('    if (headerId != HEADER_NONE)\n    {\n        timeOfDay = GetTimeOfDayForEncounters(headerId, WILD_AREA_ROCKS);','    if (gJourneyReviewMode) { gSpecialVar_Result = FALSE; return; }\n    if (headerId != HEADER_NONE)\n    {\n        timeOfDay = GetTimeOfDayForEncounters(headerId, WILD_AREA_ROCKS);')
    text=text.replace('bool8 DoesCurrentMapHaveFishingMons(void)\n{','bool8 DoesCurrentMapHaveFishingMons(void)\n{\n    if (gJourneyReviewMode) return FALSE;')
    text=text.replace('    gIsFishingEncounter = TRUE;','    if (gJourneyReviewMode) return;\n    gIsFishingEncounter = TRUE;');layer.stage(p,text)
    # Select the closest usable free edge of the existing route network.
    # Every branch is a reciprocal native map connection, never a ferry warp.
    baseline_names=[r['map'] for r in bounded];authored={};branches=[]
    def edgepoint(w,hh,d,t,depth=0):
        return (depth if d=='left' else w-1-depth,t) if d in ['left','right'] else (t,depth if d=='up' else hh-1-depth)
    for index,(theme,target) in enumerate(MARKS+[('Artisan',[119,105])]):
        candidates=[]
        for n in baseline_names:
            if n not in grids:continue
            l=ls[maps[n]['layout']];w,hh=l['width'],l['height'];sp=spans(n);v=vals(n)
            for d in OPP:
                limit=hh if d in ['left','right'] else w
                for off in range(0,limit-23,2):
                    if any(t in sp[d] for t in range(off,off+24)):continue
                    coords=[edgepoint(w,hh,d,t,depth) for t in range(off,off+24) for depth in range(2,7)]
                    if not all(v[y*w+x] in [0x112B,0x1170] for x,y in coords):continue
                    x,y=edgepoint(w,hh,d,off+12);p=int(grids[n][y,x]);xy=[p&255,p>>8]
                    dist=abs(xy[0]-target[0])+abs(xy[1]-target[1]);candidates.append((dist,n,d,off,xy))
        assert candidates,theme
        distance,parent,d,off,start=min(candidates);parent_fr=ls[maps[parent]['layout']]['layout_version']=='frlg';fr=True
        parent_before=list(vals(parent))
        n='Journey'+theme+'Approach';cname='JourneyCave'+theme
        template=copy.deepcopy(maps['JourneyWorldSea01']);w,hh=(64,24) if d in ['left','right'] else (24,64)
        template.update(id='MAP_'+n.upper(),name=n,layout='LAYOUT_'+n.upper(),connections=[dict(direction=OPP[d],offset=-off,map=maps[parent]['id'])],object_events=[],warp_events=[],coord_events=[],bg_events=[],show_map_name=True)
        maps[n]=template;maps[parent]['connections'].append(dict(direction=d,offset=off,map=template['id']))
        l=copy.deepcopy(ls[maps['JourneyWorldSea01']['layout']]);l.update(id=template['layout'],name=n+'_Layout',width=w,height=hh,blockdata_filepath=f'data/layouts/{n}/map.bin',border_filepath=f'data/layouts/{n}/border.bin')
        ls[l['id']]=l;ld['layouts'].append(l);groups['JourneyReviewCaves'].append(n)
        water=0x112B if fr else 0x1170;v=[water]*(w*hh)
        # Reserve enough room for the complete island and at least four Surf
        # lanes around it. Entrance orientation remains south in every branch.
        cx=20 if d=='left' else w-21 if d=='right' else w//2
        cy=20 if d=='up' else hh-21 if d=='down' else hh//2
        shore=[0x10C,0x10D,0x10E,0x114,0x115,0x116,0x11C,0x11D,0x11E] if fr else [0x11B,0x11C,0x11D,0x123,0x124,0x125,0x12B,0x12C,0x12D]
        land={(cx+x,cy+y) for y in range(-7,8) for x in range(-7,8) if abs(x)+abs(y)<=11}
        for x,y in land:
            row=0 if (x,y-1) not in land else 2 if (x,y+1) not in land else 1
            col=0 if (x-1,y) not in land else 2 if (x+1,y) not in land else 1
            v[y*w+x]=((3 if fr or row==col==1 else 1)<<12)|shore[row*3+col]
        # Both primary banks retain the native complete three-row cave shell.
        mountain=[[0x498,0x499,0x49A],[0x4A0,0x4A1,0x4A2],[0x4A8,0x30A9,0x4AA]]
        for yy,row in enumerate(mountain):
            for xx,t in enumerate(row):v[(cy-4+yy)*w+cx-1+xx]=t
        entry=[cx,cy-2];terrain[n]=v
        # Clear a full seven-tile apron in the parent before adding the branch.
        pl=ls[maps[parent]['layout']];pv=vals(parent)
        for t in range(off,off+24):
            for depth in range(7):
                x,y=edgepoint(pl['width'],pl['height'],d,t,depth);pv[y*pl['width']+x]=0x112B if parent_fr else 0x1170
        sp=spans(n)
        for y in range(hh):
            for x in range(w):
                if (x<2 and y not in sp['left'] or x>=w-2 and y not in sp['right'] or y<2 and x not in sp['up'] or y>=hh-2 and x not in sp['down']):v[y*w+x]=rocks[fr]
        layer.stage(l['border_filepath'],struct.pack('<4H',*[rocks[fr]]*4))
        if theme=='Artisan':
            chamber=maps['ArtisanCave_1F'];dest=len(chamber['warp_events']);cl=ls[chamber['layout']];cv=vals('ArtisanCave_1F')
            # Retain both original Artisan exits. The new Surf entrance uses
            # its own reciprocal threshold on the unused east room floor.
            exitxy=[11,17];cv[17*cl['width']+11]=cv[17*cl['width']+10]
            chamber['warp_events'].append(dict(x=11,y=17,elevation=0,dest_map=template['id'],dest_warp_id='0'))
            cname='ArtisanCave_1F';altars=[]
        else:
            original=max(sanct['sites'][:14],key=lambda q:len(maps[q['map']]['object_events']));old=maps[original['map']]
            donor=original['map'];donor_count=len(old['object_events'])
            chamber=copy.deepcopy(old);chamber.update(id='MAP_'+cname.upper(),name=cname,layout='LAYOUT_'+cname.upper(),object_events=[copy.deepcopy(old['object_events'].pop(0))],warp_events=[dict(x=14,y=19,elevation=0,dest_map=template['id'],dest_warp_id='0')],coord_events=[],bg_events=[],connections=None,show_map_name=True)
            interior=['GraniteCave_StevensRoom','MeteorFalls_StevensCave','ShoalCave_LowTideInnerRoom','CaveOfOrigin_1F','ScorchedSlab','TerraCave_End','MarineCave_End','AlteringCave'][index]
            native_map=maps[interior];native_layout=ls[native_map['layout']];cw,ch=native_layout['width'],native_layout['height'];cv=list(vals(interior))
            exit_event=copy.deepcopy(max(native_map['warp_events'],key=lambda e:e['y']))
            ex,ey=exit_event['x'],exit_event['y']
            # Retain the complete native room, with one real outside exit.
            # Other old stairs are replaced by adjacent matching floor.
            for e in native_map['warp_events']:
                if (e['x'],e['y'])==(ex,ey):continue
                near=[cv[y*cw+x] for y in range(max(0,e['y']-1),min(ch,e['y']+2)) for x in range(max(0,e['x']-1),min(cw,e['x']+2)) if not cv[y*cw+x]&0xC00]
                if near:cv[e['y']*cw+e['x']]=near[0]
            from collections import deque
            q=deque([(ex,ey)]);seen={(ex,ey)}
            while q:
                x,y=q.popleft()
                for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                    xx,yy=x+dx,y+dy
                    if 0<=xx<cw and 0<=yy<ch and (xx,yy) not in seen and not cv[yy*cw+xx]&0xC00:seen.add((xx,yy));q.append((xx,yy))
            candidates=[(abs(x-ex)+abs(y-ey),x,y) for x,y in seen if (x,y+1) in seen and abs(x-ex)+abs(y-ey)>3]
            _,ax,ay=max(candidates);altar=chamber['object_events'][0];altar.update(x=ax,y=ay,elevation=cv[ay*cw+ax]>>12)
            chamber.update(layout='LAYOUT_'+cname.upper(),warp_events=[dict(exit_event,dest_map=template['id'],dest_warp_id='0')],music=native_map['music'])
            dest=0;maps[cname]=chamber;groups['JourneyReviewCaves'].append(cname)
            cl=copy.deepcopy(native_layout);cl.update(id=chamber['layout'],name=cname+'_Layout',blockdata_filepath=f'data/layouts/{cname}/map.bin',border_filepath=f'data/layouts/{cname}/border.bin')
            ls[cl['id']]=cl;ld['layouts'].append(cl);terrain[cname]=cv
            layer.stage(cl['border_filepath'],(s/native_layout['border_filepath']).read_bytes())
            cap=next(c for c in sanct['captures'] if c['flag']==chamber['object_events'][0]['flag']);cap.update(site=theme,map=cname,surface=n,access='surf',position=[ax,ay])
            area_path='src/pokedex_area_screen.c';area=layer.outputs.get(area_path,(s/area_path).read_bytes()).decode()
            area=re.sub(r'(if \(species == '+cap['species']+r'\b.*?SetSpecialMapHasMon\([^;]+;)',lambda m:m[0].replace(old['id'],chamber['id']),area,flags=re.S)
            layer.stage(area_path,area)
            altars=[cap['species']];sanct['sites'].append(dict(theme=theme,map=cname,surface=n,access='surf',entry=entry,species_count=1,region=chamber.get('region','REGION_HOENN'),section=chamber['region_map_section']))
            script=cname+'_MapScripts::\n\tmap_script MAP_SCRIPT_ON_TRANSITION, JourneySanctuary_Sync\n\t.byte 0\n'
            layer.stage(f'data/maps/{cname}/scripts.inc',script);scripts+=f'\n\t.include "data/maps/{cname}/scripts.inc"\n'
            dexpath='src/data/journey_world_dex_locations.h'
            dex=layer.outputs.get(dexpath,(s/dexpath).read_bytes()).decode();dex=re.sub(r'(\{'+cap['species']+r',)MAP_\w+,\d+,\d+,',lambda m:m[1]+chamber['id']+f',{target[0]},{target[1]},',dex);layer.stage(dexpath,dex)
        template['warp_events']=[dict(x=entry[0],y=entry[1],elevation=3,dest_map=chamber['id'],dest_warp_id=str(dest))]
        layer.stage(f'data/maps/{n}/scripts.inc',n+'_MapScripts::\n\t.byte 0\n');scripts+=f'\n\t.include "data/maps/{n}/scripts.inc"\n'
        # Draw the shortest orthogonal sea-only branch to the existing ink.
        sea={(x,y) for y in range(112) for x in range(224) if atlas.getpixel((x,y)) in [1,2]}
        ink=[q for q in sea if before.getpixel(q)==2];nearest=min(ink,key=lambda q:(abs(q[0]-target[0])+abs(q[1]-target[1]),q))
        pixels,corners=route(atlas,atlas,nearest,(target[0],min(111,target[1]+1)),sea)
        for xy in pixels:
            if atlas.getpixel(xy) in [1,2]:atlas.putpixel(xy,2)
        for dx,dy,c in [(0,-1,15),(-1,0,15),(0,0,0),(1,0,15)]:atlas.putpixel((target[0]+dx,target[1]+dy),c)
        if theme=='Artisan':
            h=re.sub(r'(MAP_NUM\(MAP_ARTISAN_CAVE_B1F\), MAPSEC_\w+, )\d+, \d+,',lambda m:m[1]+f'{target[0]}, {target[1]},',h)
        label=theme.upper()+' CAVE' if theme!='Artisan' else 'ARTISAN CAVE'
        h=re.sub(r'(MAP_NUM\('+chamber['id']+r'\), MAPSEC_\w+, )\d+, \d+,',lambda m:m[1]+f'{target[0]}, {target[1]},',h) if theme=='Artisan' else h[:h.index('};',h.index('sWorldPoints[]'))]+point_line(chamber,target,label)+h[h.index('};',h.index('sWorldPoints[]')):]
        end=h.index('};',h.index('sWorldPoints[]'));h=h[:end]+point_line(template,nearest,theme.upper()+' SEA')+h[end:]
        grid=[]
        # The seam's existing GPS is retained across the complete opening;
        # move continuously toward the new cave over the length of the route.
        for y in range(hh):
            for x in range(w):
                t=y if d in ['left','right'] else x
                px,py=edgepoint(pl['width'],pl['height'],d,off+t)
                oldp=int(grids[parent][py,px]);a=np.array([oldp&255,oldp>>8]);z=np.array(target)
                dist=(w-1-x if d=='left' else x if d=='right' else hh-1-y if d=='up' else y)
                length=(w-1-cx if d=='left' else cx if d=='right' else hh-1-cy if d=='up' else cy)
                p=np.rint(a+(z-a)*min(1,dist/max(1,length))).astype(int);grid.append(int(p[0])|(int(p[1])<<8))
        authored[n]=grid;chart['projections'].append(dict(map=n,id=template['id'],width=w,height=hh,center=target))
        chart['nodes'].append(dict(map=n,name=theme.upper()+' SEA',position=target))
        record=dict(source=parent,destination=n,direction=d,offset=off,polyline=[list(p) for p in corners],actual_connection=True)
        chart['routes'].append(record)
        if theme=='Coral':
            # This point lies inside an existing, fully connected route. Put
            # the beach on that route rather than inventing a distant detour
            # just because all four edges already have real neighbors.
            actual='JourneyWorldSea05';al=ls[maps[actual]['layout']];aw,ah=al['width'],al['height'];av=vals(actual);choices=[]
            for ay in range(9,ah-9):
                for ax in range(9,aw-9):
                    if all(av[(ay+dy)*aw+ax+dx]==0x112B for dx,dy in [(xx-cx,yy-cy) for xx,yy in land]):
                        gp=int(grids[actual][ay,ax]);choices.append((abs((gp&255)-target[0])+abs((gp>>8)-target[1]),ax,ay))
            _,ax,ay=min(choices)
            for xx,yy in land:av[(ay+yy-cy)*aw+ax+xx-cx]=v[yy*w+xx]
            warp_index=len(maps[actual]['warp_events']);maps[actual]['warp_events'].append(dict(x=ax,y=ay-2,elevation=3,dest_map=chamber['id'],dest_warp_id='0'))
            chamber['warp_events'][0].update(dest_map=maps[actual]['id'],dest_warp_id=str(warp_index))
            site=sanct['sites'][-1];site.update(surface=actual,entry=[ax,ay])
            cap.update(surface=actual)
            terrain[parent]=parent_before;maps[parent]['connections']=[c for c in maps[parent]['connections'] if c['map']!=template['id']]
            del terrain[n];del maps[n];ld['layouts'].remove(l);del ls[l['id']];groups['JourneyReviewCaves'].remove(n)
            chart['projections'].pop();chart['nodes'].pop();chart['routes'].pop();del authored[n]
            scripts=scripts.replace(f'\n\t.include "data/maps/{n}/scripts.inc"\n','')
            layer.outputs.pop(f'data/maps/{n}/scripts.inc');layer.outputs.pop(l['border_filepath'])
            h=re.sub(r'^.*MAP_NUM\('+template['id']+r'\).*?\n','',h,flags=re.M)
            # Keep the route cursor on the cave's actual island, without a
            # jump when entering. Lipschitz bounds preserve two pixels/step.
            from scipy.ndimage import distance_transform_cdt
            mask=np.ones((ah,aw),dtype=np.uint8)
            for xx,yy in land:mask[ay+yy-cy,ax+xx-cx]=0
            distance_field=distance_transform_cdt(mask,metric='taxicab')*2
            oldgrid=grids[actual];gx=np.clip(oldgrid&255,target[0]-distance_field,target[0]+distance_field);gy=np.clip(oldgrid>>8,target[1]-distance_field,target[1]+distance_field)
            authored[actual]=list(map(int,(gx|(gy<<8)).ravel()))
            n=actual;parent=actual;entry=[ax,ay-2];start=[int(grids[actual][ay,ax])&255,int(grids[actual][ay,ax])>>8];distance=0
        branches.append(dict(theme=theme,map=cname,surface=n,parent=parent,direction=d,offset=off,entry=entry,position=target,nearest_existing_ink=list(nearest),polyline=[list(p) for p in corners],species=altars,interior_template=interior if theme!='Artisan' else 'ArtisanCave_1F',altar_stand=[chamber['object_events'][0]['x'],chamber['object_events'][0]['y']+1] if theme!='Artisan' else [11,16],donor=donor if theme!='Artisan' else None,donor_before_count=donor_count if theme!='Artisan' else 0,existing_cave=theme=='Artisan',physical_parent_gps=start,closest_available_edge_distance=distance))
    nav=rebuild(nav,oldproj,chart['projections'],authored);nav,gps=reconcile(nav,chart['projections'],maps)
    layer.stage('src/data/journey_world_position.h',nav)
    detail=decode(h).resize((448,224),Image.Resampling.NEAREST)
    # Keep all native high-resolution land; update only changed route/icon pixels.
    olddetail=list(map(int,re.search(r'sWorldDetailPixels\[\] = \{([^}]+)',h)[1].split(',')))
    for y in range(112):
        for x in range(224):
            if atlas.getpixel((x,y))==before.getpixel((x,y)):continue
            for dy in [0,1]:
                for dx in [0,1]:
                    xx,yy=2*x+dx,2*y+dy;i=yy*224+xx//2;shift=(xx&1)*4
                    olddetail[i]=(olddetail[i]&~(15<<shift))|(atlas.getpixel((x,y))<<shift)
    h=encode(h,atlas);h=re.sub(r'(sWorldDetailPixels\[\] = \{)[^}]+',lambda m:m[1]+','.join(map(str,olddetail)),h)
    layer.stage('src/data/journey_world_map.h',h)
    for n,v in terrain.items():layer.stage(ls[maps[n]['layout']]['blockdata_filepath'],struct.pack('<'+'H'*len(v),*v))
    for n,m in maps.items():
        p=f'data/maps/{n}/map.json';raw=json.dumps(m,indent=2)+'\n'
        if not (s/p).exists() or json.loads((s/p).read_text())!=m:layer.stage(p,raw)
    layer.stage('data/layouts/layouts.json',json.dumps(ld,indent=2)+'\n');layer.stage('data/maps/map_groups.json',json.dumps(groups,indent=2)+'\n');layer.stage('data/event_scripts.s',scripts)
    for site in sanct['sites']:site['species_count']=sum(c['map']==site['map'] for c in sanct['captures'])
    return layer.finish(chart=chart,branches=branches,effective_sanctuaries=sanct,rock_art=art,mountain_repairs=mountain_repairs,boundaries=rims,gps=gps,foreign_rock_and_beach_aprons=True,normal_review_mode=0,review_mode_symbol='gJourneyReviewMode',all_original_ports_preserved=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);a=p.parse_args();r=prepare(a.source);print(json.dumps({k:r[k] for k in ['branches','rock_art','gps']},indent=2))
