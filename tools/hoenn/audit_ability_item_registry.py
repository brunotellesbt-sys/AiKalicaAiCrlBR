"""Audit compiled ability/item records; this is not every effect's battle test."""
import argparse,hashlib,json,re,subprocess,tempfile
from pathlib import Path
from audit_battle_database import compiled
ROOT=Path(__file__).resolve().parents[2]

def audit(source):
    source=Path(source);rom=(source/'pokeemerald.gba').read_bytes();database=compiled(source)
    nm=subprocess.check_output([str(ROOT/'.local/arm-binutils/usr/bin/arm-none-eabi-nm'),'-n',str(source/'pokeemerald.elf')],text=True)
    symbols={n:int(a,16)-0x08000000 for a,_,n in re.findall(r'^(\w+) (\w) (\S+)$',nm,re.M)}
    with tempfile.TemporaryDirectory(dir='/tmp') as temp:
        p=Path(temp)/'probe.s'
        expressions=['ABILITIES_COUNT','sizeof(struct AbilityInfo)','offsetof(struct AbilityInfo,description)',
            'offsetof(struct SpeciesInfo,abilities)','sizeof(enum Ability)','ITEMS_COUNT','sizeof(struct ItemInfo)',
            'offsetof(struct ItemInfo,name)','offsetof(struct ItemInfo,description)','offsetof(struct ItemInfo,iconPic)',
            'offsetof(struct ItemInfo,iconPalette)','offsetof(struct ItemInfo,fieldUseFunc)','NUM_ALL_MACHINES',
            'offsetof(struct ItemInfo,sortType)','POCKET_TM_HM']
        code='#include "global.h"\n#include "pokemon.h"\n#include "item.h"\n#include <stddef.h>\nconst u32 probe[]={'+','.join(expressions)+'};'
        subprocess.run([str(ROOT/'.local/arm-gcc/usr/bin/arm-none-eabi-gcc'),'-S','-mabi=apcs-gnu','-iquote',str(source/'include'),'-x','c','-','-o',str(p)],input=code,text=True,check=True)
        count,stride,desc,abilityoffset,abilitybytes,itemcount,itemstride,name,itemdesc,icon,palette,function,machinecount,sortoffset,machinepocket=[int(n) for n in re.findall(r'\.word\s+(\d+)',p.read_text())]
    def pointer(at):
        address=int.from_bytes(rom[at:at+4],'little')
        assert 0x08000000<=address<0x08000000+len(rom),(hex(at),hex(address))
        return address-0x08000000
    registered=[]
    for ident in range(1,count):
        at=symbols['gAbilitiesInfo']+ident*stride
        assert rom[at] not in [0,255],('Missing ability name',ident)
        pointer(at+desc);registered.append(ident)
    hidden=0
    for sid in database['species']:
        at=database['compiled_layout']['symbols']['gSpeciesInfo']+sid*database['compiled_layout']['abi'][0]+abilityoffset
        slots=[int.from_bytes(rom[at+i*abilitybytes:at+(i+1)*abilitybytes],'little') for i in range(3)]
        assert slots[0] and all(0<=value<count for value in slots),(sid,slots)
        hidden+=slots[2]!=0
    machines={int.from_bytes(rom[symbols['gTMHMItemMoveIds']+i*4:symbols['gTMHMItemMoveIds']+i*4+2],'little') for i in range(machinecount)}
    items=0
    for ident in range(1,itemcount):
        at=symbols['gItemsInfo']+ident*itemstride
        # Empty reserved IDs have no name and are deliberately unavailable.
        if int.from_bytes(rom[at+name:at+name+4],'little')==0:continue
        for offset in [name,itemdesc]:pointer(at+offset)
        for offset in [icon,palette]:
            if int.from_bytes(rom[at+offset:at+offset+4],'little'):pointer(at+offset)
            else:assert rom[at+sortoffset-1]>>3==machinepocket,('Missing icon outside dynamically drawn TM/HM',ident)
        if int.from_bytes(rom[at+function:at+function+4],'little'):pointer(at+function)
        items+=1
    return dict(passed=True,rom_sha256=hashlib.sha256(rom).hexdigest(),registered_abilities=len(registered),
        species_forms_with_hidden_slot=hidden,referenced_species_forms=len(database['species']),registered_items=items,
        all_references_and_rom_pointers_valid=True,all_individual_battle_effects_tested=False)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=audit(a.source);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');print(r)
