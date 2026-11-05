"""Require the actual Weather Institute battle, reward, gym entry and Continue."""
import hashlib
from pathlib import Path

from verify_sevii_integrated_piers_update import require_true,verify_captures


def verify(report,directory):
    directory=Path(directory)
    assert report['kind']=='game-continuity-campaign'
    require_true(report,['passed','compiled_rom','native_validation_performed',
        'initial_badges_prior_quests_other_trainers_devon_scope_party_and_travel_are_fixtures',
        'no_midtrip_player_coordinates_elevations_or_badge_writes',
        'shelly_trainer_flag_weather_state_and_castform_reward_are_native','battle_uses_ordinary_native_stats'])
    assert report['full_campaign_playthrough'] is report['balance_validated'] is False
    captures=verify_captures(report['captures'],directory)
    states=report['states']
    assert [s['label'] for s in states]==[
        '01-four-badges-weather-gate','02-fifth-gym-still-blocked','03-shelly-present-before-battle',
        '05-shelly-defeated-castform-received','06-fifth-gym-door-unlocked',
        '07-fifth-gym-entered-by-door','08-weather-institute-revisited']
    # The report names each observation independently; compare its copies too.
    rows=[report[k] for k in ('initial','blocked_gym','shelly_before','shelly_after','gym_ready','gym_entered','revisited')]
    assert len(states)==len(rows)==7 and states==rows
    for s in rows:
        assert s['hoenn_badges']==s['kanto_badges']==4
        assert s['elevation']==3 and s['surfing'] is False
        assert s['capture_file'] in captures
    before,after=report['shelly_before'],report['shelly_after']
    assert before['map']=='Route119_WeatherInstitute_2F' and before['tile']==[5,6]
    assert before['weather_state']==0 and before['pending_event']==15
    assert before['shelly_defeated'] is before['castform_received'] is False
    assert report['shelly_visibility_before']==1 and 0<=report['shelly_object_id_before']<16
    assert after['weather_state']==1 and after['pending_event']==0
    assert after['shelly_defeated'] is after['castform_received'] is True
    battle=report['native_battle']
    assert battle['trainer_id']==32 and battle['outcome']==1 and battle['attacks']>0 and battle['battle_frames']>0
    require_true(battle,['actual_adjacent_A_interaction','no_script_entry_fixture','no_battle_stats_or_outcome_writes'])
    assert report['gift_species']==[382,382,382,351] and report['party_count_after']==4
    for key in ('gym_ready','gym_entered','revisited'):
        s=report[key]
        assert s['weather_state']==2 and s['pending_event']==0 and s['shelly_defeated'] and s['castform_received']
    assert report['gym_entered']['map']=='FortreeCity_Gym' and report['gym_entered']['tile']==[15,23]
    assert report['shelly_object_id_on_revisit']==16
    assert report['walked_tiles']>300 and report['transitions'] and report['inputs']
    assert all(row['key'] in (0,1,2,4,8,16,32,64,128) and row['frames']>0 for row in report['inputs'])
    path=Path(report['battery_file']);assert path.name==str(path) and path.suffix=='.sav'
    raw=(directory/path).read_bytes();assert len(raw)==131072
    sha=hashlib.sha256(raw).hexdigest();assert sha==report['battery_sha256']
    assert report['battery_saves']==[dict(file=str(path),sha256=sha,bytes=131072)]
    cold=report['cold_continue'];assert cold['passed'] is True
    assert cold['rom_sha256']==report['rom_sha256'] and cold['bundled_save_sha256']==sha
    assert len(cold['runs'])==2 and [r['battery'] for r in cold['runs']]==[False,True]
    continued=cold['runs'][1]
    require_true(continued,['bundled_save_continue_to_field','shelly_defeated','castform_received',
        'no_duplicate_local_ids','controllers_only','no_game_memory_writes','no_callback_script_or_native_call_injection'])
    assert continued['weather_state']==2 and continued['party_count']==4
    assert continued['hoenn_badges']==continued['kanto_badges']==4
    assert continued['shelly_instances']==0 and continued['local_id_counts']['3']==0
    assert continued['player_elevation']==3 and continued['player_surfing'] is False
    return report
