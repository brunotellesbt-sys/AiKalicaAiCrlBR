"""AREA restoration needs the exact new reachable land encounter, not a pool."""
from copy import deepcopy
import unittest
from atlas_dex_retired_habitats import relocate


class RestoredLandDex(unittest.TestCase):
    def fixture(self):
        owner='JourneyWorldSea00';current='JourneyAtlasScene012'
        before=dict(schema='atlas-surf-ecology-source-v1',native_c_compiled=True,
                    retired_maps=[],map_constants={owner:'MAP_OLD'},map_areas=[],source_manifest_sha256='before')
        row=dict(map=current,owner=owner,area=0,field='land_mons',species={'493':[1]},
                 trigger_sample=[[2,3]],terrain_trigger_cells=4,native_header_present=True)
        after=dict(before,retired_maps=[owner],graph_reachable_cells_supplied=True,
                   aliases={current:owner},map_constants={owner:'MAP_OLD',current:'MAP_CURRENT'},
                   map_areas=[row],source_manifest_sha256='after')
        plan=dict(scale=8,chunks=[dict(name=current,id='MAP_CURRENT',width=10,height=10,origin=[8,8])])
        return ('sWorldDexLocations[]={\n{SPECIES_ONE,MAP_OLD,1,1,0,4},\n};',before,after,plan,{'1':{'name':'SPECIES_ONE'}})

    def test_only_reviewed_owner_with_exact_reachable_land_can_be_restored(self):
        args=self.fixture()
        _,original=relocate(*args)
        self.assertEqual(len(original['removed_historically_ineffective']),1)
        header,repaired=relocate(*args,restore_inactive_from_owners=['JourneyWorldSea00'])
        self.assertIn('MAP_CURRENT',header)
        self.assertTrue(repaired['relocated'][0]['restored_land_trigger'])
        self.assertEqual(repaired['removed_historically_ineffective'],[])

    def test_other_owner_water_wrong_cap_and_missing_species_are_rejected(self):
        for key,value in (('owner','JourneyWorldSea01'),('area',1),('species',{'1025':[1]}),('species',{'493':[]})):
            args=list(deepcopy(self.fixture()));args[2]['map_areas'][0][key]=value
            with self.assertRaises(ValueError):
                relocate(*args,restore_inactive_from_owners=['JourneyWorldSea00'])
        with self.assertRaisesRegex(ValueError,'Unreviewed owner'):
            relocate(*self.fixture(),restore_inactive_from_owners=['JourneyRustboroCoast'])
