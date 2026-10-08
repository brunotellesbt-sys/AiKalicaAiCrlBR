"""Homes in Hoenn, selected-city truck arrivals in both regions and two starters."""
import argparse
import copy
from collections import deque
import hashlib
import json
from pathlib import Path
import re
import struct
from prepare_crossing import PIN
from prepare_family import LAYERS_BEFORE, HERE


def prepare(source):
    source = Path(source)
    marker = source / '.journey-birth'
    if marker.exists():
        report = json.loads(marker.read_text())
        for path, digest in report['prepared_sha256'].items():
            assert hashlib.sha256((source / path).read_bytes()).hexdigest() == digest, path
        return report
    acquired = json.loads((source / '.source-acquired.json').read_text())
    assert acquired['commit'] == PIN
    expected = dict(acquired['sha256'])
    for layer in LAYERS_BEFORE + ['family', 'travel-rules']:
        expected.update(json.loads((source / f'.journey-{layer}').read_text())['prepared_sha256'])
    inputs, originals, outputs = {}, {}, {}

    def read(path):
        if path in outputs: return outputs[path]
        raw = (source / path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected[path], path
        if path in acquired['sha256']: inputs[path] = acquired['sha256'][path]
        return raw

    def stage(path, body):
        if path in expected and path not in originals: originals[path] = hashlib.sha256(read(path)).hexdigest()
        elif path not in expected and (source / path).exists(): assert (source / path).read_bytes() == body.encode(), path
        outputs[path] = body.encode()

    def replace(path, anchor, value):
        body = read(path).decode()
        assert body.count(anchor) == 1, (path, anchor)
        stage(path, body.replace(anchor, value))

    config = json.loads((HERE / 'hoenn_homes.json').read_text())
    load = lambda name: json.loads(read(f'data/maps/{name}/map.json'))
    living = load('LittlerootTown_BrendansHouse_1F')
    bedroom = load('LittlerootTown_BrendansHouse_2F')
    groups = json.loads(read('data/maps/map_groups.json'))
    groups['group_order'] += ['JourneyHoennBedrooms', 'JourneyHoennLivingRooms']
    groups['JourneyHoennBedrooms'], groups['JourneyHoennLivingRooms'] = [], []
    homes = copy.deepcopy(json.loads((source / '.journey-family').read_text())['homes'])
    rows = []
    for city, choice in enumerate(config['cities']):
        name = choice['house']
        original = load(name)
        if city == 0:
            people = [living['object_events'][0]]
        else:
            people = [o for o in original['object_events'] if not any(t in o['graphics_id'] for t in ['ZIGZAGOON', 'KECLEON', 'SKITTY', 'POOCHYENA', 'PIDGEY', 'CLIPBOARD'])]
        assert 1 <= len(people) <= 3, name
        female = lambda o: any(t in o['graphics_id'] for t in ['MOM', 'WOMAN', 'GIRL', 'POKEFAN_F', 'EXPERT_F', 'LASS', 'BEAUTY'])
        mother = next((i for i, o in enumerate(people) if female(o)), 0)
        people.insert(0, people.pop(mother))
        roles = [1]
        for o in people[1:]:
            roles.append(4 if female(o) else 3 if 'BOY' in o['graphics_id'] or 2 in roles else 2)
        roles += [0] * (3 - len(roles))
        bname, lname = f'JourneyHoennBedroom{city:02d}', f'JourneyHoennLiving{city:02d}'
        bid, lid = f'MAP_JOURNEY_HOENN_BEDROOM_{city:02d}', f'MAP_JOURNEY_HOENN_LIVING_{city:02d}'
        if city == 0: bid, lid = bedroom['id'], living['id']
        rows.append('{' + ', '.join([original['id'], lid, bid, choice['heal'], str(len(people)), str(roles[1]), str(roles[2])]) + '}')
        homes.append(dict(index=17 + city, city=choice['name'], house=name, original_map=original['id'], living_map=lid,
            bedroom_map=bid, heal=choice['heal'], people=len(people), roles=roles[:len(people)], region='HOENN',
            original_people=[o['graphics_id'] for o in people]))
        if city == 0: continue
        out = copy.deepcopy(living)
        out.update(id=lid, name=lname, music=original['music'], region_map_section=original['region_map_section'])
        out['object_events'] = []
        graphics = {1: 'OBJ_EVENT_GFX_MOM', 2: 'OBJ_EVENT_GFX_MAN_1', 3: 'OBJ_EVENT_GFX_LITTLE_BOY', 4: 'OBJ_EVENT_GFX_LITTLE_GIRL'}
        for person, role in enumerate(roles[:len(people)]):
            obj = copy.deepcopy(living['object_events'][0])
            obj.update(local_id=f'LOCALID_JOURNEY_HOENN_FAMILY_{city}_{person + 1}', graphics_id=graphics[role],
                x=[2, 6, 2][person], y=[6, 7, 8][person], movement_type='MOVEMENT_TYPE_FACE_RIGHT',
                script='Journey_Family', flag='0')
            out['object_events'].append(obj)
        for gfx, x, y, script in [('OBJ_EVENT_GFX_PROF_BIRCH', 6, 5, 'Journey_Oak'), ('OBJ_EVENT_GFX_BIRCHS_BAG', 4, 6, 'Journey_Case')]:
            obj = copy.deepcopy(living['object_events'][0])
            obj.update(local_id=f'LOCALID_JOURNEY_HOENN_FAMILY_{city}_{len(out["object_events"]) + 1}', graphics_id=gfx,
                x=x, y=y, movement_type='MOVEMENT_TYPE_FACE_DOWN', script=script, flag='FLAG_JOURNEY_FAMILY_HIDE_VISITOR')
            out['object_events'].append(obj)
        exit_warp = original['warp_events'][0]
        for w in out['warp_events']:
            if w['dest_map'] == 'MAP_LITTLEROOT_TOWN': w.update(dest_map=exit_warp['dest_map'], dest_warp_id=exit_warp['dest_warp_id'])
            else: w.update(dest_map=bid, dest_warp_id='0')
        out['coord_events'] = [dict(type='trigger', x=w['x'], y=w['y'], elevation=w['elevation'],
            var='VAR_JOURNEY_FAMILY_STAGE', var_value='1', script='Journey_NeedStarter')
            for w in out['warp_events'] if w['dest_map'] == exit_warp['dest_map']]
        stage(f'data/maps/{lname}/map.json', json.dumps(out, indent=2) + '\n')
        stage(f'data/maps/{lname}/scripts.inc', lname + '_MapScripts::\n\tmap_script MAP_SCRIPT_ON_TRANSITION, Journey_Living_Transition\n\t.byte 0\n')
        b = copy.deepcopy(bedroom)
        b.update(id=bid, name=bname, music=original['music'], region_map_section=original['region_map_section'])
        b['object_events'], b['coord_events'] = [], []
        b['warp_events'][0].update(dest_map=original['id'], dest_warp_id='2')
        stage(f'data/maps/{bname}/map.json', json.dumps(b, indent=2) + '\n')
        stage(f'data/maps/{bname}/scripts.inc', bname + '_MapScripts::\n\t.byte 0\n')
        groups['JourneyHoennBedrooms'].append(bname)
        groups['JourneyHoennLivingRooms'].append(lname)
    stage('data/maps/map_groups.json', json.dumps(groups, indent=2) + '\n')
    path = 'include/journey_family_homes.h'
    replace(path, '\n};\n', ',\n' + ',\n'.join(rows) + '\n};\n')
    path = 'data/event_scripts.s'
    body = read(path).decode() + '\n\t.include "data/scripts/journey_birth.inc"\n'
    for name in groups['JourneyHoennBedrooms'] + groups['JourneyHoennLivingRooms']:
        body += f'\t.include "data/maps/{name}/scripts.inc"\n'
    stage(path, body)
    for a, b in [('birth.c', 'src/journey_birth.c'), ('birth.h', 'include/journey_birth.h'), ('birth.inc', 'data/scripts/journey_birth.inc')]: stage(b, (HERE / a).read_text())
    path = 'include/journey_family.h'
    replace(path, '#define GUARD_JOURNEY_FAMILY_H\n', '#define GUARD_JOURNEY_FAMILY_H\nstruct JourneyFamilyHome {\n    u16 originalMap, livingMap, bedroomMap, healLocation;\n    u8 people, secondRole, thirdRole;\n};\nconst struct JourneyFamilyHome *JourneyFamilySelectedHome(void);\n')
    path = 'src/journey_family.c'
    body = read(path).decode()
    body = body.replace('#include "journey_family.h"', '#include "journey_family.h"\n#include "journey_birth.h"')
    body, count = re.subn(r'struct JourneyFamilyHome \{.*?\n\};\n', '', body, flags=re.S)
    assert count == 1
    body = body.replace('static const struct JourneyFamilyHome *SelectedHome(void)', 'const struct JourneyFamilyHome *JourneyFamilySelectedHome(void)').replace('SelectedHome()', 'JourneyFamilySelectedHome()')
    body = body.replace('VarGet(VAR_JOURNEY_FAMILY_HOME) == 1)', '(VarGet(VAR_JOURNEY_FAMILY_HOME) == 1 || VarGet(VAR_JOURNEY_FAMILY_HOME) == 17))')
    body, count = re.subn(r'void JourneyFamilyGiveStarter\(void\)\n\{.*?\n\}', 'void JourneyFamilyGiveStarter(void)\n{\n    JourneyBirthGiveHomeStarter();\n}', body, flags=re.S)
    assert count == 1
    stage(path, body)
    path = 'include/constants/vars.h'
    replace(path, '#define VAR_UNUSED_0x40FC', '#define VAR_JOURNEY_BIRTH_ARRIVAL 0x40FC\n#define VAR_UNUSED_0x40FC')
    replace('include/constants/flags.h', '#define JOURNEY_FLAGS_END 0x1ABF', '#define FLAG_JOURNEY_KANTO_STARTER_GIVEN 0x1AC0\n#define FLAG_JOURNEY_HOENN_STARTER_GIVEN 0x1AC1\n#define JOURNEY_FLAGS_END 0x1ACF')
    replace('include/constants/event_objects.h', '#define LOCALID_FOLLOWING_POKEMON', '#define LOCALID_JOURNEY_ARRIVAL_TRUCK 250\n#define LOCALID_JOURNEY_ARRIVAL_MOM 251\n#define LOCALID_FOLLOWING_POKEMON')
    path = 'include/constants/script_menu.h'
    replace(path, '    MULTI_JOURNEY_STARTERS,', '    MULTI_JOURNEY_STARTERS,\n    MULTI_JOURNEY_START_HOENN,\n    MULTI_JOURNEY_HOENN_STARTERS,')
    menu = 'static const struct MenuAction sJourneyStartHoenn[] = {\n' + ''.join('    {COMPOUND_STRING("' + c['name'] + '")},\n' for c in config['cities']) + '};\n'
    menu += 'static const struct MenuAction sJourneyHoennStarters[] = {\n    {COMPOUND_STRING("TREECKO")},\n    {COMPOUND_STRING("TORCHIC")},\n    {COMPOUND_STRING("MUDKIP")},\n};\n'
    replace('src/data/script_menu.h', 'static const struct MultichoiceListStruct sMultichoiceLists[] =\n{', menu + '\nstatic const struct MultichoiceListStruct sMultichoiceLists[] =\n{\n    [MULTI_JOURNEY_START_HOENN] = MULTICHOICE(sJourneyStartHoenn),\n    [MULTI_JOURNEY_HOENN_STARTERS] = MULTICHOICE(sJourneyHoennStarters),')
    path = 'data/specials.inc'
    body = read(path).decode()
    for n in ['Region', 'ChooseCity', 'TruckDestination', 'SpawnArrival', 'RemoveArrival', 'HomeRegion', 'GiveHomeStarter', 'VisitOak', 'GiveKantoVisitStarter', 'CheckPartySpace', 'RecordHoennStarter', 'ArrivalVehicle']:
        body += '\n\tdef_special JourneyBirth' + n
    stage(path, body + '\n')
    path = 'src/new_game.c'
    replace(path, '''    if (gSaveBlock2Ptr->playerRegion == REGION_KANTO)
        SetWarpDestination(MAP_GROUP(MAP_PALLET_TOWN_PLAYERS_HOUSE_2F), MAP_NUM(MAP_PALLET_TOWN_PLAYERS_HOUSE_2F), WARP_ID_NONE, 6, 6);
    else
        SetWarpDestination(MAP_GROUP(MAP_INSIDE_OF_TRUCK), MAP_NUM(MAP_INSIDE_OF_TRUCK), WARP_ID_NONE, -1, -1);''', '    SetWarpDestination(MAP_GROUP(MAP_INSIDE_OF_TRUCK), MAP_NUM(MAP_INSIDE_OF_TRUCK), WARP_ID_NONE, -1, -1);')
    replace('src/overworld.c', '''    if (isFrlg)
        gFieldCallback = FieldCB_WarpExitFadeFromBlack;
    else
        gFieldCallback = ExecuteTruckSequence;''', '    gFieldCallback = ExecuteTruckSequence;')
    path = 'src/field_special_scene.c'
    replace(path, '#include "global.h"', '#include "global.h"\n#include "journey_birth.h"\n#include "constants/vars.h"')
    replace(path, '''    case 0:
        tTimer++;
        if (tTimer == 90)''', '''    case 0:
        if (VarGet(VAR_JOURNEY_FAMILY_HOME) == 0)
        {
            ScriptContext_SetupScript(JourneyBirth_ChooseCity);
            tState = 6;
            break;
        }
        tTimer++;
        if (tTimer == 90)''')
    replace(path, '''    case 5:
        tTimer++;
        if (tTimer == 120)''', '''    case 6:
        if (JourneyBirthMenuFinished())
        {
            LockPlayerFieldControls();
            BeginNormalPaletteFade(PALETTES_ALL, 0, 0, 16, 0x0000);
            tTimer = 0;
            tState = 0;
        }
        break;
    case 5:
        tTimer++;
        if (tTimer == 120)''')
    for old, new in [('SE_TRUCK_MOVE', 'SE_SHIP'), ('SE_TRUCK_STOP', 'SE_SHIP'), ('SE_TRUCK_UNLOAD', 'SE_SHIP'), ('SE_TRUCK_DOOR', 'SE_DOOR')]:
        replace(path, 'PlaySE(' + old + ');', 'PlaySE(JourneyBirthIsBoat() ? ' + new + ' : ' + old + ');')
    path = 'src/script.c'
    replace(path, '#include "global.h"', '#include "global.h"\n#include "journey_birth.h"')
    replace(path, '''    const u8 *ptr = MapHeaderCheckScriptTable(MAP_SCRIPT_ON_FRAME_TABLE);

    if (!ptr)''', '''    const u8 *ptr;
    if (JourneyBirthTryArrival()) return TRUE;
    ptr = MapHeaderCheckScriptTable(MAP_SCRIPT_ON_FRAME_TABLE);

    if (!ptr)''')
    path = 'data/maps/InsideOfTruck/scripts.inc'
    for coords in ['3, 10', '12, 10']:
        replace(path, '\tsetdynamicwarp MAP_LITTLEROOT_TOWN, ' + coords + '\n', '\tsetdynamicwarp MAP_LITTLEROOT_TOWN, ' + coords + '\n\tspecial JourneyBirthTruckDestination\n')
    path = 'data/scripts/players_house.inc'
    replace(path, 'PlayersHouse_1F_EventScript_Mom::\n', 'PlayersHouse_1F_EventScript_Mom::\n\tgoto_if_eq VAR_JOURNEY_FAMILY_HOME, 17, Journey_Family\n')
    replace(path, '\tcall Journey_WaterHMFamilyGift\n', '\tcall Journey_WaterHMFamilyGift\nPlayersHouse_1F_EventScript_MomOriginal::\n')
    path = 'data/scripts/journey_family.inc'
    replace(path, '\tgoto_if_eq VAR_0x8008, 1, PalletTown_PlayersHouse_1F_EventScript_MomOriginal', '\tgoto_if_eq VAR_0x8008, 1, JourneyBirth_FamilyMother')
    stage(path, read(path).decode() + '\nJourneyBirth_FamilyMother::\n\tspecial JourneyBirthHomeRegion\n\tgoto_if_eq VAR_RESULT, TRUE, JourneyBirth_HoennMother\n\tgoto PalletTown_PlayersHouse_1F_EventScript_MomOriginal\n')
    replace(path, '\tmsgbox Journey_Text_OakVisit\n\tclosemessage\nJourney_OakChoose::\n\tmultichoice 17, 0, MULTI_JOURNEY_STARTERS, TRUE', '''\tspecial JourneyBirthHomeRegion
\tgoto_if_eq VAR_RESULT, TRUE, JourneyBirth_BirchHomeVisit
\tmsgbox Journey_Text_OakVisit
\tgoto JourneyBirth_HomeProfessorCloseMessage
JourneyBirth_BirchHomeVisit::
\tmsgbox JourneyBirth_Text_BirchVisit
JourneyBirth_HomeProfessorCloseMessage::
\tclosemessage
Journey_OakChoose::
\tspecial JourneyBirthHomeRegion
\tgoto_if_eq VAR_RESULT, TRUE, JourneyBirth_ChooseHoennStarter
\tmultichoice 17, 0, MULTI_JOURNEY_STARTERS, TRUE
\tgoto JourneyBirth_ConfirmHomeStarter
JourneyBirth_ChooseHoennStarter::
\tmultichoice 17, 0, MULTI_JOURNEY_HOENN_STARTERS, TRUE
JourneyBirth_ConfirmHomeStarter::''')
    replace(path, '\tmsgbox Journey_Text_OakReturn\n', '\tspecial JourneyBirthHomeRegion\n\tgoto_if_eq VAR_RESULT, TRUE, JourneyBirth_ProfessorBirchReturn\n\tmsgbox Journey_Text_OakReturn\n\tgoto JourneyBirth_ProfessorHide\nJourneyBirth_ProfessorBirchReturn::\n\tmsgbox JourneyBirth_Text_BirchReturn\nJourneyBirth_ProfessorHide::\n')
    body = read(path).decode().replace('inicial de KANTO, no nível 5!', 'da sua regiao, no nível 5!').replace('Registre os POKéMON de KANTO.', 'Registre os POKéMON da regiao.')
    body = body.replace('OAK entregou a POKéDEX!', 'Recebeu a POKéDEX!')
    stage(path, body)
    path = 'data/maps/PalletTown_PlayersHouse_2F_Frlg/scripts.inc'
    replace(path, '\tmap_script MAP_SCRIPT_ON_FRAME_TABLE, Journey_FamilyCity_OnFrame\n', '')
    path = 'data/maps/PalletTown_ProfessorOaksLab_Frlg/scripts.inc'
    replace(path, '\tgivemon PLAYER_STARTER_SPECIES, 5\n', '\tgivemon PLAYER_STARTER_SPECIES, 5\n\tsetflag FLAG_JOURNEY_KANTO_STARTER_GIVEN\n')
    oak = re.search(r'^PalletTown_ProfessorOaksLab_EventScript_ProfOak::{1}\n', read(path).decode(), re.M)
    assert oak
    replace(path, oak[0], oak[0] + '\tspecial JourneyBirthVisitOak\n\tgoto_if_eq VAR_RESULT, TRUE, JourneyBirth_OakVisit\n')
    replace(path, 'PalletTown_ProfessorOaksLab_OnTransition::\n', 'PalletTown_ProfessorOaksLab_OnTransition::\n\tspecial JourneyBirthVisitOak\n\tcall_if_eq VAR_RESULT, TRUE, JourneyBirth_ShowOakForVisitor\n')
    stage(path, read(path).decode() + '\nJourneyBirth_ShowOakForVisitor::\n\tclearflag FLAG_HIDE_OAK_IN_HIS_LAB\n\treturn\n')
    path = 'data/maps/Route101/scripts.inc'
    replace(path, 'Route101_EventScript_BirchsBag::\n', 'Route101_EventScript_BirchsBag::\n\tspecial JourneyBirthCheckPartySpace\n\tgoto_if_eq VAR_RESULT, FALSE, JourneyBirth_TeamFull\n')
    path = 'src/battle_setup.c'
    replace(path, '#include "global.h"', '#include "global.h"\n#include "journey_birth.h"')
    replace(path, '    ScriptGiveMon(starterMon, 5, ITEM_NONE);', '    ScriptGiveMon(starterMon, 5, ITEM_NONE);\n    JourneyBirthRecordHoennStarter();')
    # Use existing landings; never paint a truck platform over island walkways.
    layouts = {l['id']: l for l in json.loads(read('data/layouts/layouts.json'))['layouts']}
    by_id = {}
    for group in groups['group_order']:
        for name in groups[group]:
            path = f'data/maps/{name}/map.json'
            if path in expected or path in outputs:
                m = load(name); by_id[m['id']] = m
    arrivals = []
    for home in homes:
        original = load(home['house'])
        exit_warp = original['warp_events'][0]
        city = by_id[exit_warp['dest_map']]
        sevii = 10 <= home['index'] <= 16
        if sevii:
            city = load(city['name'].replace('_Frlg', '_Harbor_Frlg'))
        layout = layouts[city['layout']]
        raw = read(layout['blockdata_filepath'])
        tiles = struct.unpack('<' + 'H' * (len(raw) // 2), raw)
        door = dict(x=8, y=4) if sevii else city['warp_events'][int(exit_warp['dest_warp_id'])]
        occupied = {(o['x'], o['y']) for o in city['object_events']} | {(w['x'], w['y']) for w in city['warp_events']} | {(c['x'], c['y']) for c in city['coord_events']}
        candidates = []
        for y in range(2, layout['height'] - 3):
            for x in range(1, layout['width'] - 4):
                cells = [(x+a, y+b) for a in range(4) for b in range(3)]
                values = [tiles[yy*layout['width'] + xx] for xx, yy in cells]
                if any(t & 0xC00 or t >> 12 < 2 for t in values) or any(p in occupied for p in cells): continue
                candidates.append((abs(x+1-door['x']) + abs(y+2-door['y']), x+1, y+2))
        boat = 10 <= home['index'] <= 16 or home['city'] in ['Dewford', 'Mossdeep', 'Sootopolis', 'Pacifidlog'] or not candidates
        if boat:
            # The doorway landing belongs to the selected residence's walkable bank.
            x, y = door['x'], door['y'] + 1
            assert not tiles[y * layout['width'] + x] & 0xC00, (city['name'], x, y)
            water = [(abs(xx-x)+abs(yy-y), xx, yy) for yy in range(layout['height']) for xx in range(layout['width'])
                     if tiles[yy*layout['width']+xx] >> 12 in (0, 1) and not tiles[yy*layout['width']+xx] & 0xC00]
            assert water, city['name']
            distance, sprite_x, sprite_y = min(water)
            if not sevii:
                # Find a shore on the same walking component as the house.
                # In Sootopolis this avoids disembarking on the opposite bank.
                blocking = {(o['x'], o['y']) for o in city['object_events']}
                queue = deque([(x, y, 0)])
                seen, shore = {(x, y)}, []
                water_cells = {(xx, yy) for _, xx, yy in water}
                while queue:
                    xx, yy, steps = queue.popleft()
                    for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                        nx, ny = xx+dx, yy+dy
                        if (nx, ny) in water_cells and (xx, yy) not in occupied:
                            shore.append((steps, xx, yy, nx, ny))
                        if not (0 <= nx < layout['width'] and 0 <= ny < layout['height']): continue
                        tile = tiles[ny*layout['width']+nx]
                        if (nx,ny) not in seen and tile >> 12 >= 2 and not tile & 0xC00:
                            seen.add((nx,ny)); queue.append((nx,ny,steps+1))
                assert shore, ('No reachable shore', city['name'])
                distance, x, y, sprite_x, sprite_y = min(shore)
            # A persistent captain provides an exit even when the chosen starter cannot Surf.
            dry = [(abs(xx-x)+abs(yy-y), xx, yy) for yy in range(layout['height']) for xx in range(layout['width']) if (xx, yy) not in occupied and (xx, yy) != (x, y) and tiles[yy*layout['width']+xx] >> 12 >= 2 and not tiles[yy*layout['width']+xx] & 0xC00]
            _, captain_x, captain_y = min(dry)
            npc = copy.deepcopy(living['object_events'][0])
            npc.update(local_id='LOCALID_JOURNEY_BIRTH_CAPTAIN_' + str(home['index']), graphics_id='OBJ_EVENT_GFX_SAILOR',
                       x=captain_x, y=captain_y, elevation=tiles[captain_y*layout['width']+captain_x] >> 12,
                       movement_type='MOVEMENT_TYPE_FACE_LEFT', script='JourneyBirth_Captain', flag='0')
            if not sevii: city['object_events'].append(npc)
            stage(f'data/maps/{city["name"]}/map.json', json.dumps(city, indent=2) + '\n')
        else:
            distance, sprite_x, sprite_y = min(candidates)
            x, y = sprite_x + 1, sprite_y
        arrivals.append(dict(index=home['index'], city=home['city'], map=city['id'], map_name=city['name'],
            vehicle='boat' if boat else 'truck', truck_x=sprite_x, truck_y=sprite_y, landing_x=x, landing_y=y,
            door_x=door['x'], door_y=door['y'], distance=distance))
    stage('include/journey_birth_arrivals.h', 'static const struct JourneyBirthArrival sJourneyBirthArrivals[] = {\n' + ',\n'.join('{' + ', '.join([a['map'], str(a['truck_x']), str(a['truck_y']), str(a['landing_x']), str(a['landing_y']), 'TRUE' if a['vehicle'] == 'boat' else 'FALSE']) + '}' for a in arrivals) + '\n};\n')
    report = dict(status='thirty_one_starting_cities_truck_and_boat_candidate', source_commit=PIN,
        homes=homes, arrivals=arrivals, excluded=config['excluded'], kanto_cities=16, hoenn_cities=15,
        truck_in_both_regions=True, selection_before_truck_motion=True, native_littleroot_intro_preserved=True,
        native_pallet_lab_starter_preserved=True, one_starter_per_region=True, regional_starter_level=5,
        requires_new_save=True, full_story_validated=False, input_sha256=inputs, original_sha256=originals,
        prepared_sha256={p: hashlib.sha256(v).hexdigest() for p, v in outputs.items()})
    for path, raw in outputs.items():
        (source / path).parent.mkdir(parents=True, exist_ok=True)
        (source / path).write_bytes(raw)
    marker.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    print(json.dumps(prepare(p.parse_args().source), indent=2))
