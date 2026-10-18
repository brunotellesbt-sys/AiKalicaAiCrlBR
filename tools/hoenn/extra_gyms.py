"""Additional badge circuit. Ace families are first; adaptive battle order puts them last."""
GYMS = [
 dict(key='MORTY',city='LavenderTown_Frlg',name='JourneyLavenderGym',leader='Morty',kind='GHOST',badge='FOG',tm='SHADOW_BALL',position=[24,9],kanto=True,gender='MALE',team=[['GASTLY','HAUNTER',25,'GENGAR',40],['MISDREAVUS','MISMAGIUS',30],['DUSKULL','DUSCLOPS',37,'DUSKNOIR',45],['DRIFLOON','DRIFBLIM',28],['SHUPPET','BANETTE',37],['SABLEYE']]),
 dict(key='WHITNEY',city='LilycoveCity',name='JourneyLilycoveGym',leader='Whitney',kind='FAIRY',badge='CHARM',tm='DAZZLING_GLEAM',position=[44,21],kanto=False,gender='FEMALE',team=[['CLEFAIRY','CLEFABLE',30],['JIGGLYPUFF','WIGGLYTUFF',30],['SNUBBULL','GRANBULL',23],['TOGEPI','TOGETIC',20,'TOGEKISS',40],['AZURILL','MARILL',18,'AZUMARILL',28],['MAWILE']]),
 dict(key='STEVEN',city='EverGrandeCity',name='JourneyEverGrandeGym',leader='Steven',kind='STEEL',badge='ALLOY',tm='FLASH_CANNON',position=[8,50],kanto=False,gender='MALE',team=[['BELDUM','METANG',20,'METAGROSS',45],['SKARMORY'],['ARON','LAIRON',32,'AGGRON',42],['MAGNEMITE','MAGNETON',30,'MAGNEZONE',42],['BRONZOR','BRONZONG',33],['SHIELDON','BASTIODON',30]]),
 dict(key='BUGSY',city='FallarborTown',name='JourneyFallarborGym',leader='Bugsy',kind='BUG',badge='HIVE',tm='X_SCISSOR',position=[11,18],kanto=False,gender='MALE',team=[['SCYTHER','SCIZOR',35],['HERACROSS'],['YANMA','YANMEGA',33],['CATERPIE','METAPOD',7,'BUTTERFREE',10],['SPINARAK','ARIADOS',22],['PINECO','FORRETRESS',31]]),
 dict(key='CANDICE',city='SlateportCity',name='JourneySlateportGym',leader='Candice',kind='ICE',badge='ICICLE',tm='ICE_BEAM',position=[10,17],kanto=False,gender='FEMALE',team=[['SNOVER','ABOMASNOW',40],['SNEASEL','WEAVILE',35],['SNORUNT','FROSLASS',35],['SWINUB','PILOSWINE',33,'MAMOSWINE',42],['LAPRAS'],['SPHEAL','SEALEO',32,'WALREIN',44]]),
 dict(key='CLAIR',city='SixIsland_Frlg',name='JourneySixIslandGym',leader='Clair',kind='DRAGON',badge='RISING',tm='DRAGON_PULSE',position=[2,13],kanto=True,gender='FEMALE',team=[['DRATINI','KINGDRA',48],['BAGON','SHELGON',30,'SALAMENCE',50],['GIBLE','GABITE',24,'GARCHOMP',48],['DRAGONAIR','DRAGONITE',55],['ALTARIA'],['FLYGON']]),
 dict(key='KAREN',city='ThreeIsland_Frlg',name='JourneyThreeIslandGym',leader='Karen',kind='DARK',badge='DUSK',tm='DARK_PULSE',position=[1,14],kanto=True,gender='FEMALE',team=[['UMBREON'],['HOUNDOUR','HOUNDOOM',24],['MURKROW','HONCHKROW',35],['SNEASEL','WEAVILE',35],['ABSOL'],['SPIRITOMB']]),
 dict(key='OAK',city='PalletTown_ProfessorOaksLab_Frlg',name='JourneyOakBasementGym',leader='Oak',kind='MIXED',badge='RESEARCH',tm='RETURN',position=None,kanto=True,gender='MALE',team=[['BULBASAUR','IVYSAUR',16,'VENUSAUR',32],['CHARMANDER','CHARMELEON',16,'CHARIZARD',36],['SQUIRTLE','WARTORTLE',16,'BLASTOISE',36],['TAUROS'],['EXEGGCUTE','EXEGGUTOR',32],['GROWLITHE','ARCANINE',36]])]
VALERIE = dict(key='VALERIE',leader='Valerie',gender='FEMALE',team=[['SYLVEON'],['MAWILE'],['MR_MIME'],['KLEFKI'],['SPRITZEE','AROMATISSE',30],['SWIRLIX','SLURPUFF',30]])

# Native class, battle portrait, field sprite and gender agree with each
# room's specialty. Students retain the room's type-specific party families.
STUDENT_PROFILES={
 'MORTY':[('CHANNELER_FRLG','CHANNELER_FRLG','CHANNELER','FEMALE'),('PSYCHIC','PSYCHIC_M','PSYCHIC_M','MALE')],
 'WHITNEY':[('LADY','LADY','WOMAN_4','FEMALE'),('BEAUTY','BEAUTY','BEAUTY','FEMALE')],
 'STEVEN':[('ENGINEER_FRLG','ENGINEER_FRLG','SCIENTIST_1','MALE'),('RUIN_MANIAC','RUIN_MANIAC','HIKER','MALE')],
 'BUGSY':[('BUG_CATCHER','BUG_CATCHER','BUG_CATCHER','MALE'),('BUG_MANIAC','BUG_MANIAC','MANIAC','MALE')],
 'CANDICE':[('EXPERT','EXPERT_M','EXPERT_M','MALE'),('EXPERT','EXPERT_F','EXPERT_F','FEMALE')],
 'CLAIR':[('DRAGON_TAMER','DRAGON_TAMER','EXPERT_M','MALE'),('COOLTRAINER','COOLTRAINER_F','COOLTRAINER_F','FEMALE')],
 'KAREN':[('GUITARIST','GUITARIST','BARD','MALE'),('POKEMANIAC','POKEMANIAC','MANIAC','MALE')],
 'OAK':[('SCIENTIST_FRLG','SCIENTIST_FRLG','SCIENTIST_1','MALE'),('SCIENTIST_FRLG','SCIENTIST_FRLG','SCIENTIST_2','MALE')],
}
MORE_STUDENTS={
 'MORTY':[('HEX_MANIAC','HEX_MANIAC','HEX_MANIAC','FEMALE'),('PSYCHIC','PSYCHIC_F','HEX_MANIAC','FEMALE')],
 'WHITNEY':[('AROMA_LADY','AROMA_LADY','WOMAN_2','FEMALE'),('LASS','LASS','LASS','FEMALE')],
 'STEVEN':[('SCIENTIST_FRLG','SCIENTIST_FRLG','SCIENTIST_2','MALE'),('COLLECTOR','COLLECTOR','MANIAC','MALE')],
 'BUGSY':[('CAMPER','CAMPER','CAMPER','MALE'),('PICNICKER','PICNICKER','PICNICKER','FEMALE')],
 'CANDICE':[('COOLTRAINER','COOLTRAINER_M','COOLTRAINER_M','MALE'),('COOLTRAINER','COOLTRAINER_F','COOLTRAINER_F','FEMALE')],
 'CLAIR':[('EXPERT','EXPERT_M','EXPERT_M','MALE'),('EXPERT','EXPERT_F','EXPERT_F','FEMALE')],
 'KAREN':[('GENTLEMAN','GENTLEMAN','GENTLEMAN','MALE'),('COOLTRAINER','COOLTRAINER_F','COOLTRAINER_F','FEMALE')],
 'OAK':[('SCHOOL_KID','SCHOOL_KID_M','BOY_2','MALE'),('SCHOOL_KID','SCHOOL_KID_F','GIRL_2','FEMALE')],
}
for key,profiles in MORE_STUDENTS.items():STUDENT_PROFILES[key]+=profiles
