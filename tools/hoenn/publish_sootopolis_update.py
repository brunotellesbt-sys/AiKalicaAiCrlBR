"""Package four final harbor editions with fresh proof and retained coastal history."""
import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

from package_versions import ROOT, package
from verify_versions import verify


def publish(source, validation, output, pallet_validation=None):
    source, validation, output = Path(source), Path(validation), Path(output)
    current = json.loads((output/'versions.json').read_text())
    previous = current['previous_validation']
    old = (ROOT/previous['manifest']).read_bytes()
    assert hashlib.sha256(old).hexdigest() == previous['manifest_sha256']
    historical = json.loads(old)['historical_validation']
    info = package(source, output)
    info.update(validation_scope='sootopolis-harbor', full_campaign_playthrough=False,
                previous_validation=previous, historical_validation=historical,
                special_encounters_validated=True, proofs=[])
    if (source/'.journey-pallet-harbor').exists():
        assert pallet_validation is not None, 'Fresh Pallet validation is required'
    pallet_validation = Path(pallet_validation) if pallet_validation is not None else None
    reproduction_path = (pallet_validation or validation)/'validation/reproduction.json'
    reproduction = json.loads(reproduction_path.read_text())
    reproduction['layers'] = info['integration_layers']
    reproduction_path.write_text(json.dumps(reproduction, indent=2)+'\n')
    if pallet_validation:
        info['pallet_harbor_validated'] = True

    def add(path, target, kind):
        relative = Path('evidence/sootopolis-harbor')/target.removesuffix('.gba')/(kind+'.json')
        destination = output/relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
        info['proofs'].append(dict(file=relative.as_posix(), target=target, kind=kind,
                                   sha256=hashlib.sha256(destination.read_bytes()).hexdigest()))

    add(validation/'validation/sootopolis-harbor.json', 'common', 'sootopolis-harbor')
    add(reproduction_path, 'common', 'reproduction')
    if pallet_validation:
        add(pallet_validation/'validation/pallet-harbor.json', 'common', 'pallet-harbor')
    for row in info['variants']:
        edition = row['file'].removeprefix('Pokemon-Journey-').removesuffix('.gba')
        add(validation/edition/'sootopolis-harbor.json', row['file'], 'sootopolis-harbor')
        add(validation/edition/'special-encounters.json', row['file'], 'special-encounters')
        if pallet_validation:
            add(pallet_validation/edition/'pallet-harbor.json', row['file'], 'pallet-harbor')
    (output/'versions.json').write_text(json.dumps(info, indent=2)+'\n')
    verify(output, require_seal=False)
    info['validated'] = True
    (output/'versions.json').write_text(json.dumps(info, indent=2)+'\n')
    verify(output)
    archive = output/'Pokemon-Journey-Four-Editions.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for name in [r['file'] for r in info['variants']]+['versions.json', 'SHA256SUMS']:
            z.write(output/name, name)
        z.writestr('START-HERE.md', (output/'START-HERE.md').read_text().replace('../../../docs/', 'docs/'))
        for proof in info['proofs']:
            z.write(output/proof['file'], proof['file'])
        for p in sorted((ROOT/'docs').rglob('*')):
            if p.is_file():
                z.write(p, 'docs/'+p.relative_to(ROOT/'docs').as_posix())
    return archive


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--validation', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=ROOT/'mods/hoenn/versions')
    parser.add_argument('--pallet-validation', type=Path)
    args = parser.parse_args()
    print(publish(args.source, args.validation, args.output, args.pallet_validation))
