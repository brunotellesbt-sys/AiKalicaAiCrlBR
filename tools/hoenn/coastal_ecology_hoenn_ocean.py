"""Observe native Hoenn water phases without changing their art or behavior.

Emerald's original eight-frame ocean includes both diagonal wave and dotted
phases. These are valid animation frames, rather than a second water palette.
This check keeps that observation separate from the repaired FRLG palettes.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import struct


def source_census(source):
    source = Path(source)
    layouts = {row['id']:row for row in json.loads(
        (source/'data/layouts/layouts.json').read_text())['layouts']}
    headers = (source/'src/data/tilesets/headers.h').read_text()
    definitions = (source/'src/data/tilesets/metatiles.h').read_text()
    cache, maps, used = {}, [], Counter()
    for path in sorted((source/'data/maps').glob('*/map.json')):
        mapping = json.loads(path.read_text())
        layout = layouts[mapping['layout']]
        if (layout['primary_tileset'] != 'gTileset_General' or
                mapping['map_type'] not in ('MAP_TYPE_ROUTE','MAP_TYPE_TOWN',
                                            'MAP_TYPE_CITY','MAP_TYPE_OCEAN_ROUTE')):
            continue
        raw = (source/layout['blockdata_filepath']).read_bytes()
        values = struct.unpack('<'+'H'*(len(raw)//2), raw)
        observed = False
        for mid in sorted({word&1023 for word in values}):
            bank = layout['primary_tileset' if mid<512 else 'secondary_tileset']
            index = mid if mid<512 else mid-512
            if bank not in cache:
                body = re.search(r'const struct Tileset '+re.escape(bank)+
                                 r'\s*=\s*\{(.*?)\};',headers,re.S)[1]
                symbol = re.search(r'\.metatiles\s*=\s*(\w+)',body)[1]
                file = re.search(r'\b'+re.escape(symbol)+r'\[\].*?"([^"]+)"',definitions)[1]
                blob = (source/file).read_bytes()
                cache[bank] = struct.unpack('<'+'H'*(len(blob)//2),blob)
            for word in cache[bank][index*8:index*8+4]:
                if word&1023 in (454,455):
                    assert word>>12==4, ('Hoenn ocean palette differs',path.parent.name,hex(mid),hex(word))
                    used[bank] += 1
                    observed = True
        if observed:
            maps.append(dict(map=path.parent.name,primary=layout['primary_tileset'],
                secondary=layout['secondary_tileset'],
                blockdata_sha256=hashlib.sha256(raw).hexdigest()))
    return dict(source_analysis_only=True,maps=maps,map_count=len(maps),
        water_graphics=[454,455],ocean_palette=4,
        water_banks=[dict(bank=bank,referenced_lower_water_words=count)
                     for bank,count in sorted(used.items())],
        all_referenced_hoenn_ocean_words_use_palette4=True,
        original_river_deep_water_dive_and_current_behaviors_unchanged=True)


def native_case(namespace):
    """Run inside the existing ocean validator's declared travel fixture."""
    from audit_generated_shore_animation import expected_channels, visible_graphic_pixels

    lib,s = namespace['lib'],namespace['s']
    native,step,warp = (namespace[key] for key in ('native','step','warp'))
    location,position,map_id = (namespace[key] for key in ('location','position','map_id'))
    source,args,picture = (namespace[key] for key in ('source','args','picture'))
    census = source_census(source)
    assert census['map_count']>=85
    frames = expected_channels(source,False)['water']['frames']
    frame_hashes = [hashlib.sha256(frame).hexdigest() for frame in frames]

    def read_bytes(address,count):
        return b''.join(lib.read32(address+i).to_bytes(4,'little')
                        for i in range(0,count,4))[:count]

    captures = []
    def capture(label):
        picture(label)
        path = args.output/(label+'.png')
        captures.append(dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))

    warp('MossdeepCity',79,34)
    native('SetPlayerAvatarTransitionFlags',8)
    step(90)
    observations = []
    seen = set()
    for _ in range(145):
        step(1)
        actual = read_bytes(0x06000000+432*32,30*32)
        digest = hashlib.sha256(actual).hexdigest()
        assert digest in frame_hashes, 'Water VRAM is not an original native Emerald frame'
        phase = frame_hashes.index(digest)
        if phase not in seen:
            seen.add(phase)
            visible = visible_graphic_pixels(read_bytes,lib,s,{454,455})
            assert len(visible)>1000, ('Native ocean pixels are not visible',phase,len(visible))
            capture('mossdeep-ocean-native-phase-'+str(phase))
            observations.append(dict(phase=phase,visible_native_water_pixels=len(visible),
                water_vram_sha256=digest,tile=list(position())))
    assert seen==set(range(8)),seen
    crossings = []
    animation_counter = s['sPrimaryTilesetAnimCounter']
    for destination,key,expected in [('JourneyMossdeepOuterSea',16,[0,26]),
                                     ('MossdeepCity',32,[79,34])]:
        # Start away from zero so a seam resetting the clock cannot look
        # like an ordinary wrap. Observe every controller frame; do not
        # write the clock or force an animation phase.
        for _ in range(256):
            if 64<=lib.read16(animation_counter)<=191:break
            step(1)
        counter_steps=[]
        for _ in range(100):
            if location()==map_id(destination):break
            before=lib.read16(animation_counter)
            step(1,key)
            after=lib.read16(animation_counter)
            assert (after-before)%256<=1, ('Native water clock restarted at seam',destination,before,after)
            counter_steps.append(dict(before=before,after=after,map=list(location())))
        step(40)
        assert location()==map_id(destination),(destination,location(),position())
        assert list(position())==expected,(destination,position())
        assert lib.read8(s['gPlayerAvatar'])&8
        layout = lib.read32(s['gMapHeader'])
        primary,secondary = lib.read32(layout+16),lib.read32(layout+20)
        assert (primary,secondary)==(s['gTileset_General'],s['gTileset_Mossdeep'])
        capture('mossdeep-ocean-seam-'+destination)
        crossings.append(dict(map=destination,tile=list(position()),surfing=True,
            primary_pointer=primary,secondary_pointer=secondary,
            native_primary_animation_counter_steps=counter_steps,
            primary_animation_clock_continuous_across_connection=True))
    return dict(source_census=census,phases=observations,crossings=crossings,
        captures=captures,all_eight_original_water_frames_observed=True,
        native_visible_pixels_match_loaded_graphics=True,
        identical_loaded_banks_across_mossdeep_city_outer_sea=True,
        controller_surf_crossing_both_directions=True,
        primary_animation_clock_continuous_across_both_connections=True,
        palette_vram_animation_clock_and_map_grid_not_written=True,
        initial_travel_progress_and_surf_state_are_fixtures=True)
