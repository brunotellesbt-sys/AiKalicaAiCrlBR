"""Protect inventory coverage from overwritten layers and false tile deltas."""
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest

from audit_generated_world_inventory import collapse, terrain_delta


class GeneratedInventory(unittest.TestCase):
    def test_later_restoration_is_not_reported_as_a_final_edit(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            original = hashlib.sha256(b'original').hexdigest()
            changed = hashlib.sha256(b'changed').hexdigest()
            (root/'.source-acquired.json').write_text(json.dumps(dict(sha256={'old.txt':original})))
            (root/'.journey-first').write_text(json.dumps(dict(prepared_sha256={'old.txt':changed, 'new.txt':changed})))
            (root/'.journey-second').write_text(json.dumps(dict(prepared_sha256={'old.txt':original})))
            (root/'old.txt').write_bytes(b'original')
            (root/'new.txt').write_bytes(b'changed')
            _, _, edits, owners, restored = collapse(root, ['first','second'])
            self.assertEqual(edits, {'new.txt':changed})
            self.assertEqual(restored, ['old.txt'])
            self.assertEqual(owners['old.txt'], ['first','second'])

    def test_actual_source_tampering_is_not_hidden_by_the_marker(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/'.source-acquired.json').write_text(json.dumps(dict(sha256={})))
            (root/'.journey-new').write_text(json.dumps(dict(prepared_sha256={'new.txt':hashlib.sha256(b'expected').hexdigest()})))
            (root/'new.txt').write_bytes(b'different')
            with self.assertRaisesRegex(AssertionError, 'Prepared source differs'):
                collapse(root, ['new'])

    def test_terrain_coordinates_include_height_and_collision_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);old=base/'old';new=base/'new';old.mkdir();new.mkdir()
            original=[0x3001]*12
            current=original.copy();current[2]=0x1001;current[10]=0x3401
            (old/'map.bin').write_bytes(struct.pack('<12H',*original))
            (new/'map.bin').write_bytes(struct.pack('<12H',*current))
            layout=dict(blockdata_filepath='map.bin',width=4,height=3)
            result=terrain_delta(new,old,layout,layout,{'map.bin'})
            self.assertEqual(result['changed_cells'],2)
            self.assertEqual(result['changed_bounds'],[2,0,2,2])


if __name__=='__main__':
    unittest.main()
