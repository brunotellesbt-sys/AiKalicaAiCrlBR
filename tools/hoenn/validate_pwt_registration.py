"""Reject invalid entries natively and check one-time rewards/restoration."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_pwt_world.py').read_text().split('for generation in range(cap+1):')[0]
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_pwt_world.py'),'exec'))
from battle_interaction_fixture import compile_probe
_,v,_=compile_probe(source,{'MON_DATA_IS_EGG','MON_DATA_HELD_ITEM','ITEM_LEFTOVERS','SPECIES_MEWTWO'})
scratch=s['gStringVar4']+800
checks=[]
def restore():
    for i,b in enumerate(original):lib.write8(party+i,b)
    lib.write8(s['gPartiesCount'],6)
    lib.write8(state+offsets[2],6);lib.write8(state+offsets[3],0)
    for i in range(6):lib.write8(s['gSelectedOrderFromParty']+i,i+1)
def rejected(label):
    snapshot=bytes(lib.read8(party+i) for i in range(6*abi[2]))
    native('JourneyPWTBegin');assert not lib.read16(s['gSpecialVar_Result'])
    assert not lib.read8(state+offsets[4])
    assert bytes(lib.read8(party+i) for i in range(6*abi[2]))==snapshot
    checks.append(dict(case=label,rejected=True,party_unchanged=True))
restore();lib.write8(state+offsets[2],5);rejected('five_selected')
restore();lib.write8(s['gSelectedOrderFromParty']+1,1);rejected('same_slot_twice')
restore();lib.write8(s['gSelectedOrderFromParty']+1,0);rejected('missing_slot')
restore();lib.write8(s['gPartiesCount'],5);rejected('only_five_owned')
restore();lib.write8(state+offsets[3],cap+1);rejected('unavailable_generation')
restore();lib.write8(scratch,1);native('SetMonData',party,v['MON_DATA_IS_EGG'],scratch);rejected('egg')
restore();lib.write16(scratch,v['ITEM_LEFTOVERS'])
for slot in range(2):native('SetMonData',party+slot*abi[2],v['MON_DATA_HELD_ITEM'],scratch)
rejected('duplicate_held_item')
restore()
for i in range(abi[2]):lib.write8(party+abi[2]+i,lib.read8(party+i))
rejected('same_species_twice')
restore();native('ZeroPlayerPartyMons')
for species in [v['SPECIES_MEWTWO'],149,376,121,445,6]:native('ScriptGiveMon',species,100,0)
rejected('frontier_banned_species')
restore();begin(0)
before=bytes(lib.read8(party+i) for i in range(6*abi[2]))
native('JourneyPWTBegin');assert not lib.read16(s['gSpecialVar_Result'])
assert bytes(lib.read8(party+i) for i in range(6*abi[2]))==before
checks.append(dict(case='already_active',rejected=True,party_unchanged=True));finish()
# Reward paths use an explicit final-stage fixture. The separate cup runs
# execute real group/knockout transitions and combat outcomes.
for pool,reward in [(0,25),(1,10)]:
    begin(pool);lib.write8(cup+offsets[12],2)
    native('JourneyPWTFinish');assert lib.read16(bp_at)==bp_before+reward
    assert bytes(lib.read8(party+i) for i in range(6*abi[2]))==original
    native('JourneyPWTFinish');assert lib.read16(bp_at)==bp_before+reward
    checks.append(dict(case='global_reward' if not pool else 'generation_reward',bp=reward,once_only=True,party_restored_byte_exact=True))
    lib.write16(bp_at,bp_before)
lib.stop()
r=dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
    version_generation_cap=cap,checks=checks,reward_stage_is_explicit_fixture=True,
    invalid_registration_native=True,full_campaign_playthrough=False)
(args.output/'pwt-registration.json').write_text(json.dumps(r,indent=2)+'\n')
print('Native PWT registration and reward checks passed:',len(checks),flush=True)
