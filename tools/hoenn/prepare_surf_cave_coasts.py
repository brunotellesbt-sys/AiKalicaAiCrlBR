"""Connect cave icons and furnish only bare marine routes with sandy islets."""
import argparse, copy, hashlib, json, random, re, struct
from pathlib import Path
from PIL import Image
from candidate_layer import Layer
from prepare_annotated_world_links import PRIOR, LAYER as PREVIOUS
from prepare_connected_sea_chart import route
from prepare_world_dex_map import decode, encode

LAYER = 'surf-cave-coasts'; PRIOR = PRIOR + [PREVIOUS]


def prepare(source):
    layer = Layer(source, LAYER, PRIOR)
    if old := layer.existing():
        return old
    s = layer.source
    maps = {p.parent.name: json.loads(p.read_text()) for p in (s / 'data/maps').glob('*/map.json')}
    layoutdata = json.loads((s / 'data/layouts/layouts.json').read_text())
    layouts = {l['id']: l for l in layoutdata['layouts']}
    byid = {m['id']: n for n, m in maps.items()}
    boundaries = []
    islands = []; skipped = []; parties = []; definitions = []; scripts = ''
    opponents = (s / 'include/constants/opponents.h').read_text()
    first = int(re.search(r'#define TRAINERS_COUNT\s+(\d+)', opponents)[1])
    flags = (s / 'include/constants/flags.h').read_text()
    # These thirteen bytes/bits are inside the existing save allocation and
    # unused between the champion flag and the sanctuary capture flags.
    used_flags = {int(x, 16) for x in re.findall(r'^#define\s+\w+\s+(0x[\da-fA-F]+)\b', flags, re.M)}
    free_flags = [f for f in range(0x1AC3, 0x1AD0) if f not in used_flags]
    for n, m in sorted(maps.items()):
        l = layouts[m['layout']]
        if not n.startswith('Journey') or 'Harbor' in n or n in ['JourneyDewfordPortIsland', 'JourneyRoute12Shipyard'] or not m.get('connections'):
            continue
        if m['map_type'] not in ['MAP_TYPE_ROUTE', 'MAP_TYPE_OCEAN_ROUTE'] or l['primary_tileset'] not in ['gTileset_General', 'gTileset_General_Frlg']:
            continue
        w, h = l['width'], l['height']; fr = l['layout_version'] == 'frlg'
        v = list(struct.unpack('<' + 'H' * (w * h), (s / l['blockdata_filepath']).read_bytes()))
        original = list(v); spans = {d: set() for d in ['left', 'right', 'up', 'down']}
        for c in m['connections']:
            d = c['direction']
            if d not in spans: continue
            q = layouts[maps[byid[c['map']]]['layout']]; off = c['offset']
            length = q['height'] if d in ['left', 'right'] else q['width']
            limit = h if d in ['left', 'right'] else w
            spans[d].update(range(max(0, off), min(limit, off + length)))
        rocks = [0x510, 0x511, 0x518, 0x519] if fr else [0x1550, 0x551, 0x558, 0x1559]
        for y in range(h):
            for x in range(w):
                closed = (x < 2 and y not in spans['left'] or x >= w - 2 and y not in spans['right']
                          or y < 2 and x not in spans['up'] or y >= h - 2 and x not in spans['down'])
                if closed and v[y * w + x] >> 12 <= 1:
                    v[y * w + x] = rocks[y % 2 * 2 + x % 2]
        # Unique borders avoid changing a port or another map sharing its art.
        l['border_filepath'] = f'data/layouts/{n}/surf-limits.bin'
        layer.stage(l['border_filepath'], struct.pack('<4H', *rocks))
        repaired = sum(a != b for a, b in zip(original, v))
        boundaries.append(dict(map=n, repaired_cells=repaired, collision_rocks=True))
        shore = [0x10C, 0x10D, 0x10E, 0x114, 0x115, 0x116, 0x11C, 0x11D, 0x11E] if fr else [0x11B, 0x11C, 0x11D, 0x123, 0x124, 0x125, 0x12B, 0x12C, 0x12D]
        if any(t >> 12 >= 3 and (t & 1023 in shore or t & 1023 in [1, 0x15]) for t in v):
            if v != original: layer.stage(l['blockdata_filepath'], struct.pack('<' + 'H' * len(v), *v))
            skipped.append(n); continue
        assert len(islands) < len(free_flags), 'No unused persistent flags left'
        rng = random.Random(int(hashlib.sha256(n.encode()).hexdigest()[:16], 16))
        # A convex, asymmetric island; each horizontal run is at least five
        # tiles wide. No narrow tips, one-tile necks or clipped beach corners.
        rows = [(-2, 2), (-3, 3), (-4, 3), (-4, 4), (-3, 4), (-3, 3), (-2, 2)]
        if rng.randrange(2): rows = [(-b, -a) for a, b in rows]
        if rng.randrange(2): rows.reverse()
        cx = max(8, min(w - 9, w // 2 + rng.randint(-max(1, w // 7), max(1, w // 7))))
        cy = max(6, min(h - 7, h // 2 + rng.randint(-max(1, h // 8), max(1, h // 8))))
        land = {(cx + x, cy + y - 3) for y, (a, b) in enumerate(rows) for x in range(a, b + 1)}
        assert all(3 <= x < w - 3 and 3 <= y < h - 3 and v[y * w + x] in [0x112B, 0x1170] for x, y in land), n
        assert not m['object_events'] and not m['warp_events'] and not m['coord_events'], n
        for x, y in land:
            row = 0 if (x, y - 1) not in land else 2 if (x, y + 1) not in land else 1
            col = 0 if (x - 1, y) not in land else 2 if (x + 1, y) not in land else 1
            v[y * w + x] = ((3 if fr or row == col == 1 else 1) << 12) | shore[row * 3 + col]
        v[cy * w + cx] = 0x3115 if fr else 0x3124
        ident = first + len(islands); key = f'TRAINER_JOURNEY_BEACH_{len(islands)}'; label = f'JourneyBeachTrainer{ident}'
        flag = free_flags[len(islands)]; definitions.append(f'#define {key} {ident}\n')
        m['object_events'].append(dict(type='object', graphics_id='OBJ_EVENT_GFX_SWIMMER_M', x=cx, y=cy, elevation=3,
            movement_type='MOVEMENT_TYPE_FACE_DOWN', movement_range_x=0, movement_range_y=0,
            trainer_type='TRAINER_TYPE_NORMAL', trainer_sight_or_berry_tree_id='2', script=label, flag='0'))
        species = rng.choice([['Tentacool', 'Wingull'], ['Staryu', 'Horsea'], ['Marill', 'Chinchou']])
        parties.append(f'\n=== {key} ===\nName: SAILOR\nClass: Swimmer M\nPic: Swimmer M\nGender: Male\nMusic: Swimmer\nAI: Basic Trainer\n'
                       + ''.join(f'\n{mon}\nLevel: 28\nIVs: 15 HP / 15 Atk / 15 Def / 15 SpA / 15 SpD / 15 Spe\n' for mon in species))
        scripts += f'''\n{label}::
\ttrainerbattle_single {key}, {label}_Intro, {label}_Defeat
\tmsgbox {label}_After, MSGBOX_NPC
\tend
{label}_Intro:
\t.string "An island stop! Let's battle!$"
{label}_Defeat:
\t.string "Your POKEMON ride the waves!$"
{label}_After:
\t.string "The open sea connects our regions.$"
'''
        layer.stage(l['blockdata_filepath'], struct.pack('<' + 'H' * len(v), *v))
        layer.stage(f'data/maps/{n}/map.json', json.dumps(m, indent=2) + '\n')
        islands.append(dict(map=n, land=sorted(map(list, land)), trainer=dict(id=ident, key=key, flag=flag, script=label, x=cx, y=cy), species=species, native_beach_edges=True))
    assert islands
    layer.stage('data/layouts/layouts.json', json.dumps(layoutdata, indent=2) + '\n')
    opponents = re.sub(r'(#define TRAINERS_COUNT\s+)\d+', lambda m: m[1] + str(first + len(islands)), opponents)
    layer.stage('include/constants/flags.h', flags + '\n' + ''.join(f'#define FLAG_JOURNEY_BEACH_TRAINER_{j} {hex(i["trainer"]["flag"])}\n' for j, i in enumerate(islands)))
    layer.stage('include/constants/opponents.h', opponents + '\n' + ''.join(definitions))
    layer.stage('src/data/trainers.party', (s / 'src/data/trainers.party').read_text() + ''.join(parties))
    layer.stage('data/scripts/journey_beach_trainers.inc', scripts)
    layer.stage('data/event_scripts.s', (s / 'data/event_scripts.s').read_text() + '\n\t.include "data/scripts/journey_beach_trainers.inc"\n')
    # New ordinary trainers need private flags. Adding to TRAINERS_COUNT must
    # not alias the unrelated system flags after MAX_TRAINERS_COUNT or change
    # the save layout. Every battle flag read/write goes through this helper.
    p = 'src/battle_setup.c'; text = (s / p).read_text()
    helper = 'static u16 JourneyBeachTrainerFlag(u16 trainerId)\n{\n'
    helper += f'    if (trainerId >= {first} && trainerId < {first + len(islands)})\n    {{\n        static const u16 flags[] = {{' + ','.join(hex(i['trainer']['flag']) for i in islands) + '};\n'
    helper += f'        return flags[trainerId - {first}];\n    }}\n    return TRAINER_FLAGS_START + trainerId;\n}}\n\n'
    text = text.replace('static u16 GetTrainerAFlag(void)\n{', helper + 'static u16 GetTrainerAFlag(void)\n{', 1)
    for expression in ['TRAINER_BATTLE_PARAM.opponentA', 'TRAINER_BATTLE_PARAM.opponentB', 'temp->params.opponentA', 'trainerId']:
        # Keep the helper's original fallback unmodified.
        old = 'TRAINER_FLAGS_START + ' + expression
        start = text.index('static u16 GetTrainerAFlag(void)\n{')
        text = text[:start] + text[start:].replace(old, 'JourneyBeachTrainerFlag(' + expression + ')')
    layer.stage(p, text)
    # The Paradox hub's south corridor was sealed from its altar room.
    # Retain all warps and encounters; open only the doorway threshold.
    chamber = 'JourneySanctuaryDimensoes'; l = layouts[maps[chamber]['layout']]
    raw = (s / l['blockdata_filepath']).read_bytes(); cells = list(struct.unpack('<' + 'H' * (len(raw) // 2), raw))
    at = 18 * l['width'] + 14; assert cells[at] == 0x783
    cells[at] = 0x364
    layer.stage(l['blockdata_filepath'], struct.pack('<' + 'H' * len(cells), *cells))
    chart = copy.deepcopy(json.loads((s / '.journey-annotated-world-links').read_text())['chart'])
    p = 'src/data/journey_world_map.h'; header = (s / p).read_text(); image = decode(header); before = image.copy()
    caves = json.loads((s / '.journey-complete-marine-atlas').read_text())['cave_entrances']; approaches = []
    sea = {(x, y) for y in range(112) for x in range(224) if image.getpixel((x, y)) in [1, 2]}
    nodes = {n['map']: n['position'] for n in chart['nodes']}
    for cave in caves:
        endpoint = tuple(cave['position']); parent = tuple(nodes.get(cave['surface'], endpoint))
        # End beside the actual cave arch, including its southern entrance.
        target = (endpoint[0], endpoint[1] + 1)
        pixels, corners = route(image, image, parent, target, sea)
        for xy in pixels:
            if image.getpixel(xy) in [1, 2]: image.putpixel(xy, 2)
        approaches.append(dict(**cave, polyline=[list(p) for p in corners], blue_pixels=[list(p) for p in pixels], native_entrance_preserved=True))
    packed = list(map(int, re.search(r'sWorldDetailPixels\[\] = \{([^}]+)', header)[1].split(',')))
    detail = Image.new('P', (448, 224))
    for y in range(224):
        for x in range(448): detail.putpixel((x, y), (packed[y * 224 + x // 2] >> ((x & 1) * 4)) & 15)
    for y in range(112):
        for x in range(224):
            if image.getpixel((x, y)) == 2 and before.getpixel((x, y)) != 2:
                for dy in [0, 1]:
                    for dx in [0, 1]:
                        if detail.getpixel((2 * x + dx, 2 * y + dy)) in [1, 2]: detail.putpixel((2 * x + dx, 2 * y + dy), 2)
    raw = bytes(detail.getpixel((x, y)) | detail.getpixel((x + 1, y)) << 4 for y in range(224) for x in range(0, 448, 2))
    header = re.sub(r'(sWorldDetailPixels\[\] = \{)[^}]+', lambda m: m[1] + ','.join(map(str, raw)), encode(header, image))
    layer.stage(p, header); chart['cave_approaches'] = approaches
    return layer.finish(islands=islands, boundaries=boundaries, cave_threshold_repairs=[dict(map=chamber, tile=[14,18], before=0x783, after=0x364)], already_furnished_routes_preserved=skipped, cave_approaches=approaches,
                        chart=chart, original_cave_entrances_and_legendary_encounters_preserved=True,
                        normal_trainer_flags_private=True, existing_save_layout_preserved=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--source', type=Path, required=True)
    print(json.dumps(prepare(p.parse_args().source), indent=2))
