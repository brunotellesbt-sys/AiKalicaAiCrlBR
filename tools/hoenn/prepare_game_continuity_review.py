"""Repair confirmed campaign and coastal camera regressions over layer 167."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

from candidate_layer import Layer
from prepare_arrival_coast_review import PRIOR as PREVIOUS_LAYERS, LAYER as PREVIOUS
from game_continuity_review_contract import PARENT_ROM_SHA256, PARENT_ELF_SHA256, PARENT_MARKER_SHA256

LAYER = 'game-continuity-review'
PRIOR = PREVIOUS_LAYERS + [PREVIOUS]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_parent(source):
    source = Path(source)
    for name, expected in [('pokeemerald.gba', PARENT_ROM_SHA256),
                           ('pokeemerald.elf', PARENT_ELF_SHA256),
                           ('.journey-arrival-coast-review', PARENT_MARKER_SHA256)]:
        assert digest(source/name) == expected, ('Frozen layer167 parent changed', name)
    expected = Layer(source, LAYER, PRIOR).expected
    for name, value in expected.items():
        assert digest(source/name) == value, ('Parent input changed', name)
    assert len(PRIOR) == 167
    return expected


def clone_parent(source, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    assert source != destination and not destination.is_relative_to(source)
    assert not destination.exists(), ('Refusing to overwrite candidate', destination)
    expected = verify_parent(source)
    shutil.copytree(source, destination, symlinks=True, copy_function=shutil.copy2)
    for name, value in expected.items():
        assert (source/name).stat().st_ino != (destination/name).stat().st_ino, name
        assert digest(destination/name) == value, name
    verify_parent(source)


def stage_repairs(layer):
    from campaign_continuity_review import repair as campaign
    from game_continuity_coasts import repair as coasts
    return dict(campaign=campaign(layer), coasts=coasts(layer),
                parent_rom_sha256=PARENT_ROM_SHA256,
                previous_arrival_coordinates_and_save_abi_unchanged=True,
                native_review_mode_suppression_preserved=True)


def prepare(source):
    layer = Layer(source, LAYER, PRIOR)
    if old := layer.existing():
        return old
    assert digest(Path(source)/'.journey-arrival-coast-review') == PARENT_MARKER_SHA256
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
