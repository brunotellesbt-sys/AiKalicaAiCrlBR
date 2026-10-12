"""Exercise native Mega form changes and the actual party cleanup for all Megas.

Battle struct, live battler data and original-species tracking are explicit fixtures. This verifies
engine transformation/recalculation, rather than claiming 91 controller battles.
"""
import hashlib,json,re,struct,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_crossover_opponents.py').read_text().split('\n# Story state is')[0]
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_crossover_opponents.py'),'exec'))
with tempfile.TemporaryDirectory(dir='/tmp') as temp:
 p=Path(temp);names=['sizeof(struct SpeciesInfo)','offsetof(struct SpeciesInfo,formChangeTable)','sizeof(struct FormChange)','FORM_CHANGE_TERMINATOR','FORM_CHANGE_BATTLE_MEGA_EVOLUTION_ITEM','FORM_CHANGE_BATTLE_MEGA_EVOLUTION_MOVE','sizeof(struct BattleStruct)','offsetof(struct BattleStruct,partyState)','0','B_TRAINER_0','MON_DATA_SPECIES','MON_DATA_HELD_ITEM','MON_DATA_MOVE1','MON_DATA_HP','MON_DATA_MAX_HP','MON_DATA_ATK','MON_DATA_DEF','MON_DATA_SPEED','MON_DATA_SPATK','MON_DATA_SPDEF']
 (p/'probe.c').write_text('#include "global.h"\n#include "pokemon.h"\n#include "battle.h"\n#include "constants/form_change_types.h"\n#include <stddef.h>\nconst u32 probe[]={'+','.join(names)+'};\nconst struct PartyState bit_probe={.changedSpecies=1};\n')
 subprocess.run([str(ROOT/'.local/arm-gcc/usr/bin/arm-none-eabi-gcc'),'-S','-iquote',str(source/'include'),'-mabi=apcs-gnu',str(p/'probe.c'),'-o',str(p/'probe.s')],check=True)
 probe=[int(x) for x in re.findall(r'\.word\s+(\d+)',(p/'probe.s').read_text().split('probe:',1)[1].split('.size',1)[0])]
 subprocess.run([str(ROOT/'.local/arm-binutils/usr/bin/arm-none-eabi-as'),'-mcpu=arm7tdmi',str(p/'probe.s'),'-o',str(p/'probe.o')],check=True)
 subprocess.run([str(ROOT/'.local/arm-binutils/usr/bin/arm-none-eabi-objcopy'),'-O','binary','--only-section=.rodata',str(p/'probe.o'),str(p/'probe.bin')],check=True)
 names_out=subprocess.check_output([str(ROOT/'.local/arm-binutils/usr/bin/arm-none-eabi-nm'),'-n',str(p/'probe.o')],text=True)
 bit_at=int(re.search(r'^(\w+) \w bit_probe$',names_out,re.M)[1],16)
 bit=struct.unpack_from('<I',(p/'probe.bin').read_bytes(),bit_at)[0];changed_shift=bit.bit_length()-1;changed_mask=2047<<changed_shift
rom=(source/'pokeemerald.gba').read_bytes();ref=json.loads((ROOT/'tools/hoenn/data/species-base-stats.json').read_text());catalog=json.loads((ROOT/'tools/hoenn/catalog_metadata.json').read_text())
info=database['compiled_layout']['symbols']['gSpeciesInfo'];sources={}
for sid,row in ref['species'].items():
 if row['mega']:continue
 ptr=struct.unpack_from('<I',rom,info+int(sid)*probe[0]+probe[1])[0]-0x08000000
 if not 0<=ptr<len(rom):continue
 for k in range(256):
  at=ptr+k*probe[2];method,target,param=struct.unpack_from('<HHH',rom,at)
  if method==probe[3]:break
  if method in probe[4:6] and str(target) in ref['species'] and ref['species'][str(target)]['mega']:
   sources.setdefault(target,dict(parent=int(sid),method=method,param=param))
 else:raise AssertionError(('Unterminated form table',sid))
mega_ids={int(sid) for sid,row in ref['species'].items() if row['mega']}
assert set(sources)==mega_ids,(len(sources),sorted(mega_ids-set(sources)))
battle=native('AllocZeroed_',probe[6],0);assert battle
old_battle=lib.read32(s['gBattleStruct']);lib.write32(s['gBattleStruct'],battle)
scratch=s['gStringVar4']+800
fields=probe[13:20]
def set_data(field,value):
 lib.write32(scratch,value);native('SetMonData',party,field,scratch)
def snapshot():
 return dict(species=native('GetMonData3',party,probe[10],0),stats=[native('GetMonData3',party,f,0) for f in fields],ability=native('GetMonAbility',party))
results=[]
for mega in sorted(mega_ids):
 row=sources[mega];parent=row['parent'];originals=[parent]
 if ref['species'][str(mega)]['species']=='SPECIES_ZYGARDE_MEGA':
  originals=[sp['id'] for sp in catalog['species'].values() if sp['name'] in ['SPECIES_ZYGARDE_10_POWER_CONSTRUCT','SPECIES_ZYGARDE_50_POWER_CONSTRUCT']]
 for original in originals:
  for i in range(6*abi[2]):lib.write8(party+i,0)
  lib.write8(s['gPartiesCount'],0);assert native('ScriptGiveMon',original,50,0)==0
  set_data(probe[11],row['param'] if row['method']==probe[4] else 0)
  if row['method']==probe[5]:set_data(probe[12],row['param'])
  before=snapshot()
  if original!=parent:set_data(probe[10],parent);native('CalculateMonStats',party)
  lib.write32(battle+probe[7],original<<changed_shift)
  move_based = row['method']==probe[5]
  native('PokemonToBattleMon',party,s['gBattleMons'])
  assert native('GetBattleFormChangeTargetSpecies',0,row['method'],before['ability'])==mega,(mega,'battle form target')
  assert native('TryBattleFormChange',0,row['method'],before['ability'])==1,(mega,parent)
  transformed=snapshot();assert transformed['species']==mega,(mega,transformed)
  assert native('TryRevertPartyMonFormChange',0)==1,(mega,'cleanup did not revert')
  after=snapshot();assert after==before,(mega,before,after)
  assert lib.read32(battle+probe[7])&changed_mask==0,(mega,'original species tracking not cleared')
  results.append(dict(mega=mega,parent=parent,original=original,move_gated=move_based,before=before,transformed=transformed,after=after))
 print('Mega cleanup passed:',ref['species'][str(mega)]['reference_name'],flush=True)
lib.write32(s['gBattleStruct'],old_battle);native('Free',battle)
assert hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest()==initial_sha
lib.stop();(args.output/'mega-reversion.json').write_text(json.dumps(dict(passed=True,rom_sha256=initial_sha,megas_checked=len(mega_ids),checks=results,base_form_stats_and_ability_restored=True,original_species_tracking_cleared=True,native_party_cleanup=True,battle_struct_fixture=True,all_mega_controller_battles=False),indent=2)+'\n')
print('All Mega native transformations and end-of-battle cleanup passed',flush=True)
