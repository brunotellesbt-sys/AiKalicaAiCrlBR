"""Stage native Surf dismounts and dry-deck drawing for integrated Sevii piers.

This helper never writes the source tree directly. The caller commits all
three integration helpers together through ``candidate_layer.Layer``.
"""
import json
import struct

from integrated_sevii_harbors import CONFIG


def repair(layer):
    source = layer.source
    touched = []

    def raw(path):
        return layer.outputs[path] if path in layer.outputs else (source / path).read_bytes()

    # A regular dry metatile at elevation 3 already takes the engine's native
    # COLLISION_ELEVATION_MISMATCH -> CanStopSurfing -> dismount path. The old
    # low-pier exception ran first and returned COLLISION_IMPASSABLE instead.
    path = 'src/event_object_movement.c'
    before = raw(path).decode()
    assert before.count('JourneyLowPierBlocks(objectEvent, x, y) || ') == 2
    assert before.count('#include "journey_coastal_piers.h"\n') == 1
    after = before.replace('JourneyLowPierBlocks(objectEvent, x, y) || ', '')
    after = after.replace('#include "journey_coastal_piers.h"\n', '')
    assert 'JourneyLowPier' not in after
    assert after.count('JourneyDewfordBridgeRailBlocks(objectEvent, x, y)') == 2
    layer.stage(path, after)
    touched.append(path)

    layouts = {row['id']: row for row in json.loads(raw('data/layouts/layouts.json'))['layouts']}
    decks = []
    for island, cfg in CONFIG.items():
        name = cfg['map']
        header = json.loads(raw(f'data/maps/{name}/map.json'))
        layout = layouts[header['layout']]
        bx, by, _, _ = cfg['bridge']
        mid = struct.unpack_from('<H', raw(layout['blockdata_filepath']),
                                 2 * (by * layout['width'] + bx))[0] & 1023
        family = '123' if island in ['One', 'Two', 'Three'] else '45' if island in ['Four', 'Five'] else '67'
        assert layout['secondary_tileset'] == 'gTileset_JourneySeviiIntegrated' + family
        attr_path = f'data/tilesets/secondary/journey_sevii_integrated_{family}/metatile_attributes.bin'
        attrs = bytearray(raw(attr_path))
        at = (mid - 640) * 4
        before_attr = struct.unpack_from('<I', attrs, at)[0]
        assert before_attr & 511 == 0, (island, mid, hex(before_attr))
        # COVERED puts both plank quadrants below the player's OAM priority.
        # Only the new private metatile is eligible; shared native art is inert.
        after_attr = (before_attr & ~0x60000000) | 0x20000000
        if after_attr != before_attr:
            struct.pack_into('<I', attrs, at, after_attr)
            layer.stage(attr_path, bytes(attrs))
            if attr_path not in touched:
                touched.append(attr_path)
        decks.append(dict(island=island, metatile=mid, private_tileset=layout['secondary_tileset'],
                          attribute=after_attr, behavior=0, layer_type=1,
                          native_player_priority=2, elevation=3))

    avatar_path = 'src/field_player_avatar.c'
    assert raw(avatar_path) == (source / avatar_path).read_bytes()
    assert b'MapGridGetElevationAt(x, y) == ELEVATION_DEFAULT' in raw(avatar_path)
    path = 'src/journey_sevii_surf.c'
    text = raw(path).decode()
    anchor = '    case (MAP_GROUP(MAP_SEVEN_ISLAND) << 8) | MAP_NUM(MAP_SEVEN_ISLAND):\n'
    assert text.count(anchor) == 1
    # The new boardwalk spans the town/canyon header boundary. Its southern
    # water is the same open coast, rather than a waterfall from Hoenn.
    text = text.replace(anchor, anchor +
        '    case (MAP_GROUP(MAP_SEVEN_ISLAND_SEVAULT_CANYON_ENTRANCE) << 8) | MAP_NUM(MAP_SEVEN_ISLAND_SEVAULT_CANYON_ENTRANCE):\n')
    layer.stage(path, text)
    touched.append(path)
    return dict(changed_paths=sorted(touched), low_pier_surf_block_removed=True,
                obsolete_low_pier_header_unreferenced=True,
                native_can_stop_surfing_unchanged=True,
                native_elevation_1_to_3_dismount=True,
                custom_avatar_position_or_elevation_writes=False,
                shared_native_wood_unchanged=True, private_dry_decks=decks,
                seven_southern_boardwalk_water_is_open_coast=True)
