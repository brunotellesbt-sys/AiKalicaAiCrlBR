"""Export actual native gym parties for every rank and party-size branch."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bootstrap_path=ROOT/'tools/hoenn/validate_competitive_bosses.py'
exec(compile(bootstrap_path.read_text().split('\nchecks=[]')[0],str(bootstrap_path),'exec'))
rules=lib.read16(s['gJourneyBuildRules']);hard=bool(lib.read8(s['gJourneyBuildRules']+2))
scaling=json.loads((source/'.journey-gym-scaling').read_text())
checks=[]
for gym in scaling['gyms']:
    group,num=map_id(gym['map']);lib.write8(save()+4,group);lib.write8(save()+5,num)
    lib.write8(s['isFrlg'],int(gym['kanto']))
    candidates=gym['trainers']+(['TRAINER_NORMAN_1'] if gym['map']=='PetalburgCity_Gym' else [])
    for name in candidates:
        if name=='TRAINER_LEADER_GIOVANNI':name='TRAINER_JOURNEY_BLUE'
        trainer=base+ids[name]*abi[0]
        if lib.read8(trainer+abi[4]) not in [abi[8],abi[9]]:continue
        for rank in range(8):
            for bank,count in [(kanto_flags,rank if gym['kanto'] else 0),(hoenn_flags,0 if gym['kanto'] else rank)]:
                for i,flag in enumerate(bank):rawflag(flag,i<count)
            for players in ([2,6] if rank<4 else [6]):
                team([6]*players);levels=generated(trainer);mons=[]
                expected=6 if rank>=4 else rank+2+(players>rank+2)
                assert len(levels)==expected,(name,rank,players,levels)
                for i,level in enumerate(levels):
                    mon=enemy+i*abi[2];species=data(mon,'MON_DATA_SPECIES')
                    ivs=data(mon,'MON_DATA_IVS');evs=[data(mon,f) for f in fields[1:7]]
                    moveset=[native('GetMonData3',mon,values['MON_DATA_MOVE1']+slot,0) for slot in range(4)]
                    assert native('JourneySpeciesAllowed',species)
                    assert native('JourneyTrainerSpecies',species,level)==species
                    assert sum(evs)==510 and max(evs)<=252
                    if hard:assert ivs&0x3FFFFFFF==0x3FFFFFFF
                    assert all(move in nonlevel[species]|{mid for at,mid in database['species'][species]['learnset'] if at<=level}
                               or native('JourneyBossMoveLegal',species,move,level) for move in moveset if move)
                    mons.append(dict(species=species,level=level,moves=moveset,nature=native('GetNature',mon),
                                     ability_slot=data(mon,'MON_DATA_ABILITY_NUM'),item=data(mon,'MON_DATA_HELD_ITEM'),evs=evs,ivs=ivs))
                checks.append(dict(leader=name,map=gym['map'],kanto=gym['kanto'],rank=rank+1,player_count=players,mons=mons))
        print('Exported',name,'Gen',4 if rules==493 else 9,'Hard' if hard else 'Normal',flush=True)
assert len({c['leader'] for c in checks})==16
if not hard:
    assert any(mon['ivs']&0x3FFFFFFF!=0x3FFFFFFF for c in checks for mon in c['mons']), 'Normal still forces perfect IVs'
assert hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest()==initial_sha
lib.stop()
(args.output/'gym-teams.json').write_text(json.dumps(dict(passed=True,rom_sha256=initial_sha,max_national=rules,
    difficulty='Hard' if hard else 'Normal',checks=checks,native_parties=True,initial_state_is_fixture=True),indent=2)+'\n')
