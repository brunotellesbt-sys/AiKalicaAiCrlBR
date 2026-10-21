"""Check compiled and live Sevii ocean art across every affected surface seam.

Each seam gets one initial position and avatar-mode fixture. Both crossings
then use controller input. The check reads the loaded tiles, palettes and
metatile tables; changing a map header or passing a route alone is insufficient.
"""
import hashlib
import json
from pathlib import Path
import re

from integrated_ocean_seams import validate_compiled, validate_loaded


ROOT = Path(__file__).resolve().parents[2]
bootstrap = (ROOT / 'tools/hoenn/validate_trainer_levels.py').read_text().split('\nchecks=[]')[0]
exec(compile(bootstrap, __file__, 'exec'))
initial_sha = hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest()
integration = json.loads((source / '.journey-sevii-integrated-piers').read_text())
metadata = integration['ocean_seams']
assert metadata['native_body_words_unchanged']
assert metadata['all_attributes_unchanged']
assert metadata['all_blockdata_and_map_events_unchanged']
assert metadata['canonical_words'] == [16838, 16839, 16839, 16838]
targets = set(metadata['target_maps'])
assert len(targets) == 18, len(targets)
all_maps = {path.parent.name: json.loads(path.read_text())
            for path in (source / 'data/maps').glob('*/map.json')}
all_by_id = {value['id']: name for name, value in all_maps.items()}
coast_source = (source / 'src/journey_sevii_surf.c').read_text()
coast_function = re.search(r'static bool32 IsConnectedSeviiCoast\([^)]*\)\s*\{(.*?)\n\}',
                           coast_source, re.S)[1]
open_coast_ids = set(re.findall(r'case\s*\(MAP_GROUP\((MAP_\w+)\)', coast_function))
assert open_coast_ids and open_coast_ids <= set(all_by_id), open_coast_ids - set(all_by_id)
open_coast_maps = {all_by_id[value] for value in open_coast_ids}

# Derive the full scope independently from the actual map headers. This also
# includes the unchanged outer bank at each end of the private-bank halo.
pairs = {}
for name in sorted(targets):
    for connection in all_maps[name].get('connections') or []:
        if connection['direction'] not in ['left', 'right', 'up', 'down']:
            continue
        other = all_by_id[connection['map']]
        pair = tuple(sorted((name, other)))
        pairs.setdefault(pair, (name, other, connection))
recorded_pairs = {tuple(sorted(row['maps'])) for row in metadata['surface_seams']}
assert set(pairs) == recorded_pairs, (sorted(set(pairs) - recorded_pairs),
                                     sorted(recorded_pairs - set(pairs)))
assert len(pairs) == metadata['expected_surface_seams'] == 26, len(pairs)
names = sorted({name for pair in pairs for name in pair} | targets)
allowed = set()
walk_prefix = 'integrated-ocean'
walk_transition_pictures = False
walk_cache_paths = True
walk_max_ticks = 1200
walk_surf_under_bridges = True
native('RtcInitLocalTimeOffset', 12, 0)
native('VarSet', 0x40FE, 7)
native('VarSet', 0x40FF, 4095)
native('VarSet', 0x4021, 65535)
native('VarSet', 0x4120, 65535)
team([40, 40, 40])
native('ScriptSetMonMoveSlot', 0, 57, 1)
for value in hoenn_flags + kanto_flags:
    rawflag(value, True)
for trainer_id in range(1, 1589):
    rawflag(0x500 + trainer_id, True)
constants = (source / 'include/constants/vars.h').read_text()
for variable, value in [('VAR_MAP_SCENE_ONE_ISLAND_HARBOR', 3),
                         ('VAR_MAP_SCENE_FOUR_ISLAND', 1)]:
    native('VarSet', int(re.search(r'^#define\s+' + variable + r'\s+(0x\w+)',
                                 constants, re.M)[1], 16), value)

# MB_FAST_WATER's Surf predicate is deliberately conditional on the native
# Sevii coast. Build the walker's behavior cache while such a coast is loaded.
# This is a fixture before any measured crossing, never a route shortcut.
warp('SixIsland_Frlg', 11, 22)
native('SetPlayerAvatarTransitionFlags', 1)
step(90)
compiled = validate_compiled(lib, s, source, metadata)
exec(compile((ROOT / 'tools/hoenn/native_water_walk.py').read_text(),
             'integrated-ocean-native-walker', 'exec'))
full_passable = {name: valid.copy() for name, valid in passable.items()}
# A door or arrow event cannot substitute for one of the physical connections.
warps = {name: {} for name in names}
captures = []
loaded_checks = []
checks = []


def ocean_palette():
    return [lib.read16(0x05000000 + 2 * (64 + index)) for index in [3, 4, 5, 7]]


def capture(label):
    picture(label)
    path = args.output / (label + '.png')
    row = dict(file=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    captures.append(row)
    return row


def passable_cell(name, x, y, surfing):
    width, height, values = blocks[name]
    if not (0 <= x < width and 0 <= y < height):
        return False
    index = y * width + x
    if index not in full_passable[name] or values[index] & 0xC00:
        return False
    behavior = behaviors[name][index]
    # MB_FAST_WATER is Surf water only on the exact native coast whitelist.
    # Cape Brink and any other unlisted native route retain fast-water rules;
    # the walker's global behavior cache must not broaden that whitelist.
    if behavior == 0x2C:
        if name not in open_coast_maps:
            return False
        wet = True
    else:
        wet = water_behaviors[behavior]
    if wet != surfing or currents[behavior] is not None:
        return False
    elevation = values[index] >> 12
    return elevation in [0, 1, 15] if surfing else elevation in [0, 3, 15]


def crossing_choices(name, other, connection, surfing):
    width, height, _ = blocks[name]
    other_width, other_height, _ = blocks[other]
    direction, offset = connection['direction'], connection['offset']
    dx, dy, key = dict(left=(-1, 0, 32), right=(1, 0, 16),
                       up=(0, -1, 64), down=(0, 1, 128))[direction]
    limit = height if direction in ['left', 'right'] else width
    other_limit = other_height if direction in ['left', 'right'] else other_width
    choices = []
    for coordinate in range(max(0, offset), min(limit, offset + other_limit)):
        x, y = ((0 if direction == 'left' else width - 1), coordinate) if direction in ['left', 'right'] else (coordinate, 0 if direction == 'up' else height - 1)
        xx, yy = ((other_width - 1 if direction == 'left' else 0), coordinate - offset) if direction in ['left', 'right'] else (coordinate - offset, other_height - 1 if direction == 'up' else 0)
        cells = [(name, x - dx, y - dy), (name, x, y),
                 (other, xx, yy), (other, xx + dx, yy + dy)]
        if not all(passable_cell(*cell, surfing) for cell in cells):
            continue
        if connection_step(name, x, y, key) != (other, xx, yy):
            continue
        reverse = {16: 32, 32: 16, 64: 128, 128: 64}[key]
        if connection_step(other, xx, yy, reverse) != (name, x, y):
            continue
        choices.append((cells[0], cells[-1]))
    return choices


def set_passability(pair, surfing):
    global passable, _planned_goal, _planned_keys
    passable = {name: {index for index in valid
                      if passable_cell(name, index % blocks[name][0],
                                       index // blocks[name][0], surfing)}
                if name in pair else set()
                for name, valid in full_passable.items()}
    _planned_goal, _planned_keys = None, {}


def loaded(label):
    name = by_location[location()]
    open_coast = bool(native('JourneySeviiIsOpenCoast'))
    assert open_coast == (name in open_coast_maps), ('Compiled coast whitelist differs from source', name, open_coast)
    value = validate_loaded(lib, s, source, metadata, name)
    row = dict(label=label, map=name, tile=list(position()),
               surfing=bool(lib.read8(s['gPlayerAvatar']) & 8),
               native_open_coast=open_coast,
               ocean_palette=ocean_palette(), loaded_art=value,
               capture=capture(label))
    loaded_checks.append(row)
    return row


for index, (pair, (name, other, connection)) in enumerate(sorted(pairs.items()), 1):
    # The previous crossing scoped the walker to its own two maps. Candidate
    # discovery must start from the complete native passability cache before
    # narrowing it to this seam; connection_step consults that same cache.
    passable = {map_name: valid.copy() for map_name, valid in full_passable.items()}
    # Prefer water so every available native Surf passage is exercised. Land
    # connections still need live loaded-bank evidence in both directions.
    choices = crossing_choices(name, other, connection, True)
    surfing = bool(choices)
    if not choices:
        choices = crossing_choices(name, other, connection, False)
    assert choices, ('No reciprocal surface passage', pair, connection)
    start, goal = choices[len(choices) // 2]
    assert start[1] <= 127 and start[2] <= 127, ('Fixture coordinate exceeds native warp ABI', start)
    set_passability(pair, surfing)
    native('SetPlayerAvatarTransitionFlags', 1)
    step(30)
    warp(*start)
    step(180)
    finish()
    assert (by_location[location()], *position()) == start, (start, location(), position())
    native('SetPlayerAvatarTransitionFlags', 8 if surfing else 1)
    step(60)
    prefix = 'seam-%02d-%s-to-%s' % (index, name, other)
    before = loaded(prefix + '-before')
    assert before['surfing'] == surfing, before
    first = len(transitions)
    walk(goal)
    after = loaded(prefix + '-after')
    assert after['surfing'] == surfing, after
    assert after['ocean_palette'] == before['ocean_palette'], ('Ocean palette changed across seam', pair, before, after)
    assert len(transitions) == first + 1, (pair, 'Outbound crossing took an indirect route', transitions[first:])
    assert transitions[-1]['source'][0] == name and transitions[-1]['destination'][0] == other
    walk(start)
    returned = loaded(prefix + '-returned')
    assert returned['surfing'] == surfing, returned
    assert returned['ocean_palette'] == before['ocean_palette'], ('Ocean palette changed on return', pair)
    observed = transitions[first:]
    assert len(observed) == 2, (pair, 'Return crossing took an indirect route', observed)
    assert observed[-1]['source'][0] == other and observed[-1]['destination'][0] == name
    checks.append(dict(maps=list(pair), source=list(start), destination=list(goal),
                       direction=connection['direction'], offset=connection['offset'],
                       mode='surf' if surfing else 'foot',
                       available_reciprocal_passages=len(choices),
                       outbound_and_return=True, native_controller_crossings=2,
                       surf_preserved=surfing, native_foot_mode_preserved=not surfing,
                       ocean_palette_identical=True, transitions=observed,
                       loaded_checks=[before['label'], after['label'], returned['label']],
                       no_midcrossing_warps_or_coordinate_writes=True))
    print('Integrated ocean art and native roundtrip passed:', pair,
          'Surf' if surfing else 'walking', flush=True)

assert len(checks) == 26 and len(transitions) == 52
assert targets <= {row['map'] for row in loaded_checks}, ('Unvisited private bank', sorted(targets - {row['map'] for row in loaded_checks}))
review_mode = bool(lib.read8(s['gJourneyReviewMode']))
lib.stop()
assert hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest() == initial_sha, 'ROM changed during validation'
result = dict(passed=True, kind='sevii-integrated-ocean-seams',
              rom_sha256=initial_sha, review_mode=review_mode, preflight=False,
              compiled_rom=True, target_maps=sorted(targets),
              compiled_art=compiled, seams=checks, loaded_checks=loaded_checks,
              surface_seams=len(checks), native_controller_crossings=2 * len(checks),
              surf_seams=sum(row['mode'] == 'surf' for row in checks),
              land_seams=sum(row['mode'] == 'foot' for row in checks),
              loaded_metatiles_palettes_and_vram_checked=True,
              attributes_and_native_object_body_words_preserved=True,
              ocean_palette_identical_at_all_checked_seams=True,
              all_affected_surface_connections_covered=True,
              no_midcrossing_warps_or_coordinate_writes=True,
              initial_positions_avatar_modes_party_and_progress_are_fixtures=True,
              full_campaign_playthrough=False, walked_tiles=walked,
              native_fast_water_coast_whitelist=sorted(open_coast_maps),
              fast_water_semantics_checked_per_map=True,
              captures=captures)
(args.output / 'ocean-seams.json').write_text(json.dumps(result, indent=2) + '\n')
