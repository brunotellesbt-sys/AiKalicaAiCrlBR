"""Build cache copies only recognized derived outputs into missing paths."""
from pathlib import Path
import tempfile
import unittest

from prepare_atlas_surf_layout import seed_build_cache


class BuildCacheTests(unittest.TestCase):
    def test_allowlisted_outputs_preserve_protected_and_existing_files(self):
        with tempfile.TemporaryDirectory(prefix='atlas-cache-test-') as temporary:
            root=Path(temporary);cache=root/'cache';target=root/'target'
            cache.mkdir();target.mkdir()
            accepted=['build/modern/src/player.o','build/modern/src/player.d',
                      'build/modern/src/player.s','build/modern/lib.a',
                      'graphics/player.4bpp.smol','data/maps/Test/header.inc']
            ignored=['extra_source.c','src/extra_source.c','build/extra_source.c',
                     'graphics/player.png','graphics/unknown.bin','unknown/generated.h',
                     'pokeemerald.gba','pokeemerald.elf']
            protected='include/constants/map_groups.h'
            existing='build/modern/src/existing.o'
            for name in accepted+ignored+[protected,existing]:
                path=cache/name;path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(b'cache')
            (target/existing).parent.mkdir(parents=True,exist_ok=True)
            (target/existing).write_bytes(b'verified')
            report=seed_build_cache(cache,target,{protected})
            self.assertEqual(report['files'],len(accepted))
            for name in accepted:
                self.assertEqual((target/name).read_bytes(),b'cache')
                self.assertNotEqual((target/name).stat().st_ino,(cache/name).stat().st_ino)
            for name in ignored+[protected]:
                self.assertFalse((target/name).exists(),name)
            self.assertEqual((target/existing).read_bytes(),b'verified')


if __name__=='__main__':
    unittest.main()
