"""A low-inode candidate must never write into its frozen parent."""
from pathlib import Path
import tempfile
import unittest

from compact_source_snapshot import clone


class CompactSnapshotTests(unittest.TestCase):
    def test_declared_generated_and_overlay_outputs_have_private_ancestors(self):
        with tempfile.TemporaryDirectory(dir='/tmp') as directory:
            root = Path(directory)
            parent, candidate = root/'parent', root/'candidate'
            for name in ('data/maps/a/map.bin', 'data/maps/a/events.inc',
                         'data/maps/b/map.bin', 'graphics/tree.png', 'tools/compiler'):
                path = parent/name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'parent')
            clone(parent, candidate, ['data/maps/a/map.bin', 'data/maps/a/events.inc'])
            for name in ('data/maps/a/map.bin', 'data/maps/a/events.inc', 'tools/compiler'):
                (candidate/name).write_bytes(b'candidate')
                self.assertEqual((parent/name).read_bytes(), b'parent')
            self.assertTrue((candidate/'data/maps/b').is_symlink())
            self.assertTrue((candidate/'graphics').is_symlink())
            self.assertEqual((candidate/'data/maps/b/map.bin').read_bytes(), b'parent')

    def test_refuses_reusing_or_nesting_a_snapshot(self):
        with tempfile.TemporaryDirectory(dir='/tmp') as directory:
            source = Path(directory)
            with self.assertRaises(AssertionError):
                clone(source, source/'inside', [])
            with self.assertRaises(AssertionError):
                clone(source, source, [])

    def test_materializes_mutable_ancestors_from_an_already_compact_parent(self):
        with tempfile.TemporaryDirectory(dir='/tmp') as directory:
            root = Path(directory)
            frozen, parent, candidate = root/'frozen', root/'parent', root/'candidate'
            frozen.mkdir(); parent.mkdir()
            (frozen/'map.bin').write_bytes(b'frozen')
            (parent/'maps').symlink_to(frozen, target_is_directory=True)
            clone(parent, candidate, ['maps/map.bin'])
            self.assertFalse((candidate/'maps').is_symlink())
            (candidate/'maps/map.bin').write_bytes(b'candidate')
            self.assertEqual((frozen/'map.bin').read_bytes(), b'frozen')


if __name__ == '__main__':
    unittest.main()
