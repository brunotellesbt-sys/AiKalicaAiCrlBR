"""Exercise real apt source formats without touching the host configuration."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from configure_ubuntu_apt import POLICY_FILE, configure


class UbuntuAptConfiguration(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.write('etc/os-release', 'ID="ubuntu"\nVERSION_ID="24.04"\n')

    def write(self, name, contents):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents if isinstance(contents, bytes) else contents.encode())
        return path

    def snapshot(self):
        return {p.relative_to(self.root): p.read_bytes()
                for p in self.root.rglob('*') if p.is_file()}

    def test_other_distributions_and_releases_are_rejected_before_writes(self):
        self.write('etc/apt/sources.list',
                   'deb http://azure.archive.ubuntu.com/ubuntu noble main\n')
        for identity in ['ID=debian\nVERSION_ID=12\n',
                         'ID=ubuntu\nVERSION_ID=22.04\n',
                         'ID=ubuntu\nVERSION_ID=24.04\nID=debian\n']:
            with self.subTest(identity=identity):
                self.write('etc/os-release', identity)
                before = self.snapshot()
                with self.assertRaises(ValueError):
                    configure(self.root)
                self.assertEqual(self.snapshot(), before)
                self.assertFalse((self.root / 'etc/apt/apt.conf.d').exists())

    def test_classic_sources_preserve_options_comments_suites_and_other_repos(self):
        original = (
            '# deb http://azure.archive.ubuntu.com/ubuntu noble main\r\n'
            'deb [arch=amd64 signed-by=/usr/share/keyrings/ubuntu-archive-keyring.gpg] '
            'http://azure.archive.ubuntu.com/ubuntu noble noble-updates main restricted\r\n'
            ' deb-src https://azure.archive.ubuntu.com/ubuntu/ noble-security universe\r\n'
            'deb https://packages.microsoft.com/ubuntu/24.04/prod noble main\r\n'
            'deb https://example.org/ubuntu noble main # keep third-party source\r\n'
        )
        path = self.write('etc/apt/sources.list', original)
        report = configure(self.root)
        expected = original.replace(
            'http://azure.archive.ubuntu.com/ubuntu noble noble-updates',
            'https://archive.ubuntu.com/ubuntu noble noble-updates').replace(
            'https://azure.archive.ubuntu.com/ubuntu/ noble-security',
            'https://archive.ubuntu.com/ubuntu/ noble-security')
        self.assertEqual(path.read_bytes(), expected.encode())
        self.assertEqual(report['ubuntu_archive_replacements'], 2)

    def test_deb822_changes_only_uri_fields_and_their_continuations(self):
        original = (
            '# URIs: http://azure.archive.ubuntu.com/ubuntu\n'
            'Types: deb deb-src\n'
            'URIs: mirror+file:/etc/apt/apt-mirrors.txt\n'
            ' https://azure.archive.ubuntu.com/ubuntu/ https://example.org/mirror\n'
            'Suites: noble noble-updates noble-backports noble-security\n'
            'Components: main restricted universe multiverse\n'
            'Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg\n'
            '\n'
            'Types: deb\n'
            'URIs: https://packages.microsoft.com/ubuntu/24.04/prod\n'
            'Suites: noble\n'
            'Components: main\n'
            'Signed-By:\n'
            ' -----BEGIN PGP PUBLIC KEY BLOCK-----\n'
            ' http://azure.archive.ubuntu.com/ubuntu\n'
            ' -----END PGP PUBLIC KEY BLOCK-----\n'
        )
        path = self.write('etc/apt/sources.list.d/ubuntu.sources', original)
        report = configure(self.root)
        expected = original.replace(
            'URIs: mirror+file:/etc/apt/apt-mirrors.txt',
            'URIs: https://archive.ubuntu.com/ubuntu').replace(
            ' https://azure.archive.ubuntu.com/ubuntu/ https://example.org/mirror',
            ' https://archive.ubuntu.com/ubuntu/ https://example.org/mirror')
        self.assertEqual(path.read_bytes(), expected.encode())
        self.assertEqual(report['ubuntu_archive_replacements'], 2)

    def test_only_exact_known_uri_tokens_change(self):
        original = (
            'deb mirror+file:/etc/apt/apt-mirrors.txt noble main\n'
            'deb mirror+file:/etc/apt/apt-mirrors.txt.backup noble main\n'
            'deb mirror+file:/etc/apt/other-mirrors.txt noble main\n'
            'deb https://azure.archive.ubuntu.com/ubuntu/custom noble main\n'
            'deb https://azure.archive.ubuntu.com.evil/ubuntu noble main\n'
        )
        path = self.write('etc/apt/sources.list.d/classic.list', original)
        report = configure(self.root)
        expected = original.replace(
            'deb mirror+file:/etc/apt/apt-mirrors.txt noble main',
            'deb https://archive.ubuntu.com/ubuntu noble main')
        self.assertEqual(path.read_bytes(), expected.encode())
        self.assertEqual(report['ubuntu_archive_replacements'], 1)

    def test_timeout_and_retry_policy_remains_verified_and_is_idempotent(self):
        self.write('etc/apt/sources.list.d/ubuntu.sources',
                   'Types: deb\nURIs: mirror+file:/etc/apt/apt-mirrors.txt\n'
                   'Suites: noble\nComponents: main\n'
                   'Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg\n')
        first = configure(self.root)
        expected = (
            '// Bounded CI downloads; normal TLS and package verification remain enabled.\n'
            'Acquire::http::Timeout "30";\n'
            'Acquire::https::Timeout "30";\n'
            'Acquire::Retries "2";\n'
        )
        self.assertEqual((self.root / POLICY_FILE).read_bytes(), expected.encode())
        before = self.snapshot()
        second = configure(self.root)
        self.assertTrue(first['apt_policy_changed'])
        self.assertFalse(second['apt_policy_changed'])
        self.assertEqual(second['source_files_changed'], [])
        self.assertEqual(second['ubuntu_archive_replacements'], 0)
        self.assertEqual(self.snapshot(), before)

    def test_cli_root_option_uses_only_the_fixture(self):
        path = self.write('etc/apt/sources.list',
                          'deb http://azure.archive.ubuntu.com/ubuntu noble main\n')
        result = subprocess.run(
            [sys.executable, str(Path(__file__).with_name('configure_ubuntu_apt.py')),
             '--root', str(self.root)],
            check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout)['ubuntu_archive_replacements'], 1)
        self.assertEqual(path.read_text(),
                         'deb https://archive.ubuntu.com/ubuntu noble main\n')


if __name__ == '__main__':
    unittest.main()
