"""New exits must use actual free native water, never shadow an old seam."""
from copy import deepcopy
from pathlib import Path
import unittest

from atlas_surf_native_edges import derive,authenticate,donor,CONTACTS
from atlas_surf_source import Source

ROOT=Path(__file__).resolve().parents[2]


@unittest.skipUnless((ROOT/'.local/generated-area-review-src/.journey-generated-area-review').is_file(),
                     'Immutable revision171 source is not installed')
class ActualSlateportOutletTests(unittest.TestCase):
    def setUp(self):self.source=Source(ROOT/'.local/generated-area-review-src')

    def test_native_outlet_and_matching_donor_are_real_and_leave_old_connection_intact(self):
        before=deepcopy(self.source.maps['SlateportCity']);row=derive(self.source)
        self.assertEqual([tuple(w['native_tile']) for w in row['authored_native_edge_witnesses']],list(CONTACTS))
        self.assertTrue(all(w['native_word']>>12==1 for w in row['authored_native_edge_witnesses']))
        spec,proof=donor(self.source)
        self.assertEqual(self.source.word(spec['map'],*spec['reef_tile']),0x15f9)
        self.assertTrue(self.source.water(spec['map'],*spec['water_tile']))
        self.assertEqual(proof['banks'],['gTileset_General','gTileset_Slateport','emerald'])
        self.assertEqual(self.source.maps['SlateportCity'],before)
        self.source.assert_unchanged()

    def test_tampered_source_edge_or_a_shadowed_native_connection_is_rejected(self):
        row=derive(self.source);row['authored_native_edge_witnesses'][0]['native_word']^=0x1000
        with self.assertRaisesRegex(ValueError,'actual free native edge'):authenticate(self.source,row)
        self.source.maps['SlateportCity']['connections'].append(dict(direction='right',map='MAP_ROUTE134',offset=40))
        with self.assertRaisesRegex(ValueError,'shadow a native connection'):derive(self.source)


if __name__=='__main__':unittest.main()
