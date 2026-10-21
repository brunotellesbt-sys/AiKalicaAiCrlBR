"""Move each Sevii terminal onto its own town's continuous wooden approach.

Stage only: the caller commits the atomic candidate layer. Existing offshore
map IDs remain open sea, retaining every physical world connection.
"""
import copy
import io
import json
import re
import struct

from PIL import Image

from render_sea_maps import MapRenderer


ISLANDS = ['One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven']
CONFIG = {
    'One': dict(map='OneIsland_TreasureBeach_Frlg', terminal=[14, 0], front=6,
                bridge=[11, 0, 3, 7], start=['OneIsland_Frlg', 12, 17],
                boarding=[12, 6, 12, 7, 128], boats=[(9, 10), (19, 10)]),
    'Two': dict(map='TwoIsland_Frlg', terminal=[2, 8], front=14,
                bridge=[9, 8, 3, 7], start=['TwoIsland_Frlg', 10, 7],
                boarding=[10, 14, 10, 15, 128], boats=[(13, 18), (5, 18)]),
    'Three': dict(map='ThreeIsland_Port_Frlg', terminal=[4, 13], front=19,
                  bridge=[11, 13, 3, 7], start=['ThreeIsland_Port_Frlg', 12, 12],
                  boarding=[13, 17, 14, 17, 16], boats=[(16, 17), (22, 17)]),
    'Four': dict(map='FourIsland_Frlg', terminal=[2, 28], front=34,
                 bridge=[9, 28, 3, 7], start=['FourIsland_Frlg', 10, 27],
                 boarding=[10, 34, 10, 35, 128], boats=[(13, 37), (5, 38)]),
    'Five': dict(map='FiveIsland_Frlg', terminal=[14, 13], front=19,
                 bridge=[11, 14, 3, 6], start=['FiveIsland_Frlg', 12, 13],
                 boarding=[11, 15, 10, 15, 32], boats=[(8, 17), (4, 18)]),
    'Six': dict(map='SixIsland_Frlg', terminal=[3, 23], front=29,
                bridge=[10, 23, 3, 7], start=['SixIsland_Frlg', 11, 22],
                boarding=[3, 29, 2, 29, 32], boats=[]),
    'Seven': dict(map='SevenIsland_Frlg', terminal=[17, 13], front=19,
                  bridge=[14, 13, 3, 7], start=['SevenIsland_Frlg', 16, 12],
                  front_map='SevenIsland_SevaultCanyon_Entrance_Frlg', front_y=0,
                  front_rows=2, boarding=[14, 1, 13, 1, 32],
                  boats=[(12, 4), (20, 7)]),
}


def repair(layer):
    source = layer.source
    renderer = MapRenderer(source)
    touched = set()

    def raw(path):
        return layer.outputs[path] if path in layer.outputs else (source / path).read_bytes()

    def read_json(path):
        return json.loads(raw(path))

    def stage(path, data):
        layer.stage(path, data)
        touched.add(path)

    def stage_json(path, value):
        stage(path, json.dumps(value, indent=2) + '\n')

    layout_data = read_json('data/layouts/layouts.json')
    layouts = {row['id']: row for row in layout_data['layouts']}
    old_ports = read_json('.journey-sevii-harbors')['ports']
    old_bridges = read_json('.journey-dewford-coast-safety')['piers']['town_bridges']
    maps, original_maps, grids, changes = {}, {}, {}, []

    def load(name):
        if name not in maps:
            maps[name] = read_json(f'data/maps/{name}/map.json')
            original_maps[name] = copy.deepcopy(maps[name])
            layout = layouts[maps[name]['layout']]
            blob = raw(layout['blockdata_filepath'])
            grids[name] = list(struct.unpack('<' + 'H' * (len(blob) // 2), blob))
        return maps[name]

    def layout_for(name):
        return layouts[load(name)['layout']]

    def value_at(name, x, y):
        return grids[name][y * layout_for(name)['width'] + x]

    def patch(name, x, y, value):
        layout = layout_for(name)
        assert 0 <= x < layout['width'] and 0 <= y < layout['height'], (name, x, y)
        index = y * layout['width'] + x
        before = grids[name][index]
        if before != value:
            changes.append(dict(map=name, position=[x, y], before=before, after=value))
            grids[name][index] = value

    donor = load('OneIsland_Harbor_Frlg')
    house = [value_at('OneIsland_Harbor_Frlg', 10 + x, y)
             for y in range(6) for x in range(7)]
    wood_mid = value_at('OneIsland_Harbor_Frlg', 10, 6) & 1023
    mids = sorted({value & 1023 for value in house} | {wood_mid})
    primary = renderer.tileset('gTileset_General_Frlg')
    donor_tiles, donor_pals, donor_words = renderer.tileset('gTileset_IslandHarbor_Frlg')
    headers = raw('src/data/tilesets/headers.h').decode()
    graphics = raw('src/data/tilesets/graphics.h').decode()
    definitions = raw('src/data/tilesets/metatiles.h').decode()
    imported = {}
    bank_records = []

    # Private copies prevent changing Mt Ember, caves, or any other map using
    # the original Sevii palettes. Actual target maps do not use palette 12.
    # Import exact RGB colors; nearest-color remapping is deliberately absent.
    for family in ['123', '45', '67']:
        old_symbol = 'gTileset_SeviiIslands' + family
        suffix = 'JourneySeviiIntegrated' + family
        new_symbol = 'gTileset_' + suffix
        original_header = re.search(r'const struct Tileset ' + old_symbol + r'\s*=\s*\{(.*?)\};', headers, re.S)[1]
        original_meta_symbol = re.search(r'\.metatiles\s*=\s*(\w+)', original_header)[1]
        original_path = re.search(r'\b' + original_meta_symbol + r'\[\].*?"([^"]+)"', definitions)[1]
        original_folder = original_path.rsplit('/', 1)[0]
        folder = 'data/tilesets/secondary/journey_sevii_integrated_' + family
        tile_image, palettes, words = renderer.tileset(old_symbol)
        words = list(words)
        attrs = bytearray(raw(original_folder + '/metatile_attributes.bin'))
        used_ids = set()
        for layout in layouts.values():
            if layout['secondary_tileset'] != old_symbol:
                continue
            for key in ['blockdata_filepath', 'border_filepath']:
                blob = raw(layout[key])
                used_ids.update(v & 1023 for v in struct.unpack('<' + 'H' * (len(blob) // 2), blob))
        slots = [640 + i for i in range(len(words) // 8)
                 if 640 + i not in used_ids and not any(words[i * 8:(i + 1) * 8])]
        while len(slots) < len(mids):
            assert 640 + len(words) // 8 < 1024
            slots.append(640 + len(words) // 8)
            words.extend([0] * 8)
            attrs.extend(bytes(4))
        used_graphics = {word & 1023 for word in words}
        spare = iter(i for i in range(640, 1024) if i not in used_graphics)
        canvas = tile_image.copy()
        converted, needed_colors, conversions = {}, set(), {}

        def source_tile(word):
            tile_id, bank = word & 1023, word >> 12
            image = primary[0] if tile_id < 640 else donor_tiles
            local_id = tile_id if tile_id < 640 else tile_id - 640
            colors = (primary[1] if bank < 7 else donor_pals)[bank]
            values = [image.getpixel((local_id % 16 * 8 + x, local_id // 16 * 8 + y))
                      for y in range(8) for x in range(8)]
            return values, colors

        for mid in mids:
            for word in donor_words[(mid - 640) * 8:(mid - 639) * 8]:
                key = (word & 1023, word >> 12)
                if key in conversions:
                    continue
                values, colors = source_tile(word)
                required = {colors[v] for v in values if v}
                banks = [i for i in range(12)
                         if required <= set((primary[1] if i < 7 else palettes)[i][1:])]
                bank = banks[0] if banks else 12
                conversions[key] = bank
                if bank == 12:
                    needed_colors.update(required)
        assert len(needed_colors) <= 15, (family, needed_colors)
        new_palette = [palettes[12][0]] + sorted(needed_colors)
        new_palette.extend([(0, 0, 0)] * (16 - len(new_palette)))
        ids = {}
        for mid, new_mid in zip(mids, slots):
            ids[mid] = new_mid
            new_words = []
            for word in donor_words[(mid - 640) * 8:(mid - 639) * 8]:
                key = (word & 1023, word >> 12)
                if key not in converted:
                    slot = next(spare)
                    bank = conversions[key]
                    target_colors = new_palette if bank == 12 else (primary[1] if bank < 7 else palettes)[bank]
                    values, colors = source_tile(word)
                    for index, old in enumerate(values):
                        value = 0 if not old else 1 + target_colors[1:].index(colors[old])
                        canvas.putpixel(((slot - 640) % 16 * 8 + index % 8,
                                         (slot - 640) // 16 * 8 + index // 8), value)
                    converted[key] = slot | (bank << 12)
                new_words.append(converted[key] | (word & 0xC00))
            at = (new_mid - 640) * 8
            words[at:at + 8] = new_words
            donor_attrs = raw('data/tilesets/secondary/island_harbor_frlg/metatile_attributes.bin')
            attrs[(new_mid - 640) * 4:(new_mid - 639) * 4] = donor_attrs[(mid - 640) * 4:(mid - 639) * 4]
        assert canvas.size == (128, 192) and len(words) <= 384 * 8
        buffer = io.BytesIO()
        canvas.save(buffer, format='PNG')
        stage(folder + '/tiles.png', buffer.getvalue())
        stage(folder + '/metatiles.bin', struct.pack('<' + 'H' * len(words), *words))
        stage(folder + '/metatile_attributes.bin', attrs)
        for bank in range(16):
            path = f'{folder}/palettes/{bank:02}.pal'
            if bank == 12:
                stage(path, 'JASC-PAL\n0100\n16\n' + '\n'.join(' '.join(map(str, color)) for color in new_palette) + '\n')
            else:
                stage(path, raw(f'{original_folder}/palettes/{bank:02}.pal'))
        graphics += f'\nconst u32 gTilesetTiles_{suffix}[] = INCBIN_U32("{folder}/tiles.4bpp.fastSmol");\n'
        graphics += f'const u16 gTilesetPalettes_{suffix}[][16] =\n{{\n' + ''.join(
            f'    INCBIN_U16("{folder}/palettes/{bank:02}.gbapal"),\n' for bank in range(16)) + '};\n'
        definitions += f'\nconst u16 gMetatiles_{suffix}[] = INCBIN_U16("{folder}/metatiles.bin");\n'
        definitions += f'const u16 gMetatileAttributes_{suffix}[] = INCBIN_U16("{folder}/metatile_attributes.bin");\n'
        new_header = original_header.replace('SeviiIslands' + family, suffix)
        headers += '\nconst struct Tileset ' + new_symbol + ' =\n{' + new_header + '};\n'
        imported[old_symbol] = dict(symbol=new_symbol, ids=ids, wood=ids[wood_mid])
        bank_records.append(dict(original=old_symbol, private=new_symbol, metatile_ids=ids,
                                 metatile_slots_previously_blank_or_appended=True, native_graphics_capacity=384,
                                 imported_graphics=len(converted), exact_colors=True, palette=12,
                                 palette_color_count=len(needed_colors), original_bank_unchanged=True,
                                 folder=folder))
    stage('src/data/tilesets/headers.h', headers)
    stage('src/data/tilesets/graphics.h', graphics)
    stage('src/data/tilesets/metatiles.h', definitions)

    def private_bank(name):
        layout = layout_for(name)
        old = layout['secondary_tileset']
        if old in imported:
            # Every previously visible tile must retain its original palette.
            blob = raw(layout['border_filepath'])
            ids_used = {v & 1023 for v in grids[name]} | {
                v & 1023 for v in struct.unpack('<' + 'H' * (len(blob) // 2), blob)}
            words = renderer.tileset(old)[2]
            assert not any(word >> 12 == 12 for mid in ids_used if mid >= 640
                           for word in words[(mid - 640) * 8:(mid - 639) * 8]), name
            layout['secondary_tileset'] = imported[old]['symbol']
            return imported[old]
        return next(row for row in imported.values() if row['symbol'] == old)

    ports = []
    for island, old_port, old_bridge in zip(ISLANDS, old_ports, old_bridges):
        assert old_port['island'] == old_bridge['island'] == island
        cfg = CONFIG[island]
        name = cfg['map']
        city = load(name)
        bank = private_bank(name)
        bx, by, bw, bh = cfg['bridge']
        tx, ty = cfg['terminal']
        front_map = cfg.get('front_map', name)
        fy = cfg.get('front_y', cfg['front'])
        front_rows = cfg.get('front_rows', 1)
        front_layout = layout_for(front_map)
        private_bank(front_map)
        deck_cells = []
        deck_segments = []

        def deck(map_name, x, y, w, h):
            wood = 0x3000 | private_bank(map_name)['wood']
            deck_segments.append(dict(map=map_name, footprint=[x, y, w, h]))
            for yy in range(y, y + h):
                for xx in range(x, x + w):
                    patch(map_name, xx, yy, wood)
                    deck_cells.append([map_name, xx, yy])

        # The incoming ramp remains a continuous three-column walk from town.
        if island == 'One':
            private_bank(old_bridge['town'])
            deck(old_bridge['town'], 11, 16, 3, 4)
        elif island in ['Two', 'Four', 'Five']:
            # Their first native board row used a different plank rhythm.
            # Replace the complete three-tile row, retaining the dry elevation.
            old_x, old_y = old_bridge['start'][1:]
            deck(name, old_x - 1, old_y, 3, 1)
        deck(name, bx, by, bw, bh)
        left, right = min(bx, tx), max(bx + bw, tx + 7)
        if island == 'Seven':
            # Leave a normal apron inside the town header. A door on the last
            # map row can be crossed as a connection before its warp is tested.
            deck(name, left, cfg['front'], right - left, 1)
        deck(front_map, left, fy, right - left, front_rows)
        terminal_cells = []
        for y in range(6):
            for x in range(7):
                value = house[y * 7 + x]
                patch(name, tx + x, ty + y, (value & ~1023) | bank['ids'][value & 1023])
                terminal_cells.append([name, tx + x, ty + y])

        # The world-sea maps are retained as sea. The previous detached port,
        # return pad, blocked boat footprints, and ferry warp all disappear.
        old_exterior = old_port['exterior']
        old_map = load(old_exterior)
        old_layout = layout_for(old_exterior)
        old_removed = []
        for y in range(old_layout['height']):
            for x in range(old_layout['width']):
                before = value_at(old_exterior, x, y)
                # Do not open previously sealed borders; remove only structures,
                # land and occupied boat water. Reef limits stay intact.
                if before >> 12 in (3, 15) or before & 1023 >= 0x280 or any(
                    [x, y] in footprint for footprint in old_port['outside_hulls']):
                    patch(old_exterior, x, y, 0x112B)
                    old_removed.append([x, y, before, 0x112B])
        old_map['object_events'] = []
        old_map['warp_events'] = []
        stage_json(f'data/maps/{old_exterior}/map.json', old_map)

        # Reuse the old ferry slot so doors elsewhere in each city retain IDs.
        warp_id = old_bridge['endpoint_warp_id']
        end_map = old_bridge['end'][0]
        assert end_map == name
        previous_warp = copy.deepcopy(city['warp_events'][warp_id])
        door_x, door_y = tx + 3, ty + 5
        interior = load(old_port['interior'])
        city['warp_events'][warp_id] = dict(x=door_x, y=door_y, elevation=3,
                                          dest_map=interior['id'], dest_warp_id='0')
        for warp in interior['warp_events']:
            warp.update(dest_map=city['id'], dest_warp_id=str(warp_id))
        stage_json(f'data/maps/{old_port["interior"]}/map.json', interior)

        # Seven's new front crosses the existing town/canyon boundary. Clear
        # the entire 2x2 boulder at (16,0), never only its lower half.
        water = 0x112B if island in ['One', 'Two', 'Five'] else 0x1273
        if island == 'Seven':
            for y in range(2, 9):
                for x in range(11, 24):
                    patch(front_map, x, y, 0x1273)
            for y in range(2):
                for x in range(11, 14):
                    patch(front_map, x, y, 0x1273)
        dbx, dby, wx, wy, key = cfg['boarding']
        boarding_map = front_map if island == 'Seven' else name
        patch(boarding_map, wx, wy, water)

        # Rehome complete sprites with one tile of unobstructed water around
        # their hulls. Six has no outside boat: a safe berth would require
        # altering its existing mountain or the city above the pier.
        boats = []
        boats_map = front_map if island == 'Seven' else name
        boats_city = load(boats_map)
        for index, xy in enumerate(cfg['boats']):
            template = old_port['outside_boat'] if index == 0 else old_port['medium_boat']
            boat = copy.deepcopy(template)
            boat.update(x=xy[0], y=xy[1])
            sprite = renderer.sprite(boat['graphics_id'], 0)
            dx, dy = renderer.sprite_offset(boat['graphics_id'])
            ox = boat['x'] * 16 + 8 - sprite.width // 2 + dx
            oy = boat['y'] * 16 + 16 - sprite.height + dy
            hull = sorted({((ox + x) // 16, (oy + y) // 16)
                           for y in range(sprite.height) for x in range(sprite.width)
                           if sprite.getpixel((x, y))[3]})
            assert not set(map(tuple, terminal_cells + deck_cells)) & {
                (boats_map, x, y) for x, y in hull}, (island, hull)
            ring = {(x + dx, y + dy) for x, y in hull
                    for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]} - set(hull)
            for x, y in sorted(ring):
                before = value_at(boats_map, x, y)
                assert not before & 0xC00 and before >> 12 in (0, 1), (island, x, y, hex(before))
                patch(boats_map, x, y, water)
            for x, y in hull:
                before = value_at(boats_map, x, y)
                assert before >> 12 != 3, (island, boat, x, y, hex(before))
                patch(boats_map, x, y, water | 0x400)
            boats_city['object_events'].append(boat)
            boats.append(dict(map=boats_map, event=boat, hull=[list(cell) for cell in hull],
                              clear_water_ring=[list(cell) for cell in sorted(ring)]))
        outside_arrival = [front_map, door_x, fy]
        # A return door exits one row below the building, including the Seven
        # seam whose next map begins precisely at the full front deck.
        if island == 'Seven':
            outside_arrival = [name, door_x, cfg['front']]
        ports.append(dict(island=island, town=old_bridge['town'], map=name,
                          interior=old_port['interior'], pid=old_port['pid'],
                          terminal_bounds=[tx, ty, 7, 6], terminal_cells=terminal_cells,
                          door=[name, door_x, door_y], door_warp_id=warp_id,
                          start=cfg['start'], outside_arrival=outside_arrival,
                          apron=outside_arrival, arrival=old_port['arrival'],
                          captain=old_port['captain'], deck_cells=sorted(set(map(tuple, deck_cells))),
                          deck_segments=deck_segments,
                          boarding=dict(dry=[boarding_map, dbx, dby],
                                        water=[boarding_map, wx, wy], outward_key=key),
                          old_exterior=old_exterior, old_removed_cells=old_removed,
                          old_warp=previous_warp,
                          exterior_connections=copy.deepcopy(old_map.get('connections')),
                          town_connections=copy.deepcopy(load(old_bridge['town']).get('connections')),
                          boats=boats, terminal_door_direct_to_interior=True,
                          ferry_warp_between_town_and_offshore_removed=True,
                          original_dimensions_preserved=True,
                          boats_omitted_for_clearance=island == 'Six'))

    for name, values in grids.items():
        if name == 'OneIsland_Harbor_Frlg' and name not in maps:
            continue
        path = layout_for(name)['blockdata_filepath']
        before = raw(path)
        after = struct.pack('<' + 'H' * len(values), *values)
        if after != before:
            stage(path, after)
        if maps[name] != original_maps[name]:
            stage_json(f'data/maps/{name}/map.json', maps[name])
        assert maps[name].get('connections') == original_maps[name].get('connections'), name
    stage_json('data/layouts/layouts.json', layout_data)
    return dict(ports=ports, private_banks=bank_records, changed_paths=sorted(touched),
                changed_cells=changes, all_seven_terminal_exteriors_integrated=True,
                surface_connections_and_map_dimensions_preserved=True,
                original_secondary_banks_unchanged=True, exact_native_terminal_colors=True,
                old_offshore_maps_retained_as_sea=True, atlas_unchanged=True)


def render_review(source, baseline, metadata, output):
    """Full native source renders, explicitly distinct from ROM captures."""
    from pathlib import Path
    from PIL import ImageDraw
    source, baseline, output = map(Path, (source, baseline, output))
    output.mkdir(parents=True, exist_ok=True)
    current, original = MapRenderer(source), MapRenderer(baseline)
    donor, _ = original.render('OneIsland_Harbor_Frlg', npcs=False)
    donor = donor.crop((10 * 16, 0, 17 * 16, 6 * 16))
    for port in metadata['ports']:
        names = list(dict.fromkeys([port['town'], port['map']] +
                                  [segment['map'] for segment in port['deck_segments']]))
        panels = []
        for state, renderer in [('before', original), ('after', current)]:
            images = []
            for name in names:
                image, _ = renderer.render(name)
                image.save(output / (port['island'] + '-' + state + '-' + name + '.png'))
                images.append(image)
            panel = Image.new('RGB', (max(image.width for image in images),
                                      sum(image.height for image in images) + 24), '#17232b')
            ImageDraw.Draw(panel).text((0, 4), port['island'] + ' - ' + state +
                                      ' (native source render, not emulator)', fill='white')
            offset = 24
            for image in images:
                panel.paste(image, (0, offset))
                offset += image.height
            panel.save(output / (port['island'] + '-' + state + '.png'))
            panels.append(panel)
        comparison = Image.new('RGB', (sum(panel.width for panel in panels) + 16,
                                       max(panel.height for panel in panels)), '#17232b')
        comparison.paste(panels[0], (0, 0))
        comparison.paste(panels[1], (panels[0].width + 16, 0))
        comparison.save(output / (port['island'] + '-comparison.png'))
        image, _ = current.render(port['old_exterior'])
        image.save(output / (port['island'] + '-offshore-cleared.png'))
        image, _ = current.render(port['map'], npcs=False)
        x, y, w, h = port['terminal_bounds']
        house = image.crop((x * 16, y * 16, (x + w) * 16, (y + h) * 16))
        assert donor.tobytes() == house.tobytes(), port['island']
    (output / 'layout-metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
