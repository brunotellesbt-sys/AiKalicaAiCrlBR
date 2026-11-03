"""Seal three independently checked native coastal reproductions into one proof."""
import argparse
import hashlib
import json
from pathlib import Path

PARTS = {
    'one': ('arrival-coast-one-native', 'arrival-coast-one-native.json'),
    'forest': ('arrival-coast-forest-native', 'arrival-coast-forest-native.json'),
    'cinnabar': ('cinnabar-door-exit', 'cinnabar-door-exit.json'),
}


def aggregate(directory):
    from verify_arrival_coast_review_update import verify_photos
    directory = Path(directory)
    components, reports = [], []
    for folder, (kind, filename) in PARTS.items():
        path = directory/folder/filename
        raw = path.read_bytes()
        report = json.loads(raw)
        assert report['passed'] is True and report['kind'] == kind
        components.append(dict(kind=kind, file=path.relative_to(directory).as_posix(),
                               sha256=hashlib.sha256(raw).hexdigest()))
        reports.append(report)
    assert len({row['rom_sha256'] for row in reports}) == 1
    assert len({row['elf_sha256'] for row in reports}) == 1
    result = dict(kind='arrival-coast-photos', passed=True,
                  rom_sha256=reports[0]['rom_sha256'], elf_sha256=reports[0]['elf_sha256'],
                  compiled_rom=True, native_validation_performed=True,
                  components=components, full_campaign_playthrough=False)
    # Reject missing controller observations, source-only captures, incomplete
    # animation phases or stale child hashes before writing a passing report.
    verify_photos(result, directory)
    target = directory/'arrival-coast-photos.json'
    target.write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(aggregate(args.directory), indent=2))
