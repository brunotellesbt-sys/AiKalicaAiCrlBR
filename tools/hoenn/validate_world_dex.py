"""Open real Pokédex AREA with controls and audit all canonical habitat locations."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_abilities.py').read_text().split('ability_field, froakie')[0]
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_abilities.py'),'exec'))
initial_rom_sha=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest()
native('SetDexPokemonPokenavFlags');assert native('ScriptGiveMon',1,5,0)==0
catalog=json.loads((ROOT/'tools/hoenn/catalog_metadata.json').read_text());counts={}
for national,sid in catalog['canonical_species'].items():
 count=native('JourneyWorldDexLocationCount',sid);assert count>0,(national,sid,'missing world habitat');counts[national]=count
print('All canonical species have integrated AREA locations:',len(counts),flush=True)
def wait(predicate,limit=500):
 for _ in range(limit):
  if predicate():return
  step(8)
 picture('world-dex-failure');raise AssertionError('Timed out waiting for Pokédex AREA')
press(8);wait(lambda:lib.read8(s['sNumStartMenuActions'])>0);step(80)
count=lib.read8(s['sNumStartMenuActions']);actions=[lib.read8(s['sCurrentStartMenuActions']+i) for i in range(count)]
index=next(i for i,v in enumerate(actions) if lib.read32(s['sStartMenuItems']+v*8+4)&~1==s['StartMenuPokedexCallback'])
for _ in range(12):
 pos=lib.read8(s['sStartMenuCursorPos'])
 if pos==index:break
 press(128 if pos<index else 64)
press(1);step(400)
for _ in range(30):
 if lib.read32(s['sWorldDex']):break
 press(1)
assert lib.read32(s['sWorldDex']),'AREA did not open from native Pokédex'
step(120);picture('pokedex-world-area')
ptr=lib.read32(s['sWorldDex']);assert lib.read8(ptr+38)>0,'Habitat markers missing'
press(2);step(200);assert lib.read32(s['sWorldDex'])==0,'AREA did not clean up'
picture('pokedex-info-after-world-area')
# Reopening exercises sprite/tile cleanup and the native screen transition again.
for _ in range(10):
 if lib.read32(s['sWorldDex']):break
 press(1)
assert lib.read32(s['sWorldDex']);step(120);picture('pokedex-world-area-reopened')
press(2);step(180)
for _ in range(8):
 if lib.read32(s['gMain']+4)&~1==s['CB2_Overworld']:break
 press(2);step(120)
assert lib.read32(s['gMain']+4)&~1==s['CB2_Overworld']
assert hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest()==initial_rom_sha,'ROM changed during Dex validation'
lib.stop()
(args.output/'world-dex.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),canonical_species=len(counts),locations_per_national_number=counts,controller_open_area=True,world_map_with_habitat_markers=True,info_return_and_reopen=True,return_to_field=True,initial_party_flags_and_location_are_fixtures=True),indent=2)+'\n')
