"""Ordinary species with a dedicated acquisition mechanic, not grass slots."""
FOSSILS = [
 ('OMANYTE','HELIX_FOSSIL',None),('KABUTO','DOME_FOSSIL',None),('AERODACTYL','OLD_AMBER',None),
 ('LILEEP','ROOT_FOSSIL',None),('ANORITH','CLAW_FOSSIL',None),
 ('CRANIDOS','SKULL_FOSSIL',None),('SHIELDON','ARMOR_FOSSIL',None),
 ('TIRTOUGA','COVER_FOSSIL',None),('ARCHEN','PLUME_FOSSIL',None),
 ('TYRUNT','JAW_FOSSIL',None),('AMAURA','SAIL_FOSSIL',None),
 ('DRACOZOLT','FOSSILIZED_BIRD','FOSSILIZED_DRAKE'),
 ('ARCTOZOLT','FOSSILIZED_BIRD','FOSSILIZED_DINO'),
 ('DRACOVISH','FOSSILIZED_FISH','FOSSILIZED_DRAKE'),
 ('ARCTOVISH','FOSSILIZED_FISH','FOSSILIZED_DINO'),
]
EVENTS = [
 ('ROTOM','JourneyLavenderWorkshop','TV with static; base form only'),
 ('SPIRITOMB','FiveIsland_MemorialPillar_Frlg','Install Odd Keystone in the old well'),
 ('UNOWN','SevenIsland_TanobyRuins_MoneanChamber_Frlg','Inspect the ancient glyph; repeat for different letters'),
 ('GIMMIGHOUL_CHEST','FiveIsland_LostCave_Room10_Frlg','Inspect the coin chest'),
 ('CASTFORM_NORMAL','Route119_WeatherInstitute_2F','Original scientist gift after Shelly'),
 ('PORYGON','CeladonCity_GameCorner_PrizeRoom_Frlg','Original Coin Case / casino prize'),
]
FORM_TOOLS = ['ROTOM_CATALOG','GRACIDEA','REVEAL_GLASS','DNA_SPLICERS','ZYGARDE_CUBE',
 'PRISON_BOTTLE','N_SOLARIZER','N_LUNARIZER','REINS_OF_UNITY',
 'RED_NECTAR','YELLOW_NECTAR','PINK_NECTAR','PURPLE_NECTAR']
FORM_TOOLS += [t+'_MEMORY' for t in 'FIRE WATER ELECTRIC GRASS ICE FIGHTING POISON GROUND FLYING PSYCHIC BUG ROCK GHOST DRAGON DARK STEEL FAIRY'.split()]
FORM_TOOLS += [t+'_PLATE' for t in 'FLAME SPLASH ZAP MEADOW ICICLE FIST TOXIC EARTH SKY MIND INSECT STONE SPOOKY DRACO DREAD IRON PIXIE'.split()]
FORM_TOOLS += [t+'_DRIVE' for t in ['DOUSE','SHOCK','BURN','CHILL']]
FORM_TOOLS += [t+'_MASK' for t in ['CORNERSTONE','WELLSPRING','HEARTHFLAME']]
