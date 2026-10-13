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
assert len(offsets)==69,offsets
state=s['sPWT'];cup=state+offsets[1];party=s['gParties'];enemy=party+6*abi[2]
cap=native('JourneyPWTMaxGeneration');hard=native('JourneyPerfectTrainerIvs')
assert cap in (4,9) and native('JourneyPWTCatalogCount')==len(rows)
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
    # This isolates the tournament lifecycle, not competitive difficulty.
    # Battle outcomes are produced by the battle engine/controller, never set.
    for i in range(6):native('ScriptSetMonMoveSlot',i,abi[142],0)
    tournament_original=bytes(lib.read8(party+i) for i in range(6*abi[2]))
    begin(3);warp('JourneyPWTArena',9,6)
    actions={int(addr,16) for addr,_,name in re.findall(r'^(\w+) (\w) (\S+)$',raw,re.M) if name=='HandleInputChooseAction'}
    move_actions={int(addr,16) for addr,_,name in re.findall(r'^(\w+) (\w) (\S+)$',raw,re.M) if name=='HandleInputChooseMove'}
    def ready():
        for _ in range(400):
            if task('Task_HandleYesNoInput'):step(12);return
            press(1)
        picture('pwt-world-ready-failure');raise AssertionError('Round ready prompt missing')
    while lib.read8(state+offsets[4]):
        ready();entrant=lib.read16(cup+offsets[9]);stage=lib.read8(cup+offsets[12])
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
                lib.write16(s['gBattleMons']+offsets[64],10000)
                lib.write16(s['gBattleMons']+offsets[65],30000)
                if lib.read16(s['gBattleMons']+abi[102]):lib.write16(s['gBattleMons']+abi[102],30000)
                for i in range(6):
                    lib.write16(party+i*abi[2]+offsets[66],16000)
                    lib.write16(party+i*abi[2]+offsets[67],10000)
                    lib.write16(party+i*abi[2]+offsets[68],30000)
                    if lib.read16(party+i*abi[2]+abi[101]):lib.write16(party+i*abi[2]+abi[101],30000)
                handler=lib.read32(s['gBattlerControllerFuncs'])&~1
                if handler in actions or handler in move_actions:
                    step(1,64);step(8);step(1,32);step(8);press(1)
                    attacks+=handler in move_actions
                else:press(2)
            elif callback==s['CB2_Overworld']:
                assert lib.read8(s['gBattleOutcome'])==1
                actual_battles.append(dict(stage=stage,opponent=entrant,attacks=attacks,outcome=1))
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
    assert lib.read16(bp_at)==bp_before+10
    assert lib.read8(cup+offsets[12])==2
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
(args.output/'pwt-world.json').write_text(json.dumps(report,indent=2)+'\n')
print('Native PWT catalog/party/board checks passed:',len(records),'teams',flush=True)
