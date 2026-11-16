"""Compare authenticated cave underlay with the unchanged candidate terrain.

This diagnostic never materializes sources, builds ROMs or approves a release.
It independently audits native banks and real terrain for both staged views;
fewer atlas-ink components must not be reported as fewer game-water SCCs.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path

from atlas_surf_bank_edges import audit_edges, requirement_scope
from atlas_surf_layout_requirements import build_requirements
from atlas_surf_overlay import OverlaySource
from prepare_atlas_surf_layout import EVIDENCE, compose
from restore_generated_area_review import verify_prefix
from validate_atlas_surf_layout_source import validate


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def diagnose(source, output):
    source, output = Path(source).resolve(), Path(output).resolve()
    if output == source or output.is_relative_to(source):
        raise ValueError('Diagnostic output must be outside the immutable source')
    before = verify_prefix(source, complete=True)
    parent = json.loads((EVIDENCE/'parent-inventory.json').read_bytes())
    native = json.loads(gzip.decompress((EVIDENCE/'native-ownership-source.json.gz').read_bytes()))
    views, reports, blobs = [], [], {}
    output.mkdir(parents=True, exist_ok=True)
    for label, preview in [('baseline', False), ('underlay-preview', True)]:
        layer, metadata = compose(source, preview_occluded_routes=preview)
        view = OverlaySource(layer)
        requirements = build_requirements(view, metadata, parent, native)
        banks = audit_edges(view, scope=requirement_scope(metadata, requirements))
        report = validate(layer, metadata, bank_pairs=banks['authenticated_bank_pairs'])
        for suffix, value in [('banks', banks), ('source', report)]:
            name = label+'-'+suffix+'.json.gz'
            raw = json.dumps(value, sort_keys=True, separators=(',', ':')).encode()+b'\n'
            packed = gzip.compress(raw, mtime=0)
            (output/name).write_bytes(packed)
            blobs[name] = dict(sha256=digest(packed), json_sha256=digest(raw))
        reports.append(dict(label=label, passed=report['passed'],
            generated_maps=metadata['geometry_plan']['map_count'],
            generated_water_sccs=report['generated_water_sccs'],
            generated_water_cells=report['generated_water_cells'], metrics=report['metrics'],
            banks=banks['summary'],errors=dict(Counter(r['kind'] for r in report['errors'])),
            pending=dict(Counter(r['kind'] for r in report['pending']))))
        views.append((layer, metadata))
    a, b = (pair[0].outputs for pair in views)
    changed = sorted(p for p in a.keys() | b.keys() if a.get(p) != b.get(p))
    original, candidate = (pair[1]['geometry_plan']['chunks'] for pair in views)
    identity = lambda rows: [(r['name'],r['group_index'],r['number'],r['origin'],r['width'],r['height'])
                             for r in rows]
    after = verify_prefix(source, complete=True)
    if before != after:
        raise ValueError('Immutable source changed during underlay diagnostic')
    result = dict(schema='atlas-cave-underlay-diagnostic/v1',parent_source=before,
        underlay=views[1][1]['occluded_routes_preview'],
        native_obstructions=views[1][1]['occluded_routes_native_obstructions'],
        comparisons=reports, changed_prepared_paths=changed,
        prepared_file_count=len(a), candidate_identities_and_rectangles_unchanged=identity(original)==identity(candidate),
        physical_terrain_unchanged=not changed,source_unchanged=True,
        current_ROMs_modified=False,native_ROM_validated=False,final_release_validated=False,
        files=blobs,
        conclusion='Authenticated atlas underlay alone does not repair the reserved native cave terrain or global Surf network.',
        next_steps=['Review actual native-water collars, cave approaches and their generated rectangle faces.',
                    'Repair Three Island boarding access against fixed atlas geography, preserving the complete terminal.',
                    'Prove physical source SCC, then build/freeze and run current ROM controller/save/edition tests.'])
    (output/'review.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = diagnose(args.source, args.output)
    print(json.dumps(dict(comparisons=result['comparisons'],
        changed_prepared_paths=result['changed_prepared_paths'],
        final_release_validated=False), indent=2))
