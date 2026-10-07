#!/usr/bin/env python3
"""Validate journey choices, physical room warps, visitors, gifts and story state in mGBA."""
import argparse
import ctypes
import json
from pathlib import Path
import struct
import zlib
from prepare import ROOT

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--library',type=Path,required=True)
p.add_argument('--directory',type=Path,default=ROOT/'mods/unova-catalog')
p.add_argument('--rom-name',default='LeafGreen-Journey-Unova')
p.add_argument('--output',type=Path,default=ROOT/'mods/unova-catalog/validation')
args=p.parse_args();args.output.mkdir(parents=True,exist_ok=True)
(args.output/'results.json').unlink(missing_ok=True)
directory=args.directory
ref=json.loads((directory/'debug-reference.json').read_text());s=ref['symbols'];abi=ref['layout']
lib=ctypes.CDLL(str(args.library.resolve()));lib.start.argtypes=[ctypes.c_char_p];lib.image.restype=ctypes.c_void_p;lib.read32.restype=ctypes.c_uint32
assert lib.start(str(directory/(args.rom_name+'.gba')).encode())
results=[]

def step(n,keys=0):lib.frames(n,keys)
def tap(keys):step(2,keys);step(40)
def save():return lib.read32(s['gSaveBlock1Ptr'])
def var(id):return lib.read16(save()+abi['save_vars']+(id-0x4000)*2)
def setvar(id,value):lib.write16(save()+abi['save_vars']+(id-0x4000)*2,value)
def flag(id):return bool(lib.read8(save()+abi['save_flags']+id//8)&(1<<(id%8)))
def setflag(id,value):
    addr=save()+abi['save_flags']+id//8;bit=1<<(id%8);old=lib.read8(addr)
    lib.write8(addr,old|bit if value else old&~bit)
def location():return lib.read8(save()+4),lib.read8(save()+5)
def map_id(name):return next((g,n) for g,names in enumerate(ref['groups']) for n,v in enumerate(names) if v==name)
def position():
    obj=s['gObjectEvents']+lib.read8(s['gPlayerAvatar']+5)*36
    return lib.read16(obj+16)-7,lib.read16(obj+18)-7

def screenshot(name):
    data=ctypes.string_at(lib.image(),240*160*4)
    raw=b''.join(b'\0'+bytes(v for i,v in enumerate(data[y*960:(y+1)*960]) if i%4!=3) for y in range(160))
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data))
    (args.output/(name+'.png')).write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',240,160,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b''))

def script(code,wait=900):
    for i,value in enumerate(code):lib.raw8(0x09f00000+i,value)
    context=s['sGlobalScriptContext']
    for i in range(116):lib.write8(context+i,0)
    lib.write8(context+1,1);lib.write32(context+8,0x09f00000)
    lib.write32(context+92,s['gScriptCmdTable']);lib.write32(context+96,s['gScriptCmdTableEnd'])
    lib.write8(s['sGlobalScriptContextStatus'],0);lib.write8(s['sLockFieldControls'],1)
    step(wait)

def special(name):return b'\x25'+struct.pack('<H',ref['specials'][name])
def warp(name,x,y):
    group,number=map_id(name)
    script(b'\x39'+bytes([group,number,255])+struct.pack('<HH',x,y)+b'\x27\x6b\x02')

def drain():
    for _ in range(180):
        if lib.read8(s['sGlobalScriptContextStatus'])==2 and not lib.read8(s['sLockFieldControls']):return
        tap(1)
    raise AssertionError('Dialogue did not release controls')

def objects():
    return {lib.read8(s['gObjectEvents']+i*36+8):lib.read16(s['gObjectEvents']+i*36+4) for i in range(16) if lib.read8(s['gObjectEvents']+i*36)&1}
def tm_slots():return []
def species():
    mon=s['gPlayerParty'];personality=lib.read32(mon);key=personality^lib.read32(mon+4)
    growth=[0,0,0,0,0,0,1,1,2,3,2,3,1,1,2,3,2,3,1,1,2,3,2,3][personality%24]
    return (lib.read32(mon+32+growth*12)^key)&65535

def record(name,**detail):results.append({'check':name,'passed':True,**detail})

stub=bytes.fromhex('00b505480549064a064b00f003f80649086000bd1847c0461111111122222222333333334444444455555555')
hook=s['gSpecials']+ref['specials']['JourneyFamilyInfo']*4
scratch=s['gStringVar4']+960

def raw32(addr,value):
    for i,b in enumerate(struct.pack('<I',value)):lib.raw8(addr+i,b)

def native(name,*args):
    code=bytearray(stub)
    values=[*(list(args)+[0]*3)[:3],s[name]|1,scratch]
    for sentinel,value in zip([0x11111111,0x22222222,0x33333333,0x44444444,0x55555555],values):
        struct.pack_into('<I',code,code.index(struct.pack('<I',sentinel)),value)
    for i,b in enumerate(code):lib.raw8(0x09f00200+i,b)
    lib.write32(scratch,0xdeadc0de)
    original=lib.read32(hook);raw32(hook,0x09f00201)
    script(special('JourneyFamilyInfo')+b'\x6b\x02',3)
    for _ in range(200):
        if lib.read32(scratch)!=0xdeadc0de:break
        step(1)
    raw32(hook,original)
    assert lib.read32(scratch)!=0xdeadc0de,('Native call did not finish',name,args)
    return lib.read32(scratch)

# Initialize through the real game's new-game function after its normal introduction.
step(180)
for _ in range(12):step(10,8);step(120)
lib.write8(save()+abi['rival_name'],255);lib.write8(lib.read32(s['gSaveBlock2Ptr']),255)
lib.write32(s['gMain'],0);lib.write8(s['gMain']+abi['main_state'],0);lib.write32(s['gMain']+4,s['CB2_NewGame']|1)
step(300);tap(1);screenshot('city-selection')
tap(128);tap(128);tap(1)
for _ in range(5):tap(1)
step(900)
assert var(0x40cb)==5
home=ref['homes'][var(0x40cc)-1]
assert location()==map_id('JourneyBedroom'+str(home['index']-1).zfill(2))
screenshot('born-in-bedroom')
record('real-city-menu-and-fixed-birth',city=home['city'],house=home['house'])
print('Boot/menu passed',flush=True)

# The original bedroom staircase reaches the selected home physically.
step(64,16);step(20);step(80,64);step(900);step(8,32);step(900)
assert location()==map_id(home['house']),location()
assert objects().get(10)==71 and objects().get(11)==157,objects()
screenshot('family-professor-and-case')
record('physical-bedroom-staircase-and-visitors')
warp(home['house'],4,5);tap(64);tap(1);step(40)
drain();step(300)
assert lib.read8(s['gPlayerPartyCount'])==1
assert native('GetMonData2',s['gPlayerParty'],abi['mon_data_species'])==1
assert lib.read8(s['gPlayerParty']+abi['pokemon_level'])==5
assert flag(0x828) and flag(0x829) and flag(0x8e1) and var(0x40ce)==2
assert 10 not in objects() and 11 not in objects()
screenshot('starter-and-pokedex-received')
record('real-oak-dialogue-starter-dex-and-departure')
for person in range(home['people']):
    lib.write16(s['gSpecialVar_LastTalked'],person+1)
    script(special('JourneyGiveGift')+b'\x6b\x02',30)
assert native('CheckBagHasItem',684,1) and native('CheckBagHasItem',688,1)
for item in [703,292,293]:assert not native('CheckBagHasItem',item,1)
record('family-hms-and-mega-items-not-distributed')
# Real mother script reuses the vanilla party healing event.
lib.write16(s['gPlayerParty']+86,1)
warp(home['house'],9,4);tap(32);tap(1);drain()
assert lib.read16(s['gPlayerParty']+86)==lib.read16(s['gPlayerParty']+88)
screenshot('mother-heals-party')
record('mother-vanilla-healing')
warp(home['house'],10,3);assert 10 not in objects() and 11 not in objects()
record('visitors-stay-gone-after-return')
warp(home['house'],4,7);step(28,128);step(900)
assert location()==map_id('VermilionCity')
record('front-door-opens-to-chosen-city-after-starter')
warp('PalletTown_ProfessorOaksLab',5,4)
assert not flag(0x2b) and 4 in objects() and objects()[4]==71
record('oak-back-in-laboratory')
# Exercise every alternative house and each household size independently.
for home in ref['homes'][1:]:
    index=home['index'];city=next(i+1 for i,c in enumerate(json.loads((ROOT/'tools/journey/homes.json').read_text())['cities']) if c['name']==home['city'])
    setvar(0x40cb,city);setvar(0x40cc,index);setvar(0x40cd,0);setvar(0x40ce,1);setflag(0x8e1,False)
    warp('JourneyBedroom'+str(index-1).zfill(2),10,2);step(8,32);step(900)
    assert location()==map_id(home['house']) and objects().get(10)==71 and objects().get(11)==157
    assert all(person+1 in objects() for person in range(home['people']))
    for person in range(home['people']):
        lib.write16(s['gSpecialVar_LastTalked'],person+1)
        script(special('JourneyGiveGift')+b'\x6b\x02',30)
    assert var(0x40cd)&3==3
    record('house-bedroom-family-and-gifts',house=home['house'],people=home['people'])
    setvar(0x40ce,2)
    warp(home['house'],4,7);step(28,128);step(900)
    outside_name=home['house'].split('_')[0]
    assert location()==map_id(outside_name),(home['house'],location(),outside_name)
    record('fixed-home-front-door-to-settlement',house=home['house'],outside=outside_name)

# Give all starter choices and verify species, level and rival's canonical starter variable.
for choice,expected,starter_var in [(0,1,0),(1,4,2),(2,7,1)]:
    setflag(0x8e1,False);lib.write8(s['gPlayerPartyCount'],0);lib.write8(save()+0x34,0)
    for byte in range(600):lib.write8(s['gPlayerParty']+byte,0)
    lib.write16(s['gSpecialVar_Result'],choice)
    script(special('JourneyGiveStarter')+b'\x6b\x02',30)
    assert native('GetMonData2',s['gPlayerParty'],abi['mon_data_species'])==expected and var(0x4031)==starter_var and lib.read8(s['gPlayerParty']+84)==5, (choice,var(0x4031),lib.read8(s['gPlayerParty']+84))
    record('starter-choice',species=expected,rival_starter_var=starter_var)
# Teach a compatible starter only in the test, then exercise both field actions
# with every badge flag unset. The distributed game still requires teaching HMs.
native('ScriptSetMonMoveSlot',0,57,0);native('ScriptSetMonMoveSlot',0,127,1)
assert all(not flag(id) for id in range(0x820,0x828))
warp('PalletTown',10,16);tap(128);tap(1);drain();step(180)
assert lib.read8(s['gPlayerAvatar'])&8
screenshot('surf-without-badges')
record('surf-usable-without-badges')
import sys
sys.path.insert(0,str(ROOT/'tools/rom_hacks'))
from remove_hm_walls import Maps, REFERENCE
original=Maps((ROOT/'Pokemon - Leaf Green Version (U) (V1.1).gba').read_bytes(),json.loads(REFERENCE.read_text()))
header=next(h for name,_,_,h in original.headers() if name=='FourIsland_IcefallCave_Entrance')
layout=original.ptr(header);width,height=original.u32(layout),original.u32(layout+4);blocks=original.ptr(layout+12)
def behavior(x,y):
    tile=original.u16(blocks+(y*width+x)*2)&1023
    return original.u32(original.attributes(layout,tile))&511
x,y=next((x,y) for y in range(height-1) for x in range(width) if behavior(x,y)==0x13 and behavior(x,y+1)==0x10)
warp('FourIsland_IcefallCave_Entrance',x,y+1)
script(special('ForcePlayerToStartSurfing')+b'\x6b\x02',120)
tap(64);tap(1);drain();step(300)
assert position()[1]<y+1,(position(),x,y)
screenshot('waterfall-without-badges')
record('waterfall-usable-without-badges',from_y=y+1,to_y=position()[1])
# Real ferry menus/animations must connect every island to Kanto before the
# League or Celio quests. No pass, ticket, badge or quest-completion flag is granted.
assert flag(0x8e3) and not flag(0x82c) and not flag(0x234)
assert var(0x4076)==0 and var(0x407e)==0
islands=['One','Two','Three','Four','Five','Six','Seven']
for number,name in enumerate(islands,1):
    warp(name+'Island_Harbor',5,4)
    lib.write16(s['gSpecialVar_0x8004'],number)
    entry='EventScript_ChooseDestFrom'+('OneIsland' if number==1 else 'TwoIsland' if number==2 else 'Island')
    script(b'\x05'+struct.pack('<I',s[entry]),90)
    tap(1);drain();step(900)
    assert location()==map_id('VermilionCity'),(name,location())
    assert var(0x4076)==0 and var(0x407e)==0 and not flag(0x82c)
    record('early-ferry-island-to-kanto',island=name)

print('Journey/start/gifts/HMs/ferries passed',flush=True)
catalog=json.loads((directory/'catalog.json').read_text())['catalog']
for index,r in enumerate(catalog):
    native('CreateScriptedWildMon',r['species_id'],50,0)
    actual=native('GetMonData2',s['gEnemyParty'],abi['mon_data_species'])
    assert actual==r['species_id'],(r['species'],actual,r['species_id'])
    assert lib.read16(s['gEnemyParty']+abi['pokemon_max_hp'])>0
    assert 1<=lib.read8(s['gEnemyParty']+abi['pokemon_level'])<=7
    record('native-pokemon-creation',species=r['species'],id=actual)
    if index%100==0:print('Species checked',index,flush=True)
render_names=['SPECIES_VICTINI','SPECIES_GARDEVOIR_MEGA','SPECIES_GENESECT']
if args.rom_name=='LeafGreen-Journey-AllRegions':
    render_names += ['SPECIES_CHESPIN','SPECIES_ROWLET','SPECIES_GROOKEY','SPECIES_SPRIGATITO','SPECIES_DIANCIE_MEGA','SPECIES_WYRDEER','SPECIES_TERAPAGOS','SPECIES_TERAPAGOS_TERASTAL','SPECIES_PECHARUNT']
if args.rom_name=='LeafGreen-Journey-AllRegions':
    render_names += [r['species'] for r in catalog if r.get('native_graphics') and r['species'] not in render_names]
for name in render_names:
    row=next(r for r in catalog if r['species']==name)
    assert native('ScriptMenu_ShowPokemonPic',row['species_id'],8,2)
    step(60);screenshot(name.lower())
    native('ScriptMenu_HidePokemonPic');step(60)
    record('donor-sprite-rendered-in-game',species=name)
# Verify native type effectiveness, including immunity and weaknesses.
for attack,defend,value in [(16,18,0),(18,16,8192),(18,1,8192),(18,17,8192),(18,10,2048),(18,3,2048),(18,8,2048),(3,18,8192),(8,18,8192)]:
    assert native('GetTypeModifier',attack+1,defend+1)==value,(attack,defend)
    record('fairy-type-effectiveness',attack=attack,defend=defend)
for mask in range(256):
    for i in range(8):setflag(0x820+i,bool(mask & (1<<i)))
    assert native('OpenWorld_BadgeCount')==mask.bit_count()
record('badge-count-all-256-combinations')
# Actual native gym party generation at every order position.
world=json.loads((directory/'manifest.json').read_text())['open_world']
native('AllocateBattleResources')
assert lib.read32(s['gBattleStruct'])
for count,ace in enumerate(world['ace_levels']):
    for i in range(8):setflag(0x820+i,i<count)
    for trainer in world['trainers']:
        lib.write32(s['gBattleTypeFlags'],8)
        size=native('CreateNPCTrainerParty',s['gEnemyParty'],trainer['id'],1)
        levels=[lib.read8(s['gEnemyParty']+i*100+84) for i in range(size)]
        expected=[ace-(0 if trainer['leader'] else 2)-min(6,trainer['highest']-lv) for lv in trainer['levels']]
        assert levels==expected,(count,trainer['name'],levels,expected)
        record('compiled-gym-party-levels',badges=count,trainer=trainer['name'],levels=levels)
for i in range(8):setflag(0x820+i,False)
lib.write32(s['gBattleTypeFlags'],8)
native('CreateNPCTrainerParty',s['gEnemyParty'],349,1)
assert [lib.read8(s['gEnemyParty']+i*100+84) for i in range(4)]==[37,35,37,41]
record('rocket-boss-not-scaled')
if args.rom_name=='LeafGreen-Journey-AllRegions':
    for battler in [0,1]:
        for gimmick in [2,3,4,5]:
            assert native('CanActivateGimmick',battler,gimmick)==0
            record('excluded-battle-mechanic-unavailable',battler=battler,gimmick=gimmick)
print('Fairy/gym checks passed',flush=True)
# Exercise each actual native Mega transformation and party reversion. Items
# exist only in this temporary test session; no distribution script is added.
fixture=bytes(lib.read8(s['gPlayerParty']+i) for i in range(100))
base_by_name={r['species']:r for r in catalog}
for r in [r for r in catalog if r['mega']]:
    base=base_by_name[r['species'].split('_MEGA')[0]]
    native('CreateScriptedWildMon',base['species_id'],50,0)
    for i in range(100):lib.write8(s['gPlayerParty']+i,lib.read8(s['gEnemyParty']+i))
    changes=native('GetSpeciesFormChanges',base['species_id'])
    chosen=None
    for j in range(30):
        row=tuple(lib.read16(changes+j*abi['form_change_size']+k*2) for k in range(5))
        if row[0]==0:break
        if row[1]==r['species_id'] and row[0] in [abi['mega_item_method'],abi['mega_move_method']]:chosen=row;break
    assert chosen,(r['species'],changes)
    method,target,param,*_=chosen
    # Fresh battle state and standard player/enemy battler positions.
    native('FreeBattleResources');native('AllocateBattleResources')
    lib.write8(s['gBattlerPositions'],0);lib.write8(s['gBattlerPositions']+1,1)
    lib.write16(s['gBattlerPartyIndexes'],0);lib.write8(s['gBattlersCount'],2)
    for i in range(abi['battle_mon_size']):lib.write8(s['gBattleMons']+i,0)
    lib.write16(s['gBattleMons']+abi['battle_species'],base['species_id'])
    if method==abi['mega_item_method']:
        lib.write32(scratch+4,param)
        native('SetMonData',s['gPlayerParty'],abi['mon_data_held_item'],scratch+4)
        lib.write16(s['gBattleMons']+abi['battle_item'],param)
    else:lib.write16(s['gBattleMons']+abi['battle_moves'],param)
    native('CopyMonLevelAndBaseStatsToBattleMon',0,s['gPlayerParty'])
    native('CopyMonAbilityAndTypesToBattleMon',0,s['gPlayerParty'])
    assert native('GetBattleFormChangeTargetSpecies',0,method)==target
    if not native('CheckBagHasItem',703,1):
        assert not native('CanMegaEvolve',0)
        assert native('AddBagItem',703,1)
    assert native('CanMegaEvolve',0),r['species']
    assert native('TryBattleFormChange',0,method),r['species']
    assert native('GetMonData2',s['gPlayerParty'],abi['mon_data_species'])==target
    assert lib.read16(s['gBattleMons'])==target
    native('SetGimmickAsActivated',0,1)
    assert not native('CanMegaEvolve',0)
    assert native('TryRevertPartyMonFormChange',0)
    assert native('GetMonData2',s['gPlayerParty'],abi['mon_data_species'])==base['species_id']
    record('native-mega-evolution-and-reversion',species=r['species'],method=method,requirement=param)
print('All Mega changes/reversions passed',flush=True)
# Start a real battle and select Mega Evolution using the actual move menu.
native('FreeBattleResources')
for i in range(600):lib.write8(s['gPlayerParty']+i,0)
lib.write8(s['gPlayerPartyCount'],0)
assert native('ScriptGiveMon',3,50,292)==0
native('CreateScriptedWildMon',649,50,0)
warp('PalletTown',10,10)
native('BattleSetup_StartScriptedWildBattle')
step(1000)
for _ in range(40):
    if lib.read32(s['gBattlerControllerFuncs'])==(s['HandleInputChooseMove']|1):break
    tap(1);step(60)
assert lib.read32(s['gBattlerControllerFuncs'])==(s['HandleInputChooseMove']|1)
screenshot('battle-genesect-before-mega')
tap(8);screenshot('battle-mega-selected');tap(1)
for _ in range(2400):
    if lib.read16(s['gBattleMons'])==906:break
    step(1)
assert lib.read16(s['gBattleMons'])==906
step(360);screenshot('battle-mega-venusaur-and-genesect')
record('real-battle-ui-mega-trigger-and-donor-sprites')
lib.stop()
(args.output/'results.json').write_text(json.dumps({'rom_sha256':__import__('hashlib').sha256((directory/(args.rom_name+'.gba')).read_bytes()).hexdigest(),'checks':results},indent=2)+'\n')
print(f'{len(results)} mGBA checks passed')
