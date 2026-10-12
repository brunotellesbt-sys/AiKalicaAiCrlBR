"""Fit every existing item type in the Bag and make TMs reusable."""
import argparse,re
from pathlib import Path
from candidate_layer import Layer
from prepare_player_choice import PRIOR,LAYER as PREVIOUS
LAYER='modern-bag';PRIOR=PRIOR+[PREVIOUS]
CAPACITIES={'BAG_ITEMS_COUNT':620,'BAG_KEYITEMS_COUNT':96,'BAG_POKEBALLS_COUNT':32,'BAG_TMHM_COUNT':110,'BAG_BERRIES_COUNT':80}

def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if result:=layer.existing():return result
    source=layer.source
    p='include/constants/global.h';text=(source/p).read_text()
    for name,count in CAPACITIES.items():
        text,n=re.subn(r'(#define '+name+r'\s+)\d+',lambda m:m[1]+str(count),text)
        assert n==1,name
    layer.stage(p,text)
    p='include/config/item.h';text=(source/p).read_text();assert '#define I_REUSABLE_TMS          FALSE' in text
    layer.stage(p,text.replace('#define I_REUSABLE_TMS          FALSE','#define I_REUSABLE_TMS          TRUE'))
    p='include/item_menu.h';text=(source/p).read_text().replace('u8 toSwapPos;','u16 toSwapPos;').replace('u8 numItemStacks[POCKETS_COUNT];','u16 numItemStacks[POCKETS_COUNT];').replace('u8 GetItemListPosition(u8 pocketId);','u16 GetItemListPosition(u8 pocketId);')
    layer.stage(p,text)
    p='src/item_menu.c';text=(source/p).read_text().replace('#define NOT_SWAPPING 0xFF','#define NOT_SWAPPING 0xFFFF').replace('u8 GetItemListPosition(u8 pocketId)','u16 GetItemListPosition(u8 pocketId)')
    layer.stage(p,text)
    return layer.finish(pocket_capacities=CAPACITIES,each_current_item_type_fits=True,reusable_tms=True,
                        quantity_per_stack=999,new_save_required=True,save_layout_changed=True,
                        extended_menu_indices_bits=16)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    print(prepare(p.parse_args().source)['layer'])
