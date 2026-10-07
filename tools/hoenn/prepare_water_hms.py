"""Give the three water HMs early and convert the five terrestrial HMs to TMs."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from prepare_crossing import PIN
from prepare_free_access import LAYERS

TERRESTRIAL = ['CUT', 'FLY', 'STRENGTH', 'FLASH', 'ROCK_SMASH']
WATER = ['SURF', 'DIVE', 'WATERFALL']
LEGACY = ['CUT', 'FLY', 'SURF', 'STRENGTH', 'FLASH', 'ROCK_SMASH', 'WATERFALL', 'DIVE']


def terrestrial_dialogues(body):
    body = re.sub(r'(?m)^(\s*\.string .*?)\bHM\b', lambda m: m[1] + 'TM', body)
    body = body.replace('HIDDEN MACHINE', 'TECHNICAL MACHINE')
    texts = {
        'RustboroCity_CuttersHouse_Text_ExplainCut': ['TM51 teaches CUT.', 'It is a GRASS-type attack.', 'You can replace it with', 'another move normally.'],
        'SSAnne_CaptainsOffice_Text_ExplainCut': ['TM51 teaches CUT.', 'It is a GRASS-type attack.', 'Train your POKéMON well!'],
        'FuchsiaCity_WardensHouse_Text_ExplainStrength': ['TM53 teaches STRENGTH.', 'It is a powerful ROCK attack.', 'You can replace it with', 'another move normally.'],
        'RusturfTunnel_Text_ExplainStrength': ['TM53 teaches STRENGTH.', 'It is a powerful ROCK attack.', 'Thanks for your help!'],
        'MauvilleCity_House1_Text_ExplainRockSmash': ['TM55 teaches ROCK SMASH.', 'Its FIGHTING attack can', 'lower the foe\'s DEFENSE.'],
        'OneIsland_KindleRoad_EmberSpa_Text_ExplainHM06': ['TM55 teaches ROCK SMASH.', 'Its FIGHTING attack can', 'lower the foe\'s DEFENSE.'],
        'GraniteCave_1F_Text_ExplainFlash': ['TM54 teaches FLASH.', 'It lowers the foe\'s accuracy.', 'Good luck exploring!'],
        'Route2_EastBuilding_Text_ExplainHM05': ['TM54 teaches FLASH.', 'It lowers the foe\'s accuracy.', 'You can replace it normally.'],
    }
    for label, lines in texts.items():
        pattern = re.compile(re.escape(label) + r'(:{1,2})\n(?:\t\.string [^\n]*\n)+')
        def replace(match):
            return label + match[1] + '\n' + ''.join(
                '\t.string "' + line + ('$' if i == len(lines) - 1 else '\\n' if i % 2 == 0 else '\\p') + '"\n'
                for i, line in enumerate(lines))
        body = pattern.sub(replace, body)
    return body


def deduplicate_original_gifts(paths, read, stage):
    changed = []
    for path in sorted(paths):
        if not path.startswith('data/') or not path.endswith('.inc'): continue
        if path in ['data/scripts/journey_campaign_gates.inc', 'data/maps/MossdeepCity_StevensHouse/scripts.inc']: continue
        body = read(path).decode()
        pattern = re.compile(r'^\t(giveitem(?:_msg)?[^\n]*\bITEM_HM_(SURF|DIVE|WATERFALL)\b[^\n]*)$', re.M)
        def replace(match):
            label = 'Journey_OwnsWaterHM_' + hashlib.sha256((path + match[0]).encode()).hexdigest()[:16]
            return (f'\tcheckitem ITEM_HM_{match[2]}\n\tgoto_if_eq VAR_RESULT, TRUE, {label}\n'
                    + match[0] + '\n' + label + '::')
        updated, count = pattern.subn(replace, body)
        if count:
            stage(path, updated)
            changed.append(path)
    return changed


def prepare(source):
    source = Path(source)
    marker = source / '.journey-water-hms'
    if marker.exists():
        report = json.loads(marker.read_text())
        for path, digest in report['prepared_sha256'].items():
            assert hashlib.sha256((source / path).read_bytes()).hexdigest() == digest, path
        return report
    acquired = json.loads((source / '.source-acquired.json').read_text())
    assert acquired['commit'] == PIN
    expected = dict(acquired['sha256'])
    for layer in LAYERS + ['free-access', 'blue-gym', 'road-access', 'mach-bike', 'yellow-stairs', 'story-access', 'story-completion']:
        expected.update(json.loads((source / f'.journey-{layer}').read_text())['prepared_sha256'])
    inputs, originals, outputs = {}, {}, {}

    def read(path):
        if path in outputs: return outputs[path]
        raw = (source / path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected[path], path
        if path in acquired['sha256']: inputs[path] = acquired['sha256'][path]
        return raw

    def stage(path, body):
        if path not in originals: originals[path] = hashlib.sha256(read(path)).hexdigest()
        outputs[path] = body.encode()

    path = 'include/constants/tms_hms.h'
    body = read(path).decode()
    body = body.replace('    F(OVERHEAT)\n', '    F(OVERHEAT) \\\n' + ' \\\n'.join('    F(' + n + ')' for n in TERRESTRIAL) + '\n')
    body, count = re.subn(r'#define FOREACH_HM\(F\).*?(?=\n#define FOREACH_TMHM)',
                         '#define FOREACH_HM(F) \\\n' + ' \\\n'.join('    F(' + n + ')' for n in WATER) + '\n',
                         body, flags=re.S)
    assert count == 1
    stage(path, body)
    replacements = {f'ITEM_HM_{n}': f'ITEM_TM_{n}' for n in TERRESTRIAL}
    replacements.update({f'ITEM_HM{i:02}': f'ITEM_{"TM" if n in TERRESTRIAL else "HM"}_{n}'
                         for i, n in enumerate(LEGACY, 1)})
    pattern = re.compile(r'\b(' + '|'.join(replacements) + r')\b')
    changed_scripts = []
    # Rewrite every original recipient by move name, before renumbering HMs.
    # Reserved item IDs stay stable; old saves are not supported by this branch.
    for path in sorted(acquired['sha256']):
        if not path.startswith(('data/', 'src/')) or not path.endswith(('.c', '.h', '.inc')): continue
        raw = (source / path).read_bytes()
        if not pattern.search(raw.decode()): continue
        body = read(path).decode()
        if path == 'src/data/items.h':
            for number in range(51, 56):
                body, count = re.subn(r'    \[ITEM_TM' + str(number) + r'\] =\n    \{.*?\n    \},\n', '', body, flags=re.S)
                assert count == 1, number
        body = pattern.sub(lambda m: replacements[m[0]], body)
        if path == 'src/data/items.h':
            for number, name in enumerate(TERRESTRIAL, 51):
                stanza = re.search(r'    \[ITEM_TM_' + name + r'\] =\n    \{.*?\n    \},', body, re.S)
                assert stanza
                updated = re.sub(r'ITEM_NAME\("HM\d+"\)', f'ITEM_NAME("TM{number}")', stanza[0])
                updated = updated.replace('.importance = 1,', '.importance = I_REUSABLE_TMS,')
                body = body[:stanza.start()] + updated + body[stanza.end():]
            for number, name in enumerate(WATER[:3], 1):
                stanza = re.search(r'    \[ITEM_HM_' + name + r'\] =\n    \{.*?\n    \},', body, re.S)
                assert stanza
                updated = re.sub(r'ITEM_NAME\("HM\d+"\)', f'ITEM_NAME("HM{number:02}")', stanza[0])
                body = body[:stanza.start()] + updated + body[stanza.end():]
        else:
            for number, name in enumerate(LEGACY, 1):
                new_number = 51 + TERRESTRIAL.index(name) if name in TERRESTRIAL else WATER.index(name) + 1
                new_text = f'TM{new_number}' if name in TERRESTRIAL else f'HM{new_number:02}'
                body = re.sub(r'(?m)^(\s*\.string .*?)\bHM' + f'{number:02}' + r'\b',
                              lambda m: m[1] + new_text, body)
            terrestrial_tokens = [f'ITEM_HM_{n}' for n in TERRESTRIAL] + [f'ITEM_HM{i:02}' for i, n in enumerate(LEGACY, 1) if n in TERRESTRIAL]
            if any(token in read(path).decode() for token in terrestrial_tokens):
                body = terrestrial_dialogues(body)
            changed_scripts.append(path)
        stage(path, body)
    water_tokens = [b'ITEM_HM_' + n.encode() for n in WATER] + [b'ITEM_HM03', b'ITEM_HM07', b'ITEM_HM08']
    gift_candidates = [p for p in acquired['sha256'] if p.startswith('data/') and p.endswith('.inc')
                       and any(token in outputs.get(p, (source / p).read_bytes()) for token in water_tokens)]
    deduplicated = deduplicate_original_gifts(gift_candidates, read, stage)
    path = 'test/bag.c'
    body = read(path).decode()
    for old, new in [('ITEM_HM07', 'ITEM_HM_WATERFALL'), ('ITEM_HM05', 'ITEM_HM_DIVE'), ('ITEM_HM02', 'ITEM_HM_SURF')]:
        body = body.replace(old, new)
    stage(path, body)
    path = 'src/data/moves_info.h'
    body = read(path).decode()
    for name, kind in [('CUT', 'GRASS'), ('STRENGTH', 'ROCK')]:
        stanza = re.search(r'    \[MOVE_' + name + r'\] =.*?(?=    \[MOVE_|\Z)', body, re.S)
        assert stanza and stanza[0].count('.type = TYPE_NORMAL,') == 1
        updated = stanza[0].replace('.type = TYPE_NORMAL,', '.type = TYPE_' + kind + ',')
        body = body[:stanza.start()] + updated + body[stanza.end():]
    stage(path, body)
    path = 'src/field_move.c'
    body = read(path).decode()
    body, count = re.subn(r'(static bool32 IsFieldMoveUnlocked_Dive\(void\)\n\{)\n.*?\n\}',
                         r'\1\n    return TRUE;\n}', body, flags=re.S)
    assert count == 1
    stage(path, body)
    path = 'include/constants/flags.h'
    body = read(path).decode()
    assert '0x1ABD' not in body and '0x1abd' not in body
    stage(path, body.replace('#define JOURNEY_FLAGS_END', '#define FLAG_JOURNEY_WATER_HMS_GIVEN 0x1ABD\n#define JOURNEY_FLAGS_END'))
    path = 'data/scripts/journey_campaign_gates.inc'
    gift = '''
Journey_WaterHMFamilyGift::
\tgoto_if_set FLAG_JOURNEY_WATER_HMS_GIVEN, Journey_WaterHMFamilyGift_Return
\tmsgbox Journey_WaterHMFamilyGift_Text, MSGBOX_DEFAULT
'''
    for i, name in enumerate(WATER):
        gift += f'''Journey_WaterHMFamilyGift_{name}::
\tcheckitem ITEM_HM_{name}
\tgoto_if_eq VAR_RESULT, TRUE, Journey_WaterHMFamilyGift_{WATER[i + 1] if i + 1 < len(WATER) else 'Complete'}
\tcheckitemspace ITEM_HM_{name}
\tgoto_if_eq VAR_RESULT, FALSE, Journey_WaterHMFamilyGift_BagFull
\tgiveitem ITEM_HM_{name}
\tgoto_if_eq VAR_RESULT, FALSE, Journey_WaterHMFamilyGift_BagFull
'''
    gift += '''Journey_WaterHMFamilyGift_Complete::
\tsetflag FLAG_JOURNEY_WATER_HMS_GIVEN
Journey_WaterHMFamilyGift_Return::
\treturn
Journey_WaterHMFamilyGift_BagFull::
\tmsgbox Journey_WaterHMFamilyGift_BagFullText, MSGBOX_DEFAULT
\treturn
Journey_WaterHMFamilyGift_Text::
\t.string "Take SURF, DIVE and\\n"
\t.string "WATERFALL for your trip!\\p"
\t.string "Teach them to your POKéMON.\\n"
\t.string "Travel safely on the water!$"
Journey_WaterHMFamilyGift_BagFullText::
\t.string "Make room in your TM pocket.\\n"
\t.string "Then talk to me again!$"
'''
    stage(path, read(path).decode() + gift)
    for path, label in [('data/scripts/players_house.inc', 'PlayersHouse_1F_EventScript_Mom'),
                        ('data/maps/PalletTown_PlayersHouse_1F_Frlg/scripts.inc', 'PalletTown_PlayersHouse_1F_EventScript_Mom')]:
        body = read(path).decode()
        anchor = label + '::\n\tlock\n\tfaceplayer\n'
        assert body.count(anchor) == 1
        stage(path, body.replace(anchor, anchor + '\tcall Journey_WaterHMFamilyGift\n'))
    path = 'data/maps/MossdeepCity_StevensHouse/scripts.inc'
    body = read(path).decode()
    anchor = '\tgiveitem ITEM_HM_DIVE\n\tsetflag FLAG_RECEIVED_HM_DIVE'
    assert body.count(anchor) == 1
    stage(path, body.replace(anchor, '''\tcheckitem ITEM_HM_DIVE
\tgoto_if_eq VAR_RESULT, TRUE, Journey_StevenAlreadyHasDive
\tgiveitem ITEM_HM_DIVE
Journey_StevenAlreadyHasDive::
\tsetflag FLAG_RECEIVED_HM_DIVE'''))
    for path, raw in outputs.items(): (source / path).write_bytes(raw)
    report = dict(status='three_water_hms_and_terrestrial_tms_candidate', source_commit=PIN,
                  hms=WATER, new_tms={name: 51 + i for i, name in enumerate(TERRESTRIAL)},
                  move_types=dict(CUT='GRASS', STRENGTH='ROCK'), early_family_gift=True,
                  gift_flag=0x1ABD, gift_partial_bag_retry=True, original_mother_events_preserved=True,
                  dive_without_badges=True, whirlpool_is_not_hm=True, whirlpool_terrain_not_added=True,
                  original_water_gifts_do_not_duplicate=deduplicated,
                  changed_original_gifts=changed_scripts, requires_new_save=True, full_story_validated=False,
                  input_sha256=inputs, original_sha256=originals,
                  prepared_sha256={p: hashlib.sha256(v).hexdigest() for p, v in outputs.items()})
    marker.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source), indent=2))
