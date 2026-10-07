"""Check actual compiled encounters, level boundaries, habitats and roamer persistence."""
import json
import re

def validate(e):
    lib=e['lib'];s=e['s'];native=e['native'];badges=e['badges'];record=e['record']
    report=json.loads((e['ROOT']/'mods/choose-starting-city/manifest.json').read_text())['wild_world']
    ids=report['species_ids'];party=s['gPlayerParty'];enemy=s['gEnemyParty']
    snapshot=bytes(lib.read8(party+i) for i in range(600))
    count=lib.read8(s['gPlayerPartyCount'])
    # Use real encrypted starter data; zero other slots. Level fixtures change
    # the cached level read by GetMonData, without fabricating encrypted species.
    assert native('GetMonData2',party,11)!=0
    first=snapshot[:100]
    for i in range(600):lib.write8(party+i,0)
    for i,b in enumerate(first):lib.write8(party+i,b)
    lib.write8(s['gPlayerPartyCount'],1)
    for mean in [1,5,6,25,98,99,100]:
        lib.write8(party+84,mean)
        assert native('WildWorld_Mean')==mean
        levels={native('WildWorld_Level') for _ in range(80)}
        assert levels==set(range(max(1,mean-5),min(100,mean+2)+1)),(mean,levels)
        record('wild-level-entire-inclusive-range',mean=mean,levels=sorted(levels))
    for i,b in enumerate(first):lib.write8(party+100+i,b)
    lib.write8(party+84,12);lib.write8(party+184,21);lib.write16(party+86,0)
    assert native('WildWorld_Mean')==16 # floor, includes fainted
    lib.write32(0x0203fff0,1);native('SetMonData',party+100,45,0x0203fff0)
    assert native('WildWorld_Mean')==12 # Egg ignored
    record('party-mean-excludes-eggs-empty-includes-fainted-rounds-down')
    for i in range(600):lib.write8(party+i,0)
    assert native('WildWorld_Mean')==5
    record('empty-party-safe-fallback')
    for i,b in enumerate(snapshot):lib.write8(party+i,b)
    lib.write8(s['gPlayerPartyCount'],count)
    lib.write8(party+84,30)
    # Representative grass, ghost, cave, electric, Safari, island, water and
    # fishing profiles: exercise the real header and encounter creator.
    for name,area in [('Route1',0),('PokemonTower_5F',0),('DiglettsCave_B1F',0),('PowerPlant',0),('SafariZone_Center',0),('SixIsland_WaterPath',0),('Route21_North',1),('Route21_North',3)]:
        e['warp'](name,8,8)
        group,num=e['map_id'](name)
        # Header is 20 bytes, info consists of rate then a ROM slot pointer.
        header=s['gWildMonHeaders']
        while (lib.read8(header),lib.read8(header+1))!=(group,num):
            assert lib.read8(header)!=255,(name,'missing header')
            header+=20
        info=lib.read32(header+4+area*4)
        assert info,(name,area)
        table=lib.read32(info+4);original=lib.read16(table+2)
        # Find profile through its group/map macro's name from reference groups.
        candidates=[p for p in report['pools'] if p['area']==area]
        def canonical(v):return re.sub('[^A-Z0-9]','',v.upper().removeprefix('MAP_'))
        pool=next(p for p in candidates if canonical(p['map'])==canonical(name))
        for phase,mask,stages in [(0,0,[0]),(1,7,[0,1]),(2,63,[1,2])]:
            badges(mask)
            allowed={ids[report['families'][family][stage]] for family in pool['families'] for stage in stages}
            for _ in range(48):
                if area==3:
                    returned=native('GenerateFishingEncounter',info,2)
                else:
                    assert native('TryGenerateWildMon',info,area,0)==1
                    returned=native('GetMonData2',enemy,11)
                actual=native('GetMonData2',enemy,11)
                assert returned==actual and actual in allowed,(name,phase,actual,allowed)
                assert 25<=lib.read8(enemy+84)<=32
                assert lib.read16(enemy+88)>0
            record('actual-wild-habitat-and-evolution-phase',map=name,area=area,phase=phase)
        # Fix RNG and compare city affinities against the identical stream.
        draws=[]
        for city in range(1,17):
            e['setvar'](0x40cb,city)
            lib.write32(s['gRngValue'],123456)
            draws.append(tuple(native('WildWorld_Species',original,area) for _ in range(32)))
        if len(pool['families'])>1:assert len(set(draws))>1,(name,'city affinity did not change encounters')
        record('home-city-changes-native-family-weights',map=name)
    # Repel operates on exactly the level of the mon it creates.
    e['warp']('Route1',8,8);badges(0)
    lib.write8(party+84,30);e['setvar'](0x4020,100) # VAR_REPEL_STEP_COUNT
    header=s['gWildMonHeaders']
    while (lib.read8(header),lib.read8(header+1))!=e['map_id']('Route1'):header+=20
    info=lib.read32(header+4)
    accepted=blocked=0
    for _ in range(160):
        if native('TryGenerateWildMon',info,0,1):
            accepted+=1
            assert 30<=lib.read8(enemy+84)<=32
        else:
            blocked+=1
    assert accepted and blocked
    e['setvar'](0x4020,0)
    record('repel-filters-the-generated-level',accepted=accepted,blocked=blocked)
    # Static encounters retain species and held item; only the level changes.
    for species in ['SPECIES_SNORLAX','SPECIES_ARTICUNO','SPECIES_MEWTWO']:
        for _ in range(12):
            native('CreateScriptedWildMon',ids[species],70,13)
            assert native('GetMonData2',enemy,11)==ids[species]
            assert native('GetMonData2',enemy,12)==13
            assert 25<=lib.read8(enemy+84)<=32
        record('scripted-wild-level-with-original-species-and-item',species=species)
    native('CreateInitialRoamerMon')
    roamer=e['save']()+0x30d0
    identity=(lib.read32(roamer),lib.read32(roamer+4),lib.read16(roamer+8))
    native('CreateRoamerMonInstance');oldmax=lib.read16(enemy+88)
    lib.write16(roamer+10,oldmax//2);lib.write8(roamer+13,8)
    lib.write8(party+84,70)
    native('CreateRoamerMonInstance')
    newmax=lib.read16(enemy+88);hp=lib.read16(enemy+86)
    assert (lib.read32(roamer),lib.read32(roamer+4),lib.read16(roamer+8))==identity
    assert abs(hp/newmax-(oldmax//2)/oldmax)<0.02
    assert native('GetMonData2',enemy,55)&255==8
    assert 65<=lib.read8(enemy+84)<=72 and lib.read8(roamer+12)==lib.read8(enemy+84)
    record('roamer-scales-with-team-preserving-identity-damage-and-status')
    for i,b in enumerate(snapshot):lib.write8(party+i,b)
    lib.write8(s['gPlayerPartyCount'],count)
