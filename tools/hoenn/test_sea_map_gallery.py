"""Gallery integrity and boundaries of controller-only campaign evidence."""
import ast
import json
from pathlib import Path
import struct
import unittest
ROOT=Path(__file__).resolve().parents[2]
GALLERY=ROOT/'mods/hoenn/sea-map-gallery'
class SeaMapGallery(unittest.TestCase):
    def test_gallery_matches_current_compiled_candidate(self):
        r=json.loads((GALLERY/'maps.json').read_text())
        candidate=json.loads((ROOT/'mods/hoenn/sea-landscapes-validation/preparation/reproduction.json').read_text())
        self.assertEqual(r['rom_sha256'],candidate['rom_sha256'])
        self.assertFalse(r['terrain_only']);self.assertFalse(r['campaign_validation'])
        self.assertEqual(len(r['maps']),41)
        self.assertNotIn('JourneyHoennCrossing',r['maps'])
        for name,m in r['maps'].items():
            png=(GALLERY/(name+'.png')).read_bytes()
            self.assertEqual(png[:8],b'\x89PNG\r\n\x1a\n')
            self.assertEqual(struct.unpack('>II',png[16:24]),(m['width_tiles']*16,m['height_tiles']*16))
            self.assertEqual(len(m['map_sha256']),64);self.assertEqual(len(m['blockdata_sha256']),64)

    def test_gallery_covers_all_sevii_ports_and_vertical_channels(self):
        r=json.loads((GALLERY/'maps.json').read_text())['maps']
        for i in range(1,8):
            destinations={c['map'] for c in r['JourneyWorldSea%02d'%i]['connections']}
            word=['ONE','TWO','THREE','FOUR','FIVE','SIX','SEVEN'][i-1]
            self.assertIn('MAP_'+word+'_ISLAND_HARBOR',destinations)
        for suffix in ['10','11','20','21','30','31']:self.assertIn('JourneyWorldLane'+suffix,r)

    def test_campaign_runner_contains_no_gameplay_mutations_or_fixture_entries(self):
        tree=ast.parse((ROOT/'tools/hoenn/validate_campaign_playthrough.py').read_text())
        forbidden={'native','warp','script','rawflag','raw_flag','write8','write16','write32','raw8'}
        calls=[]
        for n in ast.walk(tree):
            if isinstance(n,ast.Call):
                if isinstance(n.func,ast.Name):calls.append(n.func.id)
                if isinstance(n.func,ast.Attribute):calls.append(n.func.attr)
        self.assertFalse(forbidden.intersection(calls))

    def test_campaign_progress_is_not_reported_as_full_playthrough(self):
        for region in ['kanto','hoenn']:
            r=json.loads((ROOT/f'mods/hoenn/campaign-playthrough/{region}/campaign-playthrough.json').read_text())
            self.assertTrue(r['controller_only'])
            for field in ['ram_writes','script_injection','synthetic_badges','boosted_stats','disabled_wild_encounters','full_campaign_playthrough']:self.assertFalse(r[field])
            self.assertEqual(r['starting_region'],region)
            self.assertEqual(r['status'],'initial_segment_passed_campaign_incomplete')
            self.assertEqual(r['runner_sha256'],__import__('hashlib').sha256((ROOT/'tools/hoenn/validate_campaign_playthrough.py').read_bytes()).hexdigest())
            # Historical controller runs remain attached to the ROM they actually executed.
            self.assertEqual(r['rom_sha256'],json.loads((ROOT/'mods/hoenn/rusturf-reunion-validation/preparation/reproduction.json').read_text())['rom_sha256'])
            self.assertTrue(r['battles']);self.assertTrue(all(b['outcome']==1 for b in r['battles']))
            self.assertTrue(all(c['badges']==dict(kanto=0,hoenn=0) for c in r['checkpoints']))
            self.assertEqual(r['checkpoints'][-1]['party_count'],1)
            self.assertGreater(len(r['input_log']),100)
            self.assertEqual(r['checkpoints'][0]['map'],'InsideOfTruck')

if __name__=='__main__':unittest.main()
