"""Restore the complete native Seafoam mountain behind the sea sanctuaries.

The Surf review overlay cleared only a seven-by-three window of a much
larger Seafoam mountain and placed a detached small cave inside the window.
The untouched upper mass then ended in a straight cut and hanging side
fragments. Restore the original, complete 81-cell native object at the same
entrance. Coastlines, useful paths, warps, events and the atlas stay intact.
"""
import hashlib
import json
import struct


DONOR_MAP = 'Route20_Frlg'
DONOR_ENTRANCE = (72, 14)
DONOR_BOUNDS = (67, 6, 78, 15)  # Exclusive right/bottom; complete second mountain.
SMALL_CAVE = ((0x0498, 0x0471, 0x049A),
              (0x04A0, 0x0471, 0x04A2),
              (0x04A8, 0x30A9, 0x04AA))


def _dry_component(values, width, entrance):
    """Dry elevation-three component, independently of the object artwork."""
    dry = {(i % width, i // width) for i, value in enumerate(values)
           if value >> 12 == 3 and not value & 0x0C00}
    assert entrance in dry
    seen = {entrance}
    pending = [entrance]
    for x, y in pending:
        for point in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if point in dry and point not in seen:
                seen.add(point)
                pending.append(point)
    return seen


def repair(layer):
    def raw(path):
        return (layer.outputs[path] if path in layer.outputs
                else (layer.source / path).read_bytes())

    def js(path):
        return json.loads(raw(path))

    layouts = {row['id']: row for row in js('data/layouts/layouts.json')['layouts']}
    donor = js(f'data/maps/{DONOR_MAP}/map.json')
    dl = layouts[donor['layout']]
    donor_values = struct.unpack('<' + 'H' * (dl['width'] * dl['height']),
                                 raw(dl['blockdata_filepath']))
    cells = []
    x0, y0, x1, y1 = DONOR_BOUNDS
    for y in range(y0, y1):
        for x in range(x0, x1):
            value = donor_values[y * dl['width'] + x]
            tile = value & 0x03FF
            if 0x68 <= tile <= 0xAF or tile in (0xB2, 0xB3, 0xBA, 0xBB):
                cells.append([x - DONOR_ENTRANCE[0], y - DONOR_ENTRANCE[1], value])
    record = js('.journey-sea-landscapes')['seafoam_mountain']
    assert record['source_map'] == DONOR_MAP
    assert record['source_entrance'] == list(DONOR_ENTRANCE)
    assert len(cells) == 81 and cells == record['cells']
    assert next(value for dx, dy, value in cells if dx == dy == 0) == 0x30A9

    sites = [site for site in js('.journey-sanctuaries')['sites']
             if site['access'] == 'surf']
    assert {site['surface'] for site in sites} == {
        f'JourneyWorldSea{i:02d}' for i in range(9)}
    reports = []
    for site in sites:
        name = site['surface']
        map_path = f'data/maps/{name}/map.json'
        map_raw = raw(map_path)
        data = json.loads(map_raw)
        layout = layouts[data['layout']]
        assert layout['primary_tileset'] == 'gTileset_General_Frlg'
        width, height = layout['width'], layout['height']
        cx, original_cy = site['entry']
        cy = original_cy - 4
        entrance = (cx, cy)
        warp = [event for event in data['warp_events']
                if (event['x'], event['y']) == entrance]
        assert len(warp) == 1
        assert warp[0]['dest_map'] == f'MAP_JOURNEYSANCTUARY{site["theme"].upper()}'
        assert warp[0]['elevation'] == 3

        path = layout['blockdata_filepath']
        before_raw = raw(path)
        before = list(struct.unpack('<' + 'H' * (width * height), before_raw))
        after = before.copy()
        footprint = {(cx + dx, cy + dy) for dx, dy, _ in cells}
        assert all(0 <= x < width and 0 <= y < height for x, y in footprint)
        # The former overlay changed only this front window. Reject unrelated
        # edits to the mountain instead of silently overwriting newer work.
        broken = {(cx + dx, cy + dy): value for dx, dy, value in cells}
        for y in range(cy - 2, cy + 1):
            for x in range(cx - 3, cx + 4):
                assert (x, y) in footprint
                broken[x, y] = 0x3115
        for dy, row in enumerate(SMALL_CAVE):
            for dx, value in enumerate(row):
                broken[cx - 1 + dx, cy - 2 + dy] = value

        changed = []
        for dx, dy, native in cells:
            x, y = cx + dx, cy + dy
            at = y * width + x
            assert before[at] in (broken[x, y], native), (name, x, y, hex(before[at]))
            if before[at] != native:
                changed.append([x, y, before[at], native])
                after[at] = native
        assert after[cy * width + cx] == before[cy * width + cx] == 0x30A9
        assert all(a == b for i, (a, b) in enumerate(zip(before, after))
                   if (i % width, i // width) not in footprint)
        # Fill only the false walking space carved into the object. Every
        # previously reachable dry tile outside it retains access to the door.
        before_dry = _dry_component(before, width, entrance)
        after_dry = _dry_component(after, width, entrance)
        useful_dry = before_dry - footprint
        assert useful_dry <= after_dry, (name, sorted(useful_dry - after_dry))
        assert (cx, cy + 1) in after_dry
        for key in ('object_events', 'coord_events', 'bg_events'):
            assert all((event['x'], event['y']) not in footprint for event in data[key])
        assert all((event['x'], event['y']) not in footprint or event in warp
                   for event in data['warp_events'])
        if changed:
            layer.stage(path, struct.pack('<' + 'H' * len(after), *after))
        assert raw(map_path) == map_raw
        reports.append(dict(
            map=name, sanctuary=site['theme'], entrance=list(entrance),
            changed_cells=changed, complete_native_mountain_cells=len(cells),
            native_mountain_restored_exactly=True,
            doorway_and_warp_unchanged=True,
            map_events_sha256=hashlib.sha256(map_raw).hexdigest(),
            coastline_and_all_tiles_outside_object_unchanged=True,
            useful_dry_tiles_still_connected_to_door=len(useful_dry),
            false_sand_window_removed=True))
    return dict(
        donor_map=DONOR_MAP, donor_entrance=list(DONOR_ENTRANCE),
        donor_bounds=list(DONOR_BOUNDS), native_mountain_cells=cells,
        photographed_surface='JourneyWorldSea08', photographed_sanctuary='Cristais',
        shared_defect_repaired_on_all_nine_surfaces=True,
        atlas_events_warps_and_map_dimensions_unchanged=True,
        maps=reports)
