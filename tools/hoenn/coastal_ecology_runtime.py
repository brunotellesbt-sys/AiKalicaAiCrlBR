"""Enable aquatic encounter checks only on selected real aquatic travel tiles.

Encounter tables cannot supply encounters when the terrain predicate never
reaches the water branch. Keep the native behavior everywhere else, including
fast-water story barriers and ordinary floors in existing underwater maps.
"""
import hashlib

from badge_story_layer import read


DEPTH_MAPS = (
    'MAP_JOURNEYDEPTHMARES', 'MAP_JOURNEYDEPTHORIGENS',
    'MAP_JOURNEYDEPTHPROFUNDEZAS', 'MAP_JOURNEYDEPTHDIMENSOES',
    'MAP_JOURNEYDEPTHABISMO',
)

NO_SURFACING_ROUTES = (
    'MAP_UNDERWATER_ROUTE105', 'MAP_UNDERWATER_ROUTE125',
    'MAP_UNDERWATER_ROUTE127', 'MAP_UNDERWATER_ROUTE129',
)

DEPTH_PREDICATE = '''static bool8 JourneyCoastalDepthEncounterTile(u16 behavior)
{
    if (gMapHeader.mapType != MAP_TYPE_UNDERWATER)
        return FALSE;
    switch ((gSaveBlock1Ptr->location.mapGroup << 8) | gSaveBlock1Ptr->location.mapNum)
    {
''' + ''.join('    case ' + name + ':\n' for name in DEPTH_MAPS) + '''        return behavior == MB_NORMAL;
''' + ''.join('    case ' + name + ':\n' for name in NO_SURFACING_ROUTES) + '''        return behavior == MB_NO_SURFACING;
    default:
        return FALSE;
    }
}

'''


def repair(layer):
    changes = []
    path = 'src/metatile_behavior.c'
    before = read(layer, path)
    body = before.decode()
    anchor = 'bool8 MetatileBehavior_IsWaterWildEncounter(u8 metatileBehavior)\n{\n'
    addition = ('    // Open Sevii coasts reuse native fast-water artwork.\n'
                '    if (metatileBehavior == MB_FAST_WATER && JourneySeviiIsOpenCoast())\n'
                '        return TRUE;\n')
    if addition not in body:
        assert body.count(anchor) == 1
        body = body.replace(anchor, anchor + addition, 1)
        layer.stage(path, body)
    changes.append(dict(file=path, before_sha256=hashlib.sha256(before).hexdigest(),
                        after_sha256=hashlib.sha256(read(layer, path)).hexdigest()))

    path = 'src/wild_encounter.c'
    before = read(layer, path)
    body = before.decode()
    includes = ('#include "constants/maps.h"\n'
                '#include "constants/map_types.h"\n'
                '#include "constants/metatile_behaviors.h"\n')
    if DEPTH_PREDICATE not in body:
        anchor = 'bool8 StandardWildEncounter(u16 curMetatileBehavior, u16 prevMetatileBehavior)\n'
        assert body.count(anchor) == 1
        body = body.replace(anchor, DEPTH_PREDICATE + anchor, 1)
        assert body.count('#include "constants/weather.h"') == 1
        body = body.replace('#include "constants/weather.h"',
                            '#include "constants/weather.h"\n' + includes.rstrip(), 1)
        anchor = 'else if (MetatileBehavior_IsWaterWildEncounter(curMetatileBehavior) == TRUE\n'
        assert body.count(anchor) == 1
        body = body.replace(anchor, anchor +
                            '                 || JourneyCoastalDepthEncounterTile(curMetatileBehavior)\n', 1)
        anchor = 'else if (MetatileBehavior_IsWaterWildEncounter(MapGridGetMetatileBehaviorAt(x, y)) == TRUE)'
        assert body.count(anchor) == 1
        body = body.replace(anchor,
                            'else if (MetatileBehavior_IsWaterWildEncounter(MapGridGetMetatileBehaviorAt(x, y)) == TRUE\n'
                            '                 || JourneyCoastalDepthEncounterTile(MapGridGetMetatileBehaviorAt(x, y)))', 1)
        layer.stage(path, body)
    # These guards are the first exits of the original encounter entry points;
    # water coverage never changes the exploration edition's suppression.
    assert 'if (gJourneyReviewMode || sWildEncountersDisabled == TRUE)\n        return FALSE;' in body
    assert 'if (gJourneyReviewMode) return FALSE;\n    PlayerGetDestCoords(&x, &y);' in body
    assert body.count('JourneyCoastalDepthEncounterTile(') == 3
    changes.append(dict(file=path, before_sha256=hashlib.sha256(before).hexdigest(),
                        after_sha256=hashlib.sha256(read(layer, path)).hexdigest()))
    return dict(kind='coastal-ecology-encounter-runtime', files=changes,
                fast_water_only_on_connected_sevii_coasts=True,
                new_depth_water_tables_used_on_normal_underwater_floor=True,
                underwater_maps=list(DEPTH_MAPS),
                native_underwater_no_surfacing_routes=list(NO_SURFACING_ROUTES),
                native_underwater_ordinary_normal_floors_unchanged=True,
                depth_applies_to_standard_and_sweet_scent_encounters=True,
                test_edition_and_disable_encounter_guards_preserved=True,
                other_underwater_maps_and_other_fast_water_unchanged=True,
                map_layouts_attributes_and_collision_unchanged=True)
