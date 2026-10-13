"""Exercise native player stone, held-item, trade-replacement and regional targets.

Party/levels/items are fixtures. Target selection executes the real six-argument
evolution function. Evolution animations and stone consumption are not tested.
"""
import hashlib,json,re,struct,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
prefix=(ROOT/'tools/hoenn/validate_world_map.py').read_text().split('\nchecks=[]')[0]
exec(compile(prefix,str(ROOT/'tools/hoenn/validate_world_map.py'),'exec'))
sha=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest()
names=['EVO_MODE_NORMAL','EVO_MODE_ITEM_CHECK','CHECK_EVO','ITEM_THUNDER_STONE','ITEM_METAL_COAT',
       'MON_DATA_HELD_ITEM','VAR_UNUSED_0x404E','ITEM_MYSTIC_WATER','SPECIES_RAICHU_ALOLA',
       'SPECIES_PAWMO','SPECIES_PAWMOT',
       'SPECIES_GIMMIGHOUL','SPECIES_GHOLDENGO','sizeof(struct Pokemon)']
with tempfile.TemporaryDirectory(dir='/tmp') as temp:
    p=Path(temp)
    code='#include "global.h"\n#include "pokemon.h"\n#include "constants/items.h"\n#include "constants/vars.h"\n#include "constants/species.h"\nconst u32 probe[]={'+','.join(names)+'};'
    subprocess.run([str(ROOT/'.local/arm-gcc/usr/bin/arm-none-eabi-gcc'),'-S','-mabi=apcs-gnu','-iquote',str(source/'include'),'-x','c','-','-o',str(p/'probe.s')],input=code,text=True,check=True)
    values={n:int(v) for n,v in zip(names,re.findall(r'\.word\s+(\d+)',(p/'probe.s').read_text()))}
    stop=s['gStringVar4']+880;result=stop+8
    assembly='''.syntax unified
.thumb
.section .text
.global evo_fixture
.thumb_func
evo_fixture:
 push {r4,lr}
 sub sp,#8
 ldr r4,stop
 str r4,[sp]
 movs r4,#0
 str r4,[sp,#4]
 ldr r0,mon
 ldr r1,mode
 ldr r2,item
 movs r3,#0
 ldr r4,target
 bl call
 add sp,#8
 ldr r1,result
 str r0,[r1]
 pop {r4,pc}
call: bx r4
.balign 4
mon: .word 0x11111111
mode: .word 0x22222222
item: .word 0x33333333
target: .word 0x44444444
stop: .word 0x55555555
result: .word 0x66666666
'''
    (p/'call.s').write_text(assembly)
    subprocess.run([str(ROOT/'.local/arm-binutils/usr/bin/arm-none-eabi-as'),'-mthumb','-march=armv4t',str(p/'call.s'),'-o',str(p/'call.o')],check=True)
    subprocess.run([str(ROOT/'.local/arm-binutils/usr/bin/arm-none-eabi-objcopy'),'-O','binary','-j','.text',str(p/'call.o'),str(p/'call.bin')],check=True)
    stub=(p/'call.bin').read_bytes()

def target(species,level,mode='EVO_MODE_NORMAL',item=0,held=0,region=0):
    for index in range(6*values['sizeof(struct Pokemon)']):lib.write8(s['gParties']+index,0)
    lib.write8(s['gPartiesCount'],0)
    assert native('ScriptGiveMon',species,level,held)==0
    assert native('GetMonData2',s['gParties'],abi[7])==species
    native('VarSet',values['VAR_UNUSED_0x404E'],region)
    code=bytearray(stub)
    for marker,value in zip(range(1,7),[s['gParties'],values[mode],item,s['GetEvolutionTargetSpecies']|1,stop,result]):
        sentinel=marker*0x11111111;struct.pack_into('<I',code,code.index(struct.pack('<I',sentinel)),value)
    for index,byte in enumerate(code):lib.raw8(0x09f00400+index,byte)
    lib.write32(stop,0);lib.write32(result,0xDEADC0DE)
    hook=s['gSpecials'];original=lib.read32(hook);raw32(hook,0x09f00401)
    try:
        script(b'\x25\x00\x00\x6b\x02',8)
        for _ in range(200):
            if lib.read8(s['sGlobalScriptContextStatus'])==2:break
            step(1)
        assert lib.read32(result)!=0xDEADC0DE
        return lib.read32(result)
    finally:raw32(hook,original)

cases=[('early Thunder Stone',25,5,'EVO_MODE_ITEM_CHECK',values['ITEM_THUNDER_STONE'],0,0,26),
 ('Alola Thunder Stone',25,5,'EVO_MODE_ITEM_CHECK',values['ITEM_THUNDER_STONE'],0,1,values['SPECIES_RAICHU_ALOLA']),
 ('Kadabra before 36',64,35,'EVO_MODE_NORMAL',0,0,0,0),('Kadabra at 36',64,36,'EVO_MODE_NORMAL',0,0,0,65),
 ('Onix before 30',95,29,'EVO_MODE_NORMAL',0,values['ITEM_METAL_COAT'],0,0),
 ('Onix at 30 with coat',95,30,'EVO_MODE_NORMAL',0,values['ITEM_METAL_COAT'],0,208),
 ('Pawmo at 36',values['SPECIES_PAWMO'],36,'EVO_MODE_NORMAL',0,0,0,values['SPECIES_PAWMOT']),
 ('Gimmighoul at 36',values['SPECIES_GIMMIGHOUL'],36,'EVO_MODE_NORMAL',0,0,0,values['SPECIES_GHOLDENGO'])]
checks=[]
for label,species,level,mode,item,held,region,expected in cases:
    found=target(species,level,mode,item,held,region);assert found==expected,(label,found,expected)
    checks.append(dict(label=label,species=species,level=level,target=found));print('Player evolution:',label,'passed',flush=True)
assert hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest()==sha
lib.stop()
(args.output/'player-evolutions.json').write_text(json.dumps(dict(passed=True,rom_sha256=sha,checks=checks,
    native_six_argument_target_function=True,initial_party_and_items_are_fixtures=True,
    animation_and_consumption_tested=False),indent=2)+'\n')
