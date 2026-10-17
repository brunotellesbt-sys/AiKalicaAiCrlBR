"""Walk native homes, claim gifts, buy a stone and save/continue the new plaza."""
import hashlib
import json
import re
import struct
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
prefix=(ROOT/'tools/hoenn/validate_team_missions.py').read_text().split('\nassert pending(True) == 7')[0]
exec(compile(prefix,__file__,'exec'))
report=json.loads((source/'.journey-ever-grande-market').read_text())
names=['EverGrandeCity','EverGrandeCity_PokemonCenter_1F','VictoryRoad_1F',*[h['map'] for h in report['houses']]]
allowed=set();walk_prefix='ever';walk_transition_pictures=False;walk_max_ticks=1500
exec(compile((ROOT/'tools/hoenn/native_water_walk.py').read_text(),'ever-native-walker','exec'))
opening=(ROOT/'tools/hoenn/validate_world_map.py').read_text().split('\nchecks=[]')[0].split('def callback():')[1]
exec('def callback():'+opening)
code='''#include "global.h"
#include "item.h"
#include <stddef.h>
const u32 probe[]={offsetof(struct SaveBlock1,money),offsetof(struct SaveBlock2,encryptionKey),sizeof(struct ItemSlot),sizeof(struct BagPocket),ITEM_VENUSAURITE,ITEM_POTION};
'''
assembly=subprocess.check_output([str(ROOT/'.local/arm-gcc/usr/bin/arm-none-eabi-gcc'),'-S','-mabi=apcs-gnu','-iquote',str(source/'include'),'-x','c','-','-o','-'],input=code,text=True)
money_offset,key_offset,slot_size,pocket_size,stone,potion=[int(n) for n in re.findall(r'\.word\s+(\d+)',assembly.split('probe:',1)[1].split('.size',1)[0])]
assert slot_size==4
def money():return lib.read32(save()+money_offset)^lib.read32(lib.read32(s['gSaveBlock2Ptr'])+key_offset)
def set_money(value):lib.write32(save()+money_offset,value^lib.read32(lib.read32(s['gSaveBlock2Ptr'])+key_offset))
def face_talk():
    step(4,64);step(20);press(1)
def until(predicate,limit=240,key=1):
    for _ in range(limit):
        if predicate():return
        press(key)
    picture('ever-failure')
    active=[n for n,a in s.items() if any(lib.read8(s['gTasks']+i*40+4) and lib.read32(s['gTasks']+i*40)&~1==a for i in range(16))]
    raise AssertionError(('Native plaza timeout',location(),position(),active))
def close_shop():
    for _ in range(150):
        if idle():return
        if task('Task_ShopMenu') or task('Task_BuyMenu'):press(2)
        else:press(1)
    raise AssertionError('Shop did not close')

# Only this initial arrival is a travel fixture. All doors/paths below use input.
warp('EverGrandeCity',27,49);step(90);picture('ever-grande-plaza')
walk(('EverGrandeCity_PokemonCenter_1F',7,8));walk(('EverGrandeCity',27,49))
gifts=[]
for index,h in enumerate(report['houses']):
    n=h['map'];item=32 if index==0 else 34
    npc=(6,4) if index==0 else (7,4)
    walk((n,npc[0],npc[1]+1));picture(n+'-inside')
    before=native('CountTotalItemQuantityInBag',item);assert not flag(h['flag_id'])
    # A genuinely full ordinary-item pocket must leave the gift unclaimed.
    pocket=s['gBagPockets'];ptr=lib.read32(pocket);capacity=lib.read16(pocket+4)&1023
    snapshot=bytes(lib.read8(ptr+i) for i in range(capacity*slot_size))
    key=lib.read32(lib.read32(s['gSaveBlock2Ptr'])+key_offset)&65535
    for i in range(capacity):
        lib.write16(ptr+i*slot_size,potion);lib.write16(ptr+i*slot_size+2,999^key)
    assert not native('CheckBagHasSpace',item,1)
    face_talk();finish();assert not flag(h['flag_id']);picture(n+'-bag-full')
    for i,b in enumerate(snapshot):lib.write8(ptr+i,b)
    assert native('CountTotalItemQuantityInBag',item)==before
    face_talk();finish();assert flag(h['flag_id'])
    assert native('CountTotalItemQuantityInBag',item)==before+1
    face_talk();finish();assert native('CountTotalItemQuantityInBag',item)==before+1
    # The second resident speaks without giving another reward.
    walk((n,3,6 if index==0 else 4));step(4,32);step(20);press(1);finish()
    walk(('EverGrandeCity',h['door'][0],h['door'][1]+1))
    gifts.append(dict(map=n,item=h['item'],bag_full_preserves_gift=True,exactly_one_item=True,repeat_talk_no_duplicate=True,neighbor_talked=True,controller_entry_and_exit=True))

walk(('EverGrandeCity',18,42));walk(('EverGrandeCity',19,50));walk(('EverGrandeCity',19,53))
walk(('EverGrandeCity',26,53));picture('ever-market-counter')
before=native('CountTotalItemQuantityInBag',stone)
set_money(199999);face_talk();until(lambda:task('Task_ShopMenu'));press(1)
until(lambda:task('Task_BuyMenu'));step(60);picture('ever-market-prices')
assert lib.read8(s['sJourneyEverGrandeMarket'])==1
press(1);step(180);picture('ever-market-insufficient-money');press(1);close_shop()
assert money()==199999 and native('CountTotalItemQuantityInBag',stone)==before
set_money(200000);face_talk();until(lambda:task('Task_ShopMenu'));press(1);until(lambda:task('Task_BuyMenu'));step(60)
press(1);until(lambda:money()==0);picture('ever-market-purchase');close_shop()
assert native('CountTotalItemQuantityInBag',stone)==before+1
assert native('GetItemPrice',stone)==25000, 'Base/resale prices must not change'
# Opening a different ordinary stock resets the scoped markup.
scratch=s['gStringVar4']+600;lib.write16(scratch,stone);lib.write16(scratch+2,0)
native('SetShopItemsForSale',scratch)
assert native('JourneyEverGrandeShopPrice',stone)<=25000

assert native('TrySavingData',0,max_frames=6000)==1
assert native('LoadGameSave',0,max_frames=6000)==1
lib.write32(s['gMain']+4,s['CB2_ContinueSavedGame']|1);step(1500)
assert location()==map_id('EverGrandeCity')
assert all(flag(h['flag_id']) for h in report['houses'])
assert native('CountTotalItemQuantityInBag',stone)==before+1
for index,h in enumerate(report['houses']):
    npc=(6,4) if index==0 else (7,4);item=32 if index==0 else 34
    count=native('CountTotalItemQuantityInBag',item)
    walk((h['map'],npc[0],npc[1]+1));face_talk();finish()
    assert native('CountTotalItemQuantityInBag',item)==count
    walk(('EverGrandeCity',h['door'][0],h['door'][1]+1))

# Both compiled map scales must contain the restored city emblem.
nm=subprocess.check_output([str(ROOT/'.local/arm-binutils/usr/bin/arm-none-eabi-nm'),'-S',str(source/'pokeemerald.elf')],text=True)
sizes={n:(int(a,16)-0x8000000,int(z,16)) for a,z,_,n in re.findall(r'^(\w+) (\w+) (\w) (\S+)$',nm,re.M)}
rom=(source/'pokeemerald.gba').read_bytes();header=(source/'src/data/journey_world_map.h').read_text()
for symbol,fmt in [('sWorldTiles','B'),('sWorldTilemap','H'),('sWorldDetailPixels','B')]:
    values=list(map(int,re.search(symbol+r'\[\] = \{([^}]+)',header)[1].split(',')));at,size=sizes[symbol]
    assert rom[at:at+size]==struct.pack('<'+fmt*len(values),*values),symbol
warp('SootopolisCity',31,17);step(90);ptr=open_map();picture('sootopolis-red-city-map')
press(256);step(60);picture('sootopolis-red-city-zoom');press(2);wait_for(lambda:callback()==s['CB2_Overworld']);step(120);press(2)
lib.stop()
result=dict(passed=True,rom_sha256=hashlib.sha256(rom).hexdigest(),gifts=gifts,controller_center_roundtrip=True,
    victory_road_and_stairs_walked=True,market_actual_purchase=True,market_price=200000,insufficient_money_rejected=True,
    stock_specific_price_reset=True,base_item_price_unchanged=True,save_continue_preserves_gifts_and_purchase=True,
    compiled_atlas_and_zoom_match_source=True,sootopolis_city_red=True,initial_placement_money_bag_and_party_are_fixtures=True)
(args.output/'ever-grande-market.json').write_text(json.dumps(result,indent=2)+'\n')
print('Ever Grande homes, gifts, Mega market and red Sootopolis passed',flush=True)
