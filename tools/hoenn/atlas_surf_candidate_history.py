"""Replay and authenticate the terrain actually shipped in candidate533.

The earlier geometry report pins IDs/rectangles but predates cave/Dive edits.
Use the published compiled freeze for terrain, never that report's tile hashes.
Replay is in memory against the immutable171; it does not need Git history.
"""
import gzip
import hashlib
import json
from pathlib import Path

from atlas_surf_candidate_ids import load_history
from atlas_surf_overlay import OverlaySource

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = 'tools/hoenn/fixtures/atlas-candidate533-preparer.py.txt'
FIXTURE_SHA = 'b8bdb774866fbf92cd3515407dfc3a304939a145cce468d2a2bd357f01586f34'
FREEZE = 'docs/design/atlas-surf-layout/candidate-compiled-freeze.json.gz'
FREEZE_SHA = '04ddaea48ce0f2e71af200c8a56c24225333bf1f238342e1c5043e3d18300720'


def load_terrain(parent):
    code = (ROOT/FIXTURE).read_bytes()
    raw = (ROOT/FREEZE).read_bytes()
    if hashlib.sha256(code).hexdigest() != FIXTURE_SHA or hashlib.sha256(raw).hexdigest() != FREEZE_SHA:
        raise ValueError('Published candidate terrain replay fixture/freeze changed')
    freeze = json.loads(gzip.decompress(raw))
    namespace = dict(__name__='candidate533_terrain_replay',
                     __file__=str(ROOT/'tools/hoenn/prepare_atlas_surf_layout.py'))
    exec(compile(code, FIXTURE, 'exec'), namespace)
    fringe = namespace['preserve_native_water_collars']
    namespace['preserve_native_water_collars'] = lambda *args, **kwargs: fringe(
        *args, **dict(kwargs, cave_radius=3))
    layer, metadata = namespace['compose'](parent)
    keys = [p for p in freeze['prepared_sha256'] if p.startswith(('data/maps/', 'data/layouts/'))]
    if len(keys) != 1932:
        raise ValueError('Incomplete published candidate terrain inventory')
    for path in keys:
        if hashlib.sha256(layer.outputs[path]).hexdigest() != freeze['prepared_sha256'][path]:
            raise ValueError(('Replayed terrain differs from published candidate533', path))
    history = load_history()
    signature = lambda p: {r['name']: (r['group_index'], r['number'], r['origin'], r['width'], r['height'])
                           for r in p['chunks']}
    if signature(metadata['geometry_plan']) != signature(history['geometry_plan']):
        raise ValueError('Replayed candidate identities/rectangles changed')
    view = OverlaySource(layer)
    view.assert_unchanged()
    proof = dict(kind='published-candidate533-terrain-replay', fixture_sha256=FIXTURE_SHA,
                 compiled_freeze_sha256=FREEZE_SHA, original_ROM_sha256=freeze['rom_sha256'],
                 terrain_files_checked=len(keys), geometry_compiled_rows_checked=533,
                 original_source_unmodified=True, replay_is_not_native_ROM_evidence=True)
    return view, metadata['geometry_plan'], proof
