"""Create tiny source views sharing inputs but loading the actual variant ROM."""
import argparse,json
from pathlib import Path


def views(source,variants,output):
    source=Path(source).resolve();variants=Path(variants).resolve();output=Path(output).resolve()
    manifest=json.loads((variants/'versions.json').read_text());rows=[]
    for row in manifest['variants']:
        name=row['file'].removeprefix('Pokemon-Journey-').removesuffix('.gba')
        target=output/name;target.mkdir(parents=True,exist_ok=True)
        for entry in source.iterdir():
            if entry.name in ['pokeemerald.gba','build','.git']:continue
            dest=target/entry.name
            if not dest.exists():dest.symlink_to(entry,target_is_directory=entry.is_dir())
        dest=target/'pokeemerald.gba'
        if not dest.exists():dest.symlink_to(variants/row['file'])
        rows.append(dict(source=str(target),**row))
    return rows


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--variants',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();print(json.dumps(views(a.source,a.variants,a.output),indent=2))
