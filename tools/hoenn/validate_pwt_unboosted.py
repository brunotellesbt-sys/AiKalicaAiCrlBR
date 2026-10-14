"""Play native PWT battles with legal, unboosted level-50 parties.

Uses controller inputs for a deterministic attack-focused player bot against
the game's unchanged opponent AI. Travel/registration/party/seed are fixtures. No
battle stats, HP, PP, outcomes or tournament results are written during combat.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
extra=argparse.ArgumentParser(add_help=False)
extra.add_argument('--team',choices=['balanced','developing'],default='balanced')
extra.add_argument('--seed',type=int,default=101)
extra.add_argument('--opponent',type=int)
extra.add_argument('--max-battle-frames',type=int,default=240000)
opts,remaining=extra.parse_known_args()
sys.argv=[sys.argv[0],*remaining]
bootstrap=(ROOT/'tools/hoenn/validate_pwt_world.py').read_text().split('for generation in range(cap+1):')[0]
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_pwt_world.py'),'exec'))
from battle_interaction_fixture import compile_probe

profiles=json.loads((ROOT/'tools/hoenn/data/pwt-balanced-player-teams.json').read_text())
profile=profiles['developing' if opts.team=='developing' else 'generation'+str(cap)]
constants={'MON_DATA_ABILITY_NUM','MON_DATA_HP','MON_DATA_STATUS','MON_DATA_HELD_ITEM','MON_DATA_PP1',
           'MON_DATA_ATK','MON_DATA_DEF','MON_DATA_SPATK','MON_DATA_SPDEF','MON_DATA_SPEED',
           'PARTY_ACTION_SWITCH','PARTY_ACTION_SOFTBOILED'}
type_names='NORMAL FIRE WATER ELECTRIC GRASS ICE FIGHTING POISON GROUND FLYING PSYCHIC BUG ROCK GHOST DRAGON DARK STEEL FAIRY'.split()
constants.update('TYPE_'+name for name in type_names)
for mon in profile:
    constants.add('SPECIES_'+mon['species']);constants.add('ITEM_'+mon['item'])
    constants.update('MOVE_'+move for move in mon['moves'])
layout,values,masks=compile_probe(source,constants)
# Ordinary in-game settings speed the fixture up without altering combat rules.
save_options=lib.read32(s['gSaveBlock2Ptr'])
for field,value in [('save_sceneOff',1),('save_textSpeed',2)]:
    _,offset,shift,width,size=masks[field];at=save_options+offset
    prior=int.from_bytes(bytes(lib.read8(at+i) for i in range(size)),'little')
    mask=((1<<width)-1)<<shift;changed=(prior&~mask)|((value<<shift)&mask)
    for i,b in enumerate(changed.to_bytes(size,'little')):lib.write8(at+i,b)
native('ZeroPlayerPartyMons')
for slot,mon in enumerate(profile):
    species=values['SPECIES_'+mon['species']]
    assert native('JourneySpeciesAllowed',species),mon
    assert native('ScriptGiveMon',species,100,values['ITEM_'+mon['item']])==0
    scratch=s['gStringVar4']+800;lib.write8(scratch,mon['slot'])
    native('SetMonData',party+slot*abi[2],values['MON_DATA_ABILITY_NUM'],scratch)
    for move_slot,move in enumerate(mon['moves']):
        move_id=values['MOVE_'+move]
        assert native('JourneyBossMoveLegal',species,move_id,100),(mon['species'],move)
        native('ScriptSetMonMoveSlot',slot,move_id,move_slot)
original=bytes(lib.read8(party+i) for i in range(6*abi[2]))
native('SeedRng',opts.seed&65535)
begin(a.cup_generation)
ids=[lib.read16(cup+offsets[8]+2*i) for i in range(lib.read16(cup+offsets[7]))]
if opts.opponent is not None:
    assert opts.opponent in ids[1:],('Opponent not eligible',opts.opponent)
    # Isolate an actual catalog matchup without presenting it as a scheduled cup.
    lib.write16(cup+offsets[9],ids.index(opts.opponent));lib.write8(cup+offsets[10],1)
warp('JourneyPWTArena',9,6)
from pwt_cup_controller import CupController
controller=CupController(source,lib,s)
actions={int(at,16) for at,_,name in re.findall(r'^(\w+) (\w) (\S+)$',raw,re.M) if name=='HandleInputChooseAction'}
move_actions={int(at,16) for at,_,name in re.findall(r'^(\w+) (\w) (\S+)$',raw,re.M) if name=='HandleInputChooseMove'}

def party_snapshot(address):
    result=[]
    for slot in range(6):
        at=address+slot*abi[2]
        result.append(dict(level=lib.read8(at+offsets[37]),
            hp=lib.read16(at+abi[101]),max_hp=lib.read16(at+offsets[68]),
            attack=lib.read16(at+offsets[66]),speed=lib.read16(at+offsets[67])))
    return result

chart={
 'NORMAL':('','ROCK STEEL','GHOST'),'FIRE':('GRASS ICE BUG STEEL','FIRE WATER ROCK DRAGON',''),
 'WATER':('FIRE GROUND ROCK','WATER GRASS DRAGON',''),'ELECTRIC':('WATER FLYING','ELECTRIC GRASS DRAGON','GROUND'),
 'GRASS':('WATER GROUND ROCK','FIRE GRASS POISON FLYING BUG DRAGON STEEL',''),
 'ICE':('GRASS GROUND FLYING DRAGON','FIRE WATER ICE STEEL',''),
 'FIGHTING':('NORMAL ICE ROCK DARK STEEL','POISON FLYING PSYCHIC BUG FAIRY','GHOST'),
 'POISON':('GRASS FAIRY','POISON GROUND ROCK GHOST','STEEL'),
 'GROUND':('FIRE ELECTRIC POISON ROCK STEEL','GRASS BUG','FLYING'),
 'FLYING':('GRASS FIGHTING BUG','ELECTRIC ROCK STEEL',''),
 'PSYCHIC':('FIGHTING POISON','PSYCHIC STEEL','DARK'),'BUG':('GRASS PSYCHIC DARK','FIRE FIGHTING POISON FLYING GHOST STEEL FAIRY',''),
 'ROCK':('FIRE ICE FLYING BUG','FIGHTING GROUND STEEL',''),'GHOST':('PSYCHIC GHOST','DARK','NORMAL'),
 'DRAGON':('DRAGON','STEEL','FAIRY'),'DARK':('PSYCHIC GHOST','FIGHTING DARK FAIRY',''),
 'STEEL':('ICE ROCK FAIRY','FIRE WATER ELECTRIC STEEL',''),'FAIRY':('FIGHTING DRAGON DARK','FIRE POISON STEEL','')}
type_by_id={values['TYPE_'+name]:name for name in type_names}
def damage_score(row):
    if row['category']==2:return 1
    base=s['gBattleMons'];foe=base+layout['mon_size'];effect=1
    enemy_types={type_by_id.get(lib.read8(foe+layout['mon_types']+i)) for i in range(2)}
    strong,resist,immune=chart[type_by_id[row['type']]]
    for type_ in enemy_types:
        if type_ in immune.split():effect=0
        elif type_ in strong.split():effect*=2
        elif type_ in resist.split():effect*=.5
    own_types={lib.read8(base+layout['mon_types']+i) for i in range(2)}
    physical=row['category']==0
    attack=lib.read16(base+layout['mon_attack' if physical else 'mon_spAttack'])
    defense=lib.read16(foe+layout['mon_defense' if physical else 'mon_spDefense'])
    return row['power']*max(1,attack)/max(1,defense)*effect*(1.5 if row['type'] in own_types else 1)

battles=[]
chosen_samples=[]
while lib.read8(state+offsets[4]):
    for _ in range(400):
        if task('Task_HandleYesNoInput'):step(12);break
        press(1)
    else:raise AssertionError('PWT ready prompt missing')
    assert position()==(9,6)
    entrant=lib.read16(cup+offsets[9]);stage=lib.read8(cup+offsets[12])
    if opts.opponent is not None:assert ids[entrant]==opts.opponent
    press(1)
    for _ in range(400):
        if lib.read32(s['gMain']+4)&~1==s['BattleMainCB2']:break
        press(1)
    else:raise AssertionError('PWT battle did not start')
    player_start=party_snapshot(party);enemy_start=party_snapshot(enemy)
    assert lib.read8(s['gPartiesCount'])==lib.read8(s['gPartiesCount']+1)==6
    assert all(mon['level']==50 and 0<mon['max_hp']<800 and 0<mon['attack']<800 and 0<mon['speed']<800 for mon in player_start+enemy_start),(player_start,enemy_start)
    frames=0
    while (lib.read32(s['gMain']+4)&~1)!=s['CB2_Overworld']:
        callback=lib.read32(s['gMain']+4)&~1
        if callback==s['BattleMainCB2']:
            handler=lib.read32(s['gBattlerControllerFuncs'])&~1
            if handler in actions or handler in move_actions:
                step(1,64);step(8);step(1,32);step(8)
                if handler in move_actions:
                    choice=controller.choose_move(damage_score)
                    if len(chosen_samples)<16:
                        move=lib.read16(s['gBattleMons']+controller.abi[0]+choice*2)
                        chosen_samples.append(dict(slot=choice,move=move,last_executed=lib.read16(s['gLastMoves']),enemy_species=lib.read16(s['gBattleMons']+layout['mon_size']+layout['mon_species']),enemy_ability=lib.read16(s['gBattleMons']+layout['mon_size']+layout['mon_ability']),enemy_item=lib.read16(s['gBattleMons']+layout['mon_size']+layout['mon_item']),player_hp=lib.read16(s['gBattleMons']+layout['mon_hp']),enemy_hp=lib.read16(s['gBattleMons']+layout['mon_size']+layout['mon_hp'])))
                    if choice>=2:step(1,128);step(8)
                    if choice&1:step(1,16);step(8)
                    if len(chosen_samples)<16:chosen_samples[-1]['actual_cursor']=lib.read8(s['gMoveSelectionCursor'])
                press(1)
            else:press(2)
        elif task('Task_HandleChooseMonInput'):
            action=lib.read8(s['gPartyMenu']+layout['party_action'])
            offset=layout['party_slot2'] if action in (values['PARTY_ACTION_SWITCH'],values['PARTY_ACTION_SOFTBOILED']) else controller.abi[4]
            slot=lib.read8(s['gPartyMenu']+offset)
            packed=lib.read8(s['gBattlePartyCurrentOrder']+min(slot,5)//2)
            battle_id=(packed&15) if slot&1 else (packed>>4)
            active=lib.read8(s['gBattlerPartyIndexes'])
            if slot>=6 or not lib.read16(party+slot*abi[2]+abi[101]) or battle_id==active:press(16 if slot==0 else 128)
            else:press(1)
        else:press(1)
        frames+=75  # Conservative input-frame budget; not a battle turn count.
        if frames>opts.max_battle_frames:
            picture('unboosted-stalled-battle')
            print('Stall callback',hex(callback),'party action',lib.read8(s['gPartyMenu']+layout['party_action']),
                  'slots',lib.read8(s['gPartyMenu']+controller.abi[4]),lib.read8(s['gPartyMenu']+layout['party_slot2']),
                  'HP',[lib.read16(party+i*abi[2]+abi[101]) for i in range(6)],flush=True)
            raise AssertionError(('Battle did not finish',rows[ids[entrant]]['name'],frames))
    outcome=lib.read8(s['gBattleOutcome']);assert outcome in [1,2,3],outcome
    record=dict(opponent_catalog_id=ids[entrant],opponent=rows[ids[entrant]]['name'],stage=stage,
        outcome=outcome,input_frame_budget_used=frames,player_start=player_start,enemy_start=enemy_start,
        player_survivors=sum(lib.read16(party+i*abi[2]+abi[101])>0 for i in range(6)),
        enemy_survivors=sum(lib.read16(enemy+i*abi[2]+abi[101])>0 for i in range(6)))
    battles.append(record)
    print('Native unboosted battle',len(battles),record['opponent'],'outcome',outcome,'input frame budget',frames,flush=True)
    if opts.opponent is not None:
        # The normal callback will be driven only for full cup runs.
        native('JourneyPWTFinish')
        warp('JourneyPWTLobby',6,6)
        break
    for _ in range(100):
        if not lib.read8(state+offsets[4]) or task('Task_HandleYesNoInput'):break
        press(1)
    assert len(battles)<20
for _ in range(300):
    if location()==map_id('JourneyPWTLobby') and not lib.read8(s['sLockFieldControls']):break
    press(1)
assert location()==map_id('JourneyPWTLobby')
restored=bytes(lib.read8(party+i) for i in range(6*abi[2]))==original
assert restored,'Original party not restored byte-exact'
reward=lib.read16(bp_at)-bp_before
assert reward in [0,10 if a.cup_generation else 25],reward
report=dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
    version_generation_cap=cap,perfect_ivs=bool(hard),pool=a.cup_generation,team=opts.team,seed=opts.seed,
    single_catalog_matchup=opts.opponent,full_cup_participation=opts.opponent is None,
    battles=battles,chosen_move_samples=chosen_samples,wins=sum(b['outcome']==1 for b in battles),losses=sum(b['outcome']==2 for b in battles),
    registered_profile=profile,
    draws=sum(b['outcome']==3 for b in battles),champion=reward>0,bp_reward=reward,
    returned_to_lobby=True,original_party_restored_byte_exact=restored,
    player_controller_is_attack_focused_input_bot=True,opponent_ai_unchanged=True,
    player_bot_accounts_for_types_stab_category_and_defenses=True,
    ordinary_settings_battle_scene_off=True,ordinary_settings_text_speed_fast=True,
    party_travel_registration_and_seed_are_fixtures=True,battle_stat_hp_pp_or_outcome_writes=False,
    full_campaign_playthrough=False,human_difficulty_claim=False)
lib.stop()
(args.output/'pwt-unboosted.json').write_text(json.dumps(report,indent=2)+'\n')
print('Unboosted PWT run passed:',report['wins'],'wins',report['losses'],'losses',reward,'BP',flush=True)
