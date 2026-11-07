"""Draw two standalone generated ocean aprons without changing movement grids."""
import hashlib
import json
import re
import struct
from collections import Counter
from functools import lru_cache
from pathlib import Path
from badge_story_layer import read
from marine_corner_coherence import adjacent
from sevii_boundary_camera import translate_block

PATH = 'src/fieldmap.c'
SCOPED_MAPS = ('JourneyWorldSea02', 'JourneyWorldFill21Right')
REPRO_CASES = [
    dict(label='sea02-west', map=SCOPED_MAPS[0], player=[0, 2], direction='left', neighbor='JourneyWorldSea01', target=[63, 2], cell=[-3, -2], neighbor_cell=[61, -2], expected_metatile=0x12B),
    dict(label='fill21-seven', map=SCOPED_MAPS[1], player=[2, 47], direction='down', neighbor='JourneyWorldSea07', target=[43, 0], cell=[-1, 47], neighbor_cell=[40, -1], expected_metatile=0x12B),
]
CONTROL_CASES = [
    dict(label='sea02-mouth-water-projection', map=SCOPED_MAPS[0], player=[24, 0], direction='up', neighbor='JourneyTwoThreeMouth', target=[0, 23], cell=[20, -1], neighbor_cell=[-4, 23], expected_metatile=0x243),
    dict(label='sea02-mouth-conflict', map=SCOPED_MAPS[0], player=[24, 0], direction='up', neighbor='JourneyTwoThreeMouth', target=[0, 23], cell=[23, -4], neighbor_cell=[-1, 20], expected_metatile=0x243),
    dict(label='fill21-cap', map=SCOPED_MAPS[1], player=[0, 34], direction='left', neighbor='JourneyWorldFill21Cap', target=[16, 34], cell=[-1, 36], neighbor_cell=[16, 36], expected_metatile=0x243),
]
OPENING_MAP = 'SevenIsland_Harbor_Frlg'
OPENING_NEIGHBOR = 'JourneySurfLink05101'


def seven_east_openings(inputs):
    """Read every real Surf opening; folded camera projections are not terrain."""
    rows = []
    for x, y, direction, xx, yy in inputs.perimeter(OPENING_MAP):
        if direction != 'right':
            continue
        target = inputs.target(OPENING_MAP, direction, xx, yy)
        if target is None:
            continue
        name, tx, ty = target
        a, b = inputs.word(OPENING_MAP, x, y), inputs.word(name, tx, ty)
        if not (a | b) & 0xC00 and inputs.behavior(OPENING_MAP, a) in inputs.water and inputs.behavior(name, b) in inputs.water:
            rows.append(dict(map=OPENING_MAP, player=[x, y], direction=direction,
                             neighbor=name, target=[tx, ty], blocks=[a, b]))
    return rows

C_HELPERS = r'''
// Only the two standalone generated oceans below need an apron owner. Their
// graph contains folded, distant routes as well as the adjacent visible coast.
// Pick the closest direct rectangle, independently of player/camera position.
static s32 JourneyMarineRectangleDistance(const struct MapLayout *layout, s32 x, s32 y)
{
    s32 dx = x < 0 ? -x : x >= layout->width ? x - layout->width + 1 : 0;
    s32 dy = y < 0 ? -y : y >= layout->height ? y - layout->height + 1 : 0;
    return dx + dy;
}

static bool8 JourneyMarineApronMetatile(s32 x, s32 y, u16 *result)
{
    const struct MapHeader *current = &gMapHeader;
    s32 i, j, closest = 0x7FFFFFFF;
    bool8 found = FALSE;
    u16 value = 0;
    if (current->connections == NULL)
        return FALSE;
    for (i = 0; i < current->connections->count; i++)
    {
        const struct MapHeader *next;
        s32 nx, ny, distance;
        if (!JourneyMarineConnectionOrigin(current->mapLayout,
            &current->connections->connections[i], &next, &nx, &ny))
            continue;
        distance = JourneyMarineRectangleDistance(next->mapLayout, x - nx, y - ny);
        if (distance < closest) closest = distance;
    }
    for (i = 0; i < current->connections->count; i++)
    {
        const struct MapHeader *next;
        const struct MapLayout *layout, *artLayout;
        s32 nx, ny, xx, yy, bw, bh;
        u16 block, candidate;
        bool8 actual;
        if (!JourneyMarineConnectionOrigin(current->mapLayout,
            &current->connections->connections[i], &next, &nx, &ny))
            continue;
        layout = next->mapLayout;
        xx = x - nx; yy = y - ny;
        if (JourneyMarineRectangleDistance(layout, xx, yy) != closest)
            continue;
        artLayout = layout;
        actual = xx >= 0 && yy >= 0 && xx < layout->width && yy < layout->height;
        block = actual ? layout->map[yy * layout->width + xx] : 0;
        // Mirror the owner's native connection strips. A perpendicular
        // overhang is valid; later connections overwrite earlier ones.
        if (!actual && xx >= -7 && xx < layout->width + 8
            && yy >= -7 && yy < layout->height + 7 && next->connections != NULL)
        {
            for (j = 0; j < next->connections->count; j++)
            {
                const struct MapConnection *c = &next->connections->connections[j];
                const struct MapHeader *other;
                s32 ox, oy, tx, ty;
                bool8 strip = (c->direction == CONNECTION_WEST && xx >= -7 && xx < 0)
                    || (c->direction == CONNECTION_EAST && xx >= layout->width && xx < layout->width + 8)
                    || (c->direction == CONNECTION_NORTH && yy >= -7 && yy < 0)
                    || (c->direction == CONNECTION_SOUTH && yy >= layout->height && yy < layout->height + 7);
                if (!strip || !JourneyMarineConnectionOrigin(layout, c, &other, &ox, &oy))
                    continue;
                tx = xx - ox; ty = yy - oy;
                if (tx >= 0 && ty >= 0 && tx < other->mapLayout->width && ty < other->mapLayout->height)
                {
                    artLayout = other->mapLayout;
                    block = artLayout->map[ty * artLayout->width + tx];
                    actual = TRUE;
                }
            }
        }
        if (!actual)
        {
            bw = layout->isFrlg ? layout->borderWidth : 2;
            bh = layout->isFrlg ? layout->borderHeight : 2;
            if (bw == 0 || bh == 0) return FALSE;
            xx %= bw; if (xx < 0) xx += bw;
            yy %= bh; if (yy < 0) yy += bh;
            block = layout->border[yy * bw + xx];
        }
        if (!JourneyMarineViewCompatible(artLayout, block, &candidate))
            return FALSE;
        if (found && value != candidate)
            return FALSE;
        value = candidate; found = TRUE;
    }
    if (found) *result = value;
    return found;
}
'''
GATE = '''    // Preserve the established resolver on every previously eligible coast.
    if ((gSaveBlock1Ptr->location.mapGroup == MAP_GROUP(MAP_JOURNEYWORLDSEA02)
            && gSaveBlock1Ptr->location.mapNum == MAP_NUM(MAP_JOURNEYWORLDSEA02))
        || (gSaveBlock1Ptr->location.mapGroup == MAP_GROUP(MAP_JOURNEYWORLDFILL21RIGHT)
            && gSaveBlock1Ptr->location.mapNum == MAP_NUM(MAP_JOURNEYWORLDFILL21RIGHT)))
        return JourneyMarineApronMetatile(x, y, result);
'''


def repair(layer):
    before = read(layer, PATH).decode()
    anchor = 'static bool8 JourneyMarineCornerMetatile(s32 x, s32 y, u16 *result)\n{'
    assert before.count(anchor) == 1 and 'JourneyMarineApronMetatile' not in before
    # Keep declarations before statements for the repository's C dialect.
    after = before.replace(anchor, C_HELPERS + '\n' + anchor)
    insertion = '    if (!JourneyMarineViewMap(current) || current->connections == NULL)\n'
    assert after.count(insertion) == 1
    after = after.replace(insertion, GATE + insertion)
    layer.stage(PATH, after)
    return dict(kind='generated-coast-camera-aprons', scoped_maps=list(SCOPED_MAPS),
                changed_paths=[PATH], map_blocks_events_connections_world_map_unchanged=True,
                undefined_movement_collision_elevation_and_border_id_unchanged=True,
                existing_camera_resolver_preserved_outside_scope=True,
                nearest_rectangle_manhattan_owner=True, disagreeing_or_incompatible_owners_rejected=True,
                native_connection_strip_last_match_wins=True,
                source_only_raw_conflicts=30, reproduction_cases=REPRO_CASES, control_cases=CONTROL_CASES,
                before_sha256=hashlib.sha256(before.encode()).hexdigest(), after_sha256=hashlib.sha256(after.encode()).hexdigest())


def apron_owner(inputs, name, x, y):
    owners = []
    for other, dx, dy in adjacent(inputs, name):
        l = inputs.layout(other); xx, yy = x-dx, y-dy
        distance = max(-xx, xx-l['width']+1, 0) + max(-yy, yy-l['height']+1, 0)
        owners.append(dict(map=other, origin=[dx, dy], cell=[xx, yy], distance=distance))
    return [r for r in owners if r['distance'] == min(q['distance'] for q in owners)] if owners else []


@lru_cache(None)
def _bank(source, name):
    source = Path(source)
    headers = (source/'src/data/tilesets/headers.h').read_text()
    defs = (source/'src/data/tilesets/metatiles.h').read_text()
    body = re.search(r'const struct Tileset '+re.escape(name)+r'\s*=\s*\{(.*?)\};', headers, re.S)[1]
    fields = dict(re.findall(r'\.(\w+)\s*=\s*(\w+)\s*,', body))
    raw = {}
    for field in ('metatiles', 'metatileAttributes'):
        path = re.search(r'\b'+re.escape(fields[field])+r'\[\].*?"([^"]+)"', defs)[1]
        raw[field] = (source/path).read_bytes()
    return fields, raw


def compatible(inputs, source_map, target_map, block):
    a, b = inputs.layout(source_map), inputs.layout(target_map)
    frlg = a['layout_version'] == 'frlg'; to_frlg = b['layout_version'] == 'frlg'
    mid = block & 1023
    if frlg != to_frlg:
        allowed = {0x12B, 0x243, 0x110, 0x111, 0x118, 0x119, 0x10C, 0x10D, 0x10E, 0x114, 0x115, 0x116, 0x11C, 0x11D, 0x11E} if frlg else {0x170, 0x1F9, 0x150, 0x151, 0x158, 0x159, 0x11B, 0x11C, 0x11D, 0x123, 0x124, 0x125, 0x12B, 0x12C, 0x12D}
        return translate_block(block, frlg, to_frlg)&1023 if mid in allowed else None
    cutoff, size = (640, 4) if frlg else (512, 2)
    field = 'primary_tileset' if mid < cutoff else 'secondary_tileset'; index = mid if mid < cutoff else mid-cutoff
    af, ar = _bank(str(inputs.source), a[field]); bf, br = _bank(str(inputs.source), b[field])
    if ar['metatiles'][index*16:index*16+16] != br['metatiles'][index*16:index*16+16] or ar['metatileAttributes'][index*size:index*size+size] != br['metatileAttributes'][index*size:index*size+size]: return None
    # Native callback/graphics/palettes are shared by these dedicated aliases.
    if any(af.get(k) != bf.get(k) for k in ('tiles', 'palettes', 'callback')): return None
    return mid


def _owner_view(inputs, owner):
    name = owner['map']; x, y = owner['cell']; l = inputs.layout(name)
    if 0 <= x < l['width'] and 0 <= y < l['height']:
        return dict(kind='owner-actual', map=name, cell=[x,y], block=inputs.word(name,x,y))
    found = None
    if -7 <= x < l['width']+8 and -7 <= y < l['height']+7:
        origins = iter(adjacent(inputs,name))
        for c in inputs.maps[name].get('connections') or []:
            if c['direction'] not in ('left','right','up','down'): continue
            other, dx, dy = next(origins); q = inputs.layout(other); xx, yy = x-dx, y-dy
            strip = {'left': -7 <= x < 0, 'right': l['width'] <= x < l['width']+8,
                     'up': -7 <= y < 0, 'down': l['height'] <= y < l['height']+7}[c['direction']]
            if strip and 0 <= xx < q['width'] and 0 <= yy < q['height']:
                found = dict(kind='owner-native-connection', map=other, cell=[xx,yy], block=inputs.word(other,xx,yy))
    if found: return found
    bw,bh = (l.get('border_width',2),l.get('border_height',2)) if l['layout_version']=='frlg' else (2,2)
    raw = (inputs.source/l['border_filepath']).read_bytes(); xx,yy=x % bw,y % bh
    return dict(kind='owner-border', map=name, cell=[xx,yy], block=struct.unpack_from('<H',raw,2*(yy*bw+xx))[0])


def source_apron_view(inputs, name, x, y):
    assert name in SCOPED_MAPS
    rows=[]
    for owner in apron_owner(inputs,name,x,y):
        draw = _owner_view(inputs,owner); mid = compatible(inputs,draw['map'],name,draw['block'])
        rows.append(dict(owner=owner, drawing=draw, metatile=mid))
    mids={r['metatile'] for r in rows}
    accepted = len(mids)==1 and None not in mids
    return dict(map=name,cell=[x,y],owners=rows,accepted=accepted,metatile=next(iter(mids)) if accepted else None)


def legacy_metatile(inputs, name, x, y):
    """Model the old getter for these fixtures, including native strip priority."""
    own = _owner_view(inputs, dict(map=name, cell=[x, y]))
    if own['kind'] != 'owner-border':
        return compatible(inputs, own['map'], name, own['block'])
    fallback = compatible(inputs, name, name, own['block'])
    layout = inputs.layout(name)
    # These are the exact eligibility rules preserved from layer 170.
    groups = {n for n in inputs.maps if n.startswith('JourneySurfLink')}
    eligible = name in groups or any(q in groups for q, _, _ in adjacent(inputs, name))
    eligible |= inputs.maps[name].get('map_type') == 'MAP_TYPE_OCEAN_ROUTE' and layout['primary_tileset'] == 'gTileset_JourneySeviiSea'
    if not eligible:
        return fallback
    values = []
    for q, dx, dy in adjacent(inputs, name):
        for other, ox, oy in [(q, dx, dy)]+[(r, dx+rx, dy+ry) for r, rx, ry in adjacent(inputs, q)]:
            target = inputs.layout(other); xx, yy = x-ox, y-oy
            if 0 <= xx < target['width'] and 0 <= yy < target['height']:
                mid = compatible(inputs, other, name, inputs.word(other, xx, yy))
                if mid is not None:
                    values.append(mid)
    if values:
        return values[0] if len(set(values)) == 1 else fallback
    origins = iter(adjacent(inputs, name))
    for c in inputs.maps[name].get('connections') or []:
        if c['direction'] not in ('left', 'right', 'up', 'down'):
            continue
        other, dx, dy = next(origins)
        if not {'left': x < 0, 'right': x >= layout['width'], 'up': y < 0, 'down': y >= layout['height']}[c['direction']]:
            continue
        target = inputs.layout(other)
        bw, bh = (target.get('border_width', 2), target.get('border_height', 2)) if target['layout_version'] == 'frlg' else (2, 2)
        if not bw or not bh:
            continue
        raw = (inputs.source/target['border_filepath']).read_bytes()
        block = struct.unpack_from('<H', raw, 2*(((y-dy) % bh)*bw+(x-dx) % bw))[0]
        mid = compatible(inputs, other, name, block)
        if mid is not None:
            values.append(mid)
    return values[0] if values and len(set(values)) == 1 else fallback


def census(inputs):
    rows=[]; connected=0
    for name in sorted(inputs.maps):
        direct=list(adjacent(inputs,name))
        if not direct: continue
        connected+=1; l=inputs.layout(name); w,h=l['width'],l['height']
        candidates=[(r,nx+rx,ny+ry) for q,nx,ny in direct for r,rx,ry in adjacent(inputs,q) if r!=name]
        for y in range(-7,h+7):
            for x in range(-7,w+8):
                if 0<=x<w and 0<=y<h:continue
                if any(0<=x-dx<inputs.layout(q)['width'] and 0<=y-dy<inputs.layout(q)['height'] for q,dx,dy in direct):continue
                nodes={}
                for q,dx,dy in candidates:
                    t=inputs.layout(q);xx,yy=x-dx,y-dy
                    if 0<=xx<t['width'] and 0<=yy<t['height']:
                        block=inputs.word(q,xx,yy);mid=translate_block(block,t['layout_version']=='frlg',l['layout_version']=='frlg')&1023
                        nodes[q,xx,yy]=dict(map=q,cell=[xx,yy],block=block,camera_metatile=mid)
                if len({r['camera_metatile'] for r in nodes.values()})>1:
                    row=dict(map=name,cell=[x,y],candidates=list(nodes.values()))
                    if name in SCOPED_MAPS:row['canonical_apron']=source_apron_view(inputs,name,x,y)
                    rows.append(row)
    return dict(connected_maps=connected,raw_conflicting_cells=len(rows),raw_conflicting_maps=dict(Counter(r['map'] for r in rows)),conflicts=rows,
                raw_conflicts_are_not_claimed_eliminated=True)


def audit_source(current, old):
    class Capture:
        source=old.source
        expected={PATH:hashlib.sha256((old.source/PATH).read_bytes()).hexdigest()}
        outputs={}
        def stage(self,path,content):self.outputs[path]=content.encode() if isinstance(content,str) else content
    capture=Capture(); metadata=repair(capture)
    assert (current.source/PATH).read_bytes()==capture.outputs[PATH], 'Unexpected camera runtime changes'
    cases = []
    names = set(SCOPED_MAPS)
    for case in REPRO_CASES+CONTROL_CASES:
        row=source_apron_view(current,case['map'],*case['cell'])
        assert row['accepted'] and row['metatile']==case['expected_metatile'],(case,row)
        before = legacy_metatile(old, case['map'], *case['cell'])
        assert before == 0x243, (case, before)
        cases.append(dict(case=case, before=before, after=row['metatile'],
                          expected=case['expected_metatile'], passed=True, owner_evidence=row))
        names.update((case['neighbor'],))
        names.update(r['drawing']['map'] for r in row['owners'])
    result=census(current)
    previous=census(old)
    assert result['raw_conflicting_cells']==30 and result['raw_conflicting_maps']=={'JourneyWorldFill21Right':13,'JourneyWorldSea02':17},result['raw_conflicting_maps']
    def raw(rows):
        return [{k: v for k, v in row.items() if k != 'canonical_apron'} for row in rows['conflicts']]
    assert raw(result) == raw(previous), 'Camera repair must not erase raw source contradictions'
    openings = seven_east_openings(current)
    assert openings == seven_east_openings(old)
    assert [(r['neighbor'],r['player'],r['target']) for r in openings] == [(OPENING_NEIGHBOR,[16,y],[0,y]) for y in range(1,12)]
    names.update((OPENING_MAP, OPENING_NEIGHBOR))
    return dict(metadata,map_names=sorted(names),changed_camera_maps=sorted(SCOPED_MAPS),
                scoped_policy_cases=cases,unresolved_cells=0,unresolved_scope='reviewed-aperture-policy',
                full_world_camera_certified=False,raw_conflicting_cells=result['raw_conflicting_cells'],
                raw_conflicting_maps=result['raw_conflicting_maps'],raw_source_conflicts_unchanged=True,
                expanded_census=result,previous_raw_conflicting_cells=previous['raw_conflicting_cells'],
                seven_east_openings=openings,seven_east_openings_source_unchanged=True,
                source_only=True,native_controller_and_scanout_proof_required=True)
