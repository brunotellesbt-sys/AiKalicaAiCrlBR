"""Audit actual source encounter triggers, not the union of habitat pools.

Native C enums, pool initializers and the unchanged native behavior predicates
are compiled on the host. Terrain/collision is read independently from the
source layouts. This is a source audit; it does not certify a built ROM or
controller travel. Explicit reachable cells can bind a later graph proof.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import ctypes
import hashlib
import json
import os
from pathlib import Path
import posixpath
import re
import shutil
import subprocess
import tempfile

from aquatic_species import aquatic_ids
from atlas_surf_source import Source, CARDINAL, compatible_height


ROOT = Path(__file__).resolve().parents[2]
FIELDS = ('land_mons', 'water_mons', 'rock_smash_mons', 'fishing_mons', 'hidden_mons')
CAPS = (493, 1025)


def _source_view(value):
    """Accept a disk source or the verified logical Source/OverlaySource API."""
    if isinstance(value,(str,os.PathLike)):
        return Source(value)
    methods=('read','js','layout','words','word','behavior','assert_unchanged')
    if (not all(callable(getattr(value,name,None)) for name in methods)
            or not all(hasattr(value,name) for name in ('source','maps','identities','inputs'))):
        raise TypeError('Ecology census requires a path or verified Source-like terrain view')
    return value


def _registry_ids(groups):
    result={}
    order=groups.get('group_order')
    if not isinstance(order,list) or len(order)>256 or len(set(order))!=len(order):
        raise ValueError('Invalid compiled ecology map group order')
    for group,label in enumerate(order):
        names=groups.get(label)
        if not isinstance(names,list) or len(names)>256:
            raise ValueError(('Invalid compiled ecology map group',label))
        for number,name in enumerate(names):
            if not isinstance(name,str) or name in result:
                raise ValueError(('Duplicate or invalid compiled ecology map name',name))
            result[name]=(group<<8)|number
    return result


def _map_id_header(inputs):
    """Generate only the absent native map_groups.h from authenticated JSON.

    An overlay must preserve every disk-parent registry identity. Map constants
    come from the same logical map JSON consumed by the terrain census; cached
    Source dictionaries may not silently diverge from those verified reads.
    """
    registry_path='data/maps/map_groups.json'
    current_raw=inputs.read(registry_path)
    current=_registry_ids(json.loads(current_raw))
    if current!=inputs.identities:
        raise ValueError('Ecology Source identities differ from its authenticated logical registry')
    parent_path=Path(inputs.source)/registry_path
    parent_raw=parent_path.read_bytes()
    layer=getattr(inputs,'layer',None)
    if layer is not None and hashlib.sha256(parent_raw).hexdigest()!=layer.expected[registry_path]:
        raise ValueError('Ecology historical registry changed behind the candidate overlay')
    historical=_registry_ids(json.loads(parent_raw))
    for name,identity in historical.items():
        if current.get(name)!=identity:
            raise ValueError(('Ecology overlay removed or renumbered a historical map',name))
    lines=['// Host audit: generated from the verified logical map registry.',
           '#ifndef GUARD_ATLAS_ECOLOGY_MAP_GROUPS_H','#define GUARD_ATLAS_ECOLOGY_MAP_GROUPS_H']
    seen=set()
    for name,identity in sorted(current.items(),key=lambda item:item[1]):
        mapping=inputs.js(f'data/maps/{name}/map.json')
        symbol=mapping['id']
        if (not re.fullmatch(r'MAP_[A-Z0-9_]+',symbol) or symbol in seen
                or name not in inputs.maps or inputs.maps[name]['id']!=symbol):
            raise ValueError(('Invalid or inconsistent ecology map constant',name,symbol))
        seen.add(symbol)
        lines.append(f'#define {symbol} {identity}')
    lines.extend(('#endif',''))
    raw='\n'.join(lines).encode()
    return raw,dict(logical_registry_sha256=hashlib.sha256(current_raw).hexdigest(),
                    historical_registry_sha256=hashlib.sha256(parent_raw).hexdigest(),
                    generated_map_groups_sha256=hashlib.sha256(raw).hexdigest(),
                    historical_maps=len(historical),compiled_maps=len(current),
                    historical_ids_unchanged=True)


def _write_header_view(inputs,destination,roots,map_groups):
    """Mirror quoted native includes through Source.read, with no disk fallback.

    In particular, a staged pool/species/header cannot accidentally be compiled
    from the immutable parent's include directory. The sole synthetic header
    is map_groups.h, normally emitted by the native mapjson build step.
    """
    synthetic={'constants/map_groups.h':map_groups}
    written={}
    visiting=set()
    def normalized(path):
        result=posixpath.normpath(path)
        if result.startswith('../') or result.startswith('/') or result== '..' or '\\' in result:
            raise ValueError(('Unsafe quoted native ecology include',path))
        return result
    def write(path,known=None):
        path=normalized(path)
        if path in written or path in visiting:return
        raw=known if known is not None else synthetic[path] if path in synthetic else inputs.read('include/'+path)
        visiting.add(path)
        target=destination/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        written[path]=hashlib.sha256(raw).hexdigest()
        for include in re.findall(r'^\s*#\s*include\s*"([^"\n]+)"',raw.decode(),re.M):
            attempts=list(dict.fromkeys((normalized(posixpath.join(posixpath.dirname(path),include)),normalized(include))))
            for candidate in attempts:
                if candidate in synthetic:
                    write(candidate);break
                try:child=inputs.read('include/'+candidate)
                except FileNotFoundError:continue
                write(candidate,child);break
            else:
                raise ValueError(('Native ecology include is unavailable in the logical source',path,include))
        visiting.remove(path)
    for path in roots:write(path)
    # Even when the top-level native wrapper is guarded out, retain the full
    # generated identity header in this compilation's deterministic manifest.
    write('constants/map_groups.h')
    return dict(sorted(written.items()))


def definition(text, name):
    """Extract one real C definition with balanced braces and its return type."""
    matches = list(re.finditer(r'(?m)^(?:static\s+)?(?:bool8|bool32|u8|u16|u32)\s+'
                              +re.escape(name)+r'\s*\([^;{}]*\)\s*\{', text))
    if len(matches) != 1:
        raise ValueError(('Native ecology predicate missing or ambiguous', name))
    begin = matches[0].start()
    opening = text.index('{', begin)
    depth = 1
    for index in range(opening+1, len(text)):
        depth += (text[index] == '{')-(text[index] == '}')
        if depth == 0:
            return text[begin:index+1]
    raise ValueError(('Unterminated native ecology predicate', name))


class CompiledEcology:
    """Native data and predicates, evaluated without guessing implicit enums."""
    def __init__(self, inputs):
        inputs=_source_view(inputs)
        self.inputs = inputs
        source = inputs.source
        wild = inputs.read('src/journey_wild.c').decode()
        behavior = inputs.read('src/metatile_behavior.c').decode()
        coast = inputs.read('src/journey_sevii_surf.c').decode()
        encounters = inputs.read('src/wild_encounter.c').decode()
        structs = '\n'.join(re.search(r'struct '+name+r'\s*\{[^}]+\};', wild)[0]
                            for name in ('JourneyWildStages', 'JourneyWildPool'))
        table = re.search(r'static const u8 sTileBitAttributes\s*\[[^]]+\]\s*=\s*\{.*?\};', behavior, re.S)
        flags = '\n'.join(re.findall(r'^#define\s+TILE_FLAG_\w+[^\n]*', behavior, re.M))
        if table is None or not flags:
            raise ValueError('Native encounter flags missing')
        predicates = ('MetatileBehavior_IsEncounterTile', 'MetatileBehavior_IsSurfableWaterOrUnderwater',
                      'MetatileBehavior_IsLandWildEncounter', 'MetatileBehavior_IsWaterWildEncounter',
                      'MetatileBehavior_IsBridgeOverWater', 'MetatileBehavior_IsSurfableFishableWater',
                      'MetatileBehavior_IsWaterfall')
        paths = ('include/constants/maps.h','include/constants/species.h', 'include/constants/metatile_behaviors.h',
                 'include/constants/map_types.h', 'include/journey_wild_data.h',
                 'include/journey_generation4_pools.h', 'include/journey_habitat_data.h',
                 'include/journey_generation4_habitats.h')
        for path in paths:
            inputs.read(path)
        map_groups,self.map_registry_proof=_map_id_header(inputs)
        prefix = r'''
#include <stdint.h>
#include <stddef.h>
typedef uint8_t u8; typedef uint16_t u16; typedef uint32_t u32;
typedef uint8_t bool8; typedef uint32_t bool32;
#define TRUE 1
#define FALSE 0
#define ARRAY_COUNT(a) (sizeof(a)/sizeof((a)[0]))
#include "constants/species.h"
#include "constants/maps.h"
#include "constants/metatile_behaviors.h"
#include "constants/map_types.h"
static struct {struct {u8 mapGroup,mapNum;} location;} save;
static struct {struct {u8 mapGroup,mapNum;} location;} *unusedSave;
#define gSaveBlock1Ptr (&save)
static struct {enum MapType mapType;} gMapHeader;
'''
        prefix = prefix.replace('static struct {struct {u8 mapGroup,mapNum;} location;} *unusedSave;\n', '')
        data = structs+'\n#include "journey_wild_data.h"\n#include "journey_generation4_pools.h"\n'
        # Habitat data are compiled here too, preserving their actual species IDs.
        data += '#include "journey_habitat_data.h"\n#include "journey_generation4_habitats.h"\n'
        alias_path = 'src/journey_atlas_ecology.c'
        try:
            aliases = inputs.read(alias_path).decode()
            aliases = re.sub(r'^\s*#include[^\n]*\n', '', aliases, flags=re.M)
        except FileNotFoundError:
            aliases = 'u16 JourneyAtlasEcologyOwner(u16 map) {return map;}\n'
        if 'JourneyAtlasLandEncounter' in aliases:
            from atlas_sand_habitats import verify_hooks
            verify_hooks(encounters)
            extra_land = 'return JourneyAtlasLandEncounter(map, behavior, elevation);'
        else:
            extra_land = '(void)map;(void)behavior;(void)elevation;return 0;'
        functions = definition(coast, 'IsConnectedSeviiCoast')+'\n'
        functions += 'bool32 JourneySeviiIsOpenCoast(void) { return IsConnectedSeviiCoast(save.location.mapGroup, save.location.mapNum); }\n'
        functions += '\n'.join(definition(behavior, name) for name in predicates)
        functions += '\n'+definition(encounters, 'JourneyCoastalDepthEncounterTile')+'\n'
        exports = r'''
u32 ecology_pool_count(u32 cap) {return cap==493?ARRAY_COUNT(sJourneyGeneration4Pools):ARRAY_COUNT(sJourneyWildPools);}
void ecology_pool(u32 cap,u32 index,u32 *out) {
 const struct JourneyWildPool *p=cap==493?&sJourneyGeneration4Pools[index]:&sJourneyWildPools[index];
 out[0]=p->map;out[1]=p->area;out[2]=p->count;
 for(u32 i=0;i<p->count;i++)out[3+i]=p->species[i];
}
u32 ecology_stage_count(void) {return ARRAY_COUNT(sJourneyWildStages);}
void ecology_stages(u32 index,u32 *out) {
 const struct JourneyWildStages *p=&sJourneyWildStages[index];out[0]=p->root;
 for(u32 phase=0;phase<3;phase++) {out[1+phase*9]=p->count[phase];
 for(u32 i=0;i<p->count[phase];i++)out[2+phase*9+i]=p->stages[phase][i];}
}
u32 ecology_habitat_count(u32 cap) {return cap==493?ARRAY_COUNT(sJourneyGeneration4Habitats):ARRAY_COUNT(sJourneyHabitats);}
void ecology_habitat(u32 cap,u32 index,u32 *out) {
 const struct JourneyHabitat *p=cap==493?&sJourneyGeneration4Habitats[index]:&sJourneyHabitats[index];
 out[0]=p->map;out[1]=p->count;for(u32 i=0;i<p->count;i++)out[2+i]=p->species[i];
}
u32 ecology_fishing_count(void) {return ARRAY_COUNT(sJourneyFishingHabitats);}
void ecology_fishing(u32 index,u32 *out) {out[0]=sJourneyFishingHabitats[index].map;out[1]=sJourneyFishingHabitats[index].percent;}
u32 ecology_owner(u32 packed) {return JourneyAtlasEcologyOwner(packed);}
u32 ecology_trigger(u32 packed,u32 underwater,u32 behavior) {
 save.location.mapGroup=packed>>8;save.location.mapNum=packed;
 gMapHeader.mapType=underwater?MAP_TYPE_UNDERWATER:MAP_TYPE_OCEAN_ROUTE;
 return (MetatileBehavior_IsLandWildEncounter(behavior)?1:0)
 | ((MetatileBehavior_IsWaterWildEncounter(behavior)||JourneyCoastalDepthEncounterTile(behavior))?2:0)
 | (MetatileBehavior_IsSurfableFishableWater(behavior)?4:0)
 | (MetatileBehavior_IsSurfableWaterOrUnderwater(behavior)?8:0)
 | (MetatileBehavior_IsBridgeOverWater(behavior)?16:0)
 | (MetatileBehavior_IsWaterfall(behavior)?32:0);
}
'''
        exports += '\nu32 ecology_atlas_land_trigger(u32 map,u32 behavior,u32 elevation) {'+extra_land+'}\n'
        code = prefix+'\n'+data+'\n'+aliases+'\n'+flags+'\n'+table[0]+'\n'+functions+'\n'+exports
        compiler = shutil.which('cc') or shutil.which('gcc')
        if not compiler:
            raise RuntimeError('Native C compiler required for ecology audit')
        with tempfile.TemporaryDirectory(prefix='atlas-ecology-c-') as temp:
            path, library = Path(temp)/'ecology.c', Path(temp)/'ecology.so'
            include_root=Path(temp)/'include'
            self.compilation_headers_sha256=_write_header_view(inputs,include_root,
                [path.removeprefix('include/') for path in paths],map_groups)
            self.code_sha256=hashlib.sha256(code.encode()+json.dumps(self.compilation_headers_sha256,sort_keys=True).encode()).hexdigest()
            path.write_text(code)
            command = [compiler, '-std=gnu17', '-Wall', '-Wextra', '-Werror', '-shared', '-fPIC',
                       '-iquote', str(include_root), str(path), '-o', str(library)]
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode:
                raise ValueError(('Native ecology compilation failed', result.stderr))
            self.native = ctypes.CDLL(str(library))
        parent_registry=Path(inputs.source)/'data/maps/map_groups.json'
        if hashlib.sha256(parent_registry.read_bytes()).hexdigest()!=self.map_registry_proof['historical_registry_sha256']:
            raise ValueError('Historical ecology map registry changed during native compilation')
        inputs.assert_unchanged()
        self.pools, self.habitats, self.stages, self.fishing = {}, {}, {}, {}
        buffer = (ctypes.c_uint32*64)()
        for cap in CAPS:
            pools, habitats = {}, {}
            for index in range(self.native.ecology_pool_count(cap)):
                self.native.ecology_pool(cap, index, buffer)
                packed, area, count = buffer[:3]
                if count > 24 or (packed, area) in pools:
                    raise ValueError('Invalid compiled ecology pool')
                pools[packed, area] = list(buffer[3:3+count])
            for index in range(self.native.ecology_habitat_count(cap)):
                self.native.ecology_habitat(cap, index, buffer)
                packed, count = buffer[:2]
                if count > 62 or packed in habitats:
                    raise ValueError('Invalid compiled habitat table')
                habitats[packed] = list(buffer[2:2+count])
            self.pools[cap], self.habitats[cap] = pools, habitats
        for index in range(self.native.ecology_stage_count()):
            self.native.ecology_stages(index, buffer)
            phases = []
            for phase in range(3):
                count = buffer[1+phase*9]
                if count > 8:
                    raise ValueError('Invalid compiled family-stage count')
                phases.append(list(buffer[2+phase*9:2+phase*9+count]))
            self.stages[index] = dict(root=buffer[0], stages=phases)
        for index in range(self.native.ecology_fishing_count()):
            self.native.ecology_fishing(index, buffer)
            self.fishing[buffer[0]] = buffer[1]
        event = re.search(r'eventDex\[\]\s*=\s*\{([^}]+)\}', wild)
        if event is None:
            raise ValueError('Event-only encounter exclusion guard missing')
        self.event_dex = {int(x.strip()) for x in event[1].split(',')}

    def members(self, root, cap, water):
        """All effective phase outputs, including native stage fallback."""
        family = self.stages.get(root)
        if family is None:
            return []
        out = set()
        for initial in range(3):
            phase = initial
            for _ in range(3):
                eligible = {species for species in family['stages'][phase]
                            if species in self.catalog and 0 < self.catalog[species]['national_dex'] <= cap
                            and (not water or species in self.aquatic)}
                if eligible:
                    out.update(eligible)
                    break
                phase = max(0, phase-1)
        return sorted(out)


def _headers(inputs):
    document = inputs.js('src/data/wild_encounters.json')
    rows = {}
    for group in document['wild_encounter_groups']:
        if not group.get('for_maps'):
            continue
        for row in group['encounters']:
            if 'map' not in row:
                continue
            if any(any(key.startswith(field+'_') for field in FIELDS) for key in row):
                raise ValueError('Time-specific source headers require explicit runtime fallback audit')
            # The first native header for a map is the runtime default.
            rows.setdefault(row['map'], row)
    return rows


def terrain_triggers(inputs, compiled, name, reachable_cells=None):
    """Read collision, native predicates, height and physical fishing targets."""
    layout, mapping = inputs.layout(name), inputs.maps[name]
    width, height = layout['width'], layout['height']
    underwater = mapping.get('map_type') == 'MAP_TYPE_UNDERWATER'
    packed = inputs.identities[name]
    allowed = None if reachable_cells is None else {tuple(p) for p in reachable_cells}
    triggers = {area: [] for area in range(5)}
    grass = []
    masks = {}
    for index, word in enumerate(inputs.words(name)):
        point = index % width, index//width
        if word & 0xC00 or allowed is not None and point not in allowed:
            continue
        behavior = inputs.behavior(name, word)
        if behavior >= 256:
            raise ValueError(('Native u8 predicate cannot represent behavior', name, behavior))
        if behavior not in masks:
            masks[behavior] = compiled.native.ecology_trigger(packed, underwater, behavior)
        flags = masks[behavior]
        if flags & 1 or compiled.native.ecology_atlas_land_trigger(packed, behavior, word >> 12):
            triggers[0].append(point)
            grass.append(point)
        if flags & 2 or flags & 16 and word >> 12 in (0, 1, 15):
            triggers[1].append(point)
        # CanFish allows Surf from an adjacent passable Surf tile, or a dry
        # elevation3 shore facing fishable water at a different elevation.
        if not underwater and flags & (4 | 8 | 16) and not flags & 32:
            for dx, dy in CARDINAL.values():
                stand = point[0]+dx, point[1]+dy
                if not (0 <= stand[0] < width and 0 <= stand[1] < height):
                    continue
                if allowed is not None and stand not in allowed:
                    continue
                at = inputs.word(name, *stand)
                if at & 0xC00:
                    continue
                at_behavior = inputs.behavior(name, at)
                stand_flags = masks.setdefault(at_behavior, compiled.native.ecology_trigger(packed, underwater, at_behavior))
                surf = stand_flags & (8 | 16) and (flags & (8 | 16)) and compatible_height(at, word)
                shore = at >> 12 == 3 and flags & 4 and not compatible_height(at, word)
                if surf or shore:
                    triggers[3].append(stand)
                    break
    # Rock Smash has a real object/script trigger, rather than every pool row.
    rock_objects = [event for event in mapping.get('object_events', [])
                    if 'RockSmash' in event.get('script', '')]
    for event in rock_objects:
        point = event['x'], event['y']
        if any(0 <= point[0]+dx < width and 0 <= point[1]+dy < height
               and not inputs.word(name, point[0]+dx, point[1]+dy)&0xC00
               and (allowed is None or (point[0]+dx, point[1]+dy) in allowed)
               for dx, dy in CARDINAL.values()):
            triggers[2].append(point)
    return triggers, grass


def census(source, *, owner_mapping=None, retired_maps=(), reachable_cells=None, catalog=None):
    """Return per-map/per-area effective families and real source witnesses.

    ``owner_mapping`` contains physical new-map -> historical pool owner names.
    ``retired_maps`` are omitted as physical locations but remain valid owners.
    ``reachable_cells`` optionally maps each physical map to graph-proved tile
    coordinates; absent cells in that mode do not become a trigger witness.
    """
    inputs = _source_view(source)
    compiled = CompiledEcology(inputs)
    catalog_path = ROOT/'tools/hoenn/catalog_metadata.json'
    raw = catalog_path.read_bytes() if catalog is None else json.dumps(catalog, sort_keys=True).encode()
    catalog = json.loads(raw)['species'] if catalog is None else catalog
    compiled.catalog = {int(key): row for key, row in catalog.items()}
    compiled.aquatic = aquatic_ids(catalog)
    headers = _headers(inputs)
    by_packed = {value: key for key, value in inputs.identities.items()}
    actual_aliases = {}
    for name, packed in inputs.identities.items():
        owner = compiled.native.ecology_owner(packed)
        if owner not in by_packed:
            raise ValueError(('Compiled ecology owner does not exist', name, owner))
        if owner != packed:
            actual_aliases[name] = by_packed[owner]
    if owner_mapping is not None and actual_aliases != owner_mapping:
        raise ValueError(('Compiled ecology aliases differ from supplied owner mapping', actual_aliases, owner_mapping))
    aliases = actual_aliases
    retired = set(retired_maps)
    if not retired <= inputs.maps.keys():
        raise ValueError(('Unknown retired ecology maps', sorted(retired-inputs.maps.keys())))
    for name, owner in aliases.items():
        if name not in inputs.maps or owner not in inputs.maps or name == owner:
            raise ValueError(('Invalid physical ecology alias', name, owner))
    roots = {cap: set() for cap in CAPS}
    union = {cap: set() for cap in CAPS}
    witnesses, rows, grass_rows = {cap: defaultdict(list) for cap in CAPS}, [], []
    candidates = set(aliases)
    for cap in CAPS:
        candidates.update(by_packed[mid] for mid, _ in compiled.pools[cap] if mid in by_packed)
    for name in sorted(candidates-retired):
        owner = aliases.get(name, name)
        packed = inputs.identities[owner]
        mapping = inputs.maps[name]
        physical_cells = None if reachable_cells is None else reachable_cells.get(name, [])
        triggers, grass = terrain_triggers(inputs, compiled, name, physical_cells)
        if grass:
            grass_rows.append(dict(map=name, cells=len(grass), coordinates=[list(p) for p in grass]))
        header = headers.get(inputs.maps[owner]['id'], {})
        for area, field in enumerate(FIELDS):
            # Hidden search requires actual land/water terrain but no ordinary
            # source header in this project; it is never counted from a pool alone.
            if area == 4:
                continue
            table = header.get(field)
            nonzero = bool(table and (table.get('encounter_rate', 0) > 0 or area == 3))
            members_by_cap, families_by_cap = {}, {}
            for cap in CAPS:
                pool = compiled.pools[cap].get((packed, area), [])
                eligible_roots = set()
                species = set()
                for root in pool:
                    if root not in compiled.catalog or compiled.catalog[root]['national_dex'] in compiled.event_dex:
                        continue
                    effective = compiled.members(root, cap, water=area in (1, 3))
                    if effective:
                        family = compiled.stages[root]['root']
                        union[cap].add(family)
                        if nonzero and triggers[area]:
                            eligible_roots.add(family)
                            species.update(effective)
                families_by_cap[str(cap)] = sorted(eligible_roots)
                members_by_cap[str(cap)] = sorted(species)
                roots[cap].update(eligible_roots)
                for family in eligible_roots:
                    witnesses[cap][family].append(dict(map=name, owner=owner, area=area,
                                                     tile=list(triggers[area][0])))
            if any(families_by_cap.values()) or triggers[area] or table:
                rows.append(dict(map=name, owner=owner, area=area, field=field,
                                 terrain_trigger_cells=len(triggers[area]),
                                 trigger_sample=[list(p) for p in triggers[area][:8]],
                                 native_header_present=bool(table), encounter_rate=table.get('encounter_rate') if table else None,
                                 families=families_by_cap, species=members_by_cap,
                                 fishing_percent=compiled.fishing.get(packed, 100) if area == 3 else None))
    inputs.assert_unchanged()
    manifest = dict(sorted(inputs.inputs.items()))
    return dict(schema='atlas-surf-ecology-source-v1', kind='atlas-surf-ecology-source-census',
                native_c_compiled=True, native_c_sha256=compiled.code_sha256,
                native_c_headers_sha256=compiled.compilation_headers_sha256,
                compiled_map_registry=compiled.map_registry_proof,
                source_inputs_sha256=manifest,
                source_manifest_sha256=hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest(),
                catalog_sha256=hashlib.sha256(raw).hexdigest(),
                catchable_family_counts={str(cap): len(roots[cap]) for cap in CAPS},
                families={str(cap): sorted(roots[cap]) for cap in CAPS},
                pool_union_family_counts={str(cap): len(union[cap]) for cap in CAPS},
                family_witnesses={str(cap): {str(root): values for root, values in sorted(witnesses[cap].items())} for cap in CAPS},
                map_areas=rows, land_trigger_maps=grass_rows,
                map_constants={name: row['id'] for name, row in sorted(inputs.maps.items())},
                retired_maps=sorted(retired), aliases=dict(sorted(aliases.items())),
                graph_reachable_cells_supplied=reachable_cells is not None,
                compiled_alias_map_lookup_verified=True,
                global_reachability_proven=False, compiled_rom_validated=False,
                all_time_periods_equivalent_source_headers=True,
                event_species_excluded_from_ordinary_pools=True,
                final_release_validated=False)


def compare(before, after):
    """Refuse family loss; report added families separately for review."""
    missing, added = {}, {}
    for cap in map(str, CAPS):
        old, new = set(before['families'][cap]), set(after['families'][cap])
        missing[cap], added[cap] = sorted(old-new), sorted(new-old)
    return dict(kind='atlas-surf-ecology-source-comparison',
                preserved=not any(missing.values()), missing_families=missing,
                added_families=added, before_counts=before['catchable_family_counts'],
                after_counts=after['catchable_family_counts'], compiled_rom_validated=False)


def owner_requirements(report, retired_maps):
    """Expose old effective area owners; do not turn pool-only claims into land.

    A scenery reservation carrying grass should keep that exact historical
    owner. Ordinary water chunks may choose a real water/fishing owner, but
    the completed source census must prove global family preservation.
    """
    retired = set(retired_maps)
    rows = []
    for row in report['map_areas']:
        if row['map'] in retired and any(row['families'].values()):
            rows.append(dict(owner=row['map'], area=row['area'],
                             families=row['families'], species=row['species'],
                             trigger_cells=row['terrain_trigger_cells'],
                             historical_sample=row['trigger_sample'][0],
                             fishing_percent=row['fishing_percent']))
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--owner-mapping', type=Path)
    parser.add_argument('--retired-maps', type=Path)
    parser.add_argument('--reachable-cells', type=Path)
    args = parser.parse_args()
    report = census(args.source,
                    owner_mapping=json.loads(args.owner_mapping.read_text()) if args.owner_mapping else None,
                    retired_maps=json.loads(args.retired_maps.read_text()) if args.retired_maps else (),
                    reachable_cells=json.loads(args.reachable_cells.read_text()) if args.reachable_cells else None)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({key: report[key] for key in ('kind', 'catchable_family_counts', 'pool_union_family_counts', 'compiled_rom_validated')}))
