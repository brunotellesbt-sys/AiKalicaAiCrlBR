"""Native history/status/PP regressions; battle state and commands are fixtures."""
from pathlib import Path
import hashlib,json,re,struct,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2]
prefix=(ROOT/'tools/hoenn/validate_pwt_world.py').read_text().split('for generation in range(cap+1):')[0]
exec(compile(prefix,str(ROOT/'tools/hoenn/validate_pwt_world.py'),'exec'))
from pwt_cup_controller import CupController
controller=CupController(source,lib,s)
with tempfile.TemporaryDirectory(dir='/tmp') as temporary:
    p=Path(temporary)
    fields=['sizeof(struct BattleStruct)','sizeof(struct BattleResources)','sizeof(struct BattleScriptsStack)',
        'sizeof(struct BattleCallbacksStack)','offsetof(struct BattleResources,battleScriptsStack)',
        'offsetof(struct BattleResources,battleCallbackStack)','sizeof(struct BattleHistory)',
        'sizeof(struct AiPartyData)','offsetof(struct BattleHistory,usedMoves)',
        'offsetof(struct BattlePokemon,volatiles)','sizeof(struct Volatiles)','MOVES_COUNT_ALL',
        'MOVE_LIMITATIONS_ALL','ABILITY_PRESSURE','B_PP_REDUCED_BY_SPITE','GEN_4','SUBMOVE_FAILURE','BATTLE_TYPE_DOUBLE']
    code='#include "global.h"\n#include "battle.h"\n#include "battle_util.h"\n#include "battle_ai_util.h"\n#include "constants/abilities.h"\n#include <stddef.h>\nconst u32 restrictions_abi[]={'+','.join(fields)+'};\n'
    code+='const struct BattleCalcValues pressure_case={.battlerAtk=0,.battlerDef=1,.move=MOVE_SURF};\n'
    code+='const struct BattleStruct submove_mask={.submoveAnnouncement=~0u};\n'
    code+='const struct BattleCalcValues copycat_case={.battlerAtk=1,.battlerDef=0,.move=MOVE_COPYCAT};\n'
    code+='const struct BattleCalcValues mefirst_case={.battlerAtk=1,.battlerDef=0,.move=MOVE_ME_FIRST};\n'
    code+='const struct BattleCalcValues struggle_case={.battlerAtk=0,.battlerDef=1,.move=MOVE_STRUGGLE};\n'
    (p/'probe.c').write_text(code)
    subprocess.run([str(ROOT/'.local/arm-gcc/usr/bin/arm-none-eabi-gcc'),'-S','-iquote',str(source/'include'),'-mabi=apcs-gnu',str(p/'probe.c'),'-o',str(p/'probe.s')],check=True)
    probe=[int(v) for v in re.findall(r'\.word\s+(\d+)',(p/'probe.s').read_text().split('restrictions_abi:',1)[1].split('.size',1)[0])]
    subprocess.run([str(ROOT/'.local/arm-binutils/usr/bin/arm-none-eabi-as'),'-mcpu=arm7tdmi','-o',str(p/'probe.o'),str(p/'probe.s')],check=True)
    subprocess.run([str(ROOT/'.local/arm-binutils/usr/bin/arm-none-eabi-objcopy'),'-O','binary','--only-section=.rodata',str(p/'probe.o'),str(p/'probe.bin')],check=True)
    names=subprocess.check_output([str(ROOT/'.local/arm-binutils/usr/bin/arm-none-eabi-nm'),'-S',str(p/'probe.o')],text=True)
    rawprobes=(p/'probe.bin').read_bytes();calc={}
    for at,size,name in re.findall(r'^(\w+) (\w+) R (pressure_case|struggle_case|copycat_case|mefirst_case|submove_mask)$',names,re.M):
        calc[name]=rawprobes[int(at,16):int(at,16)+int(size,16)]
allocated=[]
def alloc(size):
    address=native('AllocZeroed_',size,0);assert address
    allocated.append(address);return address
saved={name:lib.read32(s[name]) for name in ['gBattleStruct','gBattleResources','gBattleHistory','gAiPartyData']}
battle=alloc(probe[0]);resources=alloc(probe[1]);history=alloc(probe[6]);ai_party=alloc(probe[7])
for name,address in zip(saved,[battle,resources,history,ai_party]):lib.write32(s[name],address)
lib.write32(resources+probe[4],alloc(probe[2]));lib.write32(resources+probe[5],alloc(probe[3]))
checks=[];instruction=0x09f00600;failure=0x09f00680
def prepare(moves=(57,58,89,182),pps=(10,10,10,10)):
    lib.write32(s['gBattleControllerExecFlags'],0)
    lib.write32(s['gBattleTypeFlags'],0)
    lib.write8(s['gBattlersCount'],2);lib.write8(s['gBattlerAttacker'],1);lib.write8(s['gBattlerTarget'],0)
    lib.write8(s['gBattlerPositions'],0);lib.write8(s['gBattlerPositions']+1,1)
    lib.write8(s['gCurrentTurnActionNumber'],0)
    lib.write8(s['gBattlerByTurnOrder'],1);lib.write8(s['gBattlerByTurnOrder']+1,0)
    for battler in range(2):native('PokemonToBattleMon',party,s['gBattleMons']+battler*controller.abi[6])
    for slot,(move,pp) in enumerate(zip(moves,pps)):
        lib.write16(s['gBattleMons']+controller.abi[0]+slot*2,move)
        lib.write8(s['gBattleMons']+controller.abi[1]+slot,pp)
    for field in controller.fields:controller.set_volatile(field,0)
    lib.write16(s['gCurrentMove'],57);lib.write16(s['gLastMoves'],0);lib.write16(s['gLastPrintedMoves'],0)
    lib.write8(s['gCurrMovePos'],0);lib.write8(s['gChosenMovePos'],0)
def command(name):
    native_command=name.startswith('BS_')
    raw=b'\0'+(bytes(4) if native_command else b'')+struct.pack('<I',failure)
    for i,b in enumerate(raw):lib.raw8(instruction+i,b)
    lib.write32(s['gBattlescriptCurrInstr'],instruction);native(name)
    return lib.read32(s['gBattlescriptCurrInstr']),instruction+len(raw)
for name in ['Cmd_disablelastusedattack','Cmd_mimicattackcopy','Cmd_copymovepermanently','Cmd_tryspiteppreduce','BS_TryInstruct']:
    for last in [0,65535,probe[11]]:
        prepare();lib.write16(s['gLastMoves'],last);lib.write16(s['gLastPrintedMoves'],last)
        if name=='Cmd_copymovepermanently':
            for slot,move in enumerate([166,57,58,89]):lib.write16(s['gBattleMons']+controller.abi[6]+controller.abi[0]+slot*2,move)
        after,_=command(name);assert after==failure,(name,last,hex(after))
        checks.append(dict(case=name,last_move=last,failed_normally=True))
mask=int.from_bytes(calc['submove_mask'],'little');sub_shift=(mask&-mask).bit_length()-1
sub_offset,sub_bit=sub_shift//8,sub_shift%8
for name in ['copycat_case','mefirst_case']:
    for last in [0,65535,probe[11]]:
        prepare((last,58,89,182));lib.write16(s['gLastUsedMove'],last)
        for i,b in enumerate(calc[name]):lib.raw8(0x09f00700+i,b)
        native('CancelerCallSubmove',0x09f00700)
        assert ((lib.read8(battle+sub_offset)>>sub_bit)&3)==probe[16],(name,last)
        checks.append(dict(case=name,last_move=last,returned_no_move=True))
for name,initial_move in [('Cmd_mimicattackcopy',102),('Cmd_copymovepermanently',166)]:
    prepare();lib.write16(s['gLastMoves'],57);lib.write16(s['gLastPrintedMoves'],57)
    for slot,move in enumerate([initial_move,58,89,182]):lib.write16(s['gBattleMons']+controller.abi[6]+controller.abi[0]+slot*2,move)
    after,next_instruction=command(name);assert after==next_instruction
    assert lib.read16(s['gBattleMons']+controller.abi[6]+controller.abi[0])==57
    expected_pp=min(5,controller.database['moves'][57]['pp']) if initial_move==102 else controller.database['moves'][57]['pp']
    assert lib.read8(s['gBattleMons']+controller.abi[6]+controller.abi[1])==expected_pp
    checks.append(dict(case=name,last_move=57,copied_normally=True,resulting_pp=expected_pp))
for chosen in [57,65535]:
    prepare();lib.write16(s['gLastPrintedMoves'],57);lib.write16(s['gChosenMoveByBattler'],chosen)
    after,next_instruction=command('BS_TryInstruct');assert after==next_instruction
    checks.append(dict(case='instruct_valid_history',chosen_move=chosen,succeeded=True))
prepare(pps=(0,10,10,10));lib.write16(s['gLastPrintedMoves'],57)
assert command('BS_TryInstruct')[0]==failure
checks.append(dict(case='instruct_no_pp',failed_normally=True))
for name in ['copycat_case','mefirst_case']:
    prepare();lib.write16(s['gLastUsedMove'],57)
    for i,b in enumerate(calc[name]):lib.raw8(0x09f00700+i,b)
    native('CancelerCallSubmove',0x09f00700)
    assert lib.read16(s['gCalledMove'])==57
    assert ((lib.read8(battle+sub_offset)>>sub_bit)&3)!=probe[16],name
    checks.append(dict(case=name,last_move=57,called_valid_move=True))
prepare();lib.write16(s['gLastMoves'],57)
after,next_instruction=command('Cmd_disablelastusedattack')
assert after==next_instruction and controller.volatile('disabledMove')==57 and controller.volatile('disableTimer')>0
assert native('CheckMoveLimitations',0,0,probe[12])==1
assert command('Cmd_disablelastusedattack')[0]==failure
checks.append(dict(case='disable_active_and_repeated',blocked_slot_mask=1,repeated_disable_fails=True))
for name in ['Cmd_disablelastusedattack','Cmd_trysetencore']:
    prepare(pps=(0,10,10,10));lib.write16(s['gLastMoves'],57)
    assert command(name)[0]==failure
    checks.append(dict(case=name,last_move_pp=0,failed_normally=True))
prepare();lib.write16(s['gLastMoves'],57)
assert command('Cmd_settorment')[0]!=failure and controller.volatile('torment')
assert native('CheckMoveLimitations',0,0,probe[12])==1
assert command('Cmd_settorment')[0]==failure
controller.set_volatile('encoredMove',57);controller.set_volatile('encoreTimer',3)
assert native('CheckMoveLimitations',0,0,probe[12])==15
assert native('AreAllMovesUnusable',0)==1
assert lib.read32(s['gSelectionBattleScripts'])==s['BattleScript_NoMovesLeft']
checks.append(dict(case='encore_plus_torment',all_slots_unusable=True,native_no_moves_script=True))
for restriction in ['disable','torment','encore_other_move','no_pp']:
    prepare(pps=(0 if restriction=='no_pp' else 10,10,10,10))
    lib.write16(s['gBattleMons']+controller.abi[9],controller.abi[11])
    lib.write16(battle+controller.abi[10],57)
    if restriction=='disable':controller.set_volatile('disabledMove',57)
    elif restriction=='torment':
        controller.set_volatile('torment',1);lib.write16(s['gLastMoves'],57)
    elif restriction=='encore_other_move':
        controller.set_volatile('encoredMove',58);controller.set_volatile('encoreTimer',3)
    assert native('CheckMoveLimitations',0,0,probe[12])==15,restriction
    assert native('AreAllMovesUnusable',0)==1
    checks.append(dict(case='choice_item_combination',restriction=restriction,native_no_moves_script=True))
prepare(pps=(0,0,0,0));assert native('CheckMoveLimitations',0,0,probe[12])==15
assert native('AreAllMovesUnusable',0)==1
checks.append(dict(case='all_pp_exhausted',all_slots_unusable=True))
prepare((65535,58,89,182));assert native('CheckMoveLimitations',0,0,probe[12])==1
checks.append(dict(case='invalid_move_slot',slot_blocked_without_assertion=True))
assert probe[14]>=probe[15]
for pp in [1,2,4,5]:
    prepare(pps=(pp,10,10,10));lib.write16(s['gLastMoves'],57)
    after,next_instruction=command('Cmd_tryspiteppreduce');assert after==next_instruction
    assert lib.read8(s['gBattleMons']+controller.abi[1])==max(0,pp-4)
    checks.append(dict(case='spite_pp',before=pp,after=max(0,pp-4)))
for use_pressure in [False,True]:
    for pp in [0,1,2,3]:
        prepare(pps=(pp,10,10,10));lib.write8(s['gBattlerAttacker'],0);lib.write8(s['gBattlerTarget'],1)
        lib.write16(s['gBattleMons']+controller.abi[6]+controller.abi[7],probe[13] if use_pressure else 0)
        for i,b in enumerate(calc['pressure_case']):lib.raw8(0x09f00700+i,b)
        native('CancelerPPDeduction',0x09f00700)
        expected=max(0,pp-(2 if use_pressure else 1))
        assert lib.read8(s['gBattleMons']+controller.abi[1])==expected,(use_pressure,pp)
        checks.append(dict(case='move_pp_pressure',pressure=use_pressure,before=pp,after=expected))
for pp in [0,1,2,3,4]:
    prepare(pps=(pp,10,10,10));lib.write8(s['gBattlersCount'],4);lib.write32(s['gBattleTypeFlags'],probe[17])
    for battler in [2,3]:
        lib.write8(s['gBattlerPositions']+battler,battler)
        native('PokemonToBattleMon',party,s['gBattleMons']+battler*controller.abi[6])
    for battler in [1,3]:lib.write16(s['gBattleMons']+battler*controller.abi[6]+controller.abi[7],probe[13])
    for i,b in enumerate(calc['pressure_case']):lib.raw8(0x09f00700+i,b)
    native('CancelerPPDeduction',0x09f00700)
    expected=max(0,pp-3);assert lib.read8(s['gBattleMons']+controller.abi[1])==expected,(pp,lib.read8(s['gBattleMons']+controller.abi[1]),expected)
    checks.append(dict(case='spread_move_two_pressure_opponents',before=pp,after=expected))
prepare(pps=(0,10,10,10));lib.write16(s['gLastMoves'],57)
assert command('Cmd_tryspiteppreduce')[0]==failure
checks.append(dict(case='spite_no_pp',failed_normally=True,pp_stays_zero=True))
prepare(pps=(1,10,10,10))
for i,b in enumerate(calc['struggle_case']):lib.raw8(0x09f00700+i,b)
native('CancelerPPDeduction',0x09f00700)
assert lib.read8(s['gBattleMons']+controller.abi[1])==1
checks.append(dict(case='struggle_has_no_pp_cost',pp_preserved=True))
for reason in ['pp_exhausted','move_removed','timer_expired']:
    prepare(pps=(0 if reason=='pp_exhausted' else 10,10,10,10))
    controller.set_volatile('encoredMove',57 if reason!='move_removed' else 85)
    controller.set_volatile('encoreTimer',1 if reason=='timer_expired' else 3)
    native('HandleEndTurnEncore',0)
    assert not controller.volatile('encoreTimer') and not controller.volatile('encoredMove')
    checks.append(dict(case='encore_end',reason=reason,cleared=True))
for reason in ['move_removed','timer_expired']:
    prepare();controller.set_volatile('disabledMove',85 if reason=='move_removed' else 57)
    controller.set_volatile('disableTimer',3 if reason=='move_removed' else 1)
    native('HandleEndTurnDisable',0)
    assert not controller.volatile('disabledMove') and not controller.volatile('disableTimer')
    checks.append(dict(case='disable_end',reason=reason,cleared=True))
prepare();controller.set_volatile('torment',1);controller.set_volatile('tormentTimer',1)
native('HandleEndTurnTorment',0);assert not controller.volatile('torment')
checks.append(dict(case='torment_end',cleared=True))
prepare();controller.set_volatile('disabledMove',57);controller.set_volatile('disableTimer',3)
controller.set_volatile('encoredMove',57);controller.set_volatile('encoreTimer',3);controller.set_volatile('torment',1)
lib.write16(s['gLastMoves'],57)
copy=alloc(probe[10]);volatile_start=s['gBattleMons']+probe[9]
for i in range(probe[10]):lib.write8(copy+i,lib.read8(volatile_start+i))
native('SwitchInClearSetData',0,copy)
assert not any(controller.volatile(f) for f in ['disabledMove','disableTimer','encoredMove','encoreTimer','torment'])
assert lib.read16(s['gLastMoves'])==0
checks.append(dict(case='normal_switch',restrictions_and_history_cleared=True))
prepare((57,487,89,65535));native('RecordMovesBasedOnStab',0)
recorded=[lib.read16(history+probe[8]+slot*2) for slot in range(4)]
assert recorded==[57,0,89,0],recorded
checks.append(dict(case='ai_stab_recording',recorded_moves=recorded,status_and_invalid_moves_excluded=True))
for name,value in saved.items():lib.write32(s[name],value)
for address in reversed(allocated):native('Free',address)
lib.stop()
(args.output/'move-restrictions.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),cases=len(checks),checks=checks,native_engine_functions=True,battle_state_and_script_arguments_are_fixtures=True),indent=2)+'\n')
print('Native move restrictions passed:',len(checks),'cases',flush=True)
