"""Fill the real Bag with all item types, scroll past 255, and save/reload."""
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
prefix=(ROOT/'tools/hoenn/validate_world_map.py').read_text().split('\nchecks=[]')[0]
exec(compile(prefix,str(ROOT/'tools/hoenn/validate_world_map.py'),'exec'))
sha=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest()
with tempfile.TemporaryDirectory(dir='/tmp') as temp:
    p=Path(temp)/'probe.s'
    code='#include "global.h"\n#include "item.h"\n#include "item_menu.h"\n#include <stddef.h>\nconst u32 probe[]={ITEMS_COUNT,POCKETS_COUNT,offsetof(struct BagMenu,numItemStacks),POCKET_ITEMS,POCKET_TM_HM,sizeof(struct SaveBlock1),sizeof(struct ItemInfo),offsetof(struct ItemInfo,name)};'
    subprocess.run([str(ROOT/'.local/arm-gcc/usr/bin/arm-none-eabi-gcc'),'-S','-mabi=apcs-gnu','-iquote',str(source/'include'),'-x','c','-','-o',str(p)],input=code,text=True,check=True)
    itemcount,pockets,stacks,regular,tmhm,savebytes,itemstride,nameoffset=[int(n) for n in re.findall(r'\.word\s+(\d+)',p.read_text())]
assert savebytes<=3968*5
counts=[0]*pockets;added=[];tms=[]
for item in range(1,itemcount):
    if not lib.read32(s['gItemsInfo']+item*itemstride+nameoffset):continue # Unregistered reserved IDs.
    pocket=native('GetItemPocket',item)
    if pocket>=pockets:continue
    if not native('GetItemName',item):continue
    assert native('AddBagItem',item,1),(item,pocket,counts)
    assert native('CheckBagHasItem',item,1)
    counts[pocket]+=1;added.append(item)
    if len(added)%100==0:print('Real Bag contains',len(added),'item types',flush=True)
    if pocket==tmhm:
        assert native('GetItemImportance',item)>0,('Consumable TM/HM',item)
        tms.append(item)
assert counts[regular]>255 and tms
assert native('TrySavingData',0,max_frames=6000)==1
assert native('LoadGameSave',0,max_frames=6000)==1
for item in added:assert native('CheckBagHasItem',item,1),('Lost item on reload',item)
press(8);wait_for(lambda:lib.read8(s['sNumStartMenuActions'])>0);step(80)
actions=[lib.read8(s['sCurrentStartMenuActions']+i) for i in range(lib.read8(s['sNumStartMenuActions']))]
index=next(i for i,v in enumerate(actions) if lib.read32(s['sStartMenuItems']+v*8+4)&~1==s['StartMenuBagCallback'])
for _ in range(12):
    pos=lib.read8(s['sStartMenuCursorPos'])
    if pos==index:break
    press(128 if pos<index else 64)
press(1);step(300)
ptr=lib.read32(s['gBagMenu']);assert ptr
assert lib.read16(ptr+stacks+regular*2)>=counts[regular]
picture('modern-bag-all-items')
# The live menu count must retain all entries instead of wrapping at 255.
step(2000,128);step(30);picture('modern-bag-scroll-beyond-255')
assert hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest()==sha
lib.stop()
(args.output/'modern-bag.json').write_text(json.dumps(dict(passed=True,rom_sha256=sha,
    all_current_item_types_fit=True,items_added=len(added),pocket_counts=counts,reusable_tm_hm_items=len(tms),
    native_save_reload_preserves_every_item=True,menu_entry_count_above_255=True,
    bag_initial_items_and_travel_are_fixtures=True,tm_importance_checked=True,
    actual_tm_teaching_reuse_tested=False,saveblock1_bytes=savebytes),indent=2)+'\n')
