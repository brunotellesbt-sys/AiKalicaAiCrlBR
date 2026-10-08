"""Exercise adaptive encounter code in the compiled ARM ROM with mGBA."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--source',type=Path,required=True);p.add_argument('--library',type=Path,required=True)
p.add_argument('--output',type=Path,default=ROOT/'mods/hoenn/integration-validation')
options=p.parse_args()
sys.argv=[sys.argv[0],'--source',str(options.source),'--library',str(options.library),'--output',str(options.output),'--water-hms','--westsea']
common=(ROOT/'tools/hoenn/validate_crossing.py').read_text().split('\nstep(900)\n')[0]
exec(compile(common,str(ROOT/'tools/hoenn/validate_crossing.py'),'exec'))
def press(key=1):step(1,key);step(35)
def task(name):return any(lib.read8(s['gTasks']+i*40+4) and lib.read32(s['gTasks']+i*40)&~1==s[name] for i in range(16))
step(900);save2=lib.read32(s['gSaveBlock2Ptr']);lib.write8(save2,255);lib.write8(save2+8,255);lib.write8(save2+abi[45],abi[46])
lib.write32(s['gMain'],0);lib.write8(s['gMain']+0x438,0);lib.write32(s['gMain']+4,s['CB2_NewGame']|1);step(300)
for _ in range(100):
 if task('Task_HandleMultichoiceGridInput'):break
 press()
assert task('Task_HandleMultichoiceGridInput');press();step(1500);warp('Route1_Frlg',5,12)
assert native('JourneyWildMean')==5
checks=[]
def team(levels):
 for i in range(6*abi[2]):lib.write8(s['gParties']+i,0)
 lib.write8(s['gPartiesCount'],0)
 for level in levels:assert native('ScriptGiveMon',1,level,0)==0
for levels in [[1],[5],[7,21,44],[99],[100]]:
 team(levels);mean=sum(levels)//len(levels);assert native('JourneyWildMean')==mean
 low,high=max(1,mean-5),min(100,mean+2)
 seen={native('JourneyWildLevel') for _ in range(100)}
 assert seen==set(range(low,high+1)),(levels,seen)
 for _ in range(15):
  native('CreateWildMon',16,80)
  assert low<=native('GetMonData3',s['gParties']+6*abi[2],abi[6],0)<=high
  native('CreateScriptedWildMon',143,80,0)
  assert native('GetMonData3',s['gParties']+6*abi[2],abi[7],0)==143
  assert low<=native('GetMonData3',s['gParties']+6*abi[2],abi[6],0)<=high
 checks.append(dict(party_levels=levels,mean=mean,observed_levels=sorted(seen),normal_and_fixed_levels=True))
 print('Native mean and bounds passed:',levels,flush=True)
# Eggs are excluded; fainted members still contribute.
team([10,30,100]);scratch=s['gStringVar4']+800;lib.write32(scratch,1)
native('SetMonData',s['gParties']+2*abi[2],abi[62],scratch)
lib.write16(scratch,0);native('SetMonData',s['gParties'],abi[47],scratch)
assert native('JourneyWildMean')==20
for kanto,hoenn in [(0,0),(5,0),(6,0),(8,3),(8,4),(8,8)]:
 for region,start in [(kanto,0x1AB0),(hoenn,abi[63])]:
  for i in range(8):
   flag=start+i; address=save()+4720+flag//8; mask=1<<(flag&7)
   value=lib.read8(address); lib.write8(address, value|mask if i<region else value&~mask)
 phase=0 if (kanto+hoenn)//2<3 else 1 if (kanto+hoenn)//2<6 else 2
 assert native('JourneyWildPhase')==phase,(kanto,hoenn)
 # Isolate the family transformation from habitat mixing.
 warp('PalletTown_PlayersHouse_2F_Frlg',6,6)
 allowed=[{1},{1,2},{2,3}][phase]
 observed={native('JourneyWildSpecies',3,0) for _ in range(80)}
 assert observed==allowed,(phase,observed)
 assert native('JourneyWildSpecies',201,0)==201
 print('Parallel regional evolution phase passed:',kanto,hoenn,flush=True)
# Complete catalog habitat membership, including highest-generation species.
prep=json.loads((source/'.journey-habitats').read_text())
metadata=json.loads((ROOT/'tools/hoenn/catalog_metadata.json').read_text())
observed_checks=[]
for h in prep['locations_data']:
 name=h['maps'][0]
 names=json.loads((source/'data/maps/map_groups.json').read_text())
 source_name=next(n for g in names['group_order'] for n in names[g] if json.loads((source/f'data/maps/{n}/map.json').read_text())['id']==name)
 warp(source_name,1,1)
 allowed={s['id'] for f in h['families'] for s in f['species']}
 roots={f['root'] for f in h['families']}
 got={native('JourneyWildSpecies',150,0) for _ in range(120)}
 assert got<=allowed,(name,got-allowed)
 group,num=map_id(source_name)
 for member in allowed:assert native('JourneyHabitatHasSpecies',group,num,member)
 assert not native('JourneyHabitatHasSpecies',group,num,150)
 observed_checks.append(dict(map=name,observed=sorted(got),allowed_count=len(allowed)))
 print('Habitat verified:',name,flush=True)
# Initial regional Pokedex immediately enables the complete National Dex.
flag=abi[50]
native('FlagSet',flag)
assert native('IsNationalPokedexEnabled')
lib.stop()
(args.output/'wild.json').write_text(json.dumps(dict(passed=True,
 rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),level_cases=checks,
 eggs_excluded=True,fainted_included=True,regional_progress='floor mean',phase_cases=6,
 native_fixed_species_preserved=True,unown_preserved=True,national_dex_from_initial_pokedex=True,
 catalog_habitats=observed_checks,habitat_preserved=True,full_campaign_validated=False),indent=2)+'\n')
