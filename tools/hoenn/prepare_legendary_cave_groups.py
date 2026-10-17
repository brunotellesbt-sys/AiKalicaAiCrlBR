"""Place each complete legendary family in a named existing cave chamber."""
import copy,json,re,struct
from collections import Counter,deque
from pathlib import Path
from render_sea_maps import MapRenderer
from prepare_world_dex_map import PAT


def prepare_groups(layer):
    s=layer.source;plan=json.loads((Path(__file__).parent/'data/legendary-cave-groups.json').read_text())
    maps={p.parent.name:json.loads(p.read_text()) for p in (s/'data/maps').glob('*/map.json')}
    original=copy.deepcopy(maps);ls={l['id']:l for l in json.loads((s/'data/layouts/layouts.json').read_text())['layouts']}
    captures={c['national_dex']:c for c in json.loads((s/'.journey-sanctuaries').read_text())['captures']}
    assert sorted(n for g in plan for n in g['national_dex'])==sorted(captures)
    objects={};changed=set();renderer=MapRenderer(s)
    for n,m in maps.items():
        keep=[]
        for o in m.get('object_events',[]):
            match=re.fullmatch(r'JourneySanctuary_(\d+)',o.get('script',''))
            if match:
                dex=int(match[1]);assert dex not in objects;objects[dex]=copy.deepcopy(o);changed.add(n)
            else:keep.append(o)
        m['object_events']=keep
    assert set(objects)==set(captures)
    def read(p):return layer.outputs.get(p,(s/p).read_bytes())
    header=read('src/data/journey_world_map.h').decode();points={m[1]:[int(m[3]),int(m[4])] for m in re.finditer(PAT,header)}
    area=read('src/pokedex_area_screen.c').decode();dexmap=read('src/data/journey_world_dex_locations.h').decode()
    placements=[]
    for g in plan:
        n=g['map'];m=maps[n];l=ls[m['layout']];w,h=l['width'],l['height'];raw=(s/l['blockdata_filepath']).read_bytes();blocks=struct.unpack('<'+'H'*(w*h),raw)
        occupied={(o['x'],o['y']) for k in ['object_events','warp_events','coord_events','bg_events'] for o in m.get(k,[]) if isinstance(o.get('x'),int)}
        passable={(i%w,i//w) for i,v in enumerate(blocks) if not v&0xC00}
        start=(m['warp_events'][0]['x'],m['warp_events'][0]['y']);q=deque([start]);seen={start}
        while q:
            x,y=q.popleft()
            for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                p=x+dx,y+dy
                if p in passable and p not in seen:seen.add(p);q.append(p)
        # Favor ordinary, connected cave floor, away from doors and all native NPCs.
        freq=Counter(blocks[y*w+x]&1023 for x,y in seen if (x,y) in passable)
        cut=640 if l['layout_version']=='frlg' else 512
        attrs=[]
        for bank in [l['primary_tileset'],l['secondary_tileset']]:
            info=re.search(r'const struct Tileset '+bank+r'\s*=\s*\{(.*?)\};',renderer.headers,re.S)[1]
            sym=re.search(r'\.metatileAttributes\s*=\s*(\w+)',info)[1]
            path=re.search(r'\b'+sym+r'\[\].*?"([^"]+)"',renderer.metas,re.S)[1]
            attrs.append((s/path).read_bytes())
        def ordinary(x,y):
            mid=blocks[y*w+x]&1023;size=4 if cut==640 else 2;bank=mid>=cut;index=mid-cut if bank else mid
            return (int.from_bytes(attrs[bank][index*size:(index+1)*size],'little')&(511 if cut==640 else 255)) in (0,8,11,12)
        candidates=[(x,y) for x,y in seen if 1<=x<w-1 and 1<=y<h-1 and ordinary(x,y) and (x,y+1) in seen and (x,y+1) in passable and not any(abs(x-a)+abs(y-b)<3 for a,b in occupied)]
        assert len(candidates)>=len(g['national_dex']),(n,len(candidates))
        selected=[]
        for num in g['national_dex']:
            choice=max(candidates,key=lambda p:(min([abs(p[0]-a)+abs(p[1]-b) for a,b in selected]+[99]),freq[blocks[p[1]*w+p[0]]&1023],abs(p[0]-start[0])+abs(p[1]-start[1]),-p[1],-p[0]))
            x,y=choice;selected.append(choice);candidates=[p for p in candidates if abs(p[0]-x)+abs(p[1]-y)>=3]
            o=objects[num];oldmap=next(mm for mm in original.values() if any(z.get('script')==o['script'] for z in mm.get('object_events',[])))
            o.update(x=x,y=y,elevation=blocks[y*w+x]>>12);m['object_events'].append(o)
            cap=captures[num];species=cap['species']
            pattern=r'(if \(species == '+species+r'\b.*?SetSpecialMapHasMon\([^;]+;)'
            area,count=re.subn(pattern,lambda z:z[0].replace(oldmap['id'],m['id']),area,flags=re.S);assert count==1,(num,count)
            xy=points[m['id']]
            dexmap,count=re.subn(r'\{'+species+r',MAP_\w+,\d+,\d+,1,0\}', '{'+species+','+m['id']+f',{xy[0]},{xy[1]},1,0'+'}',dexmap);assert count==1,(species,'dex')
            placements.append(dict(national_dex=num,species=species,map=n,name=g['name'],position=[x,y],flag=o['flag'],script=o['script'],original_map=oldmap['name']))
        m['show_map_name']=True;changed.add(n)
        assert len(m['object_events'])<=32,(n,'too many objects')
        pattern=next(z[0] for z in re.finditer(PAT,header) if z[1]==m['id'])
        header=header.replace(pattern,re.sub(r'COMPOUND_STRING\("[^"]+"\)',lambda _:f'COMPOUND_STRING("{g["name"]}")',pattern))
    for n in changed:
        assert maps[n]['warp_events']==original[n]['warp_events']
        layer.stage(f'data/maps/{n}/map.json',json.dumps(maps[n],indent=2)+'\n')
    layer.stage('src/data/journey_world_map.h',header)
    layer.stage('src/pokedex_area_screen.c',area)
    layer.stage('src/data/journey_world_dex_locations.h',dexmap)
    return dict(groups=plan,placements=placements,total=105,cave_count=len(plan),maximum_per_chamber=max(len(g['national_dex']) for g in plan),
                existing_cave_terrain_and_all_entrances_preserved=True,all_capture_flags_and_scripts_preserved=True,
                giratina_ship_battle_preserved_uncapturable=True,galactic_trio_released_to_creation_cave=True)
