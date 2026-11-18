"""Retired routes must never supply fictitious AREA destinations."""
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
import unittest

from atlas_dex_retired_habitats import relocate
from atlas_surf_ecology import DEX_ROW

ROOT=Path(__file__).resolve().parents[2]


class RetiredDexReferences(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load=lambda p:json.loads(gzip.decompress((ROOT/p).read_bytes()))
        cls.fixture=load('tools/hoenn/data/retired-dex-relocation-fixture.json.gz')
        cls.before=load('docs/design/atlas-surf-layout/ecology-parent-source.json.gz')
        cls.after=load('docs/design/legendary-chambers-review/large-caves-v8/followup/ecology-source/graph-bounded.json.gz')
        cls.catalog=json.loads((ROOT/'tools/hoenn/catalog_metadata.json').read_bytes())['species']
        cls.header=cls.fixture['header'];cls.plan=cls.fixture['plan']
        assert hashlib.sha256(cls.header.encode()).hexdigest()==cls.fixture['header_sha256']

    def test_all_effective_claims_move_to_exact_species_and_all_native_rows_survive(self):
        header,r=relocate(self.header,self.before,self.after,self.plan,self.catalog)
        self.assertEqual(len(r['relocated']),978)
        self.assertEqual(sum(x['owner_changed'] for x in r['relocated']),261)
        self.assertEqual(len(r['removed_historically_ineffective']),72)
        retired={self.after['map_constants'][n] for n in self.after['retired_maps']}
        self.assertFalse(any(m[2] in retired for m in DEX_ROW.finditer(header)))
        original={m[0] for m in DEX_ROW.finditer(self.header) if m[2] not in retired}
        self.assertLessEqual(original,{m[0] for m in DEX_ROW.finditer(header)})

    def test_pool_without_reachable_cells_is_rejected(self):
        after=dict(self.after,graph_reachable_cells_supplied=False)
        with self.assertRaisesRegex(ValueError,'graph witnesses'):
            relocate(self.header,self.before,after,self.plan,self.catalog)

    def test_missing_exact_species_cannot_be_replaced_by_its_family(self):
        after=deepcopy(self.after)
        sid=next(int(k) for k,v in self.catalog.items() if v['name']=='SPECIES_ALOMOMOLA')
        for row in after['map_areas']:
            row['species']['1025']=[s for s in row['species']['1025'] if s!=sid]
        with self.assertRaisesRegex(ValueError,'no reachable current trigger'):
            relocate(self.header,self.before,after,self.plan,self.catalog)

    def test_wrong_map_constant_cannot_reuse_a_real_trigger(self):
        plan=deepcopy(self.plan)
        for row in plan['chunks']:
            row['id']='MAP_ROUTE1'
        with self.assertRaisesRegex(ValueError,'map constant'):
            relocate(self.header,self.before,self.after,plan,self.catalog)

    def test_outside_trigger_cannot_create_an_atlas_marker(self):
        after=deepcopy(self.after)
        for row in after['map_areas']:
            if row['map'] in {r['name'] for r in self.plan['chunks']} and any(row['species'].values()):
                row['trigger_sample']=[[32767,32767]]
        with self.assertRaisesRegex(ValueError,'outside its real map'):
            relocate(self.header,self.before,after,self.plan,self.catalog)
