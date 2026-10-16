"""Replay the coastal and atlas overlays independently from their verified inputs."""
import argparse,hashlib,importlib,json,tempfile
from pathlib import Path
from prepare_lavender_harbor import PRIOR,LAYER
from prepare_sevii_surf_connections import PRIOR as BASE

def reproduce(source,inputs,output):
    source=Path(source).resolve();inputs=[Path(p) for p in inputs];layers=PRIOR+[LAYER];delta=layers[len(BASE):];assert len(inputs)==len(delta)
    reports=[json.loads((source/('.journey-'+n)).read_text()) for n in delta];final={};originals={}
    for r,snapshot in zip(reports,inputs):
        for p,h in r['original_sha256'].items():
            assert hashlib.sha256((snapshot/p).read_bytes()).hexdigest()==h,p
        for p in r['prepared_sha256']:
            if p not in final:originals[p]=(snapshot/p) if p in r['original_sha256'] else None
        final.update(r['prepared_sha256'])
    targets={Path(p) for p in final};excluded={Path('.journey-'+n) for n in delta}
    with tempfile.TemporaryDirectory(prefix='sevii-replay-',dir=source.parent) as directory:
        dest=Path(directory)
        def clone(relative):
            origin=source/relative;copy=dest/relative
            if relative in excluded:return
            if relative in targets:
                if originals[str(relative)] is not None:copy.write_bytes(originals[str(relative)].read_bytes())
                return
            if any(relative in target.parents for target in targets):
                copy.mkdir(exist_ok=True)
                for child in origin.iterdir():clone(child.relative_to(source))
            else:copy.symlink_to(origin,target_is_directory=origin.is_dir())
        for child in source.iterdir():clone(child.relative_to(source))
        for n in delta:importlib.import_module('prepare_'+n.replace('-','_')).prepare(dest)
        assert all(hashlib.sha256((dest/p).read_bytes()).hexdigest()==h for p,h in final.items())
        last=importlib.import_module('prepare_'+delta[-1].replace('-','_'));last.prepare(dest)
    proof=dict(passed=True,layers=layers,original_inputs_verified=True,idempotent=True,reproduced_layers=delta,
               byte_identical_outputs=sorted(final),differences=[])
    Path(output).parent.mkdir(parents=True,exist_ok=True);Path(output).write_text(json.dumps(proof,indent=2)+'\n');print('Independent Sevii replay passed:',len(final),'outputs')
    return proof

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--original-inputs',type=Path,nargs="+",required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();reproduce(a.source,a.original_inputs,a.output)
