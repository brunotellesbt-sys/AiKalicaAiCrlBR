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
p.add_argument('--output',type=Path,default=ROOT/'mods/choose-starting-city/validation')
args=p.parse_args();args.output.mkdir(parents=True,exist_ok=True)
directory=ROOT/'mods/choose-starting-city'
ref=json.loads((directory/'debug-reference.json').read_text());s=ref['symbols']
lib=ctypes.CDLL(str(args.library.resolve()));lib.start.argtypes=[ctypes.c_char_p];lib.image.restype=ctypes.c_void_p;lib.read32.restype=ctypes.c_uint32
assert lib.start(str(directory/'LeafGreen-Choose-Starting-City.gba').encode())
results=[]

def step(n,keys=0):lib.frames(n,keys)
def tap(keys):step(2,keys);step(40)
def save():return lib.read32(s['gSaveBlock1Ptr'])
def var(id):return lib.read16(save()+0x1000+(id-0x4000)*2)
def setvar(id,value):lib.write16(save()+0x1000+(id-0x4000)*2,value)
def flag(id):return bool(lib.read8(save()+0xee0+id//8)&(1<<(id%8)))
def setflag(id,value):
    addr=save()+0xee0+id//8;bit=1<<(id%8);old=lib.read8(addr)
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
    for i,value in enumerate(code):lib.raw8(0x08800000+i,value)
    context=s['sGlobalScriptContext']
    for i in range(116):lib.write8(context+i,0)
    lib.write8(context+1,1);lib.write32(context+8,0x08800000)
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
    return {lib.read8(s['gObjectEvents']+i*36+8):lib.read8(s['gObjectEvents']+i*36+5) for i in range(16) if lib.read8(s['gObjectEvents']+i*36)&1}
def tm_slots():return [(lib.read16(save()+0x464+i*4),lib.read16(save()+0x466+i*4)) for i in range(58)]
def species():
    mon=s['gPlayerParty'];personality=lib.read32(mon);key=personality^lib.read32(mon+4)
    growth=[0,0,0,0,0,0,1,1,2,3,2,3,1,1,2,3,2,3,1,1,2,3,2,3][personality%24]
    return (lib.read32(mon+32+growth*12)^key)&65535

def record(name,**detail):results.append({'check':name,'passed':True,**detail})

# Initialize through the real game's new-game function after its normal introduction.
step(180)
for _ in range(12):step(10,8);step(120)
lib.write8(save()+0x3a4c,255);lib.write8(lib.read32(s['gSaveBlock2Ptr']),255)
lib.write32(s['gMain'],0);lib.write8(s['gMain']+0x438,0);lib.write32(s['gMain']+4,s['CB2_NewGame']|1)
step(300);tap(1);screenshot('city-selection')
tap(128);tap(128);tap(1)
for _ in range(5):tap(1)
step(900)
assert var(0x40cb)==5
home=ref['homes'][var(0x40cc)-1]
assert location()==map_id('JourneyBedroom'+str(home['index']-1).zfill(2))
screenshot('born-in-bedroom')
record('real-city-menu-and-fixed-birth',city=home['city'],house=home['house'])
# Walk to the original bedroom staircase and use its directional warp.
step(64,16);step(20);step(80,64);step(900);step(8,32);step(900)
assert location()==map_id(home['house'])
assert objects().get(10)==71 and objects().get(11)==152
screenshot('family-professor-and-case')
record('physical-bedroom-staircase-and-visitors')
# Front-door trigger prevents entering wild battles without a starter.
warp(home['house'],4,7);step(24,128);step(10);drain()
assert location()==map_id(home['house']) and position()[1]<8
record('cannot-leave-home-without-starter')
# Speak to Oak normally; default menu choice is Bulbasaur.
warp(home['house'],4,5);tap(64);tap(1);step(40);screenshot('oak-visiting-family')
drain();step(300)
assert lib.read8(s['gPlayerPartyCount'])==1 and species()==1
assert lib.read8(s['gPlayerParty']+84)==5
assert flag(0x828) and flag(0x829) and flag(0x8e1) and var(0x40ce)==2
assert 10 not in objects() and 11 not in objects()
screenshot('starter-and-pokedex-received')
record('real-oak-dialogue-starter-dex-and-departure',species=species())
tap(8);screenshot('pokemon-and-pokedex-in-menu');tap(2)
# Mother and other family members give items, with no repeat grants.
for person in range(home['people']):
    lib.write16(s['gSpecialVar_LastTalked'],person+1)
    script(special('JourneyGiveGift')+b'\x6b\x02',30)
assert {341,345}.issubset({item for item,_ in tm_slots()})
before=tm_slots()
for person in range(home['people']):
    lib.write16(s['gSpecialVar_LastTalked'],person+1)
    script(special('JourneyGiveGift')+b'\x6b\x02',30)
assert tm_slots()==before
record('family-hms-and-no-repeat-gifts')
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
    assert location()==map_id(home['house']) and objects().get(10)==71 and objects().get(11)==152
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
    assert species()==expected and var(0x4031)==starter_var and lib.read8(s['gPlayerParty']+84)==5, (choice,species(),var(0x4031),lib.read8(s['gPlayerParty']+84))
    record('starter-choice',species=expected,rival_starter_var=starter_var)
# Teach a compatible starter only in the test, then exercise both field actions
# with every badge flag unset. The distributed game still requires teaching HMs.
script(b'\x7b\x00\x00'+struct.pack('<H',57)+b'\x7b\x00\x01'+struct.pack('<H',127)+b'\x6b\x02',30)
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
# The physical pier offers a ferry without a ticket, but still admits ticket
# holders through the original SS Anne check rather than intercepting them.
warp('VermilionCity',23,32);lib.write16(s['gSpecialVar_Result'],0)
step(20,128);step(120)
for _ in range(10):
    if lib.read16(s['gSpecialVar_Result'])==255:break
    tap(1)
assert lib.read16(s['gSpecialVar_Result'])==255
tap(2);step(300)
assert position()[1]==32 and var(0x4053)==0
record('physical-pier-ferry-without-ss-ticket')
setflag(0x234,True);warp('VermilionCity',23,32)
step(20,128);step(120);drain()
assert var(0x4053)==1
setflag(0x234,False);setvar(0x4053,0)
record('ss-ticket-preserves-original-boarding-check')
# Talk to the actual Vermilion sailor, including navigating to the second page.
warp('VermilionCity',24,32)
lib.write16(s['gSpecialVar_Result'],0)
tap(128);tap(1)
for _ in range(10):
    if lib.read16(s['gSpecialVar_Result'])==255:break
    tap(1)
assert lib.read16(s['gSpecialVar_Result'])==255
screenshot('early-ferry-menu-from-kanto')
for _ in range(4):tap(128)
tap(1);tap(128);tap(128);tap(1);drain();step(900)
assert location()==map_id('SevenIsland_Harbor'),location()
screenshot('early-ferry-to-seven-island')
record('early-ferry-kanto-to-postgame-island')
assert var(0x4076)==0 and var(0x407e)==0 and not flag(0x82c) and not flag(0x234)
record('ferry-preserves-celio-league-and-ssanne-story')
# The last option must be reachable through the actual 16-entry city grid.
lib.write16(s['gSpecialVar_Result'],0)
script(b'\x05'+struct.pack('<I',s['Journey_ChooseCity']),90)
for _ in range(10):
    if lib.read16(s['gSpecialVar_Result'])==255:break
    tap(1)
assert lib.read16(s['gSpecialVar_Result'])==255
for _ in range(7):tap(128)
tap(16);screenshot('city-selection-seven-island');tap(1);drain();step(900)
assert var(0x40cb)==16 and var(0x40cc)==16 and location()==map_id('JourneyBedroom15')
record('real-city-menu-last-island-birth')
# Every menu entry maps to one fixed home on every selection.
for city in range(16):
    for _ in range(5):
        lib.write16(s['gSpecialVar_Result'],city)
        script(special('JourneyChooseHome')+b'\x6b\x02',5)
        assert var(0x40cc)==city+1 and var(0x40cb)==city+1
    record('city-always-selects-one-fixed-house',city=city,home=city+1)
from validate_open_world import validate
validate(globals())
lib.stop()
(args.output/'results.json').write_text(json.dumps(results,indent=2)+'\n')
print(f'{len(results)} mGBA checks passed')
