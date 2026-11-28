"""Inspect the compiled PWT catalog/parties and exercise its interactive board.

Travel, party creation and opponent selection are explicit native fixtures.
This report does not claim a complete tournament or campaign playthrough.
"""
import argparse, hashlib, json, re, struct, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--source',type=Path,required=True);p.add_argument('--library',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--play-cup',action='store_true',help='Also win one real cup; player battle stats are explicitly boosted fixtures')
p.add_argument('--cup-generation',type=int,default=3)
p.add_argument('--exhaust-pp-once',action='store_true',help='Set the first active battler PP to zero as an explicit Struggle fixture')
p.add_argument('--roster-review',type=Path,help='Compare actual six-member parties against the reviewed PWT data')
p.add_argument('--galar-review',action='store_true',help='Compare the Galar postgame rematch teams')
p.add_argument('--complete-review',action='store_true',help='Compare the final documented PWT additions')
a=p.parse_args()
sys.argv=[sys.argv[0],'--source',str(a.source),'--library',str(a.library),'--output',str(a.output)]
exec(compile((ROOT/'tools/hoenn/validate_abilities.py').read_text().split('\nability_field,')[0],str(ROOT/'tools/hoenn/validate_abilities.py'),'exec'))
from pwt_catalog import load, eligible
rows=load()
with tempfile.TemporaryDirectory(prefix='pwt-world-abi-',dir='/tmp') as d:
    out=Path(d)/'abi.s'
    subprocess.run([str(ROOT/'.local/arm-gcc/usr/bin/arm-none-eabi-gcc'),'-S','-iquote',str(source/'include'),'-include',str(source/'src/journey_pwt.c'),'-D_(x)=x','-DCOMPOUND_STRING(x)=((const u8 *)(x))','-DMODERN=1','-DPOKEEMERALD','-mthumb','-march=armv4t','-mabi=apcs-gnu',str(ROOT/'tools/hoenn/fixture_pwt_world_abi.c'),'-o',str(out)],check=True)
    text=out.read_text().split('gPWTWorldFixtureABI:',1)[1].split('.size',1)[0]
    offsets=[int(v) for v in re.findall(r'\.word\s+(\d+)',text)]
assert len(offsets)==79,offsets
state=s['sPWT'];cup=state+offsets[1];party=s['gParties'];enemy=party+6*abi[2]
cap=native('JourneyPWTMaxGeneration');hard=native('JourneyPerfectTrainerIvs')
assert cap in (4,9) and native('JourneyPWTCatalogCount')==len(rows)
reviewed_parties={}
if a.roster_review:
    from prepare_pwt_official_parties import validate_review
    roster_review=json.loads(a.roster_review.read_bytes())
    reviewed_parties=validate_review(roster_review)
if a.galar_review:
    from prepare_pwt_galar_za_megas import load_review
    galar_parties=load_review()
    reviewed_parties.update(galar_parties)
if a.complete_review:
    from prepare_pwt_complete_rosters import load_review
    complete_parties=load_review()
    reviewed_parties.update(complete_parties)
if reviewed_parties:
    catalog=json.loads((ROOT/'tools/hoenn/catalog_metadata.json').read_bytes())
    species_ids={row['name'].removeprefix('SPECIES_'):row['id'] for row in catalog['species'].values()}
for i in range(6*abi[2]):lib.write8(party+i,0)
lib.write8(s['gPartiesCount'],0)
for species,level in zip([260,149,376,121,445,6],[12,75,30,5,100,20]):
    assert native('ScriptGiveMon',species,level,0)==0
original=bytes(lib.read8(party+i) for i in range(6*abi[2]))
player_keys=offsets[31:35]+[offsets[43],offsets[44],abi[107],abi[65]]
original_keys=[[native('GetMonData2',party+i*abi[2],field) for field in player_keys] for i in range(6)]
bp_at=lib.read32(s['gSaveBlock2Ptr'])+offsets[38];bp_before=lib.read16(bp_at)
def begin(pool):
    lib.write8(state+offsets[2],6);lib.write8(state+offsets[3],pool)
    for i in range(6):lib.write8(s['gSelectedOrderFromParty']+i,i+1)
    native('JourneyPWTBegin');assert lib.read16(s['gSpecialVar_Result'])==1
    assert lib.read8(state+offsets[4])==1
    ids=[lib.read16(cup+offsets[8]+2*i) for i in range(lib.read16(cup+offsets[7]))]
    assert ids[0]==65535
    assert ids[1:]==[r['id'] for r in eligible(rows,cap,pool)]
    return ids
def finish():
    native('JourneyPWTFinish')
    assert bytes(lib.read8(party+i) for i in range(6*abi[2]))==original
    assert lib.read16(bp_at)==bp_before
    assert lib.read32(s['gBattleTypeFlags'])==0
def observe_ready_positions():
    stride, local_id, map_num, map_group, initial, current, count, border = offsets[71:79]
    group, number = location()
    assert (group, number) == map_id('JourneyPWTArena')
    # Read the live field objects while the ready prompt is still on screen.
    actors = []
    for i in range(count):
        at = s['gObjectEvents'] + i * stride
        if (lib.read8(at) & 1 and lib.read8(at + local_id) == 14
                and lib.read8(at + map_num) == number and lib.read8(at + map_group) == group):
            actors.append(at)
    assert len(actors) == 1, ('PWT opponent missing or duplicated', actors)
    actor, = actors
    def tile(field):
        return [lib.read16(actor + field) - border, lib.read16(actor + field + 2) - border]
    entrant = lib.read16(cup + offsets[9])
    trainer = lib.read16(cup + offsets[8] + 2 * entrant)
    graphics = lib.read16(actor + offsets[46])
    assert graphics == lib.read16(s['sPWTWalking'] + 2 * trainer), ('PWT walking identity', trainer)
    return dict(player=list(position()), opponent_start=tile(initial), opponent=tile(current),
                catalog_id=trainer, walking_graphics=graphics)


def check_ready_positions(observed):
    assert observed['player'] == [9, 6], observed
    assert observed['opponent_start'] == [17, 6] and observed['opponent'] == [13, 6], observed


for generation in range(cap+1):
    ids=begin(generation)
    assert all(bool(native('JourneyPWTTrainerEligible',r['id'],generation))==(r['id'] in ids[1:]) for r in rows)
    finish()
ids=begin(0);records=[];iv_values=set();high_portraits=0
for index in ids[1:]:
    lib.write16(cup+offsets[9],ids.index(index));lib.write8(cup+offsets[10],1)
    native('JourneyPWTPrepareBattle');assert lib.read8(s['gPartiesCount']+1)==6
    if index==ids[1]:
        for slot in range(6):
            mon=party+slot*abi[2]
            assert [native('GetMonData2',mon,field) for field in player_keys]==original_keys[slot]
            assert sum(native('GetMonData2',mon,field) for field in offsets[19:25])==510
            assert native('GetMonData2',mon,offsets[18])==50
    trainer=lib.read16(s['sPWTTrainers']+index*offsets[13]);picture_id=native('JourneyRivalTrainerPic',trainer)
    high_portraits+=picture_id>=256
    assert native('JourneyCompetitiveAiFlags',trainer)!=0
    mons=[]
    for slot in range(6):
        mon=enemy+slot*abi[2];species=native('GetMonData2',mon,abi[7])
        assert species==native('JourneyPWTRosterSpecies',index,slot)
        assert native('JourneySpeciesAllowed',species)
        assert native('GetMonData2',mon,offsets[18])==50
        evs=[native('GetMonData2',mon,field) for field in offsets[19:25]]
        ivs=[native('GetMonData2',mon,field) for field in offsets[25:31]]
        assert sum(evs)==510 and max(evs)<=252
        assert all(value==31 or (stat in (1,5) and value==0) for stat,value in enumerate(ivs)), (rows[index]['name'],slot,ivs)
        iv_values.update(ivs)
        moves=[native('GetMonData2',mon,field) for field in offsets[31:35]]
        assert all(not move or native('JourneyBossMoveLegal',species,move,100) for move in moves) and any(moves), (rows[index]['name'],slot,species,moves)
        ability=native('GetMonAbility',mon)
        assert ability != 0
        if rows[index]['key']=='EREN' and slot==5:assert ability==offsets[62]
        mons.append(dict(species=species,level=50,evs=evs,ivs=ivs,moves=moves,ability=ability))
        if a.complete_review:
            mons[-1]['held_item'] = native('GetMonData2',mon,offsets[69])
    reviewed=reviewed_parties.get(rows[index]['key'])
    if reviewed:
        expected=reviewed['gen1_4'] if cap==4 else reviewed['reference']
        assert [mon['species'] for mon in mons]==[species_ids[mon] for mon in expected], reviewed['key']
    if a.complete_review and rows[index]['key']=='GLADION':
        silvally,=[mon for mon in mons if mon['species']==species_ids['SILVALLY_WATER']]
        assert silvally['held_item']==offsets[70], silvally
    records.append(dict(name=rows[index]['name'],trainer_id=trainer,portrait_id=picture_id,team=mons))
assert high_portraits>0 and offsets[17]==2,'PWT portraits beyond byte range must use the widened enum'
assert 0 in iv_values and 31 in iv_values
finish()
optimized_player_cases=[]
for label,species,moveset,zero_attack,zero_speed,room_teammate in [
    ('slow_special_receiver',199,[offsets[48],offsets[49],offsets[50],0],False,True,True),
    ('special_attacker_reduced_attack',199,[offsets[48],offsets[49],offsets[50],0],True,False,False),
    ('slow_physical_receiver',437,[offsets[51],offsets[52],offsets[50],offsets[53]],False,True,True),
    ('mixed_attacker',392,[offsets[54],offsets[55],offsets[56],offsets[57]],False,False,False),
]:
    native('ZeroPlayerPartyMons');assert native('ScriptGiveMon',species,100,0)==0
    for slot,move in enumerate(moveset):native('ScriptSetMonMoveSlot',0,move,slot)
    scratch=s['gStringVar4']+800
    lib.write8(scratch,1)
    for field in range(offsets[45],offsets[45]+6):native('SetMonData',party,field,scratch)
    keys=[native('GetMonData2',party,field) for field in player_keys]
    if room_teammate:
        assert offsets[47] not in moveset,'Receiver must not know Trick Room'
        assert native('ScriptGiveMon',437,100,0)==0
        native('ScriptSetMonMoveSlot',1,offsets[47],0)
        native('JourneyPWTOptimizeParty',party,2)
    else:native('JourneyPWTOptimizeMon',party)
    assert [native('GetMonData2',party,field) for field in player_keys]==keys
    ivs=[native('GetMonData2',party,field) for field in offsets[25:31]]
    evs=[native('GetMonData2',party,field) for field in offsets[19:25]]
    assert ivs==[31,0 if zero_attack else 31,31,31,31,0 if zero_speed else 31],(label,ivs)
    assert sum(evs)==510 and max(evs)<=252
    if zero_speed:
        assert evs[5]==0
        assert native('GetMonData2',party,offsets[42]) in offsets[58:62]
    if label=='mixed_attacker':assert native('GetMonData2',party,offsets[42])==14 # Naive: preserve Attack and Sp. Atk.
    assert all(native('GetMonData2',party,field)==0 for field in range(offsets[45],offsets[45]+6))
    optimized_player_cases.append(dict(case=label,ivs=ivs,evs=evs,
        nature=native('GetMonData2',party,offsets[42]),moveset_preserved=True,
        trick_room_teammate=room_teammate,receiver_does_not_need_trick_room=room_teammate,
        hyper_training_does_not_override_zero_ivs=True))
for i,value in enumerate(original):lib.write8(party+i,value)
lib.write8(s['gPartiesCount'],6)
# Exercise real modal navigation using the controller; opening/closing the board
# must not advance the scheduler or resolve fixtures again.
begin(0);before=bytes(lib.read8(cup+i) for i in range(offsets[6]))
native('JourneyPWTBoard');step(150)
picture('pwt-world-group-standings')
for key in [256,256,512,4,128,64,256]:press(key)
picture('pwt-world-bracket-preview')
press(2);step(300)
assert bytes(lib.read8(cup+i) for i in range(offsets[6]))==before
finish()
actual_battles=[]
if a.play_cup:
    from pwt_cup_controller import CupController
    controller=CupController(source,lib,s)
    exhausted_pp=False;struggle_seen=False
    # This isolates the tournament lifecycle, not competitive difficulty.
    # Battle outcomes are produced by the battle engine/controller, never set.
    for i in range(6):native('ScriptSetMonMoveSlot',i,abi[142],0)
    tournament_original=bytes(lib.read8(party+i) for i in range(6*abi[2]))
    begin(a.cup_generation);warp('JourneyPWTArena',9,6)
    actions={int(addr,16) for addr,_,name in re.findall(r'^(\w+) (\w) (\S+)$',raw,re.M) if name=='HandleInputChooseAction'}
    move_actions={int(addr,16) for addr,_,name in re.findall(r'^(\w+) (\w) (\S+)$',raw,re.M) if name=='HandleInputChooseMove'}
    def ready():
        for _ in range(400):
            if task('Task_HandleYesNoInput'):step(12);return
            press(1)
        picture('pwt-world-ready-failure');raise AssertionError('Round ready prompt missing')
    while lib.read8(state+offsets[4]):
        ready()
        entrance = observe_ready_positions()
        check_ready_positions(entrance)
        entrant=lib.read16(cup+offsets[9]);stage=lib.read8(cup+offsets[12])
        picture('pwt-world-ring-'+str(len(actual_battles)))
        press(1)
        for _ in range(300):
            if lib.read32(s['gMain']+4)&~1==s['BattleMainCB2']:break
            press(1)
        else:raise AssertionError('PWT battle did not start')
        assert lib.read8(s['gPartiesCount'])==6 and lib.read8(s['gPartiesCount']+1)==6
        assert all(lib.read8(party+i*abi[2]+offsets[37])==50 for i in range(6))
        assert all(lib.read8(enemy+i*abi[2]+offsets[37])==50 for i in range(6))
        attacks=0
        for tick in range(2400):
            callback=lib.read32(s['gMain']+4)&~1
            if callback==s['BattleMainCB2']:
                lib.write16(s['gBattleMons']+offsets[63],16000)
                lib.write16(s['gBattleMons']+controller.abi[2],16000)
                lib.write16(s['gBattleMons']+offsets[64],10000)
                lib.write16(s['gBattleMons']+offsets[65],30000)
                if lib.read16(s['gBattleMons']+abi[102]):lib.write16(s['gBattleMons']+abi[102],30000)
                for i in range(6):
                    lib.write16(party+i*abi[2]+offsets[66],16000)
                    lib.write16(party+i*abi[2]+controller.abi[3],16000)
                    lib.write16(party+i*abi[2]+offsets[67],10000)
                    lib.write16(party+i*abi[2]+offsets[68],30000)
                    if lib.read16(party+i*abi[2]+abi[101]):lib.write16(party+i*abi[2]+abi[101],30000)
                handler=lib.read32(s['gBattlerControllerFuncs'])&~1
                if a.exhaust_pp_once and not exhausted_pp and handler in actions:
                    for slot in range(4):lib.write8(s['gBattleMons']+controller.abi[1]+slot,0)
                    exhausted_pp=True
                struggle_seen |= exhausted_pp and lib.read16(s['gCurrentMove'])==165 and lib.read8(s['gBattlerAttacker'])==0
                if handler in actions or handler in move_actions:
                    step(1,64);step(8);step(1,32);step(8)
                    if handler in move_actions:
                        choice=controller.choose_move()
                        if choice>=2:step(1,128);step(8)
                        if choice&1:step(1,16);step(8)
                    press(1)
                    attacks+=handler in move_actions
                else:press(2)
            elif task('Task_HandleChooseMonInput'):
                slot=lib.read8(s['gPartyMenu']+controller.abi[4])
                if slot>=6 or not lib.read16(party+slot*abi[2]+abi[101]):press(16 if slot==0 else 128)
                else:press(1)
            elif callback==s['CB2_Overworld']:
                assert lib.read8(s['gBattleOutcome'])==1
                actual_battles.append(dict(stage=stage,opponent=entrant,attacks=attacks,outcome=1,entrance=entrance))
                print('Native victory', len(actual_battles), 'generation', a.cup_generation, flush=True)
                break
            else:press(1)
        else:
            picture('pwt-world-battle-failure');raise AssertionError('Tournament battle unfinished')
        # Continue dialogue until the next native board or the championship.
        for _ in range(100):
            if not lib.read8(state+offsets[4]) or task('Task_HandleYesNoInput'):break
            press(1)
        assert len(actual_battles)<15
    for _ in range(250):
        if location()==map_id('JourneyPWTLobby') and not lib.read8(s['sLockFieldControls']):break
        press(1)
    assert location()==map_id('JourneyPWTLobby')
    assert bytes(lib.read8(party+i) for i in range(6*abi[2]))==tournament_original
    tournament_reward = lib.read16(bp_at) - bp_before
    assert tournament_reward == (10 if a.cup_generation else 25)
    assert lib.read8(cup+offsets[12])==2
    if a.exhaust_pp_once:assert exhausted_pp and struggle_seen,'Native Struggle was not observed'
    picture('pwt-world-cup-champion-return')
lib.stop()
report=dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
    catalog_identities=len(rows),version_generation_cap=cap,perfect_ivs=bool(hard),
    catalog_teams=records,independent_portraits_above_255=high_portraits,
    widened_portrait_enum_bytes=offsets[17],board_controller_navigation=True,
    board_does_not_advance_fixtures=True,party_restored_byte_exact=True,
    player_moves_items_ability_personality_preserved=True,optimized_player_cases=optimized_player_cases,
    pwt_perfect_stats_override_normal_edition=True,
    helper_and_travel_fixtures=True,complete_tournament_playthrough=bool(actual_battles),
    actual_battles=actual_battles,player_battle_stats_boosted_for_flow_test=bool(actual_battles),
    full_campaign_playthrough=False)
if a.roster_review:
    eligible_keys = {rows[index]['key'] for index in ids[1:]}
    report['reviewed_official_teams'] = sum(row['key'] in eligible_keys for row in roster_review['reviewed'])
    report['reviewed_league_teams'] = sum(row['key'] in eligible_keys for row in roster_review['league_reviewed'])
if a.galar_review:
    report['reviewed_galar_teams'] = sum(rows[index]['key'] in galar_parties for index in ids[1:])
if a.complete_review:
    report['reviewed_final_teams'] = sum(rows[index]['key'] in complete_parties for index in ids[1:])
    report['water_silvally_memory_verified'] = cap == 9
(args.output/'pwt-world.json').write_text(json.dumps(report,indent=2)+'\n')
print('Native PWT catalog/party/board checks passed:',len(records),'teams',flush=True)
