"""Restore declared island land encounters without changing terrain or pools."""
from badge_story_layer import read

SCENES = (12, 8, 10, 14, 39, 72, 71)
OWNERS = tuple('JourneyWorldSea%02d' % i for i in (0, 1, 2, 3, 4, 6, 7))
CALL = ('JourneyAtlasLandEncounter((gSaveBlock1Ptr->location.mapGroup << 8)'
        ' | gSaveBlock1Ptr->location.mapNum, %s, PlayerGetElevation())')


def function():
    cases = ''.join('    case MAP_JOURNEYATLASSCENE%03d:\n' % i for i in SCENES)
    return '''
// These existing sand islands own terrestrial habitat pools. All other
// sand, water, heights and maps retain their original encounter behavior.
bool32 JourneyAtlasLandEncounter(u16 map, u16 behavior, u8 elevation)
{
    if (behavior != MB_SAND || elevation != 3)
        return FALSE;
    switch (map)
    {
'''+cases+'''        return TRUE;
    default:
        return FALSE;
    }
}
'''


def verify_hooks(encounters):
    for behavior in ('curMetatileBehavior', 'MapGridGetMetatileBehaviorAt(x, y)'):
        hook = ('if (MetatileBehavior_IsLandWildEncounter('+behavior+') == TRUE\n'
                '            || '+CALL % behavior+')')
        if encounters.count(hook) != 1:
            raise ValueError('Missing native sand encounter hook: '+behavior)
    if encounters.count('JourneyAtlasLandEncounter(') != 2:
        raise ValueError('Unexpected sand encounter call')


def stage(layer):
    path = 'src/journey_atlas_ecology.c'
    text = read(layer, path).decode()
    if 'JourneyAtlasLandEncounter' in text:
        raise ValueError('Sand habitat repair already staged')
    text = text.replace('#include "journey_atlas_ecology.h"',
                        '#include "journey_atlas_ecology.h"\n#include "constants/metatile_behaviors.h"')
    layer.stage(path, text+function())
    path = 'include/journey_atlas_ecology.h'
    text = read(layer, path).decode()
    if text.count('#endif') != 1:
        raise ValueError('Ambiguous ecology header')
    layer.stage(path, text.replace('#endif',
        'bool32 JourneyAtlasLandEncounter(u16 map, u16 behavior, u8 elevation);\n#endif'))
    path = 'src/wild_encounter.c'
    text = read(layer, path).decode()
    for behavior in ('curMetatileBehavior', 'MapGridGetMetatileBehaviorAt(x, y)'):
        old = 'if (MetatileBehavior_IsLandWildEncounter('+behavior+') == TRUE)'
        if text.count(old) != 1:
            raise ValueError('Ambiguous ordinary land encounter branch')
        text = text.replace(old, old[:-1]+'\n            || '+CALL % behavior+')')
    verify_hooks(text)
    layer.stage(path, text)
    return dict(maps=['JourneyAtlasScene%03d' % i for i in SCENES],
                owners=list(OWNERS), behavior='MB_SAND', elevation=3,
                terrain_changed=False, pools_changed=False,
                standard_encounter_and_sweet_scent=True)
