"""Content definitions for the connected Rocket/Magma/Aqua campaign."""

# These are additive encounters. Native trainers, items and warps retain IDs.
EPISODES = [
    dict(key='pewter', event=7, region='kanto', badge_count=4, team='magma',
         maps=[('PewterCity_Frlg', (24,24), 3)], admin=True,
         intro=['TEAM AQUA is invading KANTO!', 'We will erase them and take', 'control of the whole world!']),
    dict(key='vermilion', event=8, region='kanto', badge_count=4, team='aqua',
         maps=[('VermilionCity_Frlg', (29,14), 3)], admin=True,
         intro=['MAGMA is somewhere nearby.', 'We have not found their base.', 'AQUA will rule this world!']),
    dict(key='rock_tunnel', event=9, region='kanto', badge_count=4, team='magma',
         maps=[('RockTunnel_1F_Frlg', (24,11), 2), ('RockTunnel_B1F_Frlg', (23,15), 2)],
         intro=['KANTO will belong to MAGMA!', 'No AQUA fool can stop us!']),
    dict(key='western_sea', event=10, region='kanto', badge_count=4, team='aqua',
         maps=[('JourneyWestRiver', (12,7), 1), ('JourneyRustboroCoast', (12,18), 2),
               ('JourneyDewfordCoast', (12,28), 2)],
         intro=['These waters belong to AQUA!', 'Our reach extends to KANTO!']),
    dict(key='kanto_incursions', event=11, region='kanto', badge_count=4, team='mixed',
         maps=[('Route3_Frlg', (25,9), 1), ('Route6_Frlg', (16,16), 1),
               ('Route8_Frlg', (37,11), 1), ('Route15_Frlg', (35,10), 1)],
         intro=['Our team has reached KANTO!', 'This region will be ours!']),
    dict(key='hoenn_rocket', event=12, region='hoenn', badge_count=4, team='rocket',
         maps=[('JourneyRocketBaseB1F', (8,9), 4), ('JourneyRocketBaseB2F', (8,9), 5)],
         admin=True, intro=['This casino funds TEAM ROCKET.', 'Our HOENN branch obeys ATLAS.', 'No outsider leaves untested!']),
]

GUIDE_MESSAGES = {
    7: ('TEAM MAGMA', ['Take ROUTE 2 or 3 to PEWTER.', 'Defeat their three invaders!']),
    8: ('TEAM AQUA', ['Take ROUTE 6 to VERMILION.', 'Defeat their three invaders!']),
    9: ('TEAM MAGMA', ['Take ROUTE 10 to ROCK TUNNEL.', 'Clear both floors of MAGMA!']),
    10: ('TEAM AQUA', ['Surf south from CINNABAR.', 'Clear the western river and', 'RUSTBORO-DEWFORD sea route!']),
    11: ('MAGMA and AQUA', ['Clear the invaders on', 'KANTO ROUTES 3, 6, 8 and 15!']),
    12: ('TEAM ROCKET', ['Go to MAUVILLE GAME CORNER.', 'Use the rear floor passage.', 'Clear both basement floors!']),
    13: ('TEAM AQUA', ['We need GIOVANNI to help.', 'Finish SILPH CO. in SAFFRON', 'after six KANTO badges!']),
}

GIOVANNI_DIALOGUE = [
    'GIOVANNI: I regret my actions.',
    'I came here to repair them.',
    'ROCKET began to defend KANTO',
    'against possible tyranny by',
    'TEAM MAGMA and TEAM AQUA.',
    'But we lost that purpose.',
    'I let power and greed turn',
    'us into the threat ourselves.',
    'That does not excuse our harm.',
    'Today I will fight beside you',
    'to stop these villains!',
]

PARTNER_PARTY = '''
=== PARTNER_GIOVANNI ===
Name: GIOVANNI
Class: Boss Frlg
Pic: Leader Giovanni Frlg
Gender: Male
Music: Male
AI: Basic Trainer

Nidoking
Level: 56
IVs: 25 HP / 25 Atk / 25 Def / 25 SpA / 25 SpD / 25 Spe
- Earthquake
- Poison Jab
- Thunderbolt
- Protect

Nidoqueen
Level: 55
IVs: 25 HP / 25 Atk / 25 Def / 25 SpA / 25 SpD / 25 Spe
- Earth Power
- Thunderbolt
- Body Slam
- Protect

Rhydon
Level: 55
IVs: 25 HP / 25 Atk / 25 Def / 25 SpA / 25 SpD / 25 Spe
- Rock Slide
- Earthquake
- Megahorn
- Protect
'''
