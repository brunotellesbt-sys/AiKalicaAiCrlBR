"""Destination checks must reject missing warps while respecting chosen homes."""
import csv
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from audit_map_destinations import audit

ROOT = Path(__file__).resolve().parents[2]


class DestinationChecks(unittest.TestCase):
    def fixture(self, root):
        (root / 'data/maps').mkdir(parents=True)
        (root / 'data/layouts').mkdir(parents=True)
        (root / 'src').mkdir()
        (root / 'src/journey_family.c').write_text('fixture')
        (root / 'data/layouts/layouts.json').write_text(json.dumps({'layouts': [dict(id='L', width=10, height=10)]}))
        (root / '.journey-birth').write_text(json.dumps({'homes': [dict(original_map='HOUSE', living_map='LIVING', bedroom_map='BEDROOM')]}))
        for name, warps in [('HOUSE', []), ('LIVING', [dict(x=1,y=1,dest_map='BEDROOM',dest_warp_id='0')]),
                            ('BEDROOM', [dict(x=1,y=1,dest_map='HOUSE',dest_warp_id='0')])]:
            path = root / 'data/maps' / name
            path.mkdir()
            (path / 'map.json').write_text(json.dumps(dict(id=name,layout='L',warp_events=warps,connections=None)))

    def test_selected_house_resolves_to_living_interior(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); self.fixture(root)
            result = audit(root)
            self.assertTrue(result['passed'])
            self.assertEqual(result['conditional_home_destinations'][0]['effective'], 'LIVING')

    def test_invalid_destination_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); self.fixture(root)
            path = root / 'data/maps/BEDROOM/map.json'
            data = json.loads(path.read_text())
            data['warp_events'][0]['dest_warp_id'] = '9'
            path.write_text(json.dumps(data))
            self.assertFalse(audit(root)['passed'])

    def test_location_documents_cover_each_canonical_once(self):
        output = ROOT / 'mods/hoenn'
        report = json.loads((output / 'location-documentation.json').read_text())
        for name, digest in report['documents_sha256'].items():
            self.assertEqual(hashlib.sha256((output / name).read_bytes()).hexdigest(), digest, name)
        catalog = json.loads((ROOT / 'tools/hoenn/catalog_metadata.json').read_text())
        canonical = set(catalog['canonical_species'].values())
        with (output / 'pokemon-locations.csv').open() as stream:
            rows = list(csv.DictReader(stream))
        base = [r for r in rows if int(r['internal_id']) in canonical]
        self.assertEqual(len(base), 1025)
        self.assertEqual({int(r['national_dex']) for r in base}, set(range(1,1026)))
        specials = [r for r in base if r['category'] in ('lendário','mítico','Ultra Beast')]
        self.assertEqual(len(specials), 105)
        self.assertEqual({int(r['internal_id']) for r in specials}, set(catalog['special_species']))
        self.assertTrue(all(r['region'] in ('Kanto','Hoenn','Sevii') for r in rows))


if __name__ == '__main__':
    unittest.main()
