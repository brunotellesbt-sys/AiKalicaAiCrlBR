"""Lightweight identities shared by source, packaging and CI verification."""
SCOPE = 'generated-world-audit'
HISTORICAL_COMMIT = '48d328cab66b4788a2ee74b3598272c158db1554'
PARENT_ROM_SHA256 = '3111ff0e2f5f1caa94b808c8fecf62f7b313d6b241014f416de31eff80105771'
PARENT_ELF_SHA256 = 'fb183bfeafd693fd64d2942ebbed16929ef23ceb8a5cee1f6d1bf544b4f360be'
PARENT_MARKER_SHA256 = '0ccf2a3c758788aca607e4ed3a6dc7878e2a629e7c9be4ac8463251056078590'
BASELINE_SHA256 = {
    'versions.json': '256ff6d42c9907d9e320ef621495e979d7cfcc8cc170ed3f04a86941ecf90143',
    'review.json': 'c48de52608bdd397bd328ad62a02b26e39d701f664c533ca59cb6e61604c5a3e',
    'test.sav': 'c420ff2fa5022cddd49b86c8efae62ab043f5e16bfb3b9977aa6e475bfe4ce27',
}

# Literal resource scope reviewed against complete native objects.
PREPARED_SHA256 = {'data/layouts/JourneyDepthAbismo/map.bin': '381c11aab3145eff814c83bb28fb213ab74dc560d147d58cfa5396749f89a392',
 'data/layouts/JourneyDepthDimensoes/map.bin': '381c11aab3145eff814c83bb28fb213ab74dc560d147d58cfa5396749f89a392',
 'data/layouts/JourneyDepthMares/map.bin': 'b42aeaff0e4ac588dbae8f0ea9310261c1e2d15da38bad9c878f670ddedaf2de',
 'data/layouts/JourneyDepthOrigens/map.bin': 'b42aeaff0e4ac588dbae8f0ea9310261c1e2d15da38bad9c878f670ddedaf2de',
 'data/layouts/JourneyDepthProfundezas/map.bin': 'b42aeaff0e4ac588dbae8f0ea9310261c1e2d15da38bad9c878f670ddedaf2de',
 'data/layouts/JourneyDewfordCoast/map.bin': '8ddde7c51823a7ad99a5a678cf2dd2a3c72991b332a9a2ca31c9908b32b29d6f',
 'data/layouts/JourneyEverGrandeBackSea/map.bin': '39528a29fedfae955d06c09f8f624b8e0440b3f676c0a8c0c9016ba25bdedc62',
 'data/layouts/JourneyEverGrandeBackSouthSea/map.bin': '3c6b2b39bfa296312bddecfe2337279a0734e27e632b2f239d2ce78387a8cd5a',
 'data/layouts/JourneyHoennMiddleEastSea/map.bin': '6d897d04589d321184f97c0e65b9cf6167948bd9e03a326bbdf135474ed2b24d',
 'data/layouts/JourneyHoennMiddleSea/map.bin': 'f11a78fd6619e5179b566507cfa075fa7ec96bc32332e788a20247a384fc03d8',
 'data/layouts/JourneyHoennNorthSea/map.bin': '337ec13d3ae8afab45d15201b25b1e15a990d7a01b4dc51a5ac70237c1945c26',
 'data/layouts/JourneyHoennSouthEastSea/map.bin': '544720ca771059214f5a06b00a8cc7c19dee7135bb782f707493fabc7de7b70f',
 'data/layouts/JourneyHoennSouthSea/map.bin': 'd9c12e69fbabc3988f6364533850978dd390808dca118ffdda6505ae76d103fd',
 'data/layouts/JourneyMossdeepOuterEastSea/map.bin': '7be36a970405541229cdc2688acadf03f10c4e663e5070a0515a3a428e8ff72c',
 'data/layouts/JourneyMossdeepOuterSea/map.bin': '386b613afc8f4022e54fd8cfd596a4ad03119b9d7e151563494fc41c1293ce8c',
 'data/layouts/JourneyPacifidlogSea/map.bin': '6b275651c061bdab8c950aea9edbf2ed5404caf21053037e898893805ecefd91',
 'data/layouts/JourneyRocketBaseB1F/map.bin': '5b04261e1f3758b4c6c689c35db2ac1f09196d7e590ec3eb4a30ad4ccd29bb2e',
 'data/layouts/JourneyRocketBaseB2F/map.bin': '154fcdc76f6f5cdc75e865fd3e44ceef1c6470a808f60426c7863068f2b021a4',
 'data/layouts/JourneyRustboroCoast/map.bin': '256abec0c1b7176ab8d50d19139206422450df5f8643aed250e9a9a0bd6ebf76',
 'data/layouts/JourneySanctuaryDimensoes/map.bin': '5ec26d0c6a23f53d73e9b20cf03bac221c1eae00f39c5b21a5b9781dc0d07c29',
 'data/layouts/Route105/map.bin': 'd3d626813579b3009a924d29249fe70f82343ffe3518ec59c3fbf42d1487d7b6',
 'data/layouts/Route107/map.bin': '35d3032ea9b2f30891c3fbca1ca8e840f8101b853e07da8293975fed42a735b7',
 'data/layouts/Route108/map.bin': 'f5f70c2374d1b68f30364de9bcebfb0a391803a4a6ff44e35bcee2a1d542dfd9',
 'data/layouts/Route109/map.bin': '458556cfcd726754bf96a48e8edbaca28da7fbba6ddbb7da1b42965b77779816',
 'data/layouts/Route124/map.bin': 'f907814880affe6d3df506f0d1bdeb046e169116a074af93514db9db9e5ceb19',
 'data/layouts/Route125/map.bin': 'ad1af492163230decd23b2402fd7bc80ddd1009d4b4d0704e5183675b1a3099d',
 'data/layouts/Route126/map.bin': '6ed3e1ac0d85acacb1274525502ef716afee32f0ab2fd6343378809b9a80c404',
 'data/layouts/Route131/map.bin': '64533bf92ab5eada5aeb8d8acfb69bcd28a9d661495710533bcbc4307933c821',
 'data/layouts/Route132/map.bin': '00f363e2f7319baeb2da774e698953a740910bece64500c7f5ce1c47077a7569',
 'data/layouts/Route133/map.bin': '22afec0011dda655975645132b09a91b18ea8526ff5e6e40705f189e1f2642bc',
 'data/layouts/Route134/map.bin': 'e577f330b8311cc4b33ed0bd4fe0ead6f30cc62944e398d657a646a5ef0f819b',
 'data/layouts/ThreeIsland_Frlg/map.bin': '4f5682557a2bbfdadaf8d3a599662a35c9a49d1c9bdfe2a5744858a55d15067b',
 'data/maps/JourneyFiveIslandHarborPortLodge/map.json': '431e78199178cf9f79c2af311e7de4248aae69e53d135341632bcf6d33a4977b',
 'data/maps/JourneyFourIslandHarborPortLodge/map.json': '1616535db095505f7190197741e1ec5fca58d272d08d77e8463d19ab5d76cac2',
 'data/maps/JourneyOneIslandHarborPortLodge/map.json': 'f68b9d14560c31f4fa0afd6e238c66925a9ba573032641ef7fe6614fe9544393',
 'data/maps/JourneySanctuaryDimensoes/map.json': 'fa75df0d6c27c19764e79c1dbc0c5e2fcc970015a0207d444e37db3c2b5597e9',
 'data/maps/JourneySevenIslandHarborPortLodge/map.json': 'e17b6044fd509200676686fc019fd9a7fc4c6ebc5564c4c9538a9b8775b3f819',
 'data/maps/JourneySixIslandHarborPortLodge/map.json': 'd0f240e44de6506e7592b2f40717c053db761feb1c4c6a977d99c8dd077ded81',
 'data/maps/JourneyThreeIslandHarborPortLodge/map.json': '5bfaae8b3376370a175435e49cf9c5b7289911fa5e6991913b78c380e0beb4b6',
 'data/maps/JourneyTwoIslandHarborPortLodge/map.json': '57a8727177fdaf45876e17bd566244f3890e7ca669461368017edb8411fe8e5d'}
