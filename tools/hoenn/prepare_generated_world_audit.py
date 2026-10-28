"""Apply complete-object and legacy-exit repairs above the frozen layer 164.

The baseline is never edited. ``--clone-from`` creates a separate source tree
with independent inodes before applying the resource-only overlay.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

from candidate_layer import Layer
from prepare_badge_story import PRIOR as PREVIOUS_LAYERS, LAYER as PREVIOUS
from generated_world_contract import (PARENT_ROM_SHA256, PARENT_ELF_SHA256,
                                      PARENT_MARKER_SHA256)

LAYER = 'generated-world-audit'
PRIOR = PREVIOUS_LAYERS + [PREVIOUS]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_parent(source):
    source = Path(source)
    for name, expected in [('pokeemerald.gba', PARENT_ROM_SHA256),
                           ('pokeemerald.elf', PARENT_ELF_SHA256),
                           ('.journey-badge-story', PARENT_MARKER_SHA256)]:
        assert digest(source / name) == expected, ('Frozen layer-164 baseline changed', name)
    expected = Layer(source, LAYER, PRIOR).expected
    for name, expected_sha in expected.items():
        assert digest(source / name) == expected_sha, ('Parent source changed', name)
    assert len(PRIOR) == 164
    return expected


def clone_parent(baseline, destination):
    """Copy rather than hard-link even generated build files and graphics."""
    baseline, destination = Path(baseline).resolve(), Path(destination).resolve()
    assert baseline != destination and not destination.is_relative_to(baseline)
    assert not destination.exists(), ('Refusing to overwrite an existing candidate', destination)
    expected = verify_parent(baseline)
    shutil.copytree(baseline, destination, symlinks=True, copy_function=shutil.copy2)
    for name, expected_sha in expected.items():
        original, copied = baseline / name, destination / name
        assert original.stat().st_ino != copied.stat().st_ino, ('Shared source inode', name)
        assert digest(copied) == expected_sha, name
    verify_parent(baseline)


def stage_repairs(layer):
    from generated_world_marine import repair as marine
    from generated_world_caves import repair as caves
    from generated_world_underwater import repair as underwater
    return dict(marine=marine(layer), caves=caves(layer), underwater=underwater(layer),
                parent_rom_sha256=PARENT_ROM_SHA256,
                atlas_pixels_and_campaign_source_unchanged=True)


def prepare(source):
    layer = Layer(source, LAYER, PRIOR)
    if old := layer.existing():
        return old
    assert digest(Path(source) / '.journey-badge-story') == PARENT_MARKER_SHA256
    return layer.finish(**stage_repairs(layer))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--clone-from', type=Path)
    options = parser.parse_args()
    if options.clone_from:
        clone_parent(options.clone_from, options.source)
    print(json.dumps(prepare(options.source), indent=2))
