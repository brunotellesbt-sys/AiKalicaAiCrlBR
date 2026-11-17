"""Reject conditional-layout canonicalization and preserve the current terrain."""
import json
from pathlib import Path
import unittest
from atlas_neighbor_layouts import load,stage,refresh_saved_view
from atlas_surf_overlay import OverlaySource
from audit_neighbor_layouts import audit

PARENT=Path(__file__).resolve().parents[2]/'.local/generated-area-review-src'

@unittest.skipUnless((PARENT/'.journey-generated-area-review').exists(),'Immutable source fixture required')
class NeighborLayouts(unittest.TestCase):
    def test_only_header_is_aligned_to_the_already_active_layout(self):
        layer,_=load(PARENT);before=dict(layer.outputs);old=json.loads((PARENT/'data/maps/Route131/map.json').read_bytes())
        stage(layer);new=json.loads(layer.outputs['data/maps/Route131/map.json'])
        self.assertEqual(new,dict(old,layout='LAYOUT_ROUTE131_SKY_PILLAR'))
        self.assertEqual({n for n in layer.outputs if before.get(n)!=layer.outputs[n]},{'data/maps/Route131/map.json'})

    def test_new_condition_or_different_script_rejects_canonicalization(self):
        layer,_=load(PARENT);p='data/maps/Route131/scripts.inc'
        layer.stage(p,layer.outputs.get(p,(PARENT/p).read_bytes()).decode().replace('\tcall Route131_EventScript_SetLayout','\tcall_if_eq VAR_RESULT, TRUE, Route131_EventScript_SetLayout'))
        with self.assertRaisesRegex(ValueError,'unconditionally selected'):stage(layer)

    def test_census_keeps_conditional_maps_as_candidates_after_the_fix(self):
        layer,_=load(PARENT);stage(layer);r=audit(OverlaySource(layer))
        maps={row['map'] for row in r['alternate_layouts']}
        self.assertNotIn('Route131',maps);self.assertIn('Route130',maps);self.assertIn('Route111',maps)
        self.assertFalse(r['native_defects_confirmed'])

    def test_version7_only_refreshes_saved_background_for_version6(self):
        layer,_=load(PARENT);before=layer.outputs['src/load_save.c'].decode();refresh_saved_view(layer)
        after=layer.outputs['src/load_save.c'].decode()
        self.assertEqual(after,before.replace('if(VarGet(VAR_JOURNEY_SEVII_GEOMETRY_VERSION)>=6) return;','if(VarGet(VAR_JOURNEY_SEVII_GEOMETRY_VERSION)>=7) return;').replace('VarSet(VAR_JOURNEY_SEVII_GEOMETRY_VERSION,6);','VarSet(VAR_JOURNEY_SEVII_GEOMETRY_VERSION,7);'))

if __name__=='__main__':unittest.main()
