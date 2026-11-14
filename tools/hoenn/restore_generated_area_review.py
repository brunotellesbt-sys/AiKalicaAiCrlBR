"""Reconstruct the pinned layer-171 source without recovering the lost workspace.

This does not build a ROM or certify native tests. Existing sources must have
an intact acquisition manifest and a consecutive, hash-valid layer prefix;
partial or modified files are preserved and rejected, never overwritten.

Use the project's pinned ARM GCC/newlib toolchain (tools/unova/bootstrap.py),
binutils, numpy 2.3.5, scipy 1.16.3, and Pillow 13.0.0. Frozen generators use Pillow's
get_flattened_data API, which is unavailable in the older CI Pillow 11.3 pin.
The final source is accepted only if the historical source contracts match.
"""
import argparse
import hashlib
import importlib
import json
from pathlib import Path
import sys

from acquire_multiregion import acquire, PIN
from prepare_generated_area_review import PRIOR, LAYER
from generated_area_review_contract import PREPARED_SHA256

LAYERS = tuple(PRIOR + [LAYER])
BUILT_SHA256 = {
    'pokeemerald.gba': '52156af727381fb5b47dacf83f8f57696e05dae05c4971368310b98515eba935',
    'pokeemerald.elf': '000a4795be90877c83c4b133b3efa5234d042e8414e832d5e0e687ae4304bd46',
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _relative(name):
    path = Path(name)
    if path.is_absolute() or '..' in path.parts or not path.parts:
        raise ValueError(f'Unsafe manifest path: {name!r}')
    return path


def verify_prefix(source, *, complete=False):
    """Check every acquired/layered input before resuming any preparation."""
    source = Path(source)
    acquired = json.loads((source / '.source-acquired.json').read_text())
    if acquired['commit'] != PIN or acquired['repository'] != 'eonlynx/pokecrossroads':
        raise ValueError('Unexpected acquired source revision')
    expected = dict(acquired['sha256'])
    markers = {}
    gap = False
    for name in LAYERS:
        marker = source / ('.journey-' + name)
        if not marker.exists():
            gap = True
            continue
        if gap:
            raise ValueError('Non-consecutive layer prefix: ' + name)
        record = json.loads(marker.read_text())
        expected.update(record['prepared_sha256'])
        markers[name] = digest(marker)
    unknown = {p.name.removeprefix('.journey-')
               for p in source.glob('.journey-*')} - set(LAYERS)
    if unknown:
        raise ValueError('Source contains later/unknown layers: ' + ', '.join(sorted(unknown)))
    if complete and len(markers) != len(LAYERS):
        raise ValueError(f'Incomplete layer prefix: {len(markers)}/{len(LAYERS)}')
    for name, wanted in sorted(expected.items()):
        path = source / _relative(name)
        if not path.is_file() or digest(path) != wanted:
            raise ValueError('Preserved incomplete/modified source input: ' + name)
    if len(markers) == len(LAYERS):
        final = json.loads((source / ('.journey-' + LAYER)).read_text())
        if final['prepared_sha256'] != PREPARED_SHA256:
            raise ValueError('Reconstructed layer171 differs from its frozen source contract')
    identity = hashlib.sha256(json.dumps(expected, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return dict(source_commit=PIN, layers=len(markers), source_files_checked=len(expected),
                source_manifest_sha256=identity, layer_marker_sha256=markers)


def restore(source, *, acquire_missing=False, verify_only=False, verify_built=False):
    source = Path(source).resolve()
    if not source.exists():
        if not acquire_missing or verify_only:
            raise ValueError('Source is absent; use --acquire for a new directory')
        acquire(source)
    # Acquisition itself refuses an existing directory. A failed acquisition
    # without its final manifest is retained for inspection on the next call.
    before = verify_prefix(source)
    if not verify_only:
        for i, name in enumerate(LAYERS[before['layers']:], before['layers'] + 1):
            print(f'Preparing {i}/{len(LAYERS)}: {name}', file=sys.stderr, flush=True)
            module = 'prepare_crossing' if name == 'hoenn-crossing' else 'prepare_' + name.replace('-', '_')
            importlib.import_module(module).prepare(source)
    result = verify_prefix(source, complete=True)
    result.update(kind='reconstructed-generated-area-review-source', source=str(source),
                  lost_workspace_recovered=False, compiled_rom=False,
                  native_validation=False, historical_source_contract_matches=True)
    if verify_built:
        for name, wanted in BUILT_SHA256.items():
            if digest(source / name) != wanted:
                raise ValueError('Rebuilt artifact differs from historical layer171: ' + name)
        result['historical_built_artifact_sha256'] = dict(BUILT_SHA256)
        result['compiled_rom'] = True
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--acquire', action='store_true', help='Download pinned upstream only when source is absent')
    parser.add_argument('--verify-only', action='store_true', help='Read source and reject incomplete prefixes without preparing')
    parser.add_argument('--verify-built', action='store_true', help='Also require the original171 ROM and ELF hashes')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    report = restore(args.source, acquire_missing=args.acquire,
                     verify_only=args.verify_only, verify_built=args.verify_built)
    raw = json.dumps(report, indent=2) + '\n'
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(raw)
    print(raw, end='')
