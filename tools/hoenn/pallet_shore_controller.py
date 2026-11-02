"""Focused Pallet foot-path checks, using an existing native walk context."""
import json

from coastal_ecology_pallet_shore import CELLS


def verify_pallet_shore_controller(namespace):
    native, walk = namespace['native'], namespace['walk_to']
    step, picture = namespace['step'], namespace['picture']
    position, lib, symbols = namespace['position'], namespace['lib'], namespace['s']
    marker = json.loads((namespace['source'] / '.journey-coastal-ecology').read_text())
    assert marker['pallet_shore']['blocked_mixed_shore_cells'] == 8

    def state():
        x, y = position()
        return dict(tile=[x, y], surfing=bool(lib.read8(symbols['gPlayerAvatar']) & 8),
                    elevation=native('PlayerGetElevation'),
                    tile_elevation=native('MapGridGetElevationAt', x + 7, y + 7))

    cells = []
    for x, y, original in CELLS:
        row = dict(tile=[x, y], metatile=native('MapGridGetMetatileIdAt', x + 7, y + 7),
                   elevation=native('MapGridGetElevationAt', x + 7, y + 7),
                   collision=native('MapGridGetCollisionAt', x + 7, y + 7),
                   behavior=native('MapGridGetMetatileBehaviorAt', x + 7, y + 7))
        assert row == dict(tile=[x, y], metatile=original & 1023, elevation=3,
                           collision=1, behavior=0), row
        cells.append(row)

    # The sign at (20,16) already closes that northern approach. Check all
    # nine remaining walkable boundary edges, including both side entries.
    edges = [((14, 17), (15, 17), 16)]
    edges += [((x, 16), (x, 17), 128) for x in (15, 16, 17, 18, 19, 21, 22)]
    edges += [((23, 17), (22, 17), 32)]
    probes = []
    for index, (start, target, key) in enumerate(edges):
        # Return to the open north row before moving sideways. The native
        # Oak sign at (20,16) blocks a direct horizontal return from x21/22.
        walk(position()[0], 15)
        walk(13, 15)
        if start == (14, 17):
            walk(14, 15)
            walk(*start)
        else:
            walk(start[0], 15)
            walk(*start)
        before = state()
        assert before['tile'] == list(start) and not before['surfing']
        assert before['elevation'] == 3
        step(48, key)
        step(30)
        after = state()
        assert after == before, (start, target, before, after)
        picture('north-wet-cliff-edge-' + str(index))
        probes.append(dict(start=list(start), target=list(target), direction_key=key,
                           held_input_frames=48, before=before, after=after,
                           controller_input_only=True, blocked=True))

    # Reach the southern ramp from a complete dry grass corridor, without
    # a new travel fixture or a placement on the bridge itself.
    walk(23, 15)
    walk(23, 26)
    walk(18, 26)
    states = [state()]
    picture('south-bridge-full-grass-start')
    for index, y in enumerate((25, 24, 25, 26)):
        walk(18, y)
        row = state()
        assert not row['surfing'] and row['elevation'] == 3
        assert row['tile_elevation'] == (15 if y == 25 else 3)
        states.append(row)
        picture('south-bridge-dry-roundtrip-' + str(index))
    assert states[0] == states[-1]
    return dict(north_rim_cells=cells, north_rim_blocked_probes=probes,
                all_wet_mixed_rim_cells_blocked=True,
                north_rim_surrounding_land_route_walked=True,
                south_bridge_dry_roundtrip=states,
                south_bridge_from_full_grass_controller_roundtrip=True,
                no_new_travel_fixture_after_initial_land_route=True)
