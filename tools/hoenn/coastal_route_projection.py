"""Repair only the seven cleared coasts' GPS interiors, retaining shared edges.

A harmonic field removes the old nearest-anchor folds. A small linear program
keeps its closest feasible values under the native two-pixel step bound and
monotone progress on each principal central crossing. Connected border cells
are immutable constraints; unconnected outer cells use a free boundary.
"""
import re

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix, lil_matrix
from scipy.sparse.linalg import spsolve

ISLANDS = ('One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven')
TARGETS = tuple(island + 'Island_Harbor_Frlg' for island in ISLANDS)


def grids(header, maps):
    packed = np.array(list(map(int, re.search(r'sWorldNavigationPixels\[\] = \{([^}]+)', header)[1].split(','))), dtype=np.int32)
    by_id = {value['id']: name for name, value in maps.items()}
    result = {}
    for first, ident, width, height in re.findall(r'\{(\d+), \(MAP_GROUP\((\w+)\)<<8\)\|MAP_NUM\(\2\), (\d+), (\d+)\}', header):
        first, width, height = map(int, (first, width, height))
        values = packed[first:first + width * height].reshape(height, width)
        result[by_id[ident]] = dict(first=first, width=width, height=height,
                                   pixels=np.stack([values & 255, values >> 8], axis=2))
    return packed, result


def central_crossings(pixels):
    height, width, _ = pixels.shape
    result = []
    for direction, values in [('east', pixels[height // 2]), ('south', pixels[:, width // 2])]:
        displacement = values[-1] - values[0]
        axis = int(np.argmax(abs(displacement)))
        sign = int(np.sign(displacement[axis]))
        increments = np.diff(values[:, axis]) * sign
        result.append(dict(direction=direction, primary_axis='xy'[axis],
                           primary_direction=sign, pixels=values.tolist(),
                           backward_pixels=int(-np.minimum(increments, 0).sum()),
                           maximum_step=int(abs(np.diff(values, axis=0)).max()),
                           extent_pixels=int(abs(displacement[axis]))))
    return result


def repair(header, maps):
    packed, all_grids = grids(header, maps)
    original = packed.copy()
    by_id = {value['id']: name for name, value in maps.items()}
    records = []
    for name in TARGETS:
        grid = all_grids[name]
        old = grid['pixels']
        height, width, _ = old.shape
        assert (width, height) == (17, 13)
        count = width * height
        fixed = np.zeros((height, width), dtype=bool)
        for connection in maps[name]['connections']:
            direction, offset = connection['direction'], connection['offset']
            other = all_grids[by_id[connection['map']]]
            limit = height if direction in ('left', 'right') else width
            other_limit = other['height'] if direction in ('left', 'right') else other['width']
            for coordinate in range(max(0, offset), min(limit, offset + other_limit)):
                x, y = ((0 if direction == 'left' else width - 1), coordinate) if direction in ('left', 'right') else (coordinate, 0 if direction == 'up' else height - 1)
                fixed[y, x] = True
        # Solve the graph Laplacian with Dirichlet connected borders and free
        # unconnected borders. There is no snapping to a nearby atlas branch.
        free = np.flatnonzero(~fixed.ravel())
        free_index = {int(value): index for index, value in enumerate(free)}
        laplace = lil_matrix((len(free), len(free)))
        rhs = np.zeros((len(free), 2))
        edges = []
        flat = old.reshape(-1, 2)
        for y in range(height):
            for x in range(width):
                cell = y * width + x
                for xx, yy in ((x + 1, y), (x, y + 1)):
                    if xx < width and yy < height:
                        edges.append((cell, yy * width + xx))
                if cell not in free_index:
                    continue
                neighbors = [yy * width + xx for xx, yy in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))
                             if 0 <= xx < width and 0 <= yy < height]
                row = free_index[cell]
                laplace[row, row] = len(neighbors)
                for neighbor in neighbors:
                    if neighbor in free_index:
                        laplace[row, free_index[neighbor]] = -1
                    else:
                        rhs[row] += flat[neighbor]
        target = flat.astype(float).copy()
        target[free] = spsolve(laplace.tocsr(), rhs)
        lines = [list(range((height // 2) * width, (height // 2 + 1) * width)),
                 list(range(width // 2, count, width))]
        final = target.copy()
        for axis in (0, 1):
            rows, columns, weights, limits = [], [], [], []

            def constrain(terms, limit):
                row = len(limits)
                limits.append(limit)
                for column, weight in terms:
                    rows.append(row)
                    columns.append(column)
                    weights.append(weight)

            for here, there in edges:
                constrain(((here, 1), (there, -1)), 2)
                constrain(((there, 1), (here, -1)), 2)
            for line in lines:
                displacement = target[line[-1]] - target[line[0]]
                main = int(np.argmax(abs(displacement)))
                sign = int(np.sign(displacement[main]))
                if axis == main and sign:
                    for here, there in zip(line, line[1:]):
                        constrain(((here, sign), (there, -sign)), 0)
            for cell in range(count):
                constrain(((cell, 1), (count + cell, -1)), target[cell, axis])
                constrain(((cell, -1), (count + cell, -1)), -target[cell, axis])
            bounds = [(int(value[axis]), int(value[axis])) if locked else (0, 255)
                      for value, locked in zip(flat, fixed.ravel())] + [(0, None)] * count
            matrix = coo_matrix((weights, (rows, columns)), shape=(len(limits), count * 2)).tocsr()
            fit = linprog(np.r_[np.zeros(count), np.ones(count)], A_ub=matrix,
                          b_ub=limits, bounds=bounds, method='highs')
            assert fit.success, ('Inconsistent fixed coast GPS', name, axis, fit.message)
            final[:, axis] = fit.x[:count]
        # Nearest-integer rounding preserves integral step inequalities and
        # ordered coordinates. Tiny solver noise must not straddle a half.
        final = np.floor(final + 0.5 + 1e-9).astype(np.int32).reshape(height, width, 2)
        assert np.array_equal(final[fixed], old[fixed]), name
        maximum = max(int(abs(np.diff(final, axis=0)).max()), int(abs(np.diff(final, axis=1)).max()))
        assert maximum <= 2, (name, maximum)
        crossings = central_crossings(final)
        assert all(row['backward_pixels'] == 0 for row in crossings), (name, crossings)
        changed = np.any(final != old, axis=2)
        border = np.zeros((height, width), dtype=bool)
        border[[0, -1], :] = True
        border[:, [0, -1]] = True
        packed[grid['first']:grid['first'] + count] = (final[:, :, 0] | (final[:, :, 1] << 8)).ravel()
        records.append(dict(map=name, changed_tiles=int(changed.sum()),
                            changed_unconnected_border_tiles=int((changed & border & ~fixed).sum()),
                            fixed_connected_border_tiles=int(fixed.sum()),
                            all_connected_border_pixels_preserved=True,
                            maximum_neighbor_pixel_step=maximum,
                            before_central_crossings=central_crossings(old),
                            after_central_crossings=crossings,
                            before_pixels=old.tolist(), after_pixels=final.tolist()))
    changed_indices = set(map(int, np.flatnonzero(packed != original)))
    permitted = {index for name in TARGETS for index in range(all_grids[name]['first'],
                 all_grids[name]['first'] + all_grids[name]['width'] * all_grids[name]['height'])}
    assert changed_indices <= permitted
    result = re.sub(r'(sWorldNavigationPixels\[\] = \{)[^}]+',
                    lambda match: match[1] + ','.join(map(str, packed)), header)
    assert re.sub(r'sWorldNavigationPixels\[\] = \{[^}]+', '', result) == re.sub(r'sWorldNavigationPixels\[\] = \{[^}]+', '', header)
    return result, dict(method='harmonic-fixed-connected-borders-with-constrained-central-progress',
                        changed_tiles=len(changed_indices), changed_maps=list(TARGETS),
                        all_other_grids_bitwise_unchanged=True,
                        all_connected_border_pixels_preserved=True,
                        central_crossings_primary_axis_monotonic=True,
                        maximum_neighbor_pixel_step=max(row['maximum_neighbor_pixel_step'] for row in records),
                        no_nearest_band_snapping=True, maps=records)
