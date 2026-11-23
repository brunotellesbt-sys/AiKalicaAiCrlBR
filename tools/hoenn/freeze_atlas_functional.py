"""Authenticate a compiled private source and export immutable edition views."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from candidate_layer import Layer
from prepare_generated_area_review import PRIOR,LAYER
from package_versions import package
from package_review_rom import package as package_review


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def freeze(source,output,artifacts,aliases,build_log):
    source,output,artifacts,aliases,build_log=(Path(p).resolve() for p in (source,output,artifacts,aliases,build_log))
    assert not any(p.exists() for p in (output,artifacts,aliases)),'Preserve frozen artifacts'
    metadata=json.loads((source/'.journey-atlas-surf-layout').read_bytes())
    expected=Layer(source,'atlas-surf-layout',PRIOR+[LAYER,'atlas-surf-layout']).expected
    for name,wanted in expected.items():assert sha(source/name)==wanted,name
    log=build_log.read_text();assert 'arm-none-eabi-objcopy -O binary' in log
    used=int(re.findall(r'ROM:\s*(\d+) B',log)[-1]);assert used<33554432
    frozen=dict(schema='atlas-final-compiled-freeze/v1',source=str(source),
        rom_sha256=sha(source/'pokeemerald.gba'),elf_sha256=sha(source/'pokeemerald.elf'),
        marker_sha256=sha(source/'.journey-atlas-surf-layout'),prepared_sha256=metadata['prepared_sha256'],
        complete_source_files_checked=len(expected),
        complete_source_manifest_sha256=hashlib.sha256(json.dumps(expected,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
        source_manifest_encoding='JSON sorted keys, compact separators',migration_version=8,
        rom_used_bytes=used,rom_limit_bytes=33554432,global_source_validation_passed=True,
        known_generated_water_components=1,active_maps=len(metadata['geometry_plan']['chunks']),
        preserved_candidate_slots=len(metadata['candidate533_migration']['current_maps']) if 'current_maps' in metadata['candidate533_migration'] else 606,
        native_validated=False,final_release_validated=False)
    release=package(source,artifacts)
    review=package_review(source,artifacts/'Pokemon-Journey-Gen1-9-Normal.gba',artifacts/'test')
    rows=[]
    editions=[(r['file'].removeprefix('Pokemon-Journey-').removesuffix('.gba'),artifacts/r['file'],r['sha256']) for r in release['variants']]
    editions.append(('TESTE',artifacts/'test'/review['file'],review['sha256']))
    for name,rom,digest in editions:
        rom.chmod(0o444);folder=aliases/name;folder.mkdir(parents=True)
        for path in source.iterdir():
            if path.name!='pokeemerald.gba':(folder/path.name).symlink_to(path,target_is_directory=path.is_dir())
        (folder/'pokeemerald.gba').symlink_to(rom)
        assert sha(folder/'pokeemerald.gba')==digest
        rows.append(dict(edition=name,source=str(folder),rom_file=str(rom),sha256=digest))
    frozen['editions']=rows;frozen['release']=release;frozen['review']=review
    assert sha(source/'pokeemerald.gba')==frozen['rom_sha256']
    output.write_text(json.dumps(frozen,indent=2)+'\n')
    print('Frozen current source and five editions:',frozen['rom_sha256'],flush=True)
    return frozen


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','output','artifacts','aliases','build-log'):p.add_argument('--'+name,type=Path,required=True)
    freeze(**vars(p.parse_args()))
