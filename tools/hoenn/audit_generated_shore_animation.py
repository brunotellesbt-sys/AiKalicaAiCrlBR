"""Census generated coast graphics, then observe native shoreline banks.

Source coverage is exhaustive for the inventory; native coverage is a named
representative per used bank pair plus all seven Sevii towns. Placement and
progress are fixtures. Animation clocks, callbacks, palettes and VRAM are never
written; the report keeps source observations separate from native evidence.
"""
import argparse
from collections import Counter, defaultdict
import ctypes
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def source_census(source, inventory):
    source = Path(source)
    layouts = {row['id']: row for row in json.loads((source/'data/layouts/layouts.json').read_text())['layouts']}
    headers = (source/'src/data/tilesets/headers.h').read_text()
    declarations = (source/'src/data/tilesets/metatiles.h').read_text()
    cache = {}
    private = json.loads((source/'.journey-coastal-closures').read_text())['shore_animation']['animated_graphics']

    def bank(symbol, size):
        key = symbol, size
        if key not in cache:
            body = re.search(r'const struct Tileset '+re.escape(symbol)+r'\s*=\s*\{(.*?)\};', headers, re.S)[1]
            def raw(field):
                symbol = re.search(r'\.'+field+r'\s*=\s*(\w+)', body)[1]
                path = re.search(r'\b'+re.escape(symbol)+r'\[\].*?"([^"]+)"', declarations)[1]
                return (source/path).read_bytes()
            meta, attrs = raw('metatiles'), raw('metatileAttributes')
            cache[key] = dict(words=struct.unpack('<'+'H'*(len(meta)//2), meta),
                attrs=[int.from_bytes(attrs[i:i+size], 'little') for i in range(0,len(attrs),size)],
                callback=re.search(r'\.callback\s*=\s*(\w+)',body)[1])
        return cache[key]

    rows, groups = [], defaultdict(list)
    for item in inventory['maps']+inventory['indirect_maps']:
        name = item['map']
        mapping = json.loads((source/f'data/maps/{name}/map.json').read_text())
        layout = layouts[mapping['layout']]
        frlg = layout['layout_version']=='frlg'
        cutoff,size = (640,4) if frlg else (512,2)
        primary,secondary = [bank(layout[field],size) for field in ('primary_tileset','secondary_tileset')]
        active = primary['callback'] in ('InitTilesetAnim_General','InitTilesetAnim_General_Frlg')
        slots = set(range(416,482)) if frlg else set(range(432,462))|set(range(464,474))|set(range(480,490))
        if layout['secondary_tileset']=='gTileset_JourneyDewfordHarbor': slots.update(private)
        width,height = layout['width'],layout['height']
        data = (source/layout['blockdata_filepath']).read_bytes()
        values = struct.unpack('<'+'H'*(width*height),data)
        cells, candidates = [], []
        used_slots = set()
        source_objects = {(e['x'],e['y']) for e in mapping.get('object_events',[])}
        source_warps = {(e['x'],e['y']) for e in mapping.get('warp_events',[])}
        for index,value in enumerate(values):
            mid=value&1023; table=primary if mid<cutoff else secondary; at=mid if mid<cutoff else mid-cutoff
            words = table['words'][at*8:at*8+8]
            referenced = sorted({word&1023 for word in words} & slots) if active else []
            attr = table['attrs'][at]
            x,y = index%width,index//width
            if referenced:
                cells.append([x,y]);used_slots.update(referenced)
            if not value&0xC00 and value>>12 in (0,1,3) and (x,y) not in source_objects|source_warps:
                # Avoid forced currents, bridge transitions and deepwater
                # (which may trigger cutscenes on original event maps).
                behavior=attr&(511 if frlg else 255)
                if behavior in (0,2,8,16,21,33): candidates.append((x,y,behavior,value>>12))
        if cells:
            prefix=[[0]*(width+1) for _ in range(height+1)]
            cellset=set(map(tuple,cells))
            for yy in range(height):
                total=0
                for xx in range(width):
                    total+=(xx,yy) in cellset
                    prefix[yy+1][xx+1]=prefix[yy][xx+1]+total
            scores=[]
            for x,y,behavior,height in candidates:
                left,right=max(0,x-6),min(width,x+7)
                top,bottom=max(0,y-4),min(layout['height'],y+5)
                score=prefix[bottom][right]-prefix[top][right]-prefix[bottom][left]+prefix[top][left]
                # Favor clear land viewpoints when both modes can show shore.
                scores.append((score,height==3,-abs(x-width//2)-abs(y-layout['height']//2),x,y,behavior,height))
            point=list(max(scores)[3:]) if scores else None
        else: point=None
        key=(layout['primary_tileset'],layout['secondary_tileset'],layout['layout_version'])
        row=dict(map=name,review_scope=item.get('review_scope','direct'),type=mapping['map_type'],
            bank_pair=list(key),primary_callback=primary['callback'],secondary_callback=secondary['callback'],
            referenced_animation_graphics=sorted(used_slots),animated_metatile_cells=len(cells),
            sample_fixture=point,blockdata_sha256=sha(data),dimensions=[width,layout['height']])
        rows.append(row)
        if cells:groups[key].append(row)
    return rows,groups


def packed_png(path):
    indexed=Image.open(path)
    assert indexed.mode=='P'
    data=bytearray()
    for y in range(0,indexed.height,8):
        for x in range(0,indexed.width,8):
            for yy in range(8):
                for xx in range(0,8,2):
                    data.append(indexed.getpixel((x+xx,y+yy))|indexed.getpixel((x+xx+1,y+yy))<<4)
    return bytes(data)


def expected_channels(source,frlg):
    folder=source/'data/tilesets/primary'/('general_frlg' if frlg else 'general')/'anim'
    specs=[('water',416 if frlg else 432,'water_current_landwatersedge' if frlg else 'water',8),
           ('foam',464,'sandwatersedge' if frlg else 'sand_water_edge',8 if frlg else 7)]
    return {kind:dict(start=start,frames=[packed_png(folder/name/(str(i)+'.png')) for i in range(count)])
            for kind,start,name,count in specs}


def visible_graphic_pixels(read_bytes, lib, symbols, slots):
    """Match loaded hardware BG samples against actual visible mGBA pixels."""
    vram=read_bytes(0x06000000,65536)
    palette=[lib.read16(0x05000000+2*i)&0x7FFF for i in range(256)]
    colors=[tuple(((value>>shift)&31)<<3 for shift in (0,5,10)) for value in palette]
    pixels=ctypes.string_at(lib.image(),240*160*4)
    display=lib.read16(0x04000000)
    assert display&7==0
    result={}
    for bg in range(4):
        if not display&(0x100<<bg):continue
        control=lib.read16(0x04000008+2*bg)
        if control&0x80:continue
        charbase=((control>>2)&3)*0x4000
        if charbase:continue
        screenbase=((control>>8)&31)*0x800
        size=control>>14
        width,height=(512 if size in (1,3) else 256),(512 if size in (2,3) else 256)
        sx=lib.read16(symbols['sGpuRegBuffer']+0x10+4*bg)&511
        sy=lib.read16(symbols['sGpuRegBuffer']+0x12+4*bg)&511
        for y in range(160):
            yy=(y+sy)%height;ty=yy//8
            for x in range(240):
                xx=(x+sx)%width;tx=xx//8
                offset=screenbase+((ty//32)*(width//256)+tx//32)*2048+((ty%32)*32+tx%32)*2
                word=int.from_bytes(vram[offset:offset+2],'little')
                slot=word&1023
                if slot not in slots:continue
                px=7-xx%8 if word&1024 else xx%8
                py=7-yy%8 if word&2048 else yy%8
                index=(vram[slot*32+py*4+px//2]>>(4*(px&1)))&15
                if not index:continue
                color=colors[(word>>12)*16+index]
                actual=pixels[(y*240+x)*4:(y*240+x)*4+3]
                if max(abs(a-b) for a,b in zip(color,actual))>7:continue
                result[(x,y)]=(slot,color)
    return result


def run(options):
    inventory=json.loads(options.inventory.read_text())
    initial_sha=sha((options.source/'pokeemerald.gba').read_bytes())
    rows,groups=source_census(options.source,inventory)
    options.output.mkdir(parents=True,exist_ok=True)
    census=dict(kind='generated-shore-animation-source-census',rom_sha256=initial_sha,
        inventory_sha256=sha(options.inventory.read_bytes()),passed=True,source_analysis_only=True,native_validation_performed=False,maps_inspected=len(rows),
        maps_referencing_active_shore_graphics=sum(bool(r['animated_metatile_cells']) for r in rows),
        active_bank_pairs=len(groups),source_only=True,native_animation_proof=False,maps=rows)
    (options.output/'shore-census.json').write_text(json.dumps(census,indent=2)+'\n')
    if options.library is None:return census
    global source,args,s,lib,layouts,native,step,position,location,picture,warp,save
    sys.argv=[sys.argv[0],'--source',str(options.source),'--library',str(options.library),'--output',str(options.output)]
    bootstrap=(ROOT/'tools/hoenn/validate_sootopolis_harbor.py').read_text().split('\n# Disable Sootopolis')[0]
    exec(compile(bootstrap,__file__,'exec'),globals())
    native('DisableWildEncounters',1)
    native('RtcInitLocalTimeOffset',12,0)
    variables=(source/'include/constants/vars.h').read_text()
    # These are arrival-story fixtures, not changes to animation state. In
    # particular Four Island starts a rival cutscene on every fresh fixture.
    # Complete that previously validated episode before placing the camera.
    progress_fixtures={'VAR_MAP_SCENE_ONE_ISLAND_HARBOR':3,
                       'VAR_MAP_SCENE_FOUR_ISLAND':1,
                       'VAR_SOOTOPOLIS_CITY_STATE':0,
                       'VAR_SLATEPORT_HARBOR_STATE':2}
    for variable,value in progress_fixtures.items():
        match=re.search(r'^#define\s+'+variable+r'\s+(0x\w+|\d+)',variables,re.M)
        assert match,variable
        native('VarSet',int(match[1],0),value)
    trainer_constants=(source/'include/constants/opponents.h').read_text()
    trainer_count=max(map(int,re.findall(r'^#define\s+TRAINER_\w+\s+(\d+)\s*$',trainer_constants,re.M)))+1
    for trainer in range(1,trainer_count):
        address=save()+FLAG_OFFSET+(0x500+trainer)//8
        lib.write8(address,lib.read8(address)|(1<<((0x500+trainer)&7)))
    byname={r['map']:r for r in rows}
    representatives=[];native_exclusions=[]
    for key,members in sorted(groups.items()):
        available=[r for r in members if r['sample_fixture']]
        if key[1]=='gTileset_BattlePalace':
            native_exclusions.append(dict(bank_pair=list(key),reason='Unmodified native Battle Palace rooms enter facility control scripts; source graphics share tested General primary animation.'))
            continue
        if not available:
            native_exclusions.append(dict(bank_pair=list(key),reason='No safe initial camera fixture found; source census only.'))
            continue
        # Prefer created routes over native maps with intro/crisis scripts.
        selected=max(available,key=lambda r:(r['map'].startswith('Journey'),r['animated_metatile_cells']))
        if key[1]=='gTileset_CeladonCity':
            selected=next(r for r in available if r['map']=='Route18_Frlg')
        representatives.append(selected['map'])
    for word in ('One','Two','Three','Four','Five','Six','Seven'):
        name='ThreeIsland_Port_Frlg' if word=='Three' else word+'Island_Frlg'
        if name not in representatives:representatives.append(name)
    if options.maps:
        representatives=options.maps
    def read_bytes(address,length):
        return b''.join(lib.read32(address+i).to_bytes(4,'little') for i in range(0,length,4))[:length]
    observations=[]
    for name in representatives:
        row=byname[name]
        assert row['sample_fixture'],('No safe animation viewpoint',name)
        x,y,behavior,height=row['sample_fixture']
        warp(name,x,y)
        step(30)
        assert idle(),(name,'Animation camera fixture entered a locked field scene')
        native('SetPlayerAvatarTransitionFlags',8 if height==1 else 1)
        step(90)
        assert location()==map_id(name),(name,location())
        loaded_layout=lib.read32(s['gMapHeader'])
        assert lib.read32(loaded_layout+0x10)==s[row['bank_pair'][0]],('Unexpected loaded primary bank',name)
        assert lib.read32(loaded_layout+0x14)==s[row['bank_pair'][1]],('Unexpected loaded secondary bank',name)
        expected='TilesetAnim_General_Frlg' if row['bank_pair'][2]=='frlg' else 'TilesetAnim_General'
        assert lib.read32(s['sPrimaryTilesetAnimCallback'])&~1==s[expected],(name,'Inactive primary water animation')
        slots=row['referenced_animation_graphics']
        channels=expected_channels(source,row['bank_pair'][2]=='frlg')
        observed_channels={kind:set() for kind in channels}
        hashes={slot:set() for slot in slots}
        phases=set();captures=[];frames=[];screen_samples=[]
        # 192 native frames cover the 128-frame continuous ocean cycle and
        # independent 8-frame FRLG foam counter, without writing either clock.
        for tick in range(192):
            step(1)
            for slot in slots:hashes[slot].add(sha(read_bytes(0x06000000+slot*32,32)))
            for kind,channel in channels.items():
                loaded=read_bytes(0x06000000+channel['start']*32,len(channel['frames'][0]))
                assert loaded in channel['frames'],(name,kind,'Native frame differs from source animation asset',sha(loaded))
                observed_channels[kind].add(sha(loaded))
            phase=(lib.read32(s['gMain']+0x20)>>4)&7
            if phase not in phases:
                phases.add(phase)
                label='shore-bank-'+name+'-'+str(phase)
                picture(label)
                captures.append(dict(file=label+'.png',sha256=sha((args.output/(label+'.png')).read_bytes())))
                screen_samples.append(visible_graphic_pixels(read_bytes,lib,s,set(slots)))
                frames.append(dict(ocean_phase=phase,primary_counter=lib.read16(s['sPrimaryTilesetAnimCounter']),
                    secondary_counter=lib.read16(s['sSecondaryTilesetAnimCounter']),capture=label+'.png'))
        channel_proofs={}
        for kind,channel in channels.items():
            expected_hashes={sha(frame) for frame in channel['frames']}
            assert observed_channels[kind]==expected_hashes,(name,kind,'Incomplete asset-backed native cycle',len(observed_channels[kind]),len(expected_hashes))
            channel_proofs[kind]=dict(graphic_start=channel['start'],unique_source_frames=len(expected_hashes),observed_frame_sha256=sorted(observed_channels[kind]),every_source_phase_seen=True)
        changing=[slot for slot,values in hashes.items() if len(values)>1]
        assert phases==set(range(8)),(name,'Incomplete native ocean cycle')
        assert changing,(name,'All referenced water and shore graphics stayed static')
        images=[Image.open(args.output/c['file']).convert('RGB') for c in captures]
        changes=sum(len({im.getpixel((xx,yy)) for im in images})>1 for yy in range(160) for xx in range(240))
        common=set.intersection(*(set(sample) for sample in screen_samples))
        visible_proofs=[]
        for point in sorted(common):
            values=[sample[point] for sample in screen_samples]
            if len({value[1] for value in values})<=1 or not any(value[0] in changing for value in values):continue
            visible_proofs.append(dict(screen_position=list(point),native_graphic_slots=[value[0] for value in values],phase_rgb=[list(value[1]) for value in values]))
            if len(visible_proofs)>=12:break
        assert visible_proofs,(name,'No changing water/shore pixel was visible in native scanout')
        observations.append(dict(map=name,bank_pair=row['bank_pair'],initial_position_and_mode_are_fixtures=True,
            fixture_tile=[x,y],fixture_mode='surf' if height==1 else 'foot',
            initial_arrival_story_fixtures=progress_fixtures,
            all_eight_ocean_phases_observed=True,native_observed_frames=192,
            native_animation_channels=channel_proofs,changing_referenced_graphics=changing,referenced_graphic_hash_counts={str(k):len(v) for k,v in hashes.items()},
            visible_image_changing_pixels=changes,hardware_matched_changing_shore_pixels=visible_proofs,frames=frames,captures=captures,
            no_animation_clock_callback_palette_or_vram_writes=True))
        print('Native shore bank animation:',name,'changing graphics',len(changing),'visible pixels',changes,flush=True)
        (args.output/'shore-native-progress.json').write_text(json.dumps(observations,indent=2)+'\n')
    lib.stop()
    assert sha((source/'pokeemerald.gba').read_bytes())==initial_sha
    report=dict(kind='generated-shore-animation-native-banks',passed=True,rom_sha256=initial_sha,
        compiled_rom=True,native_validation_performed=True,source_analysis_only=False,source_census_file='shore-census.json',source_maps_inspected=len(rows),
        source_active_bank_pairs=len(groups),native_bank_pairs=len({tuple(r['bank_pair']) for r in observations}),
        native_maps_sampled=len(observations),native_exclusions=native_exclusions,observations=observations,
        captures=[capture for observation in observations for capture in observation['captures']],
        components=[dict(file='shore-census.json',sha256=sha((args.output/'shore-census.json').read_bytes()))],
        native_scope='one representative per eligible active bank pair plus all seven Sevii coastal areas; unchanged Battle Palace interior bank excluded; not every map camera',
        visible_total_pixel_changes_include_objects_not_isolated_foam=True,hardware_matched_native_shore_pixels_verified=True,
        full_campaign_playthrough=False,no_animation_clock_callback_palette_or_vram_writes=True)
    (args.output/'shore-native-banks.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--inventory',type=Path,default=ROOT/'docs/design/generated-world-audit/inventory.json')
    parser.add_argument('--library',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--maps',nargs='+')
    run(parser.parse_args())
