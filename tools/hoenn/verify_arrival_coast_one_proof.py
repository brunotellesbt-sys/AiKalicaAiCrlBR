"""Reject incomplete or stale native One coast observations."""
import hashlib
from pathlib import Path

from PIL import Image

from arrival_coast_cliffs import AFTER
from arrival_coast_review_contract import PREPARED_SHA256
from arrival_coast_water import EXPECTED_UPPER, PRIMARY, WATER_SLOTS

ONE='OneIsland_Frlg'
BEACH='OneIsland_TreasureBeach_Frlg'
LINK='JourneySurfLink05000'
FOUR='FourIsland_Frlg'
PRIMARY_FILE='data/tilesets/primary/general_frlg/journey_sevii_sea_metatiles.bin'


def require_true(info,fields):
    for field in fields:
        assert info[field] is True,field


def surf_state(state,name=None,tile=None):
    assert state['surfing'] is True and state['elevation']==1
    assert state['priority']==2 and state['sprite_visible'] is state['object_visible'] is True
    if name is not None:assert state['map']==name
    if tile is not None:assert state['tile']==tile


def capture(path,sha):
    path=Path(path)
    assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==sha,path
    with Image.open(path) as image:
        assert image.size==(240,160)
        return image.convert('RGB')


def verify(report,directory):
    directory=Path(directory)
    assert report['kind']=='arrival-coast-one-native' and report['passed'] is True
    require_true(report,['compiled_rom','native_validation_performed',
        'all_eight_animation_phases_checked_in_vram_and_visible_upper_pixels',
        'initial_placement_party_progress_and_encounter_suppression_are_fixtures',
        'no_midtrip_coordinate_elevation_avatar_palette_or_vram_writes'])
    assert report['full_campaign_playthrough'] is False
    assert all(len(report[field])==64 for field in ('rom_sha256','elf_sha256'))
    compiled=report['compiled_upper_water']
    assert compiled['file']==PRIMARY_FILE and compiled['sha256']==PREPARED_SHA256[PRIMARY_FILE]
    assert compiled['symbol']=='gMetatiles_JourneySeviiSea'
    assert compiled['upper_words_changed']==30 and compiled['all_native_upper_words_match'] is True
    assert {int(k):v for k,v in compiled['graphic_counts'].items()}==EXPECTED_UPPER

    banks=report['loaded_camera_banks']
    assert {row['map'] for row in banks}=={ONE,BEACH,LINK,FOUR}
    expected_secondary={ONE:'gTileset_JourneySeviiIntegrated123',BEACH:'gTileset_JourneySeviiIntegrated123',
                        LINK:'gTileset_SeviiIslands123',FOUR:'gTileset_JourneySeviiIntegrated45'}
    for row in banks:
        require_true(row,['loaded_from_final_rom'])
        assert row['primary']==PRIMARY and row['secondary']==expected_secondary[row['map']]
        assert all(0x08000000<=row[field]<0x0A000000 for field in ('primary_pointer','secondary_pointer'))
    # The approach and return must both observe the route's camera bank.
    assert sum(row['map']==LINK for row in banks)==2

    captures=report['captures']
    by_file={row['file']:row for row in captures}
    assert len(by_file)==len(captures)
    images={}
    for filename,row in by_file.items():
        relative=Path(filename);assert not relative.is_absolute() and '..' not in relative.parts
        images[filename]=capture(directory/filename,row['sha256'])

    cycles=report['animation_cycles']
    expected_cameras={'one-cross-map-upper-water':(ONE,{430,431,432,433}),
        'treasure-cross-map-upper-water':(BEACH,{430,431,432,433}),
        'four-upper-shore-water':(FOUR,{478,479,480,481})}
    assert len(cycles)==3 and {row['camera'] for row in cycles}==set(expected_cameras)
    for cycle in cycles:
        assert cycle['all_eight_phases_in_both_native_animation_groups'] is True
        name,required=expected_cameras[cycle['camera']]
        assert required<=set(cycle['visible_graphics'])
        rows=cycle['rows'];assert len(rows)==16 and [row['sample'] for row in rows]==list(range(16))
        phases={'current':set(),'sand':set()};visible=set()
        for row in rows:
            assert row['map']==name and set(row['valid_native_phases'])==set(phases)
            for group,values in row['valid_native_phases'].items():
                assert values and set(values)<=set(range(8));phases[group].update(values)
            pixels=row['visible_pixels']
            require_true(pixels,['actual_top_bg_vram_palette_and_scanout_compared',
                'sprites_excluded_by_oam_rectangles','mismatching_water_pixels_not_discarded'])
            assert pixels['palette']==4 and pixels['matching_visible_upper_water_pixels']>=24
            counts={int(slot):count for slot,count in pixels['graphic_pixel_counts'].items()}
            assert set(counts)==WATER_SLOTS and all(count>=0 for count in counts.values())
            assert sum(counts.values())==pixels['matching_visible_upper_water_pixels']
            visible.update(slot for slot,count in counts.items() if count)
            samples=pixels['samples'];assert samples
            assert {sample[2] for sample in samples}=={slot for slot,count in counts.items() if count}
            filename=row['capture_file']
            assert by_file[filename]['sha256']==row['capture_sha256']
            image=images[filename]
            for x,y,slot,r,g,b in samples:
                assert 0<=x<240 and 0<=y<160 and slot in WATER_SLOTS
                assert all(abs(a-c)<=7 for a,c in zip(image.getpixel((x,y)),(r,g,b))),('Water scanout PNG mismatch',filename,x,y)
        assert all(values==set(range(8)) for values in phases.values())
        assert required<=visible

    cliff=report['west_cliff']
    actual={tuple(row['cell']):row for row in cliff['compiled_cells']}
    assert set(actual)==set(AFTER) and len(actual)==49
    for cell,value in AFTER.items():
        value=0x1674 if cell==(0,7) else value
        row=actual[cell]
        assert row['word']==value and row['metatile']==value&1023
        assert row['elevation']==value>>12 and row['collision']==(value>>10)&3
    assert cliff['no_interaction_with_permanent_scenery'] is True
    limits=cliff['blocked_north'];assert len(limits)==1
    limit=limits[0]
    assert limit['target']==[ONE,0,7] and limit['key']==64 and limit['background_word']==0x1674
    assert limit['blocked_by_native_controller'] is True
    for state in(limit['before'],limit['after']):surf_state(state,ONE,[0,8])
    rock=cliff['boundary_rock']
    assert rock['tile']==[0,7] and rock['native_graphics_info']=='gObjectEventGraphicsInfo_BreakableRockFrlg'
    assert rock['all_current_native_obj_frame_bands_compared'] is True
    pixels=rock['pixels'];require_true(pixels,['exact_current_vram_frame_compared','background_color_coincidence_not_used'])
    assert pixels['expected_opaque_pixels']>=100
    assert pixels['matching_scanout_pixels']==pixels['expected_opaque_pixels']
    assert len(pixels['expected_scanout_pixels'])==pixels['expected_opaque_pixels']
    assert all(band['expected']>=8 and band['expected']==band['matched'] for band in pixels['head_body_feet_bands'])
    image=images[rock['capture_file']]
    for x,y,r,g,b,band,exclusive in pixels['expected_scanout_pixels']:
        assert all(abs(a-c)<=7 for a,c in zip(image.getpixel((x,y)),(r,g,b))),('Rock clipped in actual scanout',x,y)
    trips=cliff['roundtrip_connections']
    pairs={(row['source'][0],row['destination'][0]) for row in trips}
    assert {(LINK,ONE),(ONE,LINK),(ONE,BEACH),(BEACH,ONE)}<=pairs
    surf_state(cliff['visible_before_crossing'],LINK,[14,6])

    boulder=report['orphan_and_boulder']
    assert boulder['terminal_roof_preserved'] is boulder['whole_boulder_seen_from_both_maps'] is True
    quartet=boulder['retained_complete_cross_map_boulder']
    assert [(row['map'],row['cell'],row['word']&1023) for row in quartet]==[
        (ONE,[2,19],0x1CB),(ONE,[3,19],0x1CC),(BEACH,[2,0],0x1D3),(BEACH,[3,0],0x1D4)]
    removed=boulder['removed_orphan_cells_traversed_by_native_surf']
    assert len(removed)==3 and {tuple(row['tile']) for row in removed}=={(16,18),(18,19),(19,19)}
    for state in removed:surf_state(state,ONE)
    assert report['fixtures']==[dict(map=LINK,tile=[14,6],surfing=True),dict(map=FOUR,tile=[1,20],surfing=True)]
    for state in report['states']:surf_state(state)
    return report
