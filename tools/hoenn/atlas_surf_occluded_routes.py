"""Recover only route ink literally painted before the fixed cave glyphs.

The surf-review marker records the authored polylines.  Its pinned generator
paints every returned ocean path blue, then paints the four-pixel cave arch.
Intersecting those recorded lines with that exact arch recovers the underlay;
there is no search for a nearer route, interpolation, or new ocean corridor.
This is source evidence, not a ROM traversal or global connectivity certificate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from atlas_surf_geometry import CORRIDOR_WIDTH, SCALE, rasterize
from atlas_surf_truth import decode_atlas, orthogonal_line


ROOT = Path(__file__).resolve().parents[2]
HEADER = 'src/data/journey_world_map.h'
MARKER = '.journey-surf-review'
MARKER_SHA256 = '28b88af229a887b4d0b7c8b0c619a3560193a24ebbc7b9bcf943baf68506da05'
# The complete marker also binds unrelated, intermediate inventories. The
# restored final source is exact, but this historical marker's raw SHA differs.
# Pin the *entire* branch records independently to the published source proof;
# do not approve a newly observed marker hash or assume its provenance.
BRANCHES_SHA256 = 'cc945342ce5a61a02a8f081f49e576892afa218c7de5ce94787d10845e20adcc'
BRANCH_EVIDENCE = 'mods/hoenn/surf-review-validation/source.json'
BRANCH_EVIDENCE_SHA256 = 'f9cc441f0c7580f512d3483ae559cd807dbbf92eb6460f22e501ea2c6af0e04e'
# route() normalizes its requested endpoint to historical sea before painting.
# Ocaso's requested (140,111) was not sea; its recorded line ends at (141,111).
# This authentic endpoint is not permission to extend the line to (140,111).
NORMALIZED_ENDPOINTS = {'Ocaso': (141, 111)}
DRAW_SOURCES = {
    'tools/hoenn/prepare_surf_review.py':
        'c3ba240d54f0311b4198145e1149a9e78b4018eccc8185be124405691e3cfdba',
    'tools/hoenn/prepare_connected_sea_chart.py':
        'a77361fb3d2aca788a762bad49a46d6260a59644af518ee7c654e8ea18208b72',
}
ART_SHA256 = {
    'sWorldTiles': '09e5334176c31cc5c6fa30ed9a2e46b6f90df524ebfa0a92b3f2403742fa7b9f',
    'sWorldTilemap': 'ae2c327dad6d9ab1a1897369b793969e1229d18f45d0add22a79e4ba5a7a3196',
    'sWorldPalette': 'da38567f7f701d0d76c5c53ef00407fc6eeb75632efdf6121590b9b2f7aca73a',
    'sWorldDetailPixels': 'a7a9ce35ca044ee2df75bd49878a79536fa42f05fb1cdb0cd0593593db3b58f2',
}


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _ordered(points):
    return sorted(points, key=lambda p: (p[1], p[0]))


def _component_sizes(points):
    unseen = set(points)
    sizes = []
    while unseen:
        todo = [unseen.pop()]
        size = 0
        while todo:
            x, y = todo.pop()
            size += 1
            for q in ((x-1, y), (x+1, y), (x, y-1), (x, y+1)):
                if q in unseen:
                    unseen.remove(q)
                    todo.append(q)
        sizes.append(size)
    return sorted(sizes, reverse=True)


def _stitches(hidden, route):
    """Witness six actual adjacent game-tile pairs across each restored edge."""
    water = rasterize(route)
    result = []
    for p in _ordered(hidden):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = p[0]+dx, p[1]+dy
            if q not in route or (q in hidden and q < p):
                continue
            pairs = []
            margin = (SCALE-CORRIDOR_WIDTH)//2
            for k in range(margin, margin+CORRIDOR_WIDTH):
                if dx:
                    a = p[0]*SCALE+(SCALE-1 if dx > 0 else 0), p[1]*SCALE+k
                else:
                    a = p[0]*SCALE+k, p[1]*SCALE+(SCALE-1 if dy > 0 else 0)
                b = a[0]+dx, a[1]+dy
                if a not in water or b not in water:
                    raise ValueError(('Recovered line has no physical stitch', p, q))
                pairs.append([list(a), list(b)])
            result.append(dict(atlas_edge=[list(p), list(q)], game_tile_pairs=pairs))
    return result


def record_native_obstructions(reservations, route_pixels, recovered_pixels, proof):
    """Record blocked cave terrain in a *preview*, without opening any cell.

    An authored line under a small atlas glyph does not permit erasing the
    much larger native cave. The real source graph must decide whether its
    existing water fringe provides a path around that intact footprint.
    """
    water = rasterize(route_pixels)
    added = water - rasterize(set(route_pixels) - set(recovered_pixels))
    records = []
    for row in reservations:
        if row.get('reserved_water_policy') != 'native':
            continue
        ox,oy = row['origin']
        expected = {(ox+x,oy+y) for y,a,b in row['water_runs'] for x in range(a,b)}
        missing = {p for p in added if ox <= p[0] < ox+row['width']
                   and oy <= p[1] < oy+row['height']} - expected
        if not missing:
            continue
        evidence = row.get('native_water_evidence', {})
        branch = next((b for b in proof['branches']
                       if b['fixed_atlas'] == row.get('fixed_atlas')), None)
        if (row.get('kind') != 'cave' or branch is None
                or evidence.get('stamp_sha256') != row.get('stamp_sha256')
                or evidence.get('parent_map') != branch['surface'] or not evidence.get('source_rect')):
            raise ValueError(('Recovered route intersects unauthenticated native scenery', row['name']))
        record = dict(kind='authenticated-cave-underlay-native-obstruction',
                      cave=branch['cave'],fixed_atlas=branch['fixed_atlas'],
                      stamp_sha256=row['stamp_sha256'],native_water_evidence=evidence,
                      blocked_global_tiles=[list(p) for p in _ordered(missing)],
                      native_terrain_preserved=True,passage_approved=False,
                      prior_obstruction_evidence=row.get('route_obstruction_evidence'))
        row['route_obstruction_evidence'] = record
        records.append(dict(reservation=row['name'],**record))
    return records


def extract_occluded_routes(source, truth=None):
    """Return ``(frozenset[(x,y)], provenance)`` without modifying any source.

    ``source`` may be a source directory or the preparer's tracked ``Source``.
    Passing its decoded ``truth`` additionally checks that the caller is using
    this same immutable artwork.  The returned set includes all seven proven
    pixels, even if a caller already restored one of them for another feature.
    """
    if hasattr(source, 'read'):
        read = source.read
    else:
        directory = Path(source)
        read = lambda path: (directory/path).read_bytes()
    raw_header, raw_marker = read(HEADER), read(MARKER)
    decoded = decode_atlas(raw_header.decode())
    if dict(decoded.array_sha256) != ART_SHA256:
        raise ValueError('Immutable atlas art differs from the authenticated cave underlay')
    if truth is not None and (truth.indices != decoded.indices
                              or dict(truth.array_sha256) != ART_SHA256):
        raise ValueError('Caller atlas differs from the authenticated cave underlay')
    marker = json.loads(raw_marker)
    branch_hash = _sha(json.dumps(marker['branches'], sort_keys=True,
                                 separators=(',', ':')).encode())
    if branch_hash != BRANCHES_SHA256:
        raise ValueError('Surf-review branch marker changed; hidden routes need new evidence')
    draw_bytes = {path: (ROOT/path).read_bytes() for path in DRAW_SOURCES}
    if any(_sha(draw_bytes[path]) != expected for path, expected in DRAW_SOURCES.items()):
        raise ValueError('Historical route/glyph paint implementation changed')
    if marker['layer'] != 'surf-review':
        raise ValueError('Cave underlay marker has the wrong layer')
    hidden = set()
    branches = []
    for row in marker['branches']:
        path = []
        for first, last in zip(row['polyline'], row['polyline'][1:]):
            segment = orthogonal_line(tuple(first), tuple(last))
            path.extend(segment if not path else segment[1:])
        ax, ay = row['position']
        requested_endpoint = (ax, min(decoded.height-1, ay+1))
        painted_endpoint = NORMALIZED_ENDPOINTS.get(row['theme'], requested_endpoint)
        if (not path or path[0] != tuple(row['nearest_existing_ink'])
                or path[-1] != painted_endpoint):
            raise ValueError(('Recorded branch endpoints changed', row['theme']))
        if painted_endpoint != requested_endpoint:
            if (decoded.pixel(requested_endpoint) in (1, 2)
                    or decoded.pixel(painted_endpoint) != 2
                    or sum(abs(a-b) for a,b in zip(requested_endpoint,painted_endpoint)) != 1):
                raise ValueError(('Historical sea-normalized endpoint changed', row['theme']))
        glyph = {(ax, ay-1): 15, (ax-1, ay): 15, (ax, ay): 0, (ax+1, ay): 15}
        if any(decoded.pixel(p) != color for p, color in glyph.items()):
            raise ValueError(('Fixed cave arch changed', row['theme']))
        occluded = set(path) & glyph.keys()
        if any(decoded.pixel(p) != 2 for p in path if p not in occluded):
            raise ValueError(('Recorded branch has an unproven gap', row['theme']))
        hidden.update(occluded)
        branches.append(dict(theme=row['theme'], cave=row['map'],surface=row['surface'],
                             fixed_atlas=list(row['position']),
                             recorded_polyline=row['polyline'],
                             requested_endpoint=list(requested_endpoint),
                             painted_endpoint=list(painted_endpoint),
                             historical_endpoint_normalized=painted_endpoint != requested_endpoint,
                             literal_painted_path=[list(p) for p in path],
                             hidden_pixels=[dict(atlas=list(p), current_palette_index=decoded.pixel(p),
                                                 underlay_palette_index=2) for p in _ordered(occluded)],
                             visible_route_pixels=len(path)-len(occluded),
                             recorded_path_only=True))
    route = decoded.blue_pixels | hidden
    before = rasterize(decoded.blue_pixels)
    after = rasterize(route)
    report = dict(schema='atlas-surf-authenticated-occluded-routes/v1',
                  source_inputs_sha256={HEADER: _sha(raw_header), MARKER: _sha(raw_marker)},
                  branch_evidence=dict(path=BRANCH_EVIDENCE,sha256=BRANCH_EVIDENCE_SHA256,
                      canonical_branches_sha256=branch_hash,
                      historical_full_marker_sha256=MARKER_SHA256,
                      full_marker_bytes_match=_sha(raw_marker) == MARKER_SHA256),
                  repository_inputs_sha256=dict(DRAW_SOURCES),
                  art_sha256_before=dict(decoded.array_sha256),
                  branches=branches, recovered_pixels=[list(p) for p in _ordered(hidden)],
                  counts=dict(branches=len(branches), occluded_branches=sum(bool(r['hidden_pixels']) for r in branches),
                              visible_blue=len(decoded.blue_pixels), recovered=len(hidden),
                              combined_route=len(route), added_game_water_tiles=len(after-before)),
                  atlas_component_sizes_before=_component_sizes(decoded.blue_pixels),
                  atlas_component_sizes_after=_component_sizes(route),
                  physical_stitches=_stitches(hidden, route),
                  proof='Pinned surf-review polyline painted blue before its explicit gray/black arch',
                  current_nonblue_pixels_only=True, arbitrary_ocean_added=False,
                  pathfinding_used=False, nearest_point_used=False,
                  source_written=False, art_mutated=False,
                  native_validated=False, global_source_scc_validated=False,
                  limitations=['Only the seven literal cave-underlay pixels are authenticated.',
                               'Regional city and shipyard glyphs require separate native ownership evidence.',
                               'Physical stitched tile coordinates are source geometry, not ROM controller proof.'])
    # Re-read both inputs, detecting accidental writes or concurrent replacement.
    after_header, after_marker = read(HEADER), read(MARKER)
    if after_header != raw_header or after_marker != raw_marker:
        raise ValueError('Immutable cave underlay inputs changed during extraction')
    report['art_sha256_after'] = dict(decode_atlas(after_header.decode()).array_sha256)
    return frozenset(hidden), report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    _, evidence = extract_occluded_routes(args.source)
    args.output.write_text(json.dumps(evidence, indent=2)+'\n')
    print(json.dumps(evidence['counts'], sort_keys=True))
