"""Exercise the compiled ARM gym-party generator and actual field/event behavior."""
import json
from pathlib import Path
import struct

def validate(e):
    lib=e['lib'];s=e['s'];ref=e['ref'];root=e['ROOT']
    step=e['step'];tap=e['tap'];warp=e['warp'];script=e['script'];drain=e['drain'];flag=e['flag'];setflag=e['setflag'];var=e['var'];setvar=e['setvar'];save=e['save'];record=e['record'];location=e['location'];map_id=e['map_id'];position=e['position'];screenshot=e['screenshot']
    report=json.loads((root/'mods/choose-starting-city/manifest.json').read_text())['open_world']
    # Assembled from native_call.s. Temporary ROM memory only: production special
    # points back to its real function after each invocation. Never exported.
    stub=bytes.fromhex('00b505480549064a064b00f003f80649086000bd1847c0461111111122222222333333334444444455555555')
    hook=s['gSpecials']+ref['specials']['JourneyFamilyInfo']*4
    def raw32(addr,value):
        for i,b in enumerate(struct.pack('<I',value)):lib.raw8(addr+i,b)
    def native(name,*args):
        code=bytearray(stub)
        values=[*(list(args)+[0]*3)[:3],s[name]|1,0x0203fffc]
        for sentinel,value in zip([0x11111111,0x22222222,0x33333333,0x44444444,0x55555555],values):
            struct.pack_into('<I',code,code.index(struct.pack('<I',sentinel)),value)
        for i,b in enumerate(code):lib.raw8(0x08800200+i,b)
        lib.write32(0x0203fffc,0xdeadc0de)
        original=lib.read32(hook);raw32(hook,0x08800201)
        script(e['special']('JourneyFamilyInfo')+b'\x6b\x02',20)
        for _ in range(200):
            if lib.read32(0x0203fffc)!=0xdeadc0de:break
            step(1)
        assert lib.read32(0x0203fffc)!=0xdeadc0de,('Native call did not finish',name,args)
        raw32(hook,original)
        return lib.read32(0x0203fffc)
    def badges(mask):
        for i in range(8):setflag(0x820+i,bool(mask&(1<<i)))
    for mask in range(256):
        badges(mask);assert native('OpenWorld_BadgeCount')==mask.bit_count()
    record('badge-count-all-256-combinations')
    for count,ace in enumerate(report['ace_levels']):
        badges(((1<<count)-1)<<(8-count))
        for trainer in report['trainers']:
            lib.write32(s['gBattleTypeFlags'],8)
            size=native('CreateNPCTrainerParty',s['gEnemyParty'],trainer['id'])
            assert size==len(trainer['levels']),(count,trainer['name'],size,trainer['levels'])
            actual=[lib.read8(s['gEnemyParty']+i*100+84) for i in range(size)]
            expected=[ace-(0 if trainer['leader'] else 2)-min(6,trainer['highest']-lv) for lv in trainer['levels']]
            assert actual==expected,(count,trainer['name'],actual,expected)
            assert all(lib.read16(s['gEnemyParty']+i*100+88)>0 for i in range(size))
            record('compiled-gym-party-levels',badges=count,trainer=trainer['name'],levels=actual)
    badges(0)
    # Outside the gym, Boss Giovanni's actual party levels must remain unchanged.
    lib.write32(s['gBattleTypeFlags'],8)
    native('CreateNPCTrainerParty',s['gEnemyParty'],349)
    assert [lib.read8(s['gEnemyParty']+i*100+84) for i in range(4)]==[37,35,37,41]
    record('rocket-boss-party-not-scaled')
    # Field art and opponent portraits must be opposite to the selected gender,
    # while the new fixed graphics ID still resolves to Blue for either gender.
    save2=lib.read32(s['gSaveBlock2Ptr'])
    for gender,gfx,pic,info in [(0,7,136,'gObjectEventGraphicsInfo_GreenNormal'),(1,0,135,'gObjectEventGraphicsInfo_RedNormal')]:
        save2=lib.read32(s['gSaveBlock2Ptr'])
        lib.write8(save2+8,gender)
        actual=native('GetObjectEventGraphicsInfo',72)
        assert actual==s[info],(gender,hex(actual),hex(s[info]),lib.read8(save2+8),hex(lib.read32(s['gSaveBlock2Ptr'])))
        assert native('GetObjectEventGraphicsInfo',153)==s['gObjectEventGraphicsInfo_Blue']
        assert native('OpenWorld_TrainerPic',326)==pic
        assert native('OpenWorld_TrainerPic',350)==124 # TRAINER_PIC_RIVAL_LATE / Blue
        setflag(0x2d,False)
        warp('PalletTown_ProfessorOaksLab',5,6)
        assert e['objects']().get(8)==72
        screenshot('rival-opposite-sex-'+str(gender))
        record('opposite-sex-rival-and-independent-blue',player_gender=gender,field_graphics=gfx,battle_pic=pic)
    lib.write8(lib.read32(s['gSaveBlock2Ptr'])+8,0)
    # First-badge reward, not a particular badge. Call the real post-victory
    # script of each leader so its original badge/TM flow runs too.
    def clear_keys():
        for i in range(120):lib.write8(save()+0x3b8+i,0)
    def keys():return [lib.read16(save()+0x3b8+i*4) for i in range(30)]
    leaders=[t for t in report['trainers'] if t['leader']]
    setflag(0x23d,False);clear_keys();badges(0)
    warp('LavenderTown_VolunteerPokemonHouse',5,5)
    lib.write16(s['gSpecialVar_LastTalked'],1)
    script(b'\x05'+struct.pack('<I',s['LavenderTown_VolunteerPokemonHouse_EventScript_MrFuji']),90);drain()
    assert not flag(0x23d) and 350 not in keys()
    record('fuji-cannot-give-flute-before-first-badge')
    for i,leader in enumerate(leaders):
        badges(0);setflag(0x23d,False);clear_keys();setflag(0xad,False)
        warp(leader['gym'],5,7)
        lib.write16(s['gSpecialVar_LastTalked'],1)
        script(b'\x05'+struct.pack('<I',s[leader['victory_script']]),90);drain()
        assert flag(0x820+i) and sum(flag(0x820+n) for n in range(8))==1
        assert flag(0x23d) and keys().count(350)==1
        if i==7:assert not flag(0xad)
        record('real-first-gym-victory-awards-flute',gym=leader['gym'])
    # Full key-item pocket does not grant the unlock flag. A retry grants one copy.
    badges(1);setflag(0x23d,False);clear_keys()
    encryption=lib.read32(lib.read32(s['gSaveBlock2Ptr'])+0xf20)&65535
    ids=[349]+list(range(351,380))
    for i,item in enumerate(ids):lib.write16(save()+0x3b8+i*4,item);lib.write16(save()+0x3ba+i*4,1^encryption)
    code=b'\x04'+struct.pack('<I',s['OpenWorld_FirstBadgeReward'])+b'\x6b\x02'
    script(code,90);drain();assert not flag(0x23d) and 350 not in keys()
    lib.write16(save()+0x3b8+29*4,0);lib.write16(save()+0x3ba+29*4,encryption)
    script(code,90);drain();assert flag(0x23d) and keys().count(350)==1
    before=[lib.read32(save()+0x3b8+i*4) for i in range(30)]
    script(code,30);assert before==[lib.read32(save()+0x3b8+i*4) for i in range(30)]
    record('flute-full-pocket-retry-and-no-duplicates')
    # Physical gym entrances are usable without Rocket, key or badge progress.
    badges(0);setvar(0x4071,0);setvar(0x408a,0)
    for city,gym,x,y in [('ViridianCity','ViridianCity_Gym',36,12),('SaffronCity','SaffronCity_Gym',46,14),('CinnabarIsland','CinnabarIsland_Gym',20,6)]:
        warp(city,x,y);step(48,64);step(900)
        assert location()==map_id(gym),(city,location(),position())
        record('gym-door-open-with-zero-badges',gym=gym)
    # Tea and bicycle NPC triggers cannot turn the player back.
    for gate,x,y,direction in [('Route5_SouthEntrance',3,4,128),('Route6_NorthEntrance',3,6,64),('Route7_EastEntrance',5,4,16),('Route8_WestEntrance',7,4,32),('Route16_NorthEntrance_1F',7,10,32),('Route18_EastEntrance_1F',5,6,32)]:
        warp(gate,x,y);step(32,direction);step(90)
        assert not lib.read8(s['sLockFieldControls'])
        assert position()!=(x,y),(gate,position())
        record('road-gate-no-tea-or-bicycle-block',gate=gate)
    # Exterior island entrances open before their original quest requirements.
    badges(0)
    for outside,inside,x,y in [('MtEmber_Exterior','MtEmber_RubyPath_1F',42,40),('SixIsland_RuinValley','SixIsland_DottedHole_1F',24,25)]:
        warp(outside,x,y);step(32,64);step(900)
        assert location()==map_id(inside),(outside,location(),position())
        record('island-exterior-door-open-without-quest',entrance=outside)
    # Final doorway is physically blocked for every missing badge, regardless of
    # which seven were collected, and actually opens with all eight.
    for missing in range(8):
        badges(255^(1<<missing));warp('IndigoPlateau_PokemonCenter_1F',4,4)
        step(48,64);step(120)
        assert location()==map_id('IndigoPlateau_PokemonCenter_1F') and position()[1]>=3
        record('league-requires-each-badge',missing_badge=missing+1)
    badges(255);warp('IndigoPlateau_PokemonCenter_1F',4,4);step(64,64);step(900)
    assert location()==map_id('PokemonLeague_LoreleisRoom'),(location(),position())
    screenshot('league-entry-eight-badges');record('physical-league-entry-with-eight-badges')
