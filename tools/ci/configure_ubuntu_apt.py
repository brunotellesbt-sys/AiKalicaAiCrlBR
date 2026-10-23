"""Bound Ubuntu 24.04 CI downloads and use the official Ubuntu archive.

Run with sudo on the hosted runner before Playwright installs dependencies.
``--root`` supports isolated fixtures; this helper does not install packages.
Only known Ubuntu archive URI tokens change. Repository suites, components,
keys and third-party sources retain their original bytes.
"""
import argparse
import json
from pathlib import Path
import re
import shlex


ARCHIVE = 'https://archive.ubuntu.com/ubuntu'
MIRROR_FILE_URI = 'mirror+file:/etc/apt/apt-mirrors.txt'
POLICY_FILE = Path('etc/apt/apt.conf.d/99journey-ci-network')
POLICY = (
    '// Bounded CI downloads; normal TLS and package verification remain enabled.\n'
    'Acquire::http::Timeout "30";\n'
    'Acquire::https::Timeout "30";\n'
    'Acquire::Retries "2";\n'
).encode()


def _require_ubuntu(root):
    values = {}
    for line in (root / 'etc/os-release').read_text().splitlines():
        name, separator, value = line.partition('=')
        if separator and name in {'ID', 'VERSION_ID'}:
            tokens = shlex.split(value, comments=True)
            if len(tokens) != 1:
                raise ValueError('Invalid Ubuntu release identity')
            values[name] = tokens[0]
    if values != {'ID': 'ubuntu', 'VERSION_ID': '24.04'}:
        raise ValueError('This CI apt configuration requires Ubuntu 24.04')


def _uri(token):
    if token == MIRROR_FILE_URI:
        return ARCHIVE
    if re.fullmatch(r'https?://azure\.archive\.ubuntu\.com/ubuntu/?', token,
                    flags=re.IGNORECASE):
        return ARCHIVE + ('/' if token.endswith('/') else '')
    return token


def _rewrite(data, *, deb822):
    count = 0

    def tokens(value):
        def substitute(match):
            nonlocal count
            old = match[0]
            new = _uri(old)
            count += new != old
            return new
        return re.sub(r'\S+', substitute, value)

    result = []
    field = None
    for line in data.decode('utf-8').splitlines(keepends=True):
        if deb822:
            if not line.strip():
                field = None
            elif line.lstrip().startswith('#'):
                pass
            elif match := re.match(r'^([A-Za-z][A-Za-z0-9-]*[ \t]*:)(.*)$', line):
                field = match[1].split(':', 1)[0].strip().lower()
                if field == 'uris':
                    line = match[1] + tokens(match[2]) + line[len(match[0]):]
            elif line.startswith((' ', '\t')) and field == 'uris':
                line = tokens(line)
        elif match := re.match(r'^(\s*deb(?:-src)?\s+(?:\[[^\]\r\n]*\]\s+)?)(\S+)', line):
            line = match[1] + tokens(match[2]) + line[len(match[0]):]
        result.append(line)
    return ''.join(result).encode('utf-8'), count


def configure(root=Path('/')):
    root = Path(root)
    # Reject other distributions before creating directories or changing files.
    _require_ubuntu(root)
    sources = []
    classic = root / 'etc/apt/sources.list'
    if classic.is_file():
        sources.append(classic)
    directory = root / 'etc/apt/sources.list.d'
    sources.extend(sorted(directory.glob('*.list')))
    sources.extend(sorted(directory.glob('*.sources')))

    # Prepare every replacement before applying any change.
    pending, replacements = [], 0
    for path in sources:
        old = path.read_bytes()
        new, count = _rewrite(old, deb822=path.suffix == '.sources')
        replacements += count
        if new != old:
            pending.append((path, new))
    policy = root / POLICY_FILE
    policy_changed = not policy.is_file() or policy.read_bytes() != POLICY
    for path, contents in pending:
        path.write_bytes(contents)
    if policy_changed:
        policy.parent.mkdir(parents=True, exist_ok=True)
        policy.write_bytes(POLICY)
    return {
        'source_files_examined': len(sources),
        'source_files_changed': [str(path.relative_to(root)) for path, _ in pending],
        'ubuntu_archive_replacements': replacements,
        'apt_policy_changed': policy_changed,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('/'))
    args = parser.parse_args()
    print(json.dumps(configure(args.root), sort_keys=True))
