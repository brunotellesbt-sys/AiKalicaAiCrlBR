"""Preserve layer 170 and freeze five edition views of the generated area review."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import generated_area_review_contract as contract
from generated_area_review_contract import BASELINE_SHA256, PARENT_ROM_SHA256, SCOPE
from package_versions import ROOT, package
from package_review_rom import package as package_review


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def snapshot_baseline(output):
    output = Path(output)
    paths = {'versions.json':ROOT/'mods/hoenn/versions/versions.json',
             'review.json':ROOT/'roms/rom-de-teste/review.json',
             'test.sav':ROOT/'roms/rom-de-teste/Pokemon-Journey-TESTE.sav'}
    for name, source in paths.items():
        assert digest(source) == BASELINE_SHA256[name], ('Layer-170 baseline changed',name)
        target = output/name
        if target.exists():
            assert target.read_bytes() == source.read_bytes(), ('Existing baseline differs',target)
        else:
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source,target)
    info = json.loads((output/'versions.json').read_bytes())
    assert info['validated'] and info['parent_rom_sha256'] == PARENT_ROM_SHA256
    assert info['validation_scope'] == 'coast-scenery-review' and len(info['integration_layers']) == 170


def freeze(source, artifacts, aliases, output):
    from prepare_generated_area_review import PRIOR
    source,artifacts,aliases,output = map(lambda p:Path(p).resolve(),(source,artifacts,aliases,output))
    assert not artifacts.exists() and not aliases.exists() and not output.exists(), 'Frozen artifacts already exist'
    raw_sha,elf_sha = digest(source/'pokeemerald.gba'),digest(source/'pokeemerald.elf')
    assert raw_sha != PARENT_ROM_SHA256, 'Compile layer 171 before freezing'
    marker = source/('.journey-'+SCOPE)
    assert marker.is_file()
    assert contract.PREPARED_SHA256, 'Pin the final generated area source before freezing'
    assert json.loads(marker.read_bytes())['prepared_sha256'] == contract.PREPARED_SHA256
    for name, sha in contract.PREPARED_SHA256.items():
        assert digest(source/name) == sha, ('Prepared source changed before freezing', name)
    release = package(source,artifacts)
    assert release['integration_layers'] == PRIOR+[SCOPE]
    review = package_review(source,artifacts/'Pokemon-Journey-Gen1-9-Normal.gba',artifacts/'test')
    editions=[]
    variants=[(r['file'].removeprefix('Pokemon-Journey-').removesuffix('.gba'),
               artifacts/r['file'],r['sha256']) for r in release['variants']]
    variants.append(('TESTE',artifacts/'test'/review['file'],review['sha256']))
    for name,rom,sha in variants:
        rom.chmod(0o444)
        target=aliases/name
        target.mkdir(parents=True)
        for path in source.iterdir():
            if path.name != 'pokeemerald.gba':
                (target/path.name).symlink_to(path,target_is_directory=path.is_dir())
        # Each view refers to its own immutable exported edition. Do not build
        # or package in these views; keeping one copy avoids five extra ROMs.
        (target/'pokeemerald.gba').symlink_to(rom)
        assert digest(target/'pokeemerald.gba') == sha
        assert not rom.stat().st_mode & 0o222
        editions.append(dict(edition=name,source=str(target),rom_file=str(rom),sha256=sha))
    assert digest(source/'pokeemerald.gba') == raw_sha and digest(source/'pokeemerald.elf') == elf_sha
    result=dict(parent_source=str(source),parent_rom_sha256=raw_sha,parent_elf_sha256=elf_sha,
                layer_marker_sha256=digest(marker),editions=editions,release=release,review=review,
                aliases_are_read_only_artifact_views=True)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path)
    parser.add_argument('--artifacts',type=Path,default=ROOT/'.local/generated-area-review-artifacts')
    parser.add_argument('--aliases',type=Path,default=ROOT/'.local/generated-area-review-editions')
    parser.add_argument('--output',type=Path,default=ROOT/'.local/generated-area-review-frozen.json')
    parser.add_argument('--snapshot-baseline',type=Path)
    args=parser.parse_args()
    if args.snapshot_baseline:snapshot_baseline(args.snapshot_baseline)
    if args.source:print(json.dumps(freeze(args.source,args.artifacts,args.aliases,args.output),indent=2))
    else:assert args.snapshot_baseline
