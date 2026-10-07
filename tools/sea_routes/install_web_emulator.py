#!/usr/bin/env python3
"""Vendor the pinned GBA browser emulator; verify NPM package integrity."""
import base64
import hashlib
import io
import json
from pathlib import Path
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / 'web/emulator'
PACKAGES = [
    ('@emulatorjs/emulatorjs', 'emulatorjs', '7z3qaA4LwyurhuGvdMUDF9xJpEbxC3SNy9+E9tSaOsRo8FCS2QXam/0k/lc9kqHWRFIlLKWahNjPAStyL0rFnw=='),
    ('@emulatorjs/core-mgba', 'core-mgba', 'daiHzZQKEr+P9fra7j5YoEAXiyYUEtBhFQ8EAV/SeCtrkvqtayU7GQ9LYgoSgzkKSwsbNSskApqGuA9EGARYPA=='),
]

def main():
    TARGET.mkdir(parents=True, exist_ok=True)
    report = []
    for package, name, integrity in PACKAGES:
        url = f'https://registry.npmjs.org/{package}/-/{name}-4.2.3.tgz'
        data = urllib.request.urlopen(url, timeout=60).read()
        if base64.b64encode(hashlib.sha512(data).digest()).decode() != integrity:
            raise ValueError('Package integrity mismatch: ' + package)
        with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as tar:
            for member in tar:
                if not member.isfile(): continue
                relative = member.name.removeprefix('package/')
                if name == 'emulatorjs':
                    if not relative.startswith('data/'): continue
                    relative = relative.removeprefix('data/')
                else: relative = 'cores/' + relative
                parts = Path(relative).parts
                if '..' in parts or Path(relative).is_absolute(): raise ValueError('Unsafe package path')
                p = TARGET / relative
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(tar.extractfile(member).read())
        report.append(dict(package=package, version='4.2.3', url=url, integrity='sha512-' + integrity))
    # This is a pinned installation. An optional upstream update check has no
    # error handler and breaks browser diagnostics on offline/private hosts.
    p = TARGET / 'src/emulator.js'; text = p.read_text()
    begin = text.index('    checkForUpdates() {')
    end = text.index('    versionAsInt(ver) {', begin)
    p.write_text(text[:begin] + '    checkForUpdates() { /* Version is pinned by the host application. */ }\n' + text[end:])
    license_url = 'https://raw.githubusercontent.com/EmulatorJS/EmulatorJS/v4.2.3/LICENSE'
    (TARGET / 'LICENSE').write_bytes(urllib.request.urlopen(license_url, timeout=60).read())
    (TARGET / 'provenance.json').write_text(json.dumps(dict(packages=report,
        source='https://github.com/EmulatorJS/EmulatorJS/tree/v4.2.3',
        core_source='https://github.com/EmulatorJS/build',
        local_changes=['Disable optional update check; all runtime code is otherwise unmodified']), indent=2) + '\n')

if __name__ == '__main__': main()
