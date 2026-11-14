"""Read the existing atlas without changing its art or guessing route ownership.

The blue route ink is authoritative.  Native ownership and icon exclusions need
explicit physical witnesses; missing witnesses are never inferred from a desired
count.  This module has no source-writing operation.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
import hashlib
import json
from pathlib import Path
import re
import struct
from typing import Iterable, Mapping

ATLAS_WIDTH = 224
ATLAS_HEIGHT = 112
ROUTE_INDEX = 2
OCEAN_INDEX = 1
ART_ARRAYS = ("sWorldTiles", "sWorldTilemap", "sWorldPalette", "sWorldDetailPixels")
Point = tuple[int, int]


def array_values(header: str, symbol: str) -> tuple[int, ...]:
    match = re.search(r"\b" + re.escape(symbol) + r"\s*\[\s*\]\s*=\s*\{([^}]+)\}", header)
    if not match:
        raise ValueError(f"Missing immutable atlas array: {symbol}")
    body = re.sub(r"/\*.*?\*/|//[^\n]*", "", match[1], flags=re.S)
    try:
        return tuple(int(token.strip(), 0) for token in body.split(",") if token.strip())
    except ValueError as error:
        raise ValueError(f"Non-literal value in {symbol}") from error


@dataclass(frozen=True)
class AtlasTruth:
    indices: tuple[int, ...]
    palette: tuple[int, ...]
    array_sha256: Mapping[str, str]
    header_sha256: str
    width: int = ATLAS_WIDTH
    height: int = ATLAS_HEIGHT

    def pixel(self, point: Point) -> int:
        x, y = point
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise ValueError(f"Atlas coordinate outside image: {point}")
        return self.indices[y * self.width + x]

    @cached_property
    def blue_pixels(self) -> frozenset[Point]:
        return frozenset((x, y) for y in range(self.height) for x in range(self.width)
                         if self.pixel((x, y)) == ROUTE_INDEX)


def decode_atlas(header: str) -> AtlasTruth:
    """Decode tile flips and palette banks as the native tilemap does."""
    arrays = {name: array_values(header, name) for name in ART_ARRAYS}
    tiles, tilemap, palette = (arrays[name] for name in ART_ARRAYS[:3])
    if len(tilemap) < 32 * 17:
        raise ValueError("Atlas tilemap is too short")
    pixels = []
    for y in range(ATLAS_HEIGHT):
        for x in range(ATLAS_WIDTH):
            entry = tilemap[(y // 8 + 3) * 32 + x // 8 + 1]
            local_x = 7 - x % 8 if entry & 0x400 else x % 8
            local_y = 7 - y % 8 if entry & 0x800 else y % 8
            offset = (entry & 1023) * 32 + local_y * 4 + local_x // 2
            if offset >= len(tiles):
                raise ValueError(f"Atlas references missing tile at {x},{y}")
            value = (tiles[offset] >> ((local_x % 2) * 4)) & 15
            index = (entry >> 12) * 16 + value
            if index >= len(palette):
                raise ValueError(f"Atlas references missing palette at {x},{y}")
            pixels.append(index)
    # Hash the actual little-endian ROM bytes, including detail art. These
    # identities match the historical art contract, independent of C whitespace.
    widths = {'sWorldTiles': 'B', 'sWorldTilemap': 'H',
              'sWorldPalette': 'H', 'sWorldDetailPixels': 'B'}
    hashes = {name: hashlib.sha256(struct.pack('<' + widths[name]*len(values), *values)).hexdigest()
              for name, values in arrays.items()}
    return AtlasTruth(tuple(pixels), palette, hashes, hashlib.sha256(header.encode()).hexdigest())


def read_atlas(source: Path) -> AtlasTruth:
    return decode_atlas((Path(source) / "src/data/journey_world_map.h").read_text())


def reference_blue_pixels(path: Path) -> frozenset[Point]:
    """Read the existing enlarged source render as a *reference*, not ROM proof.

    Require nearest-neighbor uniform blocks so annotations or a screenshot's
    player/cursor cannot silently become the reconstruction's atlas input.
    The actual source arrays must still be read with ``read_atlas`` and matched.
    """
    from PIL import Image
    with Image.open(path) as raw:
        image = raw.convert("RGB")
    factor = image.width // ATLAS_WIDTH
    if factor < 1 or image.size != (ATLAS_WIDTH * factor, ATLAS_HEIGHT * factor):
        raise ValueError("Reference is not an integer enlargement of the source atlas")
    colors = {(49, 106, 180), (48, 104, 176)}
    blue = set()
    for y in range(ATLAS_HEIGHT):
        for x in range(ATLAS_WIDTH):
            color = image.getpixel((x * factor, y * factor))
            if any(image.getpixel((x * factor + dx, y * factor + dy)) != color
                   for dy in range(factor) for dx in range(factor)):
                raise ValueError(f"Reference contains non-uniform source pixel at {x},{y}")
            if color in colors:
                blue.add((x, y))
    return frozenset(blue)


def _points(values: Iterable[Iterable[int]]) -> frozenset[Point]:
    result = set()
    for value in values:
        point = tuple(value)
        if len(point) != 2 or any(type(coordinate) is not int for coordinate in point):
            raise ValueError(f"Not an integer atlas coordinate: {point}")
        result.add(point)
    return frozenset(result)


def orthogonal_line(start: Point, end: Point) -> tuple[Point, ...]:
    if start[0] != end[0] and start[1] != end[1]:
        raise ValueError(f"Access must follow one atlas axis: {start}, {end}")
    dx = (end[0] > start[0]) - (end[0] < start[0])
    dy = (end[1] > start[1]) - (end[1] < start[1])
    return tuple((start[0] + dx * step, start[1] + dy * step)
                 for step in range(abs(end[0] - start[0]) + abs(end[1] - start[1]) + 1))


def classify_pixels(truth: AtlasTruth, *, native_witnesses: Mapping[Point, list[dict]],
                    icon_witnesses: Mapping[Point, dict], accesses: Iterable[dict] = ()) -> dict:
    """Return an exhaustive, disjoint classification backed by supplied evidence.

    Each native witness names a map and local tile and explicitly records the
    native projection and actual Surf trigger.  Callers must independently check
    those records against source/ROM; this function only checks their structure.
    Icon evidence must identify its owner and explain the visual exclusion.
    """
    native = _points(native_witnesses)
    icons = _points(icon_witnesses)
    blue = truth.blue_pixels
    if native & icons:
        raise ValueError(f"Native route/icon overlap: {sorted(native & icons)}")
    if not (native | icons) <= blue:
        raise ValueError(f"Ownership given for pixels without blue ink: {sorted((native | icons) - blue)}")
    for point, records in native_witnesses.items():
        if not records:
            raise ValueError(f"No physical witness for native route {point}")
        for record in records:
            if not record.get("map") or len(record.get("tile", [])) != 2:
                raise ValueError(f"Missing native map/tile at {point}")
            if tuple(record.get("atlas", [])) != point or record.get("surfable") is not True:
                raise ValueError(f"Witness does not prove native route {point}")
    for point, record in icon_witnesses.items():
        if not record.get("owner") or not record.get("reason"):
            raise ValueError(f"Icon exclusion has no evidence at {point}")
    generated = blue - native - icons
    access_records = []
    access_pixels = set()
    for access in accesses:
        start, end = tuple(access["start"]), tuple(access["end"])
        points = orthogonal_line(start, end)
        if not access.get("name") or not access.get("reason"):
            raise ValueError("Short access needs a name and source justification")
        if not (set(points) & (blue - icons)):
            raise ValueError(f"Access is detached from atlas route ink: {access['name']}")
        endpoint_icon = access.get("endpoint_icon")
        if endpoint_icon:
            if (tuple(endpoint_icon.get("position", [])) != end or not endpoint_icon.get("owner")
                    or not endpoint_icon.get("reason") or endpoint_icon.get("palette_index") != truth.pixel(end)):
                raise ValueError(f"Access endpoint icon has no matching evidence: {access['name']}")
        for point in points:
            if truth.pixel(point) not in (OCEAN_INDEX, ROUTE_INDEX) and not (point == end and endpoint_icon):
                raise ValueError(f"Access crosses land or an icon: {point}")
            if point in icons:
                raise ValueError(f"Access crosses excluded port icon: {point}")
        access_pixels.update(set(points) - blue)
        access_records.append({**access, "pixels": [list(point) for point in points]})
    order = lambda points: [list(point) for point in sorted(points, key=lambda p: (p[1], p[0]))]
    return dict(atlas_size=[truth.width, truth.height], art_sha256=dict(truth.array_sha256),
                counts=dict(blue=len(blue), generated=len(generated), native=len(native), icons=len(icons),
                            access=len(access_pixels)),
                generated_pixels=order(generated), native_pixels=order(native), icon_pixels=order(icons),
                native_witnesses=[dict(atlas=list(point), witnesses=records)
                                  for point, records in sorted(native_witnesses.items())],
                icon_witnesses=[dict(atlas=list(point), **record)
                                for point, record in sorted(icon_witnesses.items())],
                access_pixels=order(access_pixels), accesses=access_records,
                complete_blue_classification=True, art_mutated=False,
                native_witnesses_require_independent_source_or_rom_verification=True)
