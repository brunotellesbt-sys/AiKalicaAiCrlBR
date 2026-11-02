"""Fill real aquatic travel habitats while retaining ordinary-family ownership.

The current compiled-input headers are authoritative. Earlier ecology markers
only name the family/habitat owners; replaying their old tables would erase
later story, workshop, Tower and Lostelle changes.
"""
from collections import Counter, deque
import copy
import hashlib
import json
from pathlib import Path
import re
import struct

from aquatic_species import aquatic_ids
from badge_story_layer import read
from prepare_ecology import weighted_slots, LAND_RATES, WATER_RATES
from world_dex_locations import compile_locations

ROOT = Path(__file__).resolve().parents[2]
FIELDS = ('land_mons', 'water_mons', 'rock_smash_mons', 'fishing_mons', 'hidden_mons')
MARINE_ROOTS = {72,86,90,98,116,120,129,131,170,211,222,223,226,278,320,363,366,
                369,370,456,458,592,594,688,690,692,746,747,767,771,779,781,845,
                875,960,963,976}
DEEP_ROOTS = {72,116,170,223,320,366,369,456,592,594,779,976}
RIVER_ROOTS = {7,54,60,79,118,129,158,183,194,223,258,270,283,318,339,341,349,
               393,399,418,422,501,515,535,550,580,656,692,751,816,833,846,977,
               1286,1287,1288}
DEPTH_NAMES = {'JourneyDepth'+x for x in ('Abismo','Dimensoes','Mares','Origens','Profundezas')}
OUTDOOR = {'MAP_TYPE_ROUTE','MAP_TYPE_OCEAN_ROUTE','MAP_TYPE_CITY','MAP_TYPE_TOWN'}
NATIVE_QUIET_AQUATIC = {
    'Underwater_Route128': 'native underwater approach has ordinary floor and surfacing warp, no encounter terrain; preserved',
    'Underwater_SealedChamber': 'native underwater puzzle approach has ordinary floor and surfacing warp, no encounter terrain; preserved',
    'OneIsland_KindleRoad_EmberSpa_Frlg': 'healing spa waterfall is a special facility, not an ordinary Surf encounter habitat',
}


def parse_pools(text, array):
    pattern = r'(static const struct JourneyWildPool '+array+r'\[\]\s*=\s*\{\n)(.*?)(\n?\};)'
    match = re.search(pattern, text, re.S)
    assert match, array
    rows = {}
    for ident, area, count, members in re.findall(r'\{(MAP_\w+),\s*(\d+),\s*(\d+),\s*\{([^}]*)\}\}', match[2]):
        roots = re.findall(r'SPECIES_\w+', members)
        assert len(roots) == int(count)
        key = ident, int(area)
        assert key not in rows, key
        rows[key] = roots
    return rows, match


def write_pools(text, array, rows):
    _, match = parse_pools(text, array)
    body = '\n'.join('{'+ident+','+str(area)+','+str(len(roots))+',{'+','.join(roots)+'}},'
                     for (ident,area),roots in sorted(rows.items()))
    return text[:match.start(2)] + body + text[match.end(2):]


def parse_habitats(text):
    return {ident:set(re.findall(r'SPECIES_\w+', members))
            for ident, count, members in re.findall(r'\{(MAP_\w+),\s*(\d+),\s*\{([^}]*)\}\}', text)}


def write_habitats(rows, generation4=False, capacity=1):
    body = ''.join('{'+ident+','+str(len(members))+',{'+','.join(sorted(members))+'}},\n'
                   for ident,members in sorted(rows.items()))
    if generation4:
        return 'static const struct JourneyHabitat sJourneyGeneration4Habitats[]={\n'+body+'};\n'
    size = max(capacity, max(map(len,rows.values())))
    return ('struct JourneyHabitat {u16 map,count;u16 species['+str(size)+'];};\n'
            'static const struct JourneyHabitat sJourneyHabitats[]={\n'+body+'};\n')


def spatial_census(layer):
    layouts = {l['id']:l for l in json.loads(read(layer,'data/layouts/layouts.json'))['layouts']}
    maps = {p.parent.name:json.loads(read(layer,p.relative_to(layer.source).as_posix()))
            for p in (layer.source/'data/maps').glob('*/map.json')}
    by_id = {m['id']:name for name,m in maps.items()}
    definitions = read(layer,'src/data/tilesets/headers.h').decode()
    attributes = read(layer,'src/data/tilesets/metatiles.h').decode()
    cache, records, quiet = {}, [], []
    coast = read(layer,'src/journey_sevii_surf.c').decode()
    coast_ids = set(re.findall(r'case\s*\(MAP_GROUP\((MAP_\w+)\)',coast))
    for name,mapping in sorted(maps.items()):
        layout = layouts[mapping['layout']]
        version = layout['layout_version']; cutoff,size,mask = (640,4,511) if version=='frlg' else (512,2,255)
        tables=[]
        for key in ('primary_tileset','secondary_tileset'):
            symbol=layout[key]
            if (symbol,size) not in cache:
                body=re.search(r'const struct Tileset '+symbol+r'\s*=\s*\{(.*?)\};',definitions,re.S)[1]
                attr=re.search(r'\.metatileAttributes\s*=\s*(\w+)',body)[1]
                path=re.search(r'\b'+attr+r'\[\].*?"([^"]+)"',attributes)[1]
                data=read(layer,path)
                cache[symbol,size]=[int.from_bytes(data[i:i+size],'little')&mask for i in range(0,len(data),size)]
            tables.append(cache[symbol,size])
        raw=read(layer,layout['blockdata_filepath']); values=struct.unpack('<'+'H'*(len(raw)//2),raw)
        cells=[];behaviors=Counter()
        for index,value in enumerate(values):
            if value&0xC00:continue
            mid=value&1023
            behavior=tables[0 if mid<cutoff else 1][mid if mid<cutoff else mid-cutoff]
            # Native cycling-road/decorative water and waterfalls are not a
            # traversable Surf habitat. Fast coast water is explicitly opened.
            if behavior in {16,17,18,20,21,25,34,42,80,81,82,83} or (behavior==44 and mapping['id'] in coast_ids):
                cells.append([index%layout['width'],index//layout['width'],behavior]);behaviors[behavior]+=1
        if name in DEPTH_NAMES:
            cells=[[i%layout['width'],i//layout['width'],0] for i,v in enumerate(values) if not v&0xC00 and v&1023==0x216]
            behaviors=Counter({0:len(cells)})
        if not cells and name in NATIVE_QUIET_AQUATIC:
            accepted={19} if 'EmberSpa' in name else {0,108}
            for index,value in enumerate(values):
                if value&0xC00:continue
                mid=value&1023
                behavior=tables[0 if mid<cutoff else 1][mid if mid<cutoff else mid-cutoff]
                if behavior in accepted:
                    cells.append([index%layout['width'],index//layout['width'],behavior]);behaviors[behavior]+=1
        if not cells:continue
        reason=NATIVE_QUIET_AQUATIC.get(name)
        if reason:pass
        elif name=='JourneyHoennCrossing':reason='retired prototype without game connections'
        elif 'BattleFrontier' in name or 'SafariZone' in name:reason='native facility uses separate encounter rules'
        elif mapping['map_type'] not in OUTDOOR and not(name in DEPTH_NAMES or name.startswith('Underwater_Route')):
            reason='indoor, arrival room or special cave water; ordinary outdoor Surf habitat not applicable'
        if reason:
            quiet.append(dict(map=name,map_id=mapping['id'],reason=reason,water_cells=len(cells)))
            continue
        profile='depth' if mapping['map_type']=='MAP_TYPE_UNDERWATER' else 'river' if behaviors[16]>sum(behaviors.values())//2 else 'coast' if mapping['map_type'] in {'MAP_TYPE_CITY','MAP_TYPE_TOWN'} else 'open-sea'
        records.append(dict(map=name,map_id=mapping['id'],profile=profile,water_cells=len(cells),
                            water_behaviors=dict(sorted(behaviors.items())),sample_cells=cells[:12]))
    graph={m['id']:set() for m in maps.values()}
    for mapping in maps.values():
        for connection in mapping.get('connections') or []:
            target=connection['map']
            if target in graph:graph[mapping['id']].add(target);graph[target].add(mapping['id'])
    return records,quiet,maps,by_id,graph


def repair(layer):
    catalog=json.loads((ROOT/'tools/hoenn/catalog_metadata.json').read_text())
    species={int(i):row for i,row in catalog['species'].items()}
    by_name={s['name']:i for i,s in species.items()}
    aquatic=aquatic_ids(catalog['species'])
    marker=json.loads((layer.source/'.journey-final-ecology').read_bytes())
    locations={9:copy.deepcopy(marker['ecology']['locations_data']),4:copy.deepcopy(marker['generation4']['locations'])}
    owners={cap:{f['root']:h['section'] for h in hs for f in h['families']} for cap,hs in locations.items()}
    families={cap:{f['root']:f for h in hs for f in h['families']} for cap,hs in locations.items()}
    assert len(owners[9])==sum(len(h['families']) for h in locations[9])==424
    assert len(owners[4])==sum(len(h['families']) for h in locations[4])==212
    wild_path='include/journey_wild_data.h';g4_path='include/journey_generation4_pools.h'
    texts={9:read(layer,wild_path).decode(),4:read(layer,g4_path).decode()}
    arrays={9:'sJourneyWildPools',4:'sJourneyGeneration4Pools'}
    pools={cap:parse_pools(text,arrays[cap])[0] for cap,text in texts.items()}
    original_pools=copy.deepcopy(pools)
    habitat_paths={9:'include/journey_habitat_data.h',4:'include/journey_generation4_habitats.h'}
    original_habitat_texts={cap:read(layer,p).decode() for cap,p in habitat_paths.items()}
    habitats={cap:parse_habitats(text) for cap,text in original_habitat_texts.items()}
    event_dex={int(n) for n in re.search(r'eventDex\[\]\s*=\s*\{([^}]+)\}',read(layer,'src/journey_wild.c').decode())[1].split(',')}
    def usable(cap,roots):
        return bool(roots) and all(by_name.get(root) in aquatic and species[by_name[root]]['national_dex'] not in event_dex
            and (cap==9 or species[by_name[root]]['national_dex']<=493) for root in roots)
    targets,quiet,maps,by_id,graph=spatial_census(layer)
    encounters=json.loads(read(layer,'src/data/wild_encounters.json'))
    rows=encounters['wild_encounter_groups'][0]['encounters'];original_rows=copy.deepcopy(rows)
    by_map={}
    for row in rows:by_map.setdefault(row['map'],row)
    template=next(r for r in rows if r['map']=='MAP_ROUTE108')
    def donor(cap,ident,profile):
        candidates={m:r for (m,area),r in original_pools[cap].items() if area==1 and usable(cap,r)}
        preferred=DEEP_ROOTS if profile=='depth' else RIVER_ROOTS if profile=='river' else MARINE_ROOTS
        preferred_candidates={m:r for m,r in candidates.items() if all(by_name[root] in preferred for root in r)}
        if preferred_candidates:candidates=preferred_candidates
        seen={ident};queue=deque([(ident,0)]);distance={}
        while queue:
            at,steps=queue.popleft();distance[at]=steps
            for nxt in sorted(graph.get(at,())):
                if nxt not in seen:seen.add(nxt);queue.append((nxt,steps+1))
        region=maps[by_id[ident]].get('region')
        return min(candidates,key=lambda m:(distance.get(m,10000),maps[by_id[m]].get('region')!=region,m))
    reorganized={
        'MAP_JOURNEYHOENNMIDDLESEA':'MAP_ROUTE126',
        'MAP_JOURNEYHOENNSOUTHSEA':'MAP_SEVEN_ISLAND_TANOBY_RUINS',
    }
    # The northern open sea retains Tentacool in Gen9. Gen4 formerly
    # reused freshwater Wooper across all three seas; the nearby Route107
    # Tentacool habitat supplies the northern marine corridor instead.
    reorganized_by_cap={4:dict(reorganized, MAP_JOURNEYHOENNNORTHSEA='MAP_ROUTE107'),
                        9:reorganized}
    fishing_new={};report=[]
    before_missing={4:0,9:0};new_headers=0
    for target in targets:
        ident=target['map_id'];name=target['map'];profile=target['profile']
        row=by_map.get(ident)
        if row is None:
            row=dict(map=ident,base_label='gCoastalEcology_'+name);rows.append(row);by_map[ident]=row;new_headers+=1
        # Native seaweed and the five new normal-floor depths both use water
        # records. Existing terrestrial fields remain unchanged everywhere.
        area=1
        field=FIELDS[area]
        target['area']=area;target['fields']=[field];target['variants']={}
        for cap in (4,9):
            old=pools[cap].get((ident,area),[])
            missing=not row.get(field) or not usable(cap,old)
            before_missing[cap]+=missing
            selected=None
            if area==1 and (missing or ident in reorganized_by_cap[cap]):
                selected=reorganized_by_cap[cap].get(ident)
                if selected is None or not usable(cap,original_pools[cap].get((selected,1),[])):
                    selected=donor(cap,ident,profile)
                pools[cap][ident,area]=original_pools[cap][selected,1].copy()
            roots=pools[cap].get((ident,area),[])
            assert usable(cap,roots),(cap,ident,area,roots)
            owners_used=sorted({owners[cap][by_name[r]] for r in roots})
            # All roots retain exactly one established habitat ID. Extending
            # its maps does not duplicate that family into another habitat.
            for section in owners_used:
                owner=next(h for h in locations[cap] if h['section']==section)
                if ident not in owner['maps']:owner['maps'].append(ident);owner['maps'].sort()
            members=set()
            for root in roots:
                family=families[cap][by_name[root]]
                members.update(s['name'] for s in family['species'] if s['id'] in aquatic and
                               (cap==9 or s['national_dex']<=493))
            habitats[cap].setdefault(ident,set()).update(members)
            target['variants'][str(cap)]=dict(roots=roots,habitat_ids=owners_used,donor=selected,
                previously_missing=missing,ordinary_aquatic_members=sorted(members))
        if area==1:
            roots9=pools[9][ident,1];unique=list(dict.fromkeys(roots9))
            family9=[families[9][by_name[root]] for root in unique]
            slots=weighted_slots(family9,WATER_RATES)
            rate=min(6 if profile=='river' else 5 if profile=='depth' else 4,
                     [8,6,3,1][min(f['rarity'] for f in family9)])
            if not row.get(field) or target['variants']['9']['previously_missing'] or ident in reorganized:
                row[field]=copy.deepcopy(template['water_mons'])
                row[field]['encounter_rate']=rate
                for mon,root in zip(row[field]['mons'],slots):mon['species']=species[root]['name']
            if maps[name]['map_type']!='MAP_TYPE_UNDERWATER':
                target['fields'].append('fishing_mons')
                for cap in (4,9):
                    if not usable(cap,pools[cap].get((ident,3),[])) or ident in reorganized_by_cap[cap]:
                        pools[cap][ident,3]=pools[cap][ident,1].copy()
                if not row.get('fishing_mons') or target['variants']['9']['previously_missing'] or ident in reorganized:
                    row['fishing_mons']=copy.deepcopy(template['fishing_mons'])
                    slots=[]
                    for weights in ([70,30],[60,20,20],[40,40,15,4,1]):
                        slots+=weighted_slots(family9[:len(weights)],weights)
                    for mon,root in zip(row['fishing_mons']['mons'],slots):mon['species']=species[root]['name']
                    fishing_new[ident]=[100,75,40,15][min(f['rarity'] for f in family9)]
        target['rate']=row[field]['encounter_rate']
        report.append(target)
    # Removing a family from a deliberately reassigned sea must also remove
    # its ordinary habitat/Dex claim there. Other maps, fixed encounters and
    # workshop locations remain authoritative and are never regenerated.
    displaced={}
    for cap,changes in reorganized_by_cap.items():
        for ident in changes:
            old_roots={root for (mapping,area),roots in original_pools[cap].items()
                       if mapping==ident and area in (1,3) for root in roots}
            active_roots={root for (mapping,area),roots in pools[cap].items()
                          if mapping==ident for root in roots}
            removed=old_roots-active_roots
            # A displaced aquatic family can include non-Water regional
            # forms already declared in the old habitat (Wooper Paldea).
            # Remove its whole ordinary family claim, not only swimmers.
            members={member['name'] for root in removed
                     for member in families[cap][by_name[root]]['species']
                     if cap==9 or member['national_dex']<=493}
            if members:
                habitats[cap][ident]-=members
                displaced[cap,ident]=members
            active_owners={owners[cap][by_name[root]] for root in active_roots}
            for section in {owners[cap][by_name[root]] for root in removed}-active_owners:
                owner=next(h for h in locations[cap] if h['section']==section)
                if ident in owner['maps']:owner['maps'].remove(ident)

    # Some native map IDs have multiple native header variants. The first is
    # the active default; give every variant the same aquatic habitat while
    # preserving each variant's distinct terrestrial and scripted fields.
    target_ids={r['map_id'] for r in report}
    for row in rows:
        if row['map'] not in target_ids or row is by_map[row['map']]:continue
        for field in ('water_mons','fishing_mons'):
            if field in by_map[row['map']]:row[field]=copy.deepcopy(by_map[row['map']][field])
    # Lossless unrelated-field guarantee, including late story modifications.
    for index,old in enumerate(original_rows):
        current=rows[index]
        for field in ('land_mons','rock_smash_mons','hidden_mons'):
            assert current.get(field)==old.get(field),(old['map'],field)
    for cap in (4,9):
        for key,roots in original_pools[cap].items():
            if key[1] not in (1,3):assert pools[cap][key]==roots,key
        before_roots={r for roots in original_pools[cap].values() for r in roots}
        after_roots={r for roots in pools[cap].values() for r in roots}
        assert before_roots<=after_roots,('Existing family lost',cap,before_roots-after_roots)
    for cap,path in ((9,wild_path),(4,g4_path)):
        text=write_pools(texts[cap],arrays[cap],pools[cap])
        if cap==9:
            pattern=r'(static const struct JourneyFishingHabitat sJourneyFishingHabitats\[\]\s*=\s*\{\n)(.*?)(\n\};)'
            match=re.search(pattern,text,re.S);assert match
            rates={m:int(rate) for m,rate in re.findall(r'\{(MAP_\w+),\s*(\d+)\}',match[2])}
            for m,rate in fishing_new.items():rates.setdefault(m,rate)
            body=',\n'.join('{'+m+','+str(rate)+'}' for m,rate in sorted(rates.items()))
            text=text[:match.start(2)]+body+text[match.end(2):]
        layer.stage(path,text)
    h4=write_habitats(habitats[4],True)
    capacity=max(max(map(len,habitats[4].values())),int(re.search(r'species\[(\d+)\]',original_habitat_texts[9])[1]))
    h9=write_habitats(habitats[9],capacity=capacity)
    layer.stage(habitat_paths[4],h4);layer.stage(habitat_paths[9],h9)
    layer.stage('src/data/wild_encounters.json',json.dumps(encounters,indent=2)+'\n')
    # Preserve prior fixed/workshop and unaffected ordinary Dex records.
    # Remove only displaced ordinary claims and append new aquatic locations
    # computed from the current atlas; never replay an old Dex file.
    additions,_=compile_locations(layer.source,{4:h4,9:h9})
    path='src/data/journey_world_dex_locations.h';old=read(layer,path).decode()
    removed_dex=[]
    for match in re.finditer(r'\{(SPECIES_\w+),(MAP_\w+),(\d+),(\d+),(\d+),(\d+)\}',old):
        species_name,ident,_,_,fixed,cap=match.groups()
        if fixed=='0' and species_name in displaced.get((int(cap),ident),set()):
            removed_dex.append(match[0])
    for row in removed_dex:old=old.replace(row+',\n','')
    old_rows=set(re.findall(r'\{SPECIES_\w+,[^{}]+\}',old))
    new_rows=set(re.findall(r'\{SPECIES_\w+,[^{}]+\}',additions))
    extra=sorted(new_rows-old_rows)
    assert old.rstrip().endswith('};')
    text=old.rstrip()[:-2]+''.join(row+',\n' for row in extra)+'};\n'
    layer.stage(path,text)
    from coastal_ecology_runtime import repair as runtime_repair
    runtime=runtime_repair(layer)
    return dict(kind='coastal-ecology-encounters',targets=report,quiet_exceptions=quiet,
        targeted_maps=len(report),new_native_headers=new_headers,
        previously_missing_effective_water_by_generation=before_missing,
        locations_data=locations,ordinary_families_by_generation={cap:len(owners[cap]) for cap in owners},
        no_family_repeated_between_habitat_ids=True,all_previous_pool_roots_remain_reachable=True,
        all_unaffected_land_rock_hidden_fields_and_pools_preserved=True,
        previous_fixed_and_workshop_dex_records_preserved=True,additional_dex_records=len(extra),
        removed_stale_ordinary_dex_records=removed_dex,
        removed_stale_aquatic_habitat_members=[dict(cap=cap,map_id=ident,members=sorted(members))
            for (cap,ident),members in sorted(displaced.items())],
        reorganized_maps=sorted(set().union(*(set(rows) for rows in reorganized_by_cap.values()))),
        reorganized_by_generation=reorganized_by_cap,runtime=runtime,
        review_mode_guard_unchanged=True,geometry_and_atlas_unchanged=True)
