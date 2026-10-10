"""Walk onto Five Island's grass and start a native encounter from its new header."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
exec(compile((ROOT/'tools/hoenn/validate_abilities.py').read_text().split('\nability_field,')[0],str(ROOT/'tools/hoenn/validate_abilities.py'),'exec'))
r=json.loads((source/'.journey-five-island-habitat').read_text());party=s['gParties']
for i in range(6*abi[2]):lib.write8(party+i,0)
lib.write8(s['gPartiesCount'],0);assert native('ScriptGiveMon',abi[59],6,0)==0
for f in list(range(0x1AB0,0x1AB8))+[lib.read16(s['gBadgeFlags']+2*i) for i in range(8)]:
 address=save()+4720+f//8;lib.write8(address,lib.read8(address)&~(1<<(f&7)))
warp('FiveIsland_Frlg',18,7);native('SetPlayerAvatarTransitionFlags',1);native('DisableWildEncounters',True);step(30)
for x in range(17,12,-1):
 for _ in range(100):
  if position()==(x,7):break
  step(1,32)
 else:raise AssertionError(('Cannot walk onto new grass',x,position()))
step(30);assert position()==(13,7)
assert native('MetatileBehavior_IsTallGrass',native('MapGridGetMetatileBehaviorAt',20,14))
assert native('GetCurrentMapWildMonHeaderId')!=65535
observed={native('JourneyWildSpecies',150,0) for _ in range(600)}
assert observed==set(r['family_roots']),(observed,r['family_roots'])
for sid in r['map_species']['MAP_FIVE_ISLAND']:assert native('JourneyHabitatHasSpecies',*map_id('FiveIsland_Frlg'),sid)
assert not native('JourneyHabitatHasSpecies',*map_id('FiveIsland_Frlg'),150)
picture('five-island-native-grass')
native('DisableWildEncounters',False);assert native('SweetScentWildEncounter');step(1000)
assert lib.read32(s['gMain']+4)&~1==s['BattleMainCB2']
actual=lib.read16(s['gBattleMons']+abi[74]+abi[75]);assert actual in observed
picture('five-island-native-encounter');lib.stop()
(args.output/'five-island-habitat.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),controller_walk_to_grass=True,observed_basic_species=sorted(observed),dex_membership_correct=True,no_legendaries=True,native_grass_battle_species=actual,initial_location_party_badges_and_encounter_suppression_are_fixtures=True,full_campaign_playthrough=False),indent=2)+'\n')
print('Five Island grass, all four families, Dex and native battle passed',flush=True)
