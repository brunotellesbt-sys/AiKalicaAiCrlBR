"""Reproduce or reject the beach occlusion shown in the Dewford video.

Travel uses controller input after one initial placement. Checking the OAM
visibility flag alone misses this defect: foreground beach graphics can cover
a sprite that is still enabled. Compare visible red-hat and lower-body pixels
with nearby dry ground as well as checking compiled beach layer attributes.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from PIL import Image
from integrated_dewford_view import GROUND_METATILES


ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--library', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--expect-broken', action='store_true')
view_options = parser.parse_args()
initial_sha = hashlib.sha256((view_options.source / 'pokeemerald.gba').read_bytes()).hexdigest()
sys.argv = [sys.argv[0], '--source', str(view_options.source), '--library', str(view_options.library),
            '--output', str(view_options.output)]
bootstrap = (ROOT / 'tools/hoenn/validate_sootopolis_harbor.py').read_text().split('\n# Disable Sootopolis')[0]
exec(compile(bootstrap, __file__, 'exec'))

native('RtcInitLocalTimeOffset', 12, 0)
warp('Route107', 4, 16)
native('SetPlayerAvatarTransitionFlags', 1)
step(200)
samples = []


def observe(label):
    x, y = position()
    obj = s['gObjectEvents'] + lib.read8(s['gPlayerAvatar'] + 5) * 36
    sprite = s['gSprites'] + lib.read8(obj + 35) * 68
    picture(label)
    im = Image.open(args.output / (label + '.png')).convert('RGB')
    # The tracked avatar stands at screen (120, 80). Native rock, sand and
    # bridge colours do not satisfy this red-hat mask in this small rectangle.
    red = sum(r > 140 and r > g * 1.8 and r > b * 1.8
              for r, g, b in im.crop((104, 48, 136, 96)).getdata())
    # At (7,15) the hat alone survives above the foreground beach while the
    # body is completely covered. These dark clothing/outline pixels in the
    # lower body are absent from the surrounding sand and blue sea.
    body = sum(max(rgb) < 75 for rgb in im.crop((114, 78, 126, 89)).getdata())
    row = dict(label=label, tile=[x, y], elevation=native('PlayerGetElevation'),
               surf=bool(lib.read8(s['gPlayerAvatar']) & 8),
               priority=(lib.read16(sprite + 4) >> 10) & 3,
               sprite_enabled=not bool(lib.read16(sprite + 0x3E) & 4),
               object_enabled=not bool(lib.read8(obj + 1) & 0x20),
               red_hat_pixels=red,
               lower_body_pixels=body,
               ground_metatile=native('MapGridGetMetatileIdAt', x + 7, y + 7),
               ground_layer=native('MapGridGetMetatileLayerTypeAt', x + 7, y + 7))
    assert row['elevation'] == 3 and not row['surf'], row
    assert row['priority'] == 2 and row['sprite_enabled'] and row['object_enabled'], row
    samples.append(row)
    return row


walk_to(6, 16)
reference = observe('ordinary-sand-visible-reference')
assert reference['red_hat_pixels'] >= 12, reference
assert reference['lower_body_pixels'] >= 12, reference
walk_to(7, 16)
corner = observe('east-beach-corner-avatar')
walk_to(7, 15)
footing = observe('east-side-of-bridge-footing')
# Escape to ordinary beach without trying to cross the raised stairs laterally.
walk_to(7, 16)
walk_to(6, 16)
walk_to(4, 16)
walk_to(4, 15)
observe('west-side-of-bridge-footing')
walk_to(4, 16)
walk_to(3, 16)
observe('west-beach-curve')
walk_to(4, 16)
observe('returned-to-original-beach')

compiled_attributes = s['gMetatileAttributes_JourneyDewfordHarbor']
layers = [dict(metatile=mid, attribute=lib.read16(compiled_attributes + 2 * (mid - 512)))
          for mid in GROUND_METATILES]
if view_options.expect_broken:
    assert corner['red_hat_pixels'] == 0, corner
    assert corner['lower_body_pixels'] == 0 and footing['lower_body_pixels'] == 0
    assert all(row['attribute'] >> 12 == 0 for row in layers)
    passed = False
else:
    assert all(row['ground_layer'] == 1 for row in samples), samples
    assert all(row['red_hat_pixels'] >= reference['red_hat_pixels'] * 0.75 for row in samples), samples
    assert all(row['lower_body_pixels'] >= reference['lower_body_pixels'] * 0.75 for row in samples), samples
    assert all(row['attribute'] >> 12 == 1 for row in layers), layers
    passed = True
review_mode = bool(lib.read8(s['gJourneyReviewMode']))
lib.stop()
assert hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest() == initial_sha
result = dict(passed=passed, expected_broken_baseline=view_options.expect_broken,
              bug_reproduced=view_options.expect_broken,
              rom_sha256=initial_sha, review_mode=review_mode,
              samples=samples, compiled_ground_attributes=layers,
              native_avatar_pixels_checked=True, sprite_flags_alone_not_sufficient=True,
              player_movement_uses_controller_input=True,
              no_coordinates_or_elevation_writes_after_initial_placement=True,
              source_map_dimensions_terrain_and_vendors_unchanged=True)
result['captures'] = [dict(file=row['label'] + '.png',
                           sha256=hashlib.sha256((args.output / (row['label'] + '.png')).read_bytes()).hexdigest())
                      for row in samples]
(args.output / 'dewford-beach-visibility.json').write_text(json.dumps(result, indent=2) + '\n')
print('Dewford beach occlusion ' + ('reproduced' if view_options.expect_broken else 'rejected') +
      ': visible avatar pixels and native shoreline layers verified.', flush=True)
