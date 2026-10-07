"""Release/catalog regression and compiled sea graph integrity."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/regions'))
import test_regions
sys.path.insert(0, str(ROOT / 'tools/rom_hacks'))
from remove_hm_walls import Maps

class SeaReleaseTests(test_regions.RegionsTests):
    output = ROOT / 'mods/sea-routes'
    rom_name = 'LeafGreen-Journey-SeaRoutes'

    def test_recorded_emulator_validation_matches_release(self):
        report = json.loads((self.output / 'validation/results.json').read_text())
        self.assertEqual(report['rom_sha256'], self.manifest['target_sha256'])
        self.assertEqual(len(report['checks']), 21)
        self.assertTrue(all(r['passed'] for r in report['checks']))
        browser = json.loads((self.output / 'validation/browser.json').read_text())
        self.assertTrue(browser['passed']); self.assertEqual(browser['page_errors'], [])

    def test_greninja_normal_and_hidden_ability_slots(self):
        byname = {r['species']: r for r in self.catalog['catalog']}
        slots = [self.abi['ability_torrent'], self.abi['ability_protean'], self.abi['ability_battle_bond']]
        for name in ['SPECIES_FROAKIE', 'SPECIES_FROGADIER', 'SPECIES_GRENINJA', 'SPECIES_GRENINJA_ASH']:
            p = self.offset(byname[name]) + self.abi['species_abilities']
            self.assertEqual(list(struct.unpack_from('<3H', self.rom, p)), slots if name != 'SPECIES_GRENINJA_ASH' else [slots[2]] * 3)

    def test_compiled_sea_connections_and_water_elevations(self):
        ref = json.loads((self.output / 'debug-reference.json').read_text())
        maps = Maps(self.rom, ref)
        headers = {n: (g, k, h) for n, g, k, h in maps.headers()}
        routes = json.loads((self.output / 'routes.json').read_text())['routes']
        for i, route in enumerate(routes):
            _, _, header = headers[route['name']]
            layout = maps.ptr(header)
            self.assertEqual((maps.u32(layout), maps.u32(layout + 4)), (48, 24))
            blocks = maps.ptr(layout + 12)
            self.assertEqual(set(struct.unpack_from('<1152H', self.rom, blocks)), {0x11D9})
            conn = maps.ptr(header + 12)
            self.assertEqual(maps.u32(conn), len(route['connections']))
            rows = maps.ptr(conn + 4)
            for j, connection in enumerate(route['connections']):
                p = rows + 12 * j
                expected_name = route['port'] if connection['direction'] == 'up' else routes[i + (-1 if connection['direction'] == 'left' else 1)]['name']
                group, number, _ = headers[expected_name]
                self.assertEqual(maps.u32(p), {'up': 2, 'left': 3, 'right': 4}[connection['direction']])
                self.assertEqual(struct.unpack_from('<i', self.rom, p + 4)[0], connection['offset'])
                self.assertEqual(tuple(self.rom[p + 8:p + 10]), (group, number))

    def test_port_npcs_and_warps_preserved(self):
        ref = json.loads((self.output / 'debug-reference.json').read_text())
        new = Maps(self.rom, ref)
        old_dir = ROOT / 'mods/all-regions'
        old = Maps((old_dir / 'LeafGreen-Journey-AllRegions.gba').read_bytes(), json.loads((old_dir / 'debug-reference.json').read_text()))
        new_headers = {n: h for n, _, _, h in new.headers()}
        old_headers = {n: h for n, _, _, h in old.headers()}
        for route in json.loads((self.output / 'routes.json').read_text())['routes']:
            name = route['port']; ne = new.ptr(new_headers[name] + 4); oe = old.ptr(old_headers[name] + 4)
            self.assertEqual(self.rom[ne:ne + 4], old.rom[oe:oe + 4])
            count = self.rom[ne]
            np = new.ptr(ne + 4); op = old.ptr(oe + 4)
            for i in range(count):
                # Event script addresses relocate, all NPC fields stay equal.
                n = self.rom[np + i * 24:np + (i + 1) * 24]
                o = old.rom[op + i * 24:op + (i + 1) * 24]
                self.assertEqual(n[:16] + n[20:], o[:16] + o[20:], name)
            count = self.rom[ne + 1]
            np = new.ptr(ne + 8); op = old.ptr(oe + 8)
            self.assertEqual(self.rom[np:np + count * 8], old.rom[op:op + count * 8], name)

if __name__ == '__main__': unittest.main()
