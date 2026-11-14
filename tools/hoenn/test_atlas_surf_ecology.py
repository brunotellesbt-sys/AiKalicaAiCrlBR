"""Exercise direct aliases, historical-ID leases, and encounter hook coverage."""
import ctypes
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from atlas_surf_ecology import (CONTENT_PATHS, GROUPS, HEADER, IMPLEMENTATION,
                                alias_rows, generate_lookup, stage)


class FixtureLayer:
    def __init__(self, source):
        self.source = source
        self.expected, self.outputs = {}, {}

    def write_parent(self, path, value):
        raw = value if isinstance(value, bytes) else value.encode()
        target = self.source / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        self.expected[path] = hashlib.sha256(raw).hexdigest()

    def stage(self, path, value):
        before = self.source / path
        digest = hashlib.sha256(before.read_bytes()).hexdigest() if before.exists() else None
        assert digest == self.expected.get(path), path
        self.outputs[path] = value if isinstance(value, bytes) else value.encode()


class AtlasEcology(unittest.TestCase):
    def fixture(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        layer = FixtureLayer(Path(temporary.name))
        parent = dict(group_order=['Native'], Native=['OldZero', 'OldA'])
        layer.write_parent(GROUPS, json.dumps(parent))
        for name, ident in [('OldZero', 'MAP_OLD_ZERO'), ('OldA', 'MAP_OLD_A')]:
            layer.write_parent(f'data/maps/{name}/map.json', json.dumps(dict(id=ident)))
        layer.stage(GROUPS, json.dumps(dict(group_order=['Native', 'Unused', 'Atlas'],
                                          Native=parent['Native'], Unused=[],
                                          Atlas=['NewA', 'UnusedNew', 'NewB'])))
        for name, ident in [('NewA', 'MAP_NEW_A'), ('NewB', 'MAP_NEW_B')]:
            layer.stage(f'data/maps/{name}/map.json', json.dumps(dict(id=ident)))
        layer.write_parent('src/journey_wild.c', '''#include "global.h"
u32 JourneyWildLevel(void) { return 42; }
u32 JourneyWildSpecies(u32 original,u32 area)
{
    for (u32 i = 0; i < 3; i++)
        if (MAP_GROUP(pools[i].map) == gSaveBlock1Ptr->location.mapGroup
         && MAP_NUM(pools[i].map) == gSaveBlock1Ptr->location.mapNum)
            return pools[i].species;
    return original;
}
u32 JourneyFishingOdds(u32 base)
{
    if (gSaveBlock1Ptr->location.mapGroup == 0 && gSaveBlock1Ptr->location.mapNum == 1)
        return base * 40 / 100;
    return base;
}
bool32 JourneyWildPoolAvailable(u32 area)
{
    return gSaveBlock1Ptr->location.mapGroup == 0 && gSaveBlock1Ptr->location.mapNum == 1;
}
''')
        layer.write_parent('src/journey_habitats.c', '''#include "global.h"
bool32 JourneyHabitatHasSpecies(u32 group, u32 map, u32 species)
{
    if (gJourneyBuildRules.maxNational == 493)
        return group == 0 && map == 1 && species == 72;
    return group == 0 && map == 1 && species == 592;
}
''')
        layer.write_parent('src/wild_encounter.c', '''#include "global.h"
u16 GetCurrentMapWildMonHeaderId(void)
{
    if (gSaveBlock1Ptr->location.mapGroup == 0 && gSaveBlock1Ptr->location.mapNum == 1)
        return 10;
    return 65535;
}
bool8 StandardWildEncounter(void)
{
    if (gJourneyReviewMode || gJourneyTestMode) return FALSE;
    return TRUE;
}
''')
        for path in CONTENT_PATHS:
            layer.write_parent(path, 'unchanged encounter content: ' + path)
        return layer

    def test_all_hooks_stage_without_changing_content_levels_or_suppression(self):
        layer = self.fixture()
        originals = {path: (layer.source / path).read_bytes() for path in CONTENT_PATHS}
        report = stage(layer, {'NewA': 'OldA', 'NewB': 'OldZero'})
        self.assertEqual(report['alias_count'], 2)
        self.assertEqual(report['lookup'], 'direct-group-number')
        self.assertFalse(report['compiled_rom_validated'])
        for path, raw in originals.items():
            self.assertEqual((layer.source / path).read_bytes(), raw)
            self.assertNotIn(path, layer.outputs)
        wild = layer.outputs['src/journey_wild.c'].decode()
        self.assertEqual(wild.count('JourneyAtlasEcologyOwner('), 3)
        self.assertIn('u32 JourneyWildLevel(void) { return 42; }', wild)
        encounters = layer.outputs['src/wild_encounter.c'].decode()
        self.assertIn('if (gJourneyReviewMode || gJourneyTestMode) return FALSE;', encounters)
        self.assertIn('JourneyAtlasEcologyOwner(', encounters)
        habitats = layer.outputs['src/journey_habitats.c'].decode()
        self.assertIn('gJourneyBuildRules.maxNational == 493', habitats)
        self.assertIn('group = MAP_GROUP(ecologyMap);', habitats)
        self.assertIn('map = MAP_NUM(ecologyMap);', habitats)

    def test_alias_owner_zero_and_native_identity_with_compiled_c(self):
        compiler = shutil.which('cc')
        if not compiler:
            self.skipTest('Host C compiler unavailable')
        layer = self.fixture()
        header, implementation = generate_lookup(alias_rows(layer, {'NewA': 'OldA', 'NewB': 'OldZero'}))
        (layer.source / 'global.h').write_text(
            '#include <stddef.h>\n#include <stdint.h>\n'
            'typedef uint16_t u16; typedef uint32_t u32;\n'
            '#define ARRAY_COUNT(a) (sizeof(a)/sizeof((a)[0]))\n')
        constants = layer.source / 'constants'
        constants.mkdir()
        (constants / 'maps.h').write_text(
            '#define MAP_GROUP(x) ((x)>>8)\n#define MAP_NUM(x) ((x)&255)\n'
            '#define MAP_OLD_ZERO 0\n#define MAP_OLD_A 1\n'
            '#define MAP_NEW_A 512\n#define MAP_NEW_B 514\n')
        (layer.source / Path(HEADER).name).write_text(header)
        code, library = layer.source / 'aliases.c', layer.source / 'aliases.so'
        code.write_text(implementation)
        subprocess.run([compiler, '-std=c99', '-Wall', '-Wextra', '-Werror', '-shared', '-fPIC',
                        '-I', str(layer.source), str(code), '-o', str(library)], check=True,
                       capture_output=True, text=True)
        native = ctypes.CDLL(str(library)).JourneyAtlasEcologyOwner
        native.argtypes = [ctypes.c_uint16]
        native.restype = ctypes.c_uint16
        expected = {512: 1, 514: 0}
        # Includes sparse holes, unused groups, native owner zero and invalid IDs.
        for identity in range(65536):
            self.assertEqual(native(identity), expected.get(identity, identity))

    def test_refuse_unknown_owner_new_owner_chains_and_historical_targets(self):
        for mapping in ({'Missing': 'OldA'}, {'NewA': 'Missing'},
                        {'NewA': 'NewB'}, {'OldA': 'OldZero'}):
            with self.subTest(mapping=mapping), self.assertRaises(ValueError):
                alias_rows(self.fixture(), mapping)

    def test_refuse_renumbered_historical_owner(self):
        layer = self.fixture()
        groups = json.loads(layer.outputs[GROUPS])
        groups['Native'].reverse()
        layer.stage(GROUPS, json.dumps(groups))
        with self.assertRaisesRegex(ValueError, 'removed or renumbered'):
            alias_rows(layer, {'NewA': 'OldA'})

    def test_refuse_stale_parent_or_missing_lookup_hook(self):
        layer = self.fixture()
        (layer.source / GROUPS).write_text('{}')
        with self.assertRaises(AssertionError):
            alias_rows(layer, {'NewA': 'OldA'})
        layer = self.fixture()
        path = 'src/journey_wild.c'
        layer.stage(path, (layer.source / path).read_text().replace(
            'JourneyWildPoolAvailable', 'RemovedLookup'))
        with self.assertRaisesRegex(AssertionError, 'ecology hook definition'):
            stage(layer, {'NewA': 'OldA'})
        self.assertNotIn(IMPLEMENTATION, layer.outputs)


if __name__ == '__main__':
    unittest.main()
