"""Native UI alone cannot admit arbitrary exclusions or invent graph edges."""
from types import SimpleNamespace
import unittest

from atlas_surf_native_features import FEATURES,_validate_component,verify_requirement


class NativeFeatureGuards(unittest.TestCase):
    def test_reviewed_glyph_must_be_an_entire_connected_isolated_blue_component(self):
        points=set(map(tuple,FEATURES['route12']['pixels']));truth=SimpleNamespace(blue_pixels=points)
        _validate_component(truth,FEATURES['route12']['pixels'])
        with self.assertRaisesRegex(ValueError,'piece of a larger'):
            _validate_component(truth,FEATURES['route12']['pixels'][:-1])
        with self.assertRaisesRegex(ValueError,'larger generated route'):
            _validate_component(SimpleNamespace(blue_pixels=points|{(95,40)}),FEATURES['route12']['pixels'])
        with self.assertRaisesRegex(ValueError,'not one isolated'):
            _validate_component(SimpleNamespace(blue_pixels={(1,1),(4,4)}),[[1,1],[4,4]])

    def test_an_authenticated_boolean_or_native_ui_claim_cannot_replace_physical_proof(self):
        row=dict(native_chart_feature='route12',point=FEATURES['route12']['point'],atlas=[93,39],authenticated=True)
        with self.assertRaisesRegex(ValueError,'physical proof'):verify_requirement(None,row)
        row.update(physical_native_point_and_coast_return_proven=True,reference_travel_proof_sha256='a'*64,point=['Elsewhere',8,48])
        with self.assertRaisesRegex(ValueError,'changed authored'):verify_requirement(None,row)
        row.update(point=FEATURES['route12']['point'],atlas=[94,39])
        with self.assertRaisesRegex(ValueError,'changed authored'):verify_requirement(None,row)


if __name__=='__main__':unittest.main()
