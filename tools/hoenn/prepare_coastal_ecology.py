"""Add coherent aquatic habitats and reviewed tile repairs over layer 165."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

from candidate_layer import Layer
from prepare_generated_world_audit import PRIOR as PREVIOUS_LAYERS, LAYER as PREVIOUS
from coastal_ecology_contract import PARENT_ROM_SHA256, PARENT_ELF_SHA256, PARENT_MARKER_SHA256

LAYER = 'coastal-ecology'
PRIOR = PREVIOUS_LAYERS + [PREVIOUS]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_parent(source):
    source = Path(source)
    for name, expected in [('pokeemerald.gba',PARENT_ROM_SHA256),
                           ('pokeemerald.elf',PARENT_ELF_SHA256),
                           ('.journey-generated-world-audit',PARENT_MARKER_SHA256)]:
        assert digest(source/name) == expected, ('Frozen layer-165 parent changed',name)
    expected = Layer(source,LAYER,PRIOR).expected
    for name, value in expected.items():
        assert digest(source/name) == value, ('Parent input changed',name)
    assert len(PRIOR) == 165
    return expected


def clone_parent(source, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    assert source != destination and not destination.is_relative_to(source)
    assert not destination.exists(), ('Refusing to overwrite candidate',destination)
    expected = verify_parent(source)
    shutil.copytree(source,destination,symlinks=True,copy_function=shutil.copy2)
    for name, value in expected.items():
        assert (source/name).stat().st_ino != (destination/name).stat().st_ino, name
        assert digest(destination/name) == value, name
    verify_parent(source)


def stage_repairs(layer):
    from coastal_ecology_encounters import repair as encounters
    from coastal_ecology_tiles import repair as tiles
    from coastal_ecology_piers import repair as piers
    from coastal_ecology_ocean import repair as ocean
    from coastal_ecology_cliff_rocks import repair as cliffs
    from coastal_ecology_sevii_aliases import repair as sevii_aliases
    from coastal_ecology_kindle_cliff import repair as kindle
    from coastal_ecology_pallet_shore import repair as pallet_shore
    from coastal_ecology_legacy_surf import repair as legacy_surf
    from coastal_ecology_pier_priority import repair as pier_priority
    from coastal_ecology_kanto_sea import repair as kanto_sea
    return dict(encounters=encounters(layer), tiles=tiles(layer), piers=piers(layer),
                sevii_aliases=sevii_aliases(layer), ocean=ocean(layer), cliffs=cliffs(layer),
                kindle_cliff=kindle(layer), pallet_shore=pallet_shore(layer),
                legacy_surf=legacy_surf(layer), pier_priority=pier_priority(layer),
                kanto_sea=kanto_sea(layer),
                parent_rom_sha256=PARENT_ROM_SHA256,
                review_mode_random_encounters_and_approaches_remain_disabled=True)


def prepare(source):
    layer = Layer(source,LAYER,PRIOR)
    if old := layer.existing():
        return old
    assert digest(Path(source)/'.journey-generated-world-audit') == PARENT_MARKER_SHA256
    # The persisted contract is JSON. Normalize integer metadata keys on the
    # first return too, so an independent replay and a subsequent read have
    # precisely the same value as the marker written to disk.
    return json.loads(json.dumps(layer.finish(**stage_repairs(layer))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--clone-from',type=Path)
    parser.add_argument('--clone-only',action='store_true')
    args = parser.parse_args()
    if args.clone_from:
        clone_parent(args.clone_from,args.source)
    if not args.clone_only:
        print(json.dumps(prepare(args.source),indent=2))
