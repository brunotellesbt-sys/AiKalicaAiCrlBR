"""Audit the whole reconstructed source before any ROM can be published.

The graph reads actual staged terrain, reciprocal connections, native banks,
warps and compiled-C Dive tables. Unknown bank compatibility stays pending.
This source proof never certifies emulator travel, artwork or release ROMs.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path

from atlas_surf_layout_requirements import build_requirements
from atlas_surf_overlay import OverlaySource
from atlas_surf_reachability import audit
from prepare_atlas_surf_layout import EVIDENCE,compose


def validate(layer,metadata,*,bank_pairs=(),max_states=2000000,return_graph=False):
    source=OverlaySource(layer)
    parent=json.loads((EVIDENCE/'parent-inventory.json').read_bytes())
    native=json.loads(gzip.decompress((EVIDENCE/'native-ownership-source.json.gz').read_bytes()))
    requirements=build_requirements(source,metadata,parent,native,bank_pairs=bank_pairs)
    report,graph=audit(source,plan=metadata['geometry_plan'],requirements=requirements,
                       max_states=max_states,return_graph=True)
    report.update(schema='atlas-whole-layout-source-validation/v1',
                  obligation_inventory=requirements,
                  prepared_sha256={p:hashlib.sha256(raw).hexdigest() for p,raw in layer.outputs.items()},
                  global_terrain_proven=report['passed'],native_ROM_proven=False,
                  release_eligible=False,pending_release_obligations=metadata['pending_obligations'])
    return (report,graph) if return_graph else report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--bank-evidence',type=Path)
    args=parser.parse_args()
    layer,metadata=compose(args.source)
    pairs=[]
    if args.bank_evidence:
        proof=json.loads(args.bank_evidence.read_bytes())
        pairs=proof['authenticated_bank_pairs']
        # A pair list from another candidate is not evidence for these bytes.
        expected={p:hashlib.sha256(raw).hexdigest() for p,raw in layer.outputs.items()}
        if proof.get('prepared_sha256')!=expected:
            raise ValueError('Bank compatibility evidence belongs to a different staged candidate')
    report=validate(layer,metadata,bank_pairs=pairs)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=report['passed'],physical_maps=report['physical_maps'],
        generated_water_sccs=report['generated_water_sccs'],metrics=report['metrics'],
        errors=dict(Counter(r['kind'] for r in report['errors'])),
        pending=dict(Counter(r['kind'] for r in report['pending']))),indent=2))
    raise SystemExit(0 if report['passed'] else 2)
