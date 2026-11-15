"""Stage explicit, one-time atlas save relocation after historical migration 1.

This module prepares source, not a certificate of native Save/Continue behavior.
Every retired rectangle and event warp needs an authored destination; no nearest
water search or map-centre teleport is generated here. Destination tiles must be
proved safe by the source/native validators before a release is sealed.
"""
import hashlib
import json
import re

from badge_story_layer import read
from sevii_save_geometry import MIGRATION, VARIABLE, VERSION


MODES = {'preserve': 0, 'walk': 1, 'surf': 2}
MAP = re.compile(r'MAP_[A-Z0-9_]+\Z')


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name}: expected integer in [{low}, {high}]')
    return value


def normalize_relocations(relocations):
    """Validate nonoverlapping, affine half-open rectangles and explicit warps.

    Input rows contain ``old_map``, ``destination_map``, ``source_rect``
    [left, top, right, bottom], ``destination_origin`` [x, y], ``mode``
    (preserve/walk/surf) and ``elevation`` (0 preserves; otherwise 1..15).
    Optional ``warp_relocations`` maps old event warp IDs to explicit map/ID
    destinations; it never reinterprets event-warp x/y sentinels as coordinates.
    """
    if not relocations:
        raise ValueError('No explicit save relocations supplied')
    rows, warps = [], {}
    for incoming in relocations:
        row = dict(incoming)
        for key in ('old_map', 'destination_map'):
            if not isinstance(row.get(key), str) or not MAP.fullmatch(row[key]):
                raise ValueError(f'Invalid {key}')
        if row['old_map'] == row['destination_map']:
            raise ValueError('Retired-map relocation requires a different map ID')
        rect = row.get('source_rect')
        origin = row.get('destination_origin')
        if not isinstance(rect, (tuple, list)) or len(rect) != 4:
            raise ValueError('source_rect needs four coordinates')
        if not isinstance(origin, (tuple, list)) or len(origin) != 2:
            raise ValueError('destination_origin needs two coordinates')
        rect = [_integer(x, 0, 32760, 'source_rect') for x in rect]
        origin = [_integer(x, 0, 32760, 'destination_origin') for x in origin]
        if rect[0] >= rect[2] or rect[1] >= rect[3]:
            raise ValueError('Empty source_rect')
        if origin[0]+rect[2]-rect[0] > 32760 or origin[1]+rect[3]-rect[1] > 32760:
            raise ValueError('Destination rectangle exceeds object-coordinate range')
        mode = row.get('mode', 'preserve')
        if mode not in MODES:
            raise ValueError('Unknown destination movement mode')
        elevation = _integer(row.get('elevation', 0), 0, 15, 'elevation')
        if mode == 'walk' and elevation != 3 or mode == 'surf' and elevation != 1:
            raise ValueError('walk requires elevation3; surf requires elevation1')
        normalized = dict(old_map=row['old_map'], destination_map=row['destination_map'],
                          source_rect=rect, destination_origin=origin,
                          mode=mode, elevation=elevation)
        for old in rows:
            a, b = old['source_rect'], rect
            if old['old_map'] == row['old_map'] and max(a[0], b[0]) < min(a[2], b[2]) and max(a[1], b[1]) < min(a[3], b[3]):
                raise ValueError('Ambiguous overlapping save relocation rectangles')
        rows.append(normalized)
        for warp in row.get('warp_relocations', []):
            old_id = _integer(warp.get('old_warp_id'), 0, 127, 'old_warp_id')
            new_id = _integer(warp.get('destination_warp_id'), 0, 127, 'destination_warp_id')
            destination = warp.get('destination_map', row['destination_map'])
            if not isinstance(destination, str) or not MAP.fullmatch(destination):
                raise ValueError('Invalid event-warp destination map')
            key = row['old_map'], old_id
            value = dict(old_map=row['old_map'], old_warp_id=old_id,
                         destination_map=destination, destination_warp_id=new_id)
            if key in warps and warps[key] != value:
                raise ValueError('Conflicting event-warp relocation')
            warps[key] = value
    retired = {row['old_map'] for row in rows}
    if any(row['destination_map'] in retired for row in rows) or any(w['destination_map'] in retired for w in warps.values()):
        raise ValueError('Relocation destination is itself retired')
    rows.sort(key=lambda r: (r['old_map'], r['source_rect']))
    return rows, [warps[key] for key in sorted(warps)]


ATLAS_MIGRATION = r'''
// Version 2 migrates explicit retired rectangles before saved objects load.
// Tables are authored from the frozen atlas plan; no heuristic relocation.
struct JourneyAtlasSaveMove
{
    u8 oldGroup, oldNum, newGroup, newNum;
    s16 left, top, right, bottom, dx, dy;
    u8 mode, elevation;
};
struct JourneyAtlasSaveWarp
{
    u8 oldGroup, oldNum, oldId, newGroup, newNum, newId;
};
@TABLES@

static EWRAM_DATA bool8 sJourneyAtlasReloadSavedObjects = FALSE;

bool8 JourneyAtlasSavedObjectsNeedReload(void)
{
    return sJourneyAtlasReloadSavedObjects;
}

bool8 JourneyAtlasConsumeSavedObjectReload(void)
{
    bool8 result = sJourneyAtlasReloadSavedObjects;
    sJourneyAtlasReloadSavedObjects = FALSE;
    return result;
}

static const struct JourneyAtlasSaveMove *JourneyAtlasSavedMove(u8 group, u8 num, s16 x, s16 y)
{
    u32 i;
    for (i = 0; i < ARRAY_COUNT(sJourneyAtlasSaveMoves); i++)
    {
        const struct JourneyAtlasSaveMove *move = &sJourneyAtlasSaveMoves[i];
        if (move->oldGroup == group && move->oldNum == num
         && x >= move->left && x < move->right && y >= move->top && y < move->bottom)
            return move;
    }
    return NULL;
}

static void JourneyAtlasMigrateSavedWarp(struct WarpData *warp)
{
    const struct JourneyAtlasSaveMove *move;
    u32 i;
    // Warp-ID references have a distinct authored table; x/y may be unset.
    if (warp->warpId >= 0)
    {
        for (i = 0; i < @WARP_COUNT@; i++)
        {
            const struct JourneyAtlasSaveWarp *entry = &sJourneyAtlasSaveWarps[i];
            if (warp->mapGroup == entry->oldGroup && warp->mapNum == entry->oldNum && warp->warpId == entry->oldId)
            {
                warp->mapGroup = entry->newGroup;
                warp->mapNum = entry->newNum;
                warp->warpId = entry->newId;
                return;
            }
        }
        return;
    }
    move = JourneyAtlasSavedMove(warp->mapGroup, warp->mapNum, warp->x, warp->y);
    if (move == NULL)
        return;
    warp->mapGroup = move->newGroup;
    warp->mapNum = move->newNum;
    warp->x += move->dx;
    warp->y += move->dy;
}

static void JourneyAtlasMigrateCurrentSave(void)
{
    const struct JourneyAtlasSaveMove *move = JourneyAtlasSavedMove(
        gSaveBlock1Ptr->location.mapGroup, gSaveBlock1Ptr->location.mapNum,
        gSaveBlock1Ptr->pos.x, gSaveBlock1Ptr->pos.y);
    u32 i;
    if (move == NULL)
        return;
    gSaveBlock1Ptr->pos.x += move->dx;
    gSaveBlock1Ptr->pos.y += move->dy;
    gSaveBlock1Ptr->location.mapGroup = move->newGroup;
    gSaveBlock1Ptr->location.mapNum = move->newNum;
    gSaveBlock1Ptr->location.warpId = -1;
    gSaveBlock1Ptr->location.x = gSaveBlock1Ptr->pos.x;
    gSaveBlock1Ptr->location.y = gSaveBlock1Ptr->pos.y;

    for (i = 0; i < OBJECT_EVENTS_COUNT; i++)
    {
        struct ObjectEvent *object = &gSaveBlock1Ptr->objectEvents[i];
        if (object->isPlayer || object->localId == OBJ_EVENT_ID_FOLLOWER || object->localId == OBJ_EVENT_ID_NPC_FOLLOWER)
        {
            object->mapGroup = move->newGroup;
            object->mapNum = move->newNum;
            object->initialCoords.x += move->dx;
            object->initialCoords.y += move->dy;
            object->currentCoords.x += move->dx;
            object->currentCoords.y += move->dy;
            object->previousCoords.x += move->dx;
            object->previousCoords.y += move->dy;
            if (move->elevation != 0)
                object->currentElevation = object->previousElevation = move->elevation;
            if (object->isPlayer && move->mode != 0)
            {
                u16 graphics = GetPlayerAvatarGraphicsIdByStateIdAndGender(
                    move->mode == 2 ? PLAYER_AVATAR_STATE_SURFING : PLAYER_AVATAR_STATE_NORMAL,
                    gSaveBlock2Ptr->playerGender);
                // SaveObjectEvents uses a byte-swapped ID; LoadObjectEvents
                // reverses it. The spriteId marker preserves extended IDs.
                object->graphicsId = (graphics >> 8) | (graphics << 8);
                object->spriteId = 127;
            }
        }
        else
            object->active = FALSE;
    }
#if FNPC_ENABLE_NPC_FOLLOWERS
    if (gSaveBlock3Ptr->NPCfollower.inProgress)
    {
        gSaveBlock3Ptr->NPCfollower.log.x += move->dx;
        gSaveBlock3Ptr->NPCfollower.log.y += move->dy;
    }
#endif
    // The normal Continue path will load the new header first, then rebuild
    // its native templates (including clones) before restoring scripts.
    gSaveBlock1Ptr->mapLayoutId = Overworld_GetMapHeaderByGroupAndId(move->newGroup, move->newNum)->mapLayoutId;
    CpuFill16(0, gSaveBlock1Ptr->mapView, sizeof(gSaveBlock1Ptr->mapView));
    sJourneyAtlasReloadSavedObjects = TRUE;
}

static void JourneyMigrateSeviiSaveGeometry(void)
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
}
'''


def migration_source(relocations, *, fallback_header=None):
    """Return C source retaining the byte-for-byte historical migration body.

    Only its function name, fixed guard and fixed final version are changed.
    This prevents raising CURRENT to 2 from reapplying Treasure's translation.
    """
    if fallback_header is not None and fallback_header != 'data/journey_atlas_migration.h':
        raise ValueError('Unreviewed migration fallback header')
    if relocations or fallback_header is None:
        rows, warps = normalize_relocations(relocations)
    else:
        rows, warps = [], []
    legacy = MIGRATION.replace('JourneyMigrateSeviiSaveGeometry(void)',
                               'JourneyMigrateSeviiSaveGeometryVersion1(void)')
    legacy = legacy.replace(VERSION, '1')
    entries = []
    for row in rows:
        old, new = row['old_map'], row['destination_map']
        left, top, right, bottom = row['source_rect']
        x, y = row['destination_origin']
        fields = [f'MAP_GROUP({old})', f'MAP_NUM({old})',
                  f'MAP_GROUP({new})', f'MAP_NUM({new})',
                  left, top, right, bottom, x-left, y-top,
                  MODES[row['mode']], row['elevation']]
        entries.append('    {'+', '.join(map(str, fields))+'},')
    tables = 'static const struct JourneyAtlasSaveMove sJourneyAtlasSaveMoves[] = {\n'+('\n'.join(entries) if entries else '    {0,0,0,0,0,0,0,0,0,0,0,0},')+'\n};\n'
    entries = []
    for row in warps:
        old, new = row['old_map'], row['destination_map']
        fields = [f'MAP_GROUP({old})', f'MAP_NUM({old})', row['old_warp_id'],
                  f'MAP_GROUP({new})', f'MAP_NUM({new})', row['destination_warp_id']]
        entries.append('    {'+', '.join(map(str, fields))+'},')
    # A one-element inaccessible sentinel remains valid in strict C90 too.
    tables += 'static const struct JourneyAtlasSaveWarp sJourneyAtlasSaveWarps[] = {\n'
    tables += '\n'.join(entries) if entries else '    {0, 0, 0, 0, 0, 0},'
    tables += '\n};\n'
    tables += 'static const u32 sJourneyAtlasSaveWarpCount = '+str(len(warps))+';\n'
    body=ATLAS_MIGRATION.replace('@TABLES@', tables).replace('@WARP_COUNT@', 'sJourneyAtlasSaveWarpCount')
    if fallback_header:
        anchor='\nstatic EWRAM_DATA bool8 sJourneyAtlasReloadSavedObjects = FALSE;'
        if body.count(anchor)!=1:
            raise ValueError('Migration fallback include anchor changed')
        body=body.replace(anchor,'\n#include "'+fallback_header+'"\n'+anchor,1)
        anchor='    return NULL;\n}\n\nstatic void JourneyAtlasMigrateSavedWarp'
        if body.count(anchor)!=1:
            raise ValueError('Migration fallback resolver anchor changed')
        body=body.replace(anchor,'    return JourneyAtlasMigrationFallback(group, num, x, y);\n}\n\nstatic void JourneyAtlasMigrateSavedWarp',1)
        begin=body.index('static void JourneyAtlasMigrateSavedWarp(')
        end=body.index('\nstatic void JourneyAtlasMigrateCurrentSave',begin)
        body=body[:begin]+FALLBACK_SAVED_WARP.replace('@WARP_COUNT@','sJourneyAtlasSaveWarpCount')+body[end:]
        anchor='    // The normal Continue path will load the new header first, then rebuild'
        body=body.replace(anchor,'    CpuFill16(0, gSaveBlock1Ptr->objectEventTemplates, sizeof(gSaveBlock1Ptr->objectEventTemplates));\n'+anchor,1)
        anchor='            object->previousCoords.y += move->dy;'
        body=body.replace(anchor,anchor+'''\n            if (object->isPlayer)
            {
                // Saved position is authoritative across unfinished map seams.
                object->initialCoords.x = object->currentCoords.x = object->previousCoords.x = gSaveBlock1Ptr->pos.x + MAP_OFFSET;
                object->initialCoords.y = object->currentCoords.y = object->previousCoords.y = gSaveBlock1Ptr->pos.y + MAP_OFFSET;
            }''',1)
    return legacy+body


FALLBACK_SAVED_WARP = r'''static void JourneyAtlasMigrateSavedWarp(struct WarpData *warp)
{
    const struct JourneyAtlasSaveMove *move;
    const struct JourneyAtlasLegacyMap *old;
    u32 i;
    s16 x = warp->x, y = warp->y;
    if (warp->warpId >= 0)
    {
        for (i = 0; i < @WARP_COUNT@; i++)
        {
            const struct JourneyAtlasSaveWarp *entry = &sJourneyAtlasSaveWarps[i];
            if (warp->mapGroup == entry->oldGroup && warp->mapNum == entry->oldNum && warp->warpId == entry->oldId)
            {
                warp->mapGroup = entry->newGroup;
                warp->mapNum = entry->newNum;
                warp->warpId = entry->newId;
                return;
            }
        }
        old = JourneyAtlasLegacyFind(((u16)(u8)warp->mapGroup << 8) | (u8)warp->mapNum);
        if (old == NULL)
            return;
        // An unmatched event ID has no meaningful x/y. Resolve a separately
        // declared map-centre rescue; never reinterpret its unset sentinels.
        x = old->width / 2;
        y = old->height / 2;
        move = JourneyAtlasMigrationFallback(warp->mapGroup, warp->mapNum, x, y);
    }
    else
        move = JourneyAtlasSavedMove(warp->mapGroup, warp->mapNum, x, y);
    if (move == NULL)
        return;
    warp->mapGroup = move->newGroup;
    warp->mapNum = move->newNum;
    warp->warpId = -1;
    warp->x = x + move->dx;
    warp->y = y + move->dy;
}
'''


def _map_inputs(layer):
    groups = json.loads(read(layer, 'data/maps/map_groups.json'))
    names = {name for key in groups['group_order'] for name in groups[key]}
    ids = {name: (group, number) for group, key in enumerate(groups['group_order'])
           for number, name in enumerate(groups[key])}
    layouts = {row['id']: row for row in json.loads(read(layer, 'data/layouts/layouts.json'))['layouts']}
    maps = {name: json.loads(read(layer, f'data/maps/{name}/map.json')) for name in names}
    by_constant = {row['id']: name for name, row in maps.items()}
    return ids, layouts, maps, by_constant


def validate_source_destinations(layer, relocations):
    """Check map IDs, rectangle bounds and total event-warp reference coverage.

    Collision/behavior suitability deliberately remains an independent source
    and native-proof requirement rather than trusting a label in this table.
    """
    rows, warps = normalize_relocations(relocations)
    ids, layouts, maps, by_constant = _map_inputs(layer)
    warp_keys = {(r['old_map'], r['old_warp_id']) for r in warps}
    old_maps = set()
    for row in rows:
        for key in ('old_map', 'destination_map'):
            name = by_constant.get(row[key])
            if name is None:
                raise ValueError(f'Unknown map ID {row[key]}')
            group, number = ids[name]
            if group >= 128 or number >= 128:
                raise ValueError('WarpData signed mapGroup/mapNum would overflow')
            mapping = maps[name]
            layout = layouts[mapping['layout']]
            if key == 'old_map':
                left, top, right, bottom = row['source_rect']
                if right > layout['width'] or bottom > layout['height']:
                    raise ValueError('Source relocation rectangle outside old layout')
                old_maps.add((name, row[key]))
            else:
                x, y = row['destination_origin']
                rect = row['source_rect']
                if x+rect[2]-rect[0] > layout['width'] or y+rect[3]-rect[1] > layout['height']:
                    raise ValueError('Destination relocation rectangle outside target layout')
    for name, constant in old_maps:
        events = maps[name].get('warp_events') or []
        for number in range(len(events)):
            if (constant, number) not in warp_keys:
                raise ValueError(f'Missing event-warp relocation: {constant}:{number}')
    # Each event destination must resolve to an existing native event index.
    for row in warps:
        target = by_constant.get(row['destination_map'])
        if target is None:
            raise ValueError('Unknown event-warp destination map')
        events = maps[target].get('warp_events') or []
        if row['destination_warp_id'] >= len(events):
            raise ValueError('Event-warp destination index does not exist')
    return rows, warps


def stage(layer, relocations, *, fallback_header=None):
    """Install migration 2 on a verified revision171-style parent layer."""
    if fallback_header is not None and fallback_header != 'data/journey_atlas_migration.h':
        raise ValueError('Unreviewed migration fallback header')
    if relocations or fallback_header is None:
        rows, warps = validate_source_destinations(layer, relocations)
    else:
        rows, warps = [], []
    if fallback_header:
        header=read(layer,'src/'+fallback_header).decode()
        if 'JourneyAtlasMigrationFallback' not in header or 'journey_atlas_legacy.h' not in header:
            raise ValueError('Migration fallback header is missing its resolver/legacy contract')
    source = migration_source(relocations,fallback_header=fallback_header)
    path = 'src/load_save.c'
    text = read(layer, path).decode()
    if text.count(MIGRATION) != 1:
        raise ValueError('Expected exact preserved historical migration1 source')
    anchor = '    JourneyMigrateSeviiSaveGeometry();\n    LoadObjectEvents();'
    if text.count(anchor) != 1:
        raise ValueError('Migration hook must precede LoadObjectEvents exactly once')
    text = text.replace(MIGRATION, source+'\n')
    if '#include "field_player_avatar.h"' not in text:
        text = text.replace('#include "load_save.h"', '#include "load_save.h"\n#include "field_player_avatar.h"')
    if fallback_header and '#include "fieldmap.h"' not in text:
        text=text.replace('#include "load_save.h"','#include "load_save.h"\n#include "fieldmap.h"')
    layer.stage(path, text)
    path = 'include/constants/vars.h'
    text = read(layer, path).decode()
    text, count = re.subn(r'(#define\s+'+VERSION+r'\s+)1\b', r'\g<1>2', text)
    if count != 1:
        raise ValueError('Expected geometry version1 constant')
    layer.stage(path, text)
    path = 'include/load_save.h'
    text = read(layer, path).decode()
    anchor = 'void CopyPartyAndObjectsFromSave(void);'
    if text.count(anchor) != 1:
        raise ValueError('Missing save restore prototype')
    layer.stage(path, text.replace(anchor, anchor+'\nbool8 JourneyAtlasSavedObjectsNeedReload(void);\nbool8 JourneyAtlasConsumeSavedObjectReload(void);'))
    path = 'src/overworld.c'
    text = read(layer, path).decode()
    anchor = 'static void InitObjectEventsReturnToField(void)\n{\n    SpawnObjectEventsOnReturnToField(0, 0);'
    if text.count(anchor) != 1:
        raise ValueError('Expected native saved-object restore hook')
    text = text.replace(anchor, anchor+'\n    if (JourneyAtlasConsumeSavedObjectReload())\n        TrySpawnObjectEvents(0, 0);')
    anchor = '    LoadSaveblockMapHeader();\n    ClearDiveAndHoleWarps();'
    if text.count(anchor) != 1:
        raise ValueError('Expected Continue map-header hook before object scripts')
    layer.stage(path, text.replace(anchor, '    LoadSaveblockMapHeader();\n    if (JourneyAtlasSavedObjectsNeedReload())\n        LoadObjEventTemplatesFromHeader();\n    ClearDiveAndHoleWarps();'))
    return dict(kind='atlas-save-geometry-migration', version=2,
                variable=VARIABLE, historical_migration1_preserved=True,
                relocation_rectangles=rows, event_warp_relocations=warps,
                source_sha256=hashlib.sha256(source.encode()).hexdigest(),
                restore_hook='CopyPartyAndObjectsFromSave before LoadObjectEvents',
                destination_templates='Native LoadObjEventTemplatesFromHeader with clone resolution',
                fallback_header=fallback_header,
                native_save_continue_validated=False)
