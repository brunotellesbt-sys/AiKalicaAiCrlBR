"""Make the three charted eastern islets real landing sites with unique habitats."""
import argparse, copy, hashlib, json, math, re, struct
from pathlib import Path
from PIL import Image, ImageDraw
from prepare_kanto_open_sea import CHAIN, LAYER as COAST
from prepare_ecology import FIELDS, LAND_RATES, WATER_RATES, weighted_slots

ROOT = Path(__file__).resolve().parents[2]
LAYER = 'remote-islands'
PRIOR = CHAIN + [COAST, 'coastal-world-map']
SITES = [
    ('JourneyWorldSea05', 'EMERALD CAY', 'MAPSEC_EMERALD_CAY', 176, 72, 4, 3),
    ('JourneyWorldSea08', 'SUNLIT ISLE', 'MAPSEC_SUNLIT_ISLE', 187, 77, 9, 6),
    ('JourneyWorldSea09', 'TIDEWOOD ISLE', 'MAPSEC_TIDEWOOD_ISLE', 190, 90, 9, 6),
]

def prepare(source):
    source = Path(source); marker = source / ('.journey-' + LAYER)
    if marker.exists():
        r = json.loads(marker.read_text())
        for p, h in (r['prepared_sha256'] | r['preserved_native_sha256']).items():
            assert hashlib.sha256((source / p).read_bytes()).hexdigest() == h, p
        return r
    acquired = json.loads((source / '.source-acquired.json').read_text())
    expected = dict(acquired['sha256'])
    for layer in PRIOR:
        expected.update(json.loads((source / ('.journey-' + layer)).read_text())['prepared_sha256'])
    originals, preserved, outputs = {}, {}, {}
    def read(p):
        raw = (source / p).read_bytes(); h = hashlib.sha256(raw).hexdigest()
        assert h == expected[p], p
        preserved[p] = h
        return raw
    def stage(p, value):
        originals[p] = hashlib.sha256(read(p)).hexdigest(); preserved.pop(p, None)
        outputs[p] = value if isinstance(value, bytes) else value.encode()
    layouts = {l['id']: l for l in json.loads(read('data/layouts/layouts.json'))['layouts']}
    sections = json.loads(read('src/data/region_map/region_map_sections.json'))
    sites = []
    for name, label, section, atlas_x, atlas_y, rx, ry in SITES:
        path = f'data/maps/{name}/map.json'; m = json.loads(read(path)); lay = layouts[m['layout']]
        w, h = lay['width'], lay['height']; raw = read(lay['blockdata_filepath'])
        v = list(struct.unpack('<' + 'H' * (w*h), raw)); reserved = set()
        for key in ['object_events', 'warp_events', 'coord_events', 'bg_events']:
            for e in m[key]:
                reserved.update((e['x']+dx, e['y']+dy) for dx in range(-2,3) for dy in range(-2,3))
        # Keep old Seafoam mountains, NPC beaches, Dive patches and all seams.
        # The new island occupies previously open water, away from the central lane.
        land = None
        for cy in range(h-ry-5, ry+4, -1):
            for cx in range(rx+4, w//2-rx-2):
                patch = set()
                for y in range(cy-ry-2,cy+ry+3):
                    for x in range(cx-rx-2,cx+rx+3):
                        a=math.atan2((y-cy)/ry,(x-cx)/rx)
                        edge=1+.18*math.sin(3*a+.7)+.11*math.cos(5*a+.3)
                        if ((x-cx)/rx)**2+((y-cy)/ry)**2 < edge**2: patch.add((x,y))
                if any(min(x,y,w-1-x,h-1-y)<3 or (x,y) in reserved or v[y*w+x] != 0x112B for x,y in patch): continue
                land=patch; break
            if land: break
        assert land, ('No safe island footprint', name)
        shore=[0x10C,0x10D,0x10E,0x114,0x115,0x116,0x11C,0x11D,0x11E]; grass=[]
        for x,y in land:
            row=0 if (x,y-1) not in land else 2 if (x,y+1) not in land else 1
            col=0 if (x-1,y) not in land else 2 if (x+1,y) not in land else 1
            v[y*w+x]=0x3000+shore[row*3+col]
            if all((x+dx,y+dy) in land for dx,dy in [(0,-1),(0,1),(-1,0),(1,0)]):
                v[y*w+x]=0x300D; grass.append([x,y])
        assert grass
        m['region_map_section']=section
        stage(path,json.dumps(m,indent=2)+'\n'); stage(lay['blockdata_filepath'],struct.pack('<'+'H'*len(v),*v))
        sections['map_sections'].append(dict(id=section,name=label,x=19+len(sites),y=11,width=1,height=1))
        sites.append(dict(map=name,id=m['id'],name=label,section=section,x=atlas_x,y=atlas_y,
                          landing=min([list(p) for p in land],key=lambda p:(p[1],p[0])),grass=grass,
                          connections_preserved=True,original_npcs_and_caves_preserved=True))
    stage('src/data/region_map/region_map_sections.json',json.dumps(sections,indent=2)+'\n')

    # New sections must remain in Kanto: this selects FRLG map behavior, avatars,
    # palettes and the correct region after continuous Surf and Save/Continue.
    p='include/regions.h';body=read(p).decode();body=body.replace('sectionId == MAPSEC_LAVENDER_PORT ||',
        'sectionId == MAPSEC_LAVENDER_PORT || sectionId == MAPSEC_EMERALD_CAY || sectionId == MAPSEC_SUNLIT_ISLE || sectionId == MAPSEC_TIDEWOOD_ISLE ||');stage(p,body)
    p='src/regions.c';body=read(p).decode();body=body.replace('        MAPSEC_FIVE_ISLAND,','        MAPSEC_FIVE_ISLAND,\n        MAPSEC_EMERALD_CAY,',1)
    body=body.replace('        MAPSEC_BIRTH_ISLAND_FRLG,','        MAPSEC_BIRTH_ISLAND_FRLG,\n        MAPSEC_SUNLIT_ISLE,\n        MAPSEC_TIDEWOOD_ISLE,',1);stage(p,body)


    ecology=copy.deepcopy(json.loads((source/'.journey-tower-habitats').read_text()))
    habitats=ecology['locations_data']; catalog=json.loads((ROOT/'tools/hoenn/catalog_metadata.json').read_text())
    species={int(k):v for k,v in catalog['species'].items()}
    five=next(h for h in habitats if 'MAP_FIVE_ISLAND' in h['maps'])
    tiny=next(f for f in five['families'] if f['name']=='SPECIES_MORELULL')
    five['families'].remove(tiny);five['maps'].remove('MAP_JOURNEYWORLDSEA05')
    sun=next(h for h in habitats if h['maps']==['MAP_JOURNEYWORLDSEA08'])
    sun['section']='MAPSEC_SUNLIT_ISLE'
    green=dict(section='MAPSEC_EMERALD_CAY',maps=['MAP_JOURNEYWORLDSEA05'],families=[tiny],land=True,water=False)
    tide=dict(section='MAPSEC_TIDEWOOD_ISLE',maps=['MAP_JOURNEYWORLDSEA09'],families=[],land=True,water=False)
    habitats += [green,tide]
    moved=[]
    for target, wanted in [(sun,8),(tide,8)]:
        while len(target['families'])<wanted:
            choices=[(h,f) for h in habitats if h['section'].startswith('MAPSEC_ROUTE_') and len(h['families'])>=3
                     for f in h['families'] if f['root']>400 and 12 not in f['types']]
            assert choices
            donor,f=max(choices,key=lambda hf:(sum(t in hf[1]['types'] for t in [13,7,3,0]),len(hf[0]['families']),-hf[1]['rarity'],-hf[1]['root']))
            donor['families'].remove(f); target['families'].append(f)
            moved.append(dict(root=f['root'],family=f['name'],old_section=donor['section'],section=target['section']))
    for h in habitats:h['family_count']=len(h['families'])
    roots=[f['root'] for h in habitats for f in h['families']]
    assert len(roots)==len(set(roots))==444
    bymap={m:h for h in habitats for m in h['maps']}
    encounters=json.loads(read('src/data/wild_encounters.json'));rows=encounters['wild_encounter_groups'][0]['encounters']
    template=copy.deepcopy(next(e['land_mons'] for e in rows if e['map']=='MAP_ROUTE101'))
    if not any(e['map']=='MAP_JOURNEYWORLDSEA09' for e in rows):rows.append(dict(map='MAP_JOURNEYWORLDSEA09',base_label='gTidewoodIsle',land_mons=copy.deepcopy(template)))
    for row in rows:
        if row['map'] in {s['id'] for s in sites}:row.setdefault('land_mons',copy.deepcopy(template))
    pools=[];members={};slots={}
    for row in rows:
        if row['map'] not in bymap:continue
        h=bymap[row['map']];slots[row['map']]={};ids=set()
        for area,field in enumerate(FIELDS):
            if field not in row:continue
            fs=h['families'] if field not in ['water_mons','fishing_mons'] else [f for f in h['families'] if 12 in f['types']]
            if not fs:del row[field];continue
            if field=='fishing_mons':
                rr=[]
                for rates in [[70,30],[60,20,20],[40,40,15,4,1]]:rr+=weighted_slots(sorted(fs,key=lambda f:(f['rarity'],f['root']))[:len(rates)],rates)
            else:
                rates=(LAND_RATES if field in ['land_mons','hidden_mons'] else WATER_RATES)[:len(row[field]['mons'])]
                rr=weighted_slots(fs[:len(rates)],rates)
            for mon,root in zip(row[field]['mons'],rr):mon['species']=species[root]['name']
            slots[row['map']][field]=dict(slots=[species[i]['name'] for i in rr])
            pools.append(dict(map=row['map'],area=area,roots=weighted_slots(fs,LAND_RATES)))
            ids.update(m['id'] for f in fs for m in f['species'])
        members[row['map']]=sorted(ids)
    wild=read('include/journey_wild_data.h').decode()
    poolbody=',\n'.join('{'+', '.join([p['map'],str(p['area']),str(len(p['roots'])),'{'+', '.join(species[i]['name'] for i in p['roots'])+'}'])+'}' for p in sorted(pools,key=lambda p:(p['map'],p['area'])))
    wild,count=re.subn(r'(static const struct JourneyWildPool sJourneyWildPools\[\] = \{\n).*?(\n\};)',lambda m:m[1]+poolbody+m[2],wild,flags=re.S);assert count==1
    stage('include/journey_wild_data.h',wild)
    maxcount=max(map(len,members.values()));dex='struct JourneyHabitat { u16 map, count; u16 species['+str(maxcount)+']; };\nstatic const struct JourneyHabitat sJourneyHabitats[] = {\n'
    dex+=',\n'.join('{'+m+', '+str(len(ids))+', {'+', '.join(species[i]['name'] for i in ids)+'}}' for m,ids in sorted(members.items()))+'\n};\n'
    stage('include/journey_habitat_data.h',dex);stage('src/data/wild_encounters.json',json.dumps(encounters,indent=2)+'\n')

    # Edit the same native palette/tile screen; this is not a browser overlay.
    old=read('src/data/journey_world_map.h').decode()
    def values(key):return [int(n) for n in re.search(key+r'\[\] = \{([^}]+)\}',old)[1].split(',')]
    palette=values('sWorldPalette');colors=[((n&31)*8,((n>>5)&31)*8,((n>>10)&31)*8) for n in palette]
    # Match the original quantization palette's exact RGB values for the PNG.
    colors=[(16,24,32),(112,184,232),(48,104,176),(24,112,0),(48,152,0),(80,200,0),(120,224,0),(184,240,64),(216,248,112),(184,120,8),(224,168,16),(248,208,56),(248,232,136),(248,72,24),(248,248,240),(96,80,72)]
    tilebytes=bytes(values('sWorldTiles'));tilemap=values('sWorldTilemap');im=Image.new('P',(224,112));im.putpalette([v for c in colors for v in c]+[0]*720)
    for ty in range(14):
        for tx in range(28):
            tile=tilemap[(ty+3)*32+tx+1]*32
            for y in range(8):
                for x in range(0,8,2):
                    b=tilebytes[tile+y*4+x//2];im.putpixel((tx*8+x,ty*8+y),b&15);im.putpixel((tx*8+x+1,ty*8+y),b>>4)
    draw=ImageDraw.Draw(im)
    for line in [[(176,60),(176,80)],[(167,72),(176,72)],[(187,77),(187,100)],[(187,90),(199,90)]]:
        overlay=im.copy();ImageDraw.Draw(overlay).line(line,fill=2,width=2)
        for y in range(im.height):
            for x in range(im.width):
                if im.getpixel((x,y)) in [1,2]:im.putpixel((x,y),overlay.getpixel((x,y)))
    for site in sites:
        x,y=site['x'],site['y'];draw.rectangle((x-1,y-1,x+1,y+1),fill=14);draw.point((x,y),fill=1)
        pat=r'\{\(MAP_GROUP\('+site['id']+r'\).*?COMPOUND_STRING\("[^"]+"\)\},'
        replacement='{(MAP_GROUP('+site['id']+')<<8)|MAP_NUM('+site['id']+'), '+site['section']+', '+str(x)+', '+str(y)+', COMPOUND_STRING("'+site['name']+'")},'
        old,count=re.subn(pat,lambda m:replacement,old);assert count==1,site['map']
    tiles=[bytes(32)];lookup={tiles[0]:0};tm=[0]*1024
    for ty in range(14):
        for tx in range(28):
            tile=bytes(im.getpixel((tx*8+x,ty*8+y))|(im.getpixel((tx*8+x+1,ty*8+y))<<4) for y in range(8) for x in range(0,8,2))
            if tile not in lookup:lookup[tile]=len(tiles);tiles.append(tile)
            tm[(ty+3)*32+tx+1]=lookup[tile]
    for key,vals in [('sWorldTiles',b''.join(tiles)),('sWorldTilemap',tm)]:
        old,count=re.subn(r'('+key+r'\[\] = \{)[^}]+(\})',lambda m:m[1]+','.join(map(str,vals))+m[2],old);assert count==1
    stage('src/data/journey_world_map.h',old)
    for p in ['src/journey_wild.c','src/journey_campaign_gates.c','src/journey_gym_scaling.c','src/journey_world_map.c','data/layouts/JourneyRoute12Shipyard/map.bin']:read(p)
    report=dict(layer=LAYER,sites=sites,moved_families=moved,locations_data=habitats,map_species=members,pools=pools,field_slots=slots,
                ordinary_families=444,no_family_repeated_between_locations=True,level_and_stage_rules_preserved=True,
                original_sha256=originals,preserved_native_sha256=preserved,prepared_sha256={p:hashlib.sha256(v).hexdigest() for p,v in outputs.items()})
    for p,raw in outputs.items():(source/p).write_bytes(raw)
    marker.write_text(json.dumps(report,indent=2)+'\n')
    im.convert('RGB').resize((896,448),Image.Resampling.NEAREST).save(ROOT/'mods/hoenn/world-map-gallery/world-map-art.png')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);a=p.parse_args();print(json.dumps(prepare(a.source),indent=2))
