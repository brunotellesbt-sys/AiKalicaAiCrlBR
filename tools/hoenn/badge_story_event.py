"""Meet the six qualifiers outside, share the stadium, celebrate outside again.

The scene adds actors and scripts only. Every original terrain, structure,
warp, ordinary NPC and PWT battle script remains untouched.
"""
import hashlib
import json
from pathlib import Path
import struct


HERE = Path(__file__).resolve().parent
OUTSIDE = 'data/maps/BattleFrontier_OutsideWest/map.json'
WEST_SCRIPT = 'data/maps/BattleFrontier_OutsideWest/scripts.inc'
ARENA_SCRIPT = 'data/maps/JourneyPWTArena/scripts.inc'
GALACTIC = 'src/journey_galactic.c'
CAMPAIGN = 'data/scripts/journey_campaign_gates.inc'
EVENTS = 'data/event_scripts.s'
GROUND = 'data/layouts/BattleFrontier_OutsideWest/map.bin'
PARTY = (
    ('home_opposite', 'OBJ_EVENT_GFX_VAR_0', 22, 66, 'MOVEMENT_TYPE_FACE_DOWN'),
    ('away_opposite', 'OBJ_EVENT_GFX_VAR_1', 24, 66, 'MOVEMENT_TYPE_FACE_DOWN'),
    ('away_same', 'OBJ_EVENT_GFX_VAR_2', 28, 66, 'MOVEMENT_TYPE_FACE_DOWN'),
    ('Luffy', 'OBJ_EVENT_GFX_JOURNEY_LUFFY', 21, 67, 'MOVEMENT_TYPE_FACE_RIGHT'),
    ('Eren', 'OBJ_EVENT_GFX_JOURNEY_EREN', 29, 67, 'MOVEMENT_TYPE_FACE_LEFT'),
)
TRIGGERS = ((25, 67), (26, 66), (27, 67))
OUTSIDE_FRAME_TABLE = (
    '\nJourneyQualifier_OutsideOnFrame:\n'
    '\tmap_script_2 VAR_JOURNEY_QUALIFIER_STATE, 2, JourneyQualifier_Celebration\n'
    '\tmap_script_2 VAR_JOURNEY_QUALIFIER_STATE, 4, JourneyQualifier_Gathered\n'
    '\t.2byte 0\n'
)


def _once(text, before, after, path):
    if after in text:
        assert text.count(after) == 1, path
        return text
    assert text.count(before) == 1, (path, before)
    return text.replace(before, after)


def repair(layer):
    from badge_story_layer import read

    mapping = json.loads(read(layer, OUTSIDE))
    before = json.loads(json.dumps(mapping))
    assert mapping['id'] == 'MAP_BATTLE_FRONTIER_OUTSIDE_WEST'
    assert mapping['layout'] == 'LAYOUT_BATTLE_FRONTIER_OUTSIDE_WEST'
    ground = read(layer, GROUND)
    assert len(ground) == 56 * 74 * 2
    words = struct.unpack('<' + 'H' * (56 * 74), ground)
    scene_cells = {(26, 67), (19, 67), (20, 67), *TRIGGERS}
    scene_cells.update((x, y) for _, _, x, y, _ in PARTY)
    assert all(words[y * 56 + x] == 0x005E for x, y in scene_cells)

    actors = []
    for _, graphics, x, y, facing in PARTY:
        actors.append(dict(graphics_id=graphics, x=x, y=y, elevation=0,
            movement_type=facing, movement_range_x=0, movement_range_y=0,
            trainer_type='TRAINER_TYPE_NONE', trainer_sight_or_berry_tree_id='0',
            script='JourneyQualifier_Contact', flag='0'))
    if len(mapping['object_events']) == 25:
        occupied = {(o['x'], o['y']) for o in mapping['object_events']}
        assert not occupied.intersection((o['x'], o['y']) for o in actors)
        mapping['object_events'].extend(actors)
    else:
        assert len(mapping['object_events']) == 30 and mapping['object_events'][25:] == actors
    assert not {(19, 67), (20, 67)}.intersection((o['x'], o['y']) for o in actors)
    triggers = [dict(type='trigger', x=x, y=y, elevation=0,
        var='VAR_TEMP_4', var_value='0', script='JourneyQualifier_Arrival') for x, y in TRIGGERS]
    if not mapping['coord_events']:
        mapping['coord_events'] = triggers
    else:
        assert mapping['coord_events'] == triggers
    layer.stage(OUTSIDE, json.dumps(mapping, indent=2) + '\n')

    text = read(layer, WEST_SCRIPT).decode()
    text = _once(text,
        '\tmap_script MAP_SCRIPT_ON_TRANSITION, BattleFrontier_OutsideWest_OnTransition\n',
        '\tmap_script MAP_SCRIPT_ON_TRANSITION, BattleFrontier_OutsideWest_OnTransition\n'
        '\tmap_script MAP_SCRIPT_ON_FRAME_TABLE, JourneyQualifier_OutsideOnFrame\n', WEST_SCRIPT)
    text = _once(text, 'BattleFrontier_OutsideWest_OnTransition:\n',
        'BattleFrontier_OutsideWest_OnTransition:\n\tcallnative JourneyQualifierFieldSetup\n', WEST_SCRIPT)
    if 'JourneyQualifier_OutsideOnFrame:' not in text:
        text += OUTSIDE_FRAME_TABLE
    layer.stage(WEST_SCRIPT, text)

    text = read(layer, ARENA_SCRIPT).decode()
    text = _once(text, '\tmap_script_2 VAR_TEMP_1, 0, JourneyPWT_ArenaStart\n',
        '\tmap_script_2 VAR_TEMP_1, 0, JourneyQualifier_ArenaDispatch\n', ARENA_SCRIPT)
    layer.stage(ARENA_SCRIPT, text)

    text = read(layer, GALACTIC).decode()
    text = _once(text, '#include "global.h"\n',
        '#include "global.h"\n#include "journey_qualifier_field.h"\n', GALACTIC)
    text = _once(text,
        'bool32 JourneyGalacticObjectVisible(const struct ObjectEventTemplate *o,u8 group,u8 num)\n{\n',
        'bool32 JourneyGalacticObjectVisible(const struct ObjectEventTemplate *o,u8 group,u8 num)\n{\n'
        ' if (!JourneyQualifierFieldObjectVisible(o, group, num)) return FALSE;\n', GALACTIC)
    layer.stage(GALACTIC, text)

    text = read(layer, CAMPAIGN).decode()
    text = _once(text, 'Journey_FirstBadgeReward::\n',
        'Journey_FirstBadgeReward::\n\tcall JourneyBadgeStory_Notify\n', CAMPAIGN)
    layer.stage(CAMPAIGN, text)

    text = read(layer, EVENTS).decode()
    text = _once(text, '\t.include "data/scripts/journey_galactic.inc"\n',
        '\t.include "data/scripts/journey_galactic.inc"\n'
        '\t.include "data/scripts/journey_badge_qualifier.inc"\n', EVENTS)
    layer.stage(EVENTS, text)

    for resource, target in [
        ('badge_qualifier_field.c', 'src/journey_qualifier_field.c'),
        ('badge_qualifier_field.h', 'include/journey_qualifier_field.h'),
        ('badge_qualifier.inc', 'data/scripts/journey_badge_qualifier.inc'),
    ]:
        layer.stage(target, (HERE / resource).read_bytes())
    assert mapping['object_events'][:25] == before['object_events'][:25]
    assert all(mapping[key] == before[key] for key in mapping if key not in {'object_events', 'coord_events'})
    return dict(outside_map='BattleFrontier_OutsideWest', player_scene_position=[26, 67],
        actors=[dict(role=role, local_id=26 + index, position=[x, y], graphics=graphics)
                for index, (role, graphics, x, y, _) in enumerate(PARTY)],
        original_outdoor_npc_count=25, original_npcs_preserved=True,
        scene_triggers=[list(cell) for cell in TRIGGERS],
        boat_landing_clear=[[19, 67], [20, 67]],
        original_terrain_sha256=hashlib.sha256(ground).hexdigest(),
        terrain_buildings_warps_and_original_pwt_scripts_unchanged=True,
        arena='JourneyPWTArena', independent_stadium_opponent_local_id=14,
        native_arena_positions=dict(player=[9, 6], opponent=[13, 6]),
        five_personal_congratulations_outside=True,
        badges_18_and_22_notices=True, failure_center='BattleFrontier_PokemonCenter_1F')
