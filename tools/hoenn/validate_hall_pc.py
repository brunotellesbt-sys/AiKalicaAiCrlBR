"""Navigate the native Hall of Fame PC in both regions with one and fifty teams.
Archive contents and championships are fixtures. Physical PC interaction, menu selection,
page/mon navigation, exit, save/reload and archive preservation run natively.
"""
import argparse, hashlib, json, re, struct, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source',type=Path,required=True)
parser.add_argument('--library',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
configuration=parser.parse_args()
sys.argv=[sys.argv[0],'--source',str(configuration.source),'--library',str(configuration.library),
          '--output',str(configuration.output)]
bootstrap=(ROOT/'tools/hoenn/validate_abilities.py').read_text().split('\nability_field,')[0]
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_abilities.py'),'exec'))
champion=abi[111]-0x2A+0x1F;game_clear=abi[111]-0x2A+4
native('EnableNationalPokedex')

def set_flag(flag,enabled):
 address=save()+4720+flag//8;old=lib.read8(address);mask=1<<(flag&7)
 lib.write8(address,old|mask if enabled else old&~mask)

def symbols(name):
 return {int(a,16) for a,kind,n in re.findall(r'^(\w+) (\w) (\S+)$',raw,re.M) if n==name}

def task_id(name):
 for i in range(16):
  address=s['gTasks']+i*40
  if lib.read8(address+4) and (lib.read32(address)&~1) in symbols(name):return i
 return None

def wait_task(name,limit=300):
 for _ in range(limit):
  index=task_id(name)
  if index is not None:return index
  step(10)
 picture('failed-'+name)
 raise AssertionError(('task not ready',name,hex(lib.read32(s['gMain']+4))))

def field_idle():
 return (lib.read32(s['gMain']+4)&~1)==s['CB2_Overworld'] and lib.read8(s['sGlobalScriptContextStatus'])==2 and not lib.read8(s['sLockFieldControls'])

def wait_idle():
 for _ in range(300):
  if field_idle():return
  step(10)
 picture('pc-logoff-failed')
 raise AssertionError(('PC did not return control to the field',hex(lib.read32(s['gMain']+4)),lib.read8(s['sGlobalScriptContextStatus']),lib.read8(s['sLockFieldControls']),task_id('Task_HandleMultichoiceInput'),lib.read16(s['gSpecialVar_Result'])))

def archive_read():
 pointer=native('AllocZeroed_',8192,0);assert pointer
 assert lib.read32(s['gHoFSaveBuffer'])==0
 lib.write32(s['gHoFSaveBuffer'],pointer)
 try:
  assert native('LoadGameSave',3,max_frames=6000)==1
  return bytes(lib.read8(pointer+i) for i in range(7200))
 finally:
  lib.write32(s['gHoFSaveBuffer'],0);native('Free',pointer)

def install(count):
 pointer=native('AllocZeroed_',8192,0);assert pointer
 assert lib.read32(s['gHoFSaveBuffer'])==0
 lib.write32(s['gHoFSaveBuffer'],pointer)
 # Six valid ordinary species include the latest generation's canonical entry.
 catalog=json.loads((ROOT/'mods/hoenn/history-validation/catalog.json').read_text())
 species=[catalog['canonical_species'][str(n)] for n in [1,25,252,387,658,1025]]
 records=[]
 for index in range(count):
  mons=[]
  for slot,spec in enumerate(species):
   mons.append(struct.pack('<IIHB',1000+index,2000+index*6+slot,spec<<1,50)+bytes([0xBB,0xFF])+bytes(11))
  record=b''.join(mons);assert len(record)==144
  records.append(record)
  for offset,b in enumerate(record):lib.write8(pointer+index*144+offset,b)
 native('SetGameStat',10,count-1)
 assert native('TrySavingData',3,max_frames=6000)==1
 lib.write32(s['gHoFSaveBuffer'],0);native('Free',pointer)
 return b''.join(records)+bytes(7200-count*144),species

pc_positions={}
def open_menu(map_name):
 if map_name not in pc_positions:
  data=json.loads((source/'data/maps'/map_name/'map.json').read_text())
  layout=layouts[data['layout']]
  for y in range(layout['height']):
   for x in range(layout['width']):
    behavior=native('MapGridGetMetatileBehaviorAt',x+7,y+7)
    if native('MetatileBehavior_IsPC',behavior):
     pc_positions[map_name]=(x,y);break
   if map_name in pc_positions:break
  assert map_name in pc_positions,'No PC tile found'
 x,y=pc_positions[map_name]
 warp(map_name,x,y+1)
 step(4,64);step(30);press(1)
 for _ in range(100):
  if task_id('Task_HandleMultichoiceInput') is not None:return
  press(1)
 raise AssertionError('PC menu did not open')

cases=[]
for count in [1,50]:
 expected,species=install(count)
 for f in (champion,game_clear,0x1AC2,0x1AB8):set_flag(f,True)
 assert native('TrySavingData',0,max_frames=6000)==1
 for region,map_name in [('kanto','ViridianCity_PokemonCenter_1F_Frlg'),('hoenn','OldaleTown_PokemonCenter_1F')]:
  warp(map_name,5,5)
  open_menu(map_name);picture(f'{region}-{count}-pc-menu')
  press(128);press(128);press(1)
  index=wait_task('Task_HofPC_HandleInput')
  def state():return [lib.read16(s['gTasks']+index*40+8+2*i) for i in range(5)]
  assert state()[0]==count-1 and state()[1]==count and state()[2]==0 and state()[4]==6,state()
  picture(f'{region}-{count}-newest-team')
  buffer=lib.read32(s['gHoFSaveBuffer']);assert buffer
  assert bytes(lib.read8(buffer+i) for i in range(7200))==expected
  # UP at first mon and DOWN at last mon must stop at the boundary.
  press(64);assert state()[2]==0
  for mon in range(1,6):
   press(128);wait_task('Task_HofPC_HandleInput');assert state()[2]==mon,state()
  press(128);assert state()[2]==5
  picture(f'{region}-{count}-dex-1025')
  for mon in range(4,-1,-1):
   press(64);wait_task('Task_HofPC_HandleInput');assert state()[2]==mon,state()
  for page in range(count-2,-1,-1):
   press(1);wait_task('Task_HofPC_HandleInput')
   assert state()[0]==page and state()[1]==page+1 and state()[2]==0,state()
  picture(f'{region}-{count}-oldest-team')
  # With a single team, also exercise the explicit B exit.
  press(2 if count==1 else 1)
  wait_task('Task_HandleMultichoiceInput');step(120);picture(f'{region}-{count}-returned-menu')
  press(2);wait_idle()
  assert lib.read32(s['gHoFSaveBuffer'])==0
  assert archive_read()==expected
  assert native('GetGameStat',10)==count
  assert native('TrySavingData',0,max_frames=6000)==1
  assert native('LoadGameSave',0,max_frames=6000)==1;step(30)
  assert archive_read()==expected
  picture(f'{region}-{count}-field-after-pc')
  cases.append(dict(region=region,records=count,pages_visited=count,mons_navigated=6,
                    newest_and_oldest_correct=True,mon_boundaries_respected=True,
                    menu_return_and_logoff=True,exit='B' if count==1 else 'A_at_oldest',
                    archive_unchanged=True,native_flash_save_reload=True,viewed_species=species))
  print('Native Hall PC passed:',region,count,flush=True)
lib.stop()
report=dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
            cases=cases,archive_and_championships_are_fixtures=True,physical_pc_interaction=True,national_dex_enabled=True,
            native_pc_menu_and_navigation=True,full_campaign_playthrough=False)
(args.output/'hall-pc.json').write_text(json.dumps(report,indent=2)+'\n')
