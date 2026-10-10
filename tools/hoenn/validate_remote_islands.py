"""Native continuous Surf, landing, grass habitats and final wild battle."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
prefix=(ROOT/'tools/hoenn/validate_eastern_union.py').read_text().split('exec(compile((ROOT/')[0]
exec(compile(prefix,str(ROOT/'tools/hoenn/validate_eastern_union.py'),'exec'))
exec(compile((ROOT/'tools/hoenn/native_water_walk.py').read_text(),str(ROOT/'tools/hoenn/native_water_walk.py'),'exec'))
prep=json.loads((source/'.journey-remote-islands').read_text())
native('DisableWildEncounters',True) # Navigation fixture; generation tested below.
def sea_target(name):
 w,h,v=blocks[name]
 i=min((i for i in passable[name] if water_behaviors[behaviors[name][i]] and v[i]>>12==1),key=lambda i:abs(i%w-w//2)+abs(i//w-h//2))
 return name,i%w,i//w
start=sea_target('JourneyWorldSea04');g,n=map_id(start[0])
script(b'\x39'+bytes([g,n,255])+struct.pack('<HH',*start[1:])+b'\x27\x6b\x02',frames=240);step(120)
native('SetPlayerAvatarTransitionFlags',8);step(30)
checks=[]
for site in prep['sites']:
 name=site['map'];walk(sea_target(name));assert lib.read8(s['gPlayerAvatar'])&8
 assert lib.read8(s['isFrlg'])==1,('Wrong regional map format',name)
 walk((name,*site['landing']));assert not lib.read8(s['gPlayerAvatar'])&8
 grass=site['grass'][len(site['grass'])//2];walk((name,*grass))
 assert native('MetatileBehavior_IsTallGrass',native('MapGridGetMetatileBehaviorAt',grass[0]+7,grass[1]+7))
 assert native('GetCurrentMapWildMonHeaderId')!=65535
 h=next(h for h in prep['locations_data'] if site['id'] in h['maps'])
 allowed_ids=set(prep['map_species'][site['id']]);observed={native('JourneyWildSpecies',150,0) for _ in range(400)}
 assert observed and observed<=allowed_ids,(name,observed-allowed_ids)
 for ident in allowed_ids:assert native('JourneyHabitatHasSpecies',*map_id(name),ident)
 assert not native('JourneyHabitatHasSpecies',*map_id(name),150)
 mean=native('JourneyWildMean');levels=[]
 for mon in sorted(observed):
  native('CreateWildMon',mon,80)
  level=native('GetMonData3',s['gParties']+6*abi[2],abi[6],0)
  assert max(1,mean-5)<=level<=min(100,mean+2);levels.append(level)
 before=(location(),position(),lib.read8(s['gPlayerAvatar'])&25)
 assert native('TrySavingData',0,max_frames=6000)==1;step(60)
 assert native('LoadGameSave',0,max_frames=6000)==1
 lib.write32(s['gMain']+4,s['CB2_ContinueSavedGame']|1);step(1500);finish()
 assert before==(location(),position(),lib.read8(s['gPlayerAvatar'])&25)
 assert lib.read8(s['isFrlg'])==1
 native('DisableWildEncounters',True)
 picture(name+'-grass-landing')
 checks.append(dict(map=name,name=site['name'],surf_landing=True,walkable_grass=True,
                    family_count=len(h['families']),observed_species=sorted(observed),levels=levels,mean=mean,native_dex_membership=True,native_save_continue=True))
 walk(sea_target(name));assert lib.read8(s['gPlayerAvatar'])&8
 print('Remote island landing/grass/native pool passed:',name,flush=True)
walk(start);assert location()==map_id(start[0]) and position()==start[1:]
roundtrip_transitions=list(transitions)
# Each relocated family must disappear from its previous habitat in the native Dex.
by_id_all={json.loads((source/'data/maps'/n/'map.json').read_text())['id']:n for group in groups['group_order'] for n in groups[group]}
before=json.loads((source/'.journey-tower-habitats').read_text())
for move in prep['moved_families']:
 donor=next(h for h in before['locations_data'] if h['section']==move['old_section'])
 family=next(f for f in donor['families'] if f['root']==move['root'])
 target=next(h for h in prep['locations_data'] if h['section']==move['section'])
 for member in family['species']:
  for ident in donor['maps']:assert not native('JourneyHabitatHasSpecies',*map_id(by_id_all[ident]),member['id'])
  for ident in target['maps']:assert native('JourneyHabitatHasSpecies',*map_id(by_id_all[ident]),member['id'])
# A real wild battle uses the new grass header and the unmodified encounter code.
site=prep['sites'][-1];walk((site['map'],*site['grass'][len(site['grass'])//2]))
native('DisableWildEncounters',False)
assert native('SweetScentWildEncounter')
step(1000)
# Field-script native calls cannot execute while BattleMainCB2 owns the loop.
# Read the decrypted opponent battle structure and its plain party level.
wild=lib.read16(s['gBattleMons']+abi[74]+abi[75])
level=lib.read8(s['gParties']+6*abi[2]+pabi[17])
assert wild in prep['map_species'][site['id']]
assert lib.read32(s['gMain']+4)&~1==s['BattleMainCB2']
picture('tidewood-native-wild-battle');lib.stop()
(args.output/'remote-islands.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
 continuous_surf_and_land_roundtrip=True,no_midtrip_fixture_warps=True,checks=checks,transitions=roundtrip_transitions,
 relocated_families_removed_from_old_dex_locations=True,wild_battle_species=wild,wild_battle_level=level,
 initial_location_party_defeated_flags_and_navigation_encounter_suppression_are_fixtures=True,
 final_battle_started_with_native_sweet_scent_function=True,full_campaign_playthrough=False),indent=2)+'\n')
print('Remote islands native Surf, landing, grass, Dex and wild battle passed',flush=True)
