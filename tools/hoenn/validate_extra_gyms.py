"""Native party matrix, eight physical entrances, leader wins and 24-badge gates.

Initial party, journey progress and inter-city travel are fixtures. Doors,
movement, battles, badges, TMs, Trainer Card and save/continue use the engine.
Player battle stats are boosted for deterministic functional checks.
"""
from pathlib import Path
import hashlib,json,re,struct,subprocess
ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_trainer_levels.py').read_text().split('\nchecks=[]')[0]
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_trainer_levels.py'),'exec'))
report=json.loads((source/'.journey-extra-gyms').read_text());gyms=report['gyms']
initial_sha=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest()
# Native fast-text, Set battle style and disabled attack animations are test
# options only. Damage, AI, victory and reward scripts still run normally.
settings=lib.read32(s['gSaveBlock2Ptr'])+0x14
lib.write16(settings,(lib.read16(settings)&~7)|2|0x200|0x400)
from audit_battle_database import compiled,compiled_teachable_and_egg_moves
database=compiled(source);nonlevel=compiled_teachable_and_egg_moves(source)
field_names=['MON_DATA_IVS','MON_DATA_HP_EV','MON_DATA_ATK_EV','MON_DATA_DEF_EV','MON_DATA_SPATK_EV','MON_DATA_SPDEF_EV','MON_DATA_SPEED_EV','MON_DATA_MOVE1','MON_DATA_HELD_ITEM','MON_DATA_SPECIES','MON_DATA_LEVEL','MON_DATA_IS_EGG','ITEM_TM_FOCUS_PUNCH','ITEM_POTION','offsetof(struct SaveBlock2,encryptionKey)','sizeof(struct ItemSlot)','TYPE_GHOST','TYPE_FAIRY','TYPE_STEEL','TYPE_BUG','TYPE_ICE','TYPE_DRAGON','TYPE_DARK','POCKET_TM_HM','sizeof(struct BagPocket)','MOVE_SURF','MOVE_SHADOW_BALL','offsetof(struct BattlePokemon,spAttack)','offsetof(struct Pokemon,spAttack)','MOVE_WATERFALL','SPECIES_SWAMPERT','MOVE_ICE_BEAM','MOVE_EARTHQUAKE','offsetof(struct BattlePokemon,volatiles)','offsetof(struct BattlePokemon,pp)','offsetof(struct BattlePokemon,moves)']
field_names+=['ITEM_TM_'+g['tm'] for g in gyms]+['MOVE_'+g['tm'] for g in gyms]
code='#include "global.h"\n#include "pokemon.h"\n#include "battle.h"\n#include "item.h"\n#include "constants/items.h"\n#include "constants/pokemon.h"\n#include "constants/moves.h"\n#include <stddef.h>\nconst u32 probe[]={'+','.join(field_names)+'};'
a=subprocess.check_output([str(ROOT/'.local/arm-gcc/usr/bin/arm-none-eabi-gcc'),'-S','-iquote',str(source/'include'),'-mabi=apcs-gnu','-x','c','-','-o','-'],input=code,text=True)
c=dict(zip(field_names,[int(n) for n in re.findall(r'\.word\s+(\d+)',a.split('probe:',1)[1].split('.size',1)[0])]))
def data(mon,name):return native('GetMonData3',mon,c[name],0)
all_badges=hoenn_flags+kanto_flags+list(range(0x1040,0x1048))
def set_badges(count):
    for i,f in enumerate(all_badges):rawflag(f,i<count)
    assert native('JourneyTotalBadgeCount')==count
cap=lib.read16(s['gJourneyBuildRules']);perfect=bool(lib.read8(s['gJourneyBuildRules']+2))
checks=[]
for g in gyms:
    variants=[(g['key'],g['trainer'])]
    if g['key']=='WHITNEY':variants=[('WHITNEY' if cap==493 else 'VALERIE',g['trainer'] if cap==493 else 1768)]
    for key,trainer_id in variants:
        group,number=map_id(g['name']);lib.write8(save()+4,group);lib.write8(save()+5,number)
        for rank,level,players in [(0,6,1),(0,15,6),(3,25,3),(16,45,6),(23,80,6)]:
            set_badges(rank);team([level]*players)
            levels=generated(base+trainer_id*abi[0]);expected=6 if rank>=4 else rank+2+(players>rank+2)
            if key=='CLAIR':expected=min(expected,3 if level<36 else 5 if level<50 else 6)
            assert len(levels)==expected,(key,rank,len(levels),expected)
            assert levels[-1]==min(level+5,100),(key,levels)
            mons=[]
            for j,actual_level in enumerate(levels):
                mon=enemy+j*abi[2];sid=data(mon,'MON_DATA_SPECIES');entry=database['species'][sid]
                assert native('JourneySpeciesAllowed',sid),(key,sid,cap)
                if g['kind']!='MIXED':assert c['TYPE_'+g['kind']] in entry['types'],(key,sid,entry)
                evs=[data(mon,f) for f in field_names[1:7]];ivs=data(mon,'MON_DATA_IVS')&0x3FFFFFFF
                assert sum(evs)==510 and max(evs)<=252,(key,evs)
                if perfect:assert ivs==0x3FFFFFFF
                else:assert ivs!=0x3FFFFFFF,(key,'Normal must preserve random IVs')
                moveset=[native('GetMonData3',mon,c['MON_DATA_MOVE1']+k,0) for k in range(4)]
                legal=nonlevel[sid]|{move for at,move in entry['learnset'] if at<=actual_level}
                assert all(move in legal for move in moveset if move),(key,sid,actual_level,moveset)
                assert any(database['moves'][move]['category']!=2 for move in moveset if move)
                mons.append(dict(species=sid,name=entry['name'],level=actual_level,ivs=ivs,evs=evs,moves=moveset))
            if key=='OAK' and rank>=4:assert {3,6,9}<=set(m['species'] for m in mons)
            checks.append(dict(leader=key,total_badges=rank,player_count=players,mons=mons))
    print('Native roster:',g['key'],flush=True)
# Real map-load, doors and walking tests follow the generation-only fixtures.
set_badges(0);team([40,40,40]);
for i in range(6*abi[2]):lib.write8(party+i,0)
lib.write8(s['gPartiesCount'],0)
for i in range(3):native('ScriptGiveMon',c['SPECIES_SWAMPERT'],40,0)
native('HealPlayerParty')
for i in range(41):rawflag(0x1000+i,False)
for i in range(8):rawflag(0x1048+i,False)
# Trainers are marked only while checking physical paths, then cleared and
# manually battled. The test ROM's no-approach rule does not skip interaction.
for i in range(32):rawflag(0x1009+i,True)
# The travel fixture represents a completed Sevii biker episode. Keep the
# original biker blockade in the game; do not mistake it for a gym path defect.
native('VarSet',0x417B,4)
for f in [0x1854,0x1859,0x192B]:rawflag(f,True)
names=[g['city'] for g in gyms]+[g['name'] for g in gyms]
allowed=set();walk_prefix='extra-gym';walk_transition_pictures=False;walk_max_ticks=1800
exec(compile((ROOT/'tools/hoenn/native_water_walk.py').read_text(),'extra-gym-native-walker','exec'))

def until(predicate,limit=300):
    for _ in range(limit):
        if predicate():return
        press(1)
    picture('extra-gym-timeout');raise AssertionError(('Timeout',location(),position()))
def talk(key=64):step(4,key);step(20);press(1)
def fight(trainer_id,lose=False,approach=None):
    if isinstance(trainer_id,dict):
        trainer_id=trainer_id['id'];j=g['students'].index(trainer_id);student=g['room']['students'][j]
        original=student['position'];distance=sum(abs(a-b) for a,b in zip(original,position()))
        assert 2<=distance<=student['sight'],('Trainer did not approach from clear range',g['key'],j,distance)
        approach=dict(local_id=j+3,original=original,facing=student['facing'],controller_entered_sightline_at_distance=distance,
            sight_range=student['sight'],mandatory_route_from_city=True)
    started=False;attacks=0;seen=None
    targets={int(a,16) for a,_,n in re.findall(r'^(\w+) (\w) (\S+)$',raw,re.M) if n in ['HandleInputChooseTarget','HandleInputShowTargets','HandleInputShowEntireFieldTargets']}
    for tick in range(4000):
        cb=lib.read32(s['gMain']+4)&~1
        if cb==s['BattleMainCB2']:
            started=True
            assert lib.read16(s['gTrainerBattleParameter']+abi[13])==trainer_id
            if seen is None:
                seen=[lib.read16(s['gBattleMons']+abi[74]+abi[75])]
                picture('battle-'+str(trainer_id))
                if approach is not None:
                    obj=next(s['gObjectEvents']+36*i for i in range(16) if lib.read8(s['gObjectEvents']+36*i)&1 and lib.read8(s['gObjectEvents']+36*i+8)==approach['local_id'])
                    here=[lib.read16(obj+16)-7,lib.read16(obj+18)-7]
                    assert here!=approach['original'] and sum(abs(a-b) for a,b in zip(here,position()))==1,(trainer_id,'trainer did not walk into adjacent range',here,position())
                    approach['native_position_at_battle']=here;approach['native_walked_to_player']=True
            # Native battle outcome and rewards remain untouched.
            if not lose:
                lib.write16(s['gBattleMons']+c['offsetof(struct BattlePokemon,spAttack)'],16000);lib.write16(s['gBattleMons']+pabi[15],16000);lib.write16(s['gBattleMons']+pabi[16],10000)
                lib.write16(s['gBattleMons']+pabi[20],30000)
                if lib.read16(s['gBattleMons']+abi[102]):lib.write16(s['gBattleMons']+abi[102],30000)
                lib.write32(s['gBattleMons']+abi[95],0)
                for i in range(3):
                    lib.write16(party+i*abi[2]+c['offsetof(struct Pokemon,spAttack)'],16000);lib.write16(party+i*abi[2]+pabi[8],16000);lib.write16(party+i*abi[2]+pabi[9],10000)
                    lib.write16(party+i*abi[2]+pabi[21],30000)
                    if lib.read16(party+i*abi[2]+abi[101]):lib.write16(party+i*abi[2]+abi[101],30000)
            else:
                lib.write16(s['gBattleMons']+abi[102],1)
                for i in range(3):lib.write16(party+i*abi[2]+abi[101],1)
            controllers={lib.read32(s['gBattlerControllerFuncs']+4*i)&~1 for i in range(4)}
            if controllers&targets:press(1)
            elif controllers&moves:
                # Try moves through the native UI in turn. Choice items,
                # Encore, Torment and Cursed Body can reject a selection;
                # always retry another move instead of repeating that rejection.
                slots=[j for j in range(4) if lib.read16(s['gBattleMons']+c['offsetof(struct BattlePokemon,moves)']+j*2) and lib.read8(s['gBattleMons']+c['offsetof(struct BattlePokemon,pp)']+j)]
                desired=(slots or [0])[attacks%max(1,len(slots))];current=lib.read8(s['gMoveSelectionCursor'])
                if (current&1)!=(desired&1):press(16 if desired&1 else 32)
                elif (current>>1)!=(desired>>1):press(128 if desired>>1 else 64)
                else:press(1);attacks+=1
            elif controllers&actions:
                step(1,64);step(8);step(1,32);step(8);press(1)
            else:press(2)
        elif cb in {s['CB2_InitPartyMenu'],s['CB2_UpdatePartyMenu']}:
            if task('Task_HandleChooseMonInput'):
                available=[]
                for slot in range(1,6):
                    order=lib.read8(s['gBattlePartyCurrentOrder']+slot//2)
                    physical=(order&15) if slot&1 else order>>4
                    if physical<6 and lib.read16(party+physical*abi[2]+abi[101]):available.append(slot)
                assert available,('No surviving gym test party',trainer_id)
                desired=available[0]
                press(128 if lib.read8(s['gPartyMenu']+abi[100])!=desired else 1)
            else:press(1)
        elif started and cb==s['CB2_Overworld']:
            outcome=lib.read8(s['gBattleOutcome']);assert outcome==(2 if lose else 1),(trainer_id,outcome)
            finish()
            assert bool(native('HasTrainerBeenFought',trainer_id))==(not lose)
            return dict(trainer=trainer_id,outcome=outcome,attacks=attacks,approach=approach)
        else:press(1)
    picture('battle-timeout');raise AssertionError(('Battle timeout',trainer_id,hex(cb)))
# Teach a reliable, legal move. This is a function test, not a balance proof.
for i in range(3):
    for slot in range(4):native('ScriptSetMonMoveSlot',i,[c['MOVE_WATERFALL'],c['MOVE_SURF'],c['MOVE_ICE_BEAM'],c['MOVE_EARTHQUAKE']][slot],slot)
checkpoint=args.output/'extra-gyms.checkpoint.json'
results=[]
if checkpoint.exists():
    saved=json.loads(checkpoint.read_text())
    if saved['rom_sha256']==initial_sha and saved['max_national']==cap and saved['perfect_ivs']==perfect:
        results=saved['gyms'];assert [r['leader'] for r in results]==[g['key'] for g in gyms[:len(results)]]
        for g in gyms[:len(results)]:
            rawflag(g['badge_flag'],True);rawflag(g['tm_flag'],True)
            tid=1768 if g['key']=='WHITNEY' and cap>493 else g['trainer']
            rawflag(0x1000+tid-1760,True)
            native('AddBagItem',c['ITEM_TM_'+g['tm']],1)
for index,g in enumerate(gyms):
    if index<len(results):continue
    native('HealPlayerParty')
    review_mode=bool(lib.read8(s['gJourneyReviewMode']))
    allowed=set() if review_mode else set(g['students']);before_wins=len(wins)
    if not review_mode:
        for trainer in g['students']:rawflag(0x1000+trainer-1760,False)
    start={'MORTY':(10,12),'WHITNEY':(40,25),'STEVEN':(27,49),'BUGSY':(14,8),'CANDICE':(19,20),'CLAIR':(11,12),'KAREN':(14,28),'OAK':(5,10)}[g['key']]
    warp(g['city'],*start);step(100)
    gx,gy=g['room']['guide']
    walk((g['name'],gx-1,gy));step(30);picture(g['key'].lower()+'-guide-at-entrance')
    talk(16);finish()
    assert location()==map_id(g['name']) and position()==(gx-1,gy)
    walk((g['name'],*g['room']['leader_approach']));step(60);picture(g['key'].lower()+'-inside')
    for student in g['room']['students']:
        xx,yy=student['position'];dx,dy={'RIGHT':(1,0),'LEFT':(-1,0),'DOWN':(0,1),'UP':(0,-1)}[student['facing']]
        for distance in range(7):
            for side in [-1,0,1]:
                assert native('MapGridGetCollisionAt',xx+dx*distance+dy*side+7,yy+dy*distance+dx*side+7)==0,(g['key'],'native approach blocked',student,distance,side)
    automatic_wins=wins[before_wins:]
    if not review_mode:
        assert [r['trainer'] for r in automatic_wins]==g['students'],('Mandatory route skipped a trainer',g['key'],automatic_wins)
        assert max(r['approach']['controller_entered_sightline_at_distance'] for r in automatic_wins)>=4
    trainer_id=1768 if g['key']=='WHITNEY' and cap>493 else g['trainer']
    # TM pocket is truly full before the first win; badge and TM flags must
    # remain independent so a later visit can recover the gift.
    bag_snapshot=None
    if index==0:
        pocket=s['gBagPockets']+c['POCKET_TM_HM']*c['sizeof(struct BagPocket)'];ptr=lib.read32(pocket);capacity=lib.read16(pocket+4)&1023
        bag_snapshot=bytes(lib.read8(ptr+i) for i in range(capacity*c['sizeof(struct ItemSlot)']))
        key=lib.read32(lib.read32(s['gSaveBlock2Ptr'])+c['offsetof(struct SaveBlock2,encryptionKey)'])&65535
        for j in range(capacity):lib.write16(ptr+j*4,c['ITEM_TM_FOCUS_PUNCH']);lib.write16(ptr+j*4+2,999^key)
        assert not native('CheckBagHasSpace',c['ITEM_TM_'+g['tm']],1)
    talk();leader_win=fight(trainer_id)
    assert flag(g['badge_flag']) and native('JourneyTotalBadgeCount')==index+1
    if bag_snapshot is not None:
        assert not flag(g['tm_flag'])
        for j,b in enumerate(bag_snapshot):lib.write8(ptr+j,b)
        talk();finish()
    assert flag(g['tm_flag'])
    quantity=native('CountTotalItemQuantityInBag',c['ITEM_TM_'+g['tm']]);assert quantity>=1
    assert native('ItemIdToBattleMoveId',c['ITEM_TM_'+g['tm']])==c['MOVE_'+g['tm']]
    talk();finish()
    assert native('CountTotalItemQuantityInBag',c['ITEM_TM_'+g['tm']])==quantity
    assert native('JourneyTotalBadgeCount')==index+1
    # The normal walk has already triggered all four separate approaches.
    # TESTE suppresses approaches but preserves manual challenges.
    student_wins=list(automatic_wins)
    for j,student in enumerate(g['room']['students']):
        if not review_mode:continue
        native('HealPlayerParty')
        xx,yy=student['position'];dx,dy={'RIGHT':(1,0),'LEFT':(-1,0),'DOWN':(0,1),'UP':(0,-1)}[student['facing']]
        catch_x,catch_y=xx+3*dx,yy+3*dy;trainer=g['students'][j]
        rawflag(0x1000+trainer-1760,False)
        warp(g['name'],catch_x,catch_y)
        assert native('MapGridGetCollisionAt',catch_x+7,catch_y+7)==0
        step(30)
        if review_mode:
            step(600);assert idle() and position()==(catch_x,catch_y)
            walk((g['name'],xx+dx,yy+dy));talk({(1,0):32,(-1,0):16,(0,1):64,(0,-1):128}[(dx,dy)])
            win=fight(trainer);win['automatic_approach_disabled']=True;win['manual_battle']=True
        else:
            win=fight(trainer,approach=dict(local_id=j+3,original=[xx,yy],facing=student['facing'],controller_entered_sightline_at_distance=3,sight_range=student['sight']))
        student_wins.append(win)
    walk((g['city'],g['entry'][0],g['entry'][1]+1));step(60);picture(g['key'].lower()+'-outside')
    results.append(dict(leader=g['key'],trainer=trainer_id,controller_entry_and_exit=True,guide_talked_near_entrance=True,leader_win=leader_win,
        students=student_wins,all_four_battled_separately_on_mandatory_walk=not review_mode,
        badge_once=True,tm_once=True,bag_full_retry=index==0,tm_move_matches=True))
    checkpoint.write_text(json.dumps(dict(rom_sha256=initial_sha,max_national=cap,perfect_ivs=perfect,gyms=results),indent=2)+'\n')
    print('Native gym entered, won and exited:',g['key'],flush=True)
# All 24 unique badges count; one missing badge must deny both admissions.
from validate_extra_gym_league import check_leagues
league=check_leagues(globals())
# Save at a real new gym, continue and retain the complete badge circuit.
set_badges(24);warp('JourneyOakBasementGym',*gyms[-1]['room']['safe'])
assert native('TrySavingData',0,max_frames=6000)==1
assert native('LoadGameSave',0,max_frames=6000)==1
lib.write32(s['gMain']+4,s['CB2_ContinueSavedGame']|1);step(1500)
assert location()==map_id('JourneyOakBasementGym') and native('JourneyTotalBadgeCount')==24
assert all(flag(g['tm_flag']) for g in gyms)
# Open the real Trainer Card through the player entry in the Start menu.
exec(compile((ROOT/'tools/hoenn/validate_extra_gym_card.py').read_text(),'extra-gym-card','exec'))
assert hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest()==initial_sha
lib.stop()
(args.output/'extra-gyms.json').write_text(json.dumps(dict(passed=True,rom_sha256=initial_sha,max_national=cap,perfect_ivs=perfect,
    roster_cases=len(checks),rosters=checks,gyms=results,league=league,all_24_badges_saved_and_continued=True,
    actual_three_page_trainer_card=True,initial_party_progress_travel_and_boosted_player_stats_are_fixtures=True,native_fast_text_set_style_and_no_attack_animations_are_fixtures=True,
    resume_progress_can_be_a_fixture_with_same_rom_native_results=True,enemy_party_and_native_battle_outcome_not_written=True,reward_flags_not_written_during_battles=True,full_campaign_playthrough=False),indent=2)+'\n')

checkpoint.unlink(missing_ok=True)
