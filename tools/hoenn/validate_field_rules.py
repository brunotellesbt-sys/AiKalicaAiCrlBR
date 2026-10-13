"""Validate the four HM moves, terrestrial TM types and fully lit tunnels."""
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
prefix=(ROOT/'tools/hoenn/validate_world_map.py').read_text().split('\nchecks=[]')[0]
exec(compile(prefix,str(ROOT/'tools/hoenn/validate_world_map.py'),'exec'))
sha=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest()
checks=[]
for name,move,hm in [('Cut',15,False),('Fly',19,True),('Surf',57,True),('Strength',70,False),
                     ('Waterfall',127,True),('Flash',148,False),('Rock Smash',249,False),('Whirlpool',250,False),('Dive',291,True)]:
    assert bool(native('IsMoveHM',move))==hm,(name,hm)
    checks.append(dict(move=name,hm=hm))
with tempfile.TemporaryDirectory(dir='/tmp') as directory:
    probe=Path(directory)/'types.s'
    subprocess.run([str(ROOT/'.local/arm-gcc/usr/bin/arm-none-eabi-gcc'),'-S','-mabi=apcs-gnu','-iquote',str(source/'include'),'-x','c','-','-o',str(probe)],input='#include "global.h"\n#include "constants/pokemon.h"\nconst u32 types[]={TYPE_GRASS,TYPE_ROCK};',text=True,check=True)
    grass,rock=[int(n) for n in re.findall(r'\.word\s+(\d+)',probe.read_text())]
assert native('GetMoveType',15)==grass
assert native('GetMoveType',70)==rock
dark=[p.parent.name for p in (source/'data/maps').glob('*/map.json') if json.loads(p.read_text()).get('requires_flash')]
assert not dark,dark
for name in ['GraniteCave_1F','RockTunnel_1F_Frlg','SeafoamIslands_B4F_Frlg']:
    warp(name,5,5)
    assert native('GetFlashLevel')==0,name
assert hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest()==sha
lib.stop()
(args.output/'field-rules.json').write_text(json.dumps(dict(passed=True,rom_sha256=sha,checks=checks,
    cut_grass=True,strength_rock=True,no_maps_require_flash=True,native_flash_levels_zero=True,
    tunnel_travel_is_fixture=True),indent=2)+'\n')
