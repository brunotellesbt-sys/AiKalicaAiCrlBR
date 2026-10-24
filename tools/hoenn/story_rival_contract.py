"""Independent identity and chronology fixtures for the four story protagonists."""

HERO_NAMES = {1: 'RED', 2: 'LEAF', 3: 'BRENDAN', 4: 'MAY'}
HERO_GRAPHICS = {1: 'OBJ_EVENT_GFX_RED_NORMAL', 2: 'OBJ_EVENT_GFX_GREEN_NORMAL',
                 3: 'OBJ_EVENT_GFX_BRENDAN_NORMAL', 4: 'OBJ_EVENT_GFX_MAY_NORMAL'}
HERO_PICTURES = {1: 'TRAINER_PIC_RED', 2: 'TRAINER_PIC_LEAF',
                3: 'TRAINER_PIC_BRENDAN', 4: 'TRAINER_PIC_MAY'}

# role order: local opposite sex, away opposite sex, away same sex.
# Literal expected roster rather than a second copy of the production formula.
ROLES = {
    (1, 0): (4, 2, 3), (2, 0): (3, 1, 4),
    (3, 0): (4, 2, 1), (4, 0): (3, 1, 2),
    (1, 1): (2, 4, 3), (2, 1): (1, 3, 4),
    (3, 1): (2, 4, 1), (4, 1): (1, 3, 2),
}
ROLES.update({(hero, 2): ROLES[hero, 1] for hero in HERO_NAMES})

KANTO_FAMILIES = (
    ('RIVAL_OAKS_LAB', 2), ('RIVAL_ROUTE22_EARLY', 2),
    ('RIVAL_CERULEAN', 1), ('RIVAL_SS_ANNE', 2),
    ('RIVAL_POKEMON_TOWER', 1), ('RIVAL_SILPH', 2),
    ('RIVAL_ROUTE22_LATE', 1), ('CHAMPION_FIRST', 2), ('CHAMPION_REMATCH', 2),
)
HOENN_FAMILIES = (('ROUTE_103', 2), ('RUSTBORO', 1), ('ROUTE_110', 2),
                  ('ROUTE_119', 1), ('LILYCOVE', 2))
NATIVE_TRAINERS = (
    [(f'TRAINER_{family}_{starter}', True, slot)
     for family, slot in KANTO_FAMILIES
     for starter in ('SQUIRTLE', 'BULBASAUR', 'CHARMANDER')]
    + [(f'TRAINER_{gender}_{family}_{starter}', False, slot)
       for family, slot in HOENN_FAMILIES
       for gender in ('BRENDAN', 'MAY')
       for starter in ('TREECKO', 'TORCHIC', 'MUDKIP')]
)

MAPS = (
    ('PalletTown_ProfessorOaksLab_Frlg', 'MAP_PALLET_TOWN_PROFESSOR_OAKS_LAB', True, 2),
    ('Route22_Frlg', 'MAP_ROUTE22', True, 2),
    ('CeruleanCity_Frlg', 'MAP_CERULEAN_CITY', True, 1),
    ('SSAnne_2F_Corridor_Frlg', 'MAP_SSANNE_2F_CORRIDOR', True, 2),
    ('PokemonTower_2F_Frlg', 'MAP_POKEMON_TOWER_2F', True, 1),
    ('SilphCo_7F_Frlg', 'MAP_SILPH_CO_7F', True, 2),
    ('PokemonLeague_ChampionsRoom_Frlg', 'MAP_POKEMON_LEAGUE_CHAMPIONS_ROOM', True, 2),
    ('IndigoPlateau_Exterior_Frlg', 'MAP_INDIGO_PLATEAU_EXTERIOR', True, 2),
    ('FourIsland_Frlg', 'MAP_FOUR_ISLAND', True, 1),
    ('SixIsland_PokemonCenter_1F_Frlg', 'MAP_SIX_ISLAND_POKEMON_CENTER_1F', True, 2),
    ('LittlerootTown', 'MAP_LITTLEROOT_TOWN', False, 2),
    ('LittlerootTown_ProfessorBirchsLab', 'MAP_LITTLEROOT_TOWN_PROFESSOR_BIRCHS_LAB', False, 2),
    ('LittlerootTown_BrendansHouse_1F', 'MAP_LITTLEROOT_TOWN_BRENDANS_HOUSE_1F', False, 2),
    ('LittlerootTown_BrendansHouse_2F', 'MAP_LITTLEROOT_TOWN_BRENDANS_HOUSE_2F', False, 2),
    ('LittlerootTown_MaysHouse_1F', 'MAP_LITTLEROOT_TOWN_MAYS_HOUSE_1F', False, 2),
    ('LittlerootTown_MaysHouse_2F', 'MAP_LITTLEROOT_TOWN_MAYS_HOUSE_2F', False, 2),
    ('OldaleTown', 'MAP_OLDALE_TOWN', False, 2),
    ('Route103', 'MAP_ROUTE103', False, 2),
    ('RustboroCity', 'MAP_RUSTBORO_CITY', False, 1),
    ('Route104', 'MAP_ROUTE104', False, 1),
    ('Route110', 'MAP_ROUTE110', False, 2),
    ('LavaridgeTown', 'MAP_LAVARIDGE_TOWN', False, 1),
    ('Route119', 'MAP_ROUTE119', False, 1),
    ('LilycoveCity', 'MAP_LILYCOVE_CITY', False, 2),
    ('EverGrandeCity_ChampionsRoom', 'MAP_EVER_GRANDE_CITY_CHAMPIONS_ROOM', False, 2),
)


def expected_trainer(hero, birthplace, kanto, away_slot):
    return ROLES[hero, birthplace][0 if bool(kanto) == (birthplace != 0) else away_slot]
