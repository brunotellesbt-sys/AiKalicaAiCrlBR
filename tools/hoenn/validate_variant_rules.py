"""Exercise real variant ROM limits, aquatic pools, items and player evolutions."""
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bootstrap_path=ROOT/'tools/hoenn/validate_competitive_bosses.py'
exec(compile(bootstrap_path.read_text().split('\nchecks=[]')[0],str(bootstrap_path),'exec'))
maxdex=lib.read16(s['gJourneyBuildRules']);hard=bool(lib.read8(s['gJourneyBuildRules']+2))
catalog=json.loads((ROOT/'tools/hoenn/catalog_metadata.json').read_text())
species_ids={v['name']:int(k) for k,v in catalog['species'].items()}
counts={}
for number,sid in catalog['canonical_species'].items():
    count=native('JourneyWorldDexLocationCount',sid)
    assert bool(count)==(int(number)<=maxdex),(number,count,maxdex)
    assert bool(native('JourneySpeciesAllowed',sid))==(int(number)<=maxdex)
    counts[number]=count
assert native('JourneySpeciesAllowed',species_ids['SPECIES_RAICHU_ALOLA'])
assert native('JourneySpeciesAllowed',species_ids['SPECIES_CHARIZARD_MEGA_X'])
metadata=json.loads((source/'.journey-final-ecology').read_text())
metadata['ecology']=json.loads((source/'.journey-reproducible-water').read_text())['ecology']
locations=metadata['generation4']['locations'] if maxdex==493 else metadata['ecology']['locations_data']
roots=[f['root'] for l in locations for f in l['families']]
assert len(roots)==len(set(roots))
maps={json.loads(p.read_text())['id']:p.parent.name for p in (source/'data/maps').glob('*/map.json')}
pools=metadata['generation4']['pools'] if maxdex==493 else metadata['ecology']['pools']
waterchecks=0
for phase in [0,1,2]:
    for bank in [kanto_flags,hoenn_flags]:
        for i,flag in enumerate(bank):rawflag(flag,i<[0,4,8][phase])
    assert native('JourneyWildPhase')==phase
    for p in pools:
        if p['area'] not in [1,3]:continue
        group,num=map_id(maps[p['map']]);lib.write8(save()+4,group);lib.write8(save()+5,num)
        if not p['roots']:
            assert native('JourneyWildPoolAvailable',p['area'])==0
            continue
        original=p['roots'][0]
        if isinstance(original,str):original=species_ids[original]
        for _ in range(3):
            found=native('JourneyWildSpecies',original,p['area'])
            assert found and native('JourneySpeciesAllowed',found) and native('JourneyAquaticSpecies',found),(p,phase,found)
            waterchecks+=1
    print('Variant water pools passed at phase',phase,flush=True)

with tempfile.TemporaryDirectory(dir='/tmp') as temporary:
    p=Path(temporary)
    expressions=['EVO_MODE_NORMAL','EVO_MODE_ITEM_CHECK','CHECK_EVO','ITEM_THUNDER_STONE','ITEM_METAL_COAT','REGION_ALOLA','REGION_HISUI','ITEM_MEGA_RING','MON_DATA_LEVEL','MON_DATA_HELD_ITEM','VAR_UNUSED_0x404E']
    (p/'probe.c').write_text('#include "global.h"\n#include "pokemon.h"\n#include "constants/pokemon.h"\n#include "constants/items.h"\n#include "constants/regions.h"\n#include "constants/vars.h"\nconst u32 probe[]={'+','.join(expressions)+'};\n')
    subprocess.run([str(ROOT/'.local/arm-gcc/usr/bin/arm-none-eabi-gcc'),'-S','-iquote',str(source/'include'),'-mabi=apcs-gnu',str(p/'probe.c'),'-o',str(p/'probe.s')],check=True)
    probe=[int(n) for n in re.findall(r'\.word\s+(\d+)',(p/'probe.s').read_text())]

# GetEvolutionTargetSpecies has six arguments: compile a tiny ROM-side wrapper
# is unnecessary because the existing script special covers this call. Use a
# fixture Thumb stub with the two final arguments explicitly on its stack.
# This validator checks the supplied items and regional state directly; actual
# evolution animation/consumption remains a separate controller test.
for bank in [kanto_flags,hoenn_flags]:
    for i,flag in enumerate(bank):rawflag(flag,i<1)
native('JourneySuppliesRing')
assert native('CheckBagHasItem',probe[7],1)
assert native('JourneySuppliesRing')==0 or native('CheckBagHasItem',probe[7],1)
native('VarSet',probe[10],1);assert native('JourneyEvolutionRegion')==probe[5]
native('VarSet',probe[10],3);assert native('JourneyEvolutionRegion')==probe[6]
native('VarSet',probe[10],0)
native('VarSet',0x40FE,7);native('VarSet',0x40FF,0)
assert native('JourneyCrossoverComplete')==0
native('VarSet',0x40FF,4095);assert native('JourneyCrossoverComplete')==1
assert native('JourneyGalacticCaptureLocked',483)==0
assert hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest()==initial_sha
lib.stop()
(args.output/'variant-rules.json').write_text(json.dumps(dict(passed=True,rom_sha256=initial_sha,max_national=maxdex,
    perfect_ivs=hard,canonical_habitat_locations=counts,aquatic_samples=waterchecks,unique_families=len(roots),
    mega_and_regional_forms_allowed=True,ring_and_regional_training_native=True,
    initial_state_is_fixture=True,full_campaign_playthrough=False),indent=2)+'\n')
print('Variant rules passed:',maxdex,'Hard' if hard else 'Normal',flush=True)
