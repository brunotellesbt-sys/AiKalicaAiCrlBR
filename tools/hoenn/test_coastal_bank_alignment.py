"""Bank alignment must preserve used artwork and every unrelated layout field."""
import copy
import hashlib
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from validate_coast_scenery_review_source import check_layout_metadata, check_camera_runtime, BANK_BEFORE, BANK_AFTER


class BankAlignmentTests(unittest.TestCase):
    def fixture(self, root):
        headers = ''
        for name, meta in ((BANK_BEFORE, 'Before'), (BANK_AFTER, 'After')):
            headers += 'const struct Tileset '+name+' = { .isCompressed = TRUE, .isSecondary = FALSE, .tiles = Tiles, .palettes = Palettes, .metatileAttributes = Attributes, .callback = Animation, .metatiles = '+meta+', };\n'
        raw = bytearray(640*16)
        raw[0x12B*16:0x12B*16+16] = bytes(range(16))
        for name in ('before.bin', 'after.bin'):
            (root/name).write_bytes(raw)
        old = SimpleNamespace(source=root, headers=headers,
            definitions='Before[] = INCBIN_U16("before.bin"); After[] = INCBIN_U16("after.bin");',
            maps={'JourneyWorldSea06': {'layout': 'Sea06'}},
            layouts={'Sea06': {'primary_tileset': BANK_BEFORE, 'secondary_tileset': 'Unchanged',
                               'layout_version': 'frlg', 'width': 1, 'height': 1}})
        old.grid = lambda name: (0x112B,)
        current = copy.copy(old)
        current.layouts = copy.deepcopy(old.layouts)
        current.layouts['Sea06']['primary_tileset'] = BANK_AFTER
        return old, current

    def test_used_art_matches_even_when_unused_foreign_reef_art_differs(self):
        with tempfile.TemporaryDirectory(dir='/tmp') as directory:
            root = Path(directory)
            old, current = self.fixture(root)
            raw = bytearray((root/'after.bin').read_bytes())
            raw[0x110*16] = 123  # The projected reef requires this other bank.
            (root/'after.bin').write_bytes(raw)
            proof = check_layout_metadata(current, old)
            self.assertTrue(proof[0]['every_existing_primary_metatile_identical'])
            self.assertEqual(proof[0]['used_primary_ids'], [0x12B])
            raw[0x12B*16] ^= 1
            (root/'after.bin').write_bytes(raw)
            with self.assertRaisesRegex(AssertionError, 'Existing map artwork'):
                check_layout_metadata(current, old)

    def test_rejects_geometry_secondary_bank_and_loading_changes(self):
        with tempfile.TemporaryDirectory(dir='/tmp') as directory:
            old, current = self.fixture(Path(directory))
            for key, value in (('width', 2), ('secondary_tileset', 'Other')):
                before = current.layouts['Sea06'][key]
                current.layouts['Sea06'][key] = value
                with self.assertRaisesRegex(AssertionError, 'Other layout field'):
                    check_layout_metadata(current, old)
                current.layouts['Sea06'][key] = before
            current.headers = current.headers.replace('.callback = Animation', '.callback = Different')
            with self.assertRaisesRegex(AssertionError, 'loading/behavior'):
                check_layout_metadata(current, old)

    def test_dedicated_camera_scope_cannot_change_collision_or_unknown_bank_rules(self):
        from marine_corner_coherence import extend_dedicated_ocean_camera
        with tempfile.TemporaryDirectory(dir='/tmp') as directory:
            root = Path(directory)
            old, current = root/'old', root/'current'
            for target in (old, current):
                (target/'src').mkdir(parents=True)
            before = ('#include "tv.h"\n'
                'static bool8 JourneyMarineViewMap(const struct MapHeader *header) {\n'
                '    if (JourneyMarineViewGroup(gSaveBlock1Ptr->location.mapGroup))\n'
                '        return TRUE;\n    return FALSE;\n}\n'
                'static u16 JourneyMarineTranslateBlock(void) { return 7; }\n'
                'u8 MapGridGetCollisionAt(void) { return 1; }\n')
            (old/'src/fieldmap.c').write_text(before)
            staged = {}
            layer = SimpleNamespace(source=old, outputs={},
                expected={'src/fieldmap.c': hashlib.sha256(before.encode()).hexdigest()},
                stage=lambda name, value: staged.update({name: value}))
            extend_dedicated_ocean_camera(layer)
            path = current/'src/fieldmap.c'
            path.write_text(staged['src/fieldmap.c'])
            self.assertTrue(check_camera_runtime(SimpleNamespace(source=current), SimpleNamespace(source=old))['visual_queries_only'])
            for old_text, new_text in (('return 1;', 'return 0;'),
                    ('MAP_TYPE_OCEAN_ROUTE', 'MAP_TYPE_ROUTE')):
                path.write_text(staged['src/fieldmap.c'].replace(old_text, new_text))
                with self.assertRaises(AssertionError):
                    check_camera_runtime(SimpleNamespace(source=current), SimpleNamespace(source=old))


if __name__ == '__main__':
    unittest.main()
