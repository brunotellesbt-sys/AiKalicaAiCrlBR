# Pokémon por habitat e encontros especiais

Referência da candidata nativa com Kanto, Hoenn e Sevii. Não é uma declaração de que todas as histórias e mecânicas da integração estão concluídas.

Os encontros aleatórios das 920 espécies-base comuns e variantes regionais ficam em 444 famílias, sem repetir famílias entre habitats. Andares da mesma caverna, zonas de Safari e a superfície/subsolo da mesma rota marinha contam como um habitat.

A distribuição corrigida tem 97 habitats terrestres: 18 com cinco famílias e 79 com quatro; outros 38 habitats exclusivamente aquáticos têm uma família cada. As 77 famílias com Pokémon do tipo Água estão reservadas para locais com Surf ou pesca, e também podem aparecer na grama do mesmo habitat quando ela existe.

Existem mais lagos e pontos de pesca que famílias aquáticas. Para preservar a regra de não repetir famílias, 20 mapas ficam sem encontros aquáticos; os encontros terrestres desses habitats permanecem. Esses pontos estão listados ao final. Nenhuma rota foi fechada por isso.

Nível: média inteira da equipe menos cinco até mais dois, limitada a 1–100. Ovos não contam; Pokémon desmaiados contam. Etapa evolutiva: média inteira das insígnias das duas regiões; 0–2 básicos, 3–5 básicos ou estágio 2, 6–8 estágios 2 ou 3. Famílias sem a etapa seguinte preservam a última disponível.

Na água, o filtro seleciona as evoluções aquáticas disponíveis da família: por exemplo, Vaporeon pode aparecer na água, enquanto as outras evoluções de Eevee continuam na grama do mesmo habitat. Famílias com etapas de tipos diferentes ficam em habitats terrestres com água, para que nenhuma espécie-base perca seu local.

A Pokédex Nacional vem junto à primeira Pokédex e marca o habitat da família inteira. Os slots e as chances de cada modalidade constam no arquivo `integration-validation/ecology-preparation.json`; as chances de pesca dependem da vara.

## Encontro fixo de história verificado

Hypno aparece uma vez no resgate de Lostelle, em Berry Forest, Sevii 3,
por interação com a personagem. Seu nível segue a média da equipe −5/+2,
e o evento fica acessível antes das Ligas. A família Drowzee/Hypno também
está nos encontros aleatórios de Mt. Pyre na distribuição atual.
Este encontro de roteiro não consta nos slots aleatórios da planilha;
o percurso e o resgate estão em [LOSTELLE-STORY.md](LOSTELLE-STORY.md).

## Encontros comuns por habitat

Use a busca pelo nome do Pokémon nesta página ou filtre a planilha `pokemon-locations.csv`. A coluna Região identifica Kanto, Hoenn e Sevii; os nomes internos dos mapas permitem localizar os arquivos exatos do jogo.

| Região | Habitat | Famílias e espécies | Mapas |
|---|---|---|---|
| Hoenn | Abandoned Ship | Mantine / Mantyke | MAP_ABANDONED_SHIP_HIDDEN_FLOOR_CORRIDORS, MAP_ABANDONED_SHIP_ROOMS_B1F |
| Hoenn | Altering Cave | Scyther / Scizor / Kleavor; Dratini / Dragonair / Dragonite; Skarmory; Larvitar / Pupitar / Tyranitar; Torchic / Combusken / Blaziken | MAP_ALTERING_CAVE |
| Sevii | Altering Cave Frlg | Cyndaquil / Quilava / Typhlosion / Typhlosion Hisui; Sableye; Mawile; Lileep / Cradily; Castform Normal | MAP_SIX_ISLAND_ALTERING_CAVE |
| Hoenn | Artisan Cave | Onix / Steelix; Treecko / Grovyle / Sceptile; Lunatone; Anorith / Armaldo; Absol | MAP_ARTISAN_CAVE_1F, MAP_ARTISAN_CAVE_B1F |
| Sevii | Berry Forest | Bellsprout / Weepinbell / Victreebel; Tentacool / Tentacruel; Seedot / Nuzleaf / Shiftry; Seviper; Skorupi / Drapion | MAP_THREE_ISLAND_BERRY_FOREST |
| Sevii | Birth Island Frlg | Pidgey / Pidgeotto / Pidgeot; Mareep / Flaaffy / Ampharos; Ralts / Kirlia / Gardevoir / Gallade; Buizel / Floatzel; Riolu / Lucario | MAP_JOURNEYWORLDSEA08 |
| Sevii | Bond Bridge | Furfrou Natural; Phantump / Trevenant; Crabrawler / Crabominable; Arctozolt; Cetoddle / Cetitan | MAP_THREE_ISLAND_BOND_BRIDGE |
| Sevii | Canyon Entrance | Tangela / Tangrowth; Pinsir; Ditto; Aipom / Ambipom; Stantler / Wyrdeer | MAP_SEVEN_ISLAND_SEVAULT_CANYON_ENTRANCE |
| Sevii | Cape Brink | Doduo / Dodrio; Togepi / Togetic / Togekiss; Snorlax / Munchlax; Togedemaru; Toedscool / Toedscruel | MAP_TWO_ISLAND_CAPE_BRINK |
| Hoenn | Cave Of Origin | Misdreavus / Mismagius; Qwilfish / Overqwil / Qwilfish Hisui; Bagon / Shelgon / Salamence; Beldum / Metang / Metagross; Turtwig / Grotle / Torterra | MAP_CAVE_OF_ORIGIN_1F, MAP_CAVE_OF_ORIGIN_ENTRANCE, MAP_CAVE_OF_ORIGIN_UNUSED_RUBY_SAPPHIRE_MAP1, MAP_CAVE_OF_ORIGIN_UNUSED_RUBY_SAPPHIRE_MAP2, MAP_CAVE_OF_ORIGIN_UNUSED_RUBY_SAPPHIRE_MAP3 |
| Kanto | Celadon City | Wimpod / Golisopod | MAP_CELADON_CITY |
| Kanto | Cerulean Cave | Corsola / Cursola / Corsola Galar; Chimchar / Monferno / Infernape; Cranidos / Rampardos; Shieldon / Bastiodon; Chatot | MAP_CERULEAN_CAVE_1F, MAP_CERULEAN_CAVE_2F, MAP_CERULEAN_CAVE_B1F |
| Kanto | Cerulean City | Totodile / Croconaw / Feraligatr | MAP_CERULEAN_CITY |
| Kanto | Cinnabar Island | Mudkip / Marshtomp / Swampert | MAP_CINNABAR_ISLAND |
| Hoenn | Desert Underpass | Slugma / Magcargo; Purrloin / Liepard; Durant; Nacli / Naclstack / Garganacl; Iron Treads | MAP_DESERT_UNDERPASS |
| Hoenn | Dewford Town | Oshawott / Dewott / Samurott / Samurott Hisui | MAP_DEWFORD_TOWN |
| Kanto | Digletts Cave | Cubone / Marowak / Marowak Alola; Roggenrola / Boldore / Gigalith; Pawniard / Bisharp / Kingambit; Tinkatink / Tinkatuff / Tinkaton; Orthworm | MAP_DIGLETTS_CAVE_B1F |
| Hoenn | Ever Grande City | Popplio / Brionne / Primarina | MAP_EVER_GRANDE_CITY |
| Hoenn | Fiery Path | Tepig / Pignite / Emboar; Bouffalant; Larvesta / Volcarona; Chespin / Quilladin / Chesnaught; Amaura / Aurorus | MAP_FIERY_PATH |
| Sevii | Five Island | Magnemite / Magneton / Magnezone; Blitzle / Zebstrika; Heatmor; Morelull / Shiinotic; Sizzlipede / Centiskorch | MAP_FIVE_ISLAND, MAP_JOURNEYWORLDSEA05 |
| Sevii | Five Isle Meadow | Paras / Parasect; Ponyta / Rapidash / Ponyta Galar / Rapidash Galar; Unown; Nincada / Ninjask / Shedinja; Impidimp / Morgrem / Grimmsnarl | MAP_FIVE_ISLAND_MEADOW |
| Sevii | Four Island | Marill / Azumarill / Azurill; Minccino / Cinccino; Elgyem / Beheeyem; Vullaby / Mandibuzz; Skiddo / Gogoat | MAP_FOUR_ISLAND, MAP_JOURNEYWORLDSEA04 |
| Kanto | Fuchsia City | Kabuto / Kabutops | MAP_FUCHSIA_CITY |
| Hoenn | Granite Cave | Drilbur / Excadrill; Gothita / Gothorita / Gothitelle; Axew / Fraxure / Haxorus; Golett / Golurk; Inkay / Malamar | MAP_GRANITE_CAVE_1F, MAP_GRANITE_CAVE_B1F, MAP_GRANITE_CAVE_B2F, MAP_GRANITE_CAVE_STEVENS_ROOM |
| Sevii | Green Path | Walking Wake | MAP_SIX_ISLAND_GREEN_PATH |
| Sevii | Icefall Cave | Seel / Dewgong; Cryogonal; Druddigon; Deino / Zweilous / Hydreigon; Tyrunt / Tyrantrum | MAP_FOUR_ISLAND_ICEFALL_CAVE_1F, MAP_FOUR_ISLAND_ICEFALL_CAVE_B1F, MAP_FOUR_ISLAND_ICEFALL_CAVE_BACK, MAP_FOUR_ISLAND_ICEFALL_CAVE_ENTRANCE |
| Hoenn | Jagged Pass | Rotom; Snivy / Servine / Serperior; Throh; Archen / Archeops | MAP_JAGGED_PASS |
| Kanto | Kanto Safari Zone | Tauros / Tauros Paldea Combat / Tauros Paldea Blaze / Tauros Paldea Aqua; Delibird; Electabuzz / Elekid / Electivire; Magmar / Magby / Magmortar | MAP_SAFARI_ZONE_CENTER, MAP_SAFARI_ZONE_EAST, MAP_SAFARI_ZONE_NORTH_FRLG, MAP_SAFARI_ZONE_WEST |
| Kanto | Kanto Victory Road | Diglett / Dugtrio / Diglett Alola / Dugtrio Alola; Numel / Camerupt; Hippopotas / Hippowdon; Rolycoly / Carkol / Coalossal | MAP_VICTORY_ROAD_1F_FRLG, MAP_VICTORY_ROAD_2F, MAP_VICTORY_ROAD_3F |
| Sevii | Kindle Road | Sandshrew / Sandslash / Sandshrew Alola / Sandslash Alola; Wooper / Quagsire / Clodsire / Wooper Paldea; Nosepass / Probopass; Frigibax / Arctibax / Baxcalibur | MAP_ONE_ISLAND_KINDLE_ROAD |
| Hoenn | Lilycove City | Squirtle / Wartortle / Blastoise | MAP_LILYCOVE_CITY |
| Sevii | Lost Cave | Wobbuffet / Wynaut; Sandile / Krokorok / Krookodile; Fuecoco / Crocalor / Skeledirge; Sandy Shocks | MAP_FIVE_ISLAND_LOST_CAVE_ROOM1, MAP_FIVE_ISLAND_LOST_CAVE_ROOM10, MAP_FIVE_ISLAND_LOST_CAVE_ROOM11, MAP_FIVE_ISLAND_LOST_CAVE_ROOM12, MAP_FIVE_ISLAND_LOST_CAVE_ROOM13, MAP_FIVE_ISLAND_LOST_CAVE_ROOM14, MAP_FIVE_ISLAND_LOST_CAVE_ROOM2, MAP_FIVE_ISLAND_LOST_CAVE_ROOM3, MAP_FIVE_ISLAND_LOST_CAVE_ROOM4, MAP_FIVE_ISLAND_LOST_CAVE_ROOM5, MAP_FIVE_ISLAND_LOST_CAVE_ROOM6, MAP_FIVE_ISLAND_LOST_CAVE_ROOM7, MAP_FIVE_ISLAND_LOST_CAVE_ROOM8, MAP_FIVE_ISLAND_LOST_CAVE_ROOM9 |
| Hoenn | Magma Hideout | Litten / Torracat / Incineroar; Oricorio Baile; Minior Meteor Red; Komala | MAP_MAGMA_HIDEOUT_1F, MAP_MAGMA_HIDEOUT_2F_1R, MAP_MAGMA_HIDEOUT_2F_2R, MAP_MAGMA_HIDEOUT_2F_3R, MAP_MAGMA_HIDEOUT_3F_1R, MAP_MAGMA_HIDEOUT_3F_2R, MAP_MAGMA_HIDEOUT_3F_3R, MAP_MAGMA_HIDEOUT_4F |
| Sevii | Memorial Pillar | Abra / Kadabra / Alakazam; Staryu / Starmie; Zigzagoon / Linoone / Obstagoon / Zigzagoon Galar / Linoone Galar; Litwick / Lampent / Chandelure | MAP_FIVE_ISLAND_MEMORIAL_PILLAR |
| Hoenn | Meteor Falls | Growlithe / Arcanine / Growlithe Hisui / Arcanine Hisui; Barboach / Whiscash; Honedge / Doublade / Aegislash Shield; Drampa | MAP_METEOR_FALLS_1F_1R, MAP_METEOR_FALLS_1F_2R, MAP_METEOR_FALLS_B1F_1R, MAP_METEOR_FALLS_B1F_2R, MAP_METEOR_FALLS_STEVENS_CAVE |
| Hoenn | Mirage Tower | Dreepy / Drakloak / Dragapult; Gimmighoul Chest / Gholdengo; Roaring Moon; Iron Boulder | MAP_MIRAGE_TOWER_1F, MAP_MIRAGE_TOWER_2F, MAP_MIRAGE_TOWER_3F, MAP_MIRAGE_TOWER_4F |
| Hoenn | Mossdeep City | Relicanth | MAP_MOSSDEEP_CITY |
| Sevii | Mt Ember | Fennekin / Braixen / Delphox; Passimian; Scorbunny / Raboot / Cinderace; Falinks | MAP_MT_EMBER_EXTERIOR, MAP_MT_EMBER_RUBY_PATH_1F, MAP_MT_EMBER_RUBY_PATH_B1F, MAP_MT_EMBER_RUBY_PATH_B1F_STAIRS, MAP_MT_EMBER_RUBY_PATH_B2F, MAP_MT_EMBER_RUBY_PATH_B2F_STAIRS, MAP_MT_EMBER_RUBY_PATH_B3F, MAP_MT_EMBER_SUMMIT_PATH_1F, MAP_MT_EMBER_SUMMIT_PATH_2F, MAP_MT_EMBER_SUMMIT_PATH_3F |
| Kanto | Mt Moon | Phanpy / Donphan; Baltoy / Claydol; Stunfisk / Stunfisk Galar; Stonjourner | MAP_MT_MOON_1F, MAP_MT_MOON_B1F, MAP_MT_MOON_B2F |
| Hoenn | Mt Pyre | Grimer / Muk / Grimer Alola / Muk Alola; Drowzee / Hypno; Zorua / Zoroark / Zorua Hisui / Zoroark Hisui; Charcadet / Armarouge / Ceruledge | MAP_MT_PYRE_1F, MAP_MT_PYRE_2F, MAP_MT_PYRE_3F, MAP_MT_PYRE_4F, MAP_MT_PYRE_5F, MAP_MT_PYRE_6F, MAP_MT_PYRE_EXTERIOR, MAP_MT_PYRE_SUMMIT |
| Hoenn | New Mauville | Spiritomb; Eiscue Ice; Flutter Mane; Iron Valiant | MAP_NEW_MAUVILLE_ENTRANCE, MAP_NEW_MAUVILLE_INSIDE |
| Sevii | One Island | Tropius; Finneon / Lumineon; Maractus; Karrablast / Escavalier | MAP_JOURNEYWORLDSEA01, MAP_ONE_ISLAND |
| Sevii | Outcast Island | Cramorant | MAP_SIX_ISLAND_OUTCAST_ISLAND |
| Hoenn | Pacifidlog Town | Tirtouga / Carracosta | MAP_PACIFIDLOG_TOWN |
| Kanto | Pallet Town | Basculegion M | MAP_PALLET_TOWN |
| Sevii | Pattern Bush | Stunky / Skuntank; Venipede / Whirlipede / Scolipede; Dwebble / Crustle; Toxel / Toxtricity Amped | MAP_SIX_ISLAND_PATTERN_BUSH |
| Hoenn | Petalburg City | Arctovish | MAP_PETALBURG_CITY |
| Hoenn | Petalburg Woods | Ekans / Arbok; Kricketot / Kricketune; Salandit / Salazzle; Glimmet / Glimmora | MAP_PETALBURG_WOODS |
| Kanto | Pokemon Mansion | Houndour / Houndoom; Shuppet / Banette; Duskull / Dusclops / Dusknoir; Chimecho / Chingling | MAP_POKEMON_MANSION_1F, MAP_POKEMON_MANSION_2F, MAP_POKEMON_MANSION_3F, MAP_POKEMON_MANSION_B1F |
| Kanto | Pokemon Tower | Nidoran F / Nidorina / Nidoqueen; Geodude / Graveler / Golem / Geodude Alola / Graveler Alola / Golem Alola; Exeggcute / Exeggutor / Exeggutor Alola; Iron Crown | MAP_POKEMON_TOWER_3F, MAP_POKEMON_TOWER_4F, MAP_POKEMON_TOWER_5F, MAP_POKEMON_TOWER_6F, MAP_POKEMON_TOWER_7F |
| Kanto | Power Plant | Gligar / Gliscor; Joltik / Galvantula; Fletchling / Fletchinder / Talonflame; Flabebe Red / Floette Red / Florges Red | MAP_POWER_PLANT |
| Sevii | Resort Gorgeous | Froakie / Frogadier / Greninja | MAP_FIVE_ISLAND_RESORT_GORGEOUS |
| Kanto | Rock Tunnel | Swinub / Piloswine / Mamoswine; Aron / Lairon / Aggron; Klink / Klang / Klinklang; Gouging Fire | MAP_ROCK_TUNNEL_1F, MAP_ROCK_TUNNEL_B1F |
| Kanto | Route 1 | Litleo / Pyroar; Milcery / Alcremie Strawberry Vanilla Cream; Tadbulb / Bellibolt; Varoom / Revavroom | MAP_ROUTE1 |
| Kanto | Route 10 | Remoraid / Octillery; Cubchoo / Beartic; Shelmet / Accelgor; Flamigo | MAP_ROUTE10 |
| Hoenn | Route 101 | Patrat / Watchog; Cottonee / Whimsicott; Dedenne; Greavard / Houndstone | MAP_ROUTE101 |
| Hoenn | Route 102 | Rockruff / Lycanroc Midday; Fomantis / Lurantis; Arrokuda / Barraskewda; Snom / Frosmoth | MAP_ROUTE102 |
| Hoenn | Route 103 | Volbeat; Deerling Spring / Sawsbuck Spring; Wattrel / Kilowattrel; Klawf | MAP_ROUTE103 |
| Hoenn | Route 104 | Venonat / Venomoth; Gulpin / Swalot; Roselia / Budew / Roserade; Skrelp / Dragalge | MAP_ROUTE104 |
| Hoenn | Route 105 | Poliwag / Poliwhirl / Poliwrath / Politoed | MAP_ROUTE105 |
| Hoenn | Route 106 | Wingull / Pelipper | MAP_ROUTE106 |
| Hoenn | Route 107 | Lotad / Lombre / Ludicolo | MAP_ROUTE107 |
| Hoenn | Route 108 | Ducklett / Swanna | MAP_ROUTE108 |
| Hoenn | Route 109 | Magikarp / Gyarados | MAP_ROUTE109 |
| Kanto | Route 11 | Yanma / Yanmega; Drifloon / Drifblim; Foongus / Amoonguss; Tatsugiri Curly | MAP_ROUTE11 |
| Hoenn | Route 110 | Psyduck / Golduck; Hitmonlee / Hitmonchan / Tyrogue / Hitmontop; Skwovet / Greedent; Morpeko Full Belly | MAP_ROUTE110 |
| Hoenn | Route 111 | Carnivine; Hawlucha; Noibat / Noivern; Chewtle / Drednaw | MAP_ROUTE111 |
| Hoenn | Route 112 | Goomy / Sliggoo / Goodra / Sliggoo Hisui / Goodra Hisui; Grookey / Thwackey / Rillaboom; Indeedee M; Dracozolt | MAP_ROUTE112 |
| Hoenn | Route 113 | Koffing / Weezing / Weezing Galar; Taillow / Swellow; Yungoos / Gumshoos; Squawkabilly Green | MAP_ROUTE113 |
| Hoenn | Route 114 | Timburr / Gurdurr / Conkeldurr; Swirlix / Slurpuff; Grubbin / Charjabug / Vikavolt; Flittle / Espathra | MAP_JOURNEYDEWFORDCOAST, MAP_JOURNEYRUSTBOROCOAST, MAP_ROUTE114 |
| Hoenn | Route 115 | Krabby / Kingler; Pachirisu; Rowlet / Dartrix / Decidueye / Decidueye Hisui; Bramblin / Brambleghast | MAP_ROUTE115 |
| Hoenn | Route 116 | Munna / Musharna; Cutiefly / Ribombee; Nymble / Lokix; Fidough / Dachsbun | MAP_ROUTE116 |
| Hoenn | Route 117 | Machop / Machoke / Machamp; Panpour / Simipour; Tynamo / Eelektrik / Eelektross; Silicobra / Sandaconda | MAP_ROUTE117 |
| Hoenn | Route 118 | Corphish / Crawdaunt; Lillipup / Herdier / Stoutland; Rookidee / Corvisquire / Corviknight; Brute Bonnet | MAP_ROUTE118 |
| Hoenn | Route 119 | Oddish / Gloom / Vileplume / Bellossom; Slowpoke / Slowbro / Slowking / Slowpoke Galar / Slowbro Galar / Slowking Galar; Wurmple / Silcoon / Beautifly / Cascoon / Dustox; Iron Moth | MAP_ROUTE119 |
| Kanto | Route 12 | Clamperl / Huntail / Gorebyss; Snover / Abomasnow; Mudbray / Mudsdale; Cufant / Copperajah | MAP_ROUTE12 |
| Hoenn | Route 120 | Weedle / Kakuna / Beedrill; Gastly / Haunter / Gengar; Mareanie / Toxapex; Rellor / Rabsca | MAP_ROUTE120 |
| Hoenn | Route 121 | Rattata / Raticate / Rattata Alola / Raticate Alola; Croagunk / Toxicroak; Audino; Applin / Flapple / Appletun / Dipplin / Hydrapple | MAP_ROUTE121 |
| Hoenn | Route 122 | Wishiwashi Solo | MAP_ROUTE122 |
| Hoenn | Route 123 | Sentret / Furret; Bunnelby / Diggersby; Wooloo / Dubwool; Iron Thorns | MAP_ROUTE123 |
| Hoenn | Route 124 | Alomomola | MAP_ROUTE124, MAP_UNDERWATER_ROUTE124 |
| Hoenn | Route 125 | Pyukumuku | MAP_ROUTE125 |
| Hoenn | Route 126 | Bruxish | MAP_ROUTE126, MAP_UNDERWATER_ROUTE126 |
| Hoenn | Route 127 | Iron Bundle | MAP_JOURNEYHOENNMIDDLESEA, MAP_JOURNEYHOENNNORTHSEA, MAP_JOURNEYHOENNSOUTHSEA, MAP_ROUTE127 |
| Hoenn | Route 128 | Quaxly / Quaxwell / Quaquaval | MAP_ROUTE128 |
| Hoenn | Route 129 | Piplup / Prinplup / Empoleon | MAP_ROUTE129 |
| Kanto | Route 13 | Goldeen / Seaking; Whismur / Loudred / Exploud; Mr Mime / Mime Jr / Mr Rime / Mr Mime Galar; Woobat / Swoobat | MAP_ROUTE13 |
| Hoenn | Route 130 | Mienfoo / Mienshao; Scatterbug Icy Snow / Spewpa Icy Snow / Vivillon Icy Snow; Veluza; Iron Jugulis | MAP_ROUTE130 |
| Hoenn | Route 131 | Lapras | MAP_ROUTE131 |
| Hoenn | Route 132 | Sobble / Drizzile / Inteleon | MAP_ROUTE132 |
| Hoenn | Route 133 | Dondozo | MAP_ROUTE133 |
| Hoenn | Route 134 | Omanyte / Omastar | MAP_ROUTE134 |
| Kanto | Route 14 | Vulpix / Ninetales / Vulpix Alola / Ninetales Alola; Meditite / Medicham; Espurr / Meowstic M; Sinistea Phony / Polteageist Phony | MAP_ROUTE14 |
| Kanto | Route 15 | Cacnea / Cacturne; Pumpkaboo Average / Gourgeist Average; Tandemaus / Maushold Three; Maschiff / Mabosstiff | MAP_ROUTE15 |
| Kanto | Route 16 | Poochyena / Mightyena; Vanillite / Vanillish / Vanilluxe; Shroodle / Grafaiai; Bombirdier | MAP_ROUTE16 |
| Kanto | Route 17 | Caterpie / Metapod / Butterfree; Girafarig / Farigiraf; Shroomish / Breloom; Raging Bolt | MAP_ROUTE17 |
| Kanto | Route 18 | Slakoth / Vigoroth / Slaking; Darumaka / Darmanitan Standard / Darumaka Galar / Darmanitan Galar Standard / Darmanitan Galar Zen; Klefki; Smoliv / Dolliv / Arboliva | MAP_ROUTE18 |
| Kanto | Route 19 | Dewpider / Araquanid | MAP_ROUTE19 |
| Kanto | Route 2 | Jigglypuff / Wigglytuff / Igglybuff; Makuhita / Hariyama; Spinda; Emolga | MAP_ROUTE2 |
| Kanto | Route 20 | Chinchou / Lanturn | MAP_ROUTE20 |
| Kanto | Route 21 | Shuckle; Combee / Vespiquen; Sewaddle / Swadloon / Leavanny; Stufful / Bewear | MAP_ROUTE21_NORTH, MAP_ROUTE21_SOUTH |
| Kanto | Route 22 | Ledyba / Ledian; Pidove / Tranquill / Unfezant; Basculin Red Striped; Scraggy / Scrafty | MAP_ROUTE22 |
| Kanto | Route 23 | Illumise; Swablu / Altaria; Glameow / Purugly; Solosis / Duosion / Reuniclus | MAP_ROUTE23 |
| Kanto | Route 24 | Hoppip / Skiploom / Jumpluff; Luvdisc; Bounsweet / Steenee / Tsareena; Slither Wing | MAP_ROUTE24 |
| Kanto | Route 25 | Natu / Xatu; Pansage / Simisage; Pikipek / Trumbeak / Toucannon; Capsakid / Scovillain | MAP_ROUTE25 |
| Kanto | Route 3 | Pikachu / Raichu / Pichu / Raichu Alola; Cherubi / Cherrim Overcast; Helioptile / Heliolisk; Poltchageist Counterfeit / Sinistcha Unremarkable | MAP_ROUTE3 |
| Kanto | Route 4 | Teddiursa / Ursaring / Ursaluna; Burmy Plant / Wormadam Plant / Mothim Plant; Frillish / Jellicent; Hatenna / Hattrem / Hatterene | MAP_ROUTE4 |
| Kanto | Route 5 | Voltorb / Electrode / Voltorb Hisui / Electrode Hisui; Nickit / Thievul; Lechonk / Oinkologne M; Cyclizar | MAP_ROUTE5 |
| Kanto | Route 6 | Hoothoot / Noctowl; Skitty / Delcatty; Bidoof / Bibarel; Trubbish / Garbodor | MAP_ROUTE6 |
| Kanto | Route 7 | Starly / Staravia / Staraptor; Pansear / Simisear; Rufflet / Braviary / Braviary Hisui; Comfey | MAP_ROUTE7 |
| Kanto | Route 8 | Spearow / Fearow; Meowth / Persian / Perrserker / Meowth Alola / Persian Alola / Meowth Galar; Blipbug / Dottler / Orbeetle; Iron Leaves | MAP_ROUTE8 |
| Kanto | Route 9 | Pineco / Forretress; Dunsparce / Dudunsparce Two Segment; Kecleon; Pawmi / Pawmo / Pawmot | MAP_ROUTE9 |
| Sevii | Ruin Valley | Mankey / Primeape / Annihilape; Surskit / Masquerain; Minun; Scream Tail | MAP_SIX_ISLAND_RUIN_VALLEY |
| Hoenn | Rusturf Tunnel | Nidoran M / Nidorino / Nidoking; Rhyhorn / Rhydon / Rhyperior; Trapinch / Vibrava / Flygon; Turtonator | MAP_RUSTURF_TUNNEL |
| Hoenn | Safari Zone | Eevee / Vaporeon / Jolteon / Flareon / Espeon / Umbreon / Leafeon / Glaceon / Sylveon; Chikorita / Bayleef / Meganium; Heracross; Smeargle | MAP_SAFARI_ZONE_NORTH, MAP_SAFARI_ZONE_NORTHEAST, MAP_SAFARI_ZONE_NORTHWEST, MAP_SAFARI_ZONE_SOUTH, MAP_SAFARI_ZONE_SOUTHEAST, MAP_SAFARI_ZONE_SOUTHWEST |
| Hoenn | Seafloor Cavern | Horsea / Seadra / Kingdra; Aerodactyl; Jynx / Smoochum; Solrock | MAP_SEAFLOOR_CAVERN_ENTRANCE, MAP_SEAFLOOR_CAVERN_ROOM1, MAP_SEAFLOOR_CAVERN_ROOM2, MAP_SEAFLOOR_CAVERN_ROOM3, MAP_SEAFLOOR_CAVERN_ROOM4, MAP_SEAFLOOR_CAVERN_ROOM5, MAP_SEAFLOOR_CAVERN_ROOM6, MAP_SEAFLOOR_CAVERN_ROOM7, MAP_SEAFLOOR_CAVERN_ROOM8 |
| Kanto | Seafoam Islands | Oranguru; Mimikyu Disguised; Dhelmise; Jangmo O / Hakamo O / Kommo O | MAP_SEAFOAM_ISLANDS_1F, MAP_SEAFOAM_ISLANDS_B1F, MAP_SEAFOAM_ISLANDS_B2F, MAP_SEAFOAM_ISLANDS_B3F, MAP_SEAFOAM_ISLANDS_B4F |
| Sevii | Sevault Canyon | Farfetchd / Sirfetchd / Farfetchd Galar; Porygon / Porygon2 / Porygon Z; Murkrow / Honchkrow; Miltank | MAP_SEVEN_ISLAND_SEVAULT_CANYON |
| Sevii | Seven Island | Buneary / Lopunny; Chansey / Blissey / Happiny; Spritzee / Aromatisse; Clobbopus / Grapploct | MAP_JOURNEYWORLDSEA07 |
| Hoenn | Shoal Cave | Shellder / Cloyster; Gible / Gabite / Garchomp; Sawk; Sigilyph | MAP_SHOAL_CAVE_LOW_TIDE_ENTRANCE_ROOM, MAP_SHOAL_CAVE_LOW_TIDE_ICE_ROOM, MAP_SHOAL_CAVE_LOW_TIDE_INNER_ROOM, MAP_SHOAL_CAVE_LOW_TIDE_LOWER_ROOM, MAP_SHOAL_CAVE_LOW_TIDE_STAIRS_ROOM |
| Sevii | Six Island | Snubbull / Granbull; Carvanha / Sharpedo; Yamper / Boltund; Great Tusk | MAP_JOURNEYWORLDSEA06 |
| Hoenn | Sky Pillar | Bulbasaur / Ivysaur / Venusaur; Charmander / Charmeleon / Charizard; Lickitung / Lickilicky; Kangaskhan | MAP_SKY_PILLAR_1F, MAP_SKY_PILLAR_3F, MAP_SKY_PILLAR_5F |
| Hoenn | Slateport City | Tympole / Palpitoad / Seismitoad | MAP_SLATEPORT_CITY |
| Hoenn | Sootopolis City | Spheal / Sealeo / Walrein | MAP_SOOTOPOLIS_CITY |
| Sevii | Tanoby Ruins | Wailmer / Wailord; Bronzor / Bronzong; Carbink; Duraludon / Archaludon | MAP_SEVEN_ISLAND_TANOBY_RUINS, MAP_SEVEN_ISLAND_TANOBY_RUINS_DILFORD_CHAMBER, MAP_SEVEN_ISLAND_TANOBY_RUINS_LIPTOO_CHAMBER, MAP_SEVEN_ISLAND_TANOBY_RUINS_MONEAN_CHAMBER, MAP_SEVEN_ISLAND_TANOBY_RUINS_RIXY_CHAMBER, MAP_SEVEN_ISLAND_TANOBY_RUINS_SCUFIB_CHAMBER, MAP_SEVEN_ISLAND_TANOBY_RUINS_VIAPOIS_CHAMBER, MAP_SEVEN_ISLAND_TANOBY_RUINS_WEEPTH_CHAMBER |
| Sevii | Three Isle Port | Clefairy / Clefable / Cleffa; Feebas / Milotic; Sprigatito / Floragato / Meowscarada; Iron Hands | MAP_JOURNEYWORLDSEA03, MAP_THREE_ISLAND_PORT |
| Sevii | Trainer Tower | Binacle / Barbaracle | MAP_SEVEN_ISLAND_TRAINER_TOWER |
| Sevii | Treasure Beach | Plusle; Zangoose; Snorunt / Glalie / Froslass; Ferroseed / Ferrothorn | MAP_ONE_ISLAND_TREASURE_BEACH |
| Sevii | Two Island | Electrike / Manectric; Pancham / Pangoro; Gossifleur / Eldegoss; Wiglett / Wugtrio | MAP_JOURNEYWORLDSEA02 |
| Kanto | Vermilion City | Spoink / Grumpig; Clauncher / Clawitzer; Sandygast / Palossand; Pincurchin | MAP_JOURNEYWORLDSEA00, MAP_SSANNE_EXTERIOR, MAP_VERMILION_CITY |
| Hoenn | Victory Road | Shellos West / Gastrodon West; Sudowoodo / Bonsly; Yamask / Cofagrigus / Runerigus / Yamask Galar; Bergmite / Avalugg / Avalugg Hisui | MAP_VICTORY_ROAD_1F, MAP_VICTORY_ROAD_B1F, MAP_VICTORY_ROAD_B2F |
| Kanto | Viridian City | Finizen / Palafin Zero | MAP_VIRIDIAN_CITY |
| Kanto | Viridian Forest | Zubat / Golbat / Crobat; Spinarak / Ariados; Sunkern / Sunflora; Sneasel / Weavile / Sneasler / Sneasel Hisui | MAP_VIRIDIAN_FOREST |
| Sevii | Water Labyrinth | Dracovish | MAP_FIVE_ISLAND_WATER_LABYRINTH |
| Sevii | Water Path | Torkoal; Shinx / Luxio / Luxray; Petilil / Lilligant / Lilligant Hisui; Tarountula / Spidops | MAP_SIX_ISLAND_WATER_PATH |

## Lendários, míticos e Ultra Beasts

Nenhum destes 105 Pokémon entra nos encontros aleatórios. Os altares só iniciam a batalha com oito insígnias de Kanto **e** oito de Hoenn, sem exigir vitória nas Ligas. Fugir ou derrotar o Pokémon permite tentar novamente. Capturá-lo desativa seu altar; capturas em locais antigos também são reconhecidas pela Pokédex.

As cavernas de Surf ficam nas novas ilhas desenhadas dentro do mar existente: desembarque e entre na montanha a pé. Nas cavernas de Dive, mergulhe no quadrado de água profunda, procure a entrada submersa e entre. As escadas internas levam de volta ao local de entrada.

As coordenadas abaixo são da entrada externa da caverna (Surf) ou do centro do trecho de água profunda (Dive), sem o deslocamento interno de sete tiles do motor.

| Local | Rota marítima | Acesso e coordenadas | Pokémon |
|---|---|---|---|
| Caverna Tempestades | JourneyWorldSea00 (Vermilion City) | Surf (44, 10) | Articuno, Zapdos, Raikou, Tornadus Incarnate, Thundurus Incarnate, Xurkitree, Zeraora, Regieleki |
| Caverna Aurora | JourneyWorldSea01 (One Island) | Surf (44, 10) | Mewtwo, Deoxys Normal, Azelf, Meloetta Aria, Tapu Koko, Necrozma, Zacian Hero, Fezandipiti |
| Caverna Vulcao | JourneyWorldSea02 (Two Island) | Surf (44, 10) | Moltres, Entei, Ho Oh, Groudon, Landorus Incarnate, Blacephalon, Ting Lu, Chi Yu |
| Caverna Titans | JourneyWorldSea03 (Three Isle Port) | Surf (44, 10) | Regirock, Registeel, Heatran, Diancie, Solgaleo, Celesteela, Stakataka, Meltan, Melmetal |
| Caverna Floresta | JourneyWorldSea04 (Four Island) | Surf (44, 10) | Celebi, Shaymin Land, Virizion, Silvally Normal, Tapu Bulu, Kartana, Calyrex, Ogerpon Teal |
| Caverna Eclipse | JourneyWorldSea05 (Five Island) | Surf (44, 10) | Regigigas, Giratina Altered, Darkrai, Yveltal, Guzzlord, Marshadow, Spectrier, Pecharunt |
| Caverna Dragoes | JourneyWorldSea06 (Six Island) | Surf (44, 10) | Rayquaza, Dialga, Cobalion, Reshiram, Zygarde 50, Naganadel, Zamazenta Hero, Kubfu, Koraidon |
| Caverna Estrelas | JourneyWorldSea07 (Seven Island) | Surf (44, 10) | Mew, Uxie, Cresselia, Xerneas Neutral, Tapu Lele, Magearna, Enamorus Incarnate |
| Caverna Cristais | JourneyWorldSea08 (Birth Island Frlg) | Surf (44, 10) | Regice, Terrakion, Kyurem, Nihilego, Glastrier, Chien Pao |
| Caverna Mares | JourneyHoennNorthSea (Route 127) | Surf + Dive (38, 10) | Suicune, Palkia, Manaphy, Volcanion, Terapagos Normal |
| Caverna Origens | JourneyHoennMiddleSea (Route 127) | Surf + Dive (38, 10) | Lugia, Latias, Latios, Zekrom, Cosmog, Eternatus, Regidrago, Miraidon |
| Caverna Profundezas | JourneyHoennSouthSea (Route 127) | Surf + Dive (38, 10) | Kyogre, Phione, Keldeo Ordinary, Tapu Fini, Urshifu Single Strike, Zarude, Wo Chien |
| Caverna Dimensoes | JourneyRustboroCoast (Route 114) | Surf + Dive (30, 64) | Jirachi, Mesprit, Victini, Hoopa Confined, Cosmoem, Lunala, Munkidori |
| Caverna Abismo | JourneyDewfordCoast (Route 114) | Surf + Dive (30, 64) | Arceus Normal, Genesect, Type Null, Buzzwole, Pheromosa, Poipole, Okidogi |

## Capturas especiais originais

Os eventos originais de captura também verificam as 16 insígnias. A movimentação dos personagens e os eventos de história foram preservados. Se o Pokémon já estiver marcado como capturado, a nova tentativa não inicia batalha.

- AncientTomb: Registeel.
- BirthIsland_Exterior: Deoxys Normal.
- CeruleanCave_B1F_Frlg: Mewtwo.
- DesertRuins: Regirock.
- FarawayIsland_Interior: Mew.
- IslandCave: Regice.
- MarineCave_End: Kyogre.
- MtEmber_Summit_Frlg: Moltres.
- NavelRock_Base_Frlg: Lugia.
- NavelRock_Bottom: Lugia.
- NavelRock_Summit_Frlg: Ho Oh.
- NavelRock_Top: Ho Oh.
- PowerPlant_Frlg: Zapdos.
- SeafoamIslands_B4F_Frlg: Articuno.
- SkyPillar_Top: Rayquaza.
- SouthernIsland_Interior: Latias, Latios.
- TerraCave_End: Groudon.

## Pontos aquáticos sem encontros

MAP_FIVE_ISLAND, MAP_FIVE_ISLAND_MEADOW, MAP_JOURNEYDEWFORDCOAST, MAP_JOURNEYRUSTBOROCOAST, MAP_JOURNEYWORLDSEA05, MAP_JOURNEYWORLDSEA07, MAP_ONE_ISLAND_TREASURE_BEACH, MAP_ROUTE103, MAP_ROUTE114, MAP_ROUTE121, MAP_ROUTE123, MAP_ROUTE21_NORTH, MAP_ROUTE21_SOUTH, MAP_ROUTE23, MAP_ROUTE25, MAP_SEAFOAM_ISLANDS_B3F, MAP_SEAFOAM_ISLANDS_B4F, MAP_SIX_ISLAND_WATER_PATH, MAP_THREE_ISLAND_BOND_BRIDGE, MAP_TWO_ISLAND_CAPE_BRINK.

## Limites da validação

Kanto, Hoenn e Sevii estão conectados na candidata; 96 travessias físicas por Surf e as entradas e saídas dos 14 santuários têm verificações nativas registradas. Ainda faltam revisão completa das rotas, interiores, NPCs, puzzles e as duas campanhas jogadas integralmente. Os relatórios de mGBA cobrem situações específicas; não equivalem a finalizar o jogo.

A arte de 3.323 imagens e 3.154 paletas foi comparada no motor ARM aos dados compilados. As 97 Megas têm referências auditadas; cinco transformações reais, Battle Bond, trocas, desmaios e batalhas duplas possuem verificações específicas. Isso não significa que todas as animações e batalhas foram jogadas. Os locais deste guia são da candidata, ainda não publicada no player.
