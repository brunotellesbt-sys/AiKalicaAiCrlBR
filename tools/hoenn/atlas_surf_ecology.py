"""Keep atlas routes attached to their historical encounter and habitat owners.

This stage changes lookup identity, never encounter content.  The caller must
choose an explicit historical owner for each new map; geometry/trigger audits
must reject chunks which combine incompatible owners.  An alias alone does
not establish that a family is catchable on the new terrain.
"""
from __future__ import annotations

from collections import defaultdict
import hashlib
import json
import re

from badge_story_layer import read


HEADER = 'include/journey_atlas_ecology.h'
IMPLEMENTATION = 'src/journey_atlas_ecology.c'
GROUPS = 'data/maps/map_groups.json'
CONTENT_PATHS = (
    'include/journey_wild_data.h',
    'include/journey_generation4_pools.h',
    'include/journey_habitat_data.h',
    'include/journey_generation4_habitats.h',
    'src/data/wild_encounters.json',
)
LOOKUP_FUNCTIONS = (
    ('src/journey_wild.c', 'JourneyWildSpecies'),
    ('src/journey_wild.c', 'JourneyWildPoolAvailable'),
    ('src/journey_wild.c', 'JourneyFishingOdds'),
    ('src/wild_encounter.c', 'GetCurrentMapWildMonHeaderId'),
)
DEX_LOCATIONS = 'src/data/journey_world_dex_locations.h'
DEX_ROW = re.compile(r'\{(SPECIES_\w+),(MAP_\w+),(\d+),(\d+),(\d+),(\d+)\}')


def _identities(groups):
    """Read native packed IDs; map constants use group in the upper byte."""
    result = {}
    order = groups['group_order']
    if len(order) != len(set(order)) or len(order) > 256:
        raise ValueError('Invalid native map group order')
    for group, label in enumerate(order):
        names = groups[label]
        if len(names) > 256:
            raise ValueError(f'Map group exceeds byte capacity: {label}')
        for number, name in enumerate(names):
            if name in result:
                raise ValueError(f'Duplicate native map name: {name}')
            result[name] = (group << 8) | number
    return result


def _parent_read(layer, path):
    raw = (layer.source / path).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == layer.expected[path], path
    return raw


def alias_rows(layer, owner_mapping):
    """Bind new names to unchanged historical IDs, refusing guessed chains."""
    if not isinstance(owner_mapping, dict) or not owner_mapping:
        raise ValueError('Explicit new-map to historical-owner mapping required')
    before = _identities(json.loads(_parent_read(layer, GROUPS)))
    after = _identities(json.loads(read(layer, GROUPS)))
    rows = []
    for target, owner in sorted(owner_mapping.items()):
        if not isinstance(target, str) or not isinstance(owner, str):
            raise ValueError('Ecology owners must be map names')
        if target not in after:
            raise ValueError(f'Unknown target map: {target}')
        if target in before:
            raise ValueError(f'Alias target is not a new map: {target}')
        if owner not in before:
            raise ValueError(f'Owner is not a historical map: {owner}')
        if after.get(owner) != before[owner]:
            raise ValueError(f'Historical owner was removed or renumbered: {owner}')
        if after[target] & 255 >= 100:
            raise ValueError(f'Atlas target exceeds 100-map group limit: {target}')
        if after[target] >> 8 >= 128:
            raise ValueError(f'Atlas target exceeds signed WarpData group limit: {target}')
        if before[owner] == 65535:
            raise ValueError('MAP_UNDEFINED cannot own encounters')
        target_id = json.loads(read(layer, f'data/maps/{target}/map.json'))['id']
        owner_path = f'data/maps/{owner}/map.json'
        owner_id = json.loads(_parent_read(layer, owner_path))['id']
        if json.loads(read(layer, owner_path))['id'] != owner_id:
            raise ValueError(f'Historical owner constant changed: {owner}')
        if any(not re.fullmatch(r'MAP_[A-Z0-9_]+', ident) for ident in (target_id, owner_id)):
            raise ValueError('Invalid native map constant')
        rows.append(dict(map=target, owner=owner, map_id=target_id,
                         owner_map_id=owner_id, packed_map_id=after[target],
                         owner_packed_map_id=before[owner]))
    return sorted(rows, key=lambda row: row['packed_map_id'])


def generate_lookup(rows):
    """Two byte-indexed reads, with a zero sentinel that preserves owner 0."""
    if not rows:
        raise ValueError('Empty ecology alias table')
    groups = defaultdict(list)
    for row in rows:
        groups[row['packed_map_id'] >> 8].append(row)
    body = ['#include "global.h"', '#include "constants/maps.h"',
            '#include "journey_atlas_ecology.h"', '',
            'struct JourneyAtlasEcologyGroup { const u16 *owners; u16 count; };']
    for group, members in sorted(groups.items()):
        body += [f'static const u16 sJourneyAtlasEcologyOwners{group}[] = {{']
        body += [f'    [MAP_NUM({row["map_id"]})] = {row["owner_map_id"]} + 1,'
                 for row in members]
        body += ['};']
    body += ['static const struct JourneyAtlasEcologyGroup sJourneyAtlasEcologyGroups[] = {']
    body += [f'    [{group}] = {{sJourneyAtlasEcologyOwners{group}, ARRAY_COUNT(sJourneyAtlasEcologyOwners{group})}},'
             for group in sorted(groups)]
    body += ['};', '', 'u16 JourneyAtlasEcologyOwner(u16 map)', '{',
             '    u32 group = MAP_GROUP(map), number = MAP_NUM(map);',
             '    const struct JourneyAtlasEcologyGroup *row;',
             '    if (group >= ARRAY_COUNT(sJourneyAtlasEcologyGroups)) return map;',
             '    row = &sJourneyAtlasEcologyGroups[group];',
             '    if (number >= row->count || row->owners == NULL || !row->owners[number]) return map;',
             '    return row->owners[number] - 1;', '}', '']
    header = ('#ifndef GUARD_JOURNEY_ATLAS_ECOLOGY_H\n'
              '#define GUARD_JOURNEY_ATLAS_ECOLOGY_H\n'
              'u16 JourneyAtlasEcologyOwner(u16 map);\n'
              '#endif\n')
    return header, '\n'.join(body)


def _function(text, name):
    """Locate a named definition and balance its braces, not the next function."""
    matches = list(re.finditer(r'\b' + re.escape(name) + r'\s*\([^;{}]*\)\s*\{', text))
    assert len(matches) == 1, ('Expected one ecology hook definition', name)
    opening = text.index('{', matches[0].start())
    depth = 1
    for index in range(opening + 1, len(text)):
        depth += (text[index] == '{') - (text[index] == '}')
        if depth == 0:
            return opening, index + 1
    raise AssertionError(('Unclosed ecology hook', name))


def _include(text):
    anchor = '#include "global.h"'
    assert text.count(anchor) == 1, 'Missing global.h ecology include anchor'
    assert '#include "journey_atlas_ecology.h"' not in text, 'Ecology aliases already staged'
    return text.replace(anchor, anchor + '\n#include "journey_atlas_ecology.h"', 1)


def _location_hook(text, name):
    opening, end = _function(text, name)
    body = text[opening:end]
    group = 'gSaveBlock1Ptr->location.mapGroup'
    number = 'gSaveBlock1Ptr->location.mapNum'
    assert group in body and number in body, ('Location lookup hook changed', name)
    body = body.replace(group, 'MAP_GROUP(ecologyMap)').replace(number, 'MAP_NUM(ecologyMap)')
    declaration = ('\n    u16 ecologyMap = JourneyAtlasEcologyOwner('
                   '(gSaveBlock1Ptr->location.mapGroup << 8) | gSaveBlock1Ptr->location.mapNum);')
    return text[:opening] + '{' + declaration + body[1:] + text[end:]


def _habitat_hook(text):
    name = 'JourneyHabitatHasSpecies'
    opening, end = _function(text, name)
    body = text[opening:end]
    assert 'group' in body and 'map' in body, 'Habitat lookup parameters changed'
    # Event-only species must check the physical map before ordinary aliases.
    # Otherwise a new sea chunk owned by a special-event map inherits that
    # event's species even though it has no corresponding event trigger.
    anchor = re.search(r'\n(?P<indent>\s*)if\s*\(\s*gJourneyBuildRules\.maxNational\s*==\s*493\s*\)', body)
    assert anchor and 'sJourneyEventDex' in body[:anchor.start()], 'Event guard must precede ordinary habitat aliases'
    assert 'return FALSE;' in body[:anchor.start()], 'Event-only species need a closed physical-map guard'
    assignment = ('\n    ecologyMap = JourneyAtlasEcologyOwner((group << 8) | map);'
                  '\n    group = MAP_GROUP(ecologyMap);'
                  '\n    map = MAP_NUM(ecologyMap);\n')
    body = body[:anchor.start()] + assignment + body[anchor.start():]
    return text[:opening] + '{\n    u16 ecologyMap;' + body[1:] + text[end:]


def stage(layer, owner_mapping):
    """Stage aliases after map/group writers; preserve Gen4/Gen9 and TESTE rules."""
    rows = alias_rows(layer, owner_mapping)
    header, implementation = generate_lookup(rows)
    preserved = {path: hashlib.sha256(read(layer, path)).hexdigest()
                 for path in CONTENT_PATHS}
    outputs = {HEADER: header, IMPLEMENTATION: implementation}
    for path in sorted({path for path, _ in LOOKUP_FUNCTIONS}):
        text = _include(read(layer, path).decode())
        for hook_path, name in LOOKUP_FUNCTIONS:
            if path == hook_path:
                text = _location_hook(text, name)
        outputs[path] = text
    path = 'src/journey_habitats.c'
    outputs[path] = _habitat_hook(_include(read(layer, path).decode()))
    for path, text in outputs.items():
        layer.stage(path, text)
    assert preserved == {path: hashlib.sha256(read(layer, path)).hexdigest()
                         for path in CONTENT_PATHS}, 'Ecology content changed during alias stage'
    return dict(kind='atlas-surf-ecology-aliases', aliases=rows,
                alias_count=len(rows), lookup='direct-group-number',
                changed_paths=sorted(outputs), preserved_content_sha256=preserved,
                hooks=[name for _, name in LOOKUP_FUNCTIONS] + ['JourneyHabitatHasSpecies'],
                generation4_and_generation9_content_preserved=True,
                party_level_scaling_and_evolution_phase_preserved=True,
                test_and_review_encounter_suppression_preserved=True,
                catchable_families_require_independent_compiled_trigger_audit=True,
                compiled_rom_validated=False)


def repair_dex_locations(header, before_census, after_census, plan, catalog):
    """Replace retired AREA claims only with actual graph-reachable triggers.

    The before/after reports come from validate_atlas_surf_ecology_source,
    after the physical source and aliases have been materialized. New chunks
    (including dedicated scenery reserves) must be in plan['chunks'] with
    their true global origin. No fixed-event or preserved-native row changes.
    Dead old habitat claims are removed explicitly rather than assigned a
    fictitious patch of grass. Loss of a previously effective claim rejects.
    """
    schema = 'atlas-surf-ecology-source-v1'
    if any(report.get('schema') != schema or not report.get('native_c_compiled')
           for report in (before_census, after_census)):
        raise ValueError('Dex repair requires native-C ecology source censuses')
    if not after_census.get('graph_reachable_cells_supplied'):
        raise ValueError('Dex AREA requires explicit graph-reachable trigger cells')
    if before_census.get('retired_maps'):
        raise ValueError('Before census must include historical physical routes')
    retired = set(after_census['retired_maps'])
    if not retired:
        raise ValueError('No retired maps supplied for Dex relocation')
    if plan.get('scale') != 8:
        raise ValueError('Dex atlas positions require the physical scale8 plan')
    chunks = {row['name']: row for row in plan['chunks']}
    if len(chunks) != len(plan['chunks']):
        raise ValueError('Duplicate Dex physical chunk names')
    species = {int(key): row['name'] for key, row in catalog.items()}
    # Parent map constants are included in the census for a content-bound
    # mapping from generated identifiers to their historical owners.
    parent_ids = before_census.get('map_constants', {})
    if not parent_ids:
        raise ValueError('Before census lacks bound native map constants')
    old_names = {constant: name for name, constant in parent_ids.items()}
    active_before = set()
    for row in before_census['map_areas']:
        for cap, members in row['species'].items():
            for member in members:
                active_before.add((row['map'], species[member], 4 if int(cap) == 493 else 9))
    replacements = {}
    for row in after_census['map_areas']:
        owner = row['owner']
        if owner not in retired or not any(row['species'].values()):
            continue
        chunk = chunks.get(row['map'])
        if chunk is None:
            raise ValueError(('Effective retired owner has no physical chunk origin', row['map']))
        if chunk.get('ecology_owner') != owner:
            raise ValueError(('Dex owner differs from physical chunk owner', row['map']))
        if not row['trigger_sample']:
            raise ValueError('Species claim lacks an actual trigger coordinate')
        x, y = row['trigger_sample'][0]
        if not (0 <= x < chunk['width'] and 0 <= y < chunk['height']):
            raise ValueError('Dex trigger outside physical chunk')
        gx, gy = chunk['origin']
        atlas = (gx+x)//8, (gy+y)//8
        if not (0 <= atlas[0] < 224 and 0 <= atlas[1] < 112):
            raise ValueError('Dex trigger projects outside the immutable atlas')
        for cap, members in row['species'].items():
            for member in members:
                key = owner, species[member], 4 if int(cap) == 493 else 9
                value = (species[member], chunk['id'], atlas[0], atlas[1], 0, key[2])
                replacements.setdefault(key, set()).add(value)
    matches = list(DEX_ROW.finditer(header))
    if not matches or header.count('sWorldDexLocations') != 1:
        raise ValueError('Expected one native Dex AREA array')
    emitted = set()
    removed_dead, remapped, missing = [], [], []
    for match in matches:
        name, ident = match[1], match[2]
        value = (name, ident, *map(int, match.groups()[2:]))
        old = old_names.get(ident)
        if old not in retired:
            emitted.add(value)
            continue
        if value[4]:
            raise ValueError('Fixed event AREA on retired map needs explicit event relocation')
        key = old, name, value[5]
        target = replacements.get(key)
        if target:
            # Keep one real witness for each old claim, rather than multiplying
            # every pool member across all chunks and wasting scarce ROM space.
            chosen = min(target, key=lambda row: (abs(row[2]-value[2])+abs(row[3]-value[3]), row))
            emitted.add(chosen)
            remapped.append(dict(old_map=old, species=name, cap=value[5],
                                 destination=chosen[1], atlas=list(chosen[2:4]),
                                 eligible_trigger_locations=len(target)))
        elif key in active_before:
            missing.append(dict(old_map=old, species=name, cap=value[5]))
        else:
            removed_dead.append(dict(old_map=old, species=name, cap=value[5],
                                     reason='Historical habitat row had no effective area trigger'))
    if missing:
        raise ValueError(('Previously effective Dex AREA species lost its trigger', missing))
    start = re.search(r'(static const struct JourneyWorldDexLocation sWorldDexLocations\[\]\s*=\s*\{)', header)
    if start is None:
        raise ValueError('Missing native Dex array initializer')
    end = header.find('};', start.end())
    if end < 0:
        raise ValueError('Unterminated native Dex array')
    body = '\n'.join('{'+','.join(map(str, row))+'},' for row in sorted(emitted))
    rewritten = header[:start.end()]+'\n'+body+'\n'+header[end:]
    return rewritten, dict(kind='atlas-surf-dex-trigger-relocation',
                           before_rows=len(matches), after_rows=len(emitted),
                           remapped_rows=remapped, removed_dead_claims=removed_dead,
                           effective_claims_lost=[], graph_reachable_source_witnesses=True,
                           replacement_rows_per_old_claim_at_most_one=True,
                           fixed_and_native_rows_preserved=True,
                           before_source_manifest_sha256=before_census['source_manifest_sha256'],
                           after_source_manifest_sha256=after_census['source_manifest_sha256'],
                           compiled_rom_validated=False)


def stage_dex_locations(layer, before_census, after_census, plan, catalog):
    """Stage an independently witnessed AREA correction in the current layer."""
    header = read(layer, DEX_LOCATIONS).decode()
    updated, report = repair_dex_locations(header, before_census, after_census, plan, catalog)
    layer.stage(DEX_LOCATIONS, updated)
    return report
