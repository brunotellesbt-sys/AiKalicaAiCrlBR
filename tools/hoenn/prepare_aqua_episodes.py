"""Require the native Shelly and Matt episodes at Hoenn's fourth/sixth badges."""
import argparse
import hashlib
import json
from pathlib import Path
from prepare_crossing import PIN
from prepare_family import LAYERS_BEFORE


def prepare(source):
    source = Path(source)
    marker = source / '.journey-aqua-episodes'
    if marker.exists():
        report = json.loads(marker.read_text())
        for path, digest in report['prepared_sha256'].items():
            if hashlib.sha256((source / path).read_bytes()).hexdigest() != digest:
                raise ValueError('Modified Aqua episode output: ' + path)
        return report
    acquired = json.loads((source / '.source-acquired.json').read_text())
    if acquired['commit'] != PIN:
        raise ValueError('Unexpected source revision')
    expected = dict(acquired['sha256'])
    for layer in LAYERS_BEFORE + ['family', 'travel-rules', 'birth', 'wild', 'habitats',
                                 'sanctuaries', 'ecology', 'abilities', 'mega-art', 'story-aftermath',
                                 'league-access', 'league-completion', 'league-history',
                                 'league-display', 'family-postgame', 'pwt', 'frontier-travel', 'story-puzzles']:
        expected.update(json.loads((source / ('.journey-' + layer)).read_text())['prepared_sha256'])
    originals, inputs, outputs, preserved = {}, {}, {}, {}
    def read(path):
        raw = (source / path).read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected[path]:
            raise ValueError('Unreviewed Aqua episode input: ' + path)
        if path in acquired['sha256']: inputs[path] = acquired['sha256'][path]
        return raw.decode()
    path = 'src/journey_campaign_gates.c'
    body = read(path); originals[path] = expected[path]
    anchor = 'static bool32 JourneyMissionComplete('
    if body.count(anchor) != 1: raise ValueError('Ambiguous campaign helpers')
    body = body.replace(anchor, '''static bool32 JourneyWeatherInstituteComplete(void)
{
    return VarGet(VAR_WEATHER_INSTITUTE_STATE) == 1
        && RegionalFlag(TRAINER_FLAGS_START + TRAINER_SHELLY_WEATHER_INSTITUTE);
}

static bool32 JourneyAquaHideoutComplete(void)
{
    return RegionalFlag(FLAG_TEAM_AQUA_ESCAPED_IN_SUBMARINE)
        && RegionalFlag(TRAINER_FLAGS_START + TRAINER_MATT);
}

''' + anchor)
    old = '        if (count >= 5 && !RegionalFlag(FLAG_GROUDON_AWAKENED_MAGMA_HIDEOUT))'
    if body.count(old) != 1: raise ValueError('Missing Magma checkpoint')
    body = body.replace(old, '''        if (count >= 4 && !JourneyWeatherInstituteComplete())
            return 15;
''' + old)
    old = '        if (count >= 7 && !JourneySpaceCenterComplete())'
    if body.count(old) != 1: raise ValueError('Missing Space Center checkpoint')
    body = body.replace(old, '''        if (count >= 6 && !JourneyAquaHideoutComplete())
            return 16;
''' + old)
    old = '    return JourneyGymBadgeCount(FALSE) >= 7\n        && RegionalFlag(FLAG_HIDE_SAFFRON_ROCKETS)'
    if body.count(old) != 1: raise ValueError('Missing alliance permission')
    body = body.replace(old, '''    return JourneyGymBadgeCount(FALSE) >= 7
        && JourneyWeatherInstituteComplete()
        && JourneyAquaHideoutComplete()
        && RegionalFlag(FLAG_HIDE_SAFFRON_ROCKETS)''')
    old = '    if (JourneyGymBadgeCount(FALSE) < 7\n'
    if body.count(old) != 1: raise ValueError('Missing invasion starter')
    body = body.replace(old, old + '''        || !JourneyWeatherInstituteComplete()
        || !JourneyAquaHideoutComplete()
''')
    outputs[path] = body.encode()
    path = 'data/scripts/journey_campaign_gates.inc'
    body = read(path); originals[path] = expected[path]
    anchor = '\tgoto_if_eq VAR_RESULT, 14, Journey_GymGuide_Event14'
    if body.count(anchor) != 1: raise ValueError('Missing guide dispatch')
    body = body.replace(anchor, anchor + '\n\tgoto_if_eq VAR_RESULT, 15, Journey_GymGuide_Event15\n\tgoto_if_eq VAR_RESULT, 16, Journey_GymGuide_Event16')
    for event, lines in [
        (15, ['The GYM LEADER is busy', 'helping fight TEAM AQUA!',
              'Take ROUTE 119 to the', 'WEATHER INSTITUTE.',
              'Help the scientists and', 'defeat SHELLY on floor 2!']),
        (16, ['The GYM LEADER is busy', 'helping fight TEAM AQUA!',
              'Head to LILYCOVE and SURF', 'to the AQUA HIDEOUT.',
              'Defeat MATT on floor B2!', 'If its entrance is guarded,',
              'visit CAPT. STERN at the', 'harbor in SLATEPORT first.'])]:
        body += f'\nJourney_GymGuide_Event{event}::\n\tmsgbox Journey_GymGuide_Text{event}, MSGBOX_DEFAULT\n\trelease\n\tend\n\nJourney_GymGuide_Text{event}:\n'
        for i, line in enumerate(lines):
            suffix = '$' if i == len(lines) - 1 else '\\p' if i % 2 else '\\n'
            body += '\t.string "' + line + suffix + '"\n'
    outputs[path] = body.encode()
    for path in ['data/maps/Route119_WeatherInstitute_2F/scripts.inc',
                 'data/maps/AquaHideout_B2F/scripts.inc', 'data/maps/SlateportCity_Harbor/scripts.inc',
                 'data/maps/MtPyre_Summit/scripts.inc', 'data/maps/Route119/map.json',
                 'data/maps/LilycoveCity/scripts.inc', 'src/journey_gym_scaling.c',
                 'src/journey_special.c', 'src/journey_pwt.c', 'include/constants/flags.h']:
        read(path); preserved[path] = expected[path]
    report = dict(status='mandatory_native_aqua_episodes_candidate', source_commit=PIN,
                  events=[dict(event=15, boss='Shelly', map='Route119_WeatherInstitute_2F', badges=4),
                          dict(event=16, boss='Matt', map='AquaHideout_B2F', badges=6)],
                  only_unwon_gyms_blocked=True, guide_explains_team_and_location=True,
                  roads_unchanged=True, native_castform_gift_retained=True,
                  native_submarine_theft_escape_retained=True,
                  archie_and_space_center_require_both_episodes=True,
                  independent_kanto_badges_and_league_retained=True,
                  new_flags_allocated=False, save_layout_unchanged=True,
                  full_campaign_validated=False, input_sha256=inputs, original_sha256=originals,
                  preserved_native_sha256=preserved,
                  prepared_sha256={p: hashlib.sha256(raw).hexdigest() for p, raw in outputs.items()})
    for path, raw in outputs.items(): (source / path).write_bytes(raw)
    marker.write_text(json.dumps(report, indent=2) + '\n')
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    print(json.dumps(prepare(parser.parse_args().source), indent=2))
