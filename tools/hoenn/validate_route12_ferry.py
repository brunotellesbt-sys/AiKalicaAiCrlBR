"""Talk to the shipyard captain and complete a return ferry trip with native menus."""
from pathlib import Path
import hashlib
import json
ROOT=Path(__file__).resolve().parents[2]
prefix=(ROOT/'tools/hoenn/validate_eastern_union.py').read_text().split('seams=[];cliffs=[]')[0]
prefix=prefix.replace("names=[r['map'] for r in report['rectangles']]", "names=[r['map'] for r in report['rectangles']]+['JourneyRoute12Shipyard']")
exec(compile(prefix,str(ROOT/'tools/hoenn/validate_eastern_union.py'),'exec'))
getter=s['Menu_GetCursorPos'];ldr=lib.read16(getter);assert ldr&0xF800==0x4800
cursor=lib.read32(((getter+4)&~3)+(ldr&255)*4)+2

def menu():return task('Task_HandleMultichoiceInput')
def await_menu():
 for _ in range(300):
  if menu():return
  press(1)
 raise AssertionError('Captain menu did not open')
def choose(i):
 step(16)
 for _ in range(8):
  if lib.read8(cursor)==i:break
  press(64 if lib.read8(cursor)>i else 128)
 assert lib.read8(cursor)==i;press(1)
def arrived(name):
 for _ in range(400):
  if location()==map_id(name) and idle():return
  press(1)
 raise AssertionError(('Ferry arrival failed',name,location(),position()))
warp('JourneyRoute12Shipyard',24,39);native('SetPlayerAvatarTransitionFlags',1);step(30)
step(4,32);step(20);press(1);await_menu();picture('shipyard-captain-menu');choose(1)
arrived('SlateportCity_Harbor');assert position()==(16,14);picture('shipyard-ferry-slateport')
step(4,64);step(20);press(1);await_menu();picture('slateport-return-menu');choose(0)
arrived('JourneyRoute12Shipyard');assert position()==(24,39);picture('shipyard-ferry-return')
assert native('TrySavingData',0,max_frames=6000)==1;step(60)
assert native('LoadGameSave',0,max_frames=6000)==1
lib.write32(s['gMain']+4,s['CB2_ContinueSavedGame']|1);step(1500);finish()
assert location()==map_id('JourneyRoute12Shipyard') and position()==(24,39)
picture('shipyard-ferry-return-continue');lib.stop()
(args.output/'route12-ferry.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),actual_captain_interactions=True,actual_menu_choices=True,shipyard_to_slateport_and_return=True,arrival=[24,39],return_save_continue=True,initial_party_and_placement_are_fixtures=True,full_campaign_playthrough=False),indent=2)+'\n')
print('Shipyard ferry actual captain menus, roundtrip and Continue passed',flush=True)
