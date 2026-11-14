"""Freeze a read-only inventory of revision171's replacement scope and POIs."""
import argparse
import hashlib
import json
from pathlib import Path

from atlas_surf_source import Source
from atlas_surf_coasts import inventory as coasts
from atlas_surf_adapters import inventory as adapters
from atlas_surf_pois import inventory as pois
from atlas_surf_truth import decode_atlas
from restore_generated_area_review import verify_prefix


def inventory(source):
    source = Path(source).resolve()
    parent = verify_prefix(source, complete=True)
    inputs = Source(source)
    coast = coasts(inputs)
    adapter = adapters(inputs, coast)
    poi = pois(inputs, coast)
    art = decode_atlas(inputs.read('src/data/journey_world_map.h').decode())
    before = dict(inputs.inputs)
    inputs.assert_unchanged()
    if parent != verify_prefix(source, complete=True):
        raise ValueError('Parent changed during the planning inventory')
    return dict(schema='atlas-parent-inventory/v1', kind='atlas-parent-planning-inventory',
                parent=parent, art_sha256=dict(art.array_sha256),
                counts=dict(retired_maps=len(coast['retired_maps']),
                            coast_interfaces=len(coast['native_interfaces']),
                            adapter_components=len(adapter['adapters']),
                            native_hosts=len(adapter['native_hosts']),
                            height_compatible_adapter_components=adapter['currently_height_compatible_components'],
                            surface_caves=len(poi['surface_caves']), dive_sites=len(poi['dive_sites']),
                            integrated_ports=len(poi['integrated_ports'])),
                coasts=coast, adapters=adapter, pois=poi,
                input_sha256=before,
                input_manifest_sha256=hashlib.sha256(json.dumps(before, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
                source_unchanged=True, new_map_destinations_assigned=False,
                replacement_source_prepared=False, global_reachability_proven=False,
                native_validated=False, final_release_validated=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = inventory(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(report, indent=2)+'\n'
    args.output.write_text(raw)
    print(json.dumps(dict(counts=report['counts'], report_sha256=hashlib.sha256(raw.encode()).hexdigest(),
                          final_release_validated=False), indent=2))
