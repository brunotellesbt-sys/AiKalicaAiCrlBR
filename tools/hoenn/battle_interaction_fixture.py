"""Compile the ROM's ABI for native battle interaction fixtures.

No offsets, enum IDs or packed C field layouts are inferred from another build.
The expected mechanics live in the validator, not in this ABI adapter.
"""
import re
import struct
import subprocess
import tempfile
from pathlib import Path
from audit_battle_database import compiled

ROOT = Path(__file__).resolve().parents[2]


def compile_probe(source, constants):
    fields = {
        'mon_size': 'sizeof(struct BattlePokemon)',
        'battle_size': 'sizeof(struct BattleStruct)',
        'resources_size': 'sizeof(struct BattleResources)',
        'history_size': 'sizeof(struct BattleHistory)',
        'scripts_size': 'sizeof(struct BattleScriptsStack)',
        'callbacks_size': 'sizeof(struct BattleCallbacksStack)',
        'scripts_ptr': 'offsetof(struct BattleResources,battleScriptsStack)',
        'callbacks_ptr': 'offsetof(struct BattleResources,battleCallbackStack)',
        'ctx_size': 'sizeof(struct DamageContext)',
        'ctx_abilities': 'offsetof(struct DamageContext,abilities)',
        'ctx_holds': 'offsetof(struct DamageContext,holdEffects)',
        'ctx_field': 'offsetof(struct DamageContext,fieldStatuses)',
        'ctx_modifier': 'offsetof(struct DamageContext,typeEffectivenessModifier)',
        'party_action': 'offsetof(struct PartyMenu,action)',
        'party_slot2': 'offsetof(struct PartyMenu,slotId2)',
        'bag_pocket': 'offsetof(struct BagPosition,pocket)',
        'protect_size': 'sizeof(struct ProtectStruct)',
        'special_size': 'sizeof(struct SpecialStatus)',
        'scripting_size': 'sizeof(struct BattleScripting)',
        'scripting_savedDmg': 'offsetof(struct BattleScripting,savedDmg)',
        'battle_passiveHpUpdate': 'offsetof(struct BattleStruct,passiveHpUpdate)',
        'battle_hp_delta_size': 'sizeof(((struct BattleStruct *)0)->passiveHpUpdate[0])',
        'ai_size': 'sizeof(struct AiLogicData)',
        'ai_abilities': 'offsetof(struct AiLogicData,abilities)',
        'ai_items': 'offsetof(struct AiLogicData,items)',
        'ai_holds': 'offsetof(struct AiLogicData,holdEffects)',
        'side_size': 'sizeof(struct SideTimer)',
        'cv_size': 'sizeof(struct BattleCalcValues)',
        'cv_abilities': 'offsetof(struct BattleCalcValues,abilities)',
        'cv_holds': 'offsetof(struct BattleCalcValues,holdEffects)',
    }
    for field in ['species', 'attack', 'defense', 'speed', 'spAttack', 'spDefense',
                  'moves', 'statStages', 'ability', 'types', 'pp', 'hp', 'level',
                  'maxHP', 'item', 'status1', 'volatiles']:
        fields['mon_' + field] = f'offsetof(struct BattlePokemon,{field})'
    declarations = []
    for key, expression in fields.items():
        declarations.append(f'const u32 abi_{key}={expression};')
    for name in sorted(constants):
        declarations.append(f'const u32 constant_{name}={name};')
    masks = {}
    volatile_fields = ['gastroAcid', 'neutralizingGas', 'transformed', 'root', 'smackDown',
        'magnetRise', 'telekinesis', 'embargo', 'confusionTurns', 'healBlock', 'tarShot',
        'foresight', 'slowStartTimer', 'unburdenActive', 'boosterEnergyActivated',
        'paradoxBoostedStat', 'focusEnergy', 'laserFocus', 'glaiveRush', 'endured',
        'encoreTimer', 'encoredMove', 'tauntTimer', 'disableTimer', 'disabledMove',
        'torment', 'infatuation']
    for name in volatile_fields:
        key='mon_'+name
        declarations.append(f'const struct BattlePokemon mask_{key}={{.volatiles.{name}=~0u}};')
        masks[key]='mon'
    declarations.append('const struct BattleStruct mask_battle_moldBreakerActive={.moldBreakerActive=1};')
    masks['battle_moldBreakerActive']='battle'
    declarations.append('const struct ProtectStruct mask_protect_pranksterElevated={.pranksterElevated=1};')
    masks['protect_pranksterElevated']='protect'
    declarations.append('const struct SideTimer mask_side_spikesAmount={.spikesAmount=~0u};')
    declarations.append('const struct SideTimer mask_side_toxicSpikesAmount={.toxicSpikesAmount=~0u};')
    masks['side_spikesAmount']='side';masks['side_toxicSpikesAmount']='side'
    declarations.append('const struct SaveBlock2 mask_save_sceneOff={.optionsBattleSceneOff=1};')
    declarations.append('const struct SaveBlock2 mask_save_textSpeed={.optionsTextSpeed=~0u};')
    masks['save_sceneOff']='save';masks['save_textSpeed']='save'
    for name in ['battlerAtk','battlerDef','move']:
        declarations.append(f'const struct BattleCalcValues mask_cv_{name}={{.{name}=~0u}};')
        masks['cv_'+name]='cv'
    for name in ['battlerAtk', 'battlerDef', 'move', 'chosenMove', 'moveType', 'weather',
                 'isCrit', 'randomFactor', 'aiCalc']:
        declarations.append(f'const struct DamageContext mask_ctx_{name}={{.{name}=~0u}};')
        masks['ctx_'+name]='ctx'
    code = ('#include "global.h"\n#include "battle.h"\n#include "battle_util.h"\n'
        '#include "battle_hold_effects.h"\n#include "constants/abilities.h"\n'
        '#include "constants/items.h"\n#include "constants/daycare.h"\n#include "party_menu.h"\n#include "item_menu.h"\n#include "constants/party_menu.h"\n#include "constants/battle_move_resolution.h"\n#include <stddef.h>\n' + '\n'.join(declarations))
    toolchain=ROOT/'.local'
    with tempfile.TemporaryDirectory(dir='/tmp',prefix='battle-interaction-abi-') as d:
        d=Path(d);(d/'probe.c').write_text(code)
        subprocess.run([str(toolchain/'arm-gcc/usr/bin/arm-none-eabi-gcc'), '-w', '-S',
            '-iquote', str(source/'include'), '-mabi=apcs-gnu', str(d/'probe.c'),
            '-o', str(d/'probe.s')], check=True)
        subprocess.run([str(toolchain/'arm-binutils/usr/bin/arm-none-eabi-as'), '-mcpu=arm7tdmi',
            '-o', str(d/'probe.o'), str(d/'probe.s')], check=True)
        subprocess.run([str(toolchain/'arm-binutils/usr/bin/arm-none-eabi-objcopy'), '-O', 'binary',
            '--only-section=.rodata', str(d/'probe.o'), str(d/'probe.bin')], check=True)
        symbols=subprocess.check_output([str(toolchain/'arm-binutils/usr/bin/arm-none-eabi-nm'),
            '-S', str(d/'probe.o')], text=True)
        data=(d/'probe.bin').read_bytes()
    blobs={name:data[int(at,16):int(at,16)+int(size,16)]
        for at,size,name in re.findall(r'^(\w+) (\w+) R (\S+)$',symbols,re.M)}
    abi={name:struct.unpack('<I',blobs['abi_'+name])[0] for name in fields}
    values={name:struct.unpack('<I',blobs['constant_'+name])[0] for name in constants}
    packed={}
    for name,base in masks.items():
        raw=int.from_bytes(blobs['mask_'+name],'little')
        shift=(raw&-raw).bit_length()-1;width=raw.bit_length()-shift
        assert raw==((1<<width)-1)<<shift, name
        packed[name]=(base,shift//8,shift%8,width,(shift%8+width+7)//8)
    return abi,values,packed


class BattleFixture:
    def __init__(self,source,lib,symbols,native,party,constants):
        self.lib,self.s,self.native,self.party=lib,symbols,native,party
        self.abi,self.constants,self.packed=compile_probe(source,constants)
        self.database=compiled(source)
        self.addresses={'mon':symbols['gBattleMons'],'protect':symbols['gProtectStructs']}
        self.addresses['ctx']=native('AllocZeroed_',self.abi['ctx_size'],0)
        assert self.addresses['ctx']
        self.addresses['cv']=native('AllocZeroed_',self.abi['cv_size'],0)
        self.addresses['side']=symbols['gSideTimers']
        self.ai=native('AllocZeroed_',self.abi['ai_size'],0);assert self.ai
        lib.write32(symbols['gAiLogicData'],self.ai)
        for field,size in [('gBattleStruct','battle_size'),('gBattleResources','resources_size'),
                           ('gBattleHistory','history_size')]:
            ptr=native('AllocZeroed_',self.abi[size],0);assert ptr
            lib.write32(symbols[field],ptr)
            if field=='gBattleStruct':self.addresses['battle']=ptr
            if field=='gBattleResources':self.resources=ptr
        self.stacks=[]
        for field,size in [('scripts_ptr','scripts_size'),('callbacks_ptr','callbacks_size')]:
            ptr=native('AllocZeroed_',self.abi[size],0);assert ptr
            lib.write32(self.resources+self.abi[field],ptr)
            self.stacks.append((ptr,self.abi[size]))
        self.reset()

    def c(self,name):return self.constants[name]
    def write(self,at,data):
        for i,b in enumerate(data):self.lib.raw8(at+i,b)
    def mon(self,battler,field,value,size=2):
        at=self.addresses['mon']+battler*self.abi['mon_size']+self.abi['mon_'+field]
        self.write(at,value.to_bytes(size,'little'))
    def read_mon(self,battler,field,size=2):
        at=self.addresses['mon']+battler*self.abi['mon_size']+self.abi['mon_'+field]
        return int.from_bytes(bytes(self.lib.read8(at+i) for i in range(size)),'little')
    def bits(self,name,value,battler=0):
        base,off,shift,width,size=self.packed[name]
        assert 0 <= value < (1<<width), (name,value,width)
        stride=self.abi[base+'_size'] if base in ('mon','protect','side') else 0
        at=self.addresses[base]+battler*stride+off
        raw=int.from_bytes(bytes(self.lib.read8(at+i) for i in range(size)),'little')
        mask=((1<<width)-1)<<shift
        self.write(at,((raw&~mask)|((value<<shift)&mask)).to_bytes(size,'little'))
    def types(self,battler,*names):
        types=[self.c(n) for n in names]
        self.mon(battler,'types',int.from_bytes(bytes(types+[types[-1]]*(2-len(types))+[self.c('TYPE_MYSTERY')]),'little'),3)
    def reset(self,double=False):
        lib,s=self.lib,self.s
        self.write(self.addresses['battle'],bytes(self.abi['battle_size']))
        self.write(s['gBattleMons'],bytes(4*self.abi['mon_size']))
        self.write(s['gProtectStructs'],bytes(4*self.abi['protect_size']))
        self.write(s['gSpecialStatuses'],bytes(4*self.abi['special_size']))
        self.write(s['gBattleScripting'],bytes(self.abi['scripting_size']))
        self.write(self.ai,bytes(self.abi['ai_size']))
        self.write(s['gSideTimers'],bytes(2*self.abi['side_size']))
        for ptr,size in self.stacks:self.write(ptr,bytes(size))
        lib.write16(s['gBattleWeather'],0)
        for name in ['gFieldStatuses','gBattleControllerExecFlags']:
            lib.write32(s[name],0)
        lib.write32(s['gBattleTypeFlags'],self.c('BATTLE_TYPE_FRONTIER')|(self.c('BATTLE_TYPE_DOUBLE') if double else 0))
        lib.write8(s['gBattlersCount'],4 if double else 2)
        lib.write8(s['gBattlerAttacker'],0);lib.write8(s['gBattlerTarget'],1)
        lib.write8(s['gCurrentTurnActionNumber'],0)
        self.write(s['gSideStatuses'],bytes(8))
        for battler in range(4):
            lib.write8(s['gBattlerPositions']+battler,battler)
            lib.write8(s['gBattlerByTurnOrder']+battler,battler)
            self.mon(battler,'species',self.c('SPECIES_SNORLAX'))
            for field in ['attack','defense','speed','spAttack','spDefense','hp','maxHP']:self.mon(battler,field,100)
            self.mon(battler,'level',50,1);self.types(battler,'TYPE_NORMAL')
            self.mon(battler,'statStages',int.from_bytes(bytes([6]*8),'little'),8)
            if not double and battler>=2:self.mon(battler,'hp',0)
        lib.write16(s['gCurrentMove'],self.c('MOVE_TACKLE'))

    def context(self,move,ability_atk='ABILITY_NONE',ability_def='ABILITY_NONE',
                hold_atk='HOLD_EFFECT_NONE',hold_def='HOLD_EFFECT_NONE',weather=0,crit=False,
                attacker=0,defender=1):
        if not move.startswith('MOVE_'):move='MOVE_'+move
        at=self.addresses['ctx'];self.write(at,bytes(self.abi['ctx_size']))
        for name,value in [('battlerAtk',attacker),('battlerDef',defender),('move',self.c(move)),
                           ('chosenMove',self.c(move)),('moveType',self.database['moves'][self.c(move)]['type']),
                           ('weather',weather),('isCrit',int(crit)),('aiCalc',1)]:self.bits('ctx_'+name,value)
        for battler in range(4):
            self.lib.write16(at+self.abi['ctx_abilities']+battler*2,
                self.native('GetBattlerAbility',battler))
            self.lib.write8(at+self.abi['ctx_holds']+battler,
                self.native('GetBattlerHoldEffect',battler))
        self.lib.write16(at+self.abi['ctx_abilities']+attacker*2,self.c(ability_atk))
        self.lib.write16(at+self.abi['ctx_abilities']+defender*2,self.c(ability_def))
        self.lib.write8(at+self.abi['ctx_holds']+attacker,self.c(hold_atk))
        self.lib.write8(at+self.abi['ctx_holds']+defender,self.c(hold_def))
        self.lib.write32(at+self.abi['ctx_field'],self.lib.read32(self.s['gFieldStatuses']))
        self.lib.write16(self.s['gCurrentMove'],self.c(move))
        modifier=self.native('CalcTypeEffectivenessMultiplier',at)
        self.lib.write16(at+self.abi['ctx_modifier'],modifier)
        return at

    def ai_cache(self):
        for battler in range(4):
            self.lib.write16(self.ai+self.abi['ai_abilities']+battler*2,
                self.native('GetBattlerAbility',battler))
            self.lib.write8(self.ai+self.abi['ai_holds']+battler,
                self.native('GetBattlerHoldEffect',battler))
            self.lib.write16(self.ai+self.abi['ai_items']+battler*2,self.read_mon(battler,'item'))

    def calc_values(self):
        at=self.addresses['cv'];self.write(at,bytes(self.abi['cv_size']))
        self.bits('cv_battlerAtk',0);self.bits('cv_battlerDef',1)
        self.bits('cv_move',self.c('MOVE_TACKLE'))
        for battler in range(4):
            self.lib.write16(at+self.abi['cv_abilities']+battler*2,self.native('GetBattlerAbility',battler))
            self.lib.write8(at+self.abi['cv_holds']+battler,self.native('GetBattlerHoldEffect',battler))
        return at
