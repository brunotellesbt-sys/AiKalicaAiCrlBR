"""Approach actual Surf trainers, win native battles, SAVE and cold Continue.

Initial party/progress and one location per case are fixtures. Player stats
are boosted before departure only; battles receive controller input and no
RAM writes. This proves behavior and persistence, not difficulty balance.
"""
import argparse
import hashlib
import json
from pathlib import Path

from validate_atlas_candidate_batteries_native import save_menu
from validate_coast_scenery_objects import bootstrap
from validate_cold_boot import validate as cold_boot


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(source,library,output,offset=0,limit=None,manual=False):
    source,library,output=(Path(p).resolve() for p in (source,library,output))
    output.mkdir(parents=True,exist_ok=True)
    metadata=json.loads((source/'.journey-atlas-surf-layout').read_bytes())
    all_trainers=metadata['surf_trainer_redesign']['trainers']
    selected=all_trainers[offset:offset+limit if limit else None]
    artifacts={n:sha(source/n) for n in ('pokeemerald.gba','pokeemerald.elf','.journey-atlas-surf-layout')}
    assert selected and len({r['map'] for r in all_trainers})==96
    ns=bootstrap(source,library,output,{r['map'] for r in selected})
    lib,s,abi,pabi=(ns[k] for k in ('lib','s','abi','pabi'))
    review_mode=bool(lib.read8(s['gJourneyReviewMode']))
    assert manual==review_mode,'Review edition requires an actual manual interaction'
    old={k:ns[k] for k in ('native','script','warp','step')}
    fixture=True;depth=0;controls=[];queries=[];captures=[];results=[]
    def step(frames,key=0):
        if not fixture and not depth:controls.append(dict(frames=frames,key=key))
        old['step'](frames,key)
    def native(function,*args,**kwargs):
        nonlocal depth
        if not fixture:
            assert ns['idle'](),'A getter cannot interrupt an active battle/script'
            assert function in {'HasTrainerBeenFought','GetMonData3'},function
            queries.append(dict(function=function,args=list(args)))
        depth+=1
        try:return old['native'](function,*args,**kwargs)
        finally:depth-=1
    def script(*args,**kwargs):
        assert fixture or depth,'Script injected after trainer departure'
        return old['script'](*args,**kwargs)
    def warp(*args,**kwargs):
        assert fixture,'Warp fixture during a trainer trip'
        return old['warp'](*args,**kwargs)
    ns.update(native=native,script=script,warp=warp,step=step)
    def flag(value):
        return bool(lib.read8(ns['save']()+ns['FLAG_OFFSET']+value//8)&(1<<(value&7)))
    def picture(label):
        ns['picture'](label);captures.append(dict(file=label+'.png',sha256=sha(output/(label+'.png'))))
    try:
        for row in all_trainers:ns['rawflag'](row['flag'],False)
        for row in selected:
            fixture=True;ns['team']([40,40,40]);native('HealPlayerParty')
            native('ScriptSetMonMoveSlot',0,332,0)  # legal Aerial Ace, no accuracy stall
            native('ScriptSetMonMoveSlot',0,57,1)
            for i in range(3):
                mon=ns['party']+i*abi[2]
                for at,value in [(pabi[8],16000),(pabi[9],10000),(pabi[21],30000),(abi[101],30000)]:
                    lib.write16(mon+at,value)
            x,y=row['tile'];dx,dy=row['delta'];start=[x+4*dx,y+4*dy]
            warp(row['map'],*start);native('SetPlayerAvatarTransitionFlags',8)
            native('DisableWildEncounters',1);step(180)
            assert ns['location']()==ns['map_id'](row['map']) and ns['position']()==tuple(start)
            assert not flag(row['flag'])
            unrelated=flag(0x500+row['id'])
            mapping=ns['maps'][row['map']]
            actor_index=next(i for i,o in enumerate(mapping['object_events']) if o.get('script')==row['script'])
            actor_id=mapping['object_events'][actor_index].get('local_id',actor_index+1)
            actors=[]
            for i in range(16):
                at=s['gObjectEvents']+36*i
                if lib.read8(at)&1 and lib.read8(at+8)==actor_id:
                    actors.append(dict(local_id=actor_id,tile=[lib.read16(at+16)-7,lib.read16(at+18)-7],
                        facing=lib.read8(at+24)&15))
            assert actors==[dict(local_id=actor_id,tile=row['tile'],facing={'DOWN':1,'UP':2,'LEFT':3,'RIGHT':4}[row['facing']])],(row,actors)
            picture(row['script']+'-before-sight-line');fixture=False
            key={(-1,0):16,(1,0):32,(0,-1):128,(0,1):64}[dx,dy]
            step(16,key);step(45)
            if manual:
                step(600)
                assert ns['idle']() and not lib.read8(s['gNoOfApproachingTrainers'])
                assert (lib.read32(s['gMain']+4)&~1) not in (s['CB2_InitBattle'],s['BattleMainCB2'])
                assert not flag(row['flag'])
                picture(row['script']+'-review-no-automatic-approach')
                step(120,key);step(45)
                assert sum(abs(a-b) for a,b in zip(ns['position'](),row['tile']))==1
                ns['press'](1)
            started=False;attacks=0;seen_species=set();first_battle=False
            for tick in range(1800):
                cb=lib.read32(s['gMain']+4)&~1
                if cb==s['BattleMainCB2']:
                    started=True
                    actual=lib.read16(s['gTrainerBattleParameter']+abi[13])
                    assert actual==row['id'],('Wrong native trainer approached',row,actual)
                    assert lib.read32(s['gBattleTypeFlags'])&abi[10]
                    if not first_battle:
                        picture(row['script']+'-native-battle');first_battle=True
                    controller=lib.read32(s['gBattlerControllerFuncs'])&~1
                    if controller in ns['actions']|ns['moves']:
                        sid=lib.read16(s['gBattleMons']+abi[74]+abi[75])
                        if sid:seen_species.add(sid)
                        assert lib.read8(s['gBattlersCount'])==2
                        step(1,64);step(8);step(1,32);step(8);ns['press'](1)
                        attacks+=controller in ns['moves']
                    else:ns['press'](2)
                elif started and cb==s['CB2_Overworld']:
                    assert lib.read8(s['gBattleOutcome'])==1
                    ns['finish']();step(120)
                    assert flag(row['flag']) and native('HasTrainerBeenFought',row['id'])
                    assert flag(0x500+row['id'])==unrelated,'Battle wrote to an unrelated system flag'
                    assert attacks and seen_species
                    break
                else:ns['press'](1)
            else:raise AssertionError(('Trainer battle did not finish',row['id'],attacks))
            assert len(seen_species)==2,('Both actual enemy species must take a battle turn',row,seen_species)
            picture(row['script']+'-native-victory')
            results.append(dict(trainer=row['id'],map=row['map'],private_flag=row['flag'],facing=row['facing'],
                start=start,native_actor=actors[0],native_sight_line_started_battle=not manual,
                native_manual_interaction_started_battle=manual,
                no_automatic_approach_after600_frames=manual,
                outcome=1,attacks=attacks,observed_battle_species=sorted(seen_species),
                private_defeat_flag_set=True,unrelated_system_flag_unchanged=True))
            print(row['script'],row['facing'],'native manual' if manual else 'native sight',
                  'battle/victory/private flag PASS',flush=True)
            (output/'partial-trainers.json').write_text(json.dumps(results,indent=2)+'\n')
        battery=output/'trainer-victories-controller-save.sav';callbacks=save_menu(ns,battery)
        assert artifacts=={n:sha(source/n) for n in artifacts}
    except BaseException:
        picture('surf-trainers-failure');raise
    finally:
        lib.stop();ns['emulator_workspace'].cleanup()
    expected={row['flag']:row in selected for row in all_trainers}
    cold=cold_boot(source,library,output/'cold-continue',battery,expected_geometry_version=8,expected_flags=expected)
    report=dict(kind='atlas-surf-trainers-native',passed=True,artifact_sha256=artifacts,cases=results,
        initial_party_progress_stats_and_per_case_placement_are_fixtures=True,
        after_departure_battles_and_save_controllers_only=True,no_battle_RAM_writes=True,
        controls=controls,queries=queries,captures=captures,save_callbacks=callbacks,
        battery=dict(file=battery.name,sha256=sha(battery)),
        current_cold_continue_preserves_private_flags=cold['bundled_save_continue_to_field'],
        review_mode=review_mode,balance_playthrough=False,full96coverage=len(results)==96,final_release_validated=False)
    (output/'surf-trainers-native.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','library','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--offset',type=int,default=0);p.add_argument('--limit',type=int)
    p.add_argument('--manual',action='store_true')
    a=p.parse_args();run(a.source,a.library,a.output,a.offset,a.limit,a.manual)
