"""Regression checks for aquatic coverage without erasing unrelated ecology.

These integration checks use the locally acquired immutable layer-165 source;
CI without that source skips them rather than fabricating encounter fixtures.
"""
import hashlib
import json
from pathlib import Path
import re
import unittest

from candidate_layer import Layer
from coastal_ecology_encounters import repair, parse_pools, parse_habitats
from prepare_coastal_ecology import PRIOR, LAYER

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / '.local/generated-world-audit-src'


@unittest.skipUnless((SOURCE/'.journey-generated-world-audit').exists(),
                     'Requires the acquired immutable layer-165 source')
class AquaticEcologyPreservation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.layer = Layer(SOURCE, LAYER, PRIOR)
        cls.report = repair(cls.layer)
        cls.before_rows = json.loads((SOURCE/'src/data/wild_encounters.json').read_text())[
            'wild_encounter_groups'][0]['encounters']
        cls.after_rows = json.loads(cls.layer.outputs['src/data/wild_encounters.json'])[
            'wild_encounter_groups'][0]['encounters']
        cls.target_ids = {t['map_id'] for t in cls.report['targets']}

    def test_existing_terrestrial_and_scripted_encounters_are_not_erased(self):
        for before, after in zip(self.before_rows, self.after_rows):
            self.assertEqual(before['map'], after['map'])
            for field in ('land_mons', 'rock_smash_mons', 'hidden_mons'):
                self.assertEqual(before.get(field), after.get(field),
                                 (before['map'], field))
        for cap, path, array in (
            (9, 'include/journey_wild_data.h', 'sJourneyWildPools'),
            (4, 'include/journey_generation4_pools.h', 'sJourneyGeneration4Pools')):
            before = parse_pools((SOURCE/path).read_text(), array)[0]
            after = parse_pools(self.layer.outputs[path].decode(), array)[0]
            for key, species in before.items():
                if key[1] not in (1, 3):
                    self.assertEqual(after[key], species, (cap, key))
            self.assertLessEqual({s for pool in before.values() for s in pool},
                                 {s for pool in after.values() for s in pool})

    def test_every_declared_aquatic_travel_map_has_native_water_and_valid_pools(self):
        by_map = {row['map']: row for row in self.after_rows}
        for target in self.report['targets']:
            row = by_map[target['map_id']]
            self.assertGreater(row['water_mons']['encounter_rate'], 0, target['map'])
            self.assertEqual(len(row['water_mons']['mons']), 5, target['map'])
            for cap in ('4', '9'):
                variant = target['variants'][cap]
                self.assertTrue(variant['roots'], (target['map'], cap))
                self.assertTrue(variant['ordinary_aquatic_members'], (target['map'], cap))
                self.assertTrue(variant['habitat_ids'], (target['map'], cap))
            if 'fishing_mons' in target['fields']:
                self.assertEqual(len(row['fishing_mons']['mons']), 10, target['map'])

    def test_city_coasts_are_included_and_facility_or_cave_data_is_preserved(self):
        self.assertIn('MAP_MAUVILLE_CITY', self.target_ids)
        self.assertIn('MAP_RUSTBORO_CITY', self.target_ids)
        self.assertTrue({t['map'] for t in self.report['targets']}.issuperset(
            {'JourneyDepthAbismo', 'JourneyDepthMares', 'JourneyDepthOrigens',
             'JourneyDepthProfundezas', 'JourneyDepthDimensoes'}))
        for before, after in zip(self.before_rows, self.after_rows):
            if before['map'] not in self.target_ids:
                self.assertEqual(before, after, before['map'])

    def test_family_owners_remain_unique_and_three_open_sea_habitats_are_varied(self):
        for cap, habitats in self.report['locations_data'].items():
            owners = [family['root'] for habitat in habitats for family in habitat['families']]
            self.assertEqual(len(owners), len(set(owners)), cap)
            self.assertEqual(len(owners), {4:212, 9:424}[cap])
        by_map = {target['map_id']: target for target in self.report['targets']}
        north, middle, south = (by_map['MAP_JOURNEYHOENN'+name+'SEA']
                                for name in ('NORTH', 'MIDDLE', 'SOUTH'))
        for cap in ('4', '9'):
            roots = [set(target['variants'][cap]['roots'])
                     for target in (north, middle, south)]
            self.assertEqual(len({tuple(sorted(r)) for r in roots}), 3, cap)
            self.assertEqual(roots, [{'SPECIES_TENTACOOL'},
                                    {'SPECIES_STARYU' if cap == '4' else 'SPECIES_BRUXISH'},
                                    {'SPECIES_QWILFISH' if cap == '4' else 'SPECIES_WAILMER'}])

    def test_reassigned_seas_have_only_current_ordinary_families_in_habitats_and_dex(self):
        expected = {
            4: {'NORTH': {'SPECIES_TENTACOOL', 'SPECIES_TENTACRUEL'},
                'MIDDLE': {'SPECIES_STARYU', 'SPECIES_STARMIE'},
                'SOUTH': {'SPECIES_QWILFISH', 'SPECIES_QWILFISH_HISUI'}},
            9: {'NORTH': {'SPECIES_TENTACOOL', 'SPECIES_TENTACRUEL'},
                'MIDDLE': {'SPECIES_BRUXISH'},
                'SOUTH': {'SPECIES_WAILMER', 'SPECIES_WAILORD'}}}
        dex = re.findall(r'\{(SPECIES_\w+),(MAP_\w+),\d+,\d+,(\d+),(\d+)\}',
                         self.layer.outputs['src/data/journey_world_dex_locations.h'].decode())
        for cap, path in ((4, 'include/journey_generation4_habitats.h'),
                          (9, 'include/journey_habitat_data.h')):
            habitats = parse_habitats(self.layer.outputs[path].decode())
            for sea, members in expected[cap].items():
                ident = 'MAP_JOURNEYHOENN' + sea + 'SEA'
                self.assertEqual(habitats[ident], members, (cap, ident))
                declared = {species for species, mapping, fixed, generation in dex
                            if mapping == ident and fixed == '0' and generation == str(cap)}
                self.assertEqual(declared, members, (cap, ident))
                for habitat in self.report['locations_data'][cap]:
                    if any(family['root'] == 194 for family in habitat['families']):
                        self.assertNotIn(ident, habitat['maps'], (cap, ident))

    def test_coverage_counts_include_explicit_quiet_exceptions(self):
        self.assertEqual(len(self.report['targets']), 379)
        self.assertEqual(len(self.report['quiet_exceptions']), 55)
        self.assertEqual(len(self.target_ids), 379)
        self.assertTrue(self.target_ids.isdisjoint(
            {row['map_id'] for row in self.report['quiet_exceptions']}))

    def test_fixed_dex_locations_stay_and_terrain_atlas_campaign_are_not_staged(self):
        path = 'src/data/journey_world_dex_locations.h'
        rows = lambda text: set(re.findall(r'\{SPECIES_\w+,[^{}]+\}', text))
        before = rows((SOURCE/path).read_text())
        after = rows(self.layer.outputs[path].decode())
        removed = before - after
        self.assertEqual(removed, set(self.report['removed_stale_ordinary_dex_records']))
        self.assertEqual(len(removed), 13)
        for row in removed:
            species, mapping, x, y, fixed, cap = row[1:-1].split(',')
            self.assertEqual(fixed, '0', row)
            self.assertIn(mapping, self.report['reorganized_by_generation'][int(cap)], row)
        protected = {row for row in before if row.split(',')[-2] == '1'
                     or 'MAP_JOURNEYLAVENDERWORKSHOP,' in row}
        self.assertTrue(any('MAP_JOURNEYLAVENDERWORKSHOP,' in row for row in protected))
        self.assertFalse(protected - after)
        self.assertEqual(len(after - before), self.report['additional_dex_records'])
        for name, content in self.layer.outputs.items():
            self.assertNotIn('/layouts/', name)
            self.assertNotIn('/maps/', name)
            self.assertNotIn('region_map', name)
            self.assertEqual(hashlib.sha256((SOURCE/name).read_bytes()).hexdigest(),
                             self.layer.expected[name], name)


if __name__ == '__main__':
    unittest.main()
