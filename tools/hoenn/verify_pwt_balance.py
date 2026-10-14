"""Validate unboosted combat evidence without converting losses into wins."""
def verify_report(report,sha,cap,hard,pool=None):
    assert report['passed'] and report['rom_sha256']==sha
    assert report['version_generation_cap']==cap and report['perfect_ivs'] is hard
    if pool is not None:assert report['pool']==pool and report['full_cup_participation']
    assert report['opponent_ai_unchanged'] and report['player_controller_is_attack_focused_input_bot']
    assert not report['battle_stat_hp_pp_or_outcome_writes'] and not report['human_difficulty_claim']
    assert report['returned_to_lobby'] and report['original_party_restored_byte_exact']
    assert report['battles']
    for b in report['battles']:
        assert b['outcome'] in (1,2,3)
        assert len(b['player_start'])==len(b['enemy_start'])==6
        for mon in b['player_start']+b['enemy_start']:
            assert mon['level']==50 and 0<mon['max_hp']<800
            assert 0<mon['attack']<800 and 0<mon['speed']<800
    assert report['wins']==sum(b['outcome']==1 for b in report['battles'])
    assert report['losses']==sum(b['outcome']==2 for b in report['battles'])
    assert report['draws']==sum(b['outcome']==3 for b in report['battles'])
    assert report['champion']==(report['bp_reward']>0)
    assert report['bp_reward']==(10 if report['pool'] else 25) if report['champion'] else report['bp_reward']==0
    return report
