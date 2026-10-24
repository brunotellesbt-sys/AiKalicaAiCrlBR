"""Native body scale, feet and directional frames must agree with the rivals."""
from io import BytesIO
import json
import unittest

from PIL import Image, ImageOps
from badge_story_sprites import ASSETS, ORDERS, normalize_frames, verify_asset, sha


class BadgeStorySprites(unittest.TestCase):
    def test_all_eighteen_frames_are_complete_and_share_native_rival_scale(self):
        manifest = json.loads((ASSETS / 'sources.json').read_text())
        reference_heights = []
        for name, row in manifest['rival_references'].items():
            raw = (ASSETS / (name + '-reference.png')).read_bytes()
            self.assertEqual(sha(raw), row['sha256'])
            image = Image.open(BytesIO(raw))
            for index in range(3):
                columns = image.width // 16
                x, y = (index % columns) * 16, (index // columns) * 32
                box = image.crop((x, y, x + 16, y + 32)).getbbox()
                reference_heights.append(box[3] - box[1])
        self.assertEqual((min(reference_heights), max(reference_heights)), (19, 21))
        for name in ORDERS:
            original = (ASSETS / (name + '-original.png')).read_bytes()
            normalized = (ASSETS / (name + '-normalized.png')).read_bytes()
            records = verify_asset(original, normalized, name)
            self.assertEqual(len(records), 9)
            self.assertTrue(all(r['height'] == 20 and r['width'] == 14 for r in records))

    def test_eren_side_idle_and_step_face_same_direction_before_native_mirroring(self):
        image = Image.open(ASSETS / 'eren-original.png')
        result = normalize_frames((ASSETS / 'eren-original.png').read_bytes(), 'eren')
        side = image.crop((0, 7 * 32, 16, 8 * 32))
        side = side.crop(side.getbbox()).resize((14, 20), Image.Resampling.NEAREST)
        self.assertEqual(result.crop((1, 2 * 32 + 11, 15, 2 * 32 + 31)).tobytes(), side.tobytes())
        step = image.crop((0, 8 * 32, 16, 9 * 32))
        step = ImageOps.mirror(step.crop(step.getbbox())).resize((14, 20), Image.Resampling.NEAREST)
        self.assertEqual(result.crop((1, 8 * 32 + 12, 15, 9 * 32)).tobytes(), step.tobytes())

    def test_clipped_feet_and_changed_palette_are_rejected(self):
        raw = (ASSETS / 'luffy-original.png').read_bytes()
        original = Image.open(ASSETS / 'luffy-normalized.png')
        for corruption in ('feet', 'palette'):
            image = original.copy()
            if corruption == 'feet':
                for x in range(16):
                    image.putpixel((x, 30), 0)
            else:
                palette = image.getpalette()
                palette[3] ^= 8
                image.putpalette(palette)
            output = BytesIO()
            image.save(output, format='PNG', transparency=0)
            with self.assertRaises(AssertionError):
                verify_asset(raw, output.getvalue(), 'luffy')


if __name__ == '__main__':
    unittest.main()
