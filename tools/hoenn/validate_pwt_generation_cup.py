"""Play one complete native generation cup without repeating the catalog audit.

Reuses the same controller battle loop as validate_pwt_world. Travel, registration
and boosted player battle stats are explicit fixtures. Opponent parties, battle
outcomes, progression, BP and party restoration execute in the actual ROM.
"""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
pwt_validator_text=(ROOT/'tools/hoenn/validate_pwt_world.py').read_text()
prefix=pwt_validator_text.split('for generation in range(cap+1):')[0]
exec(compile(prefix,str(ROOT/'tools/hoenn/validate_pwt_world.py'),'exec'))
assert a.play_cup and 1<=a.cup_generation<=cap
flow=pwt_validator_text.split('actual_battles=[]\n',1)[1].split('\nlib.stop()',1)[0]
# Progress logging only; the original loop still obtains every outcome natively.
flow=flow.replace("actual_battles.append(dict(stage=stage,opponent=entrant,attacks=attacks,outcome=1))",
    "actual_battles.append(dict(stage=stage,opponent=entrant,attacks=attacks,outcome=1))\n                print('Native victory',len(actual_battles),'generation',a.cup_generation,flush=True)")
actual_battles=[]
exec(compile(flow,str(ROOT/'tools/hoenn/validate_pwt_world.py'),'exec'))
entrants=[lib.read16(cup+offsets[8]+i*2) for i in range(lib.read16(cup+offsets[7]))]
for battle in actual_battles:
    index=entrants[battle['opponent']]
    battle['opponent_name']=rows[index]['name']
    battle['opponent_catalog_id']=index
    battle['level']=50;battle['player_team_size']=6;battle['enemy_team_size']=6
assert any(b['stage']==0 for b in actual_battles)
assert any(b['stage']==1 for b in actual_battles)
assert all(b['outcome']==1 for b in actual_battles)
report=dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
    version_generation_cap=cap,difficulty='Hard' if hard else 'Normal',cup_generation=a.cup_generation,
    complete_tournament_playthrough=True,actual_battles=actual_battles,entrants=len(entrants),
    champion=True,bp_reward=10,returned_to_lobby=True,party_restored_byte_exact=True,
    both_entrances_complete_at_ready_prompt=True,player_ready_position=[9,6],
    helper_and_travel_fixtures=True,player_battle_stats_boosted_for_flow_test=True,
    competitive_balance_test=False,full_campaign_playthrough=False)
report['unavailable_move_choices_avoided']=controller.avoided
report['exhausted_pp_for_struggle_fixture']=a.exhaust_pp_once
report['native_struggle_observed']=bool(struggle_seen)
lib.stop()
(args.output/'pwt-generation-cup.json').write_text(json.dumps(report,indent=2)+'\n')
print('Complete generation cup passed:',a.cup_generation,report['difficulty'],len(actual_battles),'native victories',flush=True)
