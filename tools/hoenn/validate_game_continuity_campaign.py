"""Talk to Shelly, win the real battle and reopen the fifth gym by controls.

The initial four badges, previous required quests, other defeated trainers,
Devon Scope, party and starting placement are declared inspection fixtures.
After the placement, no player coordinates/elevation, battle outcome, defeated
flag or reward are written. The route, A interaction, battle, gift and gym
doors run through their native field/battle scripts. This is not a full campaign.
"""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
WEATHER='Route119_WeatherInstitute_2F'
GYM='FortreeCity_Gym'
SHELLY=32
WEATHER_VAR=0x40B3


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def cold_continue(source, library, output, battery, expectation):
    """Extend cold boot with read-only observations of the earned quest state."""
    path=ROOT/'tools/hoenn/validate_cold_boot.py';code=path.read_text()
    anchor="                    result = dict(bundled_save_continue_to_field=True, field_map=[lib.read8(save+4), lib.read8(save+5)])"
    assert code.count(anchor)==1
    observe='''
                    def rawflag(flag):
                        return bool(lib.read8(save+EXPECT['flag_offset']+flag//8)&(1<<(flag&7)))
                    observed_weather=lib.read16(save+EXPECT['vars_offset']+(0x40B3-0x4000)*2)
                    actor= symbols['gObjectEvents']+36*lib.read8(symbols['gPlayerAvatar']+5)
                    objects=[]
                    for i in range(16):
                        obj=symbols['gObjectEvents']+36*i
                        if lib.read8(obj)&1:
                            objects.append(dict(local_id=lib.read8(obj+8),map_id=[lib.read8(obj+10),lib.read8(obj+9)],
                                tile=[lib.read16(obj+16)-7,lib.read16(obj+18)-7]))
                    counts={str(local):sum(row['local_id']==local and row['map_id']==EXPECT['map_id'] for row in objects)
                        for local in range(1,10)}
                    assert result['field_map']==EXPECT['map_id'],result
                    assert observed_weather==2 and rawflag(0x500+32) and rawflag(EXPECT['castform_flag'])
                    assert counts['3']==0 and all(count<=1 for count in counts.values()),objects
                    assert lib.read8(symbols['gPartiesCount'])==4
                    assert not lib.read8(symbols['gPlayerAvatar'])&8
                    assert lib.read8(actor+11)&15==3
                    count_badges=lambda bank:sum(rawflag(flag) for flag in bank)
                    assert count_badges(EXPECT['hoenn_badge_flags'])==4
                    assert count_badges(EXPECT['kanto_badge_flags'])==4
                    picture('campaign-continue-no-shelly-duplicate')
                    result.update(weather_state=observed_weather,shelly_defeated=True,castform_received=True,
                        party_count=4,hoenn_badges=4,kanto_badges=4,active_objects=objects,
                        local_id_counts=counts,shelly_instances=0,no_duplicate_local_ids=True,
                        player_tile=[lib.read16(actor+16)-7,lib.read16(actor+18)-7],
                        player_elevation=3,player_surfing=False,
                        controllers_only=True,no_game_memory_writes=True,
                        no_callback_script_or_native_call_injection=True)
'''
    ns={'__file__':str(path),'__name__':'campaign_native_cold_continue','EXPECT':expectation}
    exec(compile(code.replace(anchor,anchor+observe),str(path),'exec'),ns)
    result=ns['validate'](source,library,output,battery)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--library',type=Path,required=True)
    p.add_argument('--coldboot-library',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    options=p.parse_args()
    source=options.source.resolve();output=options.output.resolve();output.mkdir(parents=True,exist_ok=True)
    before_sha,before_elf=digest(source/'pokeemerald.gba'),digest(source/'pokeemerald.elf')
    runner=ROOT/'tools/hoenn/validate_team_missions.py'
    sys.argv=[str(runner),'--source',str(source),'--library',str(options.library.resolve()),'--output',str(output)]
    ns={'__file__':str(runner),'__name__':'campaign_continuity_native'}
    exec(compile(runner.read_text().split('\nassert pending(True) == 7')[0],str(runner),'exec'),ns)
    lib,native,warp,step,press=(ns[k] for k in ('lib','native','warp','step','press'))
    rawflag,flag,flag_id=(ns[k] for k in ('rawflag','flag','flag_id'))
    captures,states,inputs=[],[],[]
    def picture(label):
        ns['picture'](label)
        captures.append(dict(file=label+'.png',sha256=digest(output/(label+'.png'))))
    def position_state(label):
        group,num=ns['location']()
        name=next(name for name in ns['names'] if ns['map_id'](name)==(group,num))
        obj=ns['s']['gObjectEvents']+36*lib.read8(ns['s']['gPlayerAvatar']+5)
        state=dict(label=label,map=name,tile=list(ns['position']()),
            elevation=lib.read8(obj+11)&15,surfing=bool(lib.read8(ns['s']['gPlayerAvatar'])&8),
            weather_state=native('VarGet',WEATHER_VAR),pending_event=native('JourneyPendingCampaignEvent',0),
            hoenn_badges=native('JourneyGymBadgeCount',0),kanto_badges=native('JourneyGymBadgeCount',1),
            shelly_defeated=flag(0x500+SHELLY),castform_received=flag(flag_id('FLAG_RECEIVED_CASTFORM')),
            capture_file=label+'.png')
        picture(label);states.append(state);return state
    def finish(limit=600):
        for _ in range(limit):
            if ns['idle']():return
            if ns['task']('Task_HandleYesNoInput'):
                step(12);press(128);press(1)
            else:press(1)
        picture('campaign-dialogue-stuck')
        raise AssertionError(('Campaign dialogue did not finish',ns['location'](),ns['position']()))
    try:
        for t in ns['stories']['trainers']:rawflag(0x500+t['id'],True)
        for trainer in range(1,1589):rawflag(0x500+trainer,trainer!=SHELLY)
        native('VarSet',WEATHER_VAR,0)
        native('VarSet',0x4072,1)  # Isolate this checkpoint from the separate Route119 rival scene.
        for name in ('FLAG_HIDE_ROUTE_119_TEAM_AQUA','FLAG_RECEIVED_CASTFORM'):
            rawflag(flag_id(name),False)
        for name in ('FLAG_RECEIVED_DEVON_SCOPE','FLAG_HIDE_FORTREE_CITY_KECLEON'):
            rawflag(flag_id(name),True)
        # Ordinary native stats and legal moves; no battle-stat or enemy writes.
        for i in range(6*ns['abi'][2]):lib.write8(ns['party']+i,0)
        lib.write8(ns['s']['gPartiesCount'],0)
        for i in range(3):
            assert native('ScriptGiveMon',382,40,0)==0
            for slot,move in enumerate((323,57,58,87)):
                native('ScriptSetMonMoveSlot',i,move,slot)
        native('HealPlayerParty');native('DisableWildEncounters',1)
        ns.update(names=['FortreeCity',GYM,'Route119','Route119_WeatherInstitute_1F',WEATHER],
            allowed=set(),walk_prefix='campaign-continuity',walk_cache_paths=True,
            walk_transition_pictures=False,walk_max_ticks=5000,finish=finish)
        exec(compile((ROOT/'tools/hoenn/native_water_walk.py').read_text(),'campaign-native-controller-walker','exec'),ns)
        walk=ns['walk']
        # Keep a pure walking graph; the story's route does not require Surf.
        for name,valid in ns['passable'].items():
            ns['passable'][name]={i for i in valid if not ns['water_behaviors'][ns['behaviors'][name][i]]}
        warp('FortreeCity',22,12);native('SetPlayerAvatarTransitionFlags',1);step(90)
        fixture_end=position_state('01-four-badges-weather-gate')
        assert fixture_end['pending_event']==15 and fixture_end['hoenn_badges']==4
        original_step=ns['step']
        def observed_step(count,key=0):
            inputs.append(dict(frames=count,key=key));original_step(count,key)
        ns['step']=observed_step
        # The same ns globals back all native helpers; only input/read functions
        # and native save calls are used once the initial placement is finished.
        step=observed_step
        for _ in range(90):
            step(1,64)
            if not ns['idle']():break
        finish()
        assert ns['location']()==ns['map_id']('FortreeCity')
        blocked=position_state('02-fifth-gym-still-blocked')
        assert blocked['pending_event']==15
        walk((WEATHER,5,6));step(60)
        group,num=ns['map_id'](WEATHER)
        script=ns['s']['Route119_WeatherInstitute_2F_EventScript_Shelly']
        visibility=native('JourneyStoryObjectVisible',script)
        actor=native('GetObjectEventIdByLocalIdAndMap',3,num,group)
        before=position_state('03-shelly-present-before-battle')
        assert visibility==1 and actor<16,(visibility,actor,before)
        assert before['weather_state']==0 and before['shelly_defeated'] is False
        # Face the actual adjacent NPC and press A; no script pointer fixture.
        step(4,32);step(30);press(1)
        battle_started=False;attacks=0;battle_frames=0;observed_trainer=None
        for _ in range(1800):
            callback=lib.read32(ns['s']['gMain']+4)&~1
            if callback==ns['s']['BattleMainCB2']:
                if not battle_started:picture('04-native-shelly-battle')
                battle_started=True;battle_frames+=1
                observed_trainer=lib.read16(ns['s']['gTrainerBattleParameter']+ns['abi'][13])
                assert observed_trainer==SHELLY
                controllers={lib.read32(ns['s']['gBattlerControllerFuncs']+4*i)&~1 for i in range(4)}
                if controllers&ns['moves']:attacks+=1;press(1)
                elif controllers&ns['actions']:press(1)
                else:press(2)
            elif battle_started and callback==ns['s']['CB2_Overworld']:
                assert lib.read8(ns['s']['gBattleOutcome'])==1
                finish();break
            else:press(1)
        else:raise AssertionError(('Shelly battle did not finish',attacks,battle_frames))
        assert battle_started and attacks>0 and flag(0x500+SHELLY)
        after=position_state('05-shelly-defeated-castform-received')
        assert after['weather_state']==1 and after['castform_received'] and after['pending_event']==0
        assert after['hoenn_badges']==4 and after['kanto_badges']==4
        count=lib.read8(ns['s']['gPartiesCount']);assert count==4
        species=[native('GetMonData2',ns['party']+i*ns['abi'][2],ns['abi'][7]) for i in range(count)]
        assert species==[382,382,382,351]
        walk(('FortreeCity',22,12));step(90)
        gate_ready=position_state('06-fifth-gym-door-unlocked')
        gate_value=native('JourneyCurrentGymGate')
        assert gate_value==0 and gate_ready['pending_event']==0,(gate_value,gate_ready)
        walk((GYM,15,23));step(60)
        entered=position_state('07-fifth-gym-entered-by-door')
        assert entered['hoenn_badges']==4 and entered['map']==GYM
        walk((WEATHER,5,8));step(60)
        revisited=position_state('08-weather-institute-revisited')
        missing=native('GetObjectEventIdByLocalIdAndMap',3,num,group)
        assert missing==16 and native('JourneyStoryObjectVisible',script)==0
        assert gate_ready['weather_state']==2 and revisited['weather_state']==2 and revisited['castform_received']
        assert native('TrySavingData',0,max_frames=6000)==1
        battery=output/'weather-quest-cleared.sav'
        lib.export_save.argtypes=[ctypes.c_char_p];lib.export_save.restype=ctypes.c_int
        assert lib.export_save(str(battery).encode()) and battery.stat().st_size==131072
        with tempfile.TemporaryDirectory(prefix='campaign-save-layout-',dir='/tmp') as tmp:
            asm=Path(tmp)/'offset.s'
            subprocess.run([str(ROOT/'.local/arm-gcc/usr/bin/arm-none-eabi-gcc'),'-S','-mabi=apcs-gnu',
                '-iquote',str(source/'include'),'-x','c','-','-o',str(asm)],
                input='#include "global.h"\n#include <stddef.h>\nconst u32 probe[]={offsetof(struct SaveBlock1,vars)};',
                text=True,check=True,capture_output=True)
            vars_offset=int(re.search(r'\.word\s+(\d+)',asm.read_text())[1])
        expectations=dict(map_id=list(ns['map_id'](WEATHER)),flag_offset=ns['FLAG_OFFSET'],vars_offset=vars_offset,
            castform_flag=flag_id('FLAG_RECEIVED_CASTFORM'),hoenn_badge_flags=ns['hoenn_flags'],kanto_badge_flags=ns['kanto_flags'])
        transitions=list(ns['transitions']);walked=ns['walked']
    finally:lib.stop()
    continued=cold_continue(source,options.coldboot_library.resolve(),output/'continue',battery,expectations)
    for label in ('fresh-title','fresh-main-menu','fresh-new-game','battery-title','battery-main-menu',
                  'battery-continued-to-field','campaign-continue-no-shelly-duplicate'):
        path=output/'continue'/(label+'.png')
        captures.append(dict(file='continue/'+path.name,sha256=digest(path)))
    assert digest(source/'pokeemerald.gba')==before_sha and digest(source/'pokeemerald.elf')==before_elf
    result=dict(kind='game-continuity-campaign',passed=True,rom_sha256=before_sha,elf_sha256=before_elf,
        compiled_rom=True,native_validation_performed=True,states=states,captures=captures,
        initial=fixture_end,blocked_gym=blocked,shelly_before=before,shelly_visibility_before=visibility,
        shelly_object_id_before=actor,shelly_after=after,shelly_object_id_on_revisit=missing,
        native_battle=dict(trainer_id=observed_trainer,outcome=1,attacks=attacks,battle_frames=battle_frames,
            actual_adjacent_A_interaction=True,no_script_entry_fixture=True,no_battle_stats_or_outcome_writes=True),
        gift_species=species,party_count_after=count,gym_ready=gate_ready,gym_entered=entered,
        revisited=revisited,transitions=transitions,walked_tiles=walked,inputs=inputs,
        battery_file=battery.name,battery_sha256=digest(battery),cold_continue=continued,
        battery_saves=[dict(file=battery.name,sha256=digest(battery),bytes=131072)],
        initial_badges_prior_quests_other_trainers_devon_scope_party_and_travel_are_fixtures=True,
        no_midtrip_player_coordinates_elevations_or_badge_writes=True,
        shelly_trainer_flag_weather_state_and_castform_reward_are_native=True,
        battle_uses_ordinary_native_stats=True,full_campaign_playthrough=False,balance_validated=False)
    (output/'game-continuity-campaign.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Shelly native battle, Castform, fifth gym doors and cold Continue passed.',flush=True)


if __name__=='__main__':main()
