"""Keep Dewford's walkable beach artwork below the pedestrian sprite.

The custom shoreline uses a transparent drawing over native animated water.
Its original layer type placed that drawing on the foreground BG, so walking
beside the suspension bridge could hide the player behind ordinary sand.
Change only the layer attribute of those private shoreline metatiles.
"""
import json
import struct


FOLDER = 'data/tilesets/secondary/journey_dewford_harbor'
GROUND_METATILES = (0x201, 0x202, 0x207, 0x221, 0x22A, 0x238,
                    0x240, 0x241, 0x244, 0x245, 0x246)


def repair(layer):
    def raw(path):
        return layer.outputs[path] if path in layer.outputs else (layer.source / path).read_bytes()

    metas = raw(FOLDER + '/metatiles.bin')
    attributes = bytearray(raw(FOLDER + '/metatile_attributes.bin'))
    layouts = json.loads(raw('data/layouts/layouts.json'))['layouts']
    shared_layouts = sorted(row['id'] for row in layouts
                            if row['secondary_tileset'] == 'gTileset_JourneyDewfordHarbor')
    assert len(shared_layouts) == 4, shared_layouts
    shore = []
    # These are the private beach overlays, not the suspension bridge, its
    # stairs, buildings, forest, native primary tiles or any other tileset.
    for mid in range(512, 512 + len(metas) // 16):
        words = struct.unpack_from('<8H', metas, (mid - 512) * 16)
        if words[:4] == (0x41C6, 0x41C7, 0x41C7, 0x41C6) and all(
                not word or word >> 12 == 9 for word in words[4:]):
            shore.append(mid)
    assert tuple(shore) == GROUND_METATILES, shore
    changes = []
    before = bytes(attributes)
    for mid in shore:
        offset = (mid - 512) * 2
        old = struct.unpack_from('<H', attributes, offset)[0]
        assert old & 0xF000 == 0, (mid, old)
        new = (old & 0x0FFF) | 0x1000
        struct.pack_into('<H', attributes, offset, new)
        changes.append(dict(metatile=mid, before=old, after=new,
                            behavior_unchanged=True, native_covered_ground_layer=1))
    assert sum(a != b for a, b in zip(before, attributes)) == len(shore)
    path = FOLDER + '/metatile_attributes.bin'
    layer.stage(path, bytes(attributes))
    return dict(changed_paths=[path], changes=changes,
                shared_layouts=shared_layouts,
                beach_overlays_draw_below_pedestrians=True,
                source_art_pixels_and_palettes_unchanged=True,
                native_water_underlay_and_animation_unchanged=True,
                map_blocks_elevations_and_collisions_unchanged=True,
                bridge_stairs_and_upper_lower_levels_unchanged=True,
                terrain_buildings_vendors_events_connections_unchanged=True)
