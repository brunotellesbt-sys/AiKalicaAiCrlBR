"""Controller helper that respects native PP, Disable, Encore and Torment."""
import re,subprocess,tempfile
from pathlib import Path
from audit_battle_database import compiled
ROOT=Path(__file__).resolve().parents[2]
class CupController:
    def __init__(self,source,lib,symbols):
        self.lib,self.symbols=lib,symbols;self.database=compiled(source);self.avoided=0
        with tempfile.TemporaryDirectory(dir='/tmp') as temporary:
            p=Path(temporary);compiler=str(ROOT/'.local/arm-gcc/usr/bin/arm-none-eabi-gcc')
            fields=['offsetof(struct BattlePokemon,moves)','offsetof(struct BattlePokemon,pp)',
                'offsetof(struct BattlePokemon,spAttack)','offsetof(struct Pokemon,spAttack)',
                'offsetof(struct PartyMenu,slotId)','offsetof(struct BattlePokemon,species)','sizeof(struct BattlePokemon)',
                'offsetof(struct BattlePokemon,ability)','ABILITY_LEVITATE','offsetof(struct BattlePokemon,item)','offsetof(struct BattleStruct,choicedMove)',
                'ITEM_CHOICE_BAND','ITEM_CHOICE_SCARF','ITEM_CHOICE_SPECS','ABILITY_GORILLA_TACTICS']
            code='#include "global.h"\n#include "pokemon.h"\n#include "battle.h"\n#include "party_menu.h"\n#include "constants/abilities.h"\n#include "constants/items.h"\n#include <stddef.h>\nconst u32 cup_abi[]={'+','.join(fields)+'};\n'
            code+=''.join('const struct BattlePokemon probe_'+f+'={.volatiles.'+f+'=~0u};\n' for f in ['disabledMove','disableTimer','encoredMove','encoreTimer','encoredMovePos','torment','tormentTimer','tauntTimer','mimickedMoves','transformed','multipleTurns','bideTurns'])
            (p/'probe.c').write_text(code)
            subprocess.run([compiler,'-w','-S','-iquote',str(source/'include'),'-mabi=apcs-gnu',str(p/'probe.c'),'-o',str(p/'probe.s')],check=True)
            self.abi=[int(v) for v in re.findall(r'\.word\s+(\d+)',(p/'probe.s').read_text().split('cup_abi:',1)[1].split('.size',1)[0])]
            subprocess.run([str(ROOT/'.local/arm-binutils/usr/bin/arm-none-eabi-as'),'-mcpu=arm7tdmi','-o',str(p/'probe.o'),str(p/'probe.s')],check=True)
            subprocess.run([str(ROOT/'.local/arm-binutils/usr/bin/arm-none-eabi-objcopy'),'-O','binary','--only-section=.rodata',str(p/'probe.o'),str(p/'probe.bin')],check=True)
            names=subprocess.check_output([str(ROOT/'.local/arm-binutils/usr/bin/arm-none-eabi-nm'),'-S',str(p/'probe.o')],text=True)
            probes=(p/'probe.bin').read_bytes();self.fields={}
            for address,size,field in re.findall(r'^(\w+) (\w+) R probe_(\w+)$',names,re.M):
                at=int(address,16);mask=int.from_bytes(probes[at:at+int(size,16)],'little')
                shift=(mask&-mask).bit_length()-1;bits=mask.bit_length()-shift
                assert mask==((1<<bits)-1)<<shift
                self.fields[field]=(shift//8,shift%8,(1<<bits)-1,(shift%8+bits+7)//8)
    def volatile(self,field):
        offset,shift,mask,size=self.fields[field];base=self.symbols['gBattleMons']
        value=int.from_bytes(bytes(self.lib.read8(base+offset+i) for i in range(size)),'little')
        return (value>>shift)&mask
    def set_volatile(self,field,value,battler=0):
        offset,shift,mask,size=self.fields[field]
        at=self.symbols['gBattleMons']+battler*self.abi[6]+offset
        raw=int.from_bytes(bytes(self.lib.read8(at+i) for i in range(size)),'little')
        raw=(raw&~(mask<<shift))|((value&mask)<<shift)
        for i,b in enumerate(raw.to_bytes(size,'little')):self.lib.write8(at+i,b)
    def choose_move(self):
        lib,s=self.lib,self.symbols;base=s['gBattleMons'];scores=[]
        foe=lib.read16(base+self.abi[6]+self.abi[5])
        foe_types=self.database['species'][foe]['types']
        foe_ability=lib.read16(base+self.abi[6]+self.abi[7])
        immunities={1:{8},2:{8},4:{9},5:{3},8:{1},14:{5},15:{18},17:{19}}
        disabled=self.volatile('disabledMove')
        encored=self.volatile('encoredMove') if self.volatile('encoreTimer') else 0
        last=lib.read16(s['gLastMoves']) if self.volatile('torment') else 0
        item=lib.read16(base+self.abi[9]);ability=lib.read16(base+self.abi[7])
        choice=lib.read16(lib.read32(s['gBattleStruct'])+self.abi[10])
        locked=choice not in (0,65535) and (item in self.abi[11:14] or ability==self.abi[14])
        for slot in range(4):
            move=lib.read16(base+self.abi[0]+slot*2);pp=lib.read8(base+self.abi[1]+slot)
            row=self.database['moves'].get(move)
            if not row or not pp or move==disabled or (encored and move!=encored) or (last and move==last) or (locked and move!=choice):
                scores.append(-1);self.avoided+=1;continue
            if self.volatile('tauntTimer') and row['category']==2:
                scores.append(-1);self.avoided+=1;continue
            immune=bool(immunities.get(row['type'],set())&set(foe_types)) or (row['type']==5 and foe_ability==self.abi[8])
            scores.append((0 if immune else 1 if row['category']==2 else 1000)+row['power']*(not immune))
        # If no legal slot remains the engine selects Struggle itself.
        return max(range(4),key=lambda slot:scores[slot])
