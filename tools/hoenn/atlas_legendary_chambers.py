"""Give each special encounter its own reciprocal, bank-authenticated room.

Native campaign maps keep their original events and IDs. Room geometry is
copied whole; variation only extends identical complete rows or columns.
This preparer does not certify a release or substitute for controller proof.
"""
import copy
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import struct
import tarfile
from collections import deque

from atlas_neighbor_layouts import load as load_v6
from badge_story_layer import read
from prepare_world_dex_map import PAT
from render_sea_maps import MapRenderer, _braced

ROOT = Path(__file__).resolve().parents[2]
V7_ROM = 'c08cb7771a9731db995b7d99297c8b1ebcdd98d75a9ac5e50cdaef8dcff62c82'


def load_current(parent):
    layer, _ = load_v6(parent)
    evidence = ROOT / 'docs/design/neighbor-layout-camera-review'
    sums = dict((n, h) for h, n in
                (line.split('  ', 1) for line in (evidence / 'SHA256SUMS').read_text().splitlines()))
    blobs = {}
    for name in ('compiled-freeze-v7.json.gz', 'prepared-source-delta-v7.tar.gz'):
        raw = (evidence / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != sums[name]:
            raise ValueError(('Changed version7 snapshot', name))
        blobs[name] = raw
    frozen = json.loads(gzip.decompress(blobs['compiled-freeze-v7.json.gz']))
    if frozen['rom_sha256'] != V7_ROM:
        raise ValueError('Unexpected current ROM')
    found = {}
    with tarfile.open(fileobj=io.BytesIO(blobs['prepared-source-delta-v7.tar.gz']), mode='r:gz') as bundle:
        for member in bundle.getmembers():
            p = Path(member.name)
            if not member.isfile() or p.is_absolute() or '..' in p.parts or member.name in found:
                raise ValueError('Unsafe version7 delta')
            found[member.name] = bundle.extractfile(member).read()
    marker = found.pop('.journey-atlas-surf-layout')
    if hashlib.sha256(marker).hexdigest() != frozen['marker_sha256']:
        raise ValueError('Changed version7 marker')
    metadata = json.loads(marker)
    for name, raw in found.items():
        layer.stage(name, raw)
    if {n: hashlib.sha256(v).hexdigest() for n, v in layer.outputs.items()} != frozen['prepared_sha256']:
        raise ValueError('Incomplete version7 source replay')
    for key in ('layer', 'original_sha256', 'prepared_sha256'):
        metadata.pop(key, None)
    metadata.update(source_audit_passed=False, native_validated=False, release_eligible=False,
                    public_roms_updated=False, NATIVE_CONTRACT_FINALIZED=False)
    return layer, metadata


def _values(layer, layout):
    raw = read(layer, layout['blockdata_filepath'])
    return list(struct.unpack('<' + 'H' * (layout['width'] * layout['height']), raw))


def _pack(values):
    return struct.pack('<' + 'H' * len(values), *values)


def component(values, width, start, forbidden=()):
    allowed = {i for i, v in enumerate(values) if not v & 0xC00 and v >> 12 != 1} - set(forbidden)
    if start not in allowed:
        return set()
    seen = {start}
    queue = deque([start])
    while queue:
        i = queue.popleft()
        x, y = i % width, i // width
        for xx, yy in ((x-1, y), (x+1, y), (x, y-1), (x, y+1)):
            j = yy * width + xx
            if 0 <= xx < width and 0 <= j < len(values) and j in allowed and j not in seen:
                seen.add(j)
                queue.append(j)
    return seen


def stretch(values, width, height, col, cols, row, rows):
    """Duplicate only a stripe whose adjacent full words are identical."""
    grid = [values[y*width:(y+1)*width] for y in range(height)]
    if cols:
        if col is None or not all(r[col] == r[col-1] for r in grid):
            raise ValueError('Column would split native scenery')
        grid = [r[:col] + [r[col]] * cols + r[col:] for r in grid]
    if rows:
        if row is None or grid[row] != grid[row-1]:
            raise ValueError('Row would split native scenery')
        grid = grid[:row] + [list(grid[row]) for _ in range(rows)] + grid[row:]
    return [v for r in grid for v in r], width + cols, height + rows


class Banks:
    def __init__(self, source):
        self.renderer = MapRenderer(source)
        self.source = Path(source)
        self.cache = {}

    def behavior(self, layout, word):
        cut = 640 if layout['layout_version'] == 'frlg' else 512
        mid = word & 1023
        bank = layout['secondary_tileset'] if mid >= cut else layout['primary_tileset']
        if bank not in self.cache:
            body = re.search(r'const struct Tileset ' + bank + r'\s*=\s*\{(.*?)\};', self.renderer.headers, re.S)[1]
            symbol = re.search(r'\.metatileAttributes\s*=\s*(\w+)', body)[1]
            path = re.search(r'\b' + symbol + r'\[\].*?"([^"]+)"', self.renderer.metas, re.S)[1]
            self.cache[bank] = (self.source / path).read_bytes()
        size = 4 if cut == 640 else 2
        index = mid-cut if mid >= cut else mid
        raw = self.cache[bank][index*size:(index+1)*size]
        if len(raw) != size:
            raise ValueError(('Missing native attribute', bank, mid))
        return int.from_bytes(raw, 'little') & (511 if size == 4 else 255)


def stage(layer, reference):
    reference = Path(reference)
    banks = Banks(reference)
    plan = json.loads((ROOT / 'tools/hoenn/data/legendary-cave-groups.json').read_text())
    layouts_doc = json.loads(read(layer, 'data/layouts/layouts.json'))
    layouts = {l['id']: l for l in layouts_doc['layouts']}
    groups = json.loads(read(layer, 'data/maps/map_groups.json'))
    original_groups = copy.deepcopy(groups)
    captures = {c['national_dex']: c for c in json.loads((reference / '.journey-sanctuaries').read_text())['captures']}
    world = read(layer, 'src/data/journey_world_map.h').decode()
    points = {m[1]: (int(m[3]), int(m[4])) for m in re.finditer(PAT, world)}
    area = read(layer, 'src/pokedex_area_screen.c').decode()
    dexmap = read(layer, 'src/data/journey_world_dex_locations.h').decode()
    records, scripts, extra_points = [], [], []
    # Complete native rooms retain their walls, staircases, lakes and crystals.
    templates = [
        ('JourneySanctuaryTitans', 11, 8),
        ('SealedChamber_OuterRoom', 5, 4),
        ('SealedChamber_InnerRoom', None, 10),
        ('AlteringCave', None, None),
        ('GraniteCave_StevensRoom', None, None),
        ('MarineCave_End', None, None),
        ('TerraCave_End', None, None),
    ]
    template_cache = {}
    for template_name, _, _ in templates:
        tm = json.loads(read(layer, f'data/maps/{template_name}/map.json'))
        tl = layouts[tm['layout']]
        template_cache[template_name] = (tm, tl, _values(layer, tl))
    # The pictured ladder/hatch occupies one complete metatile in each bank.
    hatch_ids = {'gTileset_NavelRock': 0x23F, 'gTileset_Cave': 0x23F,
                 'gTileset_MeteorFalls': 0x20D, 'gTileset_RusturfTunnel': 0x227,
                 'gTileset_Cave_Frlg': 0x285, 'gTileset_RockTunnel': 0x285,
                 'gTileset_CeruleanCave': 0x285}
    new_names = []
    changed = []
    for group in plan:
        name = group['map']
        mapping = json.loads(read(layer, f'data/maps/{name}/map.json'))
        original = copy.deepcopy(mapping)
        layout = layouts[mapping['layout']]
        values = _values(layer, layout)
        width, height = layout['width'], layout['height']
        legends = {int(re.fullmatch(r'JourneySanctuary_(\d+)', o['script'])[1]): o
                   for o in mapping['object_events'] if re.fullmatch(r'JourneySanctuary_(\d+)', o.get('script', ''))}
        if set(legends) != set(group['national_dex']):
            raise ValueError(('Changed encounter group', name))
        mapping['object_events'] = [o for o in mapping['object_events'] if o not in legends.values()]
        # All special actors were appended. Removing them cannot renumber a native actor.
        for i, o in enumerate(mapping['object_events']):
            if original['object_events'][i] != o:
                raise ValueError(('Native local ID would change', name))
        forbidden = {e['y']*width+e['x'] for key in ('warp_events', 'object_events', 'coord_events', 'bg_events')
                     for e in mapping.get(key, []) if isinstance(e.get('x'), int)}
        for dex in group['national_dex']:
            actor = copy.deepcopy(legends[dex])
            px, py = actor['x'], actor['y']
            at = py*width+px
            old_word = values[at]
            if old_word & 0xC00 or at in forbidden:
                raise ValueError(('Encounter entrance is not free floor', name, dex))
            bank = layout['secondary_tileset']
            if bank == 'gTileset_Lavaridge':
                # Native Jagged Pass doorway: full three-wide, two-high arch.
                donor = json.loads(read(layer, 'data/maps/JaggedPass/map.json'))
                dl = layouts[donor['layout']]
                if (dl['primary_tileset'], dl['secondary_tileset']) != (layout['primary_tileset'], bank):
                    raise ValueError('Foreign Fiery Path doorway bank')
                dv = _values(layer, dl)
                pattern = [[dv[(17+dy)*dl['width']+15+dx] for dx in range(3)] for dy in range(2)]
                options = []
                for y in range(2, height-1):
                    for x in range(1, width-1):
                        cells = [(yy*width+xx) for yy in (y-1,y) for xx in range(x-1,x+2)]
                        front = (y+1)*width+x
                        if all(values[i]&0xC00 and i not in forbidden for i in cells) and not values[front]&0xC00 and front not in forbidden:
                            options.append((abs(x-px)+abs(y-py), x, y))
                if not options:
                    raise ValueError('No complete Fiery Path wall portal fits')
                _, px, py = min(options)
                for dy in range(2):
                    for dx in range(3):
                        values[(py-1+dy)*width+px-1+dx] = pattern[dy][dx]
                at = py*width+px
            else:
                mid = hatch_ids[bank]
                values[at] = (old_word & ~1023) | mid
                if banks.behavior(layout, values[at]) != 0x61:
                    raise ValueError(('Hatch is not a native ladder', name, hex(mid)))
            forbidden.add(at)
            parent_warp = len(mapping['warp_events'])
            room_name = f'JourneyLegendRoom{dex:04d}'
            room_id = 'MAP_' + room_name.upper()
            room_layout_id = 'LAYOUT_' + room_name.upper()
            index = len(records)
            template_name, col, row = templates[index % len(templates)]
            template, tl, tv = template_cache[template_name]
            # Sizes vary without duplicating any corner or half of an object.
            cols = ((index // 7) % 5) * 2 if col is not None else 0
            rows = ((index // 35) % 3) * 2 if row is not None else 0
            rv, rw, rh = stretch(tv, tl['width'], tl['height'], col, cols, row, rows)
            exit_event = copy.deepcopy(template['warp_events'][0])
            ex, ey = exit_event['x'], exit_event['y']
            ex += cols if col is not None and ex >= col else 0
            ey += rows if row is not None and ey >= row else 0
            exit_index = ey*rw+ex
            if banks.behavior(tl, rv[exit_index]) not in range(0x60, 0x66):
                raise ValueError(('Template lacks a genuine native exit', template_name))
            seen = component(rv, rw, exit_index)
            spots = [(x,y) for y in range(2,rh-2) for x in range(2,rw-2)
                     if all((y+dy)*rw+x+dx in seen and banks.behavior(tl, rv[(y+dy)*rw+x+dx]) in (0,8,11,12)
                            for dx in (-1,0,1) for dy in (-1,0,1))]
            if not spots:
                raise ValueError(('No full sprite clearing', room_name, template_name))
            # Different focal points, with enough floor for the whole 32px body.
            ax, ay = max(spots, key=lambda p: (abs(p[0]-ex)+abs(p[1]-ey), -abs(p[0]-(3+(dex % max(1,rw-6))))))
            actor.update(x=ax, y=ay, elevation=rv[ay*rw+ax]>>12)
            if not actor['graphics_id'].startswith('OBJ_EVENT_GFX_SPECIES('):
                raise ValueError(('Statue in individual room', dex))
            new_layout = copy.deepcopy(tl)
            folder = 'data/layouts/' + room_name
            new_layout.update(id=room_layout_id, name=room_name+'_Layout', width=rw, height=rh,
                              blockdata_filepath=folder+'/map.bin', border_filepath=folder+'/border.bin')
            layouts_doc['layouts'].append(new_layout)
            room = copy.deepcopy(template)
            room.update(id=room_id, name=room_name, layout=room_layout_id, connections=None,
                        object_events=[actor], coord_events=[], bg_events=[], allow_escaping=False,
                        allow_cycling=False, requires_flash=False, show_map_name=False,
                        region=mapping.get('region','REGION_HOENN'), region_map_section=mapping['region_map_section'],
                        warp_events=[dict(x=ex, y=ey, elevation=rv[exit_index]>>12,
                                          dest_map=mapping['id'], dest_warp_id=str(parent_warp))])
            for key in ('shared_scripts_map', 'shared_events_map'):
                room.pop(key, None)
            mapping['warp_events'].append(dict(x=px, y=py, elevation=values[at]>>12,
                                               dest_map=room_id, dest_warp_id='0'))
            layer.stage(f'data/maps/{room_name}/map.json', json.dumps(room, indent=2)+'\n')
            layer.stage(new_layout['blockdata_filepath'], _pack(rv))
            layer.stage(new_layout['border_filepath'], read(layer, tl['border_filepath']))
            scripts.append(room_name+'_MapScripts::\n\tmap_script MAP_SCRIPT_ON_TRANSITION, JourneySanctuary_Sync\n\t.byte 0\n')
            species = captures[dex]['species']
            pattern = r'(if \(species == '+species+r'\b.*?SetSpecialMapHasMon\([^;]+;)'
            area, count = re.subn(pattern, lambda m: m[0].replace(mapping['id'], room_id), area, flags=re.S)
            if count != 1:
                raise ValueError(('Missing area location', dex))
            xy = points[mapping['id']]
            location_row = '{'+species+','+room_id+f',{xy[0]},{xy[1]},1,0'+'}'
            emitted = []
            def single_location(match):
                emitted.append(match[0])
                return location_row+',' if len(emitted) == 1 else ''
            dexmap, count = re.subn(r'\{'+species+r',MAP_\w+,\d+,\d+,1,0\},?',
                                    single_location, dexmap)
            if count < 1:
                raise ValueError(('Missing Dex location', dex))
            label = species.removeprefix('SPECIES_').split('_')[0][:12] + ' DEN'
            extra_points.append(f'    {{(MAP_GROUP({room_id})<<8)|MAP_NUM({room_id}), {mapping["region_map_section"]}, {xy[0]}, {xy[1]}, COMPOUND_STRING("{label}")}},\n')
            new_names.append(room_name)
            records.append(dict(national_dex=dex, species=species, parent=name, entrance=[px,py],
                                parent_warp=parent_warp, room=room_name, exit=[ex,ey], position=[ax,ay],
                                template=template_name, width=rw, height=rh, expanded_columns=cols,
                                expanded_rows=rows, flag=actor['flag'], script=actor['script'],
                                blockdata_sha256=hashlib.sha256(_pack(rv)).hexdigest()))
        if mapping['warp_events'][:len(original['warp_events'])] != original['warp_events']:
            raise ValueError(('Original warp changed', name))
        layer.stage(f'data/maps/{name}/map.json', json.dumps(mapping, indent=2)+'\n')
        layer.stage(layout['blockdata_filepath'], _pack(values))
        changed.append(mapping['id'])
    if len(records) != 105 or {r['national_dex'] for r in records} != set(captures):
        raise ValueError('Incomplete individual-room coverage')
    for offset in range(0, len(new_names), 60):
        group_name = 'gMapGroup_JourneyLegendRooms' + str(offset//60)
        if group_name in groups or len(groups['group_order']) > 127:
            raise ValueError('Unsafe appended room group')
        groups['group_order'].append(group_name)
        groups[group_name] = new_names[offset:offset+60]
    for name in original_groups['group_order']:
        if groups[name] != original_groups[name]:
            raise ValueError('Historical map IDs changed')
    # The point table is followed by its count; insert at its own closing brace.
    point_match = re.search(PAT, world)
    end = world.index('\n};', point_match.end())
    world = world[:end] + '\n' + ''.join(extra_points).rstrip('\n') + world[end:]
    layer.stage('data/maps/map_groups.json', json.dumps(groups, indent=2)+'\n')
    layer.stage('data/layouts/layouts.json', json.dumps(layouts_doc, indent=2)+'\n')
    layer.stage('src/data/journey_world_map.h', world)
    layer.stage('src/data/journey_world_dex_locations.h', dexmap)
    layer.stage('src/pokedex_area_screen.c', area)
    script_path = 'data/maps/JourneyLegendRooms.inc'
    layer.stage(script_path, '\n'.join(scripts))
    layer.stage('data/event_scripts.s', read(layer, 'data/event_scripts.s').decode()+f'\n\t.include "{script_path}"\n')
    return dict(rooms=records, total=105, parents=len(plan), changed_parent_maps=changed,
                original_warps_and_native_actor_ids_preserved=True,
                capture_scripts_flags_and_permissions_unchanged=True,
                source_audited=False, native_validated=False)


def refresh_saved_objects(layer, changed):
    path = 'src/load_save.c'
    text = read(layer, path).decode()
    signature = 'static void JourneyMigrateSeviiSaveGeometry(void)\n{'
    body = _braced(text, text.index(signature)+len(signature)-1)
    if '>=7' not in body or 'VERSION,7);' not in body:
        raise ValueError('Unexpected migration parent')
    older = (signature+body+'}').replace('JourneyMigrateSeviiSaveGeometry(void)', 'JourneyMigrateSeviiSaveGeometryVersion7(void)', 1)
    maps = ',\n        '.join(f'(MAP_GROUP({m})<<8)|MAP_NUM({m})' for m in changed)
    new = '''static void JourneyMigrateSeviiSaveGeometry(void)
{
    static const u16 changedMaps[]={MAPS};
    u16 packed;
    u32 i,j;
    if(VarGet(VAR_JOURNEY_SEVII_GEOMETRY_VERSION)>=8) return;
    JourneyMigrateSeviiSaveGeometryVersion7();
    packed=((u16)(u8)gSaveBlock1Ptr->location.mapGroup<<8)|(u8)gSaveBlock1Ptr->location.mapNum;
    for(i=0;i<ARRAY_COUNT(changedMaps);i++)
        if(changedMaps[i]==packed)
        {
            for(j=0;j<OBJECT_EVENTS_COUNT;j++)
                if(!gSaveBlock1Ptr->objectEvents[j].isPlayer
                 && gSaveBlock1Ptr->objectEvents[j].localId!=OBJ_EVENT_ID_FOLLOWER
                 && gSaveBlock1Ptr->objectEvents[j].localId!=OBJ_EVENT_ID_NPC_FOLLOWER)
                    gSaveBlock1Ptr->objectEvents[j].active=FALSE;
            CpuFill16(0,gSaveBlock1Ptr->objectEventTemplates,sizeof(gSaveBlock1Ptr->objectEventTemplates));
            gSaveBlock1Ptr->mapLayoutId=Overworld_GetMapHeaderByGroupAndId(packed>>8,packed&255)->mapLayoutId;
            sJourneyAtlasReloadSavedObjects=TRUE;
            break;
        }
    CpuFill16(0,gSaveBlock1Ptr->mapView,sizeof(gSaveBlock1Ptr->mapView));
    VarSet(VAR_JOURNEY_SEVII_GEOMETRY_VERSION,8);
}'''.replace('MAPS', maps)
    layer.stage(path, text.replace(signature+body+'}', older+'\n'+new, 1))
    path = 'include/constants/vars.h'
    text, n = re.subn(r'(#define\s+JOURNEY_SEVII_GEOMETRY_VERSION_CURRENT\s+)7\b', r'\g<1>8', read(layer,path).decode())
    if n != 1:
        raise ValueError('Unexpected geometry constant')
    layer.stage(path, text)
