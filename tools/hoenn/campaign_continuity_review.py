"""Keep the required Weather Institute actor on her actual campaign checkpoint.

The pending-event selector returns 15 for the Institute. Its actor visibility
was left at 14, the later Rayquaza crisis, so the required boss never spawned.
Use shared names for these two IDs without changing save values or scripts.
"""
import hashlib

from badge_story_layer import read

HEADER = 'include/journey_campaign_gates.h'
GATES = 'src/journey_campaign_gates.c'
ACTORS = 'src/journey_story_continuity.c'
EVENTS = '''
// Stable script/save checkpoint IDs. Actor visibility and gym gates must agree.
enum JourneyCampaignEvent
{
    JOURNEY_CAMPAIGN_EVENT_RAYQUAZA = 14,
    JOURNEY_CAMPAIGN_EVENT_WEATHER_INSTITUTE = 15,
};
'''
HEADER_ANCHOR = '#define GUARD_JOURNEY_CAMPAIGN_GATES_H\n'
WEATHER_OLD = '''        if (count >= 4 && !JourneyWeatherInstituteComplete())
            return 15;'''
WEATHER_NEW = WEATHER_OLD.replace('return 15;', 'return JOURNEY_CAMPAIGN_EVENT_WEATHER_INSTITUTE;')
CRISIS_OLD = '''        if (count >= 7 && RegionalFlag(FLAG_SYS_WEATHER_CTRL))
            return 14;'''
CRISIS_NEW = CRISIS_OLD.replace('return 14;', 'return JOURNEY_CAMPAIGN_EVENT_RAYQUAZA;')
SHELLY_OLD = 'if(script==Route119_WeatherInstitute_2F_EventScript_Shelly)return JourneyPendingCampaignEvent(FALSE)==14;'
SHELLY_NEW = SHELLY_OLD.replace('==14;', '==JOURNEY_CAMPAIGN_EVENT_WEATHER_INSTITUTE;')
COMPLETE_OLD = 'return VarGet(VAR_WEATHER_INSTITUTE_STATE) == 1\n'
COMPLETE_NEW = 'return VarGet(VAR_WEATHER_INSTITUTE_STATE) >= 1\n'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def repair(layer):
    before = {name: read(layer, name) for name in (HEADER, GATES, ACTORS)}
    header, gates, actors = (before[name].decode() for name in (HEADER, GATES, ACTORS))
    assert header.count(HEADER_ANCHOR) == 1 and EVENTS not in header
    assert 'enum JourneyCampaignEvent' not in header
    assert gates.count(WEATHER_OLD) == gates.count(CRISIS_OLD) == 1
    assert gates.count(COMPLETE_OLD) == 1
    assert actors.count(SHELLY_OLD) == 1 and SHELLY_NEW not in actors
    assert '#include "journey_campaign_gates.h"' in actors
    after = {
        HEADER: header.replace(HEADER_ANCHOR, HEADER_ANCHOR+EVENTS).encode(),
        GATES: gates.replace(WEATHER_OLD, WEATHER_NEW).replace(CRISIS_OLD, CRISIS_NEW).replace(COMPLETE_OLD, COMPLETE_NEW).encode(),
        ACTORS: actors.replace(SHELLY_OLD, SHELLY_NEW).encode(),
    }
    for name, raw in after.items():
        assert raw != before[name]
        layer.stage(name, raw)
    return dict(kind='campaign-weather-actor-continuity', changed_paths=sorted(after),
                before_sha256={name:sha(raw) for name,raw in before.items()},
                after_sha256={name:sha(raw) for name,raw in after.items()},
                map='Route119_WeatherInstitute_2F', actor_local_id=3, actor_tile=[4,6],
                script='Route119_WeatherInstitute_2F_EventScript_Shelly',
                old_visibility_event=14, corrected_visibility_event=15,
                weather_institute_badge_checkpoint=4,
                completion_retained_after_native_route119_transition_to_state2=True,
                campaign_checkpoint_numbers_scripts_flags_and_save_abi_unchanged=True,
                all_other_actor_visibility_conditions_unchanged=True,
                terrain_objects_battle_teams_and_rewards_unchanged=True,
                native_actor_battle_reward_gate_and_continue_proofs_required=True)
