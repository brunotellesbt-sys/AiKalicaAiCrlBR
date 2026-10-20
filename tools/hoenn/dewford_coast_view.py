"""Complete the missing diagonal view of the four-map Dewford terminal."""
import json

MAPS = {
    'DewfordTown': (-20, 0),
    'Route106': (-80, -20),
    'Route107': (0, 0),
    'JourneyDewfordPortIsland': (0, -12),
}


def repair(layer):
    def read(name):
        return layer.outputs.get(name, (layer.source/name).read_bytes() if (layer.source/name).exists() else b'')
    entries = []
    for name, (x, y) in MAPS.items():
        mid = json.loads(read('data/maps/'+name+'/map.json'))['id']
        entries.append('    {MAP_GROUP('+mid+'), MAP_NUM('+mid+'), '+str(x)+', '+str(y)+'},')
    header = '''#ifndef GUARD_JOURNEY_DEWFORD_COAST_VIEW_H
#define GUARD_JOURNEY_DEWFORD_COAST_VIEW_H
// Native connection strips do not include a diagonally adjacent map. The
// terminal crosses four maps, so its corners need their actual map blocks.
// All coordinates use Route 107's origin; no new travel connections are added.
static const struct {
    u8 group;
    u8 number;
    s16 x;
    s16 y;
} sJourneyDewfordCoastOrigins[] = {
ENTRIES
};

static s32 JourneyDewfordCoastIndex(u16 group, u16 number)
{
    u32 i;
    for (i = 0; i < ARRAY_COUNT(sJourneyDewfordCoastOrigins); i++)
        if (sJourneyDewfordCoastOrigins[i].group == group
            && sJourneyDewfordCoastOrigins[i].number == number)
            return i;
    return -1;
}

static bool8 JourneyDewfordIsCoastMap(u16 group, u16 number)
{
    return JourneyDewfordCoastIndex(group, number) >= 0;
}

static void JourneyDewfordFillCornerViews(struct MapHeader *mapHeader)
{
    const struct MapLayout *layouts[ARRAY_COUNT(sJourneyDewfordCoastOrigins)];
    s32 current = JourneyDewfordCoastIndex(gSaveBlock1Ptr->location.mapGroup,
                                         gSaveBlock1Ptr->location.mapNum);
    s32 x, y, i;
    if (current < 0)
        return;
    for (i = 0; i < ARRAY_COUNT(sJourneyDewfordCoastOrigins); i++)
        layouts[i] = Overworld_GetMapHeaderByGroupAndId(
            sJourneyDewfordCoastOrigins[i].group,
            sJourneyDewfordCoastOrigins[i].number)->mapLayout;
    for (y = 0; y < gBackupMapLayout.height; y++)
    {
        for (x = 0; x < gBackupMapLayout.width; x++)
        {
            u16 *block = &gBackupMapLayout.map[y * gBackupMapLayout.width + x];
            s32 worldX, worldY;
            if (*block != MAPGRID_UNDEFINED)
                continue;
            worldX = x - MAP_OFFSET + sJourneyDewfordCoastOrigins[current].x;
            worldY = y - MAP_OFFSET + sJourneyDewfordCoastOrigins[current].y;
            for (i = 0; i < ARRAY_COUNT(layouts); i++)
            {
                s32 localX = worldX - sJourneyDewfordCoastOrigins[i].x;
                s32 localY = worldY - sJourneyDewfordCoastOrigins[i].y;
                if (localX >= 0 && localY >= 0
                    && localX < layouts[i]->width && localY < layouts[i]->height
                    && layouts[i]->primaryTileset == mapHeader->mapLayout->primaryTileset
                    && layouts[i]->secondaryTileset == mapHeader->mapLayout->secondaryTileset)
                {
                    *block = layouts[i]->map[localY * layouts[i]->width + localX];
                    break;
                }
            }
        }
    }
}
#endif
'''.replace('ENTRIES', '\n'.join(entries))
    layer.stage('include/journey_dewford_coast_view.h', header)
    name = 'src/fieldmap.c'
    text = read(name).decode()
    anchor = 'static void LoadSavedMapView(void);'
    assert text.count(anchor) == 1
    text = text.replace(anchor, anchor+'\nstatic void ClearSavedMapView(void);')
    anchor = 'void InitMap(void)\n{'
    assert text.count(anchor) == 1
    text = text.replace(anchor, '#include "journey_dewford_coast_view.h"\n\n'+anchor)
    anchor = 'void InitMapFromSavedGame(void)\n{\n    InitMapLayoutData(&gMapHeader);'
    assert text.count(anchor) == 1
    text = text.replace(anchor, anchor+'''
    if (JourneyDewfordIsCoastMap(gSaveBlock1Ptr->location.mapGroup,
                                gSaveBlock1Ptr->location.mapNum))
        ClearSavedMapView();''')
    anchor = '        InitBackupMapLayoutConnections(mapHeader);'
    assert text.count(anchor) == 1
    text = text.replace(anchor, anchor+'\n        JourneyDewfordFillCornerViews(mapHeader);')
    anchor = '        // Clear BEFORE InitMap/LoadSavedMapView can replay foreign bank IDs.'
    assert text.count(anchor) == 1
    text = text.replace(anchor, '''        freshCoastView |= JourneyDewfordIsCoastMap(
            gSaveBlock1Ptr->location.mapGroup, gSaveBlock1Ptr->location.mapNum)
            || JourneyDewfordIsCoastMap(connection->mapGroup, connection->mapNum);
'''+anchor)
    layer.stage(name, text)
    return dict(world_origins={n:list(xy) for n,xy in MAPS.items()},
                only_undefined_view_cells_filled=True,
                actual_neighbor_blocks_preserve_art_elevation_and_collision=True,
                same_tileset_required=True, connections_unchanged=True,
                old_saved_coast_view_discarded_on_continue=True,
                fresh_view_on_every_local_transition=True)
