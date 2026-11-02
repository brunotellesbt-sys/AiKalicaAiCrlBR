"""Audit compiled aquatic encounters and exercise genuine controller encounters.

The census reads the native ABI, ROM tables and tile attributes. Initial map,
party and story setup are declared fixtures; native encounter cases never
disable encounters, set Repel or write an encounter/battle result.
"""
import argparse
from collections import Counter
import ctypes
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
EVENT_DEX = {137,138,139,140,141,142,201,233,345,346,347,348,351,408,409,
             410,411,442,474,479,564,565,566,567,696,697,698,699,880,881,
             882,883,999,1000}
AREAS = ['land_mons','water_mons','rock_smash_mons','fishing_mons','hidden_mons']
COUNTS = [12,5,5,10,3]
DEPTH_NAMES = {'JourneyDepth'+name for name in ('Abismo','Dimensoes','Mares','Origens','Profundezas')}
OUTDOOR = {'MAP_TYPE_ROUTE','MAP_TYPE_OCEAN_ROUTE','MAP_TYPE_CITY','MAP_TYPE_TOWN'}


def eligibility(name,map_type,behaviors,retired=False):
    """Classify real outdoor water independently of header/pool presence."""
    if retired:return False,'retired prototype without game connections'
    if 'BattleFrontier' in name or 'SafariZone' in name:
        return False,'native facility uses separate encounter rules'
    if not any(b in {16,17,18,20,21,25,34,42,44,80,81,82,83} for b in behaviors) and name not in DEPTH_NAMES:
        return False,'only waterfall/warp water or native underwater floor without a habitat tile'
    if map_type not in OUTDOOR and not(name in DEPTH_NAMES or name.startswith('Underwater_Route')):
        return False,'indoor, arrival room or special cave water; ordinary outdoor Surf habitat not applicable'
    return True,None


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def framebuffer_visibility(pixels):
    """Reject blank/faded frames before treating a menu capture as evidence."""
    assert len(pixels)==240*160*4, 'Unexpected native framebuffer dimensions'
    colors=Counter(tuple(pixels[i:i+3]) for i in range(0,len(pixels),4))
    lit=sum(count for color,count in colors.items() if max(color)>8)
    assert len(colors)>=16 and lit>=240*160//4, ('Native capture is blank or faded',len(colors),lit)
    return dict(framebuffer_distinct_rgb_colors=len(colors),framebuffer_nonblack_pixels=lit)


def build_abi(source):
    source = Path(source)
    code = (source/'src/journey_wild.c').read_text()
    structs = '\n'.join(re.search(r'struct '+name+r'\s*\{[^}]+\};',code)[0]
                        for name in ['JourneyWildPool','JourneyWildStages'])
    expressions = {
        'header_size':'sizeof(struct WildPokemonHeader)',
        'header_types':'offsetof(struct WildPokemonHeader,encounterTypes)',
        'time_count':'TIMES_OF_DAY_COUNT',
        'time_enabled':'OW_TIME_OF_DAY_ENCOUNTERS',
        'time_fallback':'OW_TIME_OF_DAY_FALLBACK',
        'time_disable_fallback':'OW_TIME_OF_DAY_DISABLE_FALLBACK',
        'types_size':'sizeof(struct WildEncounterTypes)',
        **{f'types_{field}':f'offsetof(struct WildEncounterTypes,{native})'
           for field,native in zip(AREAS,['landMonsInfo','waterMonsInfo','rockSmashMonsInfo','fishingMonsInfo','hiddenMonsInfo'])},
        'info_size':'sizeof(struct WildPokemonInfo)',
        'info_rate':'offsetof(struct WildPokemonInfo,encounterRate)',
        'info_slots':'offsetof(struct WildPokemonInfo,wildPokemon)',
        'slot_size':'sizeof(struct WildPokemon)',
        'slot_species':'offsetof(struct WildPokemon,species)',
        'pool_size':'sizeof(struct JourneyWildPool)',
        'pool_map':'offsetof(struct JourneyWildPool,map)',
        'pool_area':'offsetof(struct JourneyWildPool,area)',
        'pool_count':'offsetof(struct JourneyWildPool,count)',
        'pool_species':'offsetof(struct JourneyWildPool,species)',
        'stages_size':'sizeof(struct JourneyWildStages)',
        'stages_root':'offsetof(struct JourneyWildStages,root)',
        'stages_count':'offsetof(struct JourneyWildStages,count)',
        'stages_species':'offsetof(struct JourneyWildStages,stages)',
        'undefined_group':'MAP_GROUP(MAP_UNDEFINED)',
        'battle_mon_size':'sizeof(struct BattlePokemon)',
        'battle_mon_species':'offsetof(struct BattlePokemon,species)',
        'battle_mon_level':'offsetof(struct BattlePokemon,level)',
    }
    text = '#include "global.h"\n#include "pokemon.h"\n#include "wild_encounter.h"\n#include "constants/maps.h"\n#include <stddef.h>\n'+structs+'\nconst u32 ecology_abi[]={'+','.join(expressions.values())+'};\n'
    with tempfile.TemporaryDirectory(prefix='ecology-abi-',dir='/tmp') as temporary:
        out = Path(temporary)/'abi.s'
        subprocess.run([str(ROOT/'.local/arm-gcc/usr/bin/arm-none-eabi-gcc'),'-S','-iquote',str(source/'include'),
                        '-mabi=apcs-gnu','-x','c','-','-o',str(out)],input=text,text=True,check=True,capture_output=True)
        values = [int(n) for n in re.findall(r'\.word\s+(\d+)',out.read_text().split('ecology_abi:',1)[1].split('.size',1)[0])]
    assert len(values)==len(expressions)
    return dict(zip(expressions,values))


def symbols_for(source):
    text = subprocess.check_output([str(ROOT/'.local/arm-binutils/usr/bin/arm-none-eabi-nm'),'-S','--defined-only',str(Path(source)/'pokeemerald.elf')],text=True)
    return {name:(int(address,16),int(size,16) if size else 0)
            for address,size,name in re.findall(r'^([\da-fA-F]+)\s+(?:([\da-fA-F]+)\s+)?\w\s+(\S+)$',text,re.M)}


class RomTables:
    def __init__(self,source):
        self.source=Path(source)
        self.rom=(self.source/'pokeemerald.gba').read_bytes()
        self.abi=build_abi(source)
        self.symbols=symbols_for(source)
        self.catalog=json.loads((ROOT/'tools/hoenn/catalog_metadata.json').read_text())['species']
        from aquatic_species import aquatic_ids
        self.aquatic=aquatic_ids(self.catalog)

    def raw(self,address,count):
        offset=address-0x08000000
        assert 0<=offset<=len(self.rom)-count, ('Pointer outside compiled ROM',hex(address),count)
        return self.rom[offset:offset+count]

    def integer(self,address,size=4):
        return int.from_bytes(self.raw(address,size),'little')

    def header_tables(self):
        a=self.abi;address,size=self.symbols['gWildMonHeaders'];result={}
        for index in range(size//a['header_size'] if size else 10000):
            at=address+index*a['header_size'];group,num=self.raw(at,2)
            if group==a['undefined_group']:break
            fields=[]
            for time in range(a['time_count']):
                table={}
                for area,field in enumerate(AREAS):
                    pointer=self.integer(at+a['header_types']+time*a['types_size']+a['types_'+field])
                    if not pointer:
                        table[field]=None;continue
                    rate=self.integer(pointer+a['info_rate'],1)
                    slots=self.integer(pointer+a['info_slots'])
                    species=[self.integer(slots+i*a['slot_size']+a['slot_species'],2) for i in range(COUNTS[area])]
                    assert all(i==0 or str(i) in self.catalog for i in species), (group,num,field,species)
                    table[field]=dict(rate=rate,species=species,info_pointer=pointer,slots_pointer=slots)
                fields.append(table)
            # Altering Cave has alternative headers after the primary one.
            result.setdefault((group<<8)|num,dict(index=index,times=fields))
        else:raise AssertionError('Unterminated native wild-header table')
        return result

    def pool_tables(self,name):
        a=self.abi;address,size=self.symbols[name];assert size%a['pool_size']==0
        result={}
        for index in range(size//a['pool_size']):
            at=address+index*a['pool_size'];key=(self.integer(at+a['pool_map'],2),self.integer(at+a['pool_area'],1))
            count=self.integer(at+a['pool_count'],1);assert count<=24
            roots=[self.integer(at+a['pool_species']+i*2,2) for i in range(count)]
            assert key not in result, ('Duplicate runtime habitat pool',name,key)
            result[key]=roots
        return result

    def stage_members(self,root,stage,cap,water=True):
        a=self.abi;address,size=self.symbols['sJourneyWildStages'];at=address+root*a['stages_size']
        assert 0<=root<size//a['stages_size']
        for _ in range(3):
            count=self.integer(at+a['stages_count']+stage,1);assert count<=8
            species=[self.integer(at+a['stages_species']+stage*16+i*2,2) for i in range(count)]
            allowed=[i for i in species if str(i) in self.catalog and
                     0<self.catalog[str(i)]['national_dex']<=cap and
                     (not water or i in self.aquatic)]
            if allowed:return allowed
            stage=max(0,stage-1)
        return []

    def behaviors(self,layout,values):
        frlg=layout['layout_version']=='frlg';cutoff,size,mask=(640,4,511) if frlg else (512,2,255)
        banks=[self.integer(self.symbols[layout[field]][0]+0x10) for field in ['primary_tileset','secondary_tileset']]
        attrs={}
        for tile in set(v&1023 for v in values):
            address=banks[0 if tile<cutoff else 1]+size*(tile if tile<cutoff else tile-cutoff)
            attrs[tile]=self.integer(address,size)&mask
        return [attrs[v&1023] for v in values]


def aquatic_candidates(source,tables,headers):
    """Inventory usable water independently of missing encounter headers."""
    source=Path(source);groups=json.loads((source/'data/maps/map_groups.json').read_text())
    ids={name:(g<<8)|n for g,label in enumerate(groups['group_order']) for n,name in enumerate(groups[label])}
    layouts={r['id']:r for r in json.loads((source/'data/layouts/layouts.json').read_text())['layouts']}
    coast=(source/'src/journey_sevii_surf.c').read_text()
    connected=set(re.findall(r'case\s*\(MAP_GROUP\((MAP_\w+)\)',coast))
    bit_address=tables.symbols['sTileBitAttributes'][0]
    tile_flags={i:tables.integer(bit_address+i,1) for i in range(256)}
    retired=json.loads((source/'.journey-navigated-sea-atlas').read_text()).get('obsolete_unconnected_route_removed')
    result=[]
    for name,mid in sorted(ids.items()):
        m=json.loads((source/f'data/maps/{name}/map.json').read_text());layout=layouts[m['layout']]
        w,h=layout['width'],layout['height'];raw=(source/layout['blockdata_filepath']).read_bytes()
        values=struct.unpack('<'+'H'*(w*h),raw);behavior=tables.behaviors(layout,values)
        underwater=m['map_type']=='MAP_TYPE_UNDERWATER'
        wet=[i for i,(value,b) in enumerate(zip(values,behavior)) if not value&0xC00 and
             ((tile_flags.get(b,0)&2) or (underwater and b==0))]
        if not wet:continue
        has_water=bool(mid in headers and any(t['water_mons'] for t in headers[mid]['times']))
        native_coast=m['id'] in connected
        counts=dict(Counter(behavior[i] for i in wet))
        required,reason=eligibility(name,m['map_type'],counts,name==retired)
        sample=next(((i%w,i//w,behavior[i]) for i in wet if 2<=i%w<min(w-2,127) and 2<=i//w<min(h-2,127)),None)
        result.append(dict(map=name,map_id=m['id'],packed_map_id=mid,type=m['map_type'],
            required=required,exception=reason,water_cells=len(wet),sample=list(sample) if sample else None,
            behavior_counts=counts,underwater=underwater,connected_sevii_coast=native_coast,
            blockdata_sha256=digest(source/layout['blockdata_filepath'])))
    return result


def census(source,allow_gaps=False):
    tables=RomTables(source);headers=tables.header_tables();candidates=aquatic_candidates(source,tables,headers)
    pools={493:tables.pool_tables('sJourneyGeneration4Pools'),1025:tables.pool_tables('sJourneyWildPools')}
    marker=Path(source)/'.journey-coastal-ecology'
    marker_data=json.loads(marker.read_text()) if marker.exists() else None
    rows=[];coverage={str(cap):dict(missing_pools=[],missing_fishing_pools=[],invalid_roots=[],empty_phases=[]) for cap in pools}
    missing_headers=[];missing_fishing=[];missing_triggers=[]
    wild_source=(Path(source)/'src/wild_encounter.c').read_text()
    behavior_source=(Path(source)/'src/metatile_behavior.c').read_text()
    water_predicate=re.search(r'bool8 MetatileBehavior_IsWaterWildEncounter\(.*?\n}\n',behavior_source,re.S)[0]
    predicate=re.search(r'static bool8 JourneyCoastalDepthEncounterTile\(.*?\n}\n',wild_source,re.S)
    predicate=predicate[0] if predicate else ''
    bits=tables.symbols['sTileBitAttributes'][0]
    def periods_for(header,field):
        periods=[]
        if header:
            for time in range(tables.abi['time_count']):
                selected=time if tables.abi['time_enabled'] else 0
                if not header['times'][selected][field] and not tables.abi['time_disable_fallback']:
                    selected=tables.abi['time_fallback']
                table=header['times'][selected][field]
                periods.append(dict(time=time,effective_time=selected,
                    rate=table['rate'] if table else 0,species=table['species'] if table else []))
        return periods
    for row in candidates:
        mid=row['packed_map_id'];header=headers.get(mid)
        row['native_header_index']=header['index'] if header else None
        # Both native seaweed and the new depth predicate use WATER area 1.
        # Header presence alone does not prove any tile reaches that branch.
        field='water_mons';area=1;row['area']=area
        trigger_behaviors=[]
        for behavior in row['behavior_counts']:
            flags=tables.integer(bits+behavior,1)
            if flags&3==3:
                trigger_behaviors.append(behavior)
            elif behavior==44 and row['connected_sevii_coast'] and 'metatileBehavior == MB_FAST_WATER && JourneySeviiIsOpenCoast()' in water_predicate:
                trigger_behaviors.append(behavior)
            elif behavior==0 and row['map'] in DEPTH_NAMES and row['map_id'] in predicate and 'MB_NORMAL' in predicate:
                trigger_behaviors.append(behavior)
            elif behavior==25 and row['map_id'] in predicate and 'MB_NO_SURFACING' in predicate:
                trigger_behaviors.append(behavior)
        row['standard_wild_trigger_behaviors']=sorted(trigger_behaviors)
        if row['required'] and not trigger_behaviors:missing_triggers.append(row['map'])
        row['time_periods']=periods_for(header,field)
        row['fishing_time_periods']=periods_for(header,'fishing_mons') if not row['underwater'] else []
        if row['required'] and (not header or any(not t['species'] or not t['rate'] for t in row['time_periods'])):
            missing_headers.append(row['map'])
        if row['required'] and not row['underwater']:
            if not header or any(not t['species'] or not t['rate'] for t in row['fishing_time_periods']):
                missing_fishing.append(row['map'])
        row['pools']={};row['fishing_pools']={}
        for cap,pool in pools.items():
            roots=pool.get((mid,area),[]);row['pools'][str(cap)]=roots
            if not row['required']:continue
            if not roots:coverage[str(cap)]['missing_pools'].append(row['map'])
            areas=[(1,roots)]
            if not row['underwater']:
                fishing=pool.get((mid,3),[]);row['fishing_pools'][str(cap)]=fishing
                if not fishing:coverage[str(cap)]['missing_fishing_pools'].append(row['map'])
                areas.append((3,fishing))
            for encounter_area,members in areas:
                for root in members:
                    spec=tables.catalog.get(str(root))
                    if not spec or spec['national_dex'] in EVENT_DEX:
                        coverage[str(cap)]['invalid_roots'].append([row['map'],encounter_area,root])
                        continue
                    for phase,stages in enumerate([[0],[0,1],[1,2]]):
                        if not all(tables.stage_members(root,stage,cap,water=True) for stage in stages):
                            coverage[str(cap)]['empty_phases'].append([row['map'],encounter_area,root,phase])
        rows.append(row)
    if marker_data:
        expected={r['map'] for r in marker_data['encounters']['targets']}
        assert expected=={r['map'] for r in rows if r['required']}, ('Independent aquatic target inventory differs',sorted(expected^{r['map'] for r in rows if r['required']}))
    gaps=bool(missing_headers or missing_fishing or missing_triggers or any(any(v.values()) for v in coverage.values()))
    report=dict(kind='coastal-ecology-census',passed=not gaps,compiled_rom=True,
        rom_sha256=hashlib.sha256(tables.rom).hexdigest(),elf_sha256=digest(Path(source)/'pokeemerald.elf'),
        abi=tables.abi,all_time_periods_checked=tables.abi['time_count'],
        aquatic_maps=len(rows),required_aquatic_maps=sum(r['required'] for r in rows),
        quiet_or_retired_maps=sum(not r['required'] for r in rows),maps=rows,
        required_map_names=sorted(r['map'] for r in rows if r['required']),
        missing_headers=missing_headers,missing_fishing_headers=missing_fishing,
        missing_standard_wild_triggers=missing_triggers,coverage_by_cap=coverage,
        native_headers_read_from_compiled_rom=True,habitat_pools_read_from_compiled_rom=True,
        terrain_behaviors_read_from_compiled_tilesets=True,diagnostic_allow_gaps=bool(allow_gaps),
        layer166_marker_present=bool(marker_data),native_controller_battles_verified=False)
    if gaps and not allow_gaps:
        raise AssertionError(('Missing aquatic encounters',missing_headers,missing_fishing,missing_triggers,
                              {k:{n:len(v) for n,v in r.items()} for k,r in coverage.items()}))
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--library',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--allow-gaps',action='store_true',help='Diagnostic census only; never a release pass')
    parser.add_argument('--native-case',help='Walk this map until a real wild battle, or verify review suppression')
    parser.add_argument('--native-matrix',action='store_true',help='Run five independent native coast, river and depth controller cases')
    parser.add_argument('--behavior',type=int,help='Require this terrain behavior for the controller lane')
    parser.add_argument('--phase',type=int,choices=[0,1,2],default=0)
    parser.add_argument('--profile',default='aquatic')
    parser.add_argument('--review-steps',type=int,default=220)
    options=parser.parse_args()
    if options.native_matrix:
        assert options.library and not options.native_case
        native_matrix(options)
        return
    if options.native_case:
        assert options.library, '--library is required for native cases'
        native_case(options)
        return
    result=census(options.source,options.allow_gaps)
    options.output.mkdir(parents=True,exist_ok=True)
    (options.output/'coastal-ecology-census.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['kind','passed','aquatic_maps','required_aquatic_maps','quiet_or_retired_maps']}),flush=True)
    print('Missing native headers:',len(result['missing_headers']),flush=True)


def native_case(options):
    """Use held directional controls to trigger an actual encounter in mGBA."""
    tables=RomTables(options.source);compiled_headers=tables.header_tables()
    candidates=aquatic_candidates(options.source,tables,compiled_headers)
    selected=next(row for row in candidates if row['map']==options.native_case)
    namespace=dict(__file__=__file__)
    old_argv=sys.argv
    sys.argv=[__file__,'--source',str(options.source),'--library',str(options.library),'--output',str(options.output)]
    try:
        bootstrap=(ROOT/'tools/hoenn/validate_abilities.py').read_text().split('\nability_field,')[0]
        exec(compile(bootstrap,__file__,'exec'),namespace)
    finally:
        sys.argv=old_argv
    source,lib,s=namespace['source'],namespace['lib'],namespace['s']
    native,step,warp,position,location,save=map(namespace.__getitem__,['native','step','warp','position','location','save'])
    abi=namespace['abi'];capture_paths=[]
    def picture(name):
        namespace['picture'](name)
        capture_paths.append(options.output/(name+'.png'))
    review=bool(lib.read8(s['gJourneyReviewMode']))
    cap=lib.read16(s['gJourneyBuildRules'])
    assert cap in (493,1025)
    # Declared setup fixtures, before walking. A neutral Torrent Swampert has
    # no encounter-reducing ability or held item. No Repel/DisableWild is used
    # to obtain the TESTE suppression result.
    for i in range(6*abi[2]):lib.write8(s['gParties']+i,0)
    lib.write8(s['gPartiesCount'],0)
    assert native('ScriptGiveMon',260,35,0)==0
    native('DisableWildEncounters',0)
    native('VarSet',0x4021,0);native('VarSet',0x4120,0)
    variables=(source/'include/constants/vars.h').read_text()
    for name,value in [('VAR_MAP_SCENE_FOUR_ISLAND',1),('VAR_MAP_SCENE_ONE_ISLAND_HARBOR',3)]:
        match=re.search(r'^#define\s+'+name+r'\s+(0x\w+)',variables,re.M)
        if match:native('VarSet',int(match[1],16),value)
    flags=[*range(0x1AB0,0x1AB8),*[lib.read16(s['gBadgeFlags']+i*2) for i in range(8)]]
    total={0:0,1:6,2:12}[options.phase]
    for index,flag in enumerate(flags):
        at=save()+namespace['FLAG_OFFSET']+flag//8;mask=1<<(flag&7)
        lib.write8(at,(lib.read8(at)|mask) if index<total else (lib.read8(at)&~mask))
    assert native('JourneyWildPhase')==options.phase
    assert native('GetSafariZoneFlag')==0
    mapping=json.loads((source/f'data/maps/{options.native_case}/map.json').read_text())
    layout=namespace['layouts'][mapping['layout']];width,height=layout['width'],layout['height']
    words=struct.unpack('<'+'H'*(width*height),(source/layout['blockdata_filepath']).read_bytes())
    behaviors=tables.behaviors(layout,words)
    excluded={(e['x'],e['y']) for key in ['warp_events','coord_events'] for e in mapping[key]}
    # Keep the private walking lane away from object/event activation. Do not
    # mark every trainer ID defeated: battle-facility IDs are not flag IDs.
    for obj in mapping['object_events']:
        radius=8 if obj.get('trainer_type')!='TRAINER_TYPE_NONE' else 1
        excluded.update((obj['x']+dx,obj['y']+dy)
                        for dx in range(-radius,radius+1) for dy in range(-radius,radius+1))
    bits=tables.symbols['sTileBitAttributes'][0]
    def usable(x,y):
        if not(2<=x<min(width-2,126) and 2<=y<min(height-2,126)) or (x,y) in excluded:return False
        i=y*width+x;b=behaviors[i]
        if words[i]&0xC00:return False
        if options.behavior is not None:return b==options.behavior
        return b in (0,18,25,34,21,16,17,44) if selected['underwater'] else b in (21,16,17,44)
    pairs=[((x,y),(x+1,y)) for y in range(2,min(height-2,126)) for x in range(2,min(width-3,125))
           if all(usable(x+dx,y+dy) for dx in range(-1,3) for dy in range(-1,2))]
    assert pairs, ('No unobstructed aquatic walking fixture',options.native_case)
    first,second=pairs[len(pairs)//2]
    warp(options.native_case,*first)
    native('SetPlayerAvatarTransitionFlags',16 if selected['underwater'] else 8)
    step(90)
    assert position()==first
    assert (lib.read8(s['gPlayerAvatar']) & (16 if selected['underwater'] else 8))
    initial_behavior=native('MapGridGetMetatileBehaviorAt',first[0]+7,first[1]+7)
    assert initial_behavior==behaviors[first[1]*width+first[0]]
    if options.behavior is not None:assert initial_behavior==options.behavior
    picture('controller-aquatic-start')
    area=1
    assert native('JourneyWildPoolAvailable',area)
    assert native('GetCurrentMapWildMonHeaderId')==compiled_headers[selected['packed_map_id']]['index']
    phase_stages=[[0],[0,1],[1,2]][options.phase]
    roots=tables.pool_tables('sJourneyGeneration4Pools' if cap==493 else 'sJourneyWildPools')[(selected['packed_map_id'],area)]
    allowed=sorted({i for root in roots for stage in phase_stages for i in tables.stage_members(root,stage,cap,True)})
    assert allowed and all(tables.catalog[str(i)]['national_dex'] not in EVENT_DEX for i in allowed)
    # The native pool selector is sampled before movement, not used to force
    # the battle that the later controller route must actually trigger.
    sampled=[native('JourneyWildSpecies',roots[0],area) for _ in range(48)]
    assert set(sampled)<=set(allowed) and 0 not in sampled
    fishing_available=bool(native('DoesCurrentMapHaveFishingMons'))
    if not selected['underwater']:assert fishing_available is not review
    initial=first;goal=second;moves=[];battle=None
    max_steps=options.review_steps if review else 1600
    for tick in range(max_steps*40):
        callback=lib.read32(s['gMain']+4)&~1
        if callback==s['BattleMainCB2']:
            assert not review, ('TESTE started a wild battle',options.native_case,moves[-5:])
            # Let the genuine encounter intro populate both battle sprites.
            for _ in range(600):
                enemy=s['gBattleMons']+tables.abi['battle_mon_size']
                species=lib.read16(enemy+tables.abi['battle_mon_species'])
                level=lib.read8(enemy+tables.abi['battle_mon_level'])
                if species in allowed and level:break
                step(2,1)
            assert species in allowed and 30<=level<=37, (options.native_case,species,level,allowed)
            assert not lib.read32(s['gBattleTypeFlags']) & 8, 'Trainer battle is not a wild encounter'
            # BattlePokemon is populated before the fade/intro has drawn.
            # A species in RAM is insufficient evidence for a useful image.
            action_handlers={int(addr,16) for addr,kind,name in re.findall(r'^(\w+) (\w) (\S+)$',namespace['raw'],re.M)
                             if name=='HandleInputChooseAction'}
            assert action_handlers
            for _ in range(800):
                if (lib.read32(s['gBattlerControllerFuncs'])&~1) in action_handlers:
                    step(30)
                    break
                step(1,1);step(12)
            else:raise AssertionError(('Wild encounter intro did not reach the visible action menu',options.native_case))
            visibility=framebuffer_visibility(ctypes.string_at(lib.image(),240*160*4))
            picture('controller-wild-battle')
            battle=dict(species=species,national_dex=tables.catalog[str(species)]['national_dex'],level=level,
                        actual_battle_main_callback=True,battle_type_flags=lib.read32(s['gBattleTypeFlags']),
                        battle_action_menu_rendered=True,**visibility)
            break
        if callback!=s['CB2_Overworld'] or lib.read8(s['sLockFieldControls']):
            step(1);continue
        assert location()==namespace['map_id'](options.native_case), ('Unexpected map during encounter walk',location())
        now=position()
        if now==goal:
            moves.append(list(now))
            goal=first if goal==second else second
            if len(moves)>=max_steps:break
        key=16 if goal[0]>now[0] else 32
        before=now
        for _ in range(32):
            step(1,key)
            if position()!=before or (lib.read32(s['gMain']+4)&~1)!=s['CB2_Overworld']:break
        step(12)
    assert moves, ('No actual controller movement',options.native_case)
    attempts=0
    if review:
        assert len(moves)>=options.review_steps and battle is None
        assert (lib.read32(s['gMain']+4)&~1)==s['CB2_Overworld']
        b=native('MapGridGetMetatileBehaviorAt',position()[0]+7,position()[1]+7)
        for _ in range(200):
            assert not native('StandardWildEncounter',b,b);attempts+=1
        assert not native('DoesCurrentMapHaveFishingMons')
        assert not native('SweetScentWildEncounter')
        picture('review-controller-water-without-encounters')
    else:
        assert battle, ('No normal-ROM encounter after actual controller steps',options.native_case,len(moves))
    lib.stop()
    captures=[dict(file=p.name,sha256=digest(p),native_emulator_capture=True) for p in capture_paths]
    result=dict(kind='coastal-ecology-native-case',passed=True,rom_sha256=hashlib.sha256(tables.rom).hexdigest(),
        elf_sha256=digest(source/'pokeemerald.elf'),
        compiled_rom=True,native_validation_performed=True,map=options.native_case,profile=options.profile,
        review_mode=review,max_national_dex=cap,phase=options.phase,area=area,
        underwater=selected['underwater'],initial_position=list(initial),walking_pair=[list(first),list(second)],
        native_case_behavior=initial_behavior,native_fishing_available=fishing_available,
        actual_controller_steps=len(moves),controller_input_only_after_initial_fixture=True,
        party_and_map_and_badges_are_initial_fixtures=True,
        trainer_defeat_flags_not_written=True,
        wild_encounters_disabled_fixture=False,repel_fixture_steps=0,
        allowed_species=allowed,native_pool_samples=sorted(set(sampled)),battle=battle,
        standard_encounter_suppression_attempts=attempts,captures=captures,
        no_battle_result_or_avatar_coordinate_writes=True)
    options.output.mkdir(parents=True,exist_ok=True)
    (options.output/'coastal-ecology-native-case.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Native aquatic encounter case passed:',options.native_case,'TESTE' if review else cap,len(moves),flush=True)


def native_matrix(options):
    """Fresh emulator processes share only an immutable ROM and ELF."""
    cases=[('SixIsland_Frlg','coast',44,0),
           ('JourneyHoennMiddleSea','open-sea',21,1),
           ('Route114','river',21,2),
           ('JourneyDepthMares','new-depth',0,2),
           ('Underwater_Route105','native-depth',25,1)]
    options.output.mkdir(parents=True,exist_ok=True)
    rows=[];captures=[]
    for name,profile,behavior,phase in cases:
        folder=options.output/name
        subprocess.run([sys.executable,str(Path(__file__).resolve()),'--source',str(options.source),
                        '--library',str(options.library),'--output',str(folder),'--native-case',name,
                        '--profile',profile,'--behavior',str(behavior),'--phase',str(phase),
                        '--review-steps',str(options.review_steps)],check=True)
        result=json.loads((folder/'coastal-ecology-native-case.json').read_text())
        assert result['passed'] and result['native_case_behavior']==behavior
        result['captures']=[dict(capture,file=name+'/'+capture['file']) for capture in result['captures']]
        captures.extend(result['captures'])
        rows.append(result)
    assert len({r['rom_sha256'] for r in rows})==len({r['elf_sha256'] for r in rows})==1
    assert len({r['review_mode'] for r in rows})==len({r['max_national_dex'] for r in rows})==1
    kind='coastal-ecology-review' if rows[0]['review_mode'] else 'coastal-ecology-native'
    report=dict(kind=kind,passed=True,
        rom_sha256=rows[0]['rom_sha256'],elf_sha256=rows[0]['elf_sha256'],
        compiled_rom=True,native_validation_performed=True,
        review_mode=rows[0]['review_mode'],max_national_dex=rows[0]['max_national_dex'],
        cases=rows,captures=captures,coast_open_sea_river_new_and_native_depth_checked=True,
        actual_controller_steps=sum(r['actual_controller_steps'] for r in rows),
        all_normal_cases_started_actual_wild_battles=all(r['battle'] is not None for r in rows) if not rows[0]['review_mode'] else None,
        all_review_cases_suppressed_encounters=all(r['battle'] is None and r['standard_encounter_suppression_attempts']==200 for r in rows) if rows[0]['review_mode'] else None,
        no_encounter_forcing_repel_or_disabled_wild_fixture=True,
        no_battle_result_or_avatar_coordinate_writes=True)
    (options.output/(kind+'.json')).write_text(json.dumps(report,indent=2)+'\n')
    print('Native aquatic matrix passed:',report['max_national_dex'],'TESTE' if report['review_mode'] else 'normal',flush=True)


if __name__=='__main__':
    main()
