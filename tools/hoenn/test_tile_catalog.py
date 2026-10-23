"""The committed native examples must remain usable without the source snapshot."""
from pathlib import Path
import unittest

from catalog_common_tiles import verify


class TileCatalog(unittest.TestCase):
    def test_exported_native_bytes_reconstruct_all_named_examples(self):
        verify(Path(__file__).resolve().parents[2] / 'assets/tiles')


if __name__=='__main__':
    unittest.main()
