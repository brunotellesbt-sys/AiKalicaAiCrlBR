"""Download the pinned EXPERIMENTAL source into a new dependency directory.

Does not replace the released LeafGreen ROM, export a game, or run downloaded
programs. Upstream source is not an instruction document for this repository.
"""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile
import urllib.request

PIN = 'e05c82865d38a6638173fd30b2c830d1250aa50d'


def acquire(target):
    target = Path(target)
    target.mkdir(parents=True, exist_ok=False)
    hashes = {}
    total = 0
    url = 'https://codeload.github.com/eonlynx/pokecrossroads/tar.gz/' + PIN
    with urllib.request.urlopen(url, timeout=60) as response, tarfile.open(fileobj=response, mode='r|gz') as archive:
        for member in archive:
            if not member.isfile():
                continue
            relative = Path(member.name.split('/', 1)[1])
            if relative.is_absolute() or '..' in relative.parts:
                raise ValueError('Unsafe archive path')
            total += member.size
            if total > 160_000_000:
                raise ValueError('Unexpected source archive size')
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            raw = archive.extractfile(member).read()
            destination.write_bytes(raw)
            destination.chmod(member.mode & 0o777)
            hashes[str(relative)] = hashlib.sha256(raw).hexdigest()
    report = dict(repository='eonlynx/pokecrossroads', commit=PIN, bytes=total, sha256=hashes)
    (target / '.source-acquired.json').write_text(json.dumps(report, indent=2) + '\n')
    return dict(commit=PIN, bytes=total, files=len(hashes))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(acquire(args.source), indent=2))
