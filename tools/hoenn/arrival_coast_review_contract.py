"""Pinned layer-166 identities for the arrival/coast follow-up."""
SCOPE = 'arrival-coast-review'
HISTORICAL_COMMIT = '23881bc1c3f3326befe2cfbe357da06abc63a062'
PARENT_ROM_SHA256 = 'f7af65b4856e6697d5d972f48f8699c7c6b7d4b277ea19cfa3949926265d1b89'
PARENT_ELF_SHA256 = '3f8ba485b37d17f58f7c7a5a64b1a8dd28492a9ea612afdead2487ceef3d1f9e'
PARENT_MARKER_SHA256 = '416e5a30dc084d82ad6a50f1e3cf0fb3767cfdc4b25b38a710eabb6bbe1866ce'
BASELINE_SHA256 = {
    'versions.json': 'e655ae718eee24044bfcecb6812b3c40e764335e53b61b314c18d18d7b9062a8',
    'review.json': '3e6a948181c48faa3a267cce944ab5e3cb7ce258ff56dd32b1c72bd6f49b14ce',
    'test.sav': 'aee846ce79e19c8576bb92d6f5492bb09f8b90a98c372622df9196a12131cd83',
}
# Pin exact reviewed output paths and bytes after the helpers finish.
PREPARED_SHA256 = {'data/layouts/CinnabarIsland_Frlg/map.bin': '95d9ae45fd9bdf8920d9403383fd10b4990760240bb6100fe87341cc2bd0ff38',
 'data/layouts/FuchsiaCity_Frlg/map.bin': '3d8d8e0478fe6ae8cc13a3c9c05f1fe3dfc36de1e9e9a48a3ef964aa0c3837a1',
 'data/layouts/JourneyFuchsiaInlet/map.bin': '50d96c3ae9cdb448853c62289591232875625ea2a8e3bc5161b8434a2e842f61',
 'data/layouts/JourneyKantoSouthSea/map.bin': '98e1847826620e8c57e7ebbf454826d6151cd76d1acfcdc7f38ae6e15343eb77',
 'data/layouts/JourneyRoute13Coast/map.bin': '09028068c61791da68d86b175ecfe4f0ba4083c7a5107c66311b437f737322da',
 'data/layouts/OneIsland_Frlg/map.bin': 'bbb244815148f7ab775df82a7656c5ce3baf67d3142a283aabc656783ba65364',
 'data/layouts/Route14_Frlg/map.bin': '27f251b5d4cbcf8efe40e802119e3fd260be76d1c65cf562533c683dddeda3a9',
 'data/layouts/Route15_Frlg/map.bin': 'be06f8208cd9089831dcaee57fb0f3ad4a751909c93402d30a2f3bb5d910df6c',
 'data/layouts/layouts.json': 'e8ae0e118d33fbf46d202260e3ee459f73d80001def3fb02451885890f479f05',
 'data/maps/OneIsland_Frlg/map.json': 'b06666fdc17d663ba2fb52caeca3a846be8aa435c92eb1163caf02637adcb707',
 'data/tilesets/primary/general_frlg/journey_sevii_sea_metatiles.bin': '01228024beb436dcaa14fd645916fc401a4639003aecc13708aee458b262dfd7',
 'include/constants/event_objects.h': '21fbd17251525eefc6a99b90f95caaec7ac22e81b1440bf1a641676347107fcf',
 'include/journey_birth_arrivals.h': '13ec366b1ab5c64dd62f024a71473c9c9bd742e62a6a5cf495b4c6222e488328',
 'src/data/object_events/object_event_graphics_info_pointers.h': 'cd8dedfc28221b142e4ab2fbcc92887d4344a3974c49a7266f24e9b25746c437',
 'src/event_object_movement.c': '851472ca7ec707d466f0fbf5f6f3758d6ca58edaef3730bbc65c4bb627e42046',
 'src/overworld.c': '9a19d8d32296d9ca07cd5e74fa2afc4742398e07643766418e15d91b5a255eaf'}
# Final observation contracts are enforced by the four strict proof verifiers.
NATIVE_CONTRACT_FINALIZED = True
