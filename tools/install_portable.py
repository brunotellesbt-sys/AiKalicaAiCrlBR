"""Prepare a local Windows kit without installing runtimes into the operating system.

Requires Python 3.10+. Launchers run on Windows; extraction also works on Linux.
"""
import argparse
import hashlib
from pathlib import Path, PurePosixPath
import zipfile

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / 'tools'
ARCHIVES = [
    ('DotNet6/dotnet-runtime-6.0.36-win-x64.zip', 'dotnet'),
    ('DotNet6/windowsdesktop-runtime-6.0.36-win-x64.zip', 'dotnet'),
    ('HexManiacAdvance/HexManiacAdvance_x64.0.5.6.1.debug.zip', 'HexManiacAdvance'),
    ('AdvanceMap/advancedMap-1.95.zip', 'AdvanceMap'),
    ('XSE/XSE-archived.zip', 'XSE'),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, default=ROOT / '.local/windows-portable')
    args = parser.parse_args()
    checksums = dict(line.split('  ', 1)[::-1] for line in (TOOLS / 'SHA256SUMS').read_text().splitlines() if line)
    for name in [p for p, _ in ARCHIVES] + ['VB6/msvbvm60.dll']:
        if hashlib.sha256((TOOLS / name).read_bytes()).hexdigest() != checksums[name]:
            raise ValueError(f'Checksum mismatch: {name}')
    dest = args.destination.resolve()
    marker = dest / '.leafgreen-kit-v1'
    if dest.exists():
        if marker.is_file():
            print(f'Existing kit preserved: {dest}')
            return
        raise FileExistsError(f'Destination already exists without installation marker: {dest}')
    dest.mkdir(parents=True)
    for name, folder in ARCHIVES:
        with zipfile.ZipFile(TOOLS / name) as archive:
            if archive.testzip() is not None:
                raise ValueError(f'Corrupted ZIP: {name}')
            for member in archive.infolist():
                path = PurePosixPath(member.filename)
                if path.is_absolute() or '..' in path.parts or '\\' in member.filename or ':' in member.filename:
                    raise ValueError(f'Unsafe archive path: {member.filename}')
                if member.filename.lower().endswith('.lnk'):
                    continue  # Old shortcuts in community archives point to someone else's ROM.
                archive.extract(member, dest / folder)
    (dest / 'XSE/msvbvm60.dll').write_bytes((TOOLS / 'VB6/msvbvm60.dll').read_bytes())
    launchers = {
        'HexManiacAdvance.cmd': '@echo off\r\npushd "%~dp0HexManiacAdvance"\r\n"%~dp0dotnet\\dotnet.exe" HexManiacAdvance.dll %*\r\npopd\r\n',
        'AdvanceMap.cmd': '@echo off\r\npushd "%~dp0AdvanceMap\\AdvanceMap"\r\nAdvanceMap.exe %*\r\npopd\r\n',
        'XSE.cmd': '@echo off\r\npushd "%~dp0XSE"\r\nXSE.exe %*\r\npopd\r\n',
    }
    for name, content in launchers.items():
        content = content.replace('popd\r\n', 'set \"leafgreen_exit_code=%ERRORLEVEL%\"\r\npopd\r\nexit /b %leafgreen_exit_code%\r\n')
        (dest / name).write_bytes(content.encode('utf-8'))
    marker.touch()
    print(f'Prepared Windows kit: {dest}')
    print('On Windows: dotnet\\dotnet.exe --list-runtimes, then open the .cmd launchers.')


if __name__ == '__main__':
    main()
