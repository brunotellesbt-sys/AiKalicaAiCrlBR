"""Reject relabelled trips, gameplay writes and rehashed wrong species pixels."""
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from PIL import Image

from verify_legendary_chambers_native import verify

ROOT=Path(__file__).resolve().parents[2]
PROOF=ROOT/'docs/design/legendary-chambers-review/prototype-v8a'


class NativeIndividualRoomEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frozen=json.loads(gzip.decompress((PROOF/'compiled-freeze.json.gz').read_bytes()))
        cls.rooms=json.loads(gzip.decompress((PROOF/'rooms.json.gz').read_bytes()))['rooms']

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='native-individual-room-proof-')
        self.addCleanup(self.temp.cleanup)
        self.folder=Path(self.temp.name)/'native'
        shutil.copytree(PROOF/'native',self.folder)

    def change_component(self,change):
        p=self.folder/'legendary-chambers-native-matrix.json'
        matrix=json.loads(p.read_bytes());row=matrix['components'][0]
        component=self.folder/row['report'];report=json.loads(component.read_bytes())
        change(report,component.parent)
        component.write_text(json.dumps(report))
        row['sha256']=hashlib.sha256(component.read_bytes()).hexdigest()
        p.write_text(json.dumps(matrix))

    def test_all105_actual_native_trips_and_210_PNGs_pass(self):
        result=verify(self.frozen,self.folder,self.rooms)
        self.assertEqual((result['rooms'],result['captures']),(105,210))
        self.assertEqual(result['visible_native_species_pixels'],48600)
        self.assertFalse(result['final_release_validated'])

    def test_another_ROM_cannot_reuse_these_current_trip_proofs(self):
        frozen=dict(self.frozen,rom_sha256='0'*64)
        with self.assertRaisesRegex(ValueError,'stale ROM'):
            verify(frozen,self.folder,self.rooms)

    def test_integrated_large_caves_ROM_has_its_own_105_fresh_native_trips(self):
        current=PROOF.parent/'large-caves-v8'
        frozen=json.loads(gzip.decompress((current/'compiled-freeze.json.gz').read_bytes()))
        rooms=json.loads(gzip.decompress((current/'rooms.json.gz').read_bytes()))['rooms']
        self.assertNotEqual(frozen['rom_sha256'],self.frozen['rom_sha256'])
        result=verify(frozen,current/'native',rooms)
        self.assertEqual((result['rooms'],result['captures']),(105,210))

    def test_one_missing_chamber_is_rejected_even_with_updated_component_hash(self):
        self.change_component(lambda report,root:report['cases'].pop())
        with self.assertRaisesRegex(ValueError,'every one of the 105'):
            verify(self.frozen,self.folder,self.rooms)

    def test_a_return_to_another_hatch_in_the_same_parent_is_rejected(self):
        self.change_component(lambda report,root:report['cases'][0]['returned'].update(tile=[0,0]))
        with self.assertRaisesRegex(ValueError,'different entrance'):
            verify(self.frozen,self.folder,self.rooms)

    def test_rehashed_wrong_PNG_pixel_cannot_replace_the_species_body(self):
        def wrong_pixel(report,root):
            case=report['cases'][0];capture=case['species_capture'];path=root/capture['file']
            with Image.open(path) as original:image=original.convert('RGB')
            x,y,*rgb=case['species_pixels']['expected_scanout_pixels'][0]
            image.putpixel((x,y),tuple(255-c for c in rgb));image.save(path)
            capture['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        self.change_component(wrong_pixel)
        with self.assertRaisesRegex(ValueError,'PNG pixels'):
            verify(self.frozen,self.folder,self.rooms)

    def test_gameplay_write_cannot_be_disguised_as_a_native_query(self):
        self.change_component(lambda report,root:report['queries'].append(dict(function='VarSet',args=[0x40DC,8])))
        with self.assertRaisesRegex(ValueError,'Gameplay mutation'):
            verify(self.frozen,self.folder,self.rooms)

    def test_component_path_cannot_escape_the_native_proof_folder(self):
        path=self.folder/'legendary-chambers-native-matrix.json'
        matrix=json.loads(path.read_bytes());matrix['components'][0]['report']='../foreign.json'
        path.write_text(json.dumps(matrix))
        with self.assertRaisesRegex(ValueError,'escapes'):
            verify(self.frozen,self.folder,self.rooms)
