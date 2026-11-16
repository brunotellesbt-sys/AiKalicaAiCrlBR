"""Terrain-authenticated one-time rescue of published533 coordinates.

Offline RLE tables cover every old cell, including corrupt blocked positions.
Keep exact safe global positions and whole scenery first. Fallback targets are
frozen safe land/water, outside events and trainer sight. This save-only table
never creates travel edges or changes the atlas. The native battery replay is
a separate obligation even after host C and source coverage pass.
"""
from collections import Counter
import hashlib
import json
import re
import struct

from atlas_surf_migration import _safe_behaviors, _destinations, _mode, _occupied, _distance
from badge_story_layer import read

HEADER_PATH = 'src/data/journey_atlas_candidate_migration.h'
# Dry rescue near the four admitted trips, outside trainer sight and bridge
# transitions. Checked against actual terrain; no UI coordinate is an edge.
NATIVE_DRY = dict(route12=['Route12_Frlg', 9, 45],
                  treasure=['OneIsland_TreasureBeach_Frlg', 14, 20],
                  pacifidlog=['PacifidlogTown', 10, 25],
                  bond=['ThreeIsland_Port_Frlg', 13, 17])
NATIVE_SURF = dict(bond=['ThreeIsland_BondBridge_Frlg', 47, 13])


def build_tables(old, old_plan, new, plan, *, physical_graph, native_features=None):
    if physical_graph is None or physical_graph.ocean_component is None or physical_graph.source is not new:
        raise ValueError('Candidate save targets need the actual passing current physical graph')
    enums = _safe_behaviors(new)
    candidates, safe, _ = _destinations(new, plan, enums)
    original_safe_count=len(safe)
    safe={key:p for key,p in safe.items() if physical_graph.component(
        [p['map'],*p['tile']],1 if p['mode']=='surf' else 0)==physical_graph.ocean_component}
    candidates={'walk':{},'surf':{}}
    for point in safe.values():
        mode,pixel=point['mode'],point['atlas_pixel']
        gx,gy=point['global_tile'];score=(abs(gx%8-4)+abs(gy%8-4),point['packed_id'],*reversed(point['tile']))
        previous=candidates[mode].get(pixel)
        if previous is None or score<previous[0]:candidates[mode][pixel]=(score,point)
    candidates={mode:{pixel:value[1] for pixel,value in rows.items()} for mode,rows in candidates.items()}
    if not candidates['walk'] or not candidates['surf']:
        raise ValueError('Both save modes need safe terrain with a physical exit/return to the ocean')
    by_world = {}
    for point in safe.values():
        key = (*point['global_tile'], point['mode'])
        if key in by_world:
            raise ValueError('Overlapping safe migration terrain')
        by_world[key] = point
    native_pixels = {}
    for feature in (native_features or {}).get('features', []):
        choices = {}
        for mode, point in [('surf', NATIVE_SURF.get(feature['key'], feature['point'])),
                            ('walk', NATIVE_DRY[feature['key']])]:
            name, x, y = point
            if _mode(new, name, x, y, enums) != mode or (x, y) in _occupied(new.maps[name]):
                raise ValueError(('Native save rescue is not safe terrain', point))
            if physical_graph.component(point,1 if mode=='surf' else 0)!=physical_graph.ocean_component:
                raise ValueError(('Native save rescue has no physical ocean roundtrip',point))
            choices[mode] = dict(map=name, packed_id=new.identities[name], tile=[x, y], mode=mode,
                                 elevation=1 if mode == 'surf' else 3, word=new.word(name, x, y))
        for pixel in feature['pixels']:
            native_pixels[tuple(pixel)] = choices
    new_chunks = {r['name']: r for r in plan['chunks']}
    destinations, indexes, maps, runs, warps = [], {}, [], [], []
    reasons = Counter()
    fallback_cache = {}

    def rescue(pixel, mode):
        key = pixel, mode
        if key not in fallback_cache:
            choices = candidates[mode]
            selected = pixel if pixel in choices else min(choices, key=lambda p: (_distance(pixel, p), p))
            fallback_cache[key] = choices[selected]
        return fallback_cache[key]

    def target(row, x, y, desired):
        name = row['name']; ox, oy = row['origin']; gx, gy = ox+x, oy+y
        old_word = old.word(name, x, y)
        same = new_chunks.get(name)
        point = safe.get((name, x, y))
        if (same is not None and point is not None and point['mode'] == desired
                and old_word == point['word'] and
                (row['origin'] == same['origin'] or row.get('member_stamps'))):
            return point, False, 'exact-native-scenery' if row.get('member_stamps') else 'exact-unchanged-cell'
        point = by_world.get((gx, gy, desired))
        if point is not None:
            return point, False, 'exact-world-cell'
        pixel = gx//8, gy//8
        if pixel in native_pixels:
            return native_pixels[pixel][desired], True, 'admitted-native-glyph'
        return rescue(pixel[0] | pixel[1] << 8, desired), True, 'safe-frozen-rescue'

    def index(point, absolute, x, y):
        dx, dy = point['tile'] if absolute else [point['tile'][0]-x, point['tile'][1]-y]
        flags = (1 if point['mode'] == 'walk' else 2) | (0x80 if absolute else 0)
        key = point['packed_id'], dx, dy, flags, point['elevation']
        if not 0 <= key[0] < 0x8000 or key[0] & 255 >= 128:
            raise ValueError('Migration target exceeds signed WarpData identity')
        if any(not -32768 <= v < 32768 for v in (dx, dy)):
            raise ValueError('Migration coordinate exceeds signed native position')
        if key not in indexes:
            if len(destinations) >= 65535:
                raise ValueError('Migration target index exceeds u16')
            indexes[key] = len(destinations); destinations.append(key)
        return indexes[key]

    for row in sorted(old_plan['chunks'], key=lambda r: (r['group_index'], r['number'])):
        name = row['name']; width, height = row['width'], row['height']
        packed = (row['group_index'] << 8) | row['number']
        if old.identities[name] != packed or new.identities.get(name) != packed:
            raise ValueError(('Published map ID not preserved', name))
        first = len(runs); previous = None
        for y in range(height):
            for x in range(width):
                mode = _mode(old, name, x, y, enums)
                # Real old land/water controls its own legal avatar state.
                # Ambiguous bridges/blocked positions use saved Surf preference.
                selections = []
                for desired in ([mode, mode] if mode else ['walk', 'surf']):
                    point, absolute, reason = target(row, x, y, desired)
                    selections.append(index(point, absolute, x, y)); reasons[reason] += 1
                key = tuple(selections); end = y*width+x+1
                if key == previous:
                    runs[-1] = (end, *key)
                else:
                    runs.append((end, *key)); previous = key
        maps.append((packed, width, height, first, len(runs)-first))
        events = old.maps[name].get('warp_events') or []
        for i, event in enumerate(events):
            if name not in new_chunks:
                raise ValueError(('Retired candidate portal has no authored destination', name, i))
            current = new.maps[name].get('warp_events') or []
            if (i >= len(current) or any(current[i][k] != event[k] for k in ('dest_map', 'dest_warp_id'))):
                raise ValueError(('Candidate portal identity changed', name, i))
            warps.append((packed, i, packed, i))
    if len(runs) >= 65535:
        raise ValueError('Migration RLE exceeds u16')
    old.assert_unchanged(); new.assert_unchanged()
    binary = (b''.join(struct.pack('<HBBHH', *r) for r in maps)
              + b''.join(struct.pack('<HHH', *r) for r in runs)
              + b''.join(struct.pack('<HhhBB', *r) for r in destinations)
              + b''.join(struct.pack('<HBHB', *r) for r in warps))
    return dict(maps=maps, runs=runs, targets=destinations, warps=warps,
                table_bytes=len(binary), table_sha256=hashlib.sha256(binary).hexdigest(),
                source_cell_count=sum(r[1]*r[2] for r in maps), reasons=dict(reasons),
                disconnected_safe_cells_excluded=original_safe_count-len(safe),
                targets_require_physical_ocean_roundtrip=True,
                native_behavior_enums=enums['named_ids'], old_input_sha256=dict(old.inputs),
                new_input_sha256=dict(new.inputs), native_battery_validated=False)


def resolve(tables, packed, x, y, surfing=False):
    """Host oracle used for independent coverage and emitted-C equivalence."""
    row = next((r for r in tables['maps'] if r[0] == packed), None)
    if row is None:
        return None
    _, width, height, first, count = row
    if not (0 <= x < width and 0 <= y < height):
        x, y = width//2, height//2
    point = y*width+x
    run = next(r for r in tables['runs'][first:first+count] if r[0] > point)
    target = tables['targets'][run[2 if surfing else 1]]
    new, a, b, flags, elevation = target
    return new, a if flags & 128 else x+a, b if flags & 128 else y+b, flags & 3, elevation


def render(tables, *, refresh_native_maps=()):
    code = '''// Save-only candidate533 migration; no live navigation reads these tables.
#ifndef GUARD_JOURNEY_ATLAS_CANDIDATE_MIGRATION_H
#define GUARD_JOURNEY_ATLAS_CANDIDATE_MIGRATION_H
struct JourneyCandidateMap { u16 map; u8 width,height; u16 first,count; };
struct JourneyCandidateRun { u16 end,foot,surf; };
struct JourneyCandidateTarget { u16 map; s16 x,y; u8 flags,elevation; };
struct __attribute__((packed)) JourneyCandidateWarp { u16 oldMap; u8 oldId; u16 newMap; u8 newId; };
typedef char JourneyCandidateMapEightBytes[(sizeof(struct JourneyCandidateMap)==8)?1:-1];
typedef char JourneyCandidateRunSixBytes[(sizeof(struct JourneyCandidateRun)==6)?1:-1];
typedef char JourneyCandidateTargetEightBytes[(sizeof(struct JourneyCandidateTarget)==8)?1:-1];
typedef char JourneyCandidateWarpSixBytes[(sizeof(struct JourneyCandidateWarp)==6)?1:-1];
'''
    for kind, name, rows in [('JourneyCandidateMap','sCandidateMaps',tables['maps']),
                             ('JourneyCandidateRun','sCandidateRuns',tables['runs']),
                             ('JourneyCandidateTarget','sCandidateTargets',tables['targets']),
                             ('JourneyCandidateWarp','sCandidateWarps',tables['warps'])]:
        code += 'static const struct '+kind+' '+name+'[]={\n'
        code += ''.join('    {'+','.join(map(str,r))+'},\n' for r in rows) if rows else '    {0},\n'
        code += '};\n'
    code += 'static const u32 sCandidateWarpCount='+str(len(tables['warps']))+';\n'
    native = sorted(set(refresh_native_maps))
    code += 'static bool8 JourneyCandidateNativeObjectsChanged(u16 map)\n{\n'
    code += '    return '+(' || '.join('map=='+str(p) for p in native) if native else '(void)map, FALSE')+';\n}\n'
    return code + r'''
static EWRAM_DATA bool8 sJourneyCandidateUpgrade;
static EWRAM_DATA struct JourneyAtlasSaveMove sJourneyCandidateMove;

static bool8 JourneyCandidateSavedSurf(void)
{
    u32 i;
    u16 graphics = GetPlayerAvatarGraphicsIdByStateIdAndGender(PLAYER_AVATAR_STATE_SURFING,gSaveBlock2Ptr->playerGender);
    graphics = (graphics >> 8) | (graphics << 8);
    for (i=0;i<OBJECT_EVENTS_COUNT;i++)
        if (gSaveBlock1Ptr->objectEvents[i].isPlayer)
            return gSaveBlock1Ptr->objectEvents[i].graphicsId == graphics;
    return FALSE;
}

static const struct JourneyCandidateMap *JourneyCandidateFind(u16 packed)
{
    u32 lo=0,hi=ARRAY_COUNT(sCandidateMaps),mid;
    while(lo<hi)
    {
        mid=lo+(hi-lo)/2;
        if(sCandidateMaps[mid].map<packed) lo=mid+1;
        else hi=mid;
    }
    if(lo==ARRAY_COUNT(sCandidateMaps)||sCandidateMaps[lo].map!=packed) return NULL;
    return &sCandidateMaps[lo];
}

static const struct JourneyAtlasSaveMove *JourneyCandidateResolve(u8 group,u8 num,s16 x,s16 y)
{
    const struct JourneyCandidateMap *map=JourneyCandidateFind(((u16)group<<8)|num);
    const struct JourneyCandidateTarget *target;
    const struct JourneyCandidateRun *run;
    u32 lo,hi,mid,point;
    s16 sourceX=x,sourceY=y;
    if(map==NULL) return NULL;
    // Invalid direct coordinates and event sentinels use the declared centre.
    if(x<0||y<0||x>=map->width||y>=map->height) { x=map->width/2;y=map->height/2; }
    point=y*map->width+x;lo=map->first;hi=lo+map->count;
    while(lo<hi)
    {
        mid=lo+(hi-lo)/2;
        if(sCandidateRuns[mid].end<=point) lo=mid+1;
        else hi=mid;
    }
    if(lo>=map->first+map->count) return NULL;
    run=&sCandidateRuns[lo];
    target=&sCandidateTargets[JourneyCandidateSavedSurf()?run->surf:run->foot];
    sJourneyCandidateMove.oldGroup=group;sJourneyCandidateMove.oldNum=num;
    sJourneyCandidateMove.newGroup=target->map>>8;sJourneyCandidateMove.newNum=target->map&255;
    sJourneyCandidateMove.dx=(target->flags&128?target->x:x+target->x)-sourceX;
    sJourneyCandidateMove.dy=(target->flags&128?target->y:y+target->y)-sourceY;
    sJourneyCandidateMove.mode=target->flags&3;sJourneyCandidateMove.elevation=target->elevation;
    sJourneyCandidateMove.left=sourceX;sJourneyCandidateMove.top=sourceY;
    sJourneyCandidateMove.right=sourceX;sJourneyCandidateMove.bottom=sourceY;
    return &sJourneyCandidateMove;
}

static bool8 JourneyCandidateMigrateWarp(struct WarpData *warp)
{
    u32 i;
    u16 packed=((u16)(u8)warp->mapGroup<<8)|(u8)warp->mapNum;
    const struct JourneyAtlasSaveMove *move;
    if(JourneyCandidateFind(packed)==NULL) return FALSE;
    if(warp->warpId>=0)
        for(i=0;i<sCandidateWarpCount;i++)
            if(sCandidateWarps[i].oldMap==packed&&sCandidateWarps[i].oldId==warp->warpId)
            {
                warp->mapGroup=sCandidateWarps[i].newMap>>8;warp->mapNum=sCandidateWarps[i].newMap&255;
                warp->warpId=sCandidateWarps[i].newId;
                return TRUE;
            }
    // Unknown event IDs have no position; do not use their sentinel as one.
    if(warp->warpId>=0) warp->x=warp->y=-1;
    move=JourneyCandidateResolve(warp->mapGroup,warp->mapNum,warp->x,warp->y);
    if(move==NULL) return FALSE;
    warp->mapGroup=move->newGroup;warp->mapNum=move->newNum;
    warp->x+=move->dx;warp->y+=move->dy;warp->warpId=-1;
    return TRUE;
}
#endif
'''


def upgrade_restore_source(text):
    """Upgrade only the exact reviewed version2 restore, keeping v1/v2 paths."""
    def replace(old, new):
        nonlocal text
        if text.count(old) != 1:
            raise ValueError(('Candidate migration restore anchor changed', old[:100]))
        text = text.replace(old, new, 1)

    replace('#include "data/journey_atlas_migration.h"',
            '#include "data/journey_atlas_migration.h"\n#include "data/journey_atlas_candidate_migration.h"')
    replace('    u32 i;\n    for (i = 0; i < ARRAY_COUNT(sJourneyAtlasSaveMoves); i++)',
            '    u32 i;\n    if (sJourneyCandidateUpgrade)\n        return JourneyCandidateResolve(group,num,x,y);\n'
            '    for (i = 0; i < ARRAY_COUNT(sJourneyAtlasSaveMoves); i++)')
    replace('    s16 x = warp->x, y = warp->y;\n',
            '    s16 x = warp->x, y = warp->y;\n'
            '    if (sJourneyCandidateUpgrade && JourneyCandidateMigrateWarp(warp))\n        return;\n')
    start = text.index('static void JourneyMigrateSeviiSaveGeometry(void)\n{')
    old = text[start:]
    # migration_source appends this final wrapper immediately after its
    # resolver/apply functions. In a full source, stop at its exact closing.
    end = old.index('    VarSet(VAR_JOURNEY_SEVII_GEOMETRY_VERSION, 2);\n}')
    old = old[:end+len('    VarSet(VAR_JOURNEY_SEVII_GEOMETRY_VERSION, 2);\n}')]
    expected = '''static void JourneyMigrateSeviiSaveGeometry(void)
{
    u16 version = VarGet(VAR_JOURNEY_SEVII_GEOMETRY_VERSION);
    if (version >= 2)
        return;
    if (version < 1)
        JourneyMigrateSeviiSaveGeometryVersion1();
    JourneyAtlasMigrateCurrentSave();
    // location was migrated using authoritative saved pos, not stale x/y.
    JourneyAtlasMigrateSavedWarp(&gSaveBlock1Ptr->continueGameWarp);
    JourneyAtlasMigrateSavedWarp(&gSaveBlock1Ptr->dynamicWarp);
    JourneyAtlasMigrateSavedWarp(&gSaveBlock1Ptr->lastHealLocation);
    JourneyAtlasMigrateSavedWarp(&gSaveBlock1Ptr->escapeWarp);
    VarSet(VAR_JOURNEY_SEVII_GEOMETRY_VERSION, 2);
}'''
    if old != expected:
        raise ValueError('Candidate migration must retain the exact version2 wrapper')
    replace(old, '''static void JourneyMigrateSeviiSaveGeometry(void)
{
    u16 version = VarGet(VAR_JOURNEY_SEVII_GEOMETRY_VERSION);
    u32 i;
    u16 packed;
    if (version >= 3)
        return;
    // Old0/1 translate directly into the current mesh. Only published533
    // saves use the candidate table; never run both on the same position.
    sJourneyCandidateUpgrade = (version == 2);
    if (version < 1)
        JourneyMigrateSeviiSaveGeometryVersion1();
    JourneyAtlasMigrateCurrentSave();
    JourneyAtlasMigrateSavedWarp(&gSaveBlock1Ptr->continueGameWarp);
    JourneyAtlasMigrateSavedWarp(&gSaveBlock1Ptr->dynamicWarp);
    JourneyAtlasMigrateSavedWarp(&gSaveBlock1Ptr->lastHealLocation);
    JourneyAtlasMigrateSavedWarp(&gSaveBlock1Ptr->escapeWarp);
    // Reload templates only where native actors moved. Other native NPC
    // positions and quest progress survive. Migrated seas already reload.
    packed=((u16)(u8)gSaveBlock1Ptr->location.mapGroup<<8)|(u8)gSaveBlock1Ptr->location.mapNum;
    if (JourneyCandidateNativeObjectsChanged(packed))
    {
        for(i=0;i<OBJECT_EVENTS_COUNT;i++)
            if(!gSaveBlock1Ptr->objectEvents[i].isPlayer
             && gSaveBlock1Ptr->objectEvents[i].localId!=OBJ_EVENT_ID_FOLLOWER
             && gSaveBlock1Ptr->objectEvents[i].localId!=OBJ_EVENT_ID_NPC_FOLLOWER)
                gSaveBlock1Ptr->objectEvents[i].active=FALSE;
        CpuFill16(0,gSaveBlock1Ptr->objectEventTemplates,sizeof(gSaveBlock1Ptr->objectEventTemplates));
        gSaveBlock1Ptr->mapLayoutId=Overworld_GetMapHeaderByGroupAndId(packed>>8,packed&255)->mapLayoutId;
        sJourneyAtlasReloadSavedObjects=TRUE;
    }
    // Discard saved graphics of repaired shoreline pieces on the first
    // Continue, including saves on unchanged native city map IDs.
    CpuFill16(0,gSaveBlock1Ptr->mapView,sizeof(gSaveBlock1Ptr->mapView));
    sJourneyCandidateUpgrade=FALSE;
    VarSet(VAR_JOURNEY_SEVII_GEOMETRY_VERSION,3);
}''')
    return text


def stage(layer, tables, *, refresh_native_maps):
    if HEADER_PATH in layer.outputs or (layer.source/HEADER_PATH).exists():
        raise ValueError('Preserve the existing candidate migration preparation')
    code = render(tables, refresh_native_maps=refresh_native_maps)
    layer.stage(HEADER_PATH, code)
    path = 'src/load_save.c'
    layer.stage(path, upgrade_restore_source(read(layer, path).decode()))
    path = 'include/constants/vars.h'; text = read(layer, path).decode()
    text, count = re.subn(r'(#define\s+JOURNEY_SEVII_GEOMETRY_VERSION_CURRENT\s+)2\b', r'\g<1>3', text)
    if count != 1:
        raise ValueError('Expected installed version2 migration before candidate533 upgrade')
    layer.stage(path, text)
    return dict(kind='candidate533-save-coordinate-upgrade', version=3, maps=len(tables['maps']),
                source_cells=tables['source_cell_count'], table_bytes=tables['table_bytes'],
                table_sha256=tables['table_sha256'], header_sha256=hashlib.sha256(code.encode()).hexdigest(),
                retained_event_warp_ids=len(tables['warps']), native_template_refresh_maps=list(refresh_native_maps),
                v0_v1_direct_to_current_geometry=True, v2_upgrade_exactly_once=True,
                saved_position_authoritative=True, terrain_checked=True,
                native_battery_validated=False, final_release_validated=False)
