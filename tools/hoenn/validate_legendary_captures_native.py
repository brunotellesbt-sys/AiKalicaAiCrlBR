"""Interact, reject incomplete badges, catch real species, SAVE and cold Continue.

Each room/progress/party/bag placement is an explicit fixture. The challenge,
Master Ball use, disappearance and SAVE receive controller input only.
"""
import argparse
import hashlib
import json
from pathlib import Path

from battle_interaction_fixture import compile_probe
from validate_atlas_candidate_batteries_native import save_menu
from validate_coast_scenery_objects import bootstrap
from validate_cold_boot import validate as cold_boot


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(source,library,output,nationals=(144,487,1025)):
    source,library,output=(Path(p).resolve() for p in (source,library,output));output.mkdir(parents=True,exist_ok=True)
    meta=json.loads((source/'.journey-atlas-surf-layout').read_bytes())
    rooms=[r for r in meta['legendary_individual_chambers']['rooms'] if r['national_dex'] in nationals]
    layout,values,_=compile_probe(source,{'ITEM_MASTER_BALL','FLAG_GET_CAUGHT','POCKET_POKE_BALLS','MON_DATA_SPECIES','B_OUTCOME_CAUGHT',
        *[r['species'] for r in rooms],*[r['flag'] for r in rooms]})
    artifacts={n:sha(source/n) for n in ('pokeemerald.gba','pokeemerald.elf','.journey-atlas-surf-layout')};results=[]
    for room in rooms:
        folder=output/str(room['national_dex']);folder.mkdir(exist_ok=True)
        ns=bootstrap(source,library,folder,[room['room']]);lib,s,abi=(ns[k] for k in ('lib','s','abi'))
        original={k:ns[k] for k in ('native','step','script','warp')}
        fixture=True;depth=0;controls=[];queries=[];captures=[]
        def step(frames,key=0):
            if not fixture and not depth:controls.append(dict(frames=frames,key=key))
            original['step'](frames,key)
        def native(function,*args,**kwargs):
            nonlocal depth
            if not fixture:
                assert ns['idle'](),'Native query during a dialog/battle'
                assert function in {'JourneySpecialUnlocked','FlagGet','GetSetPokedexFlag','GetMonData2','CheckBagHasItem'}
                if function=='GetSetPokedexFlag':assert args[1]==values['FLAG_GET_CAUGHT']
                queries.append(dict(function=function,args=list(args)))
            depth+=1
            try:return original['native'](function,*args,**kwargs)
            finally:depth-=1
        def script(*args,**kwargs):
            assert fixture or depth,'Script injected during capture';return original['script'](*args,**kwargs)
        def warp(*args,**kwargs):
            assert fixture,'Warp during capture';return original['warp'](*args,**kwargs)
        ns.update(native=native,step=step,script=script,warp=warp)
        def picture(label):
            ns['picture'](label);captures.append(dict(file=label+'.png',sha256=sha(folder/(label+'.png'))))
        def cb():return lib.read32(s['gMain']+4)&~1
        def actors():
            return [i for i in range(16) if lib.read8(s['gObjectEvents']+36*i)&1 and lib.read8(s['gObjectEvents']+36*i+8)==1]
        def place(hoenn_badges):
            nonlocal fixture
            fixture=True;native('VarSet',0x40DC,8);native('ZeroPlayerPartyMons');native('ScriptGiveMon',150,80,0)
            native('ClearBag');native('AddBagItem',values['ITEM_MASTER_BALL'],1);native('SetDexPokemonPokenavFlags')
            native('FlagClear',values[room['flag']]);native('DisableWildEncounters',1)
            for flag in ns['kanto_flags']:ns['rawflag'](flag,True)
            for i,flag in enumerate(ns['hoenn_flags']):ns['rawflag'](flag,i<hoenn_badges)
            x,y=room['position'];warp(room['room'],x,y+1);native('SetPlayerAvatarTransitionFlags',1);step(180)
            assert ns['position']()==(x,y+1) and actors()
            fixture=False
        def talk():step(1,64);step(15);ns['press'](1)
        try:
            place(7);talk();battle=False
            for _ in range(30):
                battle|=cb() in (s['CB2_InitBattle'],s['BattleMainCB2'])
                ns['press'](1)
                if ns['idle']():break
            assert not battle and ns['idle']() and not native('JourneySpecialUnlocked')
            assert not native('FlagGet',values[room['flag']]);picture('locked-with15-badges')
            place(8);assert native('JourneySpecialUnlocked');talk()
            for _ in range(220):
                if cb()==s['BattleMainCB2'] and (lib.read32(s['gBattlerControllerFuncs'])&~1) in ns['actions']:break
                ns['press'](2 if cb()==s['BattleMainCB2'] else 1)
            else:raise AssertionError('Physical legendary interaction did not start a battle')
            assert lib.read16(s['gBattleMons']+abi[74]+abi[75])==values[room['species']]
            assert not lib.read32(s['gBattleTypeFlags'])&abi[10];picture('actual-species-battle')
            step(1,64);step(10);step(1,32);step(10);step(1,16);step(10)
            assert lib.read8(s['gActionSelectionCursor'])==1;ns['press'](1);step(150)
            for _ in range(80):
                if ns['task']('Task_BagMenu_HandleInput'):break
                step(8)
            else:raise AssertionError('Native battle bag did not open')
            for _ in range(6):
                if lib.read8(s['gBagPosition']+layout['bag_pocket'])==values['POCKET_POKE_BALLS']:break
                ns['press'](16);step(120)
            assert lib.read8(s['gBagPosition']+layout['bag_pocket'])==values['POCKET_POKE_BALLS']
            ns['press'](1);step(60);ns['press'](1);step(350)
            for _ in range(250):
                if cb()==s['CB2_Overworld'] and ns['idle']():break
                ns['press'](2)
            else:raise AssertionError('Capture did not return to the field')
            step(180)
            assert lib.read8(s['gBattleOutcome'])==values['B_OUTCOME_CAUGHT']
            assert native('GetSetPokedexFlag',room['national_dex'],values['FLAG_GET_CAUGHT'])
            assert native('FlagGet',values[room['flag']]) and not actors()
            assert not native('CheckBagHasItem',values['ITEM_MASTER_BALL'],1)
            assert lib.read8(s['gPartiesCount'])==2
            assert native('GetMonData2',s['gParties']+abi[2],values['MON_DATA_SPECIES'])==values[room['species']]
            picture('caught-and-own-actor-removed')
            battery=folder/'actual-capture-controller-save.sav';callbacks=save_menu(ns,battery)
            raw=bytes(lib.read8(s['gParties']+i) for i in range(2*abi[2]));party_sha=hashlib.sha256(raw).hexdigest()
        except BaseException:picture('capture-failure');raise
        finally:lib.stop();ns['emulator_workspace'].cleanup()
        continued=cold_boot(source,library,folder/'cold-continue',battery,expected_geometry_version=8,
            expected_flags={values[room['flag']]:True},verify_current_map_objects=True,expected_party_sha256=party_sha)
        current=continued['runs'][-1];assert not current['native_object_templates']['active_current_map_objects']
        results.append(dict(national_dex=room['national_dex'],room=room['room'],species=room['species'],flag=values[room['flag']],
            locked_with15_badges=True,real_challenge_and_master_ball_capture=True,native_caught_outcome=values['B_OUTCOME_CAUGHT'],
            own_actor_removed=True,master_ball_consumed=True,captured_party_sha256=party_sha,
            native_SAVE_and_cold_Continue_preserve_actual_party_and_catch_flag=True,
            battery=dict(file=battery.relative_to(output).as_posix(),sha256=sha(battery)),
            save_callbacks=callbacks,controls=controls,queries=queries,captures=captures))
        print(room['national_dex'],'physical challenge/capture/removal/SAVE/cold party PASS',flush=True)
    assert artifacts=={n:sha(source/n) for n in artifacts}
    report=dict(kind='legendary-chambers-native-captures',passed=True,artifact_sha256=artifacts,cases=results,
        initial_room_party_bag_and_badge_progress_per_phase_are_fixtures=True,
        after_placement_interactions_battle_and_SAVE_controllers_only=True,all105_captures_claimed=False,
        final_release_validated=False)
    (output/'legendary-captures-native.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','library','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--national',type=int,action='append')
    a=p.parse_args();run(a.source,a.library,a.output,a.national or (144,487,1025))
