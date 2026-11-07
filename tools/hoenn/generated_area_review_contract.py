"""Pinned layer-170 identities for the generated-area follow-up."""
SCOPE = 'generated-area-review'
HISTORICAL_COMMIT = '6f45ef80fd0e0adf7864978ff56aac8ca8404cf3'
PARENT_ROM_SHA256 = '6a70d43313df75d2258c5bac46d7ab8c0aa50b6e4f1a7246d540159ee726d5fc'
PARENT_ELF_SHA256 = 'df384a54339cbd4de07c187592208ef4999636f095856e34aa4c1a47e5303545'
PARENT_MARKER_SHA256 = 'fc9154e5abb63d38714cb5fa094f6ce96413f0403c5512990e8646d556d41652'
BASELINE_SHA256 = {
    'versions.json': 'f2032e91d771ca47204d88b347210a6521801544560a737195b901c7809490f0',
    'review.json': '815f88c3eadd9776e2a398e6a5bb453a403741d7af051f485278d8fa9f38f9d8',
    'test.sav': '28235301c63c6c49011a09f7e97cbcb91a926c8a85b1fa699f161b1aa91d89b1',
}
# Pin the independently replayed final source before freezing or publication.
PREPARED_SHA256 = {'data/event_scripts.s': '2bf6f4402b8b91f23e4b1108113f986e5092703ebb2473b1364a6777cb8b5dc8',
 'data/layouts/FiveIsland_Frlg/map.bin': 'c0ee2ab7df07b20750a77dbc38b139e567c72e1d70974e995f908534d76896e9',
 'data/layouts/FourIsland_Frlg/map.bin': 'f52cc483c7c7a65e4f11aed80727f8cf40f717aec3467b15bdc2adc00e849834',
 'data/layouts/JourneyCaveHorizonte/map.bin': '358ccce76f8c5add46fdbb44b5b2366442824efde65ff2f372446c9796327310',
 'data/layouts/JourneyKantoSeviiTransit/map.bin': '31473ca5fa7774e1fae16a45bc94065aa0b5f60d02fd80af494ae475355a0196',
 'data/layouts/JourneyOneSouthPassage/border.bin': '23d6a6e9b3db90a879a59c7179bc454f488d9864441da95e0b384ad9f639be1e',
 'data/layouts/JourneyOneSouthPassage/map.bin': '6a57a9b7cc9f1615541897ead84d04adf72a1321a957515426a0a12f433111c4',
 'data/layouts/OneIsland_TreasureBeach_Frlg/map.bin': 'e43cbc4dd0cd07e091e9814207b6a44533028ce141c7911037bfaacba07f4d4f',
 'data/layouts/SevenIsland_SevaultCanyon_Entrance_Frlg/map.bin': 'bdb1351822351b7413c4f6bab2b707e310c93ae183889d8785cb2c812a72285b',
 'data/layouts/SixIsland_Frlg/map.bin': 'c6cde0f7b537fbe858d1cd9aa8596c4a50e2210c48d4cee0906938f13adee189',
 'data/layouts/ThreeIsland_Port_Frlg/map.bin': 'd72bd163410f3e487471f3b890578aafa55ea70df6d901d2a25b17fd84858145',
 'data/layouts/layouts.json': '50ef871fee9bbcd16d1cae27effa32fbd03d10acee3b2486d739937a779f6062',
 'data/maps/JourneyKantoSeviiTransit/map.json': '5a4b1cc2bdb2b1fa12de6297ecd49696874a61d62a5e8cd9a77ffd7f4738a1a5',
 'data/maps/JourneyOneSouthPassage/map.json': '86278adb224fc108880545fdf32dbc840f2b49250acdbc43e2851d35af608cf7',
 'data/maps/JourneyOneSouthPassage/scripts.inc': '659d7916515612d8ee97d396c5c2669ed9d661308de59a134378e5bda039aa10',
 'data/maps/OneIsland_TreasureBeach_Frlg/map.json': '47e707633185c6ed4fed6e0b07daf990e33362c53091dae1408237585da9e87a',
 'data/maps/map_groups.json': 'c141d04fb8c3854982e905c506b3c5e6c4145b5e7d644ba2ccba1d9bb9c96147',
 'src/data/journey_world_map.h': '39f09f8e515db58fe399c83763ba520a129ccdd90903a05813ead5046029b357',
 'src/data/journey_world_position.h': '0ecb77cf5c3582b53a2853e8204711aa39687292fa8856b85b97c4a03176944f',
 'src/data/wild_encounters.json': 'a617e275ee39411043ff46ed3e81e93e48e1cf0779f08a4f5cb4983f5842252f',
 'src/fieldmap.c': 'bdeb49977abcb7deb26abaee5b72d3255b496be0bff3a1541fc3efe12c1ace15'}
# Finalize only after the actual source/native report schemas are reviewed.
NATIVE_CONTRACT_FINALIZED = True
