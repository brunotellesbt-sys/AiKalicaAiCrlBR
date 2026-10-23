"""Independently audit/replay the exact layer-163 terrain and animation scope."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile

from PIL import Image

from prepare_coastal_closures import LAYER, PRIOR, prepare
from validate_dewford_coast_source import compiled_values


ROOT = Path(__file__).resolve().parents[2]
PARENT_ROM_SHA256 = '08fc8a08b95e8e3a923e3342b4f1a31bbaccd1582cbc67ea010021191c43fd6e'
FOLDER = 'data/tilesets/secondary/journey_dewford_harbor'
ISLANDS = ('One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven')
COAST_HEADERS = {f'data/maps/{island}Island_Harbor_Frlg/map.json' for island in ISLANDS}
ALLOWED_SOURCE_FILES = frozenset({
    'data/layouts/SixIsland_Frlg/map.bin',
    'data/layouts/SixIsland_WaterPath_Frlg/map.bin',
    'data/layouts/DewfordTown/map.bin',
    'data/layouts/Route106/map.bin',
    'data/layouts/Route107/map.bin',
    'data/layouts/JourneyDewfordPortIsland/map.bin',
    'include/journey_dewford_bridge.h',
    FOLDER + '/metatiles.bin', FOLDER + '/tiles.png',
    FOLDER + '/palettes/09.pal', FOLDER + '/anim/shore_frames.bin',
    'src/data/tilesets/journey_dewford_shore_anim.h',
    'src/tileset_anims.c',
    'src/main.c',
    'include/tileset_anims.h',
    'src/data/journey_world_map.h',
    'src/data/journey_world_position.h',
} | COAST_HEADERS)
EXPECTED_DYNAMIC_GRAPHICS = {514, 523, 526, 527, 530, 533, 534, 535, 536,
                             537, 543, 544, 545, 546, 1020, 1021, 1022}
FRAME_SHA256 = '86730800296e5f7e61dda7f81584e188de07bffc89f3c8fe460cd9055ab500ba'
# Independent reviewed map IDs and central crossing contracts. A crossing's
# main atlas coordinate must progress in one direction. The other coordinate
# may bow only by these literal pixel limits outside its endpoint interval;
# these small bends retain the existing atlas branches at connected borders.
COAST_GPS_CONTRACTS = {
    'MAP_ONE_ISLAND_HARBOR': ('OneIsland_Harbor_Frlg', (0, 1, 1), (0, 1, 2)),
    'MAP_TWO_ISLAND_HARBOR': ('TwoIsland_Harbor_Frlg', (0, -1, 0), (0, 1, 0)),
    'MAP_THREE_ISLAND_HARBOR': ('ThreeIsland_Harbor_Frlg', (0, 1, 0), (0, 0, 0)),
    'MAP_FOUR_ISLAND_HARBOR': ('FourIsland_Harbor_Frlg', (0, 1, 0), (1, 1, 0)),
    'MAP_FIVE_ISLAND_HARBOR': ('FiveIsland_Harbor_Frlg', (0, 1, 0), (1, 1, 0)),
    'MAP_SIX_ISLAND_HARBOR': ('SixIsland_Harbor_Frlg', (0, 1, 0), (1, 1, 1)),
    'MAP_SEVEN_ISLAND_HARBOR': ('SevenIsland_Harbor_Frlg', (0, -1, 1), (0, 1, 0)),
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def blocks(directory, name, layouts):
    mapping = json.loads((directory / f'data/maps/{name}/map.json').read_text())
    layout = layouts[mapping['layout']]
    raw = (directory / layout['blockdata_filepath']).read_bytes()
    values = list(struct.unpack('<' + 'H' * (len(raw) // 2), raw))
    assert len(values) == layout['width'] * layout['height']
    return layout, values


def audit_six(source, baseline, layouts):
    # These coordinates/words are an independent literal review of the native
    # complete coast, rather than a list read back from the repair marker.
    town_expected = {(0, 2): 0x1273, (1, 2): 0x067A, (2, 2): 0x3132,
                     (8, 2): 0x3134, (9, 2): 0x067C, (10, 2): 0x1273,
                     (0, 22): 0x1274, (1, 22): 0x047B,
                     (0, 23): 0x1278, (1, 23): 0x126B,
                     (16, 28): 0x047B, (14, 29): 0x1276,
                     (15, 29): 0x1278, (23, 29): 0x1269}
    for y in range(3, 22):
        town_expected[0, y] = 0x1270 if y == 3 else 0x1274
        town_expected[1, y] = 0x0473
    town_expected.update({(x, 28): 0x047C for x in range(17, 24)})
    town_expected.update({(x, 29): 0x126B for x in range(16, 23)})
    water_expected = {(0, 68): 0x04B3,
                      **{(0, y): 0x0473 for y in range(69, 80)}}
    checked = []
    town = None
    for name, expected, count in [('SixIsland_Frlg', town_expected, 65),
                                   ('SixIsland_WaterPath_Frlg', water_expected, 12)]:
        layout, old = blocks(baseline, name, layouts)
        _, new = blocks(source, name, layouts)
        width = layout['width']
        actual = {(i % width, i // width): b for i, (a, b) in enumerate(zip(old, new)) if a != b}
        wanted_changes = {point: value for point, value in expected.items()
                          if old[point[1] * width + point[0]] != value}
        assert actual == wanted_changes and len(actual) == count, (name, actual)
        assert all(new[y * width + x] == value for (x, y), value in expected.items())
        checked.append(dict(map=name, changed_cells=count,
                            exact_native_coast_words=True, dimensions=[width, layout['height']]))
        if name == 'SixIsland_Frlg':
            town = new
            # The old six western 2x3 trees have been removed ENTIRELY.
            for anchor_y in (3, 6, 9, 12, 16, 19):
                assert not any(new[(anchor_y+dy)*width+dx] & 1023 in
                               {0xE, 0xF, 0x1E, 0x1F, 0x24, 0x25, 0x26, 0x27}
                               for dy in range(3) for dx in range(2))
            for x, y, w, h in [(9, 7, 5, 5), (2, 13, 6, 5), (18, 8, 4, 4),
                               (15, 14, 5, 4), (3, 23, 7, 6), (10, 23, 3, 7)]:
                assert all(old[yy*width+xx] == new[yy*width+xx]
                           for yy in range(y, y+h) for xx in range(x, x+w)), (x, y, w, h)
            assert all(new[y*width+8] == 0x3001 for y in (3, 4, 5))
    tree_parts = {0xE, 0xF, 0x1E, 0x1F, 0x24, 0x25, 0x26, 0x27}
    owned, trees = set(), []
    for y in range(28):
        for x in range(23):
            if town[y*24+x] != 0x300E:
                continue
            rows = [[town[(y+dy)*24+x+dx] for dx in range(2)] for dy in range(3)]
            assert rows[0] == [0x300E, 0x300F] and rows[1] == [0x041E, 0x041F]
            assert rows[2][0] in (0x424, 0x426) and rows[2][1] in (0x425, 0x427)
            footprint = {(x+dx, y+dy) for dx in range(2) for dy in range(3)}
            assert not owned & footprint
            owned |= footprint
            trees.append([x, y, 2, 3])
    actual = {(x, y) for y in range(30) for x in range(24) if town[y*24+x] & 1023 in tree_parts}
    assert owned == actual and len(trees) == 12
    return dict(maps=checked, complete_tree_count=12, complete_tree_bounds=trees,
                removed_whole_tree_count=6, no_orphan_tree_parts=True,
                town_buildings_terminal_and_deck_unchanged=True,
                northern_dry_corridor_unchanged=True)


def audit_dewford(source, baseline, layouts):
    origins = {'DewfordTown': (-20, 0), 'Route106': (-80, -20),
               'Route107': (0, 0), 'JourneyDewfordPortIsland': (0, -12)}
    counts = {'DewfordTown': 27, 'Route106': 23, 'Route107': 17,
              'JourneyDewfordPortIsland': 9}
    checked, old_world, new_world = [], {}, {}
    for name, (ox, oy) in origins.items():
        layout, old = blocks(baseline, name, layouts)
        _, new = blocks(source, name, layouts)
        width = layout['width']
        actual, wanted = set(), set()
        for i, (before, after) in enumerate(zip(old, new)):
            x, y = i % width, i // width
            point = x+ox, y+oy
            old_world[point], new_world[point] = before, after
            owned = -7 <= point[0] < 14 and -11 <= point[1] < 7
            change = owned and before >> 12 == 4 and not before & 0xC00 and point not in {(5, 3), (6, 3)}
            if change:
                wanted.add((x, y))
                assert before & 1023 in {0x124, 0x201, 0x248, 0x249, 0x2AD}
                assert after == (before & 0xFFF) | 0x3000
            else:
                assert after == before, (name, x, y)
            if before != after:
                actual.add((x, y))
        assert actual == wanted and len(actual) == counts[name], name
        checked.append(dict(map=name, changed_floor_cells=len(actual),
                            only_elevation4_to3=True, metatiles_and_collisions_unchanged=True))
    former = []
    for (x, y), before in old_world.items():
        if before >> 12 != 4 or before & 0xC00:
            continue
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            other = x+dx, y+dy
            if other not in old_world:
                continue
            neighbor = old_world[other]
            if neighbor >> 12 == 3 and not neighbor & 0xC00 and new_world[x, y] >> 12 == new_world[other] >> 12 == 3:
                former.append([[x, y], list(other)])
    assert len(former) == 29
    assert new_world[5, 3] >> 12 == new_world[6, 3] >> 12 == 4
    assert new_world[6, 2] & 0xC00  # Terminal wall must not become a stair exit.
    old = (baseline / 'include/journey_dewford_bridge.h').read_text()
    new = (source / 'include/journey_dewford_bridge.h').read_text()
    start = 'static bool8 JourneyDewfordBridgeStairConnects('
    end = 'static void JourneyDewfordBridgeRestoreLevel('
    assert old[:old.index(start)] == new[:new.index(start)]
    assert old[old.index(end):] == new[new.index(end):]
    function = new[new.index(start):new.index(end)]
    for check in ['JourneyDewfordBridgeLowerObject(object)', 'sourceY == 16 && targetY == 15',
                  'sourceY == 15 && targetY == 16', 'sourceY == 2 && targetY == 3',
                  'sourceY == 3 && targetY == 2', 'sourceX == 4 && targetX == 5',
                  'sourceX == 5 && targetX == 4', 'sourceX == 6 && targetX == 7',
                  'sourceX == 7 && targetX == 6', 'object->currentElevation == ELEVATION_DEFAULT']:
        assert check in function, check
    assert not re.search(r'->\w+\s*=(?!=)', function), 'Stair predicate must not move the player'
    return dict(maps=checked, changed_dry_floor_cells=76,
                former_invisible_shore_boundaries=former,
                former_invisible_shore_boundary_count=29,
                unchanged_low_and_high_bridge_logic_outside_north_stair_predicate=True,
                wall_and_north_stair_levels_preserved=True)


def audit_graphics(source, baseline):
    def words(directory):
        raw = (directory / FOLDER / 'metatiles.bin').read_bytes()
        return struct.unpack('<'+'H'*(len(raw)//2), raw)
    old_words, new_words = words(baseline), words(source)
    assert len(old_words) == len(new_words)
    changed = []
    for i, (a, b) in enumerate(zip(old_words, new_words)):
        if a == b:
            continue
        mid, q = i//8 + 512, i % 8
        if (mid, q) in {(0x2DF, 7), (0x2E1, 5)}:
            assert (a, b) == (0x73F3, 0x73FB)
        else:
            assert a >> 12 == b >> 12 == 9 and (a & ~1023) == (b & ~1023)
            assert b & 1023 in {0x3FC, 0x3FD, 0x3FE}
        changed.append(dict(metatile=mid, quadrant=q, before=a, after=b))
    assert sum(row['quadrant'] in (5, 7) and row['metatile'] in (0x2DF, 0x2E1) for row in changed) == 2
    with Image.open(baseline / FOLDER / 'tiles.png') as image:
        old = image.copy()
    with Image.open(source / FOLDER / 'tiles.png') as image:
        new = image.copy()
    assert old.mode == new.mode == 'P' and old.size == new.size == (128, 256)
    changed_slots = set()
    for slot in range(512, 1024):
        x, y = (slot-512) % 16*8, (slot-512)//16*8
        if old.crop((x, y, x+8, y+8)).tobytes() != new.crop((x, y, x+8, y+8)).tobytes():
            changed_slots.add(slot)
    # Animation may also initialize constant sand quadrants. Only existing
    # palette-nine references, the three reviewed alias splits and stair cap
    # are authorized; every building/cable/flag slot remains byte-identical.
    old_p9 = {word & 1023 for word in old_words if word >> 12 == 9}
    assert changed_slots <= old_p9 | {0x3FB, 0x3FC, 0x3FD, 0x3FE}
    assert not changed_slots & set(range(682, 688))
    assert not {0x3FB, 0x3FC, 0x3FD, 0x3FE} & {word & 1023 for word in old_words}
    for slot in (0x3FB, 0x3FC, 0x3FD, 0x3FE):
        x, y = (slot-512)%16*8, (slot-512)//16*8
        assert set(old.crop((x,y,x+8,y+8)).getdata()) == {0}
    palette = lambda directory: [tuple(map(int, row.split())) for row in
                                (directory / FOLDER / 'palettes/09.pal').read_text().splitlines()[3:]]
    old_pal, new_pal = palette(baseline), palette(source)
    assert len(old_pal) == len(new_pal) == 16 and new_pal[0] == (0,0,0)
    assert all(a == b for a,b in zip(old_pal,new_pal) if a != (0,0,0))
    assert len({color for color in new_pal if color != (0,0,0)}) == 13
    frames = source / FOLDER / 'anim/shore_frames.bin'
    assert frames.stat().st_size == 4352 and digest(frames) == FRAME_SHA256
    header = (source / 'src/data/tilesets/journey_dewford_shore_anim.h').read_text()
    assert 'return gMapHeader.mapLayout->secondaryTileset == &gTileset_JourneyDewfordHarbor;' in header
    assert header.count('if (!JourneyDewfordShoreAnimationActive())') == 2
    for function in ['QueueJourneyDewfordShoreAnimation', 'RefreshJourneyDewfordShoreAnimation']:
        assert function in header
    destinations = [int(x) for x in re.findall(r'TILE_OFFSET_4BPP\((\d+)\)', header)]
    assert destinations and set(destinations) <= EXPECTED_DYNAMIC_GRAPHICS | {464}
    expected_runs = [(0,514,1),(16,523,1),(32,526,2),(64,530,1),
                     (80,533,5),(160,543,4),(224,1020,3)]
    for function in ('AppendTilesetAnimToBuffer','CpuCopy16'):
        entries = re.findall(re.escape(function)+r'\(frame \+ (\d+), \((?:u16 \*|void \*)\)\(BG_VRAM \+ TILE_OFFSET_4BPP\((\d+)\)\), (\d+) \* TILE_SIZE_4BPP\);',header)
        assert [tuple(map(int,row)) for row in entries] == expected_runs, function
    assert header.count('sJourneyDewfordShoreFrames + phase * 272;') == 2
    assert 'AppendTilesetAnimToBuffer(gTilesetAnims_General_SandWaterEdge[phase],' in header
    assert 'CpuCopy16(gTilesetAnims_General_SandWaterEdge[phase],' in header
    after_dma = '''void RefreshJourneyDewfordShoreAfterDma3Requests(void)
{
    // The secondary bank load queues a full graphics copy. Wait until that
    // queue finishes before replacing its baked phase-zero private tiles.
    // Ordinary VBlanks, including UI and battle screens, return immediately.
    if (!sJourneyDewfordShoreRefreshPending)
        return;
    if (!JourneyDewfordShoreAnimationActive() || sPrimaryTilesetAnimCallback != TilesetAnim_General)
    {
        sJourneyDewfordShoreRefreshPending = FALSE;
        return;
    }
    if (CheckForSpaceForDma3Request(-1) != 0)
        return;
    RefreshContinuousOceanTiles();
    sJourneyDewfordShoreRefreshPending = FALSE;
}
'''
    assert header.count('void RefreshJourneyDewfordShoreAfterDma3Requests(void)') == 1
    assert header.endswith('\n'+after_dma), 'Post-DMA refresh must be guarded, delayed, and one-shot'
    # The entire generated implementation has a literal reviewed contract.
    # Matching only transfer destinations would permit unrelated writes or
    # a second unguarded callback inside this new private header.
    expected_header = '''// Generated from native water and sand-edge phases; private Dewford bank only.
extern const struct Tileset gTileset_JourneyDewfordHarbor;
static const u16 sJourneyDewfordShoreFrames[] = INCBIN_U16("data/tilesets/secondary/journey_dewford_harbor/anim/shore_frames.bin");

static bool32 JourneyDewfordShoreAnimationActive(void)
{
    return gMapHeader.mapLayout->secondaryTileset == &gTileset_JourneyDewfordHarbor;
}

static void QueueJourneyDewfordShoreAnimation(u16 phase)
{
    const u16 *frame = sJourneyDewfordShoreFrames + phase * 272;
    if (!JourneyDewfordShoreAnimationActive())
        return;
'''
    expected_header += '\n'.join('    AppendTilesetAnimToBuffer(frame + %d, (u16 *)(BG_VRAM + TILE_OFFSET_4BPP(%d)), %d * TILE_SIZE_4BPP);' % run for run in expected_runs)
    expected_header += '''
    // Queue the native edge in the same batch as the sea and the private
    // composites. A second global-clock read on the next local timer tick
    // can otherwise select the following phase at a VBlank phase boundary.
    AppendTilesetAnimToBuffer(gTilesetAnims_General_SandWaterEdge[phase], (u16 *)(BG_VRAM + TILE_OFFSET_4BPP(464)), 10 * TILE_SIZE_4BPP);
}

static void RefreshJourneyDewfordShoreAnimation(u16 phase)
{
    const u16 *frame = sJourneyDewfordShoreFrames + phase * 272;
    if (!JourneyDewfordShoreAnimationActive())
        return;
'''
    expected_header += '\n'.join('    CpuCopy16(frame + %d, (void *)(BG_VRAM + TILE_OFFSET_4BPP(%d)), %d * TILE_SIZE_4BPP);' % run for run in expected_runs)
    expected_header += '''
    CpuCopy16(gTilesetAnims_General_SandWaterEdge[phase], (void *)(BG_VRAM + TILE_OFFSET_4BPP(464)), 10 * TILE_SIZE_4BPP);
}

'''+after_dma
    assert header == expected_header, 'Unreviewed private shoreline animation behavior'
    native = (source / 'src/tileset_anims.c').read_text()
    assert '#include "data/tilesets/journey_dewford_shore_anim.h"' in native
    assert 'RefreshJourneyDewfordShoreAnimation(phase);' in native
    assert native.count('QueueJourneyDewfordShoreAnimation(i);') == 1
    assert 'JourneyDewfordShoreAnimationActive()' in native
    # Reconstruct only the reviewed call sites, declaration and include from the
    # parent. In particular, unrelated FRLG/Hoenn callbacks and their clocks
    # cannot be changed under the broad tileset_anims.c filename allowlist.
    expected_native = (baseline / 'src/tileset_anims.c').read_text()
    assert expected_native.count('#include "main.h"') == 1 and '#include "dma3.h"' not in expected_native
    expected_native = expected_native.replace('#include "main.h"', '#include "main.h"\n#include "dma3.h"')
    anchor = 'static void QueueAnimTiles_General_Water(u16 timer)\n{'
    expected_native = expected_native.replace(anchor,'#include "data/tilesets/journey_dewford_shore_anim.h"\n\n'+anchor)
    water = '    AppendTilesetAnimToBuffer(gTilesetAnims_General_Water[i], (u16 *)(BG_VRAM + TILE_OFFSET_4BPP(432)), 30 * TILE_SIZE_4BPP);'
    expected_native = expected_native.replace(water,water+'\n    QueueJourneyDewfordShoreAnimation(i);')
    sand = '    u16 i = timer % ARRAY_COUNT(gTilesetAnims_General_SandWaterEdge);'
    expected_native = expected_native.replace(sand,sand+'\n    if (JourneyDewfordShoreAnimationActive())\n        return;')
    initial = '    if (sPrimaryTilesetAnimCallback == TilesetAnim_General)\n        CpuCopy16(gTilesetAnims_General_Water[phase], (void *)(BG_VRAM + TILE_OFFSET_4BPP(432)), 30 * TILE_SIZE_4BPP);'
    expected_native = expected_native.replace(initial,'    if (sPrimaryTilesetAnimCallback == TilesetAnim_General)\n    {\n        CpuCopy16(gTilesetAnims_General_Water[phase], (void *)(BG_VRAM + TILE_OFFSET_4BPP(432)), 30 * TILE_SIZE_4BPP);\n        RefreshJourneyDewfordShoreAnimation(phase);\n    }')
    declaration = 'static void RefreshContinuousOceanTiles(void);'
    assert expected_native.count(declaration) == 1
    expected_native = expected_native.replace(declaration, declaration+'\nstatic bool32 JourneyDewfordShoreAnimationActive(void);\nstatic bool32 sJourneyDewfordShoreRefreshPending;')
    secondary = 'void InitSecondaryTilesetAnimation(void)\n{\n    _InitSecondaryTilesetAnimation();\n}'
    assert expected_native.count(secondary) == 1
    expected_native = expected_native.replace(secondary, 'void InitSecondaryTilesetAnimation(void)\n{\n    _InitSecondaryTilesetAnimation();\n    sJourneyDewfordShoreRefreshPending = JourneyDewfordShoreAnimationActive();\n}')
    assert native == expected_native, 'Unrelated animation behavior or clock changed'
    # Permit exactly the public declaration, include, and one post-queue call.
    # No main-loop, interrupt, menu, audio, link or DMA-manager code may change.
    expected_api = (baseline / 'include/tileset_anims.h').read_text()
    api_anchor = 'void InitSecondaryTilesetAnimation(void);'
    assert expected_api.count(api_anchor) == 1
    expected_api = expected_api.replace(api_anchor, api_anchor+'\nvoid RefreshJourneyDewfordShoreAfterDma3Requests(void);')
    assert (source / 'include/tileset_anims.h').read_text() == expected_api, 'Unrelated public tileset API changed'
    expected_main = (baseline / 'src/main.c').read_text()
    assert expected_main.count('#include "dma3.h"') == 1 and '#include "tileset_anims.h"' not in expected_main
    expected_main = expected_main.replace('#include "dma3.h"', '#include "dma3.h"\n#include "tileset_anims.h"')
    dma_anchor = '    ProcessDma3Requests();'
    assert expected_main.count(dma_anchor) == 1
    expected_main = expected_main.replace(dma_anchor, dma_anchor+'\n    RefreshJourneyDewfordShoreAfterDma3Requests();')
    assert (source / 'src/main.c').read_text() == expected_main, 'Unrelated main/VBlank behavior changed'
    return dict(private_graphic_slots_changed=sorted(changed_slots),
                private_metatile_word_changes=changed, native_stair_cap_complete=True,
                shoreline_alias_slots_previously_empty=True,
                native_flag_and_all_unrelated_graphics_preserved=True,
                old_nonempty_palette_entries_preserved=True,
                native_phase_count=8, private_frame_bytes=4352,
                frame_data_sha256=FRAME_SHA256,
                runtime_private_bank_guard_present=True,
                native_private_secondary_reload_refresh=True,
                native_private_secondary_reload_after_dma_refresh=True,
                secondary_reload_only_marks_pending=True,
                post_dma_refresh_only_after_all_requests_complete=True,
                post_dma_refresh_one_shot_with_private_bank_and_general_callback_guards=True,
                main_vblank_only_reviewed_post_dma_call=True,
                public_tileset_api_only_reviewed_declaration=True,
                native_global_phase_on_load_hook_present=True)


def audit_route_positions(source, baseline):
    """Prove the raw GPS changes without using the repair helper or marker."""
    path = 'src/data/journey_world_position.h'
    old_header = (baseline/path).read_bytes().decode('ascii')
    new_header = (source/path).read_bytes().decode('ascii')
    payload = re.compile(r'static const u16 sWorldNavigationPixels\[\] = \{([0-9,\s]+)\};')
    old_matches, new_matches = list(payload.finditer(old_header)), list(payload.finditer(new_header))
    assert len(old_matches) == len(new_matches) == 1
    old_match, new_match = old_matches[0], new_matches[0]
    # This includes all anchors, projections, first indices, map IDs, grid
    # dimensions, declarations and every byte outside the packed u16 payload.
    assert old_header[:old_match.start(1)] == new_header[:new_match.start(1)]
    assert old_header[old_match.end(1):] == new_header[new_match.end(1):]
    old = [int(value) for value in old_match[1].split(',')]
    new = [int(value) for value in new_match[1].split(',')]
    assert len(old) == len(new) and all(0 <= value <= 65535 for value in old+new)
    declaration = re.search(r'static const struct JourneyWorldTileGrid sWorldTileGrids\[\] = \{(.*?)\};', old_header, re.S)
    assert declaration
    rows = re.findall(r'\{(\d+), \(MAP_GROUP\((\w+)\)<<8\)\|MAP_NUM\(\2\), (\d+), (\d+)\}', declaration[1])
    grids, cursor = {}, 0
    for first, ident, width, height in rows:
        first, width, height = map(int, (first, width, height))
        assert ident not in grids and first == cursor and width > 0 and height > 0
        grids[ident] = dict(first=first, width=width, height=height)
        cursor += width*height
    assert cursor == len(old)
    assert set(COAST_GPS_CONTRACTS) <= grids.keys()
    allowed = {index for ident in COAST_GPS_CONTRACTS
               for index in range(grids[ident]['first'], grids[ident]['first'] + 17*13)}
    changed = {index for index, (a, b) in enumerate(zip(old, new)) if a != b}
    assert changed and changed <= allowed, 'GPS changed outside the seven literal coast grids'
    maps = {mapping['id']: mapping for file in (baseline/'data/maps').glob('*/map.json')
            for mapping in [json.loads(file.read_text())]}
    layouts = {row['id']:row for row in json.loads((baseline/'data/layouts/layouts.json').read_text())['layouts']}

    def pixel(values, ident, x, y):
        grid = grids[ident]
        assert 0 <= x < grid['width'] and 0 <= y < grid['height']
        word = values[grid['first']+y*grid['width']+x]
        return [word & 255, word >> 8]

    def crossing(points, axis, sign):
        primary = [point[axis] for point in points]
        deltas = [b-a for a, b in zip(primary, primary[1:])]
        other = [point[1-axis] for point in points]
        low, high = sorted((other[0], other[-1]))
        excursion = max(max(low-value, value-high, 0) for value in other)
        return dict(pixels=points, primary_axis='xy'[axis], primary_direction=sign,
                    extent_pixels=abs(primary[-1]-primary[0]),
                    backward_pixels=sum(max(-sign*delta, 0) for delta in deltas) if sign else sum(map(abs, deltas)),
                    secondary_endpoint_interval=[low, high],
                    maximum_secondary_excursion=excursion)

    records = []
    for ident, (name, east_contract, south_contract) in COAST_GPS_CONTRACTS.items():
        grid = grids[ident]
        assert (grid['width'], grid['height']) == (17, 13)
        mapping = maps[ident]
        assert mapping['id'] == ident
        before = [pixel(old, ident, x, y) for y in range(13) for x in range(17)]
        after = [pixel(new, ident, x, y) for y in range(13) for x in range(17)]
        assert len({tuple(point) for point in after}) > 1
        changed_tiles = sum(a != b for a, b in zip(before, after))
        assert changed_tiles > 0, (name, 'Coast fold repair did not run')
        maximum = max(max(abs(a-b) for a, b in zip(pixel(new, ident, x, y), pixel(new, ident, xx, yy)))
                      for y in range(13) for x in range(17)
                      for xx, yy in ((x+1, y), (x, y+1)) if xx < 17 and yy < 13)
        assert maximum <= 2, (name, 'Unbounded native GPS step', maximum)
        seams, fixed = [], set()
        for connection in mapping['connections']:
            other = connection['map']
            assert other in grids
            target = grids[other]
            direction, offset = connection['direction'], connection['offset']
            assert direction in ('left', 'right', 'up', 'down')
            vertical = direction in ('left', 'right')
            limit = 13 if vertical else 17
            other_limit = target['height'] if vertical else target['width']
            samples = []
            for coordinate in range(max(0, offset), min(limit, offset+other_limit)):
                x, y = ((0 if direction == 'left' else 16), coordinate) if vertical else (coordinate, 0 if direction == 'up' else 12)
                xx, yy = ((target['width']-1 if direction == 'left' else 0), coordinate-offset) if vertical else (coordinate-offset, target['height']-1 if direction == 'up' else 0)
                original = pixel(old, ident, x, y)
                assert original == pixel(old, other, xx, yy), (name, 'Parent seam mismatch')
                assert original == pixel(new, ident, x, y) == pixel(new, other, xx, yy), (name, direction, coordinate)
                fixed.add((x, y))
                samples.append(dict(tile=[x,y], neighbor_tile=[xx,yy], pixel=original))
            assert samples
            seams.append(dict(neighbor_map_id=other, direction=direction, offset=offset,
                              shared_border_pixels=samples, unchanged=True, maximum_seam_delta=0))
        layout, old_blocks = blocks(baseline, name, layouts)
        _, new_blocks = blocks(source, name, layouts)
        assert (layout['width'],layout['height']) == (17,13) and old_blocks == new_blocks
        # These are the actual straight native sea crossings. Two's bottom
        # center cell is a rock, so its north/south sea path ends at y=11.
        lines = [('east', [(x,6) for x in range(17)], east_contract),
                 ('south', [(8,y) for y in range(12 if ident == 'MAP_TWO_ISLAND_HARBOR' else 13)], south_contract)]
        crossings = []
        for direction, coordinates, (axis, sign, bend_limit) in lines:
            assert all(old_blocks[y*17+x] == new_blocks[y*17+x] == 0x112B for x, y in coordinates), (name, direction, 'Not a straight native sea crossing')
            previous = crossing([pixel(old, ident, x, y) for x, y in coordinates],axis,sign)
            current = crossing([pixel(new, ident, x, y) for x, y in coordinates],axis,sign)
            assert current['backward_pixels'] == 0, (name,direction,current)
            assert current['maximum_secondary_excursion'] <= bend_limit, (name,direction,current)
            if sign:
                assert sign*(current['pixels'][-1][axis]-current['pixels'][0][axis]) > 0, (name,direction,'Collapsed crossing')
            crossings.append(dict(direction=direction, tiles=[list(point) for point in coordinates],
                                  native_sea_word=0x112B, before=previous, after=current,
                                  allowed_secondary_excursion=bend_limit,
                                  primary_coordinate_monotonic=True))
        records.append(dict(map=name,map_id=ident,dimensions=[17,13],first=grid['first'],
                            changed_tiles=changed_tiles,fixed_connected_border_tiles=len(fixed),
                            maximum_neighbor_pixel_step=maximum,seams=seams,
                            central_native_sea_crossings=crossings,
                            before_grid_sha256=hashlib.sha256(bytes(value for point in before for value in point)).hexdigest(),
                            after_grid_sha256=hashlib.sha256(bytes(value for point in after for value in point)).hexdigest()))
    assert sum(len(row['seams']) for row in records) == 25
    return dict(position_header_sha256=digest(source/path), changed_tiles=len(changed),
                changed_map_ids=sorted(COAST_GPS_CONTRACTS), packed_values_checked=len(old),
                all_other_packed_values_bitwise_unchanged=True,
                all_metadata_anchors_dimensions_and_first_indices_unchanged=True,
                all_25_original_connected_borders_exact=True,
                maximum_neighbor_pixel_step=max(row['maximum_neighbor_pixel_step'] for row in records),
                actual_straight_sea_crossings_primary_coordinate_monotonic=True,
                secondary_atlas_bends_bounded_by_literal_contract=True,
                fly_permissions_and_projection_code_unchanged=True,maps=records)


def audit_route_identity(source, baseline):
    names, records = {}, []
    for island in ISLANDS:
        path = f'data/maps/{island}Island_Harbor_Frlg/map.json'
        old = json.loads((baseline/path).read_text())
        new = json.loads((source/path).read_text())
        assert old['id'] == 'MAP_'+island.upper()+'_ISLAND_HARBOR'
        assert old['show_map_name'] is False and old['map_type'] == 'MAP_TYPE_ROUTE'
        assert new == (old | {'show_map_name':True, 'map_type':'MAP_TYPE_OCEAN_ROUTE'})
        assert not new['object_events'] and not new['warp_events']
        old_name = 'THREE ISLE PORT' if island == 'Three' else island.upper()+' ISLAND'
        label = island.upper()+' ISLAND COAST'
        names[old['id']] = (old_name,label)
        records.append(dict(map=island+'Island_Harbor_Frlg', map_id=old['id'],
                            before_name=old_name,name=label,show_map_name=True,
                            map_type='MAP_TYPE_OCEAN_ROUTE',
                            geometry_events_connections_and_region_section_unchanged=True))
    before = (baseline/'src/data/journey_world_map.h').read_text()
    after = (source/'src/data/journey_world_map.h').read_text()
    old_lines,new_lines = before.splitlines(),after.splitlines()
    assert len(old_lines) == len(new_lines)
    observed = set()
    row = re.compile(r'^\s*\{\(MAP_GROUP\((\w+)\)<<8\)\|MAP_NUM\(\1\), (\w+), (\d+), (\d+), COMPOUND_STRING\("([^"]+)"\)\},$')
    for old,new in zip(old_lines,new_lines):
        if old == new:
            continue
        match = row.fullmatch(old)
        assert match and match[1] in names and match[1] not in observed
        ident = match[1]
        old_name,label = names[ident]
        assert match[5] == old_name
        assert new == old.replace('"'+old_name+'"','"'+label+'"')
        observed.add(ident)
    assert observed == set(names)
    atlas = {}
    for symbol in ('sWorldTiles','sWorldTilemap','sWorldPalette'):
        expression = r'static const u\d+ '+symbol+r'\[\] = \{[^}]+\};'
        old = re.search(expression,before)[0]
        assert re.search(expression,after)[0] == old
        atlas[symbol] = hashlib.sha256(old.encode()).hexdigest()
    gps = audit_route_positions(source,baseline)
    for path in ('src/journey_world_map.c','src/journey_world_position.c'):
        if (baseline/path).exists():
            assert (source/path).read_bytes() == (baseline/path).read_bytes()
    return dict(routes=records,renamed_coast_count=7,only_point_names_changed=True,
                atlas_arrays_sha256=atlas,atlas_graphics_and_point_coordinates_unchanged=True,
                per_tile_gps=gps,position_header_sha256=gps['position_header_sha256'],
                existing_noncoast_per_tile_gps_and_fly_permissions_unchanged=True,
                physical_routes_not_created_or_duplicated=True)


def validate(source, baseline, output, preflight=False):
    source, baseline, output = map(Path, (source, baseline, output))
    assert source.resolve() != baseline.resolve()
    assert digest(baseline/'pokeemerald.gba') == PARENT_ROM_SHA256
    rom_sha = None if preflight else digest(source/'pokeemerald.gba')
    if not preflight:
        assert rom_sha != PARENT_ROM_SHA256
    assert len(PRIOR) == 162
    marker = json.loads((source/('.journey-'+LAYER)).read_text())
    assert marker['layer'] == LAYER
    animation_metadata = marker['shore_animation']
    assert animation_metadata['native_private_secondary_reload_after_dma_refresh'] is True
    assert animation_metadata['native_sand_and_private_shore_queued_with_water_phase'] is True
    assert animation_metadata['runtime_changes_restricted_to_private_dewford_bank'] is True
    assert animation_metadata['native_phase_count'] == 8
    assert animation_metadata['words_per_phase'] == 272
    assert animation_metadata['frame_data_sha256'] == FRAME_SHA256
    assert set(animation_metadata['changed_paths']) == {
        FOLDER+'/tiles.png', FOLDER+'/metatiles.bin', FOLDER+'/palettes/09.pal',
        FOLDER+'/anim/shore_frames.bin', 'src/data/tilesets/journey_dewford_shore_anim.h',
        'src/tileset_anims.c', 'src/main.c', 'include/tileset_anims.h',
    }
    expected = dict(json.loads((baseline/'.source-acquired.json').read_text())['sha256'])
    for layer in PRIOR:
        expected.update(json.loads((baseline/('.journey-'+layer)).read_text())['prepared_sha256'])
    outputs = marker['prepared_sha256']
    changed = {name for name, sha in outputs.items() if sha != expected.get(name)}
    assert changed == set(outputs) == ALLOWED_SOURCE_FILES
    assert len(expected) > 30000
    for name, sha in expected.items():
        assert digest(baseline/name) == sha, ('Baseline changed',name)
    for name, sha in (expected|outputs).items():
        assert digest(source/name) == sha, ('Unexpected source change',name)
    history = ['.source-acquired.json', *['.journey-'+name for name in PRIOR]]
    for name in history:
        assert (source/name).read_bytes() == (baseline/name).read_bytes(), name
    # Reject new compilation units/headers hidden outside the reviewed layer.
    for suffix in ('.c', '.h'):
        before = {path.relative_to(baseline).as_posix() for path in baseline.rglob('*'+suffix)}
        after = {path.relative_to(source).as_posix() for path in source.rglob('*'+suffix)}
        assert after-before <= ALLOWED_SOURCE_FILES and not before-after
        for name in (before&after)-expected.keys():
            assert (source/name).read_bytes() == (baseline/name).read_bytes(), ('Generated header changed',name)
    with tempfile.TemporaryDirectory(prefix='coastal-closures-replay-', dir='/tmp') as temporary:
        replay = Path(temporary)
        for name in [*expected,*history]:
            destination = replay/name
            destination.parent.mkdir(parents=True, exist_ok=True)
            try:
                os.link(baseline/name,destination)
            except OSError:
                shutil.copyfile(baseline/name,destination)
        fresh = json.loads(json.dumps(prepare(replay)))
        assert fresh == marker, 'Independent atomic replay disagrees'
        assert prepare(replay) == fresh, 'Layer is not idempotent'
        for name, sha in outputs.items():
            assert digest(replay/name) == sha
        for name in outputs.keys() & expected.keys():
            assert digest(baseline/name) == expected[name], 'Replay changed its baseline'
    assert (source/'data/layouts/layouts.json').read_bytes() == (baseline/'data/layouts/layouts.json').read_bytes()
    layouts = {row['id']:row for row in json.loads((baseline/'data/layouts/layouts.json').read_text())['layouts']}
    for path in (baseline/'data/maps').glob('*/map.json'):
        relative = path.relative_to(baseline).as_posix()
        if relative not in COAST_HEADERS:
            assert path.read_bytes() == (source/relative).read_bytes()
    six = audit_six(source,baseline,layouts)
    dewford = audit_dewford(source,baseline,layouts)
    graphics = audit_graphics(source,baseline)
    route_identity = audit_route_identity(source,baseline)
    gyms = json.loads((baseline/'.journey-extra-gyms').read_text())['gyms']
    assert len(gyms) == 8
    for gym in gyms:
        name = 'data/maps/'+gym['name']+'/map.json'
        mapping = json.loads((baseline/name).read_text())
        for path in [name,layouts[mapping['layout']]['blockdata_filepath'],layouts[mapping['layout']]['border_filepath']]:
            assert (source/path).read_bytes() == (baseline/path).read_bytes()
    abi_symbols = ['sizeof(struct SaveBlock1)','sizeof(struct SaveBlock2)',
                   'sizeof(struct ObjectEvent)','sizeof(struct LinkPlayer)',
                   'sizeof(struct LinkPlayerBlock)','FLAGS_COUNT']
    includes = ['global.h','constants/flags.h','link.h']
    abi = compiled_values(source,abi_symbols,includes,baseline)
    assert abi == compiled_values(baseline,abi_symbols,includes,baseline)
    moves = re.findall(r'F\((\w+)\)', (baseline/'include/constants/tms_hms.h').read_text().split('#define FOREACH_HM')[0])
    items = ['ITEM_TM_'+move for move in moves]+['ITEM_HM_SURF','ITEM_HM_DIVE',
             'ITEM_HM_WATERFALL','ITEM_HM_FLY','ITEM_FULL_RESTORE','ITEM_MAX_REVIVE','ITEM_POKE_BALL']
    item_values = compiled_values(source,items,['global.h','constants/items.h'],baseline)
    assert item_values == compiled_values(baseline,items,['global.h','constants/items.h'],baseline)
    compiled_asset = None
    if not preflight:
        rom = (source/'pokeemerald.gba').read_bytes()
        assert len(rom) == 33554432
        assert rom[0xBD] == (-sum(rom[0xA0:0xBD])-0x19)&255
        symbols = subprocess.check_output([str(ROOT/'.local/arm-binutils/usr/bin/arm-none-eabi-nm'),
                                          '-S','--defined-only',str(source/'pokeemerald.elf')],text=True)
        match = re.search(r'^([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+\w\s+sJourneyDewfordShoreFrames$',symbols,re.M)
        assert match, 'New animation asset missing from compiled ELF'
        address, size = (int(x,16) for x in match.groups())
        assert size == 4352 and 0x08000000 <= address < 0x0A000000-size
        embedded = rom[address-0x08000000:address-0x08000000+size]
        assert hashlib.sha256(embedded).hexdigest() == FRAME_SHA256
        compiled_asset = dict(address=address, bytes=size,sha256=FRAME_SHA256)
        assert digest(source/'pokeemerald.gba') == rom_sha
    assert digest(baseline/'pokeemerald.gba') == PARENT_ROM_SHA256
    report = dict(passed=True,kind='coastal-closures-source',
                  rom_sha256=rom_sha,parent_rom_sha256=PARENT_ROM_SHA256,
                  compiled_rom=not preflight,preflight=bool(preflight),layers=PRIOR+[LAYER],
                  changed_files=sorted(changed),allowed_changed_files=sorted(ALLOWED_SOURCE_FILES),
                  source_hashes_checked=len(expected|outputs),independent_replay=True,idempotent=True,
                  unrelated_source_files_unchanged=True,save_and_link_abi_unchanged=True,
                  atlas_graphics_unchanged=True,gyms_and_campaign_unchanged=True,
                  events_connections_and_layout_dimensions_unchanged=True,extra_gyms_preserved=8,
                  compiled_abi=dict(zip(abi_symbols,abi)),
                  original_tm_hm_and_item_numbers_preserved=True,
                  compiled_item_constants_preserved=len(items),
                  six_cliffs=six,dewford_movement=dewford,shore_animation=graphics,
                  route_identity=route_identity,
                  compiled_animation_asset=compiled_asset)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--baseline',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--preflight',action='store_true')
    args = parser.parse_args()
    report = validate(args.source,args.baseline,args.output,args.preflight)
    print(json.dumps({key:report[key] for key in ['passed','rom_sha256','preflight','changed_files']},indent=2))
