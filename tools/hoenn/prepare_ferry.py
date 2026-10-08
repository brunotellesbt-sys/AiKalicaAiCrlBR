"""Add an early, ticketed ferry without completing either region's story."""
import argparse
import hashlib
import json
from pathlib import Path

from prepare_crossing import PIN
from prepare_free_access import LAYERS

PORTS = [
    ('VermilionCity_Frlg', 'VERMILION', (24, 31), (23, 31)),
    ('SlateportCity_Harbor', 'SLATEPORT', (16, 13), (16, 14)),
] + [(f'{name}Island_Harbor_Frlg', f'{name.upper()} ISLAND', (9, 5), (8, 5))
     for name in ['One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven']]


def prepare(source):
    source = Path(source)
    marker = source / '.journey-ferry'
    if marker.exists():
        report = json.loads(marker.read_text())
        for path, digest in report['prepared_sha256'].items():
            assert hashlib.sha256((source / path).read_bytes()).hexdigest() == digest, path
        return report
    acquired = json.loads((source / '.source-acquired.json').read_text())
    assert acquired['commit'] == PIN
    expected = dict(acquired['sha256'])
    for layer in LAYERS + ['free-access', 'blue-gym', 'road-access', 'mach-bike',
                          'yellow-stairs', 'story-access', 'story-completion', 'water-hms']:
        expected.update(json.loads((source / f'.journey-{layer}').read_text())['prepared_sha256'])
    inputs, originals, outputs, changes = {}, {}, {}, []

    def read(path):
        raw = (source / path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected[path], path
        if path in acquired['sha256']: inputs[path] = acquired['sha256'][path]
        return raw

    def stage(path, body):
        originals[path] = hashlib.sha256(read(path)).hexdigest()
        outputs[path] = body.encode()

    path = 'include/constants/items.h'
    body = read(path).decode()
    anchor = '    ITEMS_COUNT,\n'
    assert body.count(anchor) == 1
    stage(path, body.replace(anchor, '    ITEM_JOURNEY_FERRY_TICKET = 875,\n' + anchor))
    path = 'src/data/items.h'
    body = read(path).decode()
    anchor = '    [ITEM_SS_TICKET] =\n'
    assert body.count(anchor) == 1
    stage(path, body.replace(anchor, r'''    [ITEM_JOURNEY_FERRY_TICKET] =
    {
        .name = ITEM_NAME("World Ticket"),
        .price = 0,
        .description = COMPOUND_STRING(
            "A reusable ferry ticket\n"
            "linking KANTO, HOENN\n"
            "and the SEVII ISLANDS."),
        .importance = 1,
        .pocket = POCKET_KEY_ITEMS,
        .type = ITEM_USE_BAG_MENU,
        .fieldUseFunc = ItemUseOutOfBattle_CannotUse,
        .iconPic = gItemIcon_SSTicket,
        .iconPalette = gItemIconPalette_SSTicket,
    },

''' + anchor))
    path = 'include/constants/script_menu.h'
    body = read(path).decode()
    anchor = '    MULTI_FLIGHTCALL_REGIONS,\n'
    assert body.count(anchor) == 1
    stage(path, body.replace(anchor, anchor + '    MULTI_JOURNEY_FERRY_REGIONS,\n    MULTI_JOURNEY_FERRY_ISLANDS,\n'))
    path = 'src/data/script_menu.h'
    body = read(path).decode()
    anchor = 'static const struct MultichoiceListStruct sMultichoiceLists[] =\n'
    assert body.count(anchor) == 1
    def menu(name, labels):
        return 'static const struct MenuAction ' + name + '[] =\n{\n' + ''.join(
            '    {COMPOUND_STRING("' + label + '")},\n' for label in labels) + '};\n\n'
    declarations = menu('sJourneyFerryRegions', ['VERMILION', 'SLATEPORT', 'SEVII ISLANDS', 'CANCEL'])
    declarations += menu('sJourneyFerryIslands', [p[1] for p in PORTS[2:]] + ['BACK'])
    body = body.replace(anchor, declarations + anchor)
    # Insert entries directly after the list's opening brace, independent of spacing.
    body = body.replace('sMultichoiceLists[] =\n{\n', 'sMultichoiceLists[] =\n{\n'
                        '    [MULTI_JOURNEY_FERRY_REGIONS] = MULTICHOICE(sJourneyFerryRegions),\n'
                        '    [MULTI_JOURNEY_FERRY_ISLANDS] = MULTICHOICE(sJourneyFerryIslands),\n')
    stage(path, body)
    scripts = []
    ports = []
    for index, (name, title, npc, arrival) in enumerate(PORTS):
        path = f'data/maps/{name}/map.json'
        before = json.loads(read(path))
        after = json.loads(json.dumps(before))
        assert all((o['x'], o['y']) != npc for o in before['object_events'])
        assert all((w['x'], w['y']) not in [npc, arrival] for w in before['warp_events'])
        label = f'Journey_FerryPort{index}'
        after['object_events'].append(dict(type='object', graphics_id='OBJ_EVENT_GFX_SAILOR_FRLG' if index != 1 else 'OBJ_EVENT_GFX_SAILOR',
            x=npc[0], y=npc[1], elevation=3, movement_type='MOVEMENT_TYPE_FACE_LEFT' if index != 1 else 'MOVEMENT_TYPE_FACE_DOWN',
            movement_range_x=0, movement_range_y=0, trainer_type='TRAINER_TYPE_NONE',
            trainer_sight_or_berry_tree_id='0', script=label, flag='0'))
        stage(path, json.dumps(after, indent=2) + '\n')
        changes.append(dict(map=name, before=before, after=after))
        ports.append(dict(map=name, title=title, npc=list(npc), arrival=list(arrival), script=label,
                          local_id=len(after['object_events']), map_constant=before['id']))
        scripts.append(f'{label}::\n\tsetvar VAR_0x8008, {index}\n\tgoto Journey_Ferry\n')
    script = '\n'.join(scripts) + '''
Journey_Ferry::
\tlock
\tfaceplayer
\tcheckitem ITEM_JOURNEY_FERRY_TICKET
\tgoto_if_eq VAR_RESULT, TRUE, Journey_Ferry_Menu
\tmsgbox Journey_Ferry_TicketText, MSGBOX_DEFAULT
\tcheckitemspace ITEM_JOURNEY_FERRY_TICKET
\tgoto_if_eq VAR_RESULT, FALSE, Journey_Ferry_Full
\tgiveitem ITEM_JOURNEY_FERRY_TICKET
\tgoto_if_eq VAR_RESULT, FALSE, Journey_Ferry_Full
Journey_Ferry_Menu::
\tmsgbox Journey_Ferry_WhereText, MSGBOX_DEFAULT
\tclosemessage
\tmultichoice 0, 0, MULTI_JOURNEY_FERRY_REGIONS, FALSE
\tswitch VAR_RESULT
\tcase 0, Journey_Ferry_Destination0
\tcase 1, Journey_Ferry_Destination1
\tcase 2, Journey_Ferry_Islands
\tgoto Journey_Ferry_Cancel
Journey_Ferry_Islands::
\tmultichoice 0, 0, MULTI_JOURNEY_FERRY_ISLANDS, FALSE
\tswitch VAR_RESULT
'''
    script += ''.join(f'\tcase {i}, Journey_Ferry_Destination{i + 2}\n' for i in range(7))
    script += '\tgoto Journey_Ferry_Menu\n'
    for index, port in enumerate(ports):
        x, y = port['arrival']
        script += f'''Journey_Ferry_Destination{index}::
\tgoto_if_eq VAR_0x8008, {index}, Journey_Ferry_AlreadyHere
\tmsgbox Journey_Ferry_BoardText, MSGBOX_DEFAULT
\tclosemessage
\twarp {port['map_constant']}, {x}, {y}
\twaitstate
\trelease
\tend
'''
    script += '''Journey_Ferry_Full::
\tmsgbox Journey_Ferry_FullText, MSGBOX_DEFAULT
\tgoto Journey_Ferry_Cancel
Journey_Ferry_AlreadyHere::
\tmsgbox Journey_Ferry_AlreadyHereText, MSGBOX_DEFAULT
Journey_Ferry_Cancel::
\trelease
\tend
Journey_Ferry_TicketText::
\t.string "Welcome to the WORLD FERRY!\\p"
\t.string "Take this free WORLD TICKET.\\n"
\t.string "Keep it for all your trips!$"
Journey_Ferry_WhereText::
\t.string "We sail to KANTO, HOENN\\n"
\t.string "and all seven SEVII ISLANDS.\\p"
\t.string "Where would you like to go?$"
Journey_Ferry_BoardText::
\t.string "Your ticket is valid.\\n"
\t.string "All aboard!$"
Journey_Ferry_FullText::
\t.string "Make room for the WORLD TICKET\\n"
\t.string "in your KEY ITEMS pocket.$"
Journey_Ferry_AlreadyHereText::
\t.string "You are already at this port.$"
'''
    path = 'data/scripts/journey_campaign_gates.inc'
    stage(path, read(path).decode() + '\n' + script)
    preserved = {p: hashlib.sha256(read(p)).hexdigest() for p in [
        f'data/maps/{name}/scripts.inc' for name, *_ in PORTS]}
    for path, raw in outputs.items(): (source / path).write_bytes(raw)
    report = dict(status='early_interregional_ferry_candidate', source_commit=PIN,
        ports=ports, ticket_item_id=875, reusable_ticket=True, ticket_free_at_each_port=True,
        no_badges_or_story_completion_required=True, event_changes=changes,
        native_port_scripts_unchanged=True, preserved_native_sha256=preserved,
        boat_interior_or_sailing_animation=False, requires_new_save=True,
        full_story_validated=False, input_sha256=inputs, original_sha256=originals,
        prepared_sha256={p: hashlib.sha256(v).hexdigest() for p, v in outputs.items()})
    marker.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source), indent=2))
