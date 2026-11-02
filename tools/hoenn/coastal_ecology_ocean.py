"""Use one ocean palette beneath complete Sevii shores and offshore rocks.

The previous integration normalized static fast-water graphics but retained
palette 6 on existing animated water. Its altered colors make the same wave
frame look like a second checker-pattern sea beside a newly built terminal.
Only lower-layer water words in the seven private Sevii tables are eligible.
"""
from pathlib import Path
import hashlib
import json
import struct
from coastal_ecology_sevii_aliases import TARGET_MAPS as NATIVE_TARGET_MAPS

BANKS = (
    'gTileset_JourneySeviiSea', 'gTileset_JourneySeviiSea123',
    'gTileset_JourneySeviiIntegrated123', 'gTileset_JourneySeviiSea45',
    'gTileset_JourneySeviiIntegrated45', 'gTileset_JourneySeviiSea67',
    'gTileset_JourneySeviiIntegrated67',
)


def normalize(blob):
    """Preserve tile number, flips, upper layers and every non-water word."""
    values = list(struct.unpack('<' + 'H' * (len(blob) // 2), blob))
    changes = []
    for i, word in enumerate(values):
        if i % 8 < 4 and word & 1023 in (454, 455) and word >> 12 == 6:
            values[i] = (word & 0xFFF) | 0x4000
            changes.append(dict(word_index=i, before=word, after=values[i]))
    return struct.pack('<' + 'H' * len(values), *values), changes


def repair(layer):
    source = Path(layer.source)
    metadata = json.loads((source / '.journey-sevii-integrated-piers').read_text())['ocean_seams']
    tables = {row['tileset']: row for row in metadata['tables']}
    assert set(tables) == set(BANKS)
    results = []
    for symbol in BANKS:
        previous = tables[symbol]
        path = previous['path']
        before = layer.outputs.get(path, (source / path).read_bytes())
        after, changes = normalize(before)
        assert changes, ('Expected native palette-6 water underlays', symbol)
        assert len(before) == len(after)
        assert all(row['before'] ^ row['after'] == 0x2000 for row in changes)
        layer.stage(path, after)
        results.append(dict(tileset=symbol, metatile_symbol=previous['metatile_symbol'],
            path=path, before_sha256=hashlib.sha256(before).hexdigest(),
            after_sha256=hashlib.sha256(after).hexdigest(), words_changed=changes,
            lower_water_words_changed=len(changes)))
    return dict(kind='coastal-ecology-ocean-palette', tables=results,
        target_maps=sorted(set(metadata['target_maps']) | set(NATIVE_TARGET_MAPS)),
        water_graphics=[454,455], original_palette=6, ocean_palette=4,
        lower_water_words_changed=sum(r['lower_water_words_changed'] for r in results),
        tile_ids_flip_bits_upper_object_layers_and_attributes_preserved=True,
        map_geometry_events_and_shared_native_banks_preserved=True,
        animation_frames_callbacks_and_phase_clock_preserved=True)
