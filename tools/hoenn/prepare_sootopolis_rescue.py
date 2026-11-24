"""Stage the mandatory Sootopolis rescue in a private PWT-complete source."""
import argparse
import json
from pathlib import Path
import struct

from badge_story_layer import read
from candidate_layer import Layer
from prepare_pwt_complete_rosters import LAYER as PREVIOUS, PRIOR as PREVIOUS_LAYERS

LAYER = 'sootopolis-rescue'
PRIOR = PREVIOUS_LAYERS + [PREVIOUS]
DATA = Path(__file__).parent / 'data/sootopolis-rescue'
AREA = 'JourneySootopolisRescue'
PORT = 'JourneySootopolisHarbor'
LAYOUT = 'LAYOUT_JOURNEY_SOOTOPOLIS_RESCUE'
MAP = 'MAP_JOURNEY_SOOTOPOLIS_RESCUE'
WIDTH, HEIGHT = 26, 24
OCEAN = 0x112B
GYM_LEADERS = {
    'RustboroCity_Gym': 'Roxanne', 'DewfordTown_Gym': 'Brawly',
    'MauvilleCity_Gym': 'Wattson', 'LavaridgeTown_Gym_1F': 'Flannery',
    'PetalburgCity_Gym': 'Norman', 'FortreeCity_Gym': 'Winona',
    'MossdeepCity_Gym': 'TateAndLiza', 'SootopolisCity_Gym_1F': 'Juan',
}


def replace(layer, path, old, new):
    contents = read(layer, path).decode()
    if contents.count(old) != 1:
        raise ValueError(('Unrecognized source anchor', path, old))
    layer.stage(path, contents.replace(old, new))


def read_json(layer, path):
    return json.loads(read(layer, path))


def stage_json(layer, path, value):
    layer.stage(path, json.dumps(value, indent=2) + '\n')


def actor(graphics, x, y, elevation, direction, script, flag='0'):
    return dict(graphics_id='OBJ_EVENT_GFX_' + graphics, x=x, y=y,
                elevation=elevation, movement_type='MOVEMENT_TYPE_FACE_' + direction,
                movement_range_x=0, movement_range_y=0, trainer_type='TRAINER_TYPE_NONE',
                trainer_sight_or_berry_tree_id='0', script='JourneyRescue_' + script, flag=flag)


def stage_area(layer):
    layouts_path = 'data/layouts/layouts.json'
    layouts = read_json(layer, layouts_path)
    donor = next(row for row in layouts['layouts'] if row['id'] == 'LAYOUT_JOURNEYWORLDSEA01')
    if (donor['width'], donor['height'], donor['layout_version']) != (64, 48, 'frlg'):
        raise ValueError('Unexpected beach donor layout')
    donor_words = [word for word, in struct.iter_unpack('<H', read(layer, donor['blockdata_filepath']))]
    cells = [OCEAN] * (WIDTH * HEIGHT)
    # Copy each complete sandbar, including the native wet edges and a water margin.
    for left, top, width, height, target_x, target_y in [(12, 4, 10, 9, 12, 2), (8, 29, 9, 7, 3, 16)]:
        for row in range(height):
            start = (top + row) * donor['width'] + left
            destination = (target_y + row) * WIDTH + target_x
            cells[destination:destination + width] = donor_words[start:start + width]
    occupied = [(6, 18), (8, 18), (17, 7), (18, 7), (7, 19)]
    if any(cells[y * WIDTH + x] != 0x3115 for x, y in occupied):
        raise ValueError('A rescue actor or the ferry landing is outside dry sand')
    for x, y in ((12, 13), (11, 18), (11, 19), (11, 20), (12, 16), (3, 20)):
        if cells[y * WIDTH + x] != OCEAN:
            raise ValueError('A water actor is outside open water')
    block_path = f'data/layouts/{AREA}/map.bin'
    layer.stage(block_path, struct.pack(f'<{len(cells)}H', *cells))
    layouts['layouts'].append(dict(donor, id=LAYOUT, name=AREA + '_Layout',
                                   width=WIDTH, height=HEIGHT, blockdata_filepath=block_path))
    stage_json(layer, layouts_path, layouts)

    groups_path = 'data/maps/map_groups.json'
    groups = read_json(layer, groups_path)
    group = 'JourneySootopolisStory'
    if group in groups or len(groups['group_order']) >= 128:
        raise ValueError('Cannot append the Sootopolis story group')
    groups['group_order'].append(group)
    groups[group] = [AREA]
    stage_json(layer, groups_path, groups)

    scene = read_json(layer, 'data/maps/JourneyWorldSea01/map.json')
    scene.update(id=MAP, name=AREA, layout=LAYOUT, region='REGION_HOENN',
                 region_map_section='MAPSEC_SOOTOPOLIS_CITY', show_map_name=False,
                 object_events=[
                     actor('SAILOR', 6, 18, 3, 'DOWN', 'Captain'),
                     actor('JOURNEY_LUFFY', 8, 18, 3, 'DOWN', 'Luffy'),
                     actor('SPECIES(MANAPHY)', 12, 13, 1, 'UP', 'Manaphy'),
                     actor('WOMAN_2', 17, 7, 3, 'DOWN', 'Castaway', 'FLAG_TEMP_3'),
                     actor('TWIN', 18, 7, 3, 'DOWN', 'Castaway', 'FLAG_TEMP_3'),
                     actor('LUGIA', 11, 18, 1, 'DOWN', 'Done', 'FLAG_TEMP_1'),
                     actor('KYOGRE_SIDE', 12, 16, 1, 'LEFT', 'Done', 'FLAG_TEMP_2'),
                     actor('MR_BRINEYS_BOAT', 3, 20, 1, 'RIGHT', 'Done', 'FLAG_TEMP_4'),
                 ])
    stage_json(layer, f'data/maps/{AREA}/map.json', scene)
    layer.stage(f'data/maps/{AREA}/scripts.inc', (DATA / 'rescue.inc').read_bytes())


def prepare(source):
    layer = Layer(source, LAYER, PRIOR)
    if previous := layer.existing():
        return previous
    stage_area(layer)

    path = f'data/maps/{PORT}/map.json'
    port = read_json(layer, path)
    captain, = [row for row in port['object_events'] if row['script'] == 'Journey_FerryPort17']
    captain['script'] = 'JourneyRescue_HarborCaptain'
    stage_json(layer, path, port)
    anchor = f'\t.include "data/maps/{PORT}/scripts.inc"\n'
    replace(layer, 'data/event_scripts.s', anchor, anchor + f'\t.include "data/maps/{AREA}/scripts.inc"\n')
    replace(layer, f'data/maps/{PORT}/scripts.inc', f'{PORT}_MapScripts::\n\t.byte 0\n',
            f'{PORT}_MapScripts::\n\tmap_script MAP_SCRIPT_ON_FRAME_TABLE, JourneyRescue_HarborOnFrame\n\t.byte 0\n')

    path = 'include/constants/vars.h'
    old = '#define VAR_UNUSED_0x40E5'
    original = next(row for row in read(layer, path).decode().splitlines() if row.startswith(old))
    replace(layer, path, original, '#define VAR_JOURNEY_SOOTOPOLIS_RESCUE                    0x40E5')
    replace(layer, 'include/journey_campaign_gates.h', '    JOURNEY_CAMPAIGN_EVENT_WEATHER_INSTITUTE = 15,\n',
            '    JOURNEY_CAMPAIGN_EVENT_WEATHER_INSTITUTE = 15,\n    JOURNEY_CAMPAIGN_EVENT_SOOTOPOLIS_RESCUE = 24,\n')
    path = 'src/journey_campaign_gates.c'
    original = read(layer, path).decode()
    key = 'u32 JourneyPendingCampaignEvent(bool32 kanto)\n'
    hook = """static bool32 JourneyRescueAfterRayquaza(void)
{
    // Rayquaza's three arrival paths finish with Sky Pillar state 2 or 3.
    return RegionalFlag(FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN)
        && !RegionalFlag(FLAG_SYS_WEATHER_CTRL)
        && VarGet(VAR_SKY_PILLAR_STATE) >= 2;
}

static bool32 JourneySootopolisRescuePending(void)
{
    return JourneyRescueAfterRayquaza()
        && VarGet(VAR_JOURNEY_SOOTOPOLIS_RESCUE) < 4;
}

void JourneySootopolisRescueStatus(void)
{
    gSpecialVar_Result = JourneySootopolisRescuePending();
}

void JourneySootopolisRescueGymGuard(void)
{
    // A pre-existing save inside the unwon gym still has to finish the rescue.
    gSpecialVar_Result = 0;
    if (JourneyGymBadgeCount(FALSE) == 7
        && !RegionalFlag(FLAG_BADGE01_GET + gSpecialVar_0x8004))
        gSpecialVar_Result = JourneyPendingCampaignEvent(FALSE);
}

"""
    key_gate = '            return JOURNEY_CAMPAIGN_EVENT_RAYQUAZA;\n'
    if original.count(key) != 1 or original.count(key_gate) != 1:
        raise ValueError('Unrecognized campaign gate source')
    hook_anchor = 'bool32 JourneyCanChallengeSilph(void)\n'
    ready, guard = hook.split('void JourneySootopolisRescueGymGuard(void)', 1)
    original = original.replace(key, ready + key).replace(hook_anchor, 'void JourneySootopolisRescueGymGuard(void)' + guard + hook_anchor)
    layer.stage(path, original.replace(key_gate, key_gate
                + '        if (count == 7 && JourneySootopolisRescuePending())\n'
                  '            return JOURNEY_CAMPAIGN_EVENT_SOOTOPOLIS_RESCUE;\n'))
    replace(layer, 'data/specials.inc', '\tdef_special JourneyExplainGymGate\n',
            '\tdef_special JourneyExplainGymGate\n\tdef_special JourneySootopolisRescueStatus\n'
            '\tdef_special JourneySootopolisRescueGymGuard\n')
    replace(layer, 'data/scripts/journey_campaign_gates.inc',
            '\tgoto_if_eq VAR_RESULT, 22, Journey_GymGuide_Event22\n',
            '\tgoto_if_eq VAR_RESULT, 22, Journey_GymGuide_Event22\n'
            '\tgoto_if_eq VAR_RESULT, 24, JourneyRescue_GymGuide\n')
    for badge, (gym, leader) in enumerate(GYM_LEADERS.items()):
        path = f'data/maps/{gym}/scripts.inc'
        anchor = f'{gym}_EventScript_{leader}::\n'
        replace(layer, path, anchor, anchor + f'\tsetvar VAR_0x8004, {badge}\n'
                '\tspecial JourneySootopolisRescueGymGuard\n'
                '\tgoto_if_ne VAR_RESULT, 0, JourneyRescue_IndoorGymRedirect\n')

    return layer.finish(mandatory=True, after_rayquaza=True, before_final_hoenn_gym=True,
                        save_variable='0x40E5', scope='sootopolis-rescue')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('private_source', type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.private_source), indent=2))
