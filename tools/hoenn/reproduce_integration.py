"""Recreate candidate layers from verified upstream inputs in a separate tree."""
import argparse,hashlib,importlib,json,os,tarfile,urllib.request
from pathlib import Path
from prepare_modern_field_moves import PRIOR,LAYER
from prepare_crossing import PIN


def reproduce(reference,output):
    reference=Path(reference).resolve();output=Path(output).resolve()
    output.mkdir(parents=True,exist_ok=False)
    acquired=json.loads((reference/'.source-acquired.json').read_text())
    assert acquired['commit']==PIN
    layers=PRIOR+[LAYER]
    if (reference/'.journey-dewford-competitive-shop').exists():
        from prepare_dewford_competitive_shop import PRIOR as shop_prior,LAYER as shop_layer
        layers=shop_prior+[shop_layer]
    elif (reference/'.journey-surf-review').exists():
        from prepare_surf_review import PRIOR as review_prior,LAYER as review_layer
        layers=review_prior+[review_layer]
    missing=set()
    base=reference.parent/'hoenn-multiregion-src'
    affected=set()
    for name in layers:
        affected.update(json.loads((reference/('.journey-'+name)).read_text())['prepared_sha256'])
    for name,wanted in acquired['sha256'].items():
        destination=output/name;destination.parent.mkdir(parents=True,exist_ok=True)
        candidates=[reference/name,base/name]
        for candidate in candidates:
            if candidate.is_file() and hashlib.sha256(candidate.read_bytes()).hexdigest()==wanted:
                # Share verified, unmodified image/audio inputs to conserve
                # inodes. Every mutable input and every code file is copied.
                if name not in affected and name.startswith(('graphics/','sound/')):
                    os.link(candidate,destination)
                else:
                    destination.write_bytes(candidate.read_bytes());destination.chmod(candidate.stat().st_mode&0o777)
                break
        else:missing.add(name)
    if missing:
        url='https://codeload.github.com/eonlynx/pokecrossroads/tar.gz/'+PIN
        with urllib.request.urlopen(url,timeout=60) as response,tarfile.open(fileobj=response,mode='r|gz') as archive:
            for member in archive:
                if not member.isfile() or '/' not in member.name:continue
                name=member.name.split('/',1)[1]
                if name not in missing:continue
                raw=archive.extractfile(member).read()
                assert hashlib.sha256(raw).hexdigest()==acquired['sha256'][name],name
                (output/name).write_bytes(raw);(output/name).chmod(member.mode&0o777);missing.remove(name)
        assert not missing,sorted(missing)
    (output/'.source-acquired.json').write_text(json.dumps(acquired,indent=2)+'\n')
    verified=[]
    for name in layers:
        module='prepare_crossing' if name=='hoenn-crossing' else 'prepare_'+name.replace('-','_')
        report=importlib.import_module(module).prepare(output)
        verified.append(name)
        print('Reproduced',len(verified),name,flush=True)
    expected={}
    for name in verified:expected.update(json.loads((reference/('.journey-'+name)).read_text())['prepared_sha256'])
    differences=[name for name,wanted in expected.items() if hashlib.sha256((output/name).read_bytes()).hexdigest()!=wanted]
    result=dict(passed=not differences,upstream_files_verified=len(acquired['sha256']),layers=verified,
                prepared_files_compared=len(expected),differences=differences)
    (output/'.integration-reproduction.json').write_text(json.dumps(result,indent=2)+'\n')
    assert not differences,differences
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--reference',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=reproduce(a.reference,a.output);print('Clean reproduction passed:',len(r['layers']),'layers')
