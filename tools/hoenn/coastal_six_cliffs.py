"""Stage complete native Six shore objects over the immutable layer-162 source.

Only the two map blockdata files change.  The native west coast replaces six
whole trees; the port mountain receives its complete south face and joins the
west face of Water Path.  Events, buildings, paths and map connections stay put.
"""
import hashlib
import json
from pathlib import Path
import struct


TOWN = 'SixIsland_Frlg'
WATER_PATH = 'SixIsland_WaterPath_Frlg'
REMOVED_TREES = [(0, y) for y in (3, 6, 9, 12, 16, 19)]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def repair(layer):
    """Return review metadata and stage bytes, without applying the layer."""
    def raw(path):
        return layer.outputs[path] if path in layer.outputs else (layer.source / path).read_bytes()

    layouts = {row['id']: row for row in json.loads(raw('data/layouts/layouts.json'))['layouts']}
    maps, values, originals = {}, {}, {}
    for name in (TOWN, WATER_PATH):
        mapping = json.loads(raw(f'data/maps/{name}/map.json'))
        layout = layouts[mapping['layout']]
        assert layout['layout_version'] == 'frlg'
        before = raw(layout['blockdata_filepath'])
        maps[name] = (mapping, layout)
        originals[name] = before
        values[name] = list(struct.unpack('<' + 'H' * (layout['width'] * layout['height']), before))
    assert (maps[TOWN][1]['width'], maps[TOWN][1]['height']) == (24, 30)
    assert (maps[WATER_PATH][1]['width'], maps[WATER_PATH][1]['height']) == (24, 100)

    def at(name, x, y):
        return values[name][y * maps[name][1]['width'] + x]

    def put(name, x, y, value):
        layout = maps[name][1]
        assert 0 <= x < layout['width'] and 0 <= y < layout['height']
        values[name][y * layout['width'] + x] = value

    # Free the entire two-column object footprint before adding a two-column
    # coast.  Moving only crowns or trunks would create another partial object.
    for x, y in REMOVED_TREES:
        assert [[at(TOWN, x + dx, y + dy) for dx in range(2)] for dy in range(3)] == [
            [0x300E, 0x300F], [0x041E, 0x041F], [0x0426, 0x0427]], (x, y)

    # Cape Brink's complete northwest head: water, rock cap, northern lip.
    for x, value in [(0, 0x1273), (1, 0x067A), (2, 0x3132)]:
        put(TOWN, x, 2, value)
    # Six's own west cliff donor is x15/16,y24..28.  The water-side head uses
    # the native 270 variant, keeping Surf height1 and the ordinary coast flags.
    for y in range(3, 22):
        put(TOWN, 0, y, 0x1270 if y == 3 else 0x1274)
        put(TOWN, 1, y, 0x0473)
    put(TOWN, 0, 22, 0x1274)
    put(TOWN, 1, 22, 0x047B)
    put(TOWN, 0, 23, 0x1278)
    put(TOWN, 1, 23, 0x126B)
    assert at(TOWN, 2, 22) == 0x047A  # Preserve the native dry terrace elbow.

    # Retreat the complete upper elbow/cap pair; preserve the lower side body
    # and the dry x8 corridor.  Deleting only the cap visibly squares the bend.
    assert [at(TOWN, x, 2) for x in (8, 9, 10)] == [0x3133, 0x3134, 0x067C]
    for x, value in [(8, 0x3134), (9, 0x067C), (10, 0x1273)]:
        put(TOWN, x, 2, value)
    assert all(at(TOWN, 8, y) == 0x3001 for y in (3, 4, 5))

    # Seven's native stepped coast (x2..6,y12/13) supplies all three parts:
    # southwest face corner, horizontal south face, then the inner elbow into
    # a continuing west face.  The latter belongs to the CONNECTED map, so its
    # position is Water Path(0,68), equal to Six(24,28), not a detached island.
    assert all(at(TOWN, x, 28) & 0x400 for x in range(16, 24))
    put(TOWN, 16, 28, 0x047B)
    for x in range(17, 24):
        put(TOWN, x, 28, 0x047C)
    put(TOWN, 14, 29, 0x1276)  # Remove the old water-side cliff fragment too.
    put(TOWN, 15, 29, 0x1278)
    for x in range(16, 23):
        put(TOWN, x, 29, 0x126B)
    put(TOWN, 23, 29, 0x1269)
    put(WATER_PATH, 0, 68, 0x04B3)
    # This strip is entirely solid mountain today.  Continue its exposed face
    # until the next real land connection, Ruin Valley at Water Path y80.
    for y in range(69, 80):
        assert at(WATER_PATH, 0, y) == 0x0471
        put(WATER_PATH, 0, y, 0x0473)

    records = []
    for name in (TOWN, WATER_PATH):
        mapping, layout = maps[name]
        after = struct.pack('<' + 'H' * len(values[name]), *values[name])
        old = struct.unpack('<' + 'H' * len(values[name]), originals[name])
        changed = [dict(position=[i % layout['width'], i // layout['width']], before=a, after=b)
                   for i, (a, b) in enumerate(zip(old, values[name])) if a != b]
        assert changed
        layer.stage(layout['blockdata_filepath'], after)
        records.append(dict(map=name, path=layout['blockdata_filepath'],
                            dimensions=[layout['width'], layout['height']],
                            before_sha256=digest(originals[name]), after_sha256=digest(after),
                            changed_cells=changed))
    # Native 2x3 isolated trees remaining in the town.  No fragments of any of
    # the six removed trees survive on the new shore.
    complete = []
    tree_parts = {0xE, 0xF, 0x1E, 0x1F, 0x24, 0x25, 0x26, 0x27}
    owned = set()
    for y in range(28):
        for x in range(23):
            if at(TOWN, x, y) != 0x300E:
                continue
            rows = [[at(TOWN, x + dx, y + dy) for dx in range(2)] for dy in range(3)]
            assert rows[0] == [0x300E, 0x300F] and rows[1] == [0x041E, 0x041F]
            assert rows[2][0] in (0x0424, 0x0426) and rows[2][1] in (0x0425, 0x0427)
            complete.append([x, y, 2, 3])
            owned |= {(x + dx, y + dy) for dx in range(2) for dy in range(3)}
    actual = {(x, y) for y in range(30) for x in range(24) if at(TOWN, x, y) & 1023 in tree_parts}
    assert len(complete) == 12 and owned == actual
    return dict(maps=records, removed_whole_trees=[[*point, 2, 3] for point in REMOVED_TREES],
                remaining_complete_trees=complete, complete_tree_count=12,
                native_donors=[
                    dict(map='TwoIsland_CapeBrink_Frlg', cells=[
                        dict(position=[5, 13], value=0x067A),
                        dict(position=[6, 13], value=0x3132)]),
                    dict(map=TOWN, cells=[dict(position=[15, 24], value=0x1274),
                                          dict(position=[16, 24], value=0x0473)]),
                    dict(map='SevenIsland_Frlg', cells=[
                        dict(position=[1, 12], value=0x1274),
                        dict(position=[2, 12], value=0x047B),
                        dict(position=[3, 12], value=0x047C),
                        dict(position=[6, 12], value=0x04B3),
                        dict(position=[1, 13], value=0x1278),
                        dict(position=[2, 13], value=0x126B),
                        dict(position=[5, 13], value=0x1269),
                        dict(position=[6, 13], value=0x0473)])],
                north_dry_corridor_preserved=[[8, y] for y in (3, 4, 5)],
                west_shore=dict(bounds=[0, 2, 3, 22], native_water_and_solid_body=True),
                northeast_upper_pair_retreat=dict(bounds=[8, 2, 3, 1], lower_body_preserved=True),
                port_mountain_footer=dict(town_face=[16, 28, 8, 1], town_water=[15, 29, 9, 1],
                                          connected_inner_elbow=[WATER_PATH, 0, 68],
                                          connected_west_body=[WATER_PATH, 0, 69, 1, 11]),
                buildings_paths_events_connections_dimensions_and_atlas_unchanged=True,
                helper_only_stages_bytes=True)


def render_review(source, output, metadata):
    """Whole native source renders, including the real connected map banks."""
    from PIL import Image, ImageDraw
    from render_sea_maps import MapRenderer

    source, output = Path(source), Path(output)
    output.mkdir(parents=True, exist_ok=True)
    renderer = MapRenderer(source)
    states = {'before': {}, 'after': {}}
    for record in metadata['maps']:
        raw = (source / record['path']).read_bytes()
        values = list(struct.unpack('<' + 'H' * (len(raw) // 2), raw))
        width, _ = record['dimensions']
        current = digest(raw)
        assert current in (record['before_sha256'], record['after_sha256'])
        for state in states:
            rendered = values.copy()
            for cell in record['changed_cells']:
                x, y = cell['position']
                rendered[y * width + x] = cell[state]
            states[state][record['map']] = rendered
    mapping = json.loads((source / f'data/maps/{TOWN}/map.json').read_text())
    layout = renderer.layouts[mapping['layout']]
    border_raw = (source / layout['border_filepath']).read_bytes()
    border = struct.unpack('<' + 'H' * (len(border_raw) // 2), border_raw)
    panels = []
    images = []
    for state, values in states.items():
        town, _ = renderer.render(TOWN, values=values[TOWN])
        town.save(output / f'Six-{state}.png')
        water_path, _ = renderer.render(WATER_PATH, values=values[WATER_PATH])
        water_path.save(output / f'WaterPath-{state}.png')
        width, height = 39, 44
        outside = [border[((x - 7) % layout['border_width']) + layout['border_width'] *
                          ((y - 7) % layout['border_height'])]
                   for y in range(height) for x in range(width)]
        canvas, _ = renderer.render(TOWN, values=outside, dimensions=(width, height), npcs=False)
        for name, ox, oy in [(WATER_PATH, 24, -40), ('JourneySurfLink05200', -16, 17)]:
            neighbor, _ = renderer.render(name, values=values.get(name))
            canvas.paste(neighbor, ((ox + 7) * 16, (oy + 7) * 16))
        canvas.paste(town, (7 * 16, 7 * 16))
        label = Image.new('RGB', (canvas.width, canvas.height + 24), '#17232b')
        label.paste(canvas, (0, 24))
        ImageDraw.Draw(label).text((4, 5), f'Six {state}: whole native source render with real neighbors', fill='white')
        path = output / f'Six-{state}-whole-with-neighbors.png'
        label.save(path)
        images.append(dict(state=state, file=path.name, sha256=digest(path.read_bytes())))
        panels.append(label)
    comparison = Image.new('RGB', (panels[0].width * 2 + 16, panels[0].height), '#17232b')
    comparison.paste(panels[0], (0, 0))
    comparison.paste(panels[1], (panels[0].width + 16, 0))
    comparison.save(output / 'Six-comparison-whole-with-neighbors.png')
    return images
