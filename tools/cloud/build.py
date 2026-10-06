"""Build the Wine/.NET image with verified local packages and normal TLS/APT checks."""
from pathlib import Path
import hashlib
import os
import shutil
import socket
import ssl
import subprocess
import tempfile
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / 'tools'
PACKAGES = [
    'Wine/wine-11.0-amd64-wow64.tar.xz',
    'DotNet6/dotnet-runtime-6.0.36-win-x64.zip',
    'DotNet6/windowsdesktop-runtime-6.0.36-win-x64.zip',
    'HexManiacAdvance/HexManiacAdvance_x64.0.5.6.1.debug.zip',
    'AdvanceMap/advancedMap-1.95.zip',
    'XSE/XSE-archived.zip',
    'VB6/msvbvm60.dll',
]


def main():
    checksums = dict(line.strip().split('  ', 1)[::-1] for line in (TOOLS / 'SHA256SUMS').read_text().splitlines() if line.strip())
    for path in PACKAGES + [p.relative_to(TOOLS).as_posix() for p in (TOOLS / 'Fonts').glob('*.ttf')]:
        if hashlib.sha256((TOOLS / path).read_bytes()).hexdigest() != checksums[path]:
            raise ValueError(f'Checksum mismatch: {path}')
    config = ROOT / '.local/docker-cli'
    config.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='leafgreen-build-') as temp:
        context = Path(temp)
        (context / 'packages').mkdir()
        for path in PACKAGES:
            shutil.copyfile(TOOLS / path, context / 'packages' / Path(path).name)
        shutil.copytree(TOOLS / 'Fonts', context / 'Fonts')
        for name in ['Dockerfile', 'entrypoint.sh']:
            shutil.copyfile(TOOLS / 'cloud' / name, context / name)
        cert = os.environ.get('SSL_CERT_FILE') or ssl.get_default_verify_paths().cafile
        if not cert or not Path(cert).is_file():
            raise RuntimeError('No trusted CA bundle available; TLS verification is required.')
        shutil.copyfile(cert, context / 'build-ca.pem')
        (context / 'build-ca.pem').chmod(0o644)
        command = ['docker', '--config', str(config), 'build']
        for name in ['HTTP_PROXY', 'HTTPS_PROXY']:
            if os.environ.get(name):
                command += ['--build-arg', name]
        # Docker needs the same configured proxy hostname as the host, not direct egress.
        proxy = urlsplit(os.environ.get('HTTPS_PROXY', '')).hostname
        if proxy:
            command += ['--add-host', proxy + ':' + socket.gethostbyname(proxy)]
        command += ['-t', 'leafgreen-editors:1', str(context)]
        subprocess.run(command, check=True)


if __name__ == '__main__':
    main()
