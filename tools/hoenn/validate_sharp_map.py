"""Verify exact pixel zoom and restore in the real Pokédex and map UI."""
from pathlib import Path
import hashlib,json
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
text=(ROOT/'tools/hoenn/validate_world_dex.py').read_text();prefix=text.split("ptr=lib.read32(s['sWorldDex']);assert lib.read8(ptr+38)>0")[0]
exec(compile(prefix,str(ROOT/'tools/hoenn/validate_world_dex.py'),'exec'))
ptr=lib.read32(s['sWorldDex']);base=Image.open(args.output/'pokedex-world-area.png').convert('RGB').crop((8,24,232,136))
press(1);step(120);assert lib.read8(ptr+40)==1;picture('pokedex-world-area-zoom-2x')
left,top=lib.read8(ptr+42),lib.read8(ptr+43)
detail=(source/'.journey-complete-marine-atlas').exists()
if detail:
 import re
 from prepare_world_dex_map import COLORS
 h=(source/'src/data/journey_world_map.h').read_text();pixels=bytes(map(int,re.search(r'sWorldDetailPixels\[\] = \{([^}]+)',h)[1].split(',')))
 # mGBA expands the GBA's 5-bit channels to 8-bit RGB; palette index zero
 # is transparent on Dex BG3 and uses the black backdrop.
 rgb=[(0,0,0)]+[tuple((v&248)|(v>>5) for v in c) for c in COLORS[1:]]
 art=Image.new('P',(448,224));art.putpalette([v for c in rgb for v in c]+[0]*720);art.putdata([v for b in pixels for v in [b&15,b>>4]])
 expected=art.convert('RGB').crop((2*left,2*top,2*left+224,2*top+112))
else:expected=base.crop((left,top,left+112,top+56)).resize((224,112),Image.Resampling.NEAREST)
actual=Image.open(args.output/'pokedex-world-area-zoom-2x.png').convert('RGB').crop((8,24,232,136))
difference=sum(a!=b for a,b in zip(expected.getdata(),actual.getdata()))
# Marker overlays remain eight pixels, so they intentionally do not scale.
assert difference<512,('Zoom does not match its native atlas pixels',difference,left,top)
press(1);step(80);assert lib.read8(ptr+40)==0;picture('pokedex-world-area-zoom-restored')
press(2);step(160)
for _ in range(10):
 if lib.read32(s['gMain']+4)&~1==s['CB2_Overworld']:break
 press(2);step(120)
assert lib.read32(s['gMain']+4)&~1==s['CB2_Overworld']
opening=(ROOT/'tools/hoenn/validate_world_map.py').read_text().split('checks=[]')[0].split('def callback():')[1]
exec('def callback():'+opening)
press(2);step(160)
open_map();point=lib.read32(s['sJourneyWorldMap']);old=(lib.read8(point+2056),lib.read8(point+2057))
press(256);step(90);assert lib.read8(point+2062)==1;picture('menu-world-map-zoom-2x')
assert (lib.read8(point+2056),lib.read8(point+2057))==old
press(256);step(90);assert lib.read8(point+2062)==0;picture('menu-world-map-zoom-restored')
press(2);wait_for(lambda:callback()==s['CB2_Overworld'])
assert hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest()==initial_rom_sha
lib.stop();(args.output/'sharp-map.json').write_text(json.dumps(dict(passed=True,rom_sha256=initial_rom_sha,zoom_factor=2,native_detail_zoom=detail,nearest_neighbor_pixel_differences_excluding_marker_scaling=difference,pokedex_zoom_and_restore=True,menu_map_zoom_and_restore=True,cursor_location_preserved=True,controller_ui=True,initial_flags_party_and_location_are_fixtures=True),indent=2)+'\n')
print('Native world map and Dex exact 2x zoom passed',flush=True)
