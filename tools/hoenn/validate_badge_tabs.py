"""Open the actual Trainer Card and alternate the two eight-badge pages."""
import hashlib,json
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
prefix=(ROOT/'tools/hoenn/validate_world_map.py').read_text().split('\nchecks=[]')[0]
exec(compile(prefix,str(ROOT/'tools/hoenn/validate_world_map.py'),'exec'))
initial_rom_sha=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest()
card_flags=[]
for name in ['RUSTBORO','DEWFORD','MAUVILLE','LAVARIDGE','PETALBURG','FORTREE','MOSSDEEP','SOOTOPOLIS']:
    import re
    card_flags.append(int(re.search(r'#define FLAG_DEFEATED_'+name+r'_GYM\s+(0x\w+)',(source/'include/constants/flags.h').read_text())[1],16))
for flag in list(range(0x1AB0,0x1AB8))+[lib.read16(s['gBadgeFlags']+2*i) for i in range(8)]+card_flags:
    address=save()+FLAG_OFFSET+flag//8;lib.write8(address,lib.read8(address)|(1<<(flag&7)))
press(8);wait_for(lambda:lib.read8(s['sNumStartMenuActions'])>0);step(80)
actions=[lib.read8(s['sCurrentStartMenuActions']+i) for i in range(lib.read8(s['sNumStartMenuActions']))]
index=next(i for i,value in enumerate(actions) if lib.read32(s['sStartMenuItems']+value*8+4)&~1==s['StartMenuPlayerNameCallback'])
for _ in range(12):
    pos=lib.read8(s['sStartMenuCursorPos'])
    if pos==index:break
    press(128 if pos<index else 64)
assert lib.read8(s['sStartMenuCursorPos'])==index
press(1);wait_for(lambda:callback()==s['CB2_TrainerCard']);step(200)
picture('badge-tabs-first')
press(256);step(100);picture('badge-tabs-second')
press(512);step(100);picture('badge-tabs-restored')
def band(name):return Image.open(args.output/(name+'.png')).convert('RGB').crop((24,120,224,138)).tobytes()
first=band('badge-tabs-first');second=band('badge-tabs-second');restored=band('badge-tabs-restored')
assert first!=second and first==restored,'Badge pages did not alternate and restore'
press(4);step(100);picture('badge-tabs-select');assert band('badge-tabs-select')==second
press(2);wait_for(lambda:callback()==s['CB2_Overworld']);step(60)
assert hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest()==initial_rom_sha
lib.stop()
(args.output/'badge-tabs.json').write_text(json.dumps(dict(passed=True,rom_sha256=initial_rom_sha,
    actual_start_menu_and_card=True,left_right_select_alternate=True,eight_badges_per_page=True,
    initial_badge_flags_are_fixture=True),indent=2)+'\n')
