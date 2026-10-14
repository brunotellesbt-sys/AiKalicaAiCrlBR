"""Extend the verified 100-layer reconstruction and compare every candidate file.

Uses the existing independent reconstruction to avoid a second 30,000-file
checkout. Its verified baseline contract is required, not silently assumed.
"""
import argparse,hashlib,importlib,json
from pathlib import Path
from prepare_pwt_obedience import PRIOR,LAYER
def verify(reference,reconstructed):
    reference,reconstructed=Path(reference),Path(reconstructed)
    baseline=json.loads((reconstructed/'.integration-reproduction.json').read_text())
    assert baseline['passed'] and baseline['layers']==PRIOR[:100]
    expected={}
    for name in baseline['layers']:
        expected.update(json.loads((reconstructed/('.journey-'+name)).read_text())['prepared_sha256'])
    already=[]
    for name in PRIOR[100:]+[LAYER]:
        marker=reconstructed/('.journey-'+name)
        if marker.exists():
            expected.update(json.loads(marker.read_text())['prepared_sha256']);already.append(name)
        elif already and len(already)!=len(PRIOR[100:]+[LAYER]):break
    for name,digest in expected.items():assert hashlib.sha256((reconstructed/name).read_bytes()).hexdigest()==digest,name
    for name in PRIOR[100:]+[LAYER]:
        if not (reconstructed/('.journey-'+name)).exists():
            importlib.import_module('prepare_'+name.replace('-','_')).prepare(reconstructed)
    expected={}
    for name in PRIOR+[LAYER]:expected.update(json.loads((reference/('.journey-'+name)).read_text())['prepared_sha256'])
    differences=[name for name,digest in expected.items() if hashlib.sha256((reconstructed/name).read_bytes()).hexdigest()!=digest]
    assert not differences,differences
    result=dict(passed=True,layers=PRIOR+[LAYER],verified_baseline_layers=100,
        upstream_files_verified=baseline['upstream_files_verified'],prepared_files_compared=len(expected),differences=[])
    (reconstructed/'.pwt-reproduction.json').write_text(json.dumps(result,indent=2)+'\n')
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--reference',type=Path,required=True)
    p.add_argument('--reconstructed',type=Path,required=True);a=p.parse_args()
    print(json.dumps(verify(a.reference,a.reconstructed),indent=2))
