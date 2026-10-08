"""Port the sixteen curated Kanto/Sevii starting homes to the native world."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
from prepare_crossing import PIN
from prepare_free_access import LAYERS

HERE = Path(__file__).resolve().parent
LAYERS_BEFORE = LAYERS + ['free-access', 'blue-gym', 'road-access', 'mach-bike',
    'yellow-stairs', 'story-access', 'story-completion', 'water-hms', 'ferry', 'rival']


def prepare(source):
    source = Path(source)
    marker = source / '.journey-family'
    if marker.exists():
        report = json.loads(marker.read_text())
        for path, digest in report['prepared_sha256'].items():
            assert hashlib.sha256((source / path).read_bytes()).hexdigest() == digest, path
        return report
    acquired = json.loads((source / '.source-acquired.json').read_text())
    assert acquired['commit'] == PIN
    expected = dict(acquired['sha256'])
    for layer in LAYERS_BEFORE:
        expected.update(json.loads((source / f'.journey-{layer}').read_text())['prepared_sha256'])
    inputs, originals, outputs = {}, {}, {}

    def read(path):
        if path in outputs: return outputs[path]
        raw = (source / path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected[path], path
        if path in acquired['sha256']: inputs[path] = acquired['sha256'][path]
        return raw

    def stage(path, body):
        if path in expected and path not in originals:
            originals[path] = hashlib.sha256(read(path)).hexdigest()
        elif path not in expected and (source / path).exists():
            assert (source / path).read_bytes() == body.encode(), path
        outputs[path] = body.encode()

    def replace(path, anchor, value):
        body = read(path).decode()
        assert body.count(anchor) == 1, (path, anchor)
        stage(path, body.replace(anchor, value))

    config = json.loads((HERE.parent / 'journey/homes.json').read_text())
    load = lambda name: json.loads(read(f'data/maps/{name}/map.json'))
    living = load('PalletTown_PlayersHouse_1F_Frlg')
    bedroom = load('PalletTown_PlayersHouse_2F_Frlg')
    groups = json.loads(read('data/maps/map_groups.json'))
    groups['group_order'] += ['JourneyFamilyBedrooms', 'JourneyFamilyLivingRooms']
    groups['JourneyFamilyBedrooms'] = []
    groups['JourneyFamilyLivingRooms'] = []
    homes, rows = [], []
    non_people = {'OBJ_EVENT_GFX_NIDORAN_M', 'OBJ_EVENT_GFX_CUBONE',
        'OBJ_EVENT_GFX_PIDGEY', 'OBJ_EVENT_GFX_SPEAROW', 'OBJ_EVENT_GFX_CLIPBOARD'}
    def female(o):
        return any(t in o['graphics_id'] for t in ['MOM', 'WOMAN', 'LASS', 'BEAUTY', 'COOLTRAINER_F', 'GIRL'])
    for city, choice in enumerate(config['cities']):
        assert len(choice['houses']) == 1
        name = choice['houses'][0] + '_Frlg'
        original = load(name)
        people = [o for o in original['object_events'] if o['graphics_id'] not in non_people]
        assert 1 <= len(people) <= 3
        mother = next((i for i, o in enumerate(people) if female(o)), 0)
        people.insert(0, people.pop(mother))
        roles = [1]
        for o in people[1:]:
            role = 4 if female(o) else 3 if any(t in o['graphics_id'] for t in ['BOY', 'YOUNGSTER']) or 2 in roles else 2
            roles.append(role)
        roles += [0] * (3 - len(roles))
        bname, lname = f'JourneyFamilyBedroom{city:02d}', f'JourneyFamilyLiving{city:02d}'
        bid, lid = f'MAP_JOURNEY_FAMILY_BEDROOM_{city:02d}', f'MAP_JOURNEY_FAMILY_LIVING_{city:02d}'
        if city == 0:
            bid, lid = bedroom['id'], living['id']
        rows.append('{' + ', '.join([original['id'], lid, bid, choice['heal'], str(len(people)), str(roles[1]), str(roles[2])]) + '}')
        homes.append(dict(index=city + 1, city=choice['name'], house=name, original_map=original['id'],
            living_map=lid, bedroom_map=bid, heal=choice['heal'], people=len(people), roles=roles[:len(people)],
            original_people=[o['graphics_id'] for o in people], original_sha256=hashlib.sha256(read(f'data/maps/{name}/map.json')).hexdigest()))
        if city == 0: continue
        out = copy.deepcopy(living)
        out.update(id=lid, name=lname, music=original['music'], region_map_section=original['region_map_section'])
        out['object_events'] = []
        graphics = {1: 'OBJ_EVENT_GFX_MOM_FRLG', 2: 'OBJ_EVENT_GFX_MAN', 3: 'OBJ_EVENT_GFX_LITTLE_BOY_FRLG', 4: 'OBJ_EVENT_GFX_LITTLE_GIRL_FRLG'}
        for person, role in enumerate(roles[:len(people)]):
            obj = copy.deepcopy(living['object_events'][0])
            obj.update(local_id=f'LOCALID_JOURNEY_FAMILY_{city}_{person + 1}', graphics_id=graphics[role], x=[8, 8, 3][person],
                y=[4, 6, 6][person], movement_type='MOVEMENT_TYPE_FACE_DOWN', script='Journey_Family')
            out['object_events'].append(obj)
        for gfx, x, y, script in [('OBJ_EVENT_GFX_PROF_OAK', 4, 4, 'Journey_Oak'),
                                ('OBJ_EVENT_GFX_JOURNEY_FAMILY_CASE', 6, 4, 'Journey_Case')]:
            obj = copy.deepcopy(living['object_events'][0])
            obj.update(local_id=f'LOCALID_JOURNEY_FAMILY_{city}_{len(out["object_events"]) + 1}', graphics_id=gfx, x=x, y=y, script=script,
                flag='FLAG_JOURNEY_FAMILY_HIDE_VISITOR', movement_type='MOVEMENT_TYPE_FACE_DOWN')
            out['object_events'].append(obj)
        exit_warp = next(w for w in original['warp_events'] if w['dest_map'] == choice['outside'])
        for w in out['warp_events']:
            if w['dest_map'] == 'MAP_PALLET_TOWN':
                w.update(dest_map=exit_warp['dest_map'], dest_warp_id=exit_warp['dest_warp_id'])
            else: w.update(dest_map=bid, dest_warp_id='0')
        out['coord_events'] = [dict(type='trigger', x=w['x'], y=w['y'], elevation=w['elevation'],
            var='VAR_JOURNEY_FAMILY_STAGE', var_value='1', script='Journey_NeedStarter')
            for w in out['warp_events'] if w['dest_map'] == exit_warp['dest_map']]
        stage(f'data/maps/{lname}/map.json', json.dumps(out, indent=2) + '\n')
        stage(f'data/maps/{lname}/scripts.inc', lname + '_MapScripts::\n\tmap_script MAP_SCRIPT_ON_TRANSITION, Journey_Living_Transition\n\t.byte 0\n')
        b = copy.deepcopy(bedroom)
        b.update(id=bid, name=bname, music=original['music'], region_map_section=original['region_map_section'])
        b['warp_events'][0].update(dest_map=original['id'], dest_warp_id='2')
        stage(f'data/maps/{bname}/map.json', json.dumps(b, indent=2) + '\n')
        stage(f'data/maps/{bname}/scripts.inc', bname + '_MapScripts::\n\t.byte 0\n')
        groups['JourneyFamilyBedrooms'].append(bname)
        groups['JourneyFamilyLivingRooms'].append(lname)
    stage('data/maps/map_groups.json', json.dumps(groups, indent=2) + '\n')
    stage('include/journey_family_homes.h', 'static const struct JourneyFamilyHome sJourneyFamilyHomes[] = {\n' + ',\n'.join(rows) + '\n};\n')
    for src, dest in [('family.c', 'src/journey_family.c'), ('family.h', 'include/journey_family.h'), ('family.inc', 'data/scripts/journey_family.inc')]:
        stage(dest, (HERE / src).read_text())
    path = 'data/event_scripts.s'
    body = read(path).decode() + '\n\t.include "data/scripts/journey_family.inc"\n'
    for n in groups['JourneyFamilyBedrooms'] + groups['JourneyFamilyLivingRooms']:
        body += f'\t.include "data/maps/{n}/scripts.inc"\n'
    stage(path, body)
    path = 'data/specials.inc'
    body = read(path).decode()
    for n in ['ChooseHome', 'WarpBedroom', 'SetupVisitors', 'Info', 'GiveGift', 'GiveStarter', 'VisitorIds', 'CanChooseCity']:
        body += '\n\tdef_special JourneyFamily' + n
    stage(path, body + '\n')
    replace('include/constants/vars.h', '#define VAR_UNUSED_0x40F7', '#define VAR_JOURNEY_FAMILY_HOME 0x40F7\n#define VAR_JOURNEY_FAMILY_GIFTS 0x40F8\n#define VAR_JOURNEY_FAMILY_STAGE 0x40F9\n#define VAR_JOURNEY_FAMILY_MENU_STATE 0x40FA\n#define VAR_UNUSED_0x40F7')
    replace('include/constants/flags.h', '#define JOURNEY_FLAGS_END', '#define FLAG_JOURNEY_FAMILY_STARTER_RECEIVED 0x1ABE\n#define FLAG_JOURNEY_FAMILY_HIDE_VISITOR 0x1ABF\n#define JOURNEY_FLAGS_END')
    replace('src/overworld.c', '#include "global.h"', '#include "global.h"\n#include "journey_family.h"')
    replace('src/overworld.c', '    return gMapGroups[mapGroup][mapNum];', '    const struct MapHeader *home = JourneyFamilyHomeHeader(mapGroup, mapNum);\n    if (home != NULL) return home;\n    return gMapGroups[mapGroup][mapNum];')
    replace('include/constants/script_menu.h', '    MULTI_JOURNEY_FERRY_ISLANDS,', '    MULTI_JOURNEY_FERRY_ISLANDS,\n    MULTI_JOURNEY_START_CITIES,\n    MULTI_JOURNEY_STARTERS,')
    menu = 'static const struct MenuAction sJourneyStartCities[] = {\n'
    menu += ''.join('    {COMPOUND_STRING("' + c.get('label', c['name']) + '")},\n' for c in config['cities']) + '};\n'
    menu += 'static const struct MenuAction sJourneyStarters[] = {\n    {COMPOUND_STRING("BULBASAUR")},\n    {COMPOUND_STRING("CHARMANDER")},\n    {COMPOUND_STRING("SQUIRTLE")},\n};\n'
    replace('src/data/script_menu.h', 'static const struct MultichoiceListStruct sMultichoiceLists[] =\n{', menu + '\nstatic const struct MultichoiceListStruct sMultichoiceLists[] =\n{\n    [MULTI_JOURNEY_START_CITIES] = MULTICHOICE(sJourneyStartCities),\n    [MULTI_JOURNEY_STARTERS] = MULTICHOICE(sJourneyStarters),')
    path = 'data/maps/PalletTown_PlayersHouse_2F_Frlg/scripts.inc'
    replace(path, '\t.byte 0\n', '\tmap_script MAP_SCRIPT_ON_FRAME_TABLE, Journey_FamilyCity_OnFrame\n\t.byte 0\n')
    stage(path, read(path).decode() + '\nJourney_FamilyCity_OnFrame::\n\tmap_script_2 VAR_JOURNEY_FAMILY_MENU_STATE, 0, Journey_ChooseCity\n\t.2byte 0\n')
    path = 'data/maps/PalletTown_PlayersHouse_1F_Frlg/scripts.inc'
    replace(path, 'PalletTown_PlayersHouse_1F_EventScript_Mom::\n', 'PalletTown_PlayersHouse_1F_EventScript_Mom::\n\tgoto_if_eq VAR_JOURNEY_FAMILY_HOME, 1, Journey_Family\n')
    replace(path, '\tcall Journey_WaterHMFamilyGift\n', '\tcall Journey_WaterHMFamilyGift\nPalletTown_PlayersHouse_1F_EventScript_MomOriginal::\n')
    replace('data/scripts/journey_campaign_gates.inc', 'Journey_WaterHMFamilyGift::\n', 'Journey_WaterHMFamilyGift::\n\tgoto_if_gt VAR_JOURNEY_FAMILY_HOME, 1, Journey_WaterHMFamilyGift_Return\n')
    # An original 16x16 suitcase: no donor graphics needed.
    pixels = [[0] * 16 for _ in range(16)]
    for y in range(5, 14):
        for x in range(1, 15): pixels[y][x] = 1 if x in (1, 14) or y in (5, 13) else 3
    for x, y in [(6, 3), (7, 3), (8, 3), (9, 3), (6, 4), (9, 4)]: pixels[y][x] = 1
    for y in range(6, 13): pixels[y][5] = pixels[y][10] = 2
    pixels[8][7] = pixels[8][8] = 2
    packed = [pixels[ty+y][tx+x] | pixels[ty+y][tx+x+1] << 4 for ty in (0, 8) for tx in (0, 8) for y in range(8) for x in range(0, 8, 2)]
    vals = [packed[i] | packed[i+1] << 8 for i in range(0, len(packed), 2)]
    path = 'src/data/object_events/object_event_graphics.h'
    stage(path, read(path).decode() + '\nconst u16 gObjectEventPic_JourneyFamilyCase[] = {' + ','.join(hex(v) for v in vals) + '};\n')
    path = 'src/data/object_events/object_event_pic_tables.h'
    stage(path, read(path).decode() + '\nstatic const struct SpriteFrameImage sPicTable_JourneyFamilyCase[] = {overworld_frame(gObjectEventPic_JourneyFamilyCase, 2, 2, 0)};\n')
    path = 'src/data/object_events/object_event_graphics_info.h'
    body = read(path).decode()
    info = re.search(r'const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_PokeBall = \{.*?\n\};', body, re.S)[0]
    for a, b in [('gObjectEventGraphicsInfo_PokeBall', 'gObjectEventGraphicsInfo_JourneyFamilyCase'),
        ('sPicTable_PokeBall', 'sPicTable_JourneyFamilyCase'), ('.size = 256', '.size = 128'),
        ('.height = 32', '.height = 16'), ('16x32', '16x16'), ('sAnimTable_Following', 'sAnimTable_Inanimate')]: info = info.replace(a, b)
    stage(path, body + '\n' + info + '\n')
    replace('include/constants/event_objects.h', '    NUM_OBJ_EVENT_GFX,', '    OBJ_EVENT_GFX_JOURNEY_FAMILY_CASE,\n    NUM_OBJ_EVENT_GFX,')
    path = 'src/data/object_events/object_event_graphics_info_pointers.h'
    replace(path, 'extern const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_BrendanNormal;', 'extern const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_JourneyFamilyCase;\nextern const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_BrendanNormal;')
    replace(path, '    [OBJ_EVENT_GFX_JOURNEY_GYM_BLUE]', '    [OBJ_EVENT_GFX_JOURNEY_FAMILY_CASE] = &gObjectEventGraphicsInfo_JourneyFamilyCase,\n    [OBJ_EVENT_GFX_JOURNEY_GYM_BLUE]')
    report = dict(status='sixteen_starting_cities_native_candidate', source_commit=PIN, homes=homes,
        excluded=config['excluded'], one_fixed_house_per_city=True, other_houses_preserved=True,
        water_gift_order=['SURF', 'DIVE', 'WATERFALL'], gift_partial_bag_retry=True,
        kanto_starters=['BULBASAUR', 'CHARMANDER', 'SQUIRTLE'], starter_level=5,
        pallet_lab_intro_preserved=True, native_hoenn_start_preserved=True, additional_hoenn_starts=False,
        original_mother_events_reused=True, requires_new_save=True, full_story_validated=False,
        input_sha256=inputs, original_sha256=originals,
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
