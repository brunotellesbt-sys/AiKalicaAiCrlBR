"""Stage a one-time, ABI-preserving migration of Treasure Beach save geometry.

The map's original terrain moved eight columns east. Apply the same exact
translation to legacy persisted coordinates before restoring object events;
the migration marker occupies an existing, verified unused script variable.
"""
import hashlib
import re

from badge_story_layer import read


VARIABLE = 'VAR_JOURNEY_SEVII_GEOMETRY_VERSION'
VERSION = 'JOURNEY_SEVII_GEOMETRY_VERSION_CURRENT'

MIGRATION = r'''// Geometry version 1 translates the preserved Treasure Beach terrain by +8x.
// Migrate persisted data before LoadObjectEvents or any map-view restoration.
// No save structure, event ID, player elevation or movement mode is changed.
static bool32 JourneySavedMapIsTreasureBeach(u8 mapGroup, u8 mapNum)
{
    return mapGroup == MAP_GROUP(MAP_ONE_ISLAND_TREASURE_BEACH)
        && mapNum == MAP_NUM(MAP_ONE_ISLAND_TREASURE_BEACH);
}

static void JourneyMigrateTreasureDirectWarp(struct WarpData *warp)
{
    // Warp IDs resolve through the new event table and keep their ABI.
    // Negative coordinates are native unset-position sentinels.
    if (JourneySavedMapIsTreasureBeach(warp->mapGroup, warp->mapNum)
     && warp->warpId < 0 && warp->x >= 0 && warp->x < 24
     && warp->y >= 0 && warp->y < 40)
        warp->x += 8;
}

static void JourneyMigrateSeviiSaveGeometry(void)
{
    u32 i;

    if (VarGet(VAR_JOURNEY_SEVII_GEOMETRY_VERSION) >= JOURNEY_SEVII_GEOMETRY_VERSION_CURRENT)
        return;

    if (JourneySavedMapIsTreasureBeach(gSaveBlock1Ptr->location.mapGroup,
                                     gSaveBlock1Ptr->location.mapNum))
    {
        gSaveBlock1Ptr->pos.x += 8;
        for (i = 0; i < OBJECT_EVENTS_COUNT; i++)
        {
            struct ObjectEvent *object = &gSaveBlock1Ptr->objectEvents[i];
            // The player can retain its previous map ID after a connection.
            // Other actors are translated only when owned by Treasure Beach.
            if (object->isPlayer || JourneySavedMapIsTreasureBeach(object->mapGroup, object->mapNum))
            {
                object->initialCoords.x += 8;
                object->currentCoords.x += 8;
                object->previousCoords.x += 8;
            }
        }
        for (i = 0; i < OBJECT_EVENT_TEMPLATES_COUNT; i++)
            if (gSaveBlock1Ptr->objectEventTemplates[i].localId != 0)
                gSaveBlock1Ptr->objectEventTemplates[i].x += 8;
#if FNPC_ENABLE_NPC_FOLLOWERS
        if (gSaveBlock3Ptr->NPCfollower.inProgress)
            gSaveBlock3Ptr->NPCfollower.log.x += 8;
#endif
        // Let InitMapFromSavedGame rebuild the view at the translated origin.
        CpuFill16(0, gSaveBlock1Ptr->mapView, sizeof(gSaveBlock1Ptr->mapView));
    }

    // Direct return coordinates can point here while the player is indoors
    // or elsewhere. All five persisted WarpData records use the same rule.
    JourneyMigrateTreasureDirectWarp(&gSaveBlock1Ptr->location);
    JourneyMigrateTreasureDirectWarp(&gSaveBlock1Ptr->continueGameWarp);
    JourneyMigrateTreasureDirectWarp(&gSaveBlock1Ptr->dynamicWarp);
    JourneyMigrateTreasureDirectWarp(&gSaveBlock1Ptr->lastHealLocation);
    JourneyMigrateTreasureDirectWarp(&gSaveBlock1Ptr->escapeWarp);
    VarSet(VAR_JOURNEY_SEVII_GEOMETRY_VERSION, JOURNEY_SEVII_GEOMETRY_VERSION_CURRENT);
}

'''


def _unused_variable_references(layer):
    """Fail closed if the reserved address has any executable-source consumer."""
    pattern = re.compile(r'\b(?:VAR_UNUSED_0x40DC|VAR_0x40DC|0x0*40DC|16604)\b',re.I)
    references=[]
    scanned=hashlib.sha256()
    count=0
    for directory in ('src','include','data','test','asm'):
        root=layer.source/directory
        if not root.exists():
            continue
        for path in sorted(root.rglob('*')):
            if not path.is_file() or path.suffix.lower() not in ('.c','.h','.inc','.s','.json'):
                continue
            relative=path.relative_to(layer.source).as_posix()
            # Generated build caches derive from these canonical inputs and
            # differ between a fresh checkout and an already-built snapshot.
            if relative not in layer.outputs and relative not in layer.expected:
                continue
            raw=read(layer,relative)
            scanned.update(relative.encode()+b'\0'+hashlib.sha256(raw).digest())
            count+=1
            text=raw.decode()
            for number,line in enumerate(text.splitlines(),1):
                if re.match(r'\s*#\s*line\s+\d+\b',line):
                    continue  # Generated debug line numbers are not var IDs.
                if pattern.search(line):
                    references.append(dict(path=relative,line=number,text=line))
    assert {r['path'] for r in references} == {
        'include/constants/vars.h','include/constants/vars_frlg.h'}, references
    assert len(references)==2 and all(re.match(r'\s*#define\s+VAR_(?:UNUSED_)?0x40DC\s+0x40DC\b',r['text'])
                                     for r in references), references
    return dict(references=references,files_scanned=count,
                scan_sha256=scanned.hexdigest(),scope='Canonical verified layer inputs; generated build caches excluded')


def repair(layer):
    reference_audit=_unused_variable_references(layer)
    path='include/constants/vars.h'
    text=read(layer,path).decode()
    old='#define VAR_UNUSED_0x40DC                                0x40DC // Unused Var'
    assert text.count(old)==1
    text=text.replace(old,'#define VAR_JOURNEY_SEVII_GEOMETRY_VERSION               0x40DC // Save-coordinate migration, existing unused slot\n'
                          '#define JOURNEY_SEVII_GEOMETRY_VERSION_CURRENT           1')
    layer.stage(path,text)
    path='src/new_game.c'
    text=read(layer,path).decode()
    anchor='    InitEventData();\n'
    assert text.count(anchor)==1
    layer.stage(path,text.replace(anchor,anchor+
        '    VarSet(VAR_JOURNEY_SEVII_GEOMETRY_VERSION, JOURNEY_SEVII_GEOMETRY_VERSION_CURRENT);\n'))
    path='src/load_save.c'
    text=read(layer,path).decode()
    include='#include "constants/event_objects.h"\n'
    assert text.count(include)==1
    text=text.replace(include,include+'#include "constants/map_groups.h"\n')
    anchor='void CopyPartyAndObjectsFromSave(void)\n{\n    LoadPlayerParty();\n    LoadObjectEvents();\n}'
    assert text.count(anchor)==1
    replacement=MIGRATION+anchor.replace('    LoadObjectEvents();',
        '    JourneyMigrateSeviiSaveGeometry();\n    LoadObjectEvents();')
    layer.stage(path,text.replace(anchor,replacement))
    return dict(kind='sevii-legacy-save-geometry-migration',
        variable=dict(name=VARIABLE,address=0x40DC,current_version=1,
                      original_unused_references=reference_audit['references']),
        free_variable_source_audit=reference_audit,
        new_game_hook='NewGameInitData after InitEventData',
        restore_hook='CopyPartyAndObjectsFromSave before LoadObjectEvents',
        legacy_current_map='MAP_ONE_ISLAND_TREASURE_BEACH',translation=[8,0],
        cached_map_view='Cleared with native CpuFill16 before InitMapFromSavedGame',
        object_records='Player and Treasure-owned object events; current-map templates',
        direct_warps=['location','continueGameWarp','dynamicWarp','lastHealLocation','escapeWarp'],
        direct_warp_condition='Treasure map, warpId<0, 0<=x<24 and 0<=y<40',
        warp_ids_unchanged=True,save_structures_unchanged=True,trainer_flags_used=False,
        idempotent_after_marking_and_saving=True,
        migration_source_sha256=hashlib.sha256(MIGRATION.encode()).hexdigest())
