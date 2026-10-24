"""Separate the eighteen-badge qualification from the Galactic chapter at 22.

The physical Route 22/23 checkpoints and both League doors share the same
qualification. Regional gym missions, badge awards and Galactic encounters
retain their existing logic outside these admission checks.
"""
import hashlib
import re


GALACTIC = 'src/journey_galactic.c'
EXTRA = 'src/journey_extra_gyms.c'
CHAPTER = 'data/scripts/journey_galactic.inc'
ROUTE = 'data/scripts/route23.inc'
INDIGO = 'data/maps/IndigoPlateau_PokemonCenter_1F_Frlg/scripts.inc'
EVER_GRANDE = 'data/maps/EverGrandeCity_PokemonLeague_1F/scripts.inc'
GYMS = 'data/maps/JourneyExtraGyms.inc'
PATHS = (GALACTIC, EXTRA, CHAPTER, ROUTE, INDIGO, EVER_GRANDE, GYMS)

LEAGUE_TEXT = (
    '\t.string "Both LEAGUES need 18 BADGES\\n"\n'
    '\t.string "and a FRONTIER QUALIFIER win.\\p"\n'
    '\t.string "Meet your rivals outside the\\n"\n'
    '\t.string "BATTLE FRONTIER reception.$"\n'
)


def _replace(text, before, after, path, count=1):
    """Accept only the reviewed parent or this exact already-staged output."""
    if before not in text:
        assert text.count(after) == count, (path, 'Missing reviewed gate anchor', before[:100])
        return text
    assert text.count(before) == count, (path, 'Ambiguous gate anchor', before[:100])
    return text.replace(before, after)


def _block(text, label):
    match = re.search(r'^' + re.escape(label) + r'::?\n', text, re.M)
    assert match is not None, ('Missing script label', label)
    following = re.search(r'^[A-Za-z_][A-Za-z_0-9]*::?\n', text[match.end():], re.M)
    end = match.end() + following.start() if following else len(text)
    return match, end


def _set_block(text, label, body):
    match, end = _block(text, label)
    return text[:match.end()] + body.rstrip() + '\n\n' + text[end:]


def _include_qualifier(text, path):
    include = '#include "journey_badge_qualifier.h"'
    if include not in text:
        text = _replace(text, '#include "global.h"', '#include "global.h"\n' + include, path)
    assert text.count(include) == 1, path
    return text


def repair(layer):
    from badge_story_layer import read

    before = {path: read(layer, path).decode() for path in PATHS}
    output = dict(before)

    text = _include_qualifier(output[GALACTIC], GALACTIC)
    text = _replace(text,
        'bool32 JourneyGalacticLeagueReady(void) { return JourneyTotalBadgeCount()==24 && JourneyCrossoverComplete() && VarGet(VAR_JOURNEY_GALACTIC_STATE)>=7 && JourneyPendingCampaignEvent(TRUE)==0 && JourneyPendingCampaignEvent(FALSE)==0; }',
        'bool32 JourneyGalacticLeagueReady(void) { return JourneyTotalBadgeCount() >= 18 && JourneyQualifierWon(); }',
        GALACTIC)
    text = _replace(text,
        'void JourneyGalacticAvailable(void) { gSpecialVar_Result=JourneyGymBadgeCount(TRUE)==8 && JourneyGymBadgeCount(FALSE)==8; }',
        'void JourneyGalacticAvailable(void) { gSpecialVar_Result = JourneyTotalBadgeCount() >= 22; }',
        GALACTIC)
    text = _replace(text,
        'if(script==gruntScripts[i])return JourneyGymBadgeCount(TRUE)==8 && JourneyGymBadgeCount(FALSE)==8 && state<7;',
        'if(script==gruntScripts[i])return JourneyTotalBadgeCount() >= 22 && state<7;',
        GALACTIC)
    assert not re.search(r'JourneyGymBadgeCount\((?:TRUE|FALSE)\)\s*==\s*8', text), GALACTIC
    output[GALACTIC] = text

    text = _include_qualifier(output[EXTRA], EXTRA)
    output[EXTRA] = _replace(text,
        'void JourneyExtraLeagueBadges(void) { gSpecialVar_Result = JourneyTotalBadgeCount() == 24; }',
        'void JourneyExtraLeagueBadges(void) { gSpecialVar_Result = JourneyTotalBadgeCount() >= 18 && JourneyQualifierWon(); }',
        EXTRA)

    # Indigo's old regional checklist ran before the shared C permission.
    text = output[INDIGO]
    match, end = _block(text, 'IndigoPlateau_Journey_CheckBadges')
    old = text[match.end():end]
    final = '\tspecial JourneyKantoLeaguePermission\n\treturn\n\n'
    assert old == final or len(re.findall(r'goto_if_unset FLAG_KANTO_BADGE0[1-8]_GET,', old)) == 8, INDIGO
    text = _set_block(text, 'IndigoPlateau_Journey_CheckBadges', final)
    output[INDIGO] = _set_block(text, 'IndigoPlateau_Journey_TextNeedKantoBadges', LEAGUE_TEXT)

    # Ever Grande repeated its eight regional checks after C had admitted us.
    text = output[EVER_GRANDE]
    checks = ''.join('\tgoto_if_unset FLAG_BADGE0' + str(i) + '_GET, EverGrandeCity_PokemonLeague_1F_EventScript_NotAllBadges\n' for i in range(1, 9))
    if checks in text:
        assert text.count(checks) == 1, EVER_GRANDE
        text = text.replace(checks, '')
    assert not re.search(r'goto_if_unset FLAG_BADGE0[1-8]_GET,', text), EVER_GRANDE
    text = text.replace('@ Journey: all eight regional badges are required, regardless of gym order.\n@ Its assumed the player has the remaining badges',
                        '@ Journey: qualification admits either League with eighteen total badges.')
    text = _set_block(text, 'EverGrandeCity_PokemonLeague_1F_Text_MustHaveAllGymBadges',
        '\t.string "Your 18 BADGES and victory in\\n"\n'
        '\t.string "the FRONTIER QUALIFIER have\\p"\n'
        '\t.string "qualified you for this LEAGUE.\\n"\n'
        '\t.string "We recognize your achievement!$"\n')
    text = _set_block(text, 'EverGrandeCity_PokemonLeague_1F_Text_HaventObtainedAllBadges', LEAGUE_TEXT)
    output[EVER_GRANDE] = _set_block(text, 'Journey_LeagueSixteenBadgeText', LEAGUE_TEXT)

    # Badge checks may still allow ordinary exploration before qualification.
    # Winning the event must also permit all eight physical checkpoints, even
    # when the eighteen badges include extras rather than every Kanto badge.
    text = output[ROUTE]
    for label, target in [
        ('Route22_NorthEntrance_EventScript_BadgeGuard', 'JourneyBadgeStory_Route23Qualified'),
        ('Route23_EventScript_BadgeGuard', 'JourneyBadgeStory_Route23Qualified'),
        ('Route23_EventScript_BadgeGuardTrigger', 'JourneyBadgeStory_Route23QualifiedTrigger'),
    ]:
        match, end = _block(text, label)
        body = text[match.end():end]
        hook = '\tspecial JourneyKantoLeaguePermission\n\tgoto_if_eq VAR_RESULT, TRUE, ' + target + '\n'
        if hook not in body:
            body = hook + body
            text = _set_block(text, label, body)
        else:
            assert body.count(hook) == 1, (ROUTE, label)
    if 'JourneyBadgeStory_Route23Qualified::' not in text:
        text += '''
JourneyBadgeStory_Route23Qualified::
\tsetvar VAR_MAP_SCENE_ROUTE23, 8
\tmsgbox JourneyBadgeStory_Route23QualifiedText, MSGBOX_DEFAULT
\trelease
\tend

JourneyBadgeStory_Route23QualifiedTrigger::
\tsetvar VAR_MAP_SCENE_ROUTE23, 8
\tmsgbox JourneyBadgeStory_Route23QualifiedText, MSGBOX_DEFAULT
\treleaseall
\tend

JourneyBadgeStory_Route23QualifiedText::
\t.string "Your FRONTIER QUALIFIER victory\\n"
\t.string "is recognized. Please go ahead!$"
'''
    output[ROUTE] = text

    text = output[CHAPTER]
    text = _set_block(text, 'JourneyGalactic_Text_Badges',
        '\t.string "The sealed compartment opens\\n"\n'
        '\t.string "to a trainer with 22 BADGES.\\p"\n'
        '\t.string "Earn more BADGES, then return\\n"\n'
        '\t.string "to investigate TEAM GALACTIC.$"\n')
    text = _set_block(text, 'JourneyGalactic_LeagueDenied',
        '\tmsgbox JourneyBadgeStory_LeagueRequiredText, MSGBOX_DEFAULT\n'
        '\treleaseall\n\tend\n')
    if 'JourneyBadgeStory_LeagueRequiredText::' not in text:
        text += '\nJourneyBadgeStory_LeagueRequiredText::\n' + LEAGUE_TEXT
    text = _replace(text,
        '\t.string "Both LEAGUES can now admit you.\\p"',
        '\t.string "The three captives are free.\\p"', CHAPTER)
    text = _replace(text,
        '\t.string "Stop TEAM GALACTIC before entry.$"',
        '\t.string "TEAM GALACTIC awaits at 22 BADGES.$"', CHAPTER)
    text = _replace(text,
        '\t.string "also need to be completed.\\p"',
        '\t.string "can still be completed.\\p"', CHAPTER)
    output[CHAPTER] = text

    text = output[GYMS]
    text = _replace(text,
        '\t.string "All 24 are needed for the LEAGUES!$"',
        '\t.string "The QUALIFIER opens at 18 BADGES!$"', GYMS, count=8)
    text = _replace(text,
        '\t.string "Win its BADGE for the 24-BADGE\\n"\n\t.string "KANTO and HOENN LEAGUE challenge!$"',
        '\t.string "Earn 18 BADGES and win the\\n"\n\t.string "QUALIFIER to enter both LEAGUES!$"', GYMS, count=8)
    output[GYMS] = text

    for path, text in output.items():
        layer.stage(path, text)
    return {
        'league_minimum_total_badges': 18,
        'both_leagues_require_qualifier_victory': True,
        'galactic_minimum_total_badges': 22,
        'galactic_crossover_prerequisites_preserved': True,
        'galactic_capture_locks_and_state_transitions_preserved': True,
        'regional_gym_mission_gates_and_badge_banks_unchanged': True,
        'all_eight_route23_checkpoint_conversations_and_triggers_recognize_qualification': True,
        'no_source_layouts_objects_warps_or_connections_changed': True,
        'native_validation_pending': True,
        'changed_files': list(PATHS),
        'before_sha256': {path: hashlib.sha256(text.encode()).hexdigest() for path, text in before.items()},
        'after_sha256': {path: hashlib.sha256(text.encode()).hexdigest() for path, text in output.items()},
    }
