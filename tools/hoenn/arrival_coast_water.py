"""Finish marine water overlays without recoloring the rocks above them.

Layer 166 normalized lower water graphics but assumed every upper word was
object artwork. Native FRLG boulder and beach corners also put animated water
in that upper layer. Their palette6 rectangles remained above palette4 sea.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct

from PIL import Image

from badge_story_layer import read


WATER_SLOTS = frozenset((430, 431, 432, 433, 478, 479, 480, 481))
EXPECTED_UPPER = {430: 5, 431: 5, 432: 4, 433: 4,
                  478: 3, 479: 3, 480: 3, 481: 3}
PRIMARY = 'gTileset_JourneySeviiSea'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def normalize_upper(blob):
    """Only water-only upper graphics change; lower layers and rocks stay exact."""
    assert len(blob) % 16 == 0
    before = list(struct.unpack('<' + 'H' * (len(blob) // 2), blob))
    after = before.copy()
    changes = []
    for i, word in enumerate(before):
        if i % 8 >= 4 and word >> 12 == 6 and word & 1023 in WATER_SLOTS:
            after[i] = (word & 0xFFF) | 0x4000
            changes.append(dict(word_index=i, graphic=word & 1023,
                                before=word, after=after[i]))
    return struct.pack('<' + 'H' * len(after), *after), changes


def water_frames(layer):
    """Prove these glyphs contain only transparent and water indices in all phases.

    The whole FRLG animation range cannot be recolored: earlier glyphs also
    use indices13..15, which are sand colors in palette4.
    """
    from io import BytesIO
    records = []
    groups = [('water_current_landwatersedge', 416, (430, 431, 432, 433)),
              ('sandwatersedge', 464, (478, 479, 480, 481))]
    for folder, start, slots in groups:
        for frame in range(8):
            path = f'data/tilesets/primary/general_frlg/anim/{folder}/{frame}.png'
            raw = read(layer, path)
            with Image.open(BytesIO(raw)) as im:
                assert im.mode == 'P' and im.width % 8 == im.height % 8 == 0
                colors = {}
                for slot in slots:
                    index = slot - start
                    x, y = index % (im.width // 8) * 8, index // (im.width // 8) * 8
                    assert y + 8 <= im.height
                    indices = sorted(set(im.crop((x, y, x + 8, y + 8)).getdata()))
                    assert set(indices) <= {0, 3, 4, 5, 6, 7}, (path, slot, indices)
                    colors[str(slot)] = indices
            records.append(dict(file=path, sha256=sha(raw), graphics=colors))
    return records


def orphan_above_terminal(layer):
    """Remove a boulder top whose lower half became the Treasure Beach roof.

    A lone native quarter also looks clipped beside the new port and is removed.
    Another complete boulder spans exactly the same map boundary farther west;
    it must be retained. This guard distinguishes the actual clipped object
    from every use of the native boulder family.
    """
    layouts = {r['id']: r for r in json.loads(
        read(layer, 'data/layouts/layouts.json'))['layouts']}
    names = ('OneIsland_Frlg', 'OneIsland_TreasureBeach_Frlg')
    data = {}
    for name in names:
        mapping = json.loads(read(layer, f'data/maps/{name}/map.json'))
        layout = layouts[mapping['layout']]
        raw = read(layer, layout['blockdata_filepath'])
        words = list(struct.unpack('<' + 'H' * (len(raw) // 2), raw))
        data[name] = mapping, layout, raw, words
    mapping, layout, raw, words = data[names[0]]
    _, beach, _, beach_words = data[names[1]]
    assert (layout['width'], layout['height']) == (24, 20)
    assert beach['width'] == 24
    full = [words[19 * 24 + x] for x in (2, 3)] + [beach_words[x] for x in (2, 3)]
    assert [v & 1023 for v in full] == [0x1CB, 0x1CC, 0x1D3, 0x1D4]
    removed_cells = [(16, 18), (18, 19), (19, 19)]
    clipped = [words[y * 24 + x] for x, y in removed_cells]
    assert [v & 1023 for v in clipped] == [0x1CB, 0x1CB, 0x1CC]
    roof = [beach_words[x] for x in (18, 19)]
    assert all(v & 0xC00 for v in roof) and [v & 1023 for v in roof] == [0x3A5, 0x3A5]
    occupied = {(row['x'], row['y']) for kind in
                ('object_events', 'warp_events', 'coord_events', 'bg_events')
                for row in mapping.get(kind, [])}
    assert not occupied.intersection(set(removed_cells))
    donor = words[19 * 24 + 20]
    assert donor == 0x112B  # True open sea, Surf elevation1, collision0.
    after = words.copy()
    for x, y in removed_cells:
        after[y * 24 + x] = donor
    path = layout['blockdata_filepath']
    packed = struct.pack('<' + 'H' * len(after), *after)
    layer.stage(path, packed)
    return dict(map=names[0], file=path, removed_top_cells=[list(c) for c in removed_cells],
        before=clipped, after=[donor] * 3, before_sha256=sha(raw), after_sha256=sha(packed),
        lower_half_overwritten_by_terminal=dict(map=names[1], cells=[[18, 0], [19, 0]], words=roof),
        open_water_donor=dict(map=names[0], cell=[20, 19], word=donor),
        retained_complete_cross_map_boulder=dict(
            cells=[[names[0], 2, 19], [names[0], 3, 19], [names[1], 2, 0], [names[1], 3, 0]],
            words=full), native_controller_surf_through_removed_cells_required=True,
        isolated_native_quarter_removed_for_complete_port_context=[16, 18],
        terminal_roof_graphics_events_and_connections_preserved=True)


def repair(layer):
    # The coordinator verifies the immutable parent marker separately; layer
    # input hashes cover its prepared files, not the marker file itself.
    previous = json.loads((Path(layer.source) / '.journey-coastal-ecology').read_bytes())
    tables = previous['ocean']['tables'] + previous['kanto_sea']['tables']
    assert len(tables) == 11 and len({r['tileset'] for r in tables}) == 11
    frames = water_frames(layer)
    observations, changes_by_graphic, paths = [], Counter(), []
    for row in tables:
        path = row['path']
        before = read(layer, path)
        after, changes = normalize_upper(before)
        if row['tileset'] == PRIMARY:
            assert Counter(r['graphic'] for r in changes) == EXPECTED_UPPER
            assert len(changes) == 30
            layer.stage(path, after)
            paths.append(path)
        else:
            assert not changes and after == before, row['tileset']
        changes_by_graphic.update(r['graphic'] for r in changes)
        observations.append(dict(tileset=row['tileset'], file=path,
            before_sha256=sha(before), after_sha256=sha(after), changed_words=changes,
            lower_layers_and_static_object_art_unchanged=True,
            graphic_numbers_and_flip_flags_preserved=True))
    assert dict(changes_by_graphic) == EXPECTED_UPPER
    orphan = orphan_above_terminal(layer)
    paths.append(orphan['file'])
    return dict(kind='arrival-coast-upper-water', changed_paths=paths,
        tables=observations, water_only_graphics=sorted(WATER_SLOTS),
        all_eight_native_phases=frames, changed_upper_water_words=30,
        terminal_orphan=orphan,
        attributes_graphics_callbacks_and_events_preserved=True,
        only_removed_orphan_cells_become_unblocked_surf_water=True,
        native_same_phase_visible_pixels_required=True)
