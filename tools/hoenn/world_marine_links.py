"""Missing coastal passages requested in the annotated world-map review."""
import copy
import json
import re
import struct

from sevii_navigation_grid import reconcile

PASSAGES = [
    dict(map='JourneyNorthHoennStrait', name='NORTH HOENN STRAIT', center=[109, 68], size=[32, 40],
         definition='Canal entre o litoral de Kanto e o norte da Rota 124, em Hoenn.',
         links=[('JourneyKantoEasternChannel', 'up', -23), ('Route124', 'down', -32)]),
    dict(map='JourneyTwoThreePassage', name='TWO-THREE PASSAGE', center=[179, 47], size=[64, 24],
         definition='Passagem costeira de Surf ao sul de Two Island até a costa oeste de Three Island.',
         links=[('TwoIsland_Frlg', 'up', 0), ('ThreeIsland_Harbor_Frlg', 'right', 0)]),
    dict(map='JourneyTanobyDawnSea', name='TANOBY DAWN SEA', center=[181, 106], size=[112, 24],
         definition='Mar ao sul de Sevii que une Tanoby, o mar de Seven Island e a costa de Birth Island.',
         links=[('JourneyWorldSea07', 'up', 0), ('SevenIsland_TanobyRuins_Frlg', 'up', 64),
                ('BirthIsland_Exterior_Frlg', 'right', 0)]),
]
OPPOSITE = dict(up='down', down='up', left='right', right='left')


def prepare_links(layer, maps, geometry, reference):
    """Append IDs; open only marine cells, leaving all native land/events intact."""
    s = layer.source
    ld = json.loads((s/'data/layouts/layouts.json').read_text())
    layouts = {l['id']: l for l in ld['layouts']}
    groups = json.loads((s/'data/maps/map_groups.json').read_text())
    group = next(g for g in groups['group_order'] if 'JourneyWorldSea01' in groups[g])
    scripts = (s/'data/event_scripts.s').read_text()
    before = copy.deepcopy(maps)
    changed_tiles = {}

    # This four-cell mouth already points south. Redirect just that span;
    # the existing Sea01/Sea02 east-west connection remains available.
    a, b = 'JourneyKantoEasternChannel', 'JourneyWorldSea02'
    assert any(c['map'] == maps[b]['id'] and c['direction'] == 'down' for c in maps[a]['connections'])
    for n, other in [(a, b), (b, a)]:
        maps[n]['connections'] = [c for c in maps[n]['connections'] if c['map'] != maps[other]['id']]

    for p in PASSAGES:
        n = p['map']; w, h = p['size']
        # A second run is handled by Layer.existing(); a pre-existing passage
        # is never duplicated under a fresh ID.
        assert n not in maps
        m = copy.deepcopy(maps['JourneyWorldSea01'])
        m.update(id='MAP_'+n.upper(), name=n, layout='LAYOUT_'+n.upper(),
                 connections=[], object_events=[], warp_events=[], coord_events=[], bg_events=[])
        maps[n] = m
        template = layouts[maps['JourneyWorldSea01']['layout']]
        l = copy.deepcopy(template)
        l.update(id=m['layout'], name=n+'_Layout', width=w, height=h,
                 border_filepath=f'data/layouts/{n}/border.bin', blockdata_filepath=f'data/layouts/{n}/map.bin')
        layouts[l['id']] = l; ld['layouts'].append(l); groups[group].append(n)
        layer.stage(f'data/maps/{n}/scripts.inc', n+'_MapScripts::\n\t.byte 0\n')
        scripts += f'\n\t.include "data/maps/{n}/scripts.inc"\n'
        for other, d, off in p['links']:
            m['connections'].append(dict(map=maps[other]['id'], direction=d, offset=off))
            maps[other]['connections'] = (maps[other].get('connections') or []) + [
                dict(map=m['id'], direction=OPPOSITE[d], offset=-off)]
        tiles = [0x112B]*(w*h)
        # Keep unconnected outer edges blocked; all reciprocal mouths stay open.
        spans = {d: set() for d in OPPOSITE}
        for other, d, off in p['links']:
            q = layouts[maps[other]['layout']]
            limit, length = (w, q['width']) if d in ('up', 'down') else (h, q['height'])
            spans[d].update(range(max(0, off), min(limit, off+length)))
        for y in range(h):
            for x in range(w):
                if (x<2 and y not in spans['left'] or x>=w-2 and y not in spans['right']
                    or y<2 and x not in spans['up'] or y>=h-2 and x not in spans['down']):
                    tiles[y*w+x] = [0x510, 0x511, 0x518, 0x519][y%2*2+x%2]
        # Small complete sandbars make the passages distinct marine landscapes.
        for cx in [w//3, 2*w//3]:
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    tiles[(h//2+dy)*w+cx+dx] = 0x3000 + [
                        0x10C,0x10D,0x10E,0x114,0x115,0x116,0x11C,0x11D,0x11E][(dy+1)*3+dx+1]
        layer.stage(l['blockdata_filepath'], struct.pack('<'+'H'*len(tiles), *tiles))
        layer.stage(l['border_filepath'], struct.pack('<4H', 0x510,0x511,0x518,0x519))
        changed_tiles[n] = tiles
        geometry['projections'].append(dict(map=n, id=m['id'], width=w, height=h,
                                            center=p['center'], first=0, count=0))

    # Imported FRLG animated water is frequently collision marked. Replace
    # marine cells only; original land, cave entrances and event coordinates stay.
    for n in ['TwoIsland_Frlg', 'SevenIsland_TanobyRuins_Frlg', 'BirthIsland_Exterior_Frlg']:
        l = layouts[maps[n]['layout']]; raw = (s/l['blockdata_filepath']).read_bytes()
        tiles = list(struct.unpack('<'+'H'*(len(raw)//2), raw)); wet = reference['maps'][n]['water']
        for i, water in enumerate(wet):
            if water == '1': tiles[i] = 0x112B
        layer.stage(l['blockdata_filepath'], struct.pack('<'+'H'*len(tiles), *tiles))
        changed_tiles[n] = tiles
    # Open the western marine mouth of Three Island's existing harbor.
    n = 'ThreeIsland_Harbor_Frlg'; l = layouts[maps[n]['layout']]
    raw = (s/l['blockdata_filepath']).read_bytes(); tiles = list(struct.unpack('<'+'H'*(len(raw)//2), raw))
    for y in range(9, l['height']):
        for x in range(2): tiles[y*l['width']+x] = 0x112B
    layer.stage(l['blockdata_filepath'], struct.pack('<'+'H'*len(tiles), *tiles)); changed_tiles[n] = tiles

    # The old southern edge of this sea had a closed reef because there was
    # no neighbour. Open its two border rows for the new southern passage.
    n = 'JourneyWorldSea07'; l = layouts[maps[n]['layout']]
    raw = (s/l['blockdata_filepath']).read_bytes(); tiles = list(struct.unpack('<'+'H'*(len(raw)//2), raw))
    for y in range(l['height']-2, l['height']):
        for x in range(l['width']): tiles[y*l['width']+x] = 0x112B
    layer.stage(l['blockdata_filepath'], struct.pack('<'+'H'*len(tiles), *tiles)); changed_tiles[n] = tiles

    for n, m in maps.items():
        if before.get(n) != m:
            if n in before:
                assert all(m[k] == before[n][k] for k in ['object_events','warp_events','coord_events','bg_events'])
            layer.stage(f'data/maps/{n}/map.json', json.dumps(m, indent=2)+'\n')
    for path, data in [('data/maps/map_groups.json', groups), ('data/layouts/layouts.json', ld)]:
        layer.stage(path, json.dumps(data, indent=2)+'\n')
    layer.stage('data/event_scripts.s', scripts)

    # Extend the existing per-tile GPS; reconcile both ends of every new seam.
    path = 'src/data/journey_world_position.h'; header = (s/path).read_text()
    values = list(map(int, re.search(r'sWorldNavigationPixels\[\] = \{([^}]+)', header)[1].split(',')))
    import numpy as np
    old_grids = {}; cursor = 0
    for p in geometry['projections'][:-len(PASSAGES)]:
        w,h = p['width'],p['height']; old_grids[p['map']] = values[cursor:cursor+w*h]; cursor += w*h
    additions = []
    for p in PASSAGES:
        first = len(values); w,h = p['size']; anchors = []; boundary = []
        for other,d,off in p['links']:
            ol = layouts[maps[other]['layout']]; ow,oh = ol['width'],ol['height']
            candidates = []
            ot = changed_tiles.get(other)
            if ot is None:
                raw=(s/ol['blockdata_filepath']).read_bytes(); ot=struct.unpack('<'+'H'*(len(raw)//2),raw)
            for t in range(max(0,off),min(h if d in ('left','right') else w,off+(oh if d in ('left','right') else ow))):
                x,y = (0 if d=='left' else w-1,t) if d in ('left','right') else (t,0 if d=='up' else h-1)
                xx,yy = (ow-1 if d=='left' else 0,t-off) if d in ('left','right') else (t-off,oh-1 if d=='up' else 0)
                v = old_grids[other][yy*ow+xx]; sample=[x,y,v&255,v>>8]; boundary.append(sample)
                water=reference['maps'][other]['water'][yy*ow+xx]=='1' or ot[yy*ow+xx]==0x112B
                if water and not ot[yy*ow+xx]&0xC00 and changed_tiles[p['map']][y*w+x]==0x112B:candidates.append(sample)
            assert candidates,('No marine anchor',p['map'],other)
            anchors.append(candidates[len(candidates)//2])
        # Interpolate from the actual shared geographic boundary coordinates.
        # An arbitrary route-centre anchor can make a northbound trip drift
        # sideways, even when every tile and seam satisfies the step bound.
        a = np.array(anchors); yy,xx = np.indices((h,w)); xx=xx.ravel(); yy=yy.ravel()
        distance = (a[:,0,None]-xx)**2+(a[:,1,None]-yy)**2
        weights = 1048576//np.maximum(distance,1)
        projected = ((weights.T@a[:,2:]+weights.sum(axis=0)[:,None]//2)//weights.sum(axis=0)[:,None]).astype(int)
        for x,y,px,py in boundary:projected[y*w+x] = [px,py]
        values.extend(int(x)|(int(y)<<8) for x,y in projected)
        additions.append('{'+f'{first}, (MAP_GROUP(MAP_{p["map"].upper()})<<8)|MAP_NUM(MAP_{p["map"].upper()}), {w}, {h}'+'},\n')
    header = re.sub(r'(sWorldNavigationPixels\[\] = \{)[^}]+', lambda m:m[1]+','.join(map(str, values)), header)
    end = header.index('};', header.index('sWorldTileGrids'))
    header = header[:end]+''.join(additions)+header[end:]
    header, gps = reconcile(header, geometry['projections'], maps)
    layer.stage(path, header)
    final = list(map(int,re.search(r'sWorldNavigationPixels\[\] = \{([^}]+)',header)[1].split(',')))
    cursor = 0
    for p in geometry['projections']:
        w,h = p['width'],p['height']
        if p['map'] in {q['map'] for q in PASSAGES}:
            v=final[cursor+(h//2)*w+w//2]; p['center']=[v&255,v>>8]
        cursor += w*h
    return layouts, changed_tiles, gps
