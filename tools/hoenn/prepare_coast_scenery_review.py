"""Complete coastal scenery and coherent diagonal cameras over layer 169."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil

from candidate_layer import Layer
from prepare_sevii_route_boundaries import (PRIOR as PREVIOUS_LAYERS, LAYER as PREVIOUS,
                                           GENERATED_INPUTS as PREVIOUS_GENERATED_INPUTS)
from coast_scenery_review_contract import PARENT_ROM_SHA256, PARENT_ELF_SHA256, PARENT_MARKER_SHA256

LAYER = 'coast-scenery-review'
PRIOR = PREVIOUS_LAYERS + [PREVIOUS]
GENERATED_INPUTS = list(PREVIOUS_GENERATED_INPUTS)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_parent(source):
    source = Path(source)
    for name, expected in [('pokeemerald.gba', PARENT_ROM_SHA256),
                           ('pokeemerald.elf', PARENT_ELF_SHA256),
                           ('.journey-sevii-route-boundaries', PARENT_MARKER_SHA256)]:
        assert digest(source/name) == expected, ('Frozen layer169 parent changed', name)
    expected = Layer(source, LAYER, PRIOR).expected
    for name, value in expected.items():
        assert digest(source/name) == value, ('Parent input changed', name)
    assert len(PRIOR) == 169
    return expected


def clone_parent(source, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    assert source != destination and not destination.is_relative_to(source)
    assert not destination.exists(), ('Refusing to overwrite candidate', destination)
    expected = verify_parent(source)
    def copy_input(before, after):
        relative = Path(before).relative_to(source)
        if relative.parts[0] in {'build', 'tools', 'libagbsyscall'} or relative.suffix in {'.gba', '.elf', '.map', '.sym', '.o', '.d', '.a'}:
            return shutil.copy2(before, after)
        os.link(before, after)
        return after
    shutil.copytree(source, destination, symlinks=True, copy_function=copy_input)
    detach_generated_inputs(destination)
    for name, value in expected.items():
        assert digest(destination/name) == value, name
    verify_parent(source)


def detach_generated_inputs(source):
    """Give make-generated headers private inodes before a candidate build."""
    source = Path(source)
    for name in GENERATED_INPUTS:
        path = source/name
        if path.is_file() and not path.is_symlink():
            pending = path.with_name(path.name+'.journey-private')
            shutil.copy2(path, pending)
            pending.replace(path)


def stage_repairs(layer):
    from sevii_complete_scenery import repair as scenery
    from marine_corner_coherence import repair as corners
    return dict(scenery=scenery(layer), corners=corners(layer),
                parent_rom_sha256=PARENT_ROM_SHA256,
                campaign_and_save_abi_unchanged=True,
                native_review_mode_suppression_preserved=True)


def prepare(source):
    layer = Layer(source, LAYER, PRIOR)
    if old := layer.existing():
        return old
    assert digest(Path(source)/'.journey-sevii-route-boundaries') == PARENT_MARKER_SHA256
    return json.loads(json.dumps(layer.finish(**stage_repairs(layer))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--clone-from', type=Path)
    parser.add_argument('--clone-only', action='store_true')
    args = parser.parse_args()
    if args.clone_from:
        clone_parent(args.clone_from, args.source)
    if not args.clone_only:
        print(json.dumps(prepare(args.source), indent=2))
