"""Verify native interaction evidence against an exact release ROM hash."""
import argparse
import json
from pathlib import Path

REQUIRED_GROUPS={'type_chart','status_type','status_ability','terrain','double_partner',
    'ability_resolution','grounding','move_block','powder','priority','item_negation',
    'damage','speed','critical','survival','berry','berry_heal','leppa','orbs',
    'residual_item','mental_herb','stat_stages','double_damage','weather_suppression',
    'turn_order','ai_hazards'}
REQUIRED_FUNCTIONS={'GetTypeModifier','CanBePoisoned','CanBeBurned','CanBeParalyzed',
    'CanBeFrozen','CanBeSlept','CanBeConfused','GetBattlerAbility','GetBattlerHoldEffect',
    'IsBattlerGrounded','CalcTypeEffectivenessMultiplier','CanMoveBeBlockedByTarget',
    'CalculateMoveDamageVars','ApplyModifiersAfterDmgRoll','GetBattlerTotalSpeedStat',
    'CalcCritChanceStage','GetAdjustedDamage','ItemBattleEffects',
    'GetWhichBattlerFasterOrTies','GetSwitchinHazardsDamage'}

def verify_report(report,sha,max_national=None,perfect_ivs=None):
    assert report['passed'] is True and report['rom_sha256']==sha,'Stale interaction evidence'
    if max_national is not None:
        assert report['max_national']==max_national
        assert report['version_generation_cap']==(4 if max_national==493 else 9)
    if perfect_ivs is not None:assert report['perfect_ivs'] is perfect_ivs
    checks=report['checks'];assert report['cases']==len(checks)>=600
    assert all(row['passed'] is True for row in checks)
    identities={(row['group'],row['case']) for row in checks}
    assert len(identities)==len(checks),'Duplicate case identifiers'
    groups=report['groups'];assert REQUIRED_GROUPS<=set(groups)
    assert sum(groups.values())==len(checks)
    assert all(count==sum(row['group']==group for row in checks) for group,count in groups.items())
    assert groups['type_chart']==324 and groups['status_type']==90
    for row in checks:
        if 'expected' in row:assert row['actual']==row['expected']
        elif 'expected_ratio' in row:
            assert row['baseline']>0 and 0<=row['tolerance']<=3
            assert abs(row['actual']-row['baseline']*row['expected_ratio'])<=row['tolerance']
        else:raise AssertionError(('Missing expectation',row['case']))
    assert REQUIRED_FUNCTIONS<=set(report['called_functions'])
    assert report['engine_functions_native'] and report['battle_state_is_prepared_fixture']
    assert report['damage_random_rolls_disabled']
    assert report['item_animation_and_consumption_scripts_not_played']
    assert not report['full_campaign_playthrough'] and not report['exhaustive_ability_item_coverage']
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--reports',type=Path,required=True)
    a=p.parse_args();m=json.loads(a.manifest.read_text())
    for row in m['variants']:
        edition=row['file'].removeprefix('Pokemon-Journey-').removesuffix('.gba')
        r=json.loads((a.reports/edition/'battle-interactions.json').read_text())
        verify_report(r,row['sha256'],row['max_national'],row['perfect_trainer_ivs'])
    print('Verified native battle interaction evidence for all four editions')
