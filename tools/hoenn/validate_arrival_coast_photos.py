"""Observe the repaired One coast in native mGBA, not source renders.

Initial placement, party/progress and encounter suppression are declared
geometry fixtures. After each placement, movement and crossings use controls;
no map, palette, VRAM, actor coordinates, elevation or graphics are repaired.
"""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import struct
import sys

from PIL import Image
from arrival_coast_water import EXPECTED_UPPER, PRIMARY, WATER_SLOTS
from integrated_ocean_seams import _field, _header

ROOT = Path(__file__).resolve().parents[2]
ONE = 'OneIsland_Frlg'
BEACH = 'OneIsland_TreasureBeach_Frlg'
LINK = 'JourneySurfLink05000'
FOUR = 'FourIsland_Frlg'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def animation_frames(source, folder, first, slots):
    result=[]
    for phase in range(8):
        path=source/f'data/tilesets/primary/general_frlg/anim/{folder}/{phase}.png'
        with Image.open(path) as image:
            assert image.mode=='P'
            raw=bytearray()
            for slot in slots:
                index=slot-first
                x,y=(index%(image.width//8))*8,(index//(image.width//8))*8
                data=list(image.crop((x,y,x+8,y+8)).getdata())
                assert set(data)<={0,3,4,5,6,7},(path,slot,set(data))
                raw.extend(data[i]|data[i+1]<<4 for i in range(0,64,2))
        result.append(bytes(raw))
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--library',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    options=parser.parse_args()
    options.output.mkdir(parents=True,exist_ok=True)
    source=options.source
    rom_sha,elf_sha=digest(source/'pokeemerald.gba'),digest(source/'pokeemerald.elf')
    marker=json.loads((source/'.journey-arrival-coast-review').read_bytes())
    assert marker['water']['changed_upper_water_words']==30
    path=ROOT/'tools/hoenn/validate_integrated_piers.py'
    code=path.read_text().split('\nchecks = []\ntry:')[0]
    assert code.count('names = sorted(names)')==1
    code=code.replace('names = sorted(names)','names = '+repr([ONE,BEACH,LINK,FOUR]))
    sys.argv=[str(path),'--source',str(source),'--library',str(options.library),'--output',str(options.output)]
    ns={'__file__':str(path),'__name__':'arrival_coast_photos_native'}
    exec(compile(code,str(path),'exec'),ns)
    lib,native,step,warp,walk=(ns[k] for k in ('lib','native','step','warp','walk'))
    captures,states,fixtures,loaded,phases,blockers=[],[],[],[],[],[]

    def read_bytes(address,size):
        return bytes(lib.read8(address+i) for i in range(size))

    def capture(label):
        state=ns['player_state']()
        assert state['surfing'] and state['elevation']==1,state
        assert state['priority']==2 and state['sprite_visible'] and state['object_visible'],state
        ns['picture'](label)
        state['capture_file']=label+'.png'
        captures.append(dict(file=label+'.png',sha256=digest(options.output/(label+'.png'))))
        states.append(state)
        return state

    def arrive(name,x,y,label=None):
        walk((name,x,y));step(60)
        state=ns['player_state']()
        assert state['map']==name and state['tile']==[x,y],state
        assert state['surfing'] and state['elevation']==1,state
        return capture(label) if label else state

    def place(name,x,y,label):
        warp(name,x,y);native('SetPlayerAvatarTransitionFlags',8);step(90)
        fixtures.append(dict(map=name,tile=[x,y],surfing=True))
        ns['set_passability'](water_only=True)
        return capture(label)

    def bank(name):
        state=ns['player_state']();assert state['map']==name,state
        layout=ns['layouts'][ns['maps'][name]['layout']]
        address=lib.read32(ns['s']['gMapHeader'])
        primary,secondary=lib.read32(address+16),lib.read32(address+20)
        assert primary==ns['s'][layout['primary_tileset']]
        assert secondary==ns['s'][layout['secondary_tileset']]
        assert layout['primary_tileset']==PRIMARY
        row=dict(map=name,tile=state['tile'],primary=layout['primary_tileset'],secondary=layout['secondary_tileset'],
            primary_pointer=primary,secondary_pointer=secondary,loaded_from_final_rom=True)
        loaded.append(row);return row

    def sprite_rectangles():
        result=[]
        dims=[[(8,8),(16,16),(32,32),(64,64)],[(16,8),(32,8),(32,16),(64,32)],[(8,16),(8,32),(16,32),(32,64)]]
        for index in range(128):
            at=0x07000000+index*8;a0,a1=lib.read16(at),lib.read16(at+2)
            if a0&0x300==0x200 or a0>>14>2:continue
            w,h=dims[a0>>14][a1>>14];x,y=a1&511,a0&255
            if x>=256:x-=512
            if y>=160:y-=256
            if x<240 and x+w>0 and y<160 and y+h>0:result.append((x,y,w,h))
        return result

    def visible_native_upper_water():
        """Resolve top opaque hardware BG pixels, then compare scanout.

        Sprite rectangles are excluded instead of skipping mismatching water
        pixels. A wrong palette in an upper water layer therefore fails.
        """
        vram=read_bytes(0x06000000,65536)
        palettes=[lib.read16(0x05000000+2*i)&32767 for i in range(256)]
        rgb=[tuple(((word>>shift)&31)<<3 for shift in (0,5,10)) for word in palettes]
        image=ctypes.string_at(lib.image(),240*160*4)
        display=lib.read16(0x04000000);assert display&7==0
        backgrounds=[]
        for bg in range(4):
            if not display&(0x100<<bg):continue
            control=lib.read16(0x04000008+2*bg);assert not control&0x80
            size=control>>14
            backgrounds.append(dict(bg=bg,priority=control&3,charbase=((control>>2)&3)*0x4000,
                screenbase=((control>>8)&31)*0x800,
                width=512 if size in(1,3) else 256,height=512 if size in(2,3) else 256,
                sx=lib.read16(ns['s']['sGpuRegBuffer']+0x10+4*bg)&511,
                sy=lib.read16(ns['s']['sGpuRegBuffer']+0x12+4*bg)&511))
        backgrounds.sort(key=lambda row:(row['priority'],row['bg']))
        sprites=sprite_rectangles();counts={str(slot):0 for slot in WATER_SLOTS};samples_by_graphic={slot:[] for slot in WATER_SLOTS}
        for y in range(160):
            for x in range(240):
                if any(xx<=x<xx+w and yy<=y<yy+h for xx,yy,w,h in sprites):continue
                top=None
                for bg in backgrounds:
                    xx,yy=(x+bg['sx'])%bg['width'],(y+bg['sy'])%bg['height'];tx,ty=xx//8,yy//8
                    at=bg['screenbase']+((ty//32)*(bg['width']//256)+tx//32)*2048+((ty%32)*32+tx%32)*2
                    word=int.from_bytes(vram[at:at+2],'little');slot=word&1023
                    px=7-xx%8 if word&1024 else xx%8;py=7-yy%8 if word&2048 else yy%8
                    at=bg['charbase']+slot*32+py*4+px//2
                    index=(vram[at]>>(4*(px&1)))&15
                    if index:top=(bg,word,slot,index);break
                if top is None:continue
                bg,word,slot,index=top
                if bg['charbase'] or slot not in WATER_SLOTS:continue
                assert word>>12==4,('Upper water uses another native palette',x,y,slot,hex(word))
                assert index in(3,4,5,6,7),(slot,index)
                expected=rgb[64+index];actual=image[(y*240+x)*4:(y*240+x)*4+3]
                assert all(abs(a-b)<=7 for a,b in zip(expected,actual)),('Upper-water native scanout mismatch',x,y,slot,expected,list(actual))
                counts[str(slot)]+=1
                if len(samples_by_graphic[slot])<8:samples_by_graphic[slot].append([x,y,slot,*expected])
        assert sum(counts.values())>=24,('No visible upper native water',counts,ns['player_state']())
        return dict(palette=4,matching_visible_upper_water_pixels=sum(counts.values()),graphic_pixel_counts=counts,
            samples=[sample for slot in sorted(samples_by_graphic) for sample in samples_by_graphic[slot]],actual_top_bg_vram_palette_and_scanout_compared=True,sprites_excluded_by_oam_rectangles=True,
            mismatching_water_pixels_not_discarded=True)

    native_frames={
        'current':animation_frames(source,'water_current_landwatersedge',416,(430,431,432,433)),
        'sand':animation_frames(source,'sandwatersedge',464,(478,479,480,481)),
    }

    def cycle(label,required):
        seen={'current':set(),'sand':set()};visible=set();rows=[]
        # Native shoreline updates every8frames, while current water updates
        # every16. Sample16 consecutive8frame steps without native call
        # trampolines between observations, covering both complete cycles.
        for index in range(16):
            step(8)
            matches={}
            for group,slots in [('current',(430,431,432,433)),('sand',(478,479,480,481))]:
                actual=b''.join(read_bytes(0x06000000+slot*32,32) for slot in slots)
                matches[group]=[phase for phase,expected in enumerate(native_frames[group]) if expected==actual]
                assert matches[group],('Loaded upper water glyph is not a native animation phase',group,index)
                seen[group].update(matches[group])
            pixels=visible_native_upper_water()
            visible.update(int(slot) for slot,count in pixels['graphic_pixel_counts'].items() if count)
            file=label+'-phase-'+str(index)+'.png';ns['picture'](file[:-4])
            captures.append(dict(file=file,sha256=digest(options.output/file)))
            row=dict(sample=index,map=ns['by_location'][ns['location']()],valid_native_phases=matches,
                visible_pixels=pixels,capture_file=file,capture_sha256=digest(options.output/file))
            rows.append(row);phases.append(row)
        assert all(values==set(range(8)) for values in seen.values()),seen
        assert set(required)<=visible,('Expected upper glyphs not visible in this camera',label,required,visible)
        return dict(camera=label,rows=rows,all_eight_phases_in_both_native_animation_groups=True,visible_graphics=sorted(visible))

    def rock_pixels():
        candidates=[]
        for index in range(16):
            address=ns['s']['gObjectEvents']+36*index
            if lib.read8(address)&1 and lib.read8(address+8)==marker['limits']['local_id']:
                if lib.read16(address+16)-7==0 and lib.read16(address+18)-7==7:candidates.append(index)
        assert len(candidates)==1,('Native boundary rock object missing',candidates)
        # Reuse the exact OBJ-frame observer with a selected object index;
        # this only reads memory and never swaps player and scenery actors.
        pixels_code=path.read_text().split('def visible_avatar_pixels():',1)[1].split('\n\ndef assert_foot',1)[0]
        old="    obj = s['gObjectEvents'] + lib.read8(s['gPlayerAvatar'] + 5) * 36"
        assert pixels_code.count(old)==1
        pixels_code=pixels_code.replace(old,"    obj = s['gObjectEvents'] + selected_object * 36")
        pixel_namespace=dict(ns,selected_object=candidates[0])
        exec(compile('def selected_rock_pixels():'+pixels_code,str(path),'exec'),pixel_namespace)
        data=pixel_namespace['selected_rock_pixels']()
        return dict(object_index=candidates[0],local_id=marker['limits']['local_id'],
            tile=[0,7],capture_file='one-whole-boundary-rock-before-approach.png',native_graphics_info='gObjectEventGraphicsInfo_BreakableRockFrlg',pixels=data,
            all_current_native_obj_frame_bands_compared=True)

    try:
        native('DisableWildEncounters',1)
        headers=(source/'src/data/tilesets/headers.h').read_text()
        metatile_symbol=_field(_header(headers,PRIMARY),'metatiles')
        table=next(row for row in marker['water']['tables'] if row['tileset']==PRIMARY)
        expected=(source/table['file']).read_bytes();actual=read_bytes(ns['s'][metatile_symbol],len(expected))
        assert actual==expected
        words=struct.unpack('<'+'H'*(len(actual)//2),actual)
        changed=table['changed_words'];assert len(changed)==30
        assert {slot:sum(r['graphic']==slot for r in changed) for slot in WATER_SLOTS}==EXPECTED_UPPER
        for row in changed:
            assert row['word_index']%8>=4 and words[row['word_index']]==row['after']
            assert row['before']^row['after']==0x2000 and row['after']>>12==4
        compiled=dict(symbol=metatile_symbol,file=table['file'],sha256=hashlib.sha256(actual).hexdigest(),
            upper_words_changed=30,graphic_counts=EXPECTED_UPPER,all_native_upper_words_match=True)

        place(LINK,14,6,'west-route-before-entry');bank(LINK)
        before_camera=capture('west-route-one-neighbor-camera')
        arrive(ONE,0,13,'one-cape-from-new-surf-connection');bank(ONE)
        arrive(ONE,0,9,'one-whole-boundary-rock-before-approach')
        rock=rock_pixels()
        arrive(ONE,0,8,'one-west-visible-northern-limit')
        before=ns['player_state']();assert native('MapGridGetCollisionAt',7,14)==1
        step(90,64);step(45)
        blocked=capture('one-west-up-blocked-by-whole-rock')
        assert blocked['tile']==before['tile']==[0,8] and blocked['map']==ONE
        blockers.append(dict(target=[ONE,0,7],key=64,before=before,after=blocked,
            blocked_by_native_controller=True,background_word=ns['blocks'][ONE][2][7*24]))
        assert blockers[-1]['background_word']==0x1674
        step(1,1);step(90)
        assert ns['idle']() and ns['player_state']()['tile']==[0,8]
        capture('one-boundary-rock-no-interaction')
        arrive(ONE,0,13)
        arrive(LINK,14,6,'west-route-return-camera');bank(LINK)
        assert len(ns['transitions'])>=2
        arrive(ONE,0,13)
        cliff=[]
        for row in marker['cliffs']['changed_cells']:
            x,y=row['cell'];wanted=0x1674 if(x,y)==(0,7) else row['after']
            actual_id=native('MapGridGetMetatileIdAt',x+7,y+7)
            elevation=native('MapGridGetElevationAt',x+7,y+7)
            collision=native('MapGridGetCollisionAt',x+7,y+7)
            assert actual_id==wanted&1023 and elevation==wanted>>12 and collision==(wanted>>10)&3
            cliff.append(dict(cell=[x,y],word=wanted,metatile=actual_id,elevation=elevation,collision=collision))
        assert len(cliff)==49
        arrive(ONE,4,18,'one-complete-cross-map-boulder')
        bank(ONE)
        boulder=marker['water']['terminal_orphan']['retained_complete_cross_map_boulder']
        source_quartet=[]
        for (name,x,y),word in zip(boulder['cells'],boulder['words']):
            w,h,values=ns['blocks'][name];assert values[y*w+x]==word
            grid_y=y+20 if name==BEACH else y
            assert native('MapGridGetMetatileIdAt',x+7,grid_y+7)==word&1023
            source_quartet.append(dict(map=name,cell=[x,y],word=word))
        boulder_cycle=cycle('one-cross-map-upper-water',set((430,431,432,433)))
        arrive(BEACH,4,1,'treasure-boulder-from-other-side');bank(BEACH)
        reverse_cycle=cycle('treasure-cross-map-upper-water',set((430,431,432,433)))
        arrive(ONE,4,18,'one-boulder-return-seam')
        removed=[]
        for x,y in marker['water']['terminal_orphan']['removed_top_cells']:
            state=arrive(ONE,x,y,'orphan-cleared-'+str(x)+'-'+str(y))
            assert native('MapGridGetMetatileIdAt',x+7,y+7)==0x12B
            assert native('MapGridGetCollisionAt',x+7,y+7)==0
            removed.append(state)
        for x in(18,19):
            assert ns['blocks'][BEACH][2][x]&1023==0x3A5
        place(FOUR,1,20,'four-whole-coastal-corner');bank(FOUR)
        shore_cycle=cycle('four-upper-shore-water',set((478,479,480,481)))
        report=dict(kind='arrival-coast-one-native',passed=True,rom_sha256=rom_sha,elf_sha256=elf_sha,
            compiled_rom=True,native_validation_performed=True,compiled_upper_water=compiled,
            loaded_camera_banks=loaded,animation_cycles=[boulder_cycle,reverse_cycle,shore_cycle],
            all_eight_animation_phases_checked_in_vram_and_visible_upper_pixels=True,
            west_cliff=dict(compiled_cells=cliff,boundary_rock=rock,blocked_north=blockers,
                no_interaction_with_permanent_scenery=True,roundtrip_connections=ns['transitions'],
                visible_before_crossing=before_camera),
            orphan_and_boulder=dict(retained_complete_cross_map_boulder=source_quartet,
                removed_orphan_cells_traversed_by_native_surf=removed,
                terminal_roof_preserved=True,whole_boulder_seen_from_both_maps=True),
            captures=captures,states=states,fixtures=fixtures,
            initial_placement_party_progress_and_encounter_suppression_are_fixtures=True,
            no_midtrip_coordinate_elevation_avatar_palette_or_vram_writes=True,
            full_campaign_playthrough=False)
    finally:
        lib.stop()
    assert digest(source/'pokeemerald.gba')==rom_sha and digest(source/'pokeemerald.elf')==elf_sha
    (options.output/'arrival-coast-one-native.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Native One coast: 30 upper words, eight phases in three cameras, west limit and cross-map boulder passed.',flush=True)


if __name__=='__main__':
    main()
