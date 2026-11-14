"""Contract tests for atlas ownership and physical geography, without ROM claims."""
from collections import deque
from pathlib import Path
import unittest

from atlas_surf_geometry import atlas_position, chunk_water, plan_geometry, rasterize
from atlas_surf_truth import (ART_ARRAYS, AtlasTruth, classify_pixels, decode_atlas,
                              reference_blue_pixels)

ROOT = Path(__file__).resolve().parents[2]


def fixture_truth(blue, land=()):
    pixels = [1] * (224 * 112)
    for x, y in blue:
        pixels[y * 224 + x] = 2
    for x, y in land:
        pixels[y * 224 + x] = 3
    return AtlasTruth(tuple(pixels), tuple(range(16)), {}, "fixture")


def components(points):
    todo = set(points)
    count = 0
    while todo:
        count += 1
        queue = deque([todo.pop()])
        while queue:
            x, y = queue.popleft()
            for neighbor in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if neighbor in todo:
                    todo.remove(neighbor)
                    queue.append(neighbor)
    return count


class TruthTests(unittest.TestCase):
    def test_decode_respects_native_tile_flips(self):
        tiles = [0] * 32
        tiles[0] = 0x21
        tilemap = [0] * 1024
        tilemap[3 * 32 + 1] = 0x400
        header = "\n".join(f"static unsigned short {name}[] = {{{','.join(map(str, values))}}};"
                           for name, values in zip(ART_ARRAYS, (tiles, tilemap, list(range(16)), [0])))
        truth = decode_atlas(header)
        self.assertEqual(truth.pixel((7, 0)), 1)
        self.assertEqual(truth.pixel((6, 0)), 2)
        self.assertEqual(truth.pixel((0, 0)), 0)
        self.assertEqual(set(truth.array_sha256), set(ART_ARRAYS))

    def test_classification_is_disjoint_and_exhaustive(self):
        truth = fixture_truth({(1,1),(2,1),(3,1)})
        native = {(1,1): [dict(map="Route105", tile=[4,5], atlas=[1,1], surfable=True)]}
        icon = {(3,1): dict(owner="Port", reason="Center of complete port icon")}
        result = classify_pixels(truth, native_witnesses=native, icon_witnesses=icon)
        self.assertEqual(result["counts"], dict(blue=3, generated=1, native=1, icons=1, access=0))
        self.assertEqual(result["generated_pixels"], [[2,1]])

    def test_native_requires_real_trigger_and_matching_position(self):
        truth = fixture_truth({(1,1)})
        with self.assertRaisesRegex(ValueError, "does not prove"):
            classify_pixels(truth, native_witnesses={(1,1): [dict(map="Route105",tile=[4,5],atlas=[1,1],surfable=False)]}, icon_witnesses={})
        with self.assertRaisesRegex(ValueError, "overlap"):
            classify_pixels(truth, native_witnesses={(1,1): []}, icon_witnesses={(1,1): {}})

    def test_short_access_must_remain_over_original_ocean(self):
        access = dict(name="coast", start=[1,1], end=[3,1], reason="Documented coastal tip")
        truth = fixture_truth({(1,1)})
        result = classify_pixels(truth, native_witnesses={}, icon_witnesses={}, accesses=[access])
        self.assertEqual(result["access_pixels"], [[2,1],[3,1]])
        with self.assertRaisesRegex(ValueError, "crosses land"):
            classify_pixels(fixture_truth({(1,1)}, land={(2,1)}), native_witnesses={}, icon_witnesses={}, accesses=[access])

    def test_only_witnessed_final_cave_icon_can_end_an_access(self):
        access = dict(name="cave",start=[1,1],end=[2,1],reason="Documented cave tip",
                      endpoint_icon=dict(position=[2,1],owner="Cave",palette_index=3,reason="Entrance icon"))
        truth = fixture_truth({(1,1)}, land={(2,1)})
        result = classify_pixels(truth,native_witnesses={},icon_witnesses={},accesses=[access])
        self.assertEqual(result["access_pixels"],[[2,1]])
        access["end"]=[3,1]
        with self.assertRaisesRegex(ValueError,"endpoint icon"):
            classify_pixels(truth,native_witnesses={},icon_witnesses={},accesses=[access])

    def test_published_source_render_contains_1529_blue_pixels(self):
        path = ROOT / "docs/design/coastal-closures/route-projection/unchanged-atlas-source.png"
        pixels = reference_blue_pixels(path)
        self.assertEqual(len(pixels), 1529)
        # This is an immutable-art reference assertion, not a claim that all
        # blue ink is a newly generated route or has a compiled passage.
        self.assertIn((134,55), pixels)
        # The old reported GPS(137,55) lies off the approved route ink.  It
        # cannot be used as a substitute for the source geometry's location.
        self.assertNotIn((137,55), pixels)


class GeometryTests(unittest.TestCase):
    def test_heading_and_distance_remain_physical_across_chunk_boundaries(self):
        plan = plan_geometry({(7,y) for y in range(1,12)})
        water = set()
        for chunk in plan["chunks"]:
            ox, oy = chunk["origin"]
            water.update((ox+x,oy+y) for x,y in chunk_water(chunk))
        for y in range(12, 88):
            self.assertIn((60,y), water)
            self.assertEqual(atlas_position((0,0),(60,y+1))[0], 7)
            self.assertEqual(atlas_position((0,0),(60,y+8))[1]-atlas_position((0,0),(60,y))[1], 1)
        self.assertEqual(components(water), 1)

    def test_diagonal_pixels_do_not_become_a_fake_route(self):
        self.assertEqual(components(rasterize({(1,1),(2,2)})), 2)
        self.assertEqual(components(rasterize({(1,1),(2,1),(2,2)})), 1)

    def test_chunk_partition_preserves_every_water_tile_once(self):
        pixels = {(x,4) for x in range(18)} | {(7,y) for y in range(15)}
        plan = plan_geometry(pixels)
        actual = []
        chunks = {c["id"]:c for c in plan["chunks"]}
        opposite = dict(up="down",down="up",left="right",right="left")
        for chunk in chunks.values():
            ox,oy = chunk["origin"]
            actual.extend((ox+x,oy+y) for x,y in chunk_water(chunk))
            self.assertLessEqual(chunk["width"],32)
            self.assertLessEqual(chunk["height"],32)
            for connection in chunk["connections"]:
                other = chunks[connection["map"]]
                self.assertIn(dict(direction=opposite[connection["direction"]],offset=-connection["offset"],map=chunk["id"]), other["connections"])
        self.assertEqual(len(actual), len(set(actual)))
        self.assertEqual(set(actual), rasterize(pixels))

    def test_signed_warp_map_number_is_never_over_99(self):
        # One separated route footprint per grid cell deliberately produces
        # more than two groups and exercises numbering at both boundaries.
        plan = plan_geometry({(4*x,4*y) for y in range(15) for x in range(15)})
        self.assertEqual(plan["map_count"],225)
        self.assertEqual(plan["group_count"],3)
        self.assertEqual(plan["chunks"][100]["number"],0)
        self.assertEqual(plan["chunks"][100]["group"],"JourneyAtlasSeas1")
        self.assertTrue(all(0<=chunk["number"]<100 for chunk in plan["chunks"]))
        with self.assertRaises(ValueError):
            plan_geometry({(0,0)}, maps_per_group=128)

    def test_negative_border_projection_uses_floor(self):
        self.assertEqual(atlas_position((8,8),(-9,-1)),(-1,0))


if __name__ == "__main__":
    unittest.main()
