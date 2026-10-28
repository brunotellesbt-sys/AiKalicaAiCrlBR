"""Inspect static access data of generated caves and non-gym interiors.

This is deliberately a source-only screen, not an emulator certificate. The
optimistic graph ignores elevation and water mode: a target outside it cannot
be reached by ordinary adjacent movement, while membership alone does not prove
Surf, stair, door animation, state-dependent barrier, or script behavior.
"""
import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
import re
import struct


DECORATIVE_BOATS = {'OBJ_EVENT_GFX_SS_TIDAL', 'OBJ_EVENT_GFX_MR_BRINEYS_BOAT'}
CAGE_PRISONERS = {('JourneyGalacticHall', 6, 5),
                  ('JourneyGalacticHall', 24, 5),
                  ('JourneyGalacticHall', 15, 5)}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def adjacent(point):
    x, y = point
    return ((x-1, y), (x+1, y), (x, y-1), (x, y+1))


def audit(source):
    source = Path(source)
    acquired = json.loads((source / '.source-acquired.json').read_text())['sha256']
    layouts = {row['id']: row for row in json.loads(
        (source / 'data/layouts/layouts.json').read_text())['layouts']}
    maps = {}
    for file in (source / 'data/maps').glob('*/map.json'):
        row = json.loads(file.read_text())
        maps[row['id']] = (file.parent.name, row)
    # Bedroom returns retain the native house ID. With that home selected,
    # JourneyFamilyHomeHeader replaces its header with the expanded living
    # room, whose warp table includes the bedroom stair. Resolve this explicit
    # conditional alias rather than diagnosing its native house table alone.
    family_aliases = {}
    table = source/'include/journey_family_homes.h'
    runtime = source/'src/journey_family.c'
    if table.exists() and runtime.exists():
        implementation = runtime.read_text()
        assert 'JourneyFamilyHomeHeader' in implementation
        assert 'home->originalMap' in implementation and 'home->livingMap' in implementation
        for original, living, bedroom in re.findall(
                r'\{(MAP_\w+),\s*(MAP_\w+),\s*(MAP_\w+),', table.read_text()):
            if original != living:
                assert living in maps and bedroom in maps
                family_aliases[(bedroom, original)] = living
    results, confirmed, review = [], [], []
    cache = {}

    def terrain(mapping):
        layout = layouts[mapping['layout']]
        file = layout['blockdata_filepath']
        if file not in cache:
            raw = (source / file).read_bytes()
            width, height = layout['width'], layout['height']
            assert len(raw) == width*height*2
            cache[file] = (layout, struct.unpack('<'+'H'*(width*height), raw))
        return cache[file]

    for name, mapping in sorted(maps.values()):
        if f'data/maps/{name}/map.json' in acquired or 'Gym' in name:
            continue
        if mapping['map_type'] not in ('MAP_TYPE_UNDERGROUND', 'MAP_TYPE_INDOOR'):
            continue
        layout, words = terrain(mapping)
        width, height = layout['width'], layout['height']
        free = {(index % width, index // width) for index, word in enumerate(words)
                if word & 0xC00 == 0}
        seeds, warps = set(), []
        for index, warp in enumerate(mapping['warp_events']):
            point = warp['x'], warp['y']
            valid = 0 <= point[0] < width and 0 <= point[1] < height
            row = dict(index=index, position=list(point), in_bounds=valid)
            if not valid:
                confirmed.append(dict(map=name, kind='warp_outside_map', **row))
                warps.append(row)
                continue
            word = words[point[1]*width+point[0]]
            row['block'] = f'0x{word:04X}'
            if point in free:
                seeds.add(point)
                row['graph_seed'] = list(point)
            elif (point[0], point[1]+1) in free:
                # Native exterior door warps can be solid on their origin
                # cell; the landing animation steps to the tile below it.
                seeds.add((point[0], point[1]+1))
                row['graph_seed'] = [point[0], point[1]+1]
                row['solid_warp_has_lower_floor'] = True
            else:
                row['solid_or_isolated_warp_requires_runtime_review'] = True
            target_id, target_index = warp['dest_map'], str(warp['dest_warp_id'])
            row.update(destination_map_id=target_id, destination_warp_id=target_index)
            if target_id in maps and target_index.isdecimal():
                target_name, target = maps[target_id]
                conditional = family_aliases.get((mapping['id'], target_id))
                if conditional:
                    target_name, target = maps[conditional]
                    row.update(conditional_destination_header='JourneyFamilyHomeHeader',
                               requires_matching_selected_family_home=True,
                               effective_destination_map_id=conditional,
                               native_house_header_is_not_the_selected_home_header=True)
                target_index = int(target_index)
                valid_target = target_index < len(target['warp_events'])
                row['static_destination_index_valid'] = valid_target
                if not valid_target:
                    confirmed.append(dict(map=name, kind='invalid_destination_warp', **row))
                else:
                    target_warp = target['warp_events'][target_index]
                    target_layout, target_words = terrain(target)
                    x, y = target_warp['x'], target_warp['y']
                    valid_point = 0 <= x < target_layout['width'] and 0 <= y < target_layout['height']
                    row.update(destination_map=target_name,
                               destination_position=[x, y],
                               static_destination_in_bounds=valid_point)
                    if not valid_point:
                        confirmed.append(dict(map=name, kind='destination_outside_map', **row))
                    else:
                        row['destination_block'] = f'0x{target_words[y*target_layout["width"]+x]:04X}'
            else:
                row['dynamic_or_script_destination_not_certified'] = True
            warps.append(row)
        reached, queue = set(seeds), deque(seeds)
        while queue:
            point = queue.popleft()
            for neighbor in adjacent(point):
                if neighbor in free and neighbor not in reached:
                    reached.add(neighbor)
                    queue.append(neighbor)
        objects = []
        for index, event in enumerate(mapping['object_events'], 1):
            point = event['x'], event['y']
            valid = 0 <= point[0] < width and 0 <= point[1] < height
            reachable = any(neighbor in reached for neighbor in adjacent(point))
            row = dict(local_index=index, position=list(point), in_bounds=valid,
                       script=event['script'], graphics=event['graphics_id'],
                       adjacent_floor_in_optimistic_component=reachable)
            if not valid:
                confirmed.append(dict(map=name, kind='object_outside_map', **row))
            elif not seeds:
                row['excluded_from_static_access_claim'] = 'scripted entry has no static warp'
            elif event['script'] in ('0', '0x0'):
                row['excluded_from_static_access_claim'] = 'non-interactive scenery'
            elif event['graphics_id'] in DECORATIVE_BOATS:
                row['excluded_from_static_access_claim'] = 'decorative waterborne boat; captain is separate'
            elif (name, *point) in CAGE_PRISONERS:
                row['excluded_from_static_access_claim'] = 'intentional prison barrier before Galactic state 4'
            elif not reachable:
                review.append(dict(map=name, kind='interaction_has_no_optimistic_floor_path', **row))
            objects.append(row)
        results.append(dict(map=name, map_type=mapping['map_type'], dimensions=[width, height],
                            map_sha256=sha(source / f'data/maps/{name}/map.json'),
                            blockdata_sha256=sha(source / layout['blockdata_filepath']),
                            collision_zero_cells=len(free), optimistic_reached_cells=len(reached),
                            graph_seeds=sorted(map(list, seeds)), warps=warps, objects=objects))
    return dict(kind='generated-cave-static-access-screen', source_only=True,
                native_movement_validated=False, compiled_rom_sha256=sha(source/'pokeemerald.gba'),
                scope='Created indoor/underground map headers absent from the acquired source, excluding gyms',
                maps_checked=len(results), warps_checked=sum(len(row['warps']) for row in results),
                objects_checked=sum(len(row['objects']) for row in results),
                underground_maps_checked=sum(row['map_type']=='MAP_TYPE_UNDERGROUND' for row in results),
                confirmed_invalid_data=confirmed, access_review_candidates=review, maps=results,
                limitations=['Collision graph ignores elevation, water mode, NPC occupancy and scripted changes.',
                             'A solid door warp or non-reciprocal family-home destination can be intentional.',
                             'Native controller tests remain necessary for Surf landings, stairs, doors and barriers.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    result = audit(options.source)
    options.output.parent.mkdir(parents=True, exist_ok=True)
    options.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key:result[key] for key in ['maps_checked','warps_checked','objects_checked',
          'underground_maps_checked','confirmed_invalid_data','access_review_candidates']}, indent=2))
