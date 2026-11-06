"""Exercise fail-closed source-proof checks without rebuilding a ROM."""
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import sevii_route_boundaries_contract as contract
from prepare_sevii_route_boundaries import PRIOR
from verify_sevii_route_boundaries_source import verify_report


class SeviiBoundarySourceProof(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='sevii-source-proof-', dir='/tmp')
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.prepared = {'src/fieldmap.c': 'a'*64, 'data/layouts/layouts.json': 'b'*64}
        self.pin = patch.object(contract, 'PREPARED_SHA256', self.prepared)
        self.pin.start()
        self.addCleanup(self.pin.stop)
        self.romsha = 'c'*64

    def report(self):
        names = ['Sea'+str(index) for index in range(284)]
        layouts = []
        for index, name in enumerate(names):
            layouts.append(dict(map=name, layout=name+'_Layout', symbol='g'+name,
                address=0x08001000+index*32, width=24, height=40,
                primary_pointer=0x08010000, secondary_pointer=0x08010040,
                is_frlg=True, border_width=2, border_height=2, stored_border_width=2,stored_border_height=2,
                compiled_layout_bytes_match=True,
                blockdata=dict(file='data/layouts/'+name+'/map.bin', bytes=1920,
                    sha256='d'*64, address=0x08100000+index*2048),
                borderdata=dict(file='data/layouts/'+name+'/border.bin', bytes=8,
                    sha256='e'*64, address=0x08200000+index*8)))
        exports = ['MapGridGetMetatileIdAt', 'NewGameInitData', 'CopyPartyAndObjectsFromSave']
        return dict(kind='sevii-route-boundaries-source', passed=True, preflight=False,
            compiled_rom=True, independent_replay=True, prefix_markers_unchanged=True,
            unrelated_source_files_unchanged=True, scripts_and_atlas_art_unchanged=True,
            layers=PRIOR+[contract.SCOPE], parent_rom_sha256=contract.PARENT_ROM_SHA256,
            prepared_sha256=copy.deepcopy(self.prepared), changed_files=sorted(self.prepared),
            rom_sha256=self.romsha, elf_sha256='f'*64,
            source_hashes_checked=32000, elf_rom_load_segments_checked=3,
            boundary_audit=dict(maps=284, map_names=names, unconnected_water_edges=0,
                connected_openings_preserved=True, complete_small_reefs=True),
            geography=dict(old_dimensions=[24,40], dimensions=[40,48],
                old_cells_preserved=960, offset=[8,0], objects_and_warps_preserved=True,
                geology_preserved=True),
            projection=dict(dimensions=[40,48], old_logical_pixels_preserved=960,
                other_logical_grids_preserved=True, shared_border_maximum_step=2,
                closed_loop_neighbor_maximum_step=2),
            compiled_gps=dict(symbol='sWorldNavigationPixels', address=0x08300000,
                bytes=40*48*2, sha256='2'*64), compiled_layouts=layouts,
            runtime_export_names=exports, compiled_runtime=[dict(symbol=name,
                address=0x08020000+index*32, bytes=16, sha256='1'*64)
                for index,name in enumerate(exports)],
            camera_limitations=dict(full_world_camera_certified=False,
                ambiguous_graph_cells=0, ambiguous_graph_maps=[]))

    def verify(self, report):
        return verify_report(report, self.root, self.romsha)

    def rejects(self, change):
        report = self.report()
        change(report)
        with self.assertRaises((AssertionError, KeyError)):
            self.verify(report)

    def test_complete_pinned_compiled_report_passes(self):
        report = self.report()
        self.assertIs(self.verify(report), report)

    def test_unpinned_contract_and_preflight_cannot_certify_source(self):
        with patch.object(contract, 'PREPARED_SHA256', {}):
            with self.assertRaisesRegex(AssertionError, 'not pinned'):
                self.verify(self.report())
        for key in ('passed', 'compiled_rom', 'independent_replay', 'prefix_markers_unchanged',
                    'unrelated_source_files_unchanged', 'scripts_and_atlas_art_unchanged'):
            with self.subTest(key=key):
                self.rejects(lambda r, key=key: r.update({key: False}))
        self.rejects(lambda r: r.update(preflight=True))

    def test_stale_identity_and_changed_source_scope_are_rejected(self):
        for key, value in (('rom_sha256', contract.PARENT_ROM_SHA256),
                           ('elf_sha256', contract.PARENT_ELF_SHA256),
                           ('parent_rom_sha256', '0'*64), ('elf_sha256', 'z'*64)):
            with self.subTest(key=key):
                self.rejects(lambda r, key=key, value=value: r.update({key:value}))
        self.rejects(lambda r: r['layers'].pop())
        self.rejects(lambda r: r['prepared_sha256'].update({'src/fieldmap.c':'0'*64}))
        self.rejects(lambda r: r['changed_files'].append('src/unrelated.c'))
        self.rejects(lambda r: r['changed_files'].reverse())
        self.rejects(lambda r: r.update(source_hashes_checked=0))
        self.rejects(lambda r: r.update(elf_rom_load_segments_checked=0))

    def test_boundary_holes_and_closed_existing_connections_are_rejected(self):
        self.rejects(lambda r: r['boundary_audit'].update(unconnected_water_edges=1))
        self.rejects(lambda r: r['boundary_audit'].update(connected_openings_preserved=False))
        self.rejects(lambda r: r['boundary_audit'].update(complete_small_reefs=False))
        self.rejects(lambda r: r['boundary_audit']['map_names'].pop())
        self.rejects(lambda r: r['boundary_audit']['map_names'].__setitem__(0, 'Sea1'))

    def test_geography_and_projection_regressions_are_rejected(self):
        self.rejects(lambda r: r['geography'].update(old_cells_preserved=959))
        self.rejects(lambda r: r['geography'].update(offset=[0,0]))
        self.rejects(lambda r: r['geography'].update(geology_preserved=False))
        self.rejects(lambda r: r['projection'].update(shared_border_maximum_step=3))
        self.rejects(lambda r: r['projection'].update(closed_loop_neighbor_maximum_step=-1))
        self.rejects(lambda r: r['projection'].update(old_logical_pixels_preserved=959))

    def test_missing_or_unbound_compiled_gps_is_rejected(self):
        self.rejects(lambda r: r.pop('compiled_gps'))
        self.rejects(lambda r: r['compiled_gps'].update(symbol='OtherProjection'))
        self.rejects(lambda r: r['compiled_gps'].update(bytes=0))
        self.rejects(lambda r: r['compiled_gps'].update(bytes=3841))
        self.rejects(lambda r: r['compiled_gps'].update(address=0x02000000))
        self.rejects(lambda r: r['compiled_gps'].update(sha256='invalid'))

    def test_missing_misbound_or_incomplete_compiled_layouts_are_rejected(self):
        self.rejects(lambda r: r['compiled_layouts'].pop())
        self.rejects(lambda r: r['compiled_layouts'][0].update(map='UnreviewedSea'))
        self.rejects(lambda r: r['compiled_layouts'][0].update(compiled_layout_bytes_match=False))
        self.rejects(lambda r: r['compiled_layouts'][0]['blockdata'].update(bytes=1918))
        self.rejects(lambda r: r['compiled_layouts'][0]['borderdata'].update(bytes=6))
        self.rejects(lambda r: r['compiled_layouts'][0].update(primary_pointer=0x02000000))
        self.rejects(lambda r: r['compiled_layouts'][0]['blockdata'].update(address=0x09FFFFFF))
        self.rejects(lambda r: r['compiled_layouts'][0]['blockdata'].update(file='../map.bin'))

    def test_missing_runtime_exports_or_empty_code_are_rejected(self):
        self.rejects(lambda r: r['compiled_runtime'].pop())
        self.rejects(lambda r: r['compiled_runtime'][0].update(symbol='OtherFunction'))
        self.rejects(lambda r: r['compiled_runtime'][0].update(bytes=0))
        self.rejects(lambda r: r['runtime_export_names'].__setitem__(0,'OtherFunction'))
        self.rejects(lambda r: r.update(runtime_export_names=r['runtime_export_names'][:2],
                                        compiled_runtime=r['compiled_runtime'][:2]))

    def test_camera_limitations_cannot_be_silently_promoted_to_world_certification(self):
        self.rejects(lambda r: r['camera_limitations'].update(full_world_camera_certified=True))
        self.rejects(lambda r: r['camera_limitations'].update(ambiguous_graph_cells=-1))
        self.rejects(lambda r: r['camera_limitations'].update(ambiguous_graph_cells=1))

    def test_optional_attachments_are_content_bound_and_confined_to_report_folder(self):
        file = self.root/'proof.txt'
        file.write_bytes(b'actual source observation')
        report = self.report()
        report['captures'] = [dict(file='proof.txt', sha256=hashlib.sha256(file.read_bytes()).hexdigest())]
        self.verify(report)
        file.write_bytes(b'changed observation')
        with self.assertRaisesRegex(AssertionError, 'changed'):
            self.verify(report)
        for name in ('../proof.txt', str(file), 'dir\\proof.txt'):
            with self.subTest(name=name):
                self.rejects(lambda r, name=name: r.update(captures=[dict(file=name,sha256='0'*64)]))
        with tempfile.TemporaryDirectory(prefix='sevii-outside-', dir='/tmp') as outside:
            external = Path(outside)/'proof.txt'
            external.write_bytes(b'external')
            (self.root/'escape').symlink_to(external)
            self.rejects(lambda r: r.update(captures=[dict(file='escape',
                sha256=hashlib.sha256(b'external').hexdigest())]))


if __name__ == '__main__':
    unittest.main()
