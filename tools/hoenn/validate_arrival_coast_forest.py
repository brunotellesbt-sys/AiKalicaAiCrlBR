"""Walk the Fuchsia video corner and the complete Route15/Route14 coast.

Initial travel, party, progress and encounter suppression are fixtures. After
each placement, collisions, Surf, landing and map transitions use controls;
the test never repairs avatar position, elevation, graphics, palettes or VRAM.
Whole source-map review is separate from these native camera/functional proofs.
"""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import sys

from integrated_ocean_seams import _animation_frames


ROOT = Path(__file__).resolve().parents[2]
INLET = 'JourneyFuchsiaInlet'
SEA = 'JourneyKantoSouthSea'
CITY = 'FuchsiaCity_Frlg'
EAST = 'JourneyRoute13Coast'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--library', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    options.output.mkdir(parents=True, exist_ok=True)
    marker = json.loads((options.source/'.journey-arrival-coast-review').read_bytes())
    metadata = marker['forest']
    assert metadata['kind'] == 'arrival-coast-exposed-fuchsia-forest'
    names = [row['map'] for row in metadata['maps']]
    assert {INLET, SEA, CITY, 'Route15_Frlg', 'Route14_Frlg', EAST}.issubset(names)
    # The original walking route crosses the gatehouse in Route15. Keeping
    # only the six exterior maps in the planner would reject the preserved
    # access before it could exercise either physical door warp.
    names.append('Route15_WestEntrance_1F_Frlg')
    initial_sha = hashlib.sha256((options.source/'pokeemerald.gba').read_bytes()).hexdigest()

    # Reuse the reviewed native input walker and exact current OBJ scanout
    # comparison, while limiting its route graph to this actual coastline.
    path = ROOT/'tools/hoenn/validate_integrated_piers.py'
    code = path.read_text().split('\nchecks = []\ntry:')[0]
    assert code.count('names = sorted(names)') == 1
    code = code.replace('names = sorted(names)', 'names = '+repr(sorted(names)))
    sys.argv = [str(path), '--source', str(options.source), '--library',
                str(options.library), '--output', str(options.output)]
    ns = {'__file__': str(path), '__name__': 'arrival_coast_forest_native'}
    exec(compile(code, str(path), 'exec'), ns)
    lib, native, step, walk, warp = (ns[key] for key in ('lib', 'native', 'step', 'walk', 'warp'))
    captures, states, fixtures, blockers, loaded, phases = [], [], [], [], [], []
    ocean_frames = _animation_frames(options.source)

    def capture(label, surfing=None, expect_elevation=None):
        state = ns['player_state']()
        if surfing is not None:
            assert state['surfing'] is surfing, (label, state)
        if expect_elevation is not None:
            assert state['elevation'] == expect_elevation, (label, state)
        assert state['sprite_visible'] and state['object_visible'], (label, state)
        # This compares the hat, body and feet with actual native scanout.
        state['avatar_pixels'] = ns['visible_avatar_pixels']()
        ns['picture'](label)
        file = label+'.png'
        captures.append(dict(file=file, sha256=hashlib.sha256((options.output/file).read_bytes()).hexdigest()))
        state['capture_file'] = file
        states.append(state)
        return state

    def arrive(name, x, y, label=None, surfing=None):
        walk((name, x, y))
        step(60)
        assert ns['location']() == ns['map_id'](name) and ns['position']() == (x, y)
        if label:
            return capture(label, surfing, 1 if surfing else 3 if surfing is False else None)

    def place(name, x, y, surfing):
        # Exactly one initial native travel/mode fixture for each independent
        # connected scenario; every subsequent step runs through controller input.
        warp(name, x, y)
        native('SetPlayerAvatarTransitionFlags', 8 if surfing else 1)
        step(90)
        fixtures.append(dict(map=name, tile=[x, y], surfing=surfing))
        assert ns['player_state']()['elevation'] == (1 if surfing else 3)
        ns['set_passability']()

    def blocked(key, label, target_map, target_x, target_y):
        before = ns['player_state']()
        layout = ns['layouts'][ns['maps'][target_map]['layout']]
        word = ns['blocks'][target_map][2][target_y*layout['width']+target_x]
        assert word & 0xC00, (label, hex(word), target_map, target_x, target_y)
        step(90, key)
        step(45)
        after = capture(label, before['surfing'], before['elevation'])
        assert (after['map'], after['tile'], after['surfing'], after['elevation']) == (
            before['map'], before['tile'], before['surfing'], before['elevation']), (before, after)
        blockers.append(dict(target=[target_map,target_x,target_y],target_word=word,
            key=key,before=before,after=after,blocked_by_native_controller=True))

    def loaded_bank(name):
        actual = ns['player_state']()
        assert actual['map'] == name
        layout = ns['layouts'][ns['maps'][name]['layout']]
        pointer = lib.read32(ns['s']['gMapHeader'])
        primary, secondary = lib.read32(pointer+16),lib.read32(pointer+20)
        assert primary == ns['s'][layout['primary_tileset']]
        assert secondary == ns['s'][layout['secondary_tileset']]
        result = dict(map=name,layout=layout['id'],primary=layout['primary_tileset'],
            secondary=layout['secondary_tileset'],primary_pointer=primary,
            secondary_pointer=secondary,tile=actual['tile'],loaded_from_final_rom=True)
        loaded.append(result)
        return result

    def read_bytes(address, size):
        return bytes(lib.read8(address+i) for i in range(size))

    def visible_native_water():
        """Read real hardware BG entries and matching native scanout pixels."""
        vram = read_bytes(0x06000000,65536)
        palette = [lib.read16(0x05000000+2*i)&0x7FFF for i in range(256)]
        rgb = [tuple(((word>>shift)&31)<<3 for shift in (0,5,10)) for word in palette]
        pixels = ctypes.string_at(lib.image(),240*160*4)
        display = lib.read16(0x04000000)
        assert display & 7 == 0
        samples=[]
        for bg in range(4):
            if not display & (0x100<<bg): continue
            control=lib.read16(0x04000008+2*bg)
            if control & 0x80: continue
            charbase=((control>>2)&3)*0x4000
            screenbase=((control>>8)&31)*0x800
            size=control>>14
            width,height=(512 if size in (1,3) else 256),(512 if size in (2,3) else 256)
            # BG scroll I/O is write-only. Observe the game's actual register
            # mirror, without advancing the emulator or changing its camera.
            sx=lib.read16(ns['s']['sGpuRegBuffer']+0x10+4*bg)&511
            sy=lib.read16(ns['s']['sGpuRegBuffer']+0x12+4*bg)&511
            for y in range(0,160,4):
                yy=(y+sy)%height;ty=yy//8
                for x in range(0,240,4):
                    xx=(x+sx)%width;tx=xx//8
                    at=screenbase+((ty//32)*(width//256)+tx//32)*2048+((ty%32)*32+tx%32)*2
                    word=int.from_bytes(vram[at:at+2],'little')
                    slot,bank=word&1023,word>>12
                    if charbase or slot not in (454,455): continue
                    px=7-xx%8 if word&1024 else xx%8
                    py=7-yy%8 if word&2048 else yy%8
                    at=slot*32+py*4+px//2
                    index=(vram[at]>>(4*(px&1)))&15
                    if not index: continue
                    color=rgb[bank*16+index]
                    actual=pixels[(y*240+x)*4:(y*240+x)*4+3]
                    if max(abs(a-b) for a,b in zip(color,actual))>7: continue
                    assert bank == 4, ('Visible native sea uses another palette',x,y,bg,slot,bank)
                    samples.append([x,y,*color])
        assert len(samples)>=150, ('Insufficient visible real sea pixels',len(samples))
        return dict(matching_visible_water_samples=len(samples),palette=4,
            samples=samples[::max(1,len(samples)//80)],actual_bg_vram_palette_and_scanout_compared=True)

    def animation_cycle():
        observed=set()
        for index in range(8):
            step(16)
            graphics=read_bytes(0x06000000+454*32,64)
            matches=[phase for phase,expected in enumerate(ocean_frames) if graphics==expected]
            assert matches, ('Native coast water does not match a real animation frame',index)
            observed.update(matches)
            pixels=visible_native_water()
            label='fuchsia-water-native-phase-'+str(index)
            ns['picture'](label)
            phases.append(dict(sample=index,valid_native_phases=matches,visible_pixels=pixels,
                water_vram_sha256=hashlib.sha256(graphics).hexdigest(),
                capture_file=label+'.png',capture_sha256=hashlib.sha256((options.output/(label+'.png')).read_bytes()).hexdigest()))
            # Recursive release packaging follows top-level captures. Keep
            # these same native phase images in that dependency manifest too.
            captures.append(dict(file=label+'.png',sha256=phases[-1]['capture_sha256']))
        assert observed==set(range(8)), ('Native coast cycle incomplete',observed)

    try:
        native('DisableWildEncounters',1)
        compatibility=[]
        for row in metadata['shore_aliases']['bank_compatibility']:
            old,new=ns['s'][row['original']],ns['s'][row['private']]
            assert all(lib.read8(old+i)==lib.read8(new+i) for i in range(24) if i not in range(12,16))
            compatibility.append(dict(original=row['original'],private=row['private'],
                header_fields_except_metatile_pointer_identical=True))
        primary=ns['s']['gTileset_JourneySeviiSea']
        old=ns['s']['gTileset_General_Frlg']
        old_table,new_table=lib.read32(old+12),lib.read32(primary+12)
        assert read_bytes(old_table,0x100*16)==read_bytes(new_table,0x100*16)
        for mid in (0x120,0x123,0x129,0x12A,0x130):
            original_words=[lib.read16(old_table+mid*16+2*i) for i in range(8)]
            actual_words=[lib.read16(new_table+mid*16+2*i) for i in range(8)]
            assert all(word>>12==4 for word in actual_words[:4] if word&1023 in (454,455))
            assert actual_words[4:]==original_words[4:], (mid,'Cliff upper art changed')

        # User's actual corner: approach on Surf, hit the intact western tree,
        # land on the reviewed dry margin, then use the actual Surf prompt.
        place(INLET,4,2,True)
        initial=capture('fuchsia-video-corner-surf',True,1)
        loaded_bank(INLET)
        animation_cycle()
        arrive(INLET,0,2,'fuchsia-west-forest-water',True)
        blocked(32,'fuchsia-west-forest-blocked',CITY,47,32)
        arrive(INLET,4,1,'fuchsia-native-water-shore',True)
        arrive(INLET,4,0,'fuchsia-native-dry-landing',False)
        landing=states[-1]
        blocked(64,'route15-complete-forest-base-blocked','Route15_Frlg',4,19)
        arrive(INLET,5,0,'fuchsia-dry-margin-east',False)
        blocked(16,'fuchsia-shore-tree-trunk-blocked',INLET,6,0)
        arrive(INLET,0,0,'fuchsia-dry-margin-west',False)
        blocked(32,'fuchsia-city-side-tree-blocked',CITY,47,30)
        arrive(INLET,4,0)
        prompts=len(ns['surf_prompts'])
        arrive(INLET,4,1,'fuchsia-native-surf-return',True)
        assert len(ns['surf_prompts'])>prompts, 'No native Surf prompt when leaving dry margin'
        arrive(INLET,4,2,'fuchsia-surf-roundtrip-restored',True)

        # Traverse the entire affected contiguous northern coastline, rather
        # than stopping at the first three trees shown by the short clip.
        arrive(INLET,35,2,'route15-west-seam-before',True)
        loaded_bank(INLET)
        arrive(SEA,0,2,'route15-west-seam-after',True)
        loaded_bank(SEA)
        for x in (12,28,35,36,46,57,60):
            arrive(SEA,x,2,'route15-route14-whole-coast-'+str(x),True)
        arrive(SEA,8,1,'route15-eastern-complete-bases',True)
        blocked(64,'route15-eastern-tree-base-blocked',SEA,8,0)
        arrive(SEA,44,1,'route14-southern-complete-bases',True)
        blocked(64,'route14-southern-tree-base-blocked',SEA,44,0)
        arrive(SEA,0,2,'route15-west-seam-return-before',True)
        arrive(INLET,35,2,'route15-west-seam-return-after',True)
        arrive(INLET,4,2,'fuchsia-controller-coast-return',True)

        # Independent east-facing Route14 forest corner, part of the same
        # real forest. Both the side and its finished foot remain navigable.
        place(EAST,1,1,True)
        loaded_bank(EAST)
        capture('route14-east-forest-corner',True,1)
        arrive(EAST,0,1,'route14-east-water-shore',True)
        blocked(32,'route14-east-whole-tree-blocked','Route14_Frlg',23,21)
        arrive(EAST,1,4,'route14-east-finished-foot',True)
        arrive(EAST,1,1,'route14-east-corner-return',True)

        # The original city walking space and its whole shrub/fence boundary
        # are tested from the actual land side, with its own loaded bank.
        place(CITY,44,30,False)
        loaded_bank(CITY)
        capture('fuchsia-native-city-camera-at-coast',False,3)
        for y in (26,30,35):
            arrive(CITY,44,y,'fuchsia-city-shrub-column-'+str(y),False)
            blocked(16,'fuchsia-city-shrub-blocked-'+str(y),CITY,45,y)
        arrive(CITY,42,35,'fuchsia-city-original-access-return',False)
        # Reach the ordinary Route15 path by the preserved city exit. This
        # exercises the two land-side loaded banks without crossing the forest.
        arrive('Route15_Frlg',18,12,'route15-original-land-access',False)
        loaded_bank('Route15_Frlg')
        arrive('Route14_Frlg',19,54,'route14-original-land-access',False)
        loaded_bank('Route14_Frlg')
        assignments=metadata['shore_aliases']['layout_assignments']
        assert {r['layout'] for r in assignments}.issubset({r['layout'] for r in loaded})
        required={tuple(pair) for pair in [(INLET,SEA),(SEA,INLET)]}
        actual={(row['source'][0],row['destination'][0]) for row in ns['transitions']}
        assert required.issubset(actual), ('Missing controlled coast roundtrip',actual)
        gate='Route15_WestEntrance_1F_Frlg'
        assert {('Route15_Frlg',gate),(gate,'Route15_Frlg')}.issubset(actual), (
            'Original Route15 gatehouse was not crossed through native doors',actual)
    finally:
        lib.stop()
    assert hashlib.sha256((options.source/'pokeemerald.gba').read_bytes()).hexdigest()==initial_sha
    report=dict(passed=True,kind='arrival-coast-forest-native',rom_sha256=initial_sha,
        elf_sha256=hashlib.sha256((options.source/'pokeemerald.elf').read_bytes()).hexdigest(),
        compiled_rom=True,native_validation_performed=True,initial_corner=initial,
        native_dry_landing=landing,native_surf_return_prompt=True,
        dry_margin_and_forest_controller_checks=blockers,loaded_banks=loaded,
        compiled_alias_header_identity=compatibility,native_water_animation=phases,
        all_eight_native_water_phases_visible=True,complete_coast_controller_roundtrip=True,
        route14_east_corner_controller_roundtrip=True,city_and_original_routes_accessible=True,
        original_route15_gatehouse_crossed_through_native_doors=True,
        captures=captures,states=states,transitions=ns['transitions'],walked_tiles=ns['walked'],
        fixtures=fixtures,party_progress_encounter_suppression_and_initial_travel_are_fixtures=True,
        no_midroute_position_avatar_elevation_map_grid_palette_or_vram_writes=True,
        whole_source_map_review_is_separate=True,full_campaign_playthrough=False)
    (options.output/'arrival-coast-forest-native.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Fuchsia and contiguous Route15/Route14 native forest coast passed:',ns['walked'],'tiles',flush=True)


if __name__=='__main__':
    main()
