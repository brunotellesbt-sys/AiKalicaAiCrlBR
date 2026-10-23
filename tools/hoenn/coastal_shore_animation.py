"""Restore native animation inside Dewford's flattened private shore art.

The harbor compiler baked RGB water into palette-9 foregrounds and bridge
underlays. Rebuild those exact shapes from the native eight animation phases;
retain all unrelated art, metatile attributes, map blocks and foreground words.
This helper stages outputs through the caller's atomic candidate Layer.
"""
import hashlib
import io
import struct

from PIL import Image

from compile_dewford_harbor_art import SHORE, finish_beach, inner_beaches
from render_sea_maps import MapRenderer


FOLDER = 'data/tilesets/secondary/journey_dewford_harbor'
BANK = 'gTileset_JourneyDewfordHarbor'
ANIMATION = FOLDER + '/anim/shore_frames.bin'
HEADER = 'src/data/tilesets/journey_dewford_shore_anim.h'


def _pixels(image):
    """Pillow 11.3 (CI) and newer local releases expose the same pixels."""
    method = getattr(image, 'get_flattened_data', None)
    return method() if method is not None else image.getdata()


def _images(renderer):
    images = inner_beaches(renderer)
    images[0x170] = renderer.render('Route107', values=[0x170], dimensions=(1, 1), npcs=False)[0]
    for mid in SHORE:
        images[mid] = finish_beach(renderer.render('Route107', values=[mid], dimensions=(1, 1), npcs=False)[0])
    return images


def _native_frames(source):
    frames = []
    for phase in range(8):
        renderer = MapRenderer(source)
        tiles, palettes, words = renderer.tileset('gTileset_General')
        tiles = tiles.copy()
        for name, start, count in [('water', 432, 30), ('sand_water_edge', 464, 10)]:
            # The native eight-entry sand sequence repeats frame zero last.
            frame = 0 if name == 'sand_water_edge' and phase == 7 else phase
            image = Image.open(source / f'data/tilesets/primary/general/anim/{name}/{frame}.png')
            for index in range(count):
                x, y = index % (image.width // 8) * 8, index // (image.width // 8) * 8
                target = start + index
                tiles.paste(image.crop((x, y, x + 8, y + 8)),
                            (target % (tiles.width // 8) * 8, target // (tiles.width // 8) * 8))
        renderer.cache['gTileset_General'] = tiles, palettes, words
        frames.append(_images(renderer))
    return frames


def _flip(image, word):
    if word & 0x400:
        image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    if word & 0x800:
        image = image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    return image


def _pack(tile):
    values = list(_pixels(tile))
    return bytes(values[index] | values[index + 1] << 4 for index in range(0, 64, 2))


def repair(layer):
    source = layer.source
    touched = set()

    def raw(path):
        return layer.outputs[path] if path in layer.outputs else (source / path).read_bytes()

    def stage(path, value):
        layer.stage(path, value)
        touched.add(path)

    renderer = MapRenderer(source)
    original_images = _images(renderer)
    frames = _native_frames(source)
    tiles = Image.open(io.BytesIO(raw(FOLDER + '/tiles.png'))).copy()
    assert tiles.mode == 'P' and tiles.width == 128
    original_words = struct.unpack('<' + 'H' * (len(raw(FOLDER + '/metatiles.bin')) // 2),
                                   raw(FOLDER + '/metatiles.bin'))
    words = list(original_words)
    colors = [tuple(map(int, line.split())) for line in raw(FOLDER + '/palettes/09.pal').decode().splitlines()[3:]]
    assert len(colors) == 16 and colors[0] == (0, 0, 0)
    original_colors = colors.copy()
    required = sorted({color for images in frames for image in images.values()
                       for color in _pixels(image)})
    for color in required:
        if color not in colors:
            vacant = next((index for index in range(1, 16) if colors[index] == (0, 0, 0)), None)
            assert vacant is not None, ('Animated shore exceeds the private palette', required)
            colors[vacant] = color
    assert len(set(required)) <= 15

    def graphic(slot):
        index = slot - 512
        x, y = index % 16 * 8, index // 16 * 8
        return tiles.crop((x, y, x + 8, y + 8))

    def indexed(image):
        result = Image.new('P', image.size)
        result.putdata([colors.index(color) for color in _pixels(image)])
        return result

    used = {word & 1023 for word in words}
    # 0x3FB belongs to the separate stair-cap repair. Three late, empty slots
    # split static-image aliases whose native animation phases differ.
    available = iter(slot for slot in range(0x3FC, 0x400)
                     if slot not in used and not any(_pixels(graphic(slot))))
    assignments, sequences, groups, splits = {}, {}, [], []
    for mid in range(512, 512 + len(words) // 8):
        for layer_at in [0, 4]:
            offset = (mid - 512) * 8 + layer_at
            group = words[offset:offset + 4]
            if not any(word >> 12 == 9 for word in group):
                continue
            assert all(word >> 12 == 9 for word in group), (mid, layer_at, group)
            old = Image.new('RGB', (16, 16))
            for quadrant, word in enumerate(group):
                image = graphic(word & 1023)
                image.putpalette([component for color in original_colors for component in color])
                old.paste(_flip(image.convert('RGB'), word), (quadrant % 2 * 8, quadrant // 2 * 8))
            matches = [key for key, image in original_images.items() if image.tobytes() == old.tobytes()]
            assert matches, ('Unknown private shore shape', hex(mid), layer_at)
            assert len({tuple(images[key].tobytes() for images in frames) for key in matches}) == 1, (mid, matches)
            key = matches[0]
            groups.append(dict(metatile=mid, word_offset=layer_at, native_shape=key))
            for quadrant, word in enumerate(group):
                x, y = quadrant % 2 * 8, quadrant // 2 * 8
                images = [indexed(_flip(frame[key].crop((x, y, x + 8, y + 8)), word)) for frame in frames]
                signature = tuple(image.tobytes() for image in images)
                slot = word & 1023
                variants = assignments.setdefault(slot, {})
                if signature not in variants:
                    target = slot if not variants else next(available)
                    variants[signature] = target
                    sequences[target] = images
                    if target != slot:
                        splits.append(dict(original_graphic=slot, new_graphic=target))
                words[offset + quadrant] = (word & ~1023) | variants[signature]
    assert len(groups) == 30 and len(assignments) == 17 and len(splits) == 3
    assert all(before == after or before >> 12 == after >> 12 == 9
               for before, after in zip(original_words, words))
    assert not set(sequences) & set(range(682, 688)), 'Native animated flag overwritten'

    dynamic = sorted(slot for slot, images in sequences.items()
                     if len({image.tobytes() for image in images}) > 1)
    runs = []
    for slot in dynamic:
        if runs and slot == runs[-1]['start'] + runs[-1]['count']:
            runs[-1]['count'] += 1
        else:
            runs.append(dict(start=slot, count=1))
    assert len(runs) + 3 <= 20, 'Native animation DMA queue capacity exceeded'
    payload, word_offset = bytearray(), 0
    for run in runs:
        run['frame_word_offset'] = word_offset
        word_offset += run['count'] * 16
    for phase in range(8):
        for run in runs:
            for slot in range(run['start'], run['start'] + run['count']):
                payload.extend(_pack(sequences[slot][phase]))
    assert len(payload) == 8 * word_offset * 2
    for slot, images in sequences.items():
        tiles.paste(images[0], ((slot - 512) % 16 * 8, (slot - 512) // 16 * 8))
    png = io.BytesIO()
    tiles.save(png, format='PNG')
    stage(FOLDER + '/tiles.png', png.getvalue())
    stage(FOLDER + '/metatiles.bin', struct.pack('<' + 'H' * len(words), *words))
    stage(FOLDER + '/palettes/09.pal', 'JASC-PAL\n0100\n16\n' + '\n'.join(' '.join(map(str, color)) for color in colors) + '\n')
    stage(ANIMATION, bytes(payload))

    queue = '\n'.join('    AppendTilesetAnimToBuffer(frame + %d, (u16 *)(BG_VRAM + TILE_OFFSET_4BPP(%d)), %d * TILE_SIZE_4BPP);'
                      % (run['frame_word_offset'], run['start'], run['count']) for run in runs)
    refresh = '\n'.join('    CpuCopy16(frame + %d, (void *)(BG_VRAM + TILE_OFFSET_4BPP(%d)), %d * TILE_SIZE_4BPP);'
                        % (run['frame_word_offset'], run['start'], run['count']) for run in runs)
    header = '''// Generated from native water and sand-edge phases; private Dewford bank only.
extern const struct Tileset gTileset_JourneyDewfordHarbor;
static const u16 sJourneyDewfordShoreFrames[] = INCBIN_U16("%s");

static bool32 JourneyDewfordShoreAnimationActive(void)
{
    return gMapHeader.mapLayout->secondaryTileset == &gTileset_JourneyDewfordHarbor;
}

static void QueueJourneyDewfordShoreAnimation(u16 phase)
{
    const u16 *frame = sJourneyDewfordShoreFrames + phase * %d;
    if (!JourneyDewfordShoreAnimationActive())
        return;
%s
    // Queue the native edge in the same batch as the sea and the private
    // composites. A second global-clock read on the next local timer tick
    // can otherwise select the following phase at a VBlank phase boundary.
    AppendTilesetAnimToBuffer(gTilesetAnims_General_SandWaterEdge[phase], (u16 *)(BG_VRAM + TILE_OFFSET_4BPP(464)), 10 * TILE_SIZE_4BPP);
}

static void RefreshJourneyDewfordShoreAnimation(u16 phase)
{
    const u16 *frame = sJourneyDewfordShoreFrames + phase * %d;
    if (!JourneyDewfordShoreAnimationActive())
        return;
%s
    CpuCopy16(gTilesetAnims_General_SandWaterEdge[phase], (void *)(BG_VRAM + TILE_OFFSET_4BPP(464)), 10 * TILE_SIZE_4BPP);
}

void RefreshJourneyDewfordShoreAfterDma3Requests(void)
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
''' % (ANIMATION, word_offset, queue, word_offset, refresh)
    stage(HEADER, header)
    path = 'src/tileset_anims.c'
    text = raw(path).decode()
    assert '#include "dma3.h"' not in text
    text = text.replace('#include "main.h"', '#include "main.h"\n#include "dma3.h"')
    anchor = 'static void QueueAnimTiles_General_Water(u16 timer)\n{'
    assert text.count(anchor) == 1 and HEADER.removeprefix('src/') not in text
    text = text.replace(anchor, '#include "' + HEADER.removeprefix('src/') + '"\n\n' + anchor)
    water = '    AppendTilesetAnimToBuffer(gTilesetAnims_General_Water[i], (u16 *)(BG_VRAM + TILE_OFFSET_4BPP(432)), 30 * TILE_SIZE_4BPP);'
    assert text.count(water) == 1
    text = text.replace(water, water + '\n    QueueJourneyDewfordShoreAnimation(i);')
    sand = '    u16 i = timer % ARRAY_COUNT(gTilesetAnims_General_SandWaterEdge);'
    assert text.count(sand) == 1
    text = text.replace(sand, sand + '\n    if (JourneyDewfordShoreAnimationActive())\n        return;')
    initial = '''    if (sPrimaryTilesetAnimCallback == TilesetAnim_General)
        CpuCopy16(gTilesetAnims_General_Water[phase], (void *)(BG_VRAM + TILE_OFFSET_4BPP(432)), 30 * TILE_SIZE_4BPP);'''
    assert text.count(initial) == 1
    text = text.replace(initial, '''    if (sPrimaryTilesetAnimCallback == TilesetAnim_General)
    {
        CpuCopy16(gTilesetAnims_General_Water[phase], (void *)(BG_VRAM + TILE_OFFSET_4BPP(432)), 30 * TILE_SIZE_4BPP);
        RefreshJourneyDewfordShoreAnimation(phase);
    }''')
    # Camera connections leave their queued full secondary graphics copy
    # pending through this initializer. The VBlank hook runs one refresh only
    # after the native BG DMA queue drains, using the current global phase.
    declaration = 'static void RefreshContinuousOceanTiles(void);'
    assert text.count(declaration) == 1
    text = text.replace(declaration, declaration + '\nstatic bool32 JourneyDewfordShoreAnimationActive(void);\nstatic bool32 sJourneyDewfordShoreRefreshPending;')
    secondary = '''void InitSecondaryTilesetAnimation(void)
{
    _InitSecondaryTilesetAnimation();
}'''
    assert text.count(secondary) == 1
    text = text.replace(secondary, '''void InitSecondaryTilesetAnimation(void)
{
    _InitSecondaryTilesetAnimation();
    sJourneyDewfordShoreRefreshPending = JourneyDewfordShoreAnimationActive();
}''')
    stage(path, text)
    path = 'include/tileset_anims.h'
    text = raw(path).decode()
    declaration = 'void InitSecondaryTilesetAnimation(void);'
    assert text.count(declaration) == 1
    text = text.replace(declaration, declaration + '\nvoid RefreshJourneyDewfordShoreAfterDma3Requests(void);')
    stage(path, text)
    path = 'src/main.c'
    text = raw(path).decode()
    assert '#include "tileset_anims.h"' not in text
    text = text.replace('#include "dma3.h"', '#include "dma3.h"\n#include "tileset_anims.h"')
    dma = '    ProcessDma3Requests();'
    assert text.count(dma) == 1
    text = text.replace(dma, dma + '\n    RefreshJourneyDewfordShoreAfterDma3Requests();')
    stage(path, text)
    return dict(changed_paths=sorted(touched), native_phase_count=8,
                native_water_graphics=[432, 461], native_sand_graphics=[464, 473],
                native_sand_frame_order=[0, 1, 2, 3, 4, 5, 6, 0],
                palette_bank=9, palette_used_colors=len(required),
                shore_and_bridge_underlay_groups=groups, static_alias_splits=splits,
                animated_graphics=dynamic, dma_runs=runs,
                words_per_phase=word_offset, frame_data_sha256=hashlib.sha256(payload).hexdigest(),
                native_flag_graphics_preserved=True, bridge_foregrounds_preserved=True,
                map_blocks_attributes_events_heights_unchanged=True,
                native_global_phase_on_load_and_during_animation=True,
                native_sand_and_private_shore_queued_with_water_phase=True,
                native_private_secondary_reload_refresh=True,
                native_private_secondary_reload_after_dma_refresh=True,
                runtime_changes_restricted_to_private_dewford_bank=True)
