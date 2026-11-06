"""Repair Sevii route boundaries and pretransition camera objects over layer 168."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil

from candidate_layer import Layer
from prepare_game_continuity_review import PRIOR as PREVIOUS_LAYERS, LAYER as PREVIOUS
from sevii_route_boundaries_contract import PARENT_ROM_SHA256, PARENT_ELF_SHA256, PARENT_MARKER_SHA256

LAYER = 'sevii-route-boundaries'
PRIOR = PREVIOUS_LAYERS + [PREVIOUS]
GENERATED_INPUTS = [
    'data/layouts/layouts.inc', 'data/layouts/layouts_table.inc',
    'include/constants/map_groups.h', 'include/constants/layouts.h',
    'include/constants/map_event_ids.h', 'src/data/map_group_count.h',
    'data/maps/connections.inc', 'data/maps/groups.inc',
    'data/maps/events.inc', 'data/maps/headers.inc', '.map_version',
    *[f'data/maps/{name}/{kind}.inc'
      for name in ('OneIsland_Frlg', 'OneIsland_TreasureBeach_Frlg', 'JourneySurfLink05000')
      for kind in ('header', 'events', 'connections')],
]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_parent(source):
    source = Path(source)
    for name, expected in [('pokeemerald.gba', PARENT_ROM_SHA256),
                           ('pokeemerald.elf', PARENT_ELF_SHA256),
                           ('.journey-game-continuity-review', PARENT_MARKER_SHA256)]:
        assert digest(source/name) == expected, ('Frozen layer168 parent changed', name)
    expected = Layer(source, LAYER, PRIOR).expected
    for name, value in expected.items():
        assert digest(source/name) == value, ('Parent input changed', name)
    assert len(PRIOR) == 168
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
    from sevii_boundary_camera import repair as camera
    from sevii_route_boundaries import repair as boundaries
    return dict(camera=camera(layer), boundaries=boundaries(layer),
                parent_rom_sha256=PARENT_ROM_SHA256,
                campaign_and_save_abi_unchanged=True,
                native_review_mode_suppression_preserved=True)


def prepare(source):
    layer = Layer(source, LAYER, PRIOR)
    if old := layer.existing():
        return old
    assert digest(Path(source)/'.journey-game-continuity-review') == PARENT_MARKER_SHA256
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
