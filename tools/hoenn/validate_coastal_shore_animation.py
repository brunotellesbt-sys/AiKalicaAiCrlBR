"""Observe actual shoreline VRAM, scanout pixels and controller map crossings.

No animation callback, clock or graphics RAM is written by this validator.
Initial party/progress/position/avatar-mode fixtures are explicit. Cycles and
both directions of every local coast connection then advance native frames.
"""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

from PIL import Image

from coastal_shore_animation import ANIMATION
from dewford_coast_view import MAPS

ROOT = Path(__file__).resolve().parents[2]
PARENT_SHA = '08fc8a08b95e8e3a923e3342b4f1a31bbaccd1582cbc67ea010021191c43fd6e'
PRIVATE = 'gTileset_JourneyDewfordHarbor'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def pack_image(path):
    image = Image.open(path)
    result = bytearray()
    for y in range(0, image.height, 8):
        for x in range(0, image.width, 8):
            for dy in range(8):
                for dx in range(0, 8, 2):
                    result.append(image.getpixel((x+dx, y+dy)) | image.getpixel((x+dx+1, y+dy)) << 4)
    return bytes(result)


def run(options):
    global source, args, s, lib, layouts, native, step, position, location, picture, warp
    global names, allowed, walk_prefix, walk_surf_under_bridges, by_location, maps
    sys.argv = [sys.argv[0], '--source', str(options.source), '--library', str(options.library),
                '--output', str(options.output)]
    bootstrap = (ROOT / 'tools/hoenn/validate_sootopolis_harbor.py').read_text().split('\n# Disable Sootopolis')[0]
    exec(compile(bootstrap, __file__, 'exec'), globals())
    initial_sha = digest((source / 'pokeemerald.gba').read_bytes())
    assert initial_sha != PARENT_SHA, 'Historical ROM cannot validate the current shore animation'
    marker = json.loads((source / '.journey-coastal-closures').read_text())
    metadata = marker['shore_animation']
    assert metadata['native_sand_and_private_shore_queued_with_water_phase']
    assert metadata['native_private_secondary_reload_after_dma_refresh']
    assert 'sJourneyDewfordShoreRefreshPending' in s
    assert len(metadata['animated_graphics']) == 17 and len(metadata['dma_runs']) == 7
    payload = (source / ANIMATION).read_bytes()
    assert digest(payload) == metadata['frame_data_sha256']
    stride = metadata['words_per_phase'] * 2
    assert len(payload) == stride * 8 == 4352
    water_frames = [pack_image(source / f'data/tilesets/primary/general/anim/water/{i}.png') for i in range(8)]
    sand_frames = [pack_image(source / f'data/tilesets/primary/general/anim/sand_water_edge/{i if i<7 else 0}.png') for i in range(8)]
    source_graphics = pack_image(source / 'data/tilesets/secondary/journey_dewford_harbor/tiles.png')
    private_slots = set(metadata['animated_graphics'])
    native_animated = set(range(432, 462)) | set(range(464, 474)) | set(range(480, 490)) | set(range(508, 512)) | set(range(682, 688))
    static_slots = [i for i in range(512, 1024) if i not in private_slots | set(range(682,688))]
    colors = [tuple(map(int,line.split())) for line in (source / 'data/tilesets/secondary/journey_dewford_harbor/palettes/09.pal').read_text().splitlines()[3:]]
    expected_palette = [sum((channel >> 3) << shift for channel,shift in zip(color,(0,5,10))) for color in colors]

    def read_bytes(address, length):
        return b''.join(lib.read32(address+i).to_bytes(4,'little') for i in range(0,length,4))[:length]

    def pending_secondary_graphics_dma():
        pending=[]
        for index in range(128):
            request=s['sDma3Requests']+index*16
            target=lib.read32(request+4);size=lib.read16(request+8)
            if size and target<0x06008000 and target+size>0x06004000:
                pending.append(dict(index=index,destination=target,bytes=size))
        return pending

    def current_phase(check_palette=True):
        water = read_bytes(0x06000000 + 432*32, 30*32)
        matches = [i for i, frame in enumerate(water_frames) if water == frame]
        private = b''.join(read_bytes(0x06000000 + run['start']*32, run['count']*32) for run in metadata['dma_runs'])
        phases = [i for i in matches if private == payload[i*stride:(i+1)*stride]]
        assert len(phases) == 1, ('Sea/private shoreline phase disagreement',
            dict(water_phases=matches,
                 private_phases=[i for i in range(8) if private==payload[i*stride:(i+1)*stride]],
                 private_vram_sha256=digest(private),vblank_counter=lib.read32(s['gMain']+0x20),
                 primary_timer=lib.read16(s['sPrimaryTilesetAnimCounter']),
                 secondary_timer=lib.read16(s['sSecondaryTilesetAnimCounter']),location=list(location())))
        phase = phases[0]
        sand = read_bytes(0x06000000 + 464*32, 10*32)
        assert sand == sand_frames[phase], ('Sea/native foam phase disagreement', phase, digest(sand))
        if check_palette:
            assert [lib.read16(0x05000000 + (9*16+i)*2) & 0x7FFF for i in range(16)] == expected_palette
        for slot in static_slots:
            assert read_bytes(0x06000000 + slot*32,32) == source_graphics[(slot-512)*32:(slot-511)*32], ('Static shore/bridge/stair/flag-neighbor graphic changed',slot)
        return dict(phase=phase, vblank_counter=lib.read32(s['gMain']+0x20),
                    primary_timer=lib.read16(s['sPrimaryTilesetAnimCounter']),
                    secondary_timer=lib.read16(s['sSecondaryTilesetAnimCounter']),
                    water_vram_sha256=digest(water), private_vram_sha256=digest(private),
                    sand_vram_sha256=digest(sand), static_private_graphics_unchanged=True)

    def scanout_points():
        """Project actual loaded 4bpp hardware BG entries into the native image."""
        vram = read_bytes(0x06000000,65536)
        palette = [lib.read16(0x05000000 + 2*i) & 0x7FFF for i in range(256)]
        rgb = [tuple(((value>>shift)&31)<<3 for shift in (0,5,10)) for value in palette]
        pixels = ctypes.string_at(lib.image(),240*160*4)
        display = lib.read16(0x04000000)
        assert display & 7 == 0, 'Expected native mode-zero field backgrounds'
        found = {'water':{}, 'foam':{}, 'static':{}, 'static_land':{}, 'static_bridge':{}, 'animated':{}}
        for bg in range(4):
            if not display & (0x100<<bg):
                continue
            control = lib.read16(0x04000008 + 2*bg)
            assert not control & 0x80
            charbase = ((control>>2)&3)*0x4000
            screenbase = ((control>>8)&31)*0x800
            size = control>>14
            width,height = (512 if size in (1,3) else 256),(512 if size in (2,3) else 256)
            # BG scroll I/O is write-only on GBA. Bus reads return open-bus
            # data; observe the game's SetGpuReg mirror without calling a
            # native function (which would itself advance the frame).
            scroll_x = lib.read16(s['sGpuRegBuffer']+0x10+4*bg)&511
            scroll_y = lib.read16(s['sGpuRegBuffer']+0x12+4*bg)&511
            for y in range(160):
                yy=(y+scroll_y)%height;ty=yy//8
                for x in range(240):
                    xx=(x+scroll_x)%width;tx=xx//8
                    offset=screenbase+((ty//32)*(width//256)+tx//32)*2048+((ty%32)*32+tx%32)*2
                    word=int.from_bytes(vram[offset:offset+2],'little')
                    slot=word&1023;bank=word>>12
                    animated=charbase==0 and slot in private_slots and bank==9
                    static=charbase==0 and bank in (5,6,7) and slot not in native_animated | private_slots
                    if not(animated or static):
                        continue
                    px=7-xx%8 if word&1024 else xx%8
                    py=7-yy%8 if word&2048 else yy%8
                    at=charbase+slot*32+py*4+px//2
                    if at>=len(vram):
                        continue
                    index=(vram[at]>>(4*(px&1)))&15
                    if not index:
                        continue
                    color=rgb[bank*16+index]
                    actual=pixels[(y*240+x)*4:(y*240+x)*4+3]
                    if max(abs(a-b) for a,b in zip(color,actual))>7:
                        continue # A higher BG or an OBJ legitimately covers this pixel.
                    if animated:
                        found['animated'][(x,y)]=color
                    if animated and color[2]>color[0]+25 and color[2]>color[1]+10:
                        found['water'][(x,y)]=color
                    elif animated and index in (12,13):
                        # The private palette's pale sand (index 7) is not
                        # foam. Native foam really disappears in phases
                        # 0, 5, 6 and 7; identify its white colors exactly.
                        found['foam'][(x,y)]=color
                    elif static:
                        found['static'][(x,y)]=color
                        # The harbor art compiler reserves bank 7 for the
                        # suspension bridge/stairs; native dry sand is bank 5.
                        if bank==5:found['static_land'][(x,y)]=color
                        if bank==7:found['static_bridge'][(x,y)]=color
        return found

    def selected_points(points,maximum):
        ordered=sorted(points.items())
        if len(ordered)>maximum:
            ordered=[ordered[i*len(ordered)//maximum] for i in range(maximum)]
        return [[x,y,*color] for (x,y),color in ordered]

    def capture_cycle(name, fixture):
        frames, full_points, previous = {}, {}, None
        for tick in range(210):
            step(1)
            state=current_phase()
            phase=state['phase']
            if phase in frames or previous!=phase:
                previous=phase
                continue
            points=scanout_points()
            assert len(points['water'])>=24 and len(points['static'])>=32, (name,phase,{k:len(v) for k,v in points.items()})
            label=f'shore-{name}-phase-{phase}'
            picture(label)
            file=label+'.png'
            captures.append(dict(file=file,sha256=digest((args.output/file).read_bytes())))
            state.update(capture_file=file)
            frames[phase]=state;full_points[phase]=points
            if len(frames)==8:
                break
        assert set(frames)==set(range(8)), (name,'Incomplete native eight-phase cycle',sorted(frames))
        visible_all=set.intersection(*(set(points['animated']) for points in full_points.values()))
        fixed={'water':sorted(set(full_points[0]['water'])&visible_all),
               # Follow the same visible coordinates through the complete
               # cycle, including the native phases where foam recedes.
               'foam':sorted(set.union(*(set(points['foam']) for points in full_points.values()))&visible_all)}
        static_all=set.intersection(*(set(points['static']) for points in full_points.values()))
        static_all={point for point in static_all if len({points['static'][point] for points in full_points.values()})==1}
        fixed['static']=sorted(static_all)
        assert len(fixed['water'])>=24 and len(fixed['foam'])>=4 and len(fixed['static'])>=32, (name,{k:len(v) for k,v in fixed.items()},
            {phase:dict(phase_state=frames[phase],counts={kind:len(values) for kind,values in points.items()},
                        visible_bounds=[min(points['animated']),max(points['animated'])],
                        phase_zero_overlap=len(set(points['animated'])&set(full_points[0]['animated'])))
             for phase,points in full_points.items()})
        static_kind_proofs={}
        for kind in ('static_land','static_bridge'):
            common=set.intersection(*(set(points[kind]) for points in full_points.values()))
            common={point:full_points[0][kind][point] for point in common
                    if len({points[kind][point] for points in full_points.values()})==1}
            static_kind_proofs[kind]=selected_points(common,32)
        assert len(static_kind_proofs['static_land'])>=32,(name,'No invariant dry-land screen pixels')
        if name in ('DewfordTown','Route107'):
            assert len(static_kind_proofs['static_bridge'])>=32,(name,'No invariant bridge screen pixels')
        for kind,coordinates in fixed.items():
            limit=96 if kind=='static' else 64
            if len(coordinates)>limit:fixed[kind]=[coordinates[i*len(coordinates)//limit] for i in range(limit)]
        for phase,row in frames.items():
            row['expected_screen_pixels']={kind:[[x,y,*full_points[phase]['static' if kind=='static' else 'animated'][(x,y)]] for x,y in coordinates] for kind,coordinates in fixed.items()}
        changes={}
        for kind,minimum in [('water',8),('foam',2)]:
            coordinates=fixed[kind]
            proofs=[]
            images={phase:Image.open(args.output/row['capture_file']).convert('RGB') for phase,row in frames.items()}
            for point in sorted(coordinates):
                values=[images[phase].getpixel(point) for phase in range(8)]
                if max(max(abs(a-b) for a,b in zip(values[0],color)) for color in values[1:])<8:
                    continue
                proofs.append(dict(position=list(point), phase_rgb=[list(value) for value in values]))
                if len(proofs)>=16:
                    break
            assert len(proofs)>=minimum,(name,kind,'Visible native animation did not change enough pixels',len(proofs))
            changes[kind]=proofs
        return dict(map=name,fixture=fixture,frames=[frames[i] for i in range(8)],visible_pixel_change_proofs=changes,
                    static_pixel_kind_proofs=static_kind_proofs)

    native('RtcInitLocalTimeOffset',12,0)
    native('VarSet',0x40FE,7)
    assert native('ScriptGiveMon',260,50,0)==0
    native('ScriptSetMonMoveSlot',0,57,0)
    for flag in [lib.read16(s['gBadgeFlags']+2*i) for i in range(8)]+list(range(0x1AB0,0x1AB8)):
        native('FlagSet',flag)
    for trainer in range(1,1589):
        # Only fixture progress: no automatic trainer can interrupt a phase sample.
        address=save()+FLAG_OFFSET+(0x500+trainer)//8
        lib.write8(address,lib.read8(address)|(1<<((0x500+trainer)&7)))
    names=list(MAPS)+['Route105','Route108']
    allowed=set();walk_prefix='shore-animation';walk_surf_under_bridges=True
    exec(compile((ROOT/'tools/hoenn/native_water_walk.py').read_text(),__file__,'exec'),globals())
    compiled_payload=read_bytes(s['sJourneyDewfordShoreFrames'],len(payload))
    assert compiled_payload==payload, 'Compiled private shore frame asset differs from source'
    captures=[];cycles=[]
    group_mids={row['metatile'] for row in metadata['shore_and_bridge_underlay_groups']}
    world={}
    for name,(ox,oy) in MAPS.items():
        width,height,values=blocks[name]
        for index,value in enumerate(values):world[(index%width+ox,index//width+oy)]=(name,index%width,index//width,value)
    for name in MAPS:
        candidates=[]
        ox,oy=MAPS[name]
        width,height,values=blocks[name]
        occupied_source={(event['x'],event['y']) for event in maps[name]['object_events']}
        for index,value in enumerate(values):
            x,y=index%width,index//width
            if value>>12!=3 or value&0xC00 or water_behaviors[behaviors[name][index]] or (x,y) in occupied_source or (x,y) in warps[name]:
                continue
            wx,wy=x+ox,y+oy
            score=sum(row[3]&1023 in group_mids for point,row in world.items() if abs(point[0]-wx)<=6 and abs(point[1]-wy)<=4)
            candidates.append((score,-abs(wx-4)-abs(wy-4),x,y))
        assert candidates,name
        _,_,x,y=max(candidates)
        warp(name,x,y);native('SetPlayerAvatarTransitionFlags',1);step(60)
        assert location()==map_id(name)
        cycles.append(capture_cycle(name,dict(map=name,tile=[x,y],mode='foot',initial_position_fixture=True)))
        print('Native water and foam eight-phase cycle passed:',name,flush=True)

    pairs={}
    ids={mapping['id']:name for name,mapping in maps.items()}
    for name in MAPS:
        for connection in maps[name].get('connections') or []:
            if connection['map'] in ids:
                other=ids[connection['map']]
                pairs.setdefault(tuple(sorted((name,other))),(name,other,connection))
    assert len(pairs)==6,len(pairs)
    connection_checks=[];onload_samples=[]

    def passable_water(name,x,y):
        width,height,values=blocks[name]
        if not(0<=x<width and 0<=y<height):return False
        at=y*width+x
        return values[at]>>12 in (1,15) and not values[at]&0xC00 and water_behaviors[behaviors[name][at]] and currents[behaviors[name][at]] is None

    def cross_to(destination,key):
        before=location();origin=by_location[before];start=list(position())
        changed=False;first_ready=None;first_sample=None;header_sample=None;initialization=None
        for tick in range(500):
            previous_position=list(position())
            step(1,key if not changed else 0)
            if location()!=before and not changed:
                changed=True
                assert location()==map_id(destination),(origin,destination,location())
                header_sample=dict(frames_until_map_change=tick+1,last_source_tile=previous_position,
                    secondary_timer_at_map_change=lib.read16(s['sSecondaryTilesetAnimCounter']))
            if location()!=map_id(destination):continue
            # ApplyCurrentWarp changes the save location before decompression
            # finishes. The counter resets before queued BG graphics DMA, so
            # record initialization and observe its first completed DMA frame.
            if changed and initialization is None and lib.read16(s['sSecondaryTilesetAnimCounter'])==0:
                assert tick+1-header_sample['frames_until_map_change']<=12,('Missed native secondary initialization',destination,header_sample,tick)
                initialization=dict(secondary_timer=0,frame=tick+1,vblank_counter=lib.read32(s['gMain']+0x20),
                    pending_secondary_graphics_dma=pending_secondary_graphics_dma(),
                    private_shore_refresh_pending=bool(lib.read32(s['sJourneyDewfordShoreRefreshPending'])))
                if destination in MAPS and initialization['pending_secondary_graphics_dma']:
                    assert initialization['private_shore_refresh_pending'],('Private reload did not request its post-DMA refresh',destination,initialization)
            if changed and first_sample is None and initialization is not None and not pending_secondary_graphics_dma():
                assert tick+1-initialization['frame']<=2,('Secondary graphics DMA did not finish promptly',destination,initialization,tick)
                loaded_timer=lib.read16(s['sSecondaryTilesetAnimCounter'])
                assert loaded_timer<=2,('Missed first completed secondary graphics DMA frame',destination,initialization,tick,loaded_timer)
                refresh_pending=bool(lib.read32(s['sJourneyDewfordShoreRefreshPending']))
                assert not refresh_pending,('Post-DMA shore refresh still pending on the first loaded frame',destination,initialization,tick)
                label=f'shore-cross-{len(connection_checks)}-{origin}-to-{destination}-first-loaded'
                picture(label)
                capture=dict(file=label+'.png',sha256=digest((args.output/(label+'.png')).read_bytes()))
                captures.append(capture)
                first_sample=dict(source_map=origin,destination_map=destination,
                    start_tile=start,first_destination_tile=list(position()),
                    controller_key=key,frames_until_first_loaded=tick+1,capture_file=capture['file'],
                    secondary_timer=loaded_timer,initialization_observation=initialization,
                    pending_secondary_graphics_dma=[],private_shore_refresh_pending=False,**header_sample)
                if destination in MAPS:
                    try:
                        state=current_phase(check_palette=False)
                        clock=state['vblank_counter']
                        assert state['phase'] in {(clock>>4)&7,((clock-1)>>4)&7},('Load did not initialize current global phase',destination,state)
                    except AssertionError as error:
                        failure=dict(passed=False,rom_sha256=initial_sha,first_loaded_frame=first_sample,
                            assertion=str(error),pending_secondary_graphics_dma=pending_secondary_graphics_dma(),
                            no_animation_callback_clock_or_vram_writes=True)
                        diagnosis=[]
                        for after in range(1,5):
                            step(1)
                            row=dict(native_frames_after_failed_assertion=after,
                                pending_secondary_graphics_dma=pending_secondary_graphics_dma())
                            try:row['state']=current_phase(check_palette=False)
                            except AssertionError as later:row['assertion']=str(later)
                            diagnosis.append(row)
                        failure['postfailure_native_observations']=diagnosis
                        (args.output/'shore-animation-failure.json').write_text(json.dumps(failure,indent=2)+'\n')
                        raise
                    state.update(map=destination,first_loaded_frame=True,
                        initialization_secondary_counter_zero_observed=True,
                        pending_secondary_graphics_dma=[],private_shore_refresh_pending=False,
                        current_global_phase_after_native_bg_dma_verified=True,capture_file=capture['file'])
                    onload_samples.append(state)
                    first_sample['onload_sample_index']=len(onload_samples)-1
            if changed and first_sample is not None and idle():
                if first_ready is None:first_ready=tick
                if tick-first_ready>=45:
                    if destination in MAPS:
                        current_phase()
                        assert 'onload_sample_index' in first_sample,('Private bank initialization was not observed',destination)
                    first_sample.update(ready_destination_tile=list(position()),native_surf_mode=bool(lib.read8(s['gPlayerAvatar'])&8))
                    return first_sample
        raise AssertionError(('Controller coast crossing failed',destination,location(),position()))

    for pair,(name,other,connection) in sorted(pairs.items()):
        w,h,_=blocks[name];ow,oh,_=blocks[other]
        direction=connection['direction'];offset=connection['offset']
        dx,dy,key=dict(left=(-1,0,32),right=(1,0,16),up=(0,-1,64),down=(0,1,128))[direction]
        choices=[]
        for coordinate in range(max(0,offset),min(h if dx else w,offset+(oh if dx else ow))):
            x,y=((0 if dx<0 else w-1),coordinate) if dx else (coordinate,0 if dy<0 else h-1)
            xx,yy=((ow-1 if dx<0 else 0),coordinate-offset) if dx else (coordinate-offset,oh-1 if dy<0 else 0)
            cells=[(name,x-dx,y-dy),(name,x,y),(other,xx,yy),(other,xx+dx,yy+dy)]
            if all(passable_water(*cell) for cell in cells):choices.append(cells)
        assert choices,('No physical Surf seam',pair)
        cells=choices[len(choices)//2]
        warp(*cells[0]);native('SetPlayerAvatarTransitionFlags',8);step(60)
        outward=cross_to(other,key)
        assert lib.read8(s['gPlayerAvatar'])&8
        # Move one tile away from the seam before coming back; no position writes.
        step(16,key);step(20)
        inward=cross_to(name,{16:32,32:16,64:128,128:64}[key])
        assert lib.read8(s['gPlayerAvatar'])&8
        connection_checks.append(dict(maps=list(pair),initial_fixture=list(cells[0]),direction=direction,
                                      native_controller_crossings=2,global_phase_checked_on_private_bank_load=True,
                                      observed_crossings=[outward,inward],
                                      no_midcrossing_warps_or_clock_or_graphics_writes=True))
        print('Native shore load phase and controller roundtrip passed:',pair,flush=True)
    assert len(cycles)==4 and all(len(cycle['frames'])==8 for cycle in cycles)
    assert len(connection_checks)==6 and len(onload_samples)==10 and len(captures)==44
    review_mode=bool(lib.read8(s['gJourneyReviewMode']))
    lib.stop()
    assert digest((source/'pokeemerald.gba').read_bytes())==initial_sha
    report=dict(passed=True,kind='shore-animation',rom_sha256=initial_sha,review_mode=review_mode,
                compiled_rom=True,preflight=False,native_phase_count=8,animated_graphics=metadata['animated_graphics'],
                dma_runs=metadata['dma_runs'],frame_data_sha256=metadata['frame_data_sha256'],
                frame_data_hex=compiled_payload.hex(),
                cycles=cycles,captures=captures,connections=connection_checks,onload_samples=onload_samples,
                water_and_foam_visible_pixels_animate=True,sea_native_sand_and_private_composites_share_phase=True,
                one_shot_private_reload_refresh_after_native_bg_dma_verified=True,
                private_static_bridge_stairs_and_terrain_graphics_preserved=True,
                native_flag_animation_slots_excluded=True,hardware_scanout_pixels_verified=True,
                six_native_frgl_water_pattern_not_replaced=True,
                initial_party_progress_position_and_avatar_mode_are_fixtures=True,
                no_animation_callback_clock_or_vram_writes=True,full_campaign_playthrough=False)
    (args.output/'shore-animation.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--library',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    run(parser.parse_args())
