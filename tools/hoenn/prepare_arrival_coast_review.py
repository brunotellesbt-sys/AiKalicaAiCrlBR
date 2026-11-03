"""Repair arrival destinations and newly exposed coastal objects over layer166."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

from candidate_layer import Layer
from prepare_coastal_ecology import PRIOR as PREVIOUS_LAYERS, LAYER as PREVIOUS
from arrival_coast_review_contract import PARENT_ROM_SHA256, PARENT_ELF_SHA256, PARENT_MARKER_SHA256

LAYER = 'arrival-coast-review'
PRIOR = PREVIOUS_LAYERS + [PREVIOUS]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_parent(source):
    source = Path(source)
    for name, expected in [('pokeemerald.gba', PARENT_ROM_SHA256),
                           ('pokeemerald.elf', PARENT_ELF_SHA256),
                           ('.journey-coastal-ecology', PARENT_MARKER_SHA256)]:
        assert digest(source/name) == expected, ('Frozen layer166 parent changed', name)
    expected = Layer(source, LAYER, PRIOR).expected
    for name, value in expected.items():
        assert digest(source/name) == value, ('Parent input changed', name)
    assert len(PRIOR) == 166
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
    from arrival_coast_water import repair as water
    from arrival_coast_cliffs import repair as cliffs
    from arrival_coast_forest import repair as forest
    from arrival_coast_limits import repair as limits
    from coastal_followup_pier import repair as pier
    from coastal_followup_arrivals import repair as arrivals
    return dict(water=water(layer), cliffs=cliffs(layer), forest=forest(layer), limits=limits(layer), pier=pier(layer), arrivals=arrivals(layer),
                parent_rom_sha256=PARENT_ROM_SHA256,
                atlas_pixels_wild_tables_and_unrelated_campaign_source_unchanged=True,
                review_mode_encounters_and_approaches_remain_disabled=True)


def prepare(source):
    layer = Layer(source, LAYER, PRIOR)
    if old := layer.existing():
        return old
    assert digest(Path(source)/'.journey-coastal-ecology') == PARENT_MARKER_SHA256
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
