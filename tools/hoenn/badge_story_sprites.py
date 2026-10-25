"""Use native indexed GBA frames at the same visible scale as the four rivals."""
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re

from PIL import Image, ImageOps
from badge_story_layer import read

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / 'tools/hoenn/data/badge-story/sprites'
ORDERS = {'eren': (0, 1, 7, 3, 4, 5, 6, 7, 8), 'luffy': tuple(range(9))}
VISIBLE_SIZE = (14, 20)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def normalize_frames(raw, name):
    """Keep palette indices; normalize whole bodies, including hats and feet."""
    original = Image.open(BytesIO(raw))
    assert original.mode == 'P' and original.size == (16, 288)
    assert max(original.tobytes()) < 16
    result = Image.new('P', original.size, 0)
    result.putpalette(original.getpalette())
    for index, donor_index in enumerate(ORDERS[name]):
        donor = original.crop((0, donor_index * 32, 16, (donor_index + 1) * 32))
        bounds = donor.getbbox()
        assert bounds is not None
        body = donor.crop(bounds)
        # Eren's last raw side step faced the opposite way. Canonical frames
        # all face west; the native animation table mirrors them for east.
        if name == 'eren' and index == 8:
            body = ImageOps.mirror(body)
        body = body.resize(VISIBLE_SIZE, Image.Resampling.NEAREST)
        bottom = 31 if index < 3 else 32
        result.paste(body, (1, index * 32 + bottom - 20))
    return result


def verify_asset(original, normalized, name):
    prepared = Image.open(BytesIO(normalized))
    expected = normalize_frames(original, name)
    assert prepared.mode == 'P' and prepared.size == (16, 288)
    assert prepared.info.get('transparency') == 0
    assert prepared.getpalette() == expected.getpalette()
    assert prepared.tobytes() == expected.tobytes(), (name, 'Changed native frame pixels')
    frames = []
    for index in range(9):
        image = prepared.crop((0, index * 32, 16, (index + 1) * 32))
        bottom = 31 if index < 3 else 32
        assert image.getbbox() == (1, bottom - 20, 15, bottom)
        frames.append(dict(frame=index, bounds=list(image.getbbox()),
                           width=14, height=20, bottom=bottom))
    return frames


def repair(layer):
    manifest = json.loads((ASSETS / 'sources.json').read_text())
    reports = []
    for name in ('eren', 'luffy'):
        original = (ASSETS / (name + '-original.png')).read_bytes()
        normalized = (ASSETS / (name + '-normalized.png')).read_bytes()
        source = manifest['source_files'][name]
        assert sha(original) == source['original_sha256']
        assert sha(normalized) == source['normalized_sha256']
        frames = verify_asset(original, normalized, name)
        for prefix in ('journey_', 'journey_pwt_'):
            path = 'graphics/object_events/pics/people/' + prefix + name + '.png'
            assert sha(read(layer, path)) == sha(original), path
            layer.stage(path, normalized)
            reports.append(dict(path=path, frames=frames, sha256=sha(normalized)))

    path = 'src/data/object_events/object_event_pic_tables.h'
    text = read(layer, path).decode()
    for name in ('EREN', 'PWTEREN'):
        expression = r'static const struct SpriteFrameImage sPicTable_Journey' + name + r'\[\] = \{[^\n]+\};'
        canonical = ('static const struct SpriteFrameImage sPicTable_Journey' + name
                     + '[] = { overworld_ascending_frames(gObjectEventPic_Journey'
                     + name + ', 2, 4) };')
        text, count = re.subn(expression, canonical, text)
        assert count == 1, name
    layer.stage(path, text)
    path = 'src/data/object_events/object_event_graphics_info.h'
    text = read(layer, path).decode()
    for name in ('EREN', 'PWTEREN'):
        expression = (r'(gObjectEventGraphicsInfo_Journey' + name
                      + r' = \{[^\n]*?\.anims\s*=\s*)sAnimTable_JourneyRivals')
        text, count = re.subn(expression, r'\1sAnimTable_Standard', text)
        assert count == 1, name
    layer.stage(path, text)
    return dict(visible_size=list(VISIBLE_SIZE), canvas=[16, 32], frames_per_actor=9,
                standard_directional_animation=True, indexed_palette_unchanged=True,
                no_frame_clipping=True, battle_portraits_unchanged=True, sprites=reports)
