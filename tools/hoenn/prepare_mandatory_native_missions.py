"""Require original regional episodes without restoring roadblocks."""
import argparse
import hashlib
import json
from pathlib import Path
from prepare_crossing import PIN
from prepare_early_story_tools import PRECEDING

QUESTS = [
 dict(key='mt_moon', kanto=True, badges=1, event=17, trainers=['TRAINER_TEAM_ROCKET_GRUNT', 'TRAINER_TEAM_ROCKET_GRUNT_2', 'TRAINER_TEAM_ROCKET_GRUNT_3', 'TRAINER_TEAM_ROCKET_GRUNT_4', 'TRAINER_SUPER_NERD_MIGUEL'], flags=['FLAG_GOT_FOSSIL_FROM_MT_MOON'], variables=[]),
 dict(key='cerulean_rocket', kanto=True, badges=2, event=18, trainers=['TRAINER_TEAM_ROCKET_GRUNT_5', 'TRAINER_TEAM_ROCKET_GRUNT_6'], flags=['FLAG_GOT_TM28_FROM_ROCKET'], variables=[['VAR_MAP_SCENE_ROUTE24', 1]]),
 dict(key='fuji_rescue', kanto=True, badges=4, event=19, trainers=['TRAINER_TEAM_ROCKET_GRUNT_19', 'TRAINER_TEAM_ROCKET_GRUNT_20', 'TRAINER_TEAM_ROCKET_GRUNT_21'], flags=['FLAG_RESCUED_MR_FUJI'], variables=[['VAR_MAP_SCENE_POKEMON_TOWER_6F', 1]]),
 dict(key='petalburg_woods', kanto=False, badges=1, event=20, trainers=['TRAINER_GRUNT_PETALBURG_WOODS'], flags=[], variables=[['VAR_PETALBURG_WOODS_STATE', 1]]),
 dict(key='rusturf_recovery', kanto=False, badges=1, event=21, trainers=['TRAINER_GRUNT_RUSTURF_TUNNEL'], flags=['FLAG_RECOVERED_DEVON_GOODS'], variables=[]),
 dict(key='steven_letter', kanto=False, badges=2, event=23, trainers=[], flags=['FLAG_DELIVERED_STEVEN_LETTER'], variables=[]),
 dict(key='oceanic_museum', kanto=False, badges=2, event=22, trainers=['TRAINER_GRUNT_MUSEUM_1', 'TRAINER_GRUNT_MUSEUM_2'], flags=['FLAG_DELIVERED_DEVON_GOODS'], variables=[]),
]
HINTS = {
 17: ('TEAM ROCKET', ['Go to MT. MOON on ROUTE 4.', 'Clear the basement ROCKETS.', 'Help secure the fossils, too!']),
 18: ('TEAM ROCKET', ['Visit CERULEAN and ROUTE 24.', 'Recover the stolen TM and', 'stop the bridge recruiter!']),
 19: ('TEAM ROCKET', ['Go to LAVENDER via ROUTE 8.', 'Calm the ghost in the TOWER.', 'Clear floor 7 and save FUJI!']),
 20: ('TEAM AQUA', ['Go to PETALBURG WOODS,', 'on ROUTE 104.', 'Help the DEVON researcher!']),
 21: ('TEAM AQUA', ['Visit RUSTBORO, then take', 'ROUTE 116 to RUSTURF TUNNEL.', 'Rescue PEEKO and the package!']),
 22: ('TEAM AQUA', ['Go to SLATEPORT SHIPYARD,', 'then the OCEANIC MUSEUM.', 'Deliver the DEVON PARTS', 'and help STERN on floor 2!']),
 23: (None, ['Visit DEVON CORP in RUSTBORO.', 'Take the LETTER to STEVEN', 'in GRANITE CAVE, ROUTE 106.']),
}

EXTRAS = '''
static void JourneyStartDevonRecovery(void)
{
    // Start the theft after the first arbitrary Hoenn badge, not just Roxanne.
    if (JourneyGymBadgeCount(FALSE) >= 1
        && JourneyNativeCampaignEvent(FALSE, 1) != 20
        && VarGet(VAR_RUSTBORO_CITY_STATE) == 0)
        VarSet(VAR_RUSTBORO_CITY_STATE, 1);
}

void JourneyKantoLeaguePermission(void)
{
    gSpecialVar_Result = JourneyGymBadgeCount(TRUE) == 8
        && JourneyPendingCampaignEvent(TRUE) == 0;
}

void JourneyHoennLeaguePermission(void)
{
    gSpecialVar_Result = JourneyGymBadgeCount(FALSE) == 8
        && JourneyPendingCampaignEvent(FALSE) == 0;
}

void JourneyRegionalStoryGuide(void)
{
    gSpecialVar_Result = JourneyPendingCampaignEvent(isFrlg);
}

'''

def prepare(source):
    source = Path(source)
    marker = source / '.journey-mandatory-native-missions'
    if marker.exists():
        report = json.loads(marker.read_text())
        for path, digest in (report['prepared_sha256'] | report['preserved_native_sha256']).items():
            if hashlib.sha256((source / path).read_bytes()).hexdigest() != digest:
                raise ValueError('Modified mandatory mission output: ' + path)
        return report
    acquired = json.loads((source / '.source-acquired.json').read_text())
    if acquired['commit'] != PIN:
        raise ValueError('Unexpected source revision')
    expected = dict(acquired['sha256'])
    for layer in PRECEDING + ['early-story-tools']:
        expected.update(json.loads((source / ('.journey-' + layer)).read_text())['prepared_sha256'])
    paths = ['src/journey_campaign_gates.c', 'data/scripts/journey_campaign_gates.inc', 'data/specials.inc',
        'data/maps/IndigoPlateau_PokemonCenter_1F_Frlg/scripts.inc', 'data/maps/EverGrandeCity_PokemonLeague_1F/scripts.inc',
        'data/maps/RustboroCity_Gym/scripts.inc', 'data/maps/GraniteCave_StevensRoom/scripts.inc']
    preserved_paths = ['data/maps/MtMoon_B2F_Frlg/scripts.inc', 'data/maps/Route24_Frlg/scripts.inc',
        'data/maps/CeruleanCity_Frlg/scripts.inc', 'data/maps/PokemonTower_6F_Frlg/scripts.inc', 'data/maps/PokemonTower_7F_Frlg/scripts.inc',
        'data/maps/PetalburgWoods/scripts.inc', 'data/maps/RusturfTunnel/scripts.inc', 'data/maps/RustboroCity/scripts.inc',
        'data/maps/SlateportCity_OceanicMuseum_2F/scripts.inc',
        'src/journey_gym_scaling.c', 'src/journey_wild.c', 'src/journey_family.c']
    original, preserved = {}, {}
    for path in paths + preserved_paths:
        digest = hashlib.sha256((source / path).read_bytes()).hexdigest()
        if digest != expected[path]:
            raise ValueError('Unreviewed mission input: ' + path)
        (original if path in paths else preserved)[path] = digest
    outputs = {p: (source / p).read_text() for p in paths}
    edits = []
    def replace(path, before, after):
        if outputs[path].count(before) != 1:
            raise ValueError('Ambiguous mission anchor: ' + path)
        outputs[path] = outputs[path].replace(before, after)
        edits.append(dict(path=path, before=before, after=after))
    c = paths[0]
    body = 'static u32 JourneyNativeCampaignEvent(bool32 kanto, u32 count)\n{\n'
    for q in QUESTS:
        conditions = ['!RegionalFlag(TRAINER_FLAGS_START + ' + t + ')' for t in q['trainers']]
        conditions += ['!RegionalFlag(' + f + ')' for f in q['flags']]
        conditions += ['VarGet(' + v + ') < ' + str(value) for v, value in q['variables']]
        body += '    if (kanto == ' + ('TRUE' if q['kanto'] else 'FALSE') + ' && count >= ' + str(q['badges']) + '\n        && (' + '\n            || '.join(conditions) + '))\n        return ' + str(q['event']) + ';\n'
    body += '    return 0;\n}\n\n'
    replace(c, 'u32 JourneyPendingCampaignEvent(bool32 kanto)', body + 'u32 JourneyPendingCampaignEvent(bool32 kanto)')
    replace(c, '    u32 i, count = JourneyGymBadgeCount(kanto);\n',
        '    u32 i, count = JourneyGymBadgeCount(kanto);\n    u32 nativeEvent = JourneyNativeCampaignEvent(kanto, count);\n    if (nativeEvent && nativeEvent != 19) return nativeEvent;\n')
    replace(c, '    for (i = 0; i < ARRAY_COUNT(sJourneyTeamMissions); i++)\n        if (sJourneyTeamMissions[i].kanto == kanto\n            && count >=',
        '    if (nativeEvent) return nativeEvent;\n    for (i = 0; i < ARRAY_COUNT(sJourneyTeamMissions); i++)\n        if (sJourneyTeamMissions[i].kanto == kanto\n            && count >=')
    for name, kanto in [('JourneyCanChallengeSilph', True), ('JourneyCanStartArchieAlliance', False)]:
        region = 'TRUE' if kanto else 'FALSE'
        before = 'bool32 ' + name + '(void)\n{\n    return JourneyGymBadgeCount(' + region + ') >= ' + ('6' if kanto else '7')
        replace(c, before, before + '\n        && JourneyNativeCampaignEvent(' + region + ', 8) == 0')
    replace(c, 'void JourneyUpdateGymGate(void)', EXTRAS + 'void JourneyUpdateGymGate(void)')
    replace(c, '    if (!isFrlg)\n        JourneyStartSpaceCenterInvasion();',
        '    if (!isFrlg)\n    {\n        JourneyStartDevonRecovery();\n        JourneyStartSpaceCenterInvasion();\n    }')
    script = paths[1]
    replace(script, '\tspecial JourneyExplainGymGate\n', '\tspecial JourneyExplainGymGate\nJourney_GymGuide_Dispatch::\n')
    checks = ''.join('\tgoto_if_eq VAR_RESULT, ' + str(q['event']) + ', Journey_GymGuide_Event' + str(q['event']) + '\n' for q in QUESTS)
    replace(script, '\tgoto_if_eq VAR_RESULT, 16, Journey_GymGuide_Event16\n', '\tgoto_if_eq VAR_RESULT, 16, Journey_GymGuide_Event16\n' + checks)
    new_text, addition = [], '\n'
    for event, (team, lines) in HINTS.items():
        text = ['The GYM LEADER is busy', 'helping fight ' + team + '!' if team else 'helping DEVON researchers.'] + lines
        new_text.extend(text)
        addition += 'Journey_GymGuide_Event' + str(event) + '::\n\tmsgbox Journey_GymGuide_Text' + str(event) + ', MSGBOX_DEFAULT\n\treleaseall\n\tend\n\nJourney_GymGuide_Text' + str(event) + '::\n'
        for i, line in enumerate(text):
            escape = '\\p' if i % 2 else '\\n'
            if i == len(text) - 1:
                escape = '$'
            addition += '\t.string "' + line + escape + '"\n'
        addition += '\n'
    outputs[script] += addition
    replace(paths[2], '\tdef_special JourneyFirstBadgeRewardPermission', '\tdef_special JourneyFirstBadgeRewardPermission\n\tdef_special JourneyKantoLeaguePermission\n\tdef_special JourneyHoennLeaguePermission\n\tdef_special JourneyRegionalStoryGuide')
    p = paths[3]
    replace(p, '\tsetvar VAR_RESULT, TRUE\n\treturn\n', '\tspecial JourneyKantoLeaguePermission\n\treturn\n')
    replace(p, 'IndigoPlateau_Journey_Denied::\n', 'IndigoPlateau_Journey_Denied::\n\tspecial JourneyRegionalStoryGuide\n\tgoto_if_ne VAR_RESULT, 0, Journey_GymGuide_Dispatch\n')
    p = paths[4]
    replace(p, '\tcall_if_unset FLAG_ENTERED_ELITE_FOUR, EverGrandeCity_PokemonLeague_1F_EventScript_GuardsBlockDoor',
        '\tspecial JourneyHoennLeaguePermission\n\tcall_if_eq VAR_RESULT, FALSE, EverGrandeCity_PokemonLeague_1F_EventScript_GuardsBlockDoor\n\tcall_if_unset FLAG_ENTERED_ELITE_FOUR, EverGrandeCity_PokemonLeague_1F_EventScript_GuardsBlockDoor')
    replace(p, 'EverGrandeCity_PokemonLeague_1F_EventScript_DoorGuard::\n\tlockall\n',
        'EverGrandeCity_PokemonLeague_1F_EventScript_DoorGuard::\n\tlockall\n\tspecial JourneyHoennLeaguePermission\n\tgoto_if_eq VAR_RESULT, FALSE, Journey_HoennLeagueMissionDenied\n')
    outputs[p] += '\nJourney_HoennLeagueMissionDenied::\n\tspecial JourneyRegionalStoryGuide\n\tgoto_if_ne VAR_RESULT, 0, Journey_GymGuide_Dispatch\n\tgoto EverGrandeCity_PokemonLeague_1F_EventScript_NotAllBadges\n'
    p = paths[5]
    replace(p, '\tsetvar VAR_RUSTBORO_CITY_STATE, 1', '\tcall_if_eq VAR_RUSTBORO_CITY_STATE, 0, Journey_RoxanneStartDevonRecovery')
    outputs[p] += '\nJourney_RoxanneStartDevonRecovery::\n\tsetvar VAR_RUSTBORO_CITY_STATE, 1\n\treturn\n'
    p = paths[6]
    replace(p, 'GraniteCave_StevensRoom_EventScript_Steven::\n\tlock\n\tfaceplayer\n',
        'GraniteCave_StevensRoom_EventScript_Steven::\n\tlock\n\tfaceplayer\n'
        '\tgoto_if_set FLAG_DELIVERED_STEVEN_LETTER, Journey_StevenLetterReady\n'
        '\tcheckitem ITEM_LETTER\n\tgoto_if_eq VAR_RESULT, FALSE, Journey_StevenLetterNeeded\n'
        'Journey_StevenLetterReady::\n')
    outputs[p] += '\nJourney_StevenLetterNeeded::\n\tmsgbox Journey_StevenLetterText, MSGBOX_DEFAULT\n\trelease\n\tend\n\nJourney_StevenLetterText::\n\t.string "Please bring the LETTER from\\n"\n\t.string "DEVON CORP in RUSTBORO.$"\n'
    new_text += ['Please bring the LETTER from', 'DEVON CORP in RUSTBORO.']
    report = dict(status='mandatory_native_missions_candidate', source_commit=PIN, quests=QUESTS, new_dialogue_lines=new_text,
        regional_leagues_require_story_completion=True, roads_not_closed=True, existing_boss_thresholds_preserved=True,
        devon_theft_after_first_arbitrary_hoenn_badge=True, late_roxanne_does_not_reset_devon=True,
        original_sha256=original, preserved_native_sha256=preserved, edits=edits,
        prepared_sha256={p: hashlib.sha256(t.encode()).hexdigest() for p, t in outputs.items()}, full_campaign_validated=False)
    for path, text in outputs.items():
        (source / path).write_text(text)
    marker.write_text(json.dumps(report, indent=2) + '\n')
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    print(json.dumps(prepare(parser.parse_args().source), indent=2))
