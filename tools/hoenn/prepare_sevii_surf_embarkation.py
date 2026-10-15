"""Allow embarking again from native Sevii shores, preserving the coastal art."""
import argparse
from pathlib import Path
from candidate_layer import Layer
from prepare_sevii_coast_camera import PRIOR,LAYER as PREVIOUS

LAYER='sevii-surf-embarkation';PRIOR=PRIOR+[PREVIOUS]


def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if old:=layer.existing():return old
    s=layer.source
    p='include/journey_sevii_surf.h';layer.stage(p,(s/p).read_text().replace('#endif','bool32 JourneySeviiIsOpenCoast(void);\n#endif'))
    p='src/journey_sevii_surf.c';layer.stage(p,(s/p).read_text()+'''
bool32 JourneySeviiIsOpenCoast(void)
{
    return IsConnectedSeviiCoast(gSaveBlock1Ptr->location.mapGroup, gSaveBlock1Ptr->location.mapNum);
}
''')
    p='src/metatile_behavior.c';text=(s/p).read_text().replace('#include "global.h"','#include "global.h"\n#include "journey_sevii_surf.h"',1)
    needle='''bool8 MetatileBehavior_IsSurfableFishableWater(u8 metatileBehavior)
{
''';assert text.count(needle)==1
    text=text.replace(needle,needle+'''    if (metatileBehavior == MB_FAST_WATER && JourneySeviiIsOpenCoast())
        return TRUE;
''')
    needle='''bool8 MetatileBehavior_IsFastWater(u8 metatileBehavior)
{
''';assert text.count(needle)==1
    text=text.replace(needle,needle+'''    if (metatileBehavior == MB_FAST_WATER && JourneySeviiIsOpenCoast())
        return FALSE;
''');layer.stage(p,text)
    return layer.finish(native_coast_water_art_preserved=True,can_embark_again_after_native_island_disembark=True,
                        fast_water_rule_changed_only_in_connected_sevii_coasts=True,port_layouts_and_events_unchanged=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);print(prepare(p.parse_args().source)['layer'])
