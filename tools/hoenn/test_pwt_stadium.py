"""Check authored walking assets can be packed into legal GBA graphics."""
import hashlib,json,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parent/'data/pwt/generated'
class StadiumAssets(unittest.TestCase):
    def test_all_79_characters_have_nine_indexed_frames_and_source_provenance(self):
        records=json.loads((ROOT/'sources.json').read_text())['records']
        self.assertEqual(len({r['key'] for r in records}),79)
        for row in records:
            image=Image.open(ROOT/row['file'])
            self.assertEqual(image.mode,'P');self.assertEqual(image.size,(32,288))
            self.assertEqual(image.info['transparency'],0)
            self.assertLessEqual(max(image.getdata()),15)
            self.assertEqual(hashlib.sha256((ROOT/row['file']).read_bytes()).hexdigest(),row['converted_sha256'])
            self.assertEqual(hashlib.sha256((ROOT/row['source_sheet']).read_bytes()).hexdigest(),row['source_sha256'])
            self.assertTrue((ROOT/row['source_reference']).is_file())
            self.assertEqual(len(row['source_boxes']),9)
            for frame in range(9):
                self.assertTrue(any(image.crop((0,frame*32,32,(frame+1)*32)).getdata()))
    def test_authored_stadium_has_native_aspect_ratio(self):
        image=Image.open(ROOT/'arena-source.png')
        self.assertEqual(image.width,2*image.height)
        image.close()
if __name__=='__main__':unittest.main()
