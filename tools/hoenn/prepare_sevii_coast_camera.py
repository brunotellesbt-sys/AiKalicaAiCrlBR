"""Do not carry stale ocean-corner collision tiles across short Sevii coasts."""
import argparse
from pathlib import Path
from candidate_layer import Layer
from prepare_sevii_surf_connections import PRIOR,LAYER as PREVIOUS,ISLANDS

LAYER='sevii-coast-camera';PRIOR=PRIOR+[PREVIOUS]


def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if old:=layer.existing():return old
    s=layer.source
    p='include/journey_sevii_surf.h';text=(s/p).read_text().replace('#endif','bool32 JourneySeviiNeedsFreshCoastView(u8 fromGroup, u8 fromNum, u8 toGroup, u8 toNum);\n#endif');layer.stage(p,text)
    p='src/journey_sevii_surf.c';text=(s/p).read_text().replace('#include "constants/vars.h"','#include "constants/vars.h"\n#include "constants/maps.h"')
    names=[i+'Island_Harbor_Frlg' for i in ISLANDS]+['ThreeIsland_Port_Frlg' if i=='Three' else i+'Island_Frlg' for i in ISLANDS]
    # Use the real generated map IDs rather than deriving them from spelling.
    import json
    ids=[json.loads((s/f'data/maps/{n}/map.json').read_text())['id'] for n in names]
    cases=''.join('    case (MAP_GROUP('+ident+') << 8) | MAP_NUM('+ident+'):\n' for ident in ids)
    text+='''
static bool32 IsConnectedSeviiCoast(u8 group, u8 num)
{
    switch ((group << 8) | num)
    {
'''+cases+'''        return TRUE;
    default:
        return FALSE;
    }
}

bool32 JourneySeviiNeedsFreshCoastView(u8 fromGroup, u8 fromNum, u8 toGroup, u8 toNum)
{
    return (gPlayerAvatar.flags & PLAYER_AVATAR_FLAG_SURFING)
        && (IsConnectedSeviiCoast(fromGroup, fromNum) || IsConnectedSeviiCoast(toGroup, toNum));
}
''';layer.stage(p,text)
    p='src/fieldmap.c';text=(s/p).read_text().replace('#include "global.h"','#include "global.h"\n#include "journey_sevii_surf.h"',1)
    needle='''    int old_x, old_y;
    gCamera.active = FALSE;''';assert text.count(needle)==1
    text=text.replace(needle,'''    int old_x, old_y;
    bool32 freshCoastView;
    gCamera.active = FALSE;''')
    needle='''        SetPositionFromConnection(connection, direction, x, y);
        LoadMapFromCameraTransition(connection->mapGroup, connection->mapNum);''';assert text.count(needle)==1
    text=text.replace(needle,'''        freshCoastView = JourneySeviiNeedsFreshCoastView(
            gSaveBlock1Ptr->location.mapGroup, gSaveBlock1Ptr->location.mapNum,
            connection->mapGroup, connection->mapNum);
        SetPositionFromConnection(connection, direction, x, y);
        LoadMapFromCameraTransition(connection->mapGroup, connection->mapNum);''')
    needle='''        MoveMapViewToBackup(direction);''';assert text.count(needle)==1
    text=text.replace(needle,'''        // A short island map can still contain a third map's blocked corner
        // in its saved apron. Keep the newly loaded coast/collision grid.
        if (freshCoastView)
            ClearSavedMapView();
        else
            MoveMapViewToBackup(direction);''');layer.stage(p,text)
    return layer.finish(affected_coast_maps=names,refresh_only_when_surfing_between_sevii_coasts=True,
                        no_new_fades_or_warps=True,stale_blocked_border_tiles_not_copied_into_native_island=True,
                        port_layouts_and_events_unchanged=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);print(prepare(p.parse_args().source)['layer'])
