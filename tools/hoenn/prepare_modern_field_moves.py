"""Restore Fly as the fourth HM, preserve open land routes and lit caves."""
import argparse,json,re
from pathlib import Path
from candidate_layer import Layer
from prepare_modern_bag import PRIOR,LAYER as PREVIOUS
LAYER='modern-field-moves';PRIOR=PRIOR+[PREVIOUS]

def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if result:=layer.existing():return result
    source=layer.source
    p='src/rom_header_gf.c';text=(source/p).read_text()
    # Preserve the historical SDK ABI; its one-byte metadata cannot describe
    # the expanded pocket. The actual engine/menu uses the full 620 capacity.
    text=text.replace('.bagCountItems = BAG_ITEMS_COUNT,','.bagCountItems = min(BAG_ITEMS_COUNT,255),')
    layer.stage(p,text)
    p='include/constants/tms_hms.h';text=(source/p).read_text()
    assert text.count('    F(FLY) \\\n')==1
    text=text.replace('    F(FLY) \\\n','').replace('    F(WATERFALL)\n','    F(WATERFALL) \\\n    F(FLY)\n')
    layer.stage(p,text)
    affected=[]
    for folder,extensions in [('src',{'.c','.h'}),('include',{'.h'}),('data',{'.inc'}),('test',{'.c','.h'})]:
        for path in sorted((source/folder).rglob('*')):
            if path.suffix not in extensions:continue
            text=path.read_text()
            if 'ITEM_TM_FLY' not in text:continue
            p=path.relative_to(source).as_posix();text=text.replace('ITEM_TM_FLY','ITEM_HM_FLY')
            if p=='src/data/items.h':
                match=re.search(r'    \[ITEM_HM_FLY\] =\n    \{.*?\n    \},',text,re.S);assert match
                stanza=match[0].replace('ITEM_NAME("TM52")','ITEM_NAME("HM04")').replace('.importance = I_REUSABLE_TMS,','.importance = 1,')
                text=text[:match.start()]+stanza+text[match.end():]
            elif folder=='data':
                text=re.sub(r'(?m)^(\s*\.string .*?)\bTM52\b',lambda m:m[1]+'HM04',text)
            layer.stage(p,text);affected.append(p)
    p='src/field_move.c';text=(source/p).read_text()
    text,n=re.subn(r'(static bool32 IsFieldMoveUnlocked_Fly\(void\)\n\{).*?\n\}',r'\1\n    return TRUE;\n}',text,flags=re.S);assert n==1
    layer.stage(p,text)
    p='src/overworld.c';text=(source/p).read_text()
    text,n=re.subn(r'(void SetDefaultFlashLevel\(void\)\n\{).*?\n\}',r'\1\n    gSaveBlock1Ptr->flashLevel = 0;\n}',text,flags=re.S);assert n==1
    layer.stage(p,text)
    dark=[]
    for path in sorted((source/'data/maps').glob('*/map.json')):
        data=json.loads(path.read_text())
        if data.get('requires_flash'):
            data['requires_flash']=False
            layer.stage(path.relative_to(source).as_posix(),json.dumps(data,indent=2)+'\n');dark.append(path.parent.name)
    return layer.finish(hms=['SURF','DIVE','WATERFALL','FLY'],fly_badge_free=True,
        family_hms=['SURF','DIVE','WATERFALL'],terrestrial_tms=['CUT','STRENGTH','FLASH','ROCK_SMASH'],
        caves_fully_lit=True,newly_cleared_dark_maps=dark,fly_item_references=affected,
        gf_sdk_metadata_capacity_is_clamped=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    print(prepare(p.parse_args().source)['layer'])
