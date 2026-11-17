"""Authenticated cave-underlay recovery rejects new gaps and altered evidence."""
import base64
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import zlib

from atlas_surf_geometry import rasterize
from atlas_surf_occluded_routes import (ART_SHA256, BRANCH_EVIDENCE_SHA256,
    HEADER, MARKER, extract_occluded_routes, record_native_obstructions)
from atlas_surf_truth import decode_atlas


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'.local/generated-area-review-src'
EXPECTED = frozenset({(109, 49), (210, 65), (210, 86), (141, 110), (200, 110),
                      (119, 104), (119, 105)})


class MemorySource:
    def __init__(self, values):
        self.values = values

    def read(self, name):
        return self.values[name]


class OccludedRoutesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = json.loads((ROOT/'tools/hoenn/fixtures/atlas-cave-underlay-171.json').read_bytes())
        header = zlib.decompress(base64.b64decode(fixture['header_zlib_base64']))
        assert hashlib.sha256(header).hexdigest() == fixture['header_sha256']
        assert fixture['branch_evidence_sha256'] == BRANCH_EVIDENCE_SHA256
        cls.original = {HEADER: header, MARKER: json.dumps(fixture['marker']).encode()}
        cls.truth = decode_atlas(header.decode())
        cls.pixels, cls.proof = extract_occluded_routes(MemorySource(cls.original), cls.truth)

    def test_exact_historical_underlay_and_immutable_art(self):
        self.assertEqual(self.pixels, EXPECTED)
        self.assertEqual(self.proof['counts']['recovered'], 7)
        self.assertEqual(self.proof['counts']['occluded_branches'], 6)
        self.assertEqual(self.proof['art_sha256_before'], ART_SHA256)
        self.assertEqual(self.proof['art_sha256_after'], ART_SHA256)
        self.assertTrue(all(self.truth.pixel(p) in (0, 15) for p in self.pixels))
        self.assertEqual(extract_occluded_routes(MemorySource(self.original))[0], EXPECTED)

    def test_ocaso_keeps_the_authenticated_sea_endpoint_not_the_requested_land(self):
        row = next(r for r in self.proof['branches'] if r['theme'] == 'Ocaso')
        self.assertEqual(row['requested_endpoint'], [140, 111])
        self.assertEqual(row['painted_endpoint'], [141, 111])
        self.assertTrue(row['historical_endpoint_normalized'])
        self.assertNotIn((140, 111), self.truth.blue_pixels | self.pixels)
        self.assertEqual(row['hidden_pixels'][0]['atlas'], [141, 110])

    def test_branch_order_and_every_branch_field_are_authenticated(self):
        for field, value in [('polyline', [[140, 100], [140, 111]]),
                             ('position', [141, 110]), ('map', 'InventedCave')]:
            changed = dict(self.original)
            marker = json.loads(changed[MARKER])
            marker['branches'][6][field] = value
            changed[MARKER] = json.dumps(marker).encode()
            with self.assertRaisesRegex(ValueError, 'branch marker changed'):
                extract_occluded_routes(MemorySource(changed))
        changed = dict(self.original)
        marker = json.loads(changed[MARKER])
        marker['branches'].reverse()
        changed[MARKER] = json.dumps(marker).encode()
        with self.assertRaisesRegex(ValueError, 'branch marker changed'):
            extract_occluded_routes(MemorySource(changed))

    def test_marker_serialization_does_not_change_authenticated_branches(self):
        changed = dict(self.original)
        marker = json.loads(changed[MARKER])
        changed[MARKER] = json.dumps(marker, sort_keys=True, indent=4).encode()
        self.assertEqual(extract_occluded_routes(MemorySource(changed))[0], EXPECTED)

    def test_actual_restored_source_matches_portable_historical_fixture(self):
        if not (SOURCE/HEADER).exists():
            self.skipTest('Optional full source171 reconstruction is not installed')
        original = {p: (SOURCE/p).read_bytes() for p in (HEADER, MARKER)}
        pixels, proof = extract_occluded_routes(MemorySource(original))
        self.assertEqual(pixels, EXPECTED)
        self.assertEqual(proof['branches'], self.proof['branches'])
        self.assertEqual({p: (SOURCE/p).read_bytes() for p in original}, original)

    def test_concurrent_input_replacement_is_rejected(self):
        reads = 0
        class ChangingSource:
            def read(inner, name):
                nonlocal reads
                reads += 1
                return self.original[name] + (b' ' if reads > 2 else b'')
        with self.assertRaisesRegex(ValueError, 'changed during extraction'):
            extract_occluded_routes(ChangingSource())

    def test_recorded_paths_and_physical_stitches_have_no_invented_ocean(self):
        routes = self.truth.blue_pixels | self.pixels
        water = rasterize(routes)
        for branch in self.proof['branches']:
            path = list(map(tuple, branch['literal_painted_path']))
            self.assertTrue(set(path) <= routes)
            self.assertTrue(all(abs(a[0]-b[0])+abs(a[1]-b[1]) == 1
                                for a, b in zip(path, path[1:])))
            self.assertEqual([r['atlas'] for r in branch['hidden_pixels']],
                             [list(p) for p in path if p in self.pixels])
        for edge in self.proof['physical_stitches']:
            self.assertEqual(len(edge['game_tile_pairs']), 6)
            for a, b in edge['game_tile_pairs']:
                self.assertIn(tuple(a), water)
                self.assertIn(tuple(b), water)
                self.assertEqual(abs(a[0]-b[0])+abs(a[1]-b[1]), 1)
        self.assertEqual(len(self.proof['atlas_component_sizes_before']), 15)
        self.assertEqual(len(self.proof['atlas_component_sizes_after']), 10)
        self.assertFalse(self.proof['arbitrary_ocean_added'])
        self.assertFalse(self.proof['native_validated'])

    def test_changed_marker_cannot_authorize_an_ocean_shortcut(self):
        changed = dict(self.original)
        marker = json.loads(changed[MARKER])
        marker['branches'][0]['polyline'] = [[109, 49], [109, 48], [110, 48]]
        changed[MARKER] = json.dumps(marker).encode()
        with self.assertRaisesRegex(ValueError, 'marker changed'):
            extract_occluded_routes(MemorySource(changed))

    def test_all_four_art_arrays_are_pinned(self):
        for symbol in ART_SHA256:
            changed = dict(self.original)
            header = changed[HEADER].decode()
            import re
            pattern = r'(\b'+symbol+r'\s*\[\s*\]\s*=\s*\{\s*)(0x[0-9a-fA-F]+|\d+)'
            changed[HEADER] = re.sub(pattern, lambda m: m[1]+str(int(m[2], 0)^1),
                                     header, count=1).encode()
            self.assertNotEqual(changed[HEADER], self.original[HEADER], symbol)
            with self.assertRaises(ValueError, msg=symbol):
                extract_occluded_routes(MemorySource(changed))

    def test_changed_paint_order_implementation_is_rejected(self):
        with patch('atlas_surf_occluded_routes.DRAW_SOURCES',
                   {'tools/hoenn/prepare_surf_review.py': '0'*64}):
            with self.assertRaisesRegex(ValueError, 'paint implementation changed'):
                extract_occluded_routes(MemorySource(self.original))

    def test_native_cave_is_preserved_when_an_authored_line_crosses_its_body(self):
        row = dict(name='Ocaso', kind='cave', fixed_atlas=[140,110],
                   origin=[1128,880],width=8,height=8,water_runs=[],
                   stamp_sha256='a'*64,reserved_water_policy='native',
                   native_water_evidence=dict(parent_map='JourneyOcasoApproach',
                       source_rect=[5,36,15,15],stamp_sha256='a'*64))
        original = deepcopy(row)
        records = record_native_obstructions([row], self.truth.blue_pixels | self.pixels,
                                             self.pixels, self.proof)
        self.assertTrue(records)
        self.assertFalse(records[0]['passage_approved'])
        self.assertTrue(records[0]['native_terrain_preserved'])
        evidence = row.pop('route_obstruction_evidence')
        self.assertEqual(row, original)
        self.assertEqual(evidence['cave'], 'JourneyCaveOcaso')
        self.assertTrue(all((x//8,y//8) == (141,110)
                            for x,y in evidence['blocked_global_tiles']))
        for field,value in [('kind','ordinary'),('fixed_atlas',[0,0])]:
            changed = dict(original, **{field:value})
            with self.assertRaisesRegex(ValueError, 'unauthenticated native scenery'):
                record_native_obstructions([changed], self.truth.blue_pixels | self.pixels,
                                           self.pixels, self.proof)

    def test_preview_cannot_materialize_an_unreviewed_save_identity_change(self):
        from prepare_atlas_surf_layout import prepare
        with self.assertRaisesRegex(ValueError, 'cannot materialize'):
            prepare(SOURCE, preview_occluded_routes=True)


if __name__ == '__main__':
    unittest.main()
