"""Strictly verify the observed final-ROM forest/camera/control proof.

The enclosing arrival/coast release verifier binds ROM/ELF hashes. This module
checks the route, actual bank assignments, pixels and complete native cycle;
it does not accept a source render as a native screenshot.
"""
from pathlib import Path
import re

from verify_sevii_integrated_piers_update import (
    require_true, verify_captures, verify_native_avatar_pixels)

INLET='JourneyFuchsiaInlet'
SEA='JourneyKantoSouthSea'
CITY='FuchsiaCity_Frlg'
EAST='JourneyRoute13Coast'
GATE='Route15_WestEntrance_1F_Frlg'
PRIMARY='gTileset_JourneySeviiSea'
LAVENDER='gTileset_JourneyKantoSeaLavenderTown'


def observed_route():
    rows=[]
    def add(name,m,x,y,surf=True):rows.append((name+'.png',m,[x,y],surf))
    for name,x,y,surf in [
        ('fuchsia-video-corner-surf',4,2,True),('fuchsia-west-forest-water',0,2,True),
        ('fuchsia-west-forest-blocked',0,2,True),('fuchsia-native-water-shore',4,1,True),
        ('fuchsia-native-dry-landing',4,0,False),('route15-complete-forest-base-blocked',4,0,False),
        ('fuchsia-dry-margin-east',5,0,False),('fuchsia-shore-tree-trunk-blocked',5,0,False),
        ('fuchsia-dry-margin-west',0,0,False),('fuchsia-city-side-tree-blocked',0,0,False),
        ('fuchsia-native-surf-return',4,1,True),('fuchsia-surf-roundtrip-restored',4,2,True),
        ('route15-west-seam-before',35,2,True)]:add(name,INLET,x,y,surf)
    add('route15-west-seam-after',SEA,0,2)
    for x in (12,28,35,36,46,57,60):add('route15-route14-whole-coast-'+str(x),SEA,x,2)
    for name,x,y in [('route15-eastern-complete-bases',8,1),('route15-eastern-tree-base-blocked',8,1),
        ('route14-southern-complete-bases',44,1),('route14-southern-tree-base-blocked',44,1),
        ('route15-west-seam-return-before',0,2)]:add(name,SEA,x,y)
    add('route15-west-seam-return-after',INLET,35,2)
    add('fuchsia-controller-coast-return',INLET,4,2)
    for name,x,y in [('route14-east-forest-corner',1,1),('route14-east-water-shore',0,1),
        ('route14-east-whole-tree-blocked',0,1),('route14-east-finished-foot',1,4),
        ('route14-east-corner-return',1,1)]:add(name,EAST,x,y)
    add('fuchsia-native-city-camera-at-coast',CITY,44,30,False)
    for y in (26,30,35):
        add('fuchsia-city-shrub-column-'+str(y),CITY,44,y,False)
        add('fuchsia-city-shrub-blocked-'+str(y),CITY,44,y,False)
    add('fuchsia-city-original-access-return',CITY,42,35,False)
    add('route15-original-land-access','Route15_Frlg',18,12,False)
    add('route14-original-land-access','Route14_Frlg',19,54,False)
    return rows


def verify(report,directory):
    directory=Path(directory)
    assert report['kind']=='arrival-coast-forest-native'
    require_true(report,['passed','compiled_rom','native_validation_performed',
        'native_surf_return_prompt','all_eight_native_water_phases_visible',
        'complete_coast_controller_roundtrip','route14_east_corner_controller_roundtrip',
        'city_and_original_routes_accessible','original_route15_gatehouse_crossed_through_native_doors',
        'party_progress_encounter_suppression_and_initial_travel_are_fixtures',
        'no_midroute_position_avatar_elevation_map_grid_palette_or_vram_writes',
        'whole_source_map_review_is_separate'])
    assert report['full_campaign_playthrough'] is False
    for name in ('rom_sha256','elf_sha256'):
        assert re.fullmatch('[a-f0-9]{64}',report[name]),name
    assert report['walked_tiles']==424
    assert report['fixtures']==[
        dict(map=INLET,tile=[4,2],surfing=True),
        dict(map=EAST,tile=[1,1],surfing=True),
        dict(map=CITY,tile=[44,30],surfing=False)]
    route=observed_route()
    phase_names=['fuchsia-water-native-phase-'+str(i)+'.png' for i in range(8)]
    images=verify_captures(report['captures'],directory,[row[0] for row in route]+phase_names)
    states=report['states']
    assert len(states)==len(route)==43
    by_capture={}
    for state,(name,m,tile,surfing) in zip(states,route):
        assert (state['capture_file'],state['map'],state['tile'],state['surfing'])==(name,m,tile,surfing)
        assert state['elevation']==state['tile_elevation']==(1 if surfing else 3)
        assert state['priority']==2
        require_true(state,['sprite_visible','object_visible'])
        verify_native_avatar_pixels(state['avatar_pixels'],images[name])
        by_capture[name]=state
    assert report['initial_corner']==states[0]
    assert report['native_dry_landing']==by_capture['fuchsia-native-dry-landing.png']

    banks=report['loaded_banks']
    expected=[(INLET,'LAYOUT_JOURNEYFUCHSIAINLET',LAVENDER,[4,2]),
        (INLET,'LAYOUT_JOURNEYFUCHSIAINLET',LAVENDER,[35,2]),
        (SEA,'LAYOUT_JOURNEYKANTOSOUTHSEA',LAVENDER,[0,2]),
        (EAST,'LAYOUT_JOURNEYROUTE13COAST',LAVENDER,[1,1]),
        (CITY,'LAYOUT_FUCHSIA_CITY','gTileset_FuchsiaCity',[44,30]),
        ('Route15_Frlg','LAYOUT_ROUTE15','gTileset_FuchsiaCity',[18,12]),
        ('Route14_Frlg','LAYOUT_ROUTE14',LAVENDER,[19,54])]
    assert len(banks)==len(expected)==7
    addresses={}
    for row,(name,layout,secondary,tile) in zip(banks,expected):
        assert (row['map'],row['layout'],row['primary'],row['secondary'],row['tile'])==(
            name,layout,PRIMARY,secondary,tile)
        require_true(row,['loaded_from_final_rom'])
        for symbol,field in ((PRIMARY,'primary_pointer'),(secondary,'secondary_pointer')):
            pointer=row[field]
            assert type(pointer) is int and 0x08000000<=pointer<0x0A000000 and pointer%4==0
            assert addresses.setdefault(symbol,pointer)==pointer
    assert len(set(addresses.values()))==3
    assert report['compiled_alias_header_identity']==[
        dict(original='gTileset_General_Frlg',private=PRIMARY,header_fields_except_metatile_pointer_identical=True),
        dict(original='gTileset_LavenderTown',private=LAVENDER,header_fields_except_metatile_pointer_identical=True)]

    blockers=report['dry_margin_and_forest_controller_checks']
    expected=[(CITY,47,32,0x041F,32,'fuchsia-west-forest-blocked.png'),
        ('Route15_Frlg',4,19,0x0424,64,'route15-complete-forest-base-blocked.png'),
        (INLET,6,0,0x0424,16,'fuchsia-shore-tree-trunk-blocked.png'),
        (CITY,47,30,0x041F,32,'fuchsia-city-side-tree-blocked.png'),
        (SEA,8,0,0x0424,64,'route15-eastern-tree-base-blocked.png'),
        (SEA,44,0,0x0424,64,'route14-southern-tree-base-blocked.png'),
        ('Route14_Frlg',23,21,0x041F,32,'route14-east-whole-tree-blocked.png'),
        *[(CITY,45,y,0x0405,16,'fuchsia-city-shrub-blocked-'+str(y)+'.png') for y in (26,30,35)]]
    assert len(blockers)==len(expected)==10
    for row,(name,x,y,word,key,capture) in zip(blockers,expected):
        assert row['target']==[name,x,y] and row['target_word']==word and row['key']==key
        assert row['target_word']&0xC00
        require_true(row,['blocked_by_native_controller'])
        before,after=row['before'],row['after']
        assert after==by_capture[capture]
        for field in ('map','tile','surfing','elevation','tile_elevation','priority'):
            assert before[field]==after[field],('Controller crossed forest',capture,field)

    assert report['transitions']==[
        dict(source=[INLET,35,2],destination=[SEA,0,2]),
        dict(source=[SEA,0,2],destination=[INLET,35,2]),
        dict(source=[CITY,47,22],destination=['Route15_Frlg',0,12]),
        dict(source=['Route15_Frlg',9,11],destination=[GATE,1,6]),
        dict(source=[GATE,11,6],destination=['Route15_Frlg',16,11]),
        dict(source=['Route15_Frlg',71,14],destination=['Route14_Frlg',0,54])]

    phases=report['native_water_animation']
    assert len(phases)==8 and [row['sample'] for row in phases]==list(range(8))
    phase_images=verify_captures([dict(file=row['capture_file'],sha256=row['capture_sha256'])
        for row in phases],directory,['fuchsia-water-native-phase-'+str(i)+'.png' for i in range(8)])
    observed=set();graphics=set()
    for row in phases:
        native_phase=row['valid_native_phases']
        assert len(native_phase)==1 and type(native_phase[0]) is int and native_phase[0] in range(8)
        observed.update(native_phase)
        graphic=row['water_vram_sha256'];assert re.fullmatch('[a-f0-9]{64}',graphic)
        graphics.add(graphic)
        pixels=row['visible_pixels']
        assert pixels['palette']==4 and pixels['matching_visible_water_samples']>=150
        require_true(pixels,['actual_bg_vram_palette_and_scanout_compared'])
        samples=pixels['samples']
        assert 75<=len(samples)<=100 and len({tuple(p[:2]) for p in samples})==len(samples)
        image=phase_images[row['capture_file']]
        for x,y,*color in samples:
            assert type(x) is int and type(y) is int and 0<=x<240 and 0<=y<160
            assert len(color)==3 and all(type(v) is int and 0<=v<=248 and v%8==0 for v in color)
            assert all(abs(actual-expected)<=7 for actual,expected in zip(image.getpixel((x,y)),color))
    assert observed==set(range(8)) and len(graphics)==8
    return True
