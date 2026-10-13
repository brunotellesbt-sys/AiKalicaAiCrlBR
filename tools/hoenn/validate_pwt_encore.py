"""Exercise native Encore with empty/invalid history and a valid prior move."""
from pathlib import Path
import hashlib,json,re,struct,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2]
prefix=(ROOT/'tools/hoenn/validate_pwt_world.py').read_text().split('for generation in range(cap+1):')[0]
exec(compile(prefix,str(ROOT/'tools/hoenn/validate_pwt_world.py'),'exec'))
from pwt_cup_controller import CupController
controller=CupController(source,lib,s)
with tempfile.TemporaryDirectory(dir='/tmp') as d:
    out=Path(d)/'encore.s'
    code='#include "global.h"\n#include "battle.h"\nconst u32 encore_abi[]={sizeof(struct BattleStruct),MOVES_COUNT_ALL};'
    subprocess.run([str(ROOT/'.local/arm-gcc/usr/bin/arm-none-eabi-gcc'),'-S','-iquote',str(source/'include'),'-mabi=apcs-gnu','-x','c','-','-o',str(out)],input=code,text=True,check=True)
    size,count=map(int,re.findall(r'\.word\s+(\d+)',out.read_text().split('encore_abi:',1)[1].split('.size',1)[0]))
allocated=native('AllocZeroed_',size,0);assert allocated
old=lib.read32(s['gBattleStruct']);lib.write32(s['gBattleStruct'],allocated)
lib.write8(s['gBattlerTarget'],0);lib.write8(s['gBattlerAttacker'],1);lib.write8(s['gBattlersCount'],2)
native('PokemonToBattleMon',party,s['gBattleMons'])
instruction=0x09f00600;failure=0x09f00640
for i,b in enumerate(b'\0'+struct.pack('<I',failure)):lib.raw8(instruction+i,b)
checks=[]
for move in [0,65535,count]:
    lib.write16(s['gLastMoves'],move);lib.write32(s['gBattlescriptCurrInstr'],instruction)
    native('Cmd_trysetencore')
    assert lib.read32(s['gBattlescriptCurrInstr'])==failure,(move,'Encore did not fail normally')
    checks.append(dict(last_move=move,failed_normally=True,invalid_move_assertion=False))
for chosen in [57,65535]:
    lib.write16(s['gLastMoves'],57);lib.write16(s['gChosenMoveByBattler'],chosen)
    for slot in range(4):
        lib.write16(s['gBattleMons']+controller.abi[0]+slot*2,57)
        lib.write8(s['gBattleMons']+controller.abi[1]+slot,10)
    # Clear just the encored move/timer through their compiled bit masks.
    for field in ['encoredMove','encoreTimer']:
        off,shift,mask,length=controller.fields[field]
        at=s['gBattleMons']+off
        value=int.from_bytes(bytes(lib.read8(at+i) for i in range(length)),'little')&~(mask<<shift)
        for i,b in enumerate(value.to_bytes(length,'little')):lib.write8(at+i,b)
    lib.write32(s['gBattlescriptCurrInstr'],instruction);native('Cmd_trysetencore')
    assert lib.read32(s['gBattlescriptCurrInstr'])==instruction+5
    assert controller.volatile('encoredMove')==57 and controller.volatile('encoreTimer')>0
    checks.append(dict(last_move=57,chosen_move=chosen,encore_applied=True))
lib.write32(s['gBattleStruct'],old);native('Free',allocated);lib.stop()
(args.output/'pwt-encore.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),checks=checks,no_history_fails_without_crashing=True,valid_encore_preserved=True,invalid_chosen_move_sentinel_safe=True,battle_state_and_script_arguments_are_fixtures=True),indent=2)+'\n')
print('Native Encore regression passed',flush=True)
