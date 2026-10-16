"""Buy real stock, use both Hyper Training services and collect Dewford's gift."""
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
prefix=(ROOT/'tools/hoenn/validate_sootopolis_harbor.py').read_text().split('\n# Disable Sootopolis')[0]
exec(compile(prefix,__file__,'exec'))
report=json.loads((source/'.journey-dewford-competitive-shop').read_text())
expressions=['offsetof(struct SaveBlock1,money)','sizeof(struct Pokemon)','MON_DATA_HP_IV',
             'MON_DATA_HYPER_TRAINED_HP','MON_DATA_LEVEL','MON_DATA_IS_EGG',
             'ITEM_BOTTLE_CAP','ITEM_GOLD_BOTTLE_CAP','ITEM_FULL_RESTORE','SPECIES_SWAMPERT',
             'ITEM_TM_PLAY_ROUGH','MOVE_PLAY_ROUGH','SPECIES_CLEFAIRY']
expressions += ['ITEM_'+item for item in report['prices']]
code='#include "global.h"\n#include "pokemon.h"\n#include "constants/items.h"\n#include "constants/species.h"\n#include "constants/moves.h"\n#include <stddef.h>\nconst u32 probe[]={'+','.join(expressions)+'};'
with tempfile.TemporaryDirectory(dir='/tmp') as tmp:
    probe=Path(tmp)/'shop.s'
    subprocess.run([str(ROOT/'.local/arm-gcc/usr/bin/arm-none-eabi-gcc'),'-S','-mabi=apcs-gnu','-iquote',str(source/'include'),'-x','c','-','-o',str(probe)],input=code,text=True,check=True)
    c=dict(zip(expressions,map(int,re.findall(r'\.word\s+(\d+)',probe.read_text()))))
scratch=s['gStringVar4']+800
party=s['gParties'];mon_size=c['sizeof(struct Pokemon)']
def setdata(field,value):
    lib.write32(scratch,value);native('SetMonData',party,c[field],scratch)
def data(field):return native('GetMonData2',party,c[field])
def quantity(item):return native('CountTotalItemQuantityInBag',c['ITEM_'+item])
def finish():
    for _ in range(300):
        if idle():return
        press(1)
    picture('dialogue-failure');raise AssertionError('Dialogue did not release controls')
def wait_for(test,label,frames=700):
    for _ in range(frames):
        if test():step(20);return
        step(1)
    picture('missing-'+label);raise AssertionError(label)
def task_id(name):
    return next((i for i in range(16) if lib.read8(s['gTasks']+i*40+4) and lib.read32(s['gTasks']+i*40)&~1==s[name]),None)
def advance_to(name):
    for _ in range(500):
        if task(name):step(20);return
        press(1)
    picture('missing-'+name);raise AssertionError(name)
def menu():return task('Task_HandleScrollingMultichoiceInput')
def choose(index):
    for _ in range(500):
        if menu():step(20);break
        press(1)
    else:
        picture('missing-dynamic-menu');raise AssertionError('Dynamic menu missing')
    for _ in range(index):press(128)
    press(1)
def talk_vendor():step(4,64);step(20);press(1)
def leave_shop():
    for _ in range(25):
        if idle():return
        press(2);step(30)
        if idle():return
        if not task('Task_BuyMenu') and not task('Task_ShopMenu') and not menu():press(1)
    picture('shop-exit-failure');raise AssertionError('Could not leave the shop')
def buy(category,index,item):
    before=quantity(item);money_before=native('GetMoney',save()+c['offsetof(struct SaveBlock1,money)'])
    warp('Route107',2,16);talk_vendor();choose(category)
    advance_to('Task_ShopMenu');press(1)
    wait_for(lambda:task('Task_BuyMenu'),'buy-list')
    for _ in range(index):press(128)
    press(1);advance_to('Task_BuyHowManyDialogueHandleInput');picture('buy-'+item)
    press(1);advance_to('Task_CallYesOrNoCallback');press(1)
    advance_to('Task_BuyMenu');leave_shop()
    assert quantity(item)==before+1,item
    money_after=native('GetMoney',save()+c['offsetof(struct SaveBlock1,money)'])
    assert money_before-money_after==report['prices'][item],(item,money_before,money_after)
    return dict(item=item,price=money_before-money_after,quantity_received=1)
native('SetPlayerAvatarTransitionFlags',1)
warp('Route107',0,16);walk_to(5,16);walk_to(5,15);walk_to(5,16);walk_to(0,16)
picture('stall-and-footpath')
for name,price in report['prices'].items():assert native('GetItemPrice',c['ITEM_'+name])==price,name
native('SetMoney',save()+c['offsetof(struct SaveBlock1,money)'],999999)
purchases=[buy(0,report['stocks'][0].index('CHOICE_SCARF'),'CHOICE_SCARF'),buy(4,0,'BOTTLE_CAP'),buy(4,1,'GOLD_BOTTLE_CAP')]
# A real purchase with insufficient money must not add an item or change funds.
native('SetMoney',save()+c['offsetof(struct SaveBlock1,money)'],0)
before=quantity('BOTTLE_CAP')
warp('Route107',2,16);talk_vendor();choose(4);advance_to('Task_ShopMenu');press(1);wait_for(lambda:task('Task_BuyMenu'),'poor-buy-list')
press(1);step(120);picture('insufficient-money');press(1);step(60)
leave_shop()
assert quantity('BOTTLE_CAP')==before and native('GetMoney',save()+c['offsetof(struct SaveBlock1,money)'])==0
# Make one level-50 trainee. Its IVs are fixtures; all training below uses
# the party screen, the trainer's menus, and confirmation buttons.
for i in range(6*mon_size):lib.write8(party+i,0)
lib.write8(s['gPartiesCount'],0);assert native('ScriptGiveMon',c['SPECIES_SWAMPERT'],50,0)==0
for stat in range(6):
    lib.write32(scratch,7+stat);native('SetMonData',party,c['MON_DATA_HP_IV']+stat,scratch)
    lib.write32(scratch,0);native('SetMonData',party,c['MON_DATA_HYPER_TRAINED_HP']+stat,scratch)
native('CalculateMonStats',party)
def training(gold,cancel=False):
    warp('Route107',1,16);talk_vendor();advance_to('Task_HandleChooseMonInput');press(1)
    choose(1 if gold else 0)
    if not gold:choose(1) # Attack
    advance_to('Task_HandleYesNoInput');picture('hyper-gold-confirm' if gold else 'hyper-single-confirm')
    if cancel:press(128)
    press(1);finish()
before=quantity('BOTTLE_CAP');training(False,True);assert quantity('BOTTLE_CAP')==before
assert all(native('GetMonData2',party,c['MON_DATA_HYPER_TRAINED_HP']+i)==0 for i in range(6))
training(False);assert quantity('BOTTLE_CAP')==before-1
assert [native('GetMonData2',party,c['MON_DATA_HYPER_TRAINED_HP']+i) for i in range(6)]==[0,1,0,0,0,0]
gold_before=quantity('GOLD_BOTTLE_CAP');training(True);assert quantity('GOLD_BOTTLE_CAP')==gold_before-1
assert all(native('GetMonData2',party,c['MON_DATA_HYPER_TRAINED_HP']+i)==1 for i in range(6))
assert [native('GetMonData2',party,c['MON_DATA_HP_IV']+i) for i in range(6)]==list(range(7,13))
# Boundary cases call the same native transactional service with fixtures.
native('VarSet',0x8008,0);native('VarSet',0x8006,1)
native('AddBagItem',c['ITEM_GOLD_BOTTLE_CAP'],2);gold_before=quantity('GOLD_BOTTLE_CAP')
native('JourneyHyperApply');assert lib.read16(s['gSpecialVar_Result'])==3 and quantity('GOLD_BOTTLE_CAP')==gold_before
setdata('MON_DATA_LEVEL',49);native('JourneyHyperApply');assert lib.read16(s['gSpecialVar_Result'])==2 and quantity('GOLD_BOTTLE_CAP')==gold_before
setdata('MON_DATA_LEVEL',50);setdata('MON_DATA_IS_EGG',1);native('JourneyHyperApply');assert lib.read16(s['gSpecialVar_Result'])==4 and quantity('GOLD_BOTTLE_CAP')==gold_before
setdata('MON_DATA_IS_EGG',0)
# Pick up the actual Poké Ball, then return to check its persistent flag.
native('FlagClear',report['item']['flag']);warp('Route106',75,17)
before=quantity('FULL_RESTORE');step(4,64);press(1);finish()
assert quantity('FULL_RESTORE')==before+1 and native('FlagGet',report['item']['flag'])
warp('Route107',0,16);warp('Route106',75,17);picture('full-restore-collected')
assert native('FlagGet',report['item']['flag'])
for x in (8,9):
    warp('JourneyDewfordPortIsland',7,8)
    assert native('MapGridGetCollisionAt',x+7,6+7)!=0 and native('MapGridGetCollisionAt',x+7,7+7)!=0
picture('closed-northeast-forest')
# Walk behind the peak and collect the real TM ball beside the closing trees.
warp('Route106',77,14);walk_to(79,14)
change_map(16,'JourneyDewfordPortIsland');walk_to(6,6)
native('FlagClear',report['tm']['flag']);warp('JourneyDewfordPortIsland',6,6)
before=quantity('TM_PLAY_ROUGH');step(4,16);press(1);finish()
assert quantity('TM_PLAY_ROUGH')==before+1 and native('FlagGet',report['tm']['flag'])
assert native('ItemIdToBattleMoveId',c['ITEM_TM_PLAY_ROUGH'])==c['MOVE_PLAY_ROUGH']
assert native('CanLearnTeachableMove',c['SPECIES_CLEFAIRY'],c['MOVE_PLAY_ROUGH'])
picture('play-rough-collected')
mode=bool(lib.read8(s['gJourneyReviewMode']));lib.stop()
r=dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),review_mode=mode,
       prices_checked=len(report['prices']),purchases=purchases,insufficient_money_preserves_money_and_bag=True,
       two_attendants_interacted=True,footpath_to_bridge_walked=True,
       single_cap_only_one_stat=True,gold_cap_all_six_stats=True,original_genetic_ivs_preserved=True,
       cancellation_preserves_caps=True,perfect_stats_preserve_caps=True,level49_rejected=True,eggs_rejected=True,
       full_restore_picked_up_once=True,closed_trees_block_walk=True,play_rough_picked_up_and_native_teachable=True,lighthouse_back_path_walked=True,initial_party_money_and_position_are_fixtures=True)
(args.output/'dewford-competitive-shop.json').write_text(json.dumps(r,indent=2)+'\n')
print('Dewford stall: purchases, two attendants, Hyper Training, gift and footpath passed.')
