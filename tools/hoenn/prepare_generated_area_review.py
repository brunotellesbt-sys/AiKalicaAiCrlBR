"""Review generated areas and extend native diagonal cameras over layer 170."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil

from candidate_layer import Layer
from prepare_coast_scenery_review import (PRIOR as PREVIOUS_LAYERS, LAYER as PREVIOUS,
                                           GENERATED_INPUTS as PREVIOUS_GENERATED_INPUTS)
from generated_area_review_contract import PARENT_ROM_SHA256, PARENT_ELF_SHA256, PARENT_MARKER_SHA256

LAYER = 'generated-area-review'
PRIOR = PREVIOUS_LAYERS + [PREVIOUS]
GENERATED_INPUTS = list(PREVIOUS_GENERATED_INPUTS)


def generated_inputs(source):
    # A new map rewrites map_groups.h, which invalidates every derived map
    # header. All those outputs must be private, including through a compact
    # parent's directory symlinks; otherwise make would edit older snapshots.
    return sorted(set(GENERATED_INPUTS) | {
        'src/data/heal_locations.json', 'src/data/wild_encounters.h',
        *[f'data/maps/{path.parent.name}/{kind}.inc'
          for path in (Path(source)/'data/maps').glob('*/map.json')
          for kind in ('header', 'events', 'connections')]})


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_parent(source):
    source = Path(source)
    for name, expected in [('pokeemerald.gba', PARENT_ROM_SHA256),
                           ('pokeemerald.elf', PARENT_ELF_SHA256),
                           ('.journey-coast-scenery-review', PARENT_MARKER_SHA256)]:
        assert digest(source/name) == expected, ('Frozen layer170 parent changed', name)
    expected = Layer(source, LAYER, PRIOR).expected
    for name, value in expected.items():
        assert digest(source/name) == value, ('Parent input changed', name)
    assert len(PRIOR) == 170
    return expected


def clone_parent(source, destination, compact=False):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    assert source != destination and not destination.is_relative_to(source)
    assert not destination.exists(), ('Refusing to overwrite candidate', destination)
    expected = verify_parent(source)
    if compact:
        from compact_source_snapshot import clone
        preview = Layer(source, LAYER, PRIOR)
        stage_repairs(preview)
        clone(source, destination, set(preview.outputs) | set(generated_inputs(source)),
              cache=source.parent/'coast-scenery-review-build-cache.tar.gz')
        verify_parent(source)
        return
    def copy_input(before, after):
        relative = Path(before).relative_to(source)
        if relative.parts[0] in {'build', 'tools', 'libagbsyscall'} or relative.suffix in {'.gba', '.elf', '.map', '.sym', '.o', '.d', '.a'}:
            return shutil.copy2(before, after)
        os.link(before, after)
        return after
    # The parent may itself be compact: materialize its directory links for a
    # fully writable clone, then detach every generated output below.
    shutil.copytree(source, destination, symlinks=False, copy_function=copy_input)
    detach_generated_inputs(destination)
    for name, value in expected.items():
        assert digest(destination/name) == value, name
    verify_parent(source)


def detach_generated_inputs(source):
    """Give make-generated headers private inodes before a candidate build."""
    source = Path(source)
    for name in generated_inputs(source):
        path = source/name
        if path.is_file() and not path.is_symlink():
            pending = path.with_name(path.name+'.journey-private')
            shutil.copy2(path, pending)
            pending.replace(path)


def stage_repairs(layer):
    from generated_coast_cameras import repair as coast
    from generated_cave_portals import repair as caves
    from port_boundary_scenery import repair as ports
    from one_south_surf_link import repair as south
    return dict(coast=coast(layer), caves=caves(layer),
                ports=ports(layer), one_south=south(layer),
                parent_rom_sha256=PARENT_ROM_SHA256,
                campaign_and_save_abi_unchanged=True,
                native_review_mode_suppression_preserved=True)


def prepare(source):
    layer = Layer(source, LAYER, PRIOR)
    if old := layer.existing():
        return old
    assert digest(Path(source)/'.journey-coast-scenery-review') == PARENT_MARKER_SHA256
    return json.loads(json.dumps(layer.finish(**stage_repairs(layer))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--clone-from', type=Path)
    parser.add_argument('--clone-only', action='store_true')
    parser.add_argument('--compact', action='store_true', help='Reuse frozen directories while materializing every reviewed/generated output')
    args = parser.parse_args()
    if args.clone_from:
        clone_parent(args.clone_from, args.source, compact=args.compact)
    if not args.clone_only:
        print(json.dumps(prepare(args.source), indent=2))
