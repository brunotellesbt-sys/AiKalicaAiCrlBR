#!/usr/bin/env python3
"""Audit the supplied Emerald and inventory the complete pinned Hoenn source."""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile
import urllib.request
import zipfile

PIN = '731ad5bfd6e6f265508d0efcca0ba42f9dcf5881'
EXPECTED = 'a9dec84dfe7f62ab2220bafaef7479da0929d066ece16a6885f6226db19085af'
SOURCE = 'https://github.com/pret/pokeemerald/tree/' + PIN


def audit(archive, output):
    with zipfile.ZipFile(archive) as z:
        names = [n for n in z.namelist() if n.lower().endswith('.gba')]
        if len(names) != 1:
            raise ValueError('Expected exactly one Emerald ROM in the supplied ZIP')
        rom = z.read(names[0])
    digest = hashlib.sha256(rom).hexdigest()
    if digest != EXPECTED or rom[0xac:0xb0] != b'BPEE':
        raise ValueError('Unexpected Emerald revision; source data cannot be matched safely')
    maps = {}; groups = None; features = []; file_hashes = {}
    url = 'https://codeload.github.com/pret/pokeemerald/tar.gz/' + PIN
    with urllib.request.urlopen(url, timeout=60) as response, tarfile.open(fileobj=response, mode='r|gz') as tar:
        for member in tar:
            if not member.isfile(): continue
            path = member.name.split('/', 1)[1]
            if path.startswith('src/') and path.endswith('.c'):
                if any(k in path for k in ['battle_factory', 'battle_dome', 'battle_pike',
                    'battle_arena', 'battle_palace', 'battle_pyramid', 'battle_tower',
                    'contest', 'pokenav', 'pokeblock', 'secret_base']): features.append(path)
            if path == 'data/maps/map_groups.json' or path.startswith('data/maps/') and path.endswith('map.json'):
                raw = tar.extractfile(member).read()
                data = json.loads(raw)
                file_hashes[path] = hashlib.sha256(raw).hexdigest()
                if path.endswith('map_groups.json'): groups = data
                else: maps[data['name']] = data
    if groups is None: raise ValueError('Missing Hoenn map groups')
    rows = []
    for group, label in enumerate(groups['group_order']):
        for number, name in enumerate(groups[label]):
            m = maps[name]
            events = m
            while events.get('shared_events_map'):
                events = maps[events['shared_events_map']]
            rows.append(dict(name=name, group=group, number=number, layout=m['layout'],
                objects=len(events.get('object_events', [])), trainers=sum(o.get('trainer_type') == 'TRAINER_TYPE_NORMAL' for o in events.get('object_events', [])),
                warps=len(events.get('warp_events', [])), triggers=len(events.get('coord_events', [])),
                background_events=len(events.get('bg_events', [])), connections=m.get('connections'),
                shared_events_map=m.get('shared_events_map')))
    report = dict(status='inventory_only_not_integrated', supplied_rom=dict(filename=names[0],
        bytes=len(rom), sha256=digest), source_repository=SOURCE, source_commit=PIN,
        map_groups=len(groups['group_order']), map_count=len(rows),
        totals={key: sum(r[key] for r in rows) for key in ['objects', 'trainers', 'warps', 'triggers', 'background_events']},
        preservation_required_features=sorted(features), map_source_sha256=file_hashes, maps=rows,
        integration_pending=['Map layouts/tilesets and connections', 'NPC graphics and scripts',
            'Independent Hoenn story flags, variables and eight badges', 'Dive and Whirlpool field actions',
            'Emerald specials, contests, Battle Frontier, PokéNav and Secret Bases',
            'Vermilion–Slateport ticket ferry and continuous Surf routes',
            'Existing party/box/save compatibility and regression checks'])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k:report[k] for k in ['status', 'map_count', 'map_groups', 'totals']}, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive', type=Path, required=True)
    p.add_argument('--output', type=Path, default=Path('mods/hoenn/source-inventory.json'))
    a = p.parse_args(); audit(a.archive, a.output)
