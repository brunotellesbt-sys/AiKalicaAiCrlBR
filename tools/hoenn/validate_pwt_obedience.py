"""Native PWT obedience and the two regional badge cases; state is a fixture."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_pwt_world.py').read_text().split('for generation in range(cap+1):')[0]
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_pwt_world.py'),'exec'))
from battle_interaction_fixture import BattleFixture
constants={'BATTLE_TYPE_FRONTIER','BATTLE_TYPE_DOUBLE','BATTLE_TYPE_PWT','BATTLE_TYPE_TRAINER',
 'SPECIES_SNORLAX','TYPE_NORMAL','TYPE_MYSTERY','MOVE_TACKLE','OBEYS','MON_DATA_MET_LEVEL'}
f=BattleFixture(source,lib,s,native,party,constants)
native('ZeroPlayerPartyMons');native('ScriptGiveMon',143,100,0)
native('PokemonToBattleMon',party,s['gBattleMons'])
f.mon(0,'level',50,1)
checks=[]
kanto=list(range(0x1AB0,0x1AB8));hoenn=[lib.read16(s['gBadgeFlags']+i*2) for i in range(8)]
def badges(k,h):
    for bank,count in [(kanto,k),(hoenn,h)]:
        for i,flag in enumerate(bank):native('FlagSet' if i<count else 'FlagClear',flag)
badges(0,0)
lib.write32(s['gBattleTypeFlags'],f.c('BATTLE_TYPE_TRAINER')|f.c('BATTLE_TYPE_PWT'))
for seed in range(32):
    native('SeedRng',seed)
    assert native('GetAttackerObedienceForAction')==f.c('OBEYS')
checks.append(dict(case='pwt_level_50_met_100_no_badges',seeds=32,always_obeys=True))
lib.write32(s['gBattleTypeFlags'],f.c('BATTLE_TYPE_TRAINER'))
for k,h,met in [(8,0,100),(0,8,100),(3,0,40),(0,3,40),(5,1,60),(1,5,60)]:
    badges(k,h);scratch=s['gStringVar4']+800;lib.write8(scratch,met)
    native('SetMonData',party,f.c('MON_DATA_MET_LEVEL'),scratch)
    native('PokemonToBattleMon',party,s['gBattleMons'])
    assert native('GetAttackerObedienceForAction')==f.c('OBEYS'),(k,h,met)
    checks.append(dict(case='regional_badge_obedience',kanto=k,hoenn=h,met_level=met,obeys=True))
lib.stop()
r=dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),checks=checks,
    pwt_no_badge_obedience=True,both_regional_cases_count=True,prepared_native_state=True)
(args.output/'pwt-obedience.json').write_text(json.dumps(r,indent=2)+'\n')
print('PWT and regional obedience checks passed',flush=True)
