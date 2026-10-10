"""Verify the exported ROM and ensure its release evidence belongs to it."""
import hashlib
import json
from pathlib import Path
import argparse
from package_playable import LAYERS, PIN, ROM_NAME

ROOT = Path(__file__).resolve().parents[2]

def verify(directory):
    directory = Path(directory)
    manifest = json.loads((directory / 'release.json').read_text())
    raw = (directory / ROM_NAME).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if manifest['file'] != ROM_NAME or manifest['bytes'] != len(raw) or manifest['sha256'] != digest:
        raise ValueError('Release ROM does not match its manifest')
    if len(raw) != 32 * 1024 * 1024 or raw[0xB2] != 0x96 or raw[0xBD] != (-sum(raw[0xA0:0xBD]) - 0x19) & 255:
        raise ValueError('Invalid GBA header or ROM size')
    if manifest['source_commit'] != PIN or manifest['layers'] != LAYERS:
        raise ValueError('Unexpected integration source/layers')
    if not manifest['requires_new_save'] or manifest['game_language'] != 'English':
        raise ValueError('Unexpected release settings')
    if (directory / 'SHA256SUMS').read_text() != digest + '  ' + ROM_NAME + '\n':
        raise ValueError('Checksum file does not match the release')
    evidence = ROOT / 'mods/hoenn/playable-validation'
    for name in ['campaign-kanto/campaign-playthrough.json','campaign-hoenn/campaign-playthrough.json','browser.json','homes/family.json','birth-rules/birth-rules.json','eastern-ocean/eastern-union.json','leagues/sixteen-badge-leagues.json','world-map/world-map.json','coast/kanto-open-sea.json']:
        report = json.loads((evidence / name).read_text())
        if report['rom_sha256'] != digest:
            raise ValueError('Evidence belongs to another ROM: ' + name)
        if name.startswith('campaign-'):
            if not report['controller_only'] or report['ram_writes'] or report['script_injection']:
                raise ValueError('Opening was not controller-only: ' + name)
            if not report['battles'] or any(b['outcome'] != 1 for b in report['battles']):
                raise ValueError('Opening battle did not pass: ' + name)
        elif not report['passed']:
            raise ValueError('Failed release evidence: ' + name)
    print('Playable alpha ROM, checksum, layer chain and matching native/browser evidence passed:', digest)
    return manifest

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--directory',type=Path,default=ROOT / 'mods/hoenn/playable')
    verify(p.parse_args().directory)
