"""Partial-copy recovery must preserve edits and isolate every mutable file."""
import hashlib
from pathlib import Path
import tempfile
import unittest

from prepare_legendary_chambers import clone_authenticated


class PrivateChamberPreparation(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='chamber-copy-guards-')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.source=self.root/'source';self.source.mkdir()
        (self.source/'source.c').write_bytes(b'authenticated input\n')
        (self.source/'build').mkdir()
        (self.source/'build/cache.o').write_bytes(b'private generated cache')
        (self.source/'.journey-atlas-surf-layout').write_bytes(b'independent marker')
        self.expected={'source.c':hashlib.sha256((self.source/'source.c').read_bytes()).hexdigest()}
        self.target=self.root/'target'

    def test_only_authenticated_readonly_inputs_share_inodes(self):
        clone_authenticated(self.source,self.target,self.expected)
        self.assertTrue((self.source/'source.c').samefile(self.target/'source.c'))
        self.assertFalse((self.target/'source.c').stat().st_mode&0o222)
        for name in ('build/cache.o','.journey-atlas-surf-layout'):
            self.assertEqual((self.source/name).read_bytes(),(self.target/name).read_bytes())
            self.assertFalse((self.source/name).samefile(self.target/name))

    def test_unchanged_partial_copy_can_resume_without_overwriting_its_files(self):
        self.target.mkdir();path=self.target/'source.c'
        path.write_bytes((self.source/'source.c').read_bytes())
        inode=path.stat().st_ino
        clone_authenticated(self.source,self.target,self.expected,resume=True)
        self.assertEqual(path.stat().st_ino,inode)
        self.assertEqual((self.target/'build/cache.o').read_bytes(),b'private generated cache')

    def test_changed_partial_preparation_is_preserved_and_rejected(self):
        self.target.mkdir();path=self.target/'source.c';path.write_bytes(b'unfinished authored work')
        with self.assertRaisesRegex(ValueError,'Preserve changed partial'):
            clone_authenticated(self.source,self.target,self.expected,resume=True)
        self.assertEqual(path.read_bytes(),b'unfinished authored work')

    def test_changed_reference_and_compiled_artifacts_are_not_silently_accepted(self):
        (self.source/'source.c').write_bytes(b'changed frozen input')
        with self.assertRaisesRegex(Exception,'Frozen input changed'):
            clone_authenticated(self.source,self.target,self.expected)

    def test_old_ROM_ELF_and_linker_map_can_be_omitted_from_a_new_build(self):
        for name in ('pokeemerald.gba','pokeemerald.elf','pokeemerald.map'):
            (self.source/name).write_bytes(b'old compiled output')
        clone_authenticated(self.source,self.target,self.expected,omit_compiled_artifacts=True)
        self.assertTrue((self.target/'source.c').is_file())
        self.assertFalse(any((self.target/n).exists() for n in ('pokeemerald.gba','pokeemerald.elf','pokeemerald.map')))
