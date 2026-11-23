"""Export completed native runs losslessly; never change public ROMs or seals."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from verify_atlas_functional_release import ROOT,load,sha


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    raw=json.dumps(value,sort_keys=True,indent=2).encode()+b'\n'
    path.write_bytes(gzip.compress(raw,mtime=0) if path.suffix=='.gz' else raw)


def export(native,frozen,ecology,output):
    native,frozen,ecology,output=(Path(p).resolve() for p in (native,frozen,ecology,output))
    assert not output.exists(),'Preserve existing reviewed evidence'
    output.mkdir(parents=True)
    f=load(frozen);meta=load(Path(f['source'])/'.journey-atlas-surf-layout')
    write(output/'freeze.json.gz',f);write(output/'metadata.json.gz',meta)
    logical={}
    def copy_tree(source,dest):
        for p in sorted(source.rglob('*')):
            if not p.is_file() or p.name.startswith('partial-') or '.pickle' in p.name or 'failure' in p.name:continue
            assert not p.is_symlink(),'Unexpected native attachment symlink'
            raw=p.read_bytes();target=dest/p.relative_to(source)
            if p.suffix=='.json' and len(raw)>250000:
                target=target.with_suffix('.json.gz')
                logical[(dest/p.relative_to(source)).relative_to(output).as_posix()]=dict(
                    file=target.relative_to(output).as_posix(),decompressed_sha256=hashlib.sha256(raw).hexdigest())
                raw=gzip.compress(raw,mtime=0)
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    folders=['chambers','exteriors','rocks103','trainers','coasts','dives','legacy','neighbor','captures',
             'captain','three-port','seven-ports','land-habitats-complete','compiled-source']
    for folder in folders:
        assert (native/folder).is_dir(),('Missing current native obligation',folder)
        copy_tree(native/folder,output/folder)
    for ed in f['editions']:
        name=ed['edition'];base=native/'editions'/name
        for kind in ('rules','trainer','water-wild'):
            source=base/kind
            if kind=='rules' and (base/'rules-complete').is_dir():source=base/'rules-complete'
            assert source.is_dir(),('Missing edition obligation',name,kind)
            copy_tree(source,output/'editions'/name/kind)
    copy_tree(ecology,output/'ecology')
    def report_name(path):
        p=output/path
        return p.with_suffix('.json.gz').relative_to(output).as_posix() if not p.exists() else path
    for folder,stem in [('chambers','legendary-chambers'),('exteriors','large-cave-exteriors')]:
        name=report_name(folder+'/'+stem+'-native.json');r=load(output/name)
        assert r['passed']
        write(output/folder/(stem+'-native-matrix.json'),dict(passed=True,artifact_sha256=r['artifact_sha256'],
            components=[dict(report=Path(name).name,sha256=sha(output/name))]))
    # Compact files retain the original report's decompressed bytes exactly.
    # This index resolves original JSON references without relabeling a proof.
    write(output/'logical-JSON-paths.json',logical)
    files={p.relative_to(output).as_posix():sha(p) for p in output.rglob('*') if p.is_file()}
    write(output/'evidence-files.json',files)
    print('Exported current evidence files:',len(files),'index',sha(output/'evidence-files.json'))
    return files


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('native','frozen','ecology','output'):p.add_argument('--'+name,type=Path,required=True)
    export(**vars(p.parse_args()))
