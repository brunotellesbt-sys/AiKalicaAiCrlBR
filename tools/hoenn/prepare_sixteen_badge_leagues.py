"""Require all sixteen badges at both Leagues; retain regional gym missions."""
import argparse
import hashlib
import json
from pathlib import Path
from prepare_crossing import PIN
from prepare_early_story_tools import PRECEDING

MESSAGE = ['Both LEAGUES require all', '16 GYM BADGES: eight from', 'KANTO and eight from HOENN.', 'Complete both GYM circuits!']
TEXT = '\n'.join('\t.string "' + s + ('\\n' if i % 2 == 0 else '\\p' if i == 1 else '$') + '"' for i,s in enumerate(MESSAGE)) + '\n'

def prepare(source):
    source = Path(source)
    marker = source / '.journey-sixteen-badge-leagues'
    if marker.exists():
        report = json.loads(marker.read_text())
        for path, digest in (report['prepared_sha256'] | report['preserved_native_sha256']).items():
            if hashlib.sha256((source / path).read_bytes()).hexdigest() != digest:
                raise ValueError('Modified sixteen badge League output: ' + path)
        return report
    acquired = json.loads((source / '.source-acquired.json').read_text())
    if acquired['commit'] != PIN: raise ValueError('Unexpected source revision')
    expected = dict(acquired['sha256'])
    for layer in PRECEDING + ['early-story-tools', 'mandatory-native-missions']:
        expected.update(json.loads((source / ('.journey-' + layer)).read_text())['prepared_sha256'])
    paths = ['src/journey_campaign_gates.c', 'data/maps/IndigoPlateau_PokemonCenter_1F_Frlg/scripts.inc',
        'data/maps/EverGrandeCity_PokemonLeague_1F/scripts.inc']
    preserve = ['data/scripts/journey_campaign_gates.inc', 'include/journey_team_missions.h',
        'src/journey_gym_scaling.c', 'src/journey_wild.c', 'src/journey_family.c',
        'data/maps/SilphCo_11F_Frlg/scripts.inc', 'data/maps/MossdeepCity_SpaceCenter_2F/scripts.inc',
        'data/maps/SeafloorCavern_Room9/scripts.inc']
    original, preserved = {}, {}
    for path in paths + preserve:
        digest = hashlib.sha256((source / path).read_bytes()).hexdigest()
        if digest != expected[path]: raise ValueError('Unreviewed League input: ' + path)
        (original if path in paths else preserved)[path] = digest
    outputs = {p: (source / p).read_text() for p in paths}
    edits = []
    def replace(path, before, after):
        if outputs[path].count(before) != 1: raise ValueError('Ambiguous League anchor: ' + path)
        outputs[path] = outputs[path].replace(before, after)
        edits.append(dict(path=path, before=before, after=after))
    c = paths[0]
    for name, region in [('JourneyKantoLeaguePermission', 'TRUE'), ('JourneyHoennLeaguePermission', 'FALSE')]:
        before = 'void ' + name + '(void)\n{\n    gSpecialVar_Result = JourneyGymBadgeCount(' + region + ') == 8\n        && JourneyPendingCampaignEvent(' + region + ') == 0;\n}'
        after = 'void ' + name + '(void)\n{\n    gSpecialVar_Result = JourneyGymBadgeCount(TRUE) == 8\n        && JourneyGymBadgeCount(FALSE) == 8;\n}'
        replace(c, before, after)
    kanto = paths[1]
    replace(kanto, '\tspecial JourneyRegionalStoryGuide\n\tgoto_if_ne VAR_RESULT, 0, Journey_GymGuide_Dispatch\n', '')
    before = '\t.string "The KANTO LEAGUE requires all\\n"\n\t.string "eight KANTO GYM BADGES.\\p"\n\t.string "HOENN BADGES count toward\\n"\n\t.string "the HOENN LEAGUE instead.$"\n'
    replace(kanto, before, TEXT)
    hoenn = paths[2]
    replace(hoenn, '\tspecial JourneyHoennLeaguePermission\n\tcall_if_eq VAR_RESULT, FALSE, EverGrandeCity_PokemonLeague_1F_EventScript_GuardsBlockDoor\n',
        '\tspecial JourneyHoennLeaguePermission\n\tcall_if_eq VAR_RESULT, FALSE, EverGrandeCity_PokemonLeague_1F_EventScript_GuardsBlockDoor\n\tcall_if_eq VAR_RESULT, TRUE, Journey_LeagueRestoreClearedEntrance\n')
    replace(hoenn, '\tgoto_if_eq VAR_RESULT, FALSE, Journey_HoennLeagueMissionDenied',
        '\tgoto_if_eq VAR_RESULT, FALSE, Journey_HoennLeagueSixteenBadgesDenied')
    before = 'Journey_HoennLeagueMissionDenied::\n\tspecial JourneyRegionalStoryGuide\n\tgoto_if_ne VAR_RESULT, 0, Journey_GymGuide_Dispatch\n\tgoto EverGrandeCity_PokemonLeague_1F_EventScript_NotAllBadges\n'
    replace(hoenn, before, 'Journey_HoennLeagueSixteenBadgesDenied::\n\tmsgbox Journey_LeagueSixteenBadgeText, MSGBOX_DEFAULT\n\treleaseall\n\tend\n\nJourney_LeagueSixteenBadgeText::\n' + TEXT)
    outputs[hoenn] += '\nJourney_LeagueRestoreClearedEntrance::\n\tgoto_if_unset FLAG_ENTERED_ELITE_FOUR, Journey_LeagueRestoreEntranceDone\n\tsetobjectxyperm LOCALID_LEAGUE_GUARD_1, 8, 2\n\tsetobjectxyperm LOCALID_LEAGUE_GUARD_2, 11, 2\nJourney_LeagueRestoreEntranceDone::\n\treturn\n'
    # Everything outside the two League permission functions is byte-identical.
    restored = outputs[c]
    for e in reversed(edits):
        if e['path'] == c: restored = restored.replace(e['after'], e['before'])
    assert hashlib.sha256(restored.encode()).hexdigest() == original[c]
    report = dict(status='sixteen_badge_leagues_candidate', source_commit=PIN,
        required_badges=dict(kanto=8, hoenn=8), both_leagues_require_sixteen=True,
        league_messages_are_not_gym_messages=True, mission_checks_remain_at_regional_gym_checkpoints=True,
        campaign_logic_outside_league_permissions_preserved=True, regional_champions_remain_separate=True,
        dialogue_lines=MESSAGE, original_sha256=original, preserved_native_sha256=preserved, edits=edits,
        prepared_sha256={p: hashlib.sha256(t.encode()).hexdigest() for p,t in outputs.items()}, full_campaign_validated=False)
    for path, text in outputs.items(): (source / path).write_text(text)
    marker.write_text(json.dumps(report, indent=2) + '\n')
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    print(json.dumps(prepare(parser.parse_args().source), indent=2))
