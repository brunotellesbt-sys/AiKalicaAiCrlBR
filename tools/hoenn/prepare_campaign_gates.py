"""Add regional story checkpoints and gym-door guides to the native candidate."""
import argparse
import hashlib
import json
import re
from pathlib import Path

from prepare_crossing import PIN
from prepare_gym_scaling import HOENN, KANTO

MESSAGES = {
    1: ('TEAM ROCKET', ['Take ROUTE 7 to CELADON.', 'Go below the GAME CORNER', 'and help in the hideout!']),
    2: ('TEAM ROCKET', ['Take ROUTE 7 or 8.', 'In SAFFRON, go help at', 'SILPH CO., on floor 11!']),
    3: ('TEAM MAGMA', ['Take the cable car on', 'ROUTE 112 to MT. CHIMNEY.', 'Please help at the summit!']),
    4: ('TEAM MAGMA', ['Take ROUTE 112 and head', 'to JAGGED PASS.', 'Help inside MAGMA HIDEOUT!']),
    5: ('TEAM MAGMA', ['Cross ROUTE 124 to MOSSDEEP.', 'Help at the SPACE CENTER,', 'on the second floor!']),
    6: ('TEAM AQUA', ['Use DIVE on ROUTE 128.', 'Help deep inside the', 'SEAFLOOR CAVERN!']),
}


def cities_header(cities):
    return ('static const struct JourneyGymCity sJourneyGymCities[] = {\n'
            + ''.join(f'    {{{c["id"]}, {"TRUE" if c["kanto"] else "FALSE"}, {c["badge"]}, '
                      f'{c["door"]["x"]}, {c["door"]["y"]}, {c["guide_local_id"]}}},\n' for c in cities) + '};\n')


def warp_hook(text):
    anchor = '    if (direction == DIR_NORTH)\n    {\n        if (MetatileBehavior_IsOpenSecretBaseDoor'
    if text.count(anchor) != 1:
        raise ValueError('Unexpected native door warp')
    text = text.replace('#include "global.h"', '#include "global.h"\n#include "journey_campaign_gates.h"', 1)
    return text.replace(anchor, '    if (direction == DIR_NORTH)\n    {\n'
        '        if (JourneyTryGymDoorGate(position->x, position->y))\n            return TRUE;\n'
        '        if (MetatileBehavior_IsOpenSecretBaseDoor')


def prepare(source, refresh_helpers=False):
    source = Path(source)
    marker = source / '.journey-campaign-gates'
    if marker.exists():
        report = json.loads(marker.read_text())
        for path, digest in report['prepared_sha256'].items():
            if hashlib.sha256((source / path).read_bytes()).hexdigest() != digest:
                raise ValueError('Modified campaign output: ' + path)
        if refresh_helpers:
            acquired = json.loads((source / '.source-acquired.json').read_text())
            helpers = Path(__file__).parent
            updates = {'src/journey_campaign_gates.c': (helpers / 'campaign_gates.c').read_text(),
                       'include/journey_campaign_gates.h': (helpers / 'campaign_gates.h').read_text(),
                       'include/journey_gym_cities.h': cities_header(report['cities'])}
            path = 'src/field_control_avatar.c'
            if path not in report['prepared_sha256']:
                if hashlib.sha256((source / path).read_bytes()).hexdigest() != acquired['sha256'][path]:
                    raise ValueError('Unreviewed door warp source')
                updates[path] = warp_hook((source / path).read_text())
            else:
                text = (source / path).read_text().replace('#include "journey_campaign_gates.h"\n','')
                text = text.replace('                if (JourneyTryGymDoorGate(position->x, position->y))\n                    return TRUE;\n','')
                text = text.replace('        if (JourneyTryGymDoorGate(position->x, position->y))\n            return TRUE;\n','')
                updates[path] = warp_hook(text)
            for path, text in updates.items():
                if path not in report['original_sha256']:
                    report['original_sha256'][path] = acquired['sha256'].get(path)
                (source / path).write_text(text)
                report['prepared_sha256'][path] = hashlib.sha256(text.encode()).hexdigest()
            marker.write_text(json.dumps(report, indent=2) + '\n')
        return report
    acquired = json.loads((source / '.source-acquired.json').read_text())
    if acquired['commit'] != PIN:
        raise ValueError('Unexpected base')
    expected = dict(acquired['sha256'])
    for name in ['hoenn-crossing', 'worldsea', 'westsea', 'region-state', 'east-coast', 'gym-scaling']:
        expected.update(json.loads((source / f'.journey-{name}').read_text())['prepared_sha256'])
    outputs, originals, cities = {}, {}, []

    def stage(path, text):
        target = source / path
        digest = hashlib.sha256(target.read_bytes()).hexdigest() if target.exists() else None
        if digest is not None and digest != expected.get(path):
            raise ValueError('Unreviewed modification: ' + path)
        originals[path] = digest
        outputs[path] = text.encode()

    for kanto, gyms in [(False, HOENN), (True, KANTO)]:
        badge = 0
        for gym in gyms:
            if gym.endswith('_B1F'):
                continue
            city = gym.split('_Gym')[0] + ('_Frlg' if kanto else '')
            path = f'data/maps/{city}/map.json'
            data = json.loads((source / path).read_text())
            gym_id = json.loads((source / f'data/maps/{gym}/map.json').read_text())['id']
            entrances = [w for w in data['warp_events'] if w['dest_map'] == gym_id]
            if len(entrances) != 1:
                raise ValueError('Ambiguous gym entrance: ' + city)
            door = entrances[0]
            if any(o['x'] == door['x'] and o['y'] == door['y'] for o in data['object_events']):
                raise ValueError('Occupied gym door: ' + city)
            # Appending retains implicit local IDs of every native object.
            data['object_events'].append(dict(type='object', graphics_id='OBJ_EVENT_GFX_MAN',
                x=door['x'], y=door['y'], elevation=0, movement_type='MOVEMENT_TYPE_FACE_DOWN',
                movement_range_x=0, movement_range_y=0, trainer_type='TRAINER_TYPE_NONE',
                trainer_sight_or_berry_tree_id='0', script='Journey_GymGuide',
                flag='FLAG_HIDE_JOURNEY_' + ('KANTO' if kanto else 'HOENN') + '_GYM_GUIDE'))
            stage(path, json.dumps(data, indent=2) + '\n')
            path = f'data/maps/{city}/scripts.inc'
            script = (source / path).read_text()
            onload = re.search(r'map_script MAP_SCRIPT_ON_LOAD, (\w+)', script)
            if onload:
                anchor = re.search(r'^' + onload[1] + r'::?\n', script, re.M)
                if not anchor:
                    raise ValueError('Missing on-load script: ' + city)
                script = script[:anchor.end()] + '\tspecial JourneyUpdateGymGate\n' + script[anchor.end():]
            else:
                anchor = re.search(r'^\w+_MapScripts::\n', script)
                if not anchor:
                    raise ValueError('Missing map scripts: ' + city)
                label = 'Journey_' + city + '_OnLoad'
                script = script[:anchor.end()] + f'\tmap_script MAP_SCRIPT_ON_LOAD, {label}\n' + script[anchor.end():]
                script += f'\n{label}::\n\tspecial JourneyUpdateGymGate\n\tend\n'
            stage(path, script)
            cities.append(dict(map=city, id=data['id'], kanto=kanto, badge=badge,
                               door=door, guide_local_id=len(data['object_events'])))
            badge += 1
    stage('include/journey_gym_cities.h', cities_header(cities))
    stage('src/journey_campaign_gates.c', (Path(__file__).parent / 'campaign_gates.c').read_text())
    stage('include/journey_campaign_gates.h', (Path(__file__).parent / 'campaign_gates.h').read_text())
    path = 'src/field_control_avatar.c'
    stage(path, warp_hook((source / path).read_text()))
    path = 'include/constants/flags.h'
    text = (source / path).read_text()
    anchor = '#define JOURNEY_FLAGS_END 0x1ABF'
    if text.count(anchor) != 1:
        raise ValueError('Unexpected regional flag allocation')
    stage(path, text.replace(anchor, '#define FLAG_HIDE_JOURNEY_KANTO_GYM_GUIDE 0x1AB9\n'
                            '#define FLAG_HIDE_JOURNEY_HOENN_GYM_GUIDE 0x1ABA\n' + anchor))
    path = 'data/specials.inc'
    stage(path, (source / path).read_text() + '\tdef_special JourneyUpdateGymGate\n'
          '\tdef_special JourneyExplainGymGate\n\tdef_special JourneyStartSpaceCenterInvasion\n')
    script = 'Journey_GymGuide::\n\tlock\n\tfaceplayer\n\tspecial JourneyExplainGymGate\n'
    for event in MESSAGES:
        script += f'\tgoto_if_eq VAR_RESULT, {event}, Journey_GymGuide_Event{event}\n'
    script += '\trelease\n\tend\n'
    for event, (team, lines) in MESSAGES.items():
        script += f'\nJourney_GymGuide_Event{event}::\n\tmsgbox Journey_GymGuide_Text{event}, MSGBOX_DEFAULT\n\trelease\n\tend\n'
        paragraphs = ['The GYM LEADER is busy', 'helping fight ' + team + '!'] + lines
        script += f'\nJourney_GymGuide_Text{event}::\n'
        for i, line in enumerate(paragraphs):
            if len(line) > 28:
                raise ValueError('Dialogue line too long: ' + line)
            suffix = '$' if i == len(paragraphs)-1 else ('\\p' if i == 1 else '\\n' if i % 2 == 0 else '\\l')
            script += f'\t.string "{line}{suffix}"\n'
    stage('data/scripts/journey_campaign_gates.inc', script)
    path = 'data/event_scripts.s'
    stage(path, (source / path).read_text() + '\n\t.include "data/scripts/journey_campaign_gates.inc"\n')

    # This original post-gym block would otherwise re-enable the invasion when
    # the player later defeats Mossdeep, even after completing the story event.
    path = 'data/maps/MossdeepCity_Gym/scripts.inc'
    text = (source / path).read_text()
    begin = '\tclearflag FLAG_HIDE_SLATEPORT_CITY_HARBOR_PATRONS\n'
    end = '\tsetvar VAR_MOSSDEEP_SPACE_CENTER_STATE, 1\n'
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError('Unexpected Mossdeep invasion trigger')
    start = text.index(begin); stop = text.index(end, start) + len(end)
    stage(path, text[:start] + '\tspecial JourneyStartSpaceCenterInvasion\n' + text[stop:])
    # Dive remains a field move requiring a Pokemon with Dive. Completing the
    # Space Center now permits it before the seventh badge, avoiding a cycle.
    path = 'src/field_move.c'
    text = (source / path).read_text()
    old = 'static bool32 IsFieldMoveUnlocked_Dive(void)\n{\n    return FlagGet(FLAG_BADGE07_GET);\n}'
    new = 'static bool32 IsFieldMoveUnlocked_Dive(void)\n{\n    return FlagGet(FLAG_BADGE07_GET) || FlagGet(FLAG_DEFEATED_MAGMA_SPACE_CENTER);\n}'
    if text.count(old) != 1:
        raise ValueError('Unexpected Dive gate')
    stage(path, text.replace(old, new))
    for path, raw in outputs.items():
        target = source / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    report = dict(status='regional_checkpoint_guides_campaign_access_still_pending',
        source_commit=PIN, cities=cities, guide_flags=[0x1AB9, 0x1ABA],
        before_gym_ordinals=dict(kanto=[3, 4], hoenn=[3, 6, 7, 7]),
        completed_events_release_gate=True, defeated_gyms_remain_open=True,
        physical_gym_access_validated=False, full_story_validated=False,
        original_sha256=originals,
        prepared_sha256={p: hashlib.sha256(raw).hexdigest() for p, raw in outputs.items()})
    marker.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--refresh-helpers', action='store_true', help='Refresh helper code only after checking all prepared hashes')
    args = parser.parse_args()
    print(json.dumps(prepare(args.source,args.refresh_helpers), indent=2))
