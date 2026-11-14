"""Lay out route ink in one physical coordinate system, without GPS grids.

Coordinates are global game tiles.  Six-tile corridors occupy an eight-tile
atlas pixel and connect only to its four immediate route neighbors.  Map
partitioning changes storage, never physical distance or heading.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Iterable

Point = tuple[int, int]
SCALE = 8
CORRIDOR_WIDTH = 6
CHUNK_TILES = 32
MAPS_PER_GROUP = 100


def atlas_position(origin: Point, tile: Point, scale: int = SCALE) -> Point:
    """Use floor division, including negative local coordinates at map borders."""
    return ((origin[0] + tile[0]) // scale, (origin[1] + tile[1]) // scale)


def rasterize(pixels: Iterable[Point], *, scale: int = SCALE,
              corridor_width: int = CORRIDOR_WIDTH) -> frozenset[Point]:
    if scale <= 0 or corridor_width <= 0 or corridor_width > scale:
        raise ValueError("Invalid atlas scale/corridor width")
    if (scale - corridor_width) % 2:
        raise ValueError("Corridor must be centered on whole game tiles")
    pixels = frozenset(tuple(point) for point in pixels)
    if any(len(point) != 2 or any(type(c) is not int for c in point) for point in pixels):
        raise ValueError("Route coordinates must be integer pairs")
    margin = (scale - corridor_width) // 2
    water = set()
    for x, y in pixels:
        left, top = x * scale + margin, y * scale + margin
        for yy in range(top, top + corridor_width):
            water.update((xx, yy) for xx in range(left, left + corridor_width))
        # Fill the two-tile gap between consecutive six-tile footprints.
        if (x + 1, y) in pixels:
            for yy in range(top, top + corridor_width):
                water.update((xx, yy) for xx in range(left + corridor_width, (x + 1) * scale + margin))
        if (x, y + 1) in pixels:
            for yy in range(top + corridor_width, (y + 1) * scale + margin):
                water.update((xx, yy) for xx in range(left, left + corridor_width))
    return frozenset(water)


def _runs(water: Iterable[Point], origin: Point) -> list[list[int]]:
    rows = defaultdict(list)
    for x, y in water:
        rows[y - origin[1]].append(x - origin[0])
    runs = []
    for y, values in sorted(rows.items()):
        values.sort()
        start = previous = values[0]
        for value in values[1:]:
            if value != previous + 1:
                runs.append([y, start, previous + 1])
                start = value
            previous = value
        runs.append([y, start, previous + 1])
    return runs


def plan_geometry(pixels: Iterable[Point], *, scale: int = SCALE,
                  corridor_width: int = CORRIDOR_WIDTH, chunk_tiles: int = CHUNK_TILES,
                  maps_per_group: int = MAPS_PER_GROUP, prefix: str = "JourneyAtlasSea") -> dict:
    if chunk_tiles < scale or chunk_tiles > 127 or chunk_tiles % scale:
        raise ValueError("Chunks must fit native signed coordinates and divide atlas pixels evenly")
    if not 1 <= maps_per_group <= 100:
        raise ValueError("Groups must contain at most 100 maps (WarpData mapNum is signed)")
    pixels = frozenset(tuple(point) for point in pixels)
    water = rasterize(pixels, scale=scale, corridor_width=corridor_width)
    buckets = defaultdict(set)
    for x, y in water:
        buckets[(x // chunk_tiles, y // chunk_tiles)].add((x, y))
    chunks, lookup = [], {}
    for number, (cell, cells) in enumerate(sorted(buckets.items(), key=lambda entry: (entry[0][1], entry[0][0]))):
        # Keep one tile for the complete perimeter where the grid cell permits
        # it.  Water crossing a grid boundary remains exactly on both edges.
        cx, cy = cell
        x0 = max(cx * chunk_tiles, min(x for x, _ in cells) - 1)
        y0 = max(cy * chunk_tiles, min(y for _, y in cells) - 1)
        x1 = min((cx + 1) * chunk_tiles, max(x for x, _ in cells) + 2)
        y1 = min((cy + 1) * chunk_tiles, max(y for _, y in cells) + 2)
        name = f"{prefix}{number:03}"
        chunk = dict(name=name, id="MAP_" + name.upper(), group=f"JourneyAtlasSeas{number // maps_per_group}",
                     number=number % maps_per_group, origin=[x0, y0], width=x1-x0, height=y1-y0,
                     cell=[cx, cy], water_runs=_runs(cells, (x0, y0)), connections=[])
        chunks.append(chunk)
        lookup[cell] = chunk
    for chunk in chunks:
        cx, cy = chunk["cell"]
        cells = buckets[(cx, cy)]
        for direction, dx, dy in (("right", 1, 0), ("down", 0, 1), ("left", -1, 0), ("up", 0, -1)):
            other = lookup.get((cx + dx, cy + dy))
            if other is None:
                continue
            if not any((x + dx, y + dy) in buckets[(cx + dx, cy + dy)] for x, y in cells):
                continue
            axis = 1 if dx else 0
            chunk["connections"].append(dict(direction=direction,
                                               offset=other["origin"][axis]-chunk["origin"][axis],
                                               map=other["id"]))
    return dict(schema="atlas-surf-geometry-v1", scale=scale, corridor_width=corridor_width,
                chunk_tiles=chunk_tiles, maps_per_group=maps_per_group,
                route_pixels=[list(point) for point in sorted(pixels, key=lambda p: (p[1], p[0]))],
                water_tiles=len(water), chunks=chunks,
                map_count=len(chunks), group_count=(len(chunks)+maps_per_group-1)//maps_per_group,
                affine_projection="floor((origin_global_tile + local_tile) / scale)",
                art_changed=False, per_cell_gps_arrays=False)


def chunk_water(chunk: dict) -> frozenset[Point]:
    """Expand local runs, for source writers and independently frozen evidence."""
    return frozenset((x, y) for y, start, end in chunk["water_runs"] for x in range(start, end))
