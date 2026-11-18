"""Independent source checks for individual encounters and native campaign IDs."""
import hashlib
import json
from collections import deque
from pathlib import Path
import re
import struct

from badge_story_layer import read
from prepare_world_dex_map import PAT


def audit(layer, reference, report):
    reference = Path(reference)
    rooms = report['rooms']
    if len(rooms) != 105 or len({r['national_dex'] for r in rooms}) != 105:
        raise ValueError('Each special encounter needs exactly one room')
    old_groups = json.loads((reference/'data/maps/map_groups.json').read_text())
    groups = json.loads(read(layer, 'data/maps/map_groups.json'))
    if groups['group_order'][:len(old_groups['group_order'])] != old_groups['group_order']:
        raise ValueError('Historical group indices changed')
    for name in old_groups['group_order']:
        if groups[name] != old_groups[name]:
            raise ValueError('Historical map numbers changed')
    appended = groups['group_order'][len(old_groups['group_order']):]
    if len(groups['group_order']) > 128 or any(len(groups[g]) > 100 for g in appended):
        raise ValueError('Map identity cannot be persisted in WarpData')
    layouts = {l['id']: l for l in json.loads(read(layer, 'data/layouts/layouts.json'))['layouts']}
    old_layouts = {l['id']: l for l in json.loads((reference/'data/layouts/layouts.json').read_text())['layouts']}
    dexmap = read(layer, 'src/data/journey_world_dex_locations.h').decode()
    world = read(layer, 'src/data/journey_world_map.h').decode()
    area = read(layer, 'src/pokedex_area_screen.c').decode()
    parents, checked_inputs = {}, {}
    for record in rooms:
        parent_name = record['parent']
        if parent_name not in parents:
            before = json.loads((reference/f'data/maps/{parent_name}/map.json').read_text())
            after = json.loads(read(layer, f'data/maps/{parent_name}/map.json'))
            ordinary = [o for o in before['object_events'] if not re.fullmatch(r'JourneySanctuary_\d+',o.get('script',''))]
            if after['object_events'] != ordinary:
                raise ValueError(('Native campaign actor changed', parent_name))
            for i, actor in enumerate(ordinary):
                if actor != before['object_events'][i]:
                    raise ValueError('Native numeric local ID changed')
            for key in before.keys() | after.keys():
                if key not in ('object_events','warp_events') and before.get(key) != after.get(key):
                    raise ValueError(('Native map header or event changed',parent_name,key))
            if after['warp_events'][:len(before['warp_events'])] != before['warp_events']:
                raise ValueError(('Native campaign warp changed',parent_name))
            for suffix in ('scripts.inc',):
                path = f'data/maps/{parent_name}/{suffix}'
                if (reference/path).is_file() and read(layer,path) != (reference/path).read_bytes():
                    raise ValueError(('Native capture or campaign script changed',path))
            parents[parent_name] = (before,after)
        before,parent = parents[parent_name]
        name = record['room']
        room = json.loads(read(layer,f'data/maps/{name}/map.json'))
        room_id = 'MAP_'+name.upper()
        if room['id'] != room_id or sum(name in groups[g] for g in groups['group_order']) != 1:
            raise ValueError('Missing or ambiguous compiled room identity')
        if len(room['object_events']) != 1 or len(room['warp_events']) != 1:
            raise ValueError('Room must contain exactly one encounter and return')
        actor = room['object_events'][0]
        old_actor = next(o for o in before['object_events'] if o.get('script') == record['script'])
        for key in old_actor.keys() | actor.keys():
            if key not in ('x','y','elevation') and old_actor.get(key) != actor.get(key):
                raise ValueError(('Encounter identity, sprite or flag changed',name,key))
        if not actor['graphics_id'].startswith('OBJ_EVENT_GFX_SPECIES('):
            raise ValueError('A statue cannot represent a legendary')
        entry = parent['warp_events'][record['parent_warp']]
        exit_event = room['warp_events'][0]
        if (entry['dest_map'], str(entry['dest_warp_id'])) != (room_id,'0'):
            raise ValueError('Entrance leads to the wrong chamber')
        if (exit_event['dest_map'],str(exit_event['dest_warp_id'])) != (parent['id'],str(record['parent_warp'])):
            raise ValueError('Exit must return through its own entrance')
        layout = layouts[room['layout']]
        raw = read(layer,layout['blockdata_filepath'])
        if len(raw) != 2*layout['width']*layout['height'] or hashlib.sha256(raw).hexdigest() != record['blockdata_sha256']:
            raise ValueError('Room geometry changed after preparation')
        if (layout['width']+15)*(layout['height']+14) > 10240:
            raise ValueError('Native map buffer overflow')
        values = struct.unpack('<'+'H'*(len(raw)//2),raw)
        template = json.loads((reference/f'data/maps/{record["template"]}/map.json').read_text())
        donor_layout = old_layouts[template['layout']]
        for key in ('primary_tileset','secondary_tileset','layout_version'):
            if layout[key] != donor_layout[key]:
                raise ValueError('Room uses a foreign native graphics bank')
        if read(layer,layout['border_filepath']) != (reference/donor_layout['border_filepath']).read_bytes():
            raise ValueError('Room border differs from its whole native donor')
        # Independently remove the inserted identical stripes, then compare
        # every word to the complete original room, including blocked corners.
        stripes = {'JourneySanctuaryTitans':(11,8), 'SealedChamber_OuterRoom':(5,4),
                   'SealedChamber_InnerRoom':(None,10), 'AlteringCave':(None,None),
                   'GraniteCave_StevensRoom':(None,None), 'MarineCave_End':(None,None),
                   'TerraCave_End':(None,None)}
        col,row = stripes[record['template']]
        cols,rows = record['expanded_columns'],record['expanded_rows']
        if (cols and col is None) or (rows and row is None) or cols not in (0,2,4,6,8) or rows not in (0,2,4):
            raise ValueError('Unreviewed native-room expansion')
        grid = [list(values[y*layout['width']:(y+1)*layout['width']]) for y in range(layout['height'])]
        if rows:
            if any(r != grid[row-1] for r in grid[row:row+rows+1]):
                raise ValueError('A row expansion cut a native object')
            del grid[row:row+rows]
        if cols:
            if any(any(v != r[col-1] for v in r[col:col+cols+1]) for r in grid):
                raise ValueError('A column expansion cut a native object')
            for r in grid:
                del r[col:col+cols]
        donor_raw = (reference/donor_layout['blockdata_filepath']).read_bytes()
        restored = struct.pack('<'+'H'*sum(map(len,grid)),*(v for r in grid for v in r))
        if restored != donor_raw or len(grid) != donor_layout['height'] or any(len(r) != donor_layout['width'] for r in grid):
            raise ValueError('A room lost part of its native scenery')
        for x,y in ((actor['x'],actor['y']),(exit_event['x'],exit_event['y'])):
            if not (0 <= x < layout['width'] and 0 <= y < layout['height']) or values[y*layout['width']+x]&0xC00:
                raise ValueError('Encounter or return is physically blocked')
        width=layout['width']
        start=exit_event['y']*width+exit_event['x']
        goal=(actor['y']+1)*width+actor['x']
        seen={start};queue=deque([start])
        while queue and goal not in seen:
            i=queue.popleft();x,y=i%width,i//width
            for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                j=yy*width+xx
                if 0<=xx<width and 0<=yy<layout['height'] and j not in seen and not values[j]&0xC00 and values[j]>>12!=1:
                    seen.add(j);queue.append(j)
        if goal not in seen:
            raise ValueError('Species clearing requires walking over water or a wall')
        pattern = r'\{'+record['species']+r',([^,]+),(\d+),(\d+),1,0\}'
        rows = re.findall(pattern,dexmap)
        if len(rows) != 1 or rows[0][0] != room_id:
            raise ValueError(('Pokédex contains stale or duplicate special location',name))
        point_rows = [m for m in re.finditer(PAT,world) if m[1] == room_id]
        if len(point_rows) != 1 or tuple(point_rows[0][i] for i in (3,4)) != rows[0][1:]:
            raise ValueError('Room and Pokédex atlas coordinates disagree')
        branch = re.search(r'if \(species == '+record['species']+r'\b.*?SetSpecialMapHasMon\([^;]+;',area,re.S)
        if branch is None or room_id not in branch[0]:
            raise ValueError('Native area screen still points to the shared room')
    # Four graphic arrays remain byte-for-byte identical; only points grow.
    old_world = (reference/'src/data/journey_world_map.h').read_text()
    for symbol in ('sWorldTiles','sWorldTilemap','sWorldPalette','sWorldDetailPixels'):
        pattern = r'\b'+symbol+r'\[\][^=]*=\s*\{[^}]*\}'
        a,b = re.search(pattern,old_world),re.search(pattern,world)
        if a is not None and (b is None or a[0] != b[0]):
            raise ValueError(('World map artwork changed',symbol))
    for name,raw in layer.outputs.items():
        checked_inputs[name] = hashlib.sha256(raw).hexdigest()
    return dict(passed=True, rooms=105, parents=len(parents),
                unique_native_geometries=len({r['blockdata_sha256'] for r in rooms}),
                original_warp_prefixes_and_native_NPCs_preserved=True,
                single_current_Dex_location_per_species=True,
                capture_scripts_flags_and_species_sprites_preserved=True,
                input_sha256=checked_inputs, native_gameplay_validated=False)
