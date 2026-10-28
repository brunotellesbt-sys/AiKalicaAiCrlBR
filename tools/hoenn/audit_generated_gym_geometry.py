"""Inspect the built eight-gym graphs; source analysis is not emulator proof."""
import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
import re
import struct

from PIL import Image


DIRECTIONS = {'RIGHT': (1, 0), 'LEFT': (-1, 0), 'DOWN': (0, 1), 'UP': (0, -1)}


def reached(floor, start, blocked=frozenset()):
    if start not in floor or start in blocked:
        return set()
    seen, pending = {start}, deque([start])
    while pending:
        x, y = pending.popleft()
        for point in ((x-1, y), (x+1, y), (x, y-1), (x, y+1)):
            if point in floor and point not in blocked and point not in seen:
                seen.add(point)
                pending.append(point)
    return seen


def audit(source):
    source = Path(source)
    gyms = json.loads((source / '.journey-extra-gyms').read_text())['gyms']
    layouts = {row['id']: row for row in json.loads((source / 'data/layouts/layouts.json').read_text())['layouts']}
    rooms, failures = [], []
    for gym in gyms:
        mapping = json.loads((source / f'data/maps/{gym["name"]}/map.json').read_text())
        layout = layouts[mapping['layout']]
        width, height = layout['width'], layout['height']
        raw = (source / layout['blockdata_filepath']).read_bytes()
        words = struct.unpack('<' + 'H' * (width * height), raw)
        floor = {(i % width, i // width) for i, value in enumerate(words) if not value & 0xC00}
        room = gym['room']
        start, target = tuple(room['entry']), tuple(room['leader_approach'])
        objects = mapping['object_events']
        occupied = {(o['x'], o['y']) for o in objects}
        students = [o for o in objects if o['trainer_type'] != 'TRAINER_TYPE_NONE' and o is not objects[0]]
        checks = dict(all_floor_one_component=reached(floor, start) == floor,
                      leader_approach_reachable=target in reached(floor, start, occupied),
                      all_floor_elevation_three=all(words[y*width+x] >> 12 == 3 for x, y in floor),
                      all_actor_feet_on_clear_floor=occupied <= floor,
                      unique_actor_positions=len(occupied) == len(objects),
                      guide_off_three_wide_entry=not any(abs(o['x']-start[0]) <= 1 and o['y'] >= height-4 for o in objects),
                      four_students=len(students) == 4,
                      exit_warps_on_clear_floor=all((w['x'], w['y']) in floor for w in mapping['warp_events']))
        private = source / 'data/tilesets/secondary' / gym['key'].lower() / 'metatile_attributes.bin'
        attrs = struct.unpack('<' + 'H' * (private.stat().st_size // 2), private.read_bytes())
        exits = {(w['x'], w['y']) for w in mapping['warp_events']}
        checks['ordinary_walk_behaviors_outside_exits'] = all(
            words[y*width+x] & 1023 >= 512 and attrs[(words[y*width+x] & 1023)-512] & 255 == 0
            for x, y in floor-exits)
        rows, facings = [], []
        for local_id, student in enumerate(objects, 1):
            if student not in students:
                continue
            facing = student['movement_type'].removeprefix('MOVEMENT_TYPE_FACE_')
            facings.append(facing)
            x, y = student['x'], student['y']
            distance = int(student['trainer_sight_or_berry_tree_id'])
            dx, dy = DIRECTIONS[facing]
            beam = {(x+dx*d, y+dy*d) for d in range(1, distance+1)}
            approach = {(x+dx*d+dy*side, y+dy*d+dx*side)
                        for d in range(distance+1) for side in [-1, 0, 1]}
            body = (x, y)
            row = dict(local_id=local_id, position=[x, y], facing=facing, sight=distance,
                       clear_sightline=beam <= floor and not (beam & (occupied-{body})),
                       three_wide_approach=approach <= floor,
                       sightline_is_mandatory=target not in reached(floor, start, occupied | beam),
                       can_reach_every_sight_cell=beam <= reached(floor, start, occupied))
            rows.append(row)
        checks['four_different_facings'] = set(facings) == set(DIRECTIONS)
        for name, passed in checks.items():
            if not passed:
                failures.append(dict(map=gym['name'], check=name))
        for row in rows:
            for name in ['clear_sightline', 'three_wide_approach', 'sightline_is_mandatory', 'can_reach_every_sight_cell']:
                if not row[name]:
                    failures.append(dict(map=gym['name'], position=row['position'], local_id=row['local_id'], check=name))
        rooms.append(dict(map=gym['name'], dimensions=[width, height],
                          blockdata_sha256=hashlib.sha256(raw).hexdigest(),
                          actor_positions=[dict(local_id=i+1, position=[o['x'], o['y']], graphics=o['graphics_id']) for i,o in enumerate(objects)],
                          walkable_cells=len(floor), checks=checks, students=rows))
    sprites = []
    for key in ['morty', 'whitney', 'valerie', 'steven', 'bugsy', 'candice', 'clair', 'karen']:
        path = source / f'graphics/object_events/pics/people/journey_pwt_{key}.png'
        image = Image.open(path)
        transparent_corners = image.mode == 'P' and all(image.getpixel((x, frame*32+y)) == 0
            for frame in range(9) for x, y in [(0,0), (image.width-1,0), (0,31), (image.width-1,31)])
        bounds = [image.crop((0, frame*32, image.width, (frame+1)*32)).getbbox() for frame in range(9)]
        row = dict(name=key, source=path.relative_to(source).as_posix(), dimensions=list(image.size),
                   sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                   all_nine_frames_have_visible_pixels=all(bounds), index_zero_corners=transparent_corners,
                   visible_bounds=[list(box) if box else None for box in bounds])
        if not transparent_corners or not all(bounds):
            failures.append(dict(sprite=key, check='native_index_zero_transparency_or_missing_frame'))
        sprites.append(row)
    return dict(kind='generated-gym-geometry', source_analysis_only=True, native_validation_performed=False,
                rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
                rooms=rooms, sprites=sprites, failures=failures,
                geometry_checks_passed=not failures,
                limitations=['Graph checks do not certify native movement, battle approach, draw priority or animation.',
                             'Corner transparency does not replace whole-sprite visual review.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    result = audit(options.source)
    options.output.parent.mkdir(parents=True, exist_ok=True)
    options.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(dict(rooms=len(result['rooms']), failures=result['failures'], source_analysis_only=True), indent=2))
