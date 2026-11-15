"""Audit physical source reachability without reading GPS or trusting plan edges.

The graph uses native block words, bank-specific behaviors, cardinal source
connections, directed warp events and explicit Dive witnesses.  Its SCCs are
terrain proofs, not controller/actor/camera certificates.  Missing final
destinations remain pending; historical coordinates are never substituted.
"""
from array import array
from collections import Counter, deque
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from atlas_surf_source import Source

DIRS = {'left': (-1, 0), 'right': (1, 0), 'up': (0, -1), 'down': (0, 1)}
OPPOSITE = {'left': 'right', 'right': 'left', 'up': 'down', 'down': 'up'}
KINDS = ('ports', 'caves', 'dives', 'adapters', 'native_pixels')

# Reviewed resolver bodies, already exercised by the emitted-C Dive tests.
# These fingerprints authenticate the implemented arithmetic/guards; they are
# never ROM hashes or native-pass flags. A changed implementation needs review.
_DIVE_FUNCTIONS = {
    'JourneyAtlasDiveBehavior': 'c399842c462501d62eeb831fcc4c51b924934f0849602a1f2f262211ea84eaef',
    'JourneyAtlasDiveSurfaceCell': 'a05cfeeb9cb51d87fa348f4bd61809df39ccefd6fa2861d025093382b0d5dea6',
    'JourneyAtlasDiveDepthCell': '6b6c70470e3dc29cccf225cb73629915209b085e05b1ed5452477ec1ab35ce80',
    'JourneyAtlasSetDiveWarp': 'dc2cb20d7691797d51152416ca22ee6bc69cdcd8d31559ae3862c7cecb08dfc6',
    'JourneyAtlasDepthSite': 'c97804c3dc5b4cd1ac7e0b0379661c6b4367851fbda80c719d4dc1dca214e252',
    'JourneyAtlasChunk': 'c4ad33eaacad6107322995108d296eb8a59570840961a821adcc1f4720e9416b',
    'JourneyAtlasWorldChunk': '40804dd14372b06890ba589d6ce89c3cde64cdddcfc343351687507c983d1995',
    'JourneyAtlasFloor32': 'c529c2b6911b3db22f939bcf93425fd57ad32453fa13155c9c39549183d3d87d',
}


def _compact(text):
    return re.sub(r'\s+', '', re.sub(r'/\*.*?\*/|//[^\n]*', '', text, flags=re.S))


def _function_body(text, name):
    clean = re.sub(r'/\*.*?\*/|//[^\n]*', '', text, flags=re.S)
    match = re.search(r'\b'+re.escape(name)+r'\s*\([^;{}]*\)\s*\{', clean)
    if not match:
        raise ValueError(('Missing implemented source function', name))
    depth, end = 1, match.end()
    start = end
    while end < len(clean) and depth:
        depth += (clean[end] == '{')-(clean[end] == '}')
        end += 1
    if depth:
        raise ValueError(('Unclosed implemented source function', name))
    return clean[start:end-1]


def _literal_rows(text, symbol, columns):
    clean = re.sub(r'/\*.*?\*/|//[^\n]*', '', text, flags=re.S)
    match = re.search(r'\b'+re.escape(symbol)+r'\s*\[\s*\]\s*=\s*\{(.*?)\};', clean, re.S)
    if not match:
        raise ValueError(('Missing literal C table', symbol))
    body = match[1]
    groups = re.findall(r'\{([^{}]*)\}', body) if columns > 1 else [body]
    if columns > 1 and re.sub(r'\{[^{}]*\}|[\s,]', '', body):
        raise ValueError(('Nonliteral or nested C initializer', symbol))
    rows = []
    for group in groups:
        tokens = [token.strip() for token in group.split(',') if token.strip()]
        if any(not re.fullmatch(r'[+-]?(?:0[xX][0-9a-fA-F]+|\d+)', token) for token in tokens):
            raise ValueError(('Nonliteral numeric C initializer', symbol))
        values = [int(token, 16) if 'x' in token.lower() else int(token) for token in tokens]
        if columns > 1 and len(values) != columns:
            raise ValueError(('C initializer field count changed', symbol))
        rows.append(values)
    return rows if columns > 1 else rows[0]


def _define_integer(text, name):
    match = re.search(r'^\s*#define\s+'+re.escape(name)+r'\s+\(?([+-]?\d+)\)?\s*$', text, re.M)
    if not match:
        raise ValueError(('Missing literal C bound', name))
    return int(match[1])


class AtlasDiveSource:
    """Model the implemented tri-state resolver and its actual numeric tables.

    No JSON Dive/Emerge connection is added, required, or trusted. Surface
    owners come from the authenticated runtime C table; underwater coordinates
    come from the independent Depth-origin table. All destination words are
    read using their own source map's bank, just as the reviewed C helper does.
    """
    def __init__(self, source, graph, header):
        self.source, self.graph = source, graph
        runtime = source.read('src/data/journey_atlas_runtime.h').decode()
        overworld = source.read('src/overworld.c').decode()
        self.input_sha256 = {name: hashlib.sha256(text.encode()).hexdigest() for name,text in (
            ('src/data/journey_atlas_dives.h',header),
            ('src/data/journey_atlas_runtime.h',runtime),('src/overworld.c',overworld))}
        expected_struct = ('struct JourneyAtlasDiveSite { u16 depth; s16 x, y; u16 width, height; '
                           's16 left, top; u16 patchWidth, patchHeight; };')
        if _compact(expected_struct) not in _compact(header) or _compact(
                'struct JourneyAtlasChunk { u16 map; s16 x, y; u8 width, height; };') not in _compact(runtime):
            raise ValueError('Actual C Dive/chunk field layout changed')
        for name,expected in _DIVE_FUNCTIONS.items():
            text = header if name == 'JourneyAtlasDepthSite' else runtime if name in (
                'JourneyAtlasChunk','JourneyAtlasWorldChunk','JourneyAtlasFloor32') else overworld
            if hashlib.sha256(_compact(_function_body(text,name)).encode()).hexdigest() != expected:
                raise ValueError(('Implemented Dive arithmetic or rejection guard is unreviewed',name))
        predicates=source.read('src/metatile_behavior.c').decode()
        for name,expected in (
                ('MetatileBehavior_IsSurfableWaterOrUnderwater','c618a9a8b0f2670a63b262dba9d4785d363ca4ae98b16650748c55a2138affb1'),
                ('MetatileBehavior_IsDiveable','aa7ae21e5649102bce84b9a7e3975b02513b7f9290f10925fbe07c7697e3ea7a'),
                ('MetatileBehavior_IsUnableToEmerge','b6ea192a3b18de62dfab7b6e676939c42f1f005b8fa64eed7f0261e786148fc5')):
            if hashlib.sha256(_compact(_function_body(predicates,name)).encode()).hexdigest()!=expected:
                raise ValueError(('Native Dive callback semantics changed',name))
        config=source.read('include/config/general.h').decode()
        if not re.search(r'^\s*#define\s+BUGFIX\s*$',config,re.M) or re.search(r'^\s*#undef\s+BUGFIX\b',config,re.M):
            raise ValueError('Native UnableToEmerge BUGFIX configuration is unmodelled')
        hook = _compact(_function_body(overworld,'SetDiveWarp'))
        prefix = _compact('''const struct MapConnection *connection;
            s8 atlas = JourneyAtlasSetDiveWarp(dir, x, y);
            if (atlas >= 0) return atlas != 0;
            connection = GetMapConnection(dir);''')
        if not hook.startswith(prefix) or hook.count('JourneyAtlasSetDiveWarp(') != 1:
            raise ValueError('Tri-state Dive resolver must reject/resolve before legacy GetMapConnection')
        if '#include "data/journey_atlas_dives.h"' not in overworld or '#include "data/journey_atlas_runtime.h"' not in overworld:
            raise ValueError('Implemented overworld Dive hook does not include its actual tables')
        identities = getattr(source,'identities',None)
        if not identities or len(set(identities.values())) != len(identities):
            raise ValueError('Compiled map registry identities required for actual C Dive tables')
        by_identity = {value:name for name,value in identities.items()}
        self.chunks = []
        for identity,x,y,width,height in _literal_rows(runtime,'sAtlasChunks',5):
            name = by_identity.get(identity)
            if name is None or name not in source.maps or identity>>8 >= 128 or identity&255 >= 100:
                raise ValueError(('Atlas C owner has an invalid signed map identity',identity))
            layout = source.layout(name)
            if [width,height] != [layout['width'],layout['height']] or not 1 <= width <= 127 or not 1 <= height <= 127:
                raise ValueError(('Atlas C owner dimensions differ from source layout',name))
            if not (-32768 <= x <= 32767 and -32768 <= y <= 32767 and x+width <= 32768 and y+height <= 32768):
                raise ValueError(('Atlas C owner coordinate overflows its signed fields',name))
            self.chunks.append(dict(map=identity,name=name,x=x,y=y,width=width,height=height))
        if not self.chunks or len({c['map'] for c in self.chunks}) != len(self.chunks):
            raise ValueError('Atlas runtime C owners are empty or duplicated')
        for i,first in enumerate(self.chunks):
            for second in self.chunks[i+1:]:
                if (max(first['x'],second['x']) < min(first['x']+first['width'],second['x']+second['width'])
                        and max(first['y'],second['y']) < min(first['y']+first['height'],second['y']+second['height'])):
                    raise ValueError('Actual C runtime owners overlap')
        self._validate_indexes(runtime)
        self.by_name = {c['name']:c for c in self.chunks}
        self.sites = {}
        for identity,x,y,width,height,left,top,patch_width,patch_height in _literal_rows(header,'sAtlasDiveSites',9):
            name = by_identity.get(identity)
            if name is None or identity>>8 >= 128 or identity&255 >= 128 or name in self.sites:
                raise ValueError(('Depth C table has an unknown/duplicate signed map identity',identity))
            layout = source.layout(name)
            if source.maps[name].get('map_type') != 'MAP_TYPE_UNDERWATER' or [width,height] != [layout['width'],layout['height']]:
                raise ValueError(('Depth C table disagrees with its actual underwater layout',name))
            if not (1 <= width < 128 and 1 <= height < 128
                    and 0 < patch_width <= width and 0 < patch_height <= height
                    and -32768 <= x <= 32767 and -32768 <= y <= 32767
                    and -32768 <= left <= 32767 and -32768 <= top <= 32767
                    and x <= left and y <= top and left+patch_width <= x+width
                    and top+patch_height <= y+height):
                raise ValueError(('Depth C table coordinate bounds invalid',name))
            self.sites[name] = dict(name=name,map=identity,x=x,y=y,width=width,height=height,
                left=left,top=top,patch_width=patch_width,patch_height=patch_height)
        if not self.sites:
            raise ValueError('Actual C Dive site table is empty')
        sites=list(self.sites.values())
        for i,first in enumerate(sites):
            for second in sites[i+1:]:
                if (max(first['left'],second['left']) < min(first['left']+first['patch_width'],second['left']+second['patch_width'])
                        and max(first['top'],second['top']) < min(first['top']+first['patch_height'],second['top']+second['patch_height'])):
                    raise ValueError('Actual C Dive patch rectangles overlap')
        self.resolved_requirements=[]

    def _validate_indexes(self,runtime):
        groups,spatial={},{}
        for index,chunk in enumerate(self.chunks):
            group,number=chunk['map']>>8,chunk['map']&255
            groups.setdefault(group,{})[number]=index+1
            for row in range(chunk['y']//32,(chunk['y']+chunk['height']-1)//32+1):
                spatial.setdefault(row,[]).append(index)
        base,last=min(groups),max(groups);group_rows=[];slots=[]
        for group in range(base,last+1):
            members=groups.get(group,{})
            count=max(members)+1 if members else 0
            group_rows.append([len(slots),count]);slots.extend(members.get(n,0) for n in range(count))
        row_base,row_last=min(spatial),max(spatial);row_rows=[];row_chunks=[]
        for row in range(row_base,row_last+1):
            members=sorted(spatial.get(row,[]),key=lambda index:(self.chunks[index]['x'],index))
            row_rows.append([len(row_chunks),len(members),max((self.chunks[i]['width'] for i in members),default=0)])
            row_chunks.extend(members)
        expected=(('sAtlasGroups',2,group_rows),('sAtlasMapSlots',1,slots),
                  ('sAtlasRows',3,row_rows),('sAtlasRowChunks',1,row_chunks))
        for symbol,columns,values in expected:
            if _literal_rows(runtime,symbol,columns) != values:
                raise ValueError(('Actual C runtime owner index differs from real rectangles',symbol))
        for name,value in (('JOURNEY_ATLAS_GROUP_BASE',base),('JOURNEY_ATLAS_ROW_BASE',row_base),
                           ('JOURNEY_ATLAS_MIN_X',min(c['x'] for c in self.chunks)),
                           ('JOURNEY_ATLAS_MAX_X',max(c['x']+c['width'] for c in self.chunks))):
            if _define_integer(runtime,name) != value:
                raise ValueError(('Actual C runtime index bound changed',name))

    def owner(self,x,y):
        return next((c for c in self.chunks if c['x'] <= x < c['x']+c['width']
                     and c['y'] <= y < c['y']+c['height']),None)

    def surface_valid(self,name,x,y,require_dive=False):
        if name not in self.graph.by_name or self.source.maps[name].get('map_type') == 'MAP_TYPE_UNDERWATER':
            return False
        try:cell=self.graph.point([name,x,y])
        except ValueError:return False
        return (not self.graph.words[cell]&0xC00 and self.graph.words[cell]>>12==1
                and self.source.behavior(name,self.graph.words[cell])<=255
                and self.graph.water[cell] and (not require_dive or self.graph.behaviors[cell] in (
                    'MB_INTERIOR_DEEP_WATER','MB_DEEP_WATER','MB_SOOTOPOLIS_DEEP_WATER')))

    def depth_valid(self,name,x,y):
        if name not in self.graph.by_name or self.source.maps[name].get('map_type') != 'MAP_TYPE_UNDERWATER':
            return False
        try:cell=self.graph.point([name,x,y])
        except ValueError:return False
        return (not self.graph.words[cell]&0xC00 and self.graph.words[cell]>>12==3
                and self.source.behavior(name,self.graph.words[cell])<=255
                and self.graph.behaviors[cell] not in ('MB_NO_SURFACING','MB_SEAWEED_NO_SURFACING','MB_WATER_DOOR','UNKNOWN'))

    def descend(self,surface,x,y):
        chunk=self.by_name.get(surface)
        if chunk is None or not self.surface_valid(surface,x,y,True):return None
        gx,gy=chunk['x']+x,chunk['y']+y
        for site in self.sites.values():
            if site['left'] <= gx < site['left']+site['patch_width'] and site['top'] <= gy < site['top']+site['patch_height']:
                xx,yy=gx-site['x'],gy-site['y']
                return [site['name'],xx,yy] if self.depth_valid(site['name'],xx,yy) else None
        return None

    def emerge(self,depth,x,y):
        site=self.sites.get(depth)
        if site is None or not self.depth_valid(depth,x,y):return None
        gx,gy=site['x']+x,site['y']+y
        chunk=self.owner(gx,gy)
        if chunk is None:return None
        xx,yy=gx-chunk['x'],gy-chunk['y']
        return [chunk['name'],xx,yy] if self.surface_valid(chunk['name'],xx,yy) else None

    def add_edges(self):
        for site in self.sites.values():
            for gy in range(site['top'],site['top']+site['patch_height']):
                for gx in range(site['left'],site['left']+site['patch_width']):
                    chunk=self.owner(gx,gy)
                    if chunk is None:
                        self.graph.errors.append(dict(kind='atlas-dive-patch-owner-missing',depth=site['name'],global_tile=[gx,gy]))
                        continue
                    source=[chunk['name'],gx-chunk['x'],gy-chunk['y']]
                    destination=self.descend(*source)
                    if destination is None:
                        self.graph.errors.append(dict(kind='atlas-dive-patch-terrain-rejected',depth=site['name'],surface=source))
                    else:self.graph.dives.setdefault(self.graph.point(source),[]).append(self.graph.point(destination))
            if site['name'] not in self.graph.by_name:
                self.graph.errors.append(dict(kind='atlas-depth-outside-audited-scope',depth=site['name']))
                continue
            for y in range(site['height']):
                for x in range(site['width']):
                    destination=self.emerge(site['name'],x,y)
                    if destination is not None:
                        self.graph.dives.setdefault(self.graph.point([site['name'],x,y]),[]).append(self.graph.point(destination))

    def requirements(self,rows):
        covered=set()
        for row in rows:
            surface,depth=row.get('surface'),row.get('depth')
            resolved=[];valid=True
            if surface not in self.by_name or depth not in self.sites or not row.get('points'):
                self.graph.errors.append(dict(kind='atlas-dive-required-map-or-points-invalid',key=row.get('key')))
                self.resolved_requirements.append((row,[],False));continue
            covered.add(depth);site=self.sites[depth];chunk=self.by_name[surface]
            for field,actual in (('depth_origin',[site['x'],site['y']]),('surface_origin',[chunk['x'],chunk['y']])):
                if field in row and row[field] != actual:
                    valid=False;self.graph.errors.append(dict(kind='atlas-dive-required-origin-differs-from-c-table',key=row.get('key'),field=field))
            for point in row['points']:
                if len(point)!=2 or any(type(v) is not int or not 0<=v<128 for v in point):
                    valid=False;self.graph.errors.append(dict(kind='atlas-dive-required-point-bounds-invalid',key=row.get('key')));continue
                destination=self.descend(surface,*point)
                returned=self.emerge(*destination) if destination is not None else None
                source=[surface,*point]
                if destination is None or destination[0]!=depth or returned!=source:
                    valid=False;self.graph.errors.append(dict(kind='atlas-dive-required-transform-roundtrip-rejected',key=row.get('key'),surface=source,depth=destination,returned=returned))
                else:resolved.append((source,destination))
            self.resolved_requirements.append((row,resolved,valid and len(resolved)==len(row['points'])))
        for depth in self.sites.keys()-covered:
            self.graph.pending.append(dict(kind='final-atlas-dive-site-uncovered',depth=depth))


def elevation_step(current, old_word, new_word):
    """Mirror mismatch and ObjectEventUpdateElevation, including bridge carry.

    Height zero is a genuine transition. Height fifteen retains the avatar's
    effective elevation; it cannot alone join height-one and height-three seas.
    """
    old, new = old_word >> 12, new_word >> 12
    if current != 0 and new not in (0, 15, current):
        return None
    return current if old == 15 or new == 15 else new


def _behavior_names(source):
    """Compile the real enum, including comments/expressions and FRLG entries."""
    if hasattr(source, 'behavior_names'):
        return source.behavior_names
    header = source.read('include/constants/metatile_behaviors.h').decode()
    clean = re.sub(r'/\*.*?\*/|//[^\n]*', '', header, flags=re.S)
    names = sorted(set(re.findall(r'\bMB_[A-Z0-9_]+\b', clean)))
    compiler = shutil.which('cc') or shutil.which('gcc')
    if not compiler:
        raise RuntimeError('C compiler required to authenticate native behavior enum')
    code = '#include <stdio.h>\n#include <limits.h>\n' + header + '\nint main(void){\n'
    code += ''.join(f'printf("{name}=%u\\n", (unsigned){name});\n' for name in names)
    code += 'return 0;}\n'
    with tempfile.TemporaryDirectory(prefix='atlas-reachability-enum-') as temporary:
        binary = Path(temporary) / 'enum'
        subprocess.run([compiler, '-std=gnu17', '-Wall', '-Werror', '-x', 'c', '-', '-o', str(binary)],
                       input=code, text=True, capture_output=True, check=True)
        output = subprocess.check_output([str(binary)], text=True)
    return {int(value): name for name, value in (line.split('=') for line in output.splitlines())}


def _scc(offsets, edges):
    """Iterative Kosaraju with compact CSR arrays; no recursive tile DFS."""
    count = len(offsets) - 1
    seen, order = bytearray(count), array('I')
    for root in range(count):
        if seen[root]:
            continue
        seen[root] = 1
        stack = [(root, offsets[root])]
        while stack:
            node, at = stack[-1]
            if at == offsets[node + 1]:
                order.append(node)
                stack.pop()
            else:
                stack[-1] = node, at + 1
                target = edges[at]
                if not seen[target]:
                    seen[target] = 1
                    stack.append((target, offsets[target]))
    sizes = array('I', [0]) * count
    for target in edges:
        sizes[target] += 1
    reverse_offsets = array('I', [0])
    for size in sizes:
        reverse_offsets.append(reverse_offsets[-1] + size)
    cursor = array('I', reverse_offsets[:-1])
    reverse = array('I', [0]) * len(edges)
    for node in range(count):
        for at in range(offsets[node], offsets[node + 1]):
            target = edges[at]
            reverse[cursor[target]] = node
            cursor[target] += 1
    labels = array('i', [-1]) * count
    component = 0
    for root in reversed(order):
        if labels[root] >= 0:
            continue
        labels[root] = component
        stack = [root]
        while stack:
            node = stack.pop()
            for at in range(reverse_offsets[node], reverse_offsets[node + 1]):
                target = reverse[at]
                if labels[target] < 0:
                    labels[target] = component
                    stack.append(target)
        component += 1
    return labels, component


class PhysicalGraph:
    """A bounded physical scope; map metadata and plan GPS never create edges."""
    def __init__(self, source, map_names, *, max_states=1000000, bank_witnesses=(), origins=None):
        self.source = source
        self.names = sorted(set(map_names))
        self.errors, self.pending = [], []
        self.by_name, self.cells, self.bases, self.map_at = {}, [], [], []
        self.words, self.water, self.behaviors = array('H'), bytearray(), []
        self.warps, self.dives = {}, {}
        self.max_states = max_states
        self.behavior_names = _behavior_names(source)
        self.banks = {tuple(row) for row in bank_witnesses}
        self.origins = origins or {}
        self.unmodelled = Counter()
        if sum(source.layout(name)['width'] * source.layout(name)['height'] for name in self.names) > 2 * max_states:
            raise ValueError('Physical terrain budget exceeded; narrow audited scope')
        for index, name in enumerate(self.names):
            if name not in source.maps:
                raise ValueError(('Unknown physical map', name))
            layout = source.layout(name)
            self.by_name[name] = index
            self.bases.append(len(self.words))
            self.cells.append(layout['width'] * layout['height'])
            for y in range(layout['height']):
                for x in range(layout['width']):
                    word = source.word(name, x, y)
                    self.words.append(word)
                    self.water.append(bool(source.water(name, x, y)))
                    self.behaviors.append(self.behavior_names.get(source.behavior(name, word), 'UNKNOWN'))
                    self.map_at.append(index)
        self.connections = {}
        self.connection_witnesses = []
        self._connections()
        self._warps()

    def point(self, point):
        name, x, y = point
        if name not in self.by_name:
            raise ValueError(('Point outside audited physical scope', point))
        row = self.source.layout(name)
        if not (type(x) is int and type(y) is int and 0 <= x < row['width'] and 0 <= y < row['height']):
            raise ValueError(('Point outside source layout', point))
        return self.bases[self.by_name[name]] + y * row['width'] + x

    def location(self, cell):
        index = self.map_at[cell]
        name = self.names[index]
        local = cell - self.bases[index]
        return name, local % self.source.layout(name)['width'], local // self.source.layout(name)['width']

    def banks_match(self, first, second):
        a, b = self.source.layout(first), self.source.layout(second)
        keys = ('primary_tileset', 'secondary_tileset', 'layout_version')
        return (all(a.get(key) == b.get(key) for key in keys)
                or (first, second) in self.banks)

    def _connections(self):
        for name in self.names:
            row = self.source.layout(name)
            for link in self.source.maps[name].get('connections') or []:
                direction = link['direction']
                if direction not in DIRS:
                    continue
                target = self.source.by_id.get(link['map'])
                if target not in self.by_name:
                    continue
                offset = int(link['offset'])
                other = self.source.layout(target)
                reverse = [edge for edge in self.source.maps[target].get('connections') or []
                           if edge['direction'] == OPPOSITE[direction]
                           and edge['map'] == self.source.maps[name]['id']
                           and int(edge['offset']) == -offset]
                if len(reverse) != 1:
                    self.errors.append(dict(kind='nonreciprocal-connection', map=name, target=target,
                                            direction=direction, offset=offset))
                bank_ok = self.banks_match(name, target)
                if not bank_ok:
                    self.pending.append(dict(kind='bank-translation-unproven', map=name, target=target))
                axis = 'height' if direction in ('left', 'right') else 'width'
                pairs = 0
                for value in range(max(0, offset), min(row[axis], offset + other[axis])):
                    if direction in ('left', 'right'):
                        a = [name, row['width'] - 1 if direction == 'right' else 0, value]
                        b = [target, 0 if direction == 'right' else other['width'] - 1, value - offset]
                    else:
                        a = [name, value, row['height'] - 1 if direction == 'down' else 0]
                        b = [target, value - offset, 0 if direction == 'down' else other['height'] - 1]
                    first, second = self.point(a), self.point(b)
                    if name in self.origins and target in self.origins:
                        before, after = self.origins[name], self.origins[target]
                        dx, dy = DIRS[direction]
                        if (after[0] + b[1] - before[0] - a[1],
                                after[1] + b[2] - before[1] - a[2]) != (dx, dy):
                            # This is a rejection check, never a synthetic edge.
                            self.errors.append(dict(kind='nonaffine-physical-connection', map=name,
                                target=target, direction=direction, source_tile=a[1:], target_tile=b[1:]))
                            break
                    if bank_ok:
                        key = first, direction
                        if key in self.connections and self.connections[key] != second:
                            self.errors.append(dict(kind='ambiguous-boundary-owner', map=name, tile=a[1:]))
                        else:
                            self.connections[key] = second
                    if self.water[first] and self.water[second] and not self.words[first] & 0xC00 and not self.words[second] & 0xC00:
                        if elevation_step(self.words[first] >> 12, self.words[first], self.words[second]) is not None:
                            pairs += 1
                self.connection_witnesses.append(dict(map=name, target=target, direction=direction,
                    offset=offset, reciprocal=len(reverse) == 1, compatible_water_pairs=pairs, banks_checked=bank_ok))

    def _warps(self):
        for name in self.names:
            for number, event in enumerate(self.source.maps[name].get('warp_events') or []):
                target = self.source.by_id.get(event['dest_map'])
                if target not in self.by_name:
                    continue
                try:
                    index = int(event['dest_warp_id'])
                    events = self.source.maps[target].get('warp_events') or []
                    if not 0 <= index < len(events):
                        raise ValueError('warp index')
                    destination = events[index]
                    a = self.point([name, event['x'], event['y']])
                    b = self.point([target, destination['x'], destination['y']])
                except (ValueError, KeyError, TypeError):
                    self.errors.append(dict(kind='invalid-directed-warp', map=name, warp=number))
                    continue
                if not any(tag in self.behaviors[a] for tag in ('WARP', 'DOOR', 'LADDER', 'ESCALATOR')):
                    self.pending.append(dict(kind='warp-activation-unmodelled', map=name, warp=number,
                                             behavior=self.behaviors[a]))
                    continue
                self.warps.setdefault(a, []).append((b, int(event.get('elevation', 0))))

    def passable(self, cell):
        if self.words[cell] & 0xC00:
            return False
        behavior = self.behaviors[cell]
        # Conservative: do not turn a current/ledge/forced floor into a
        # bidirectional edge merely because its collision bits are zero.
        if any(tag in behavior for tag in ('JUMP', 'SLIDE', 'WALK_', 'CURRENT', 'STAIRS', 'ICE', 'UNKNOWN')):
            self.unmodelled[behavior] += 1
            return False
        return True

    def step_cell(self, cell, direction):
        name, x, y = self.location(cell)
        dx, dy = DIRS[direction]
        row = self.source.layout(name)
        if 0 <= x + dx < row['width'] and 0 <= y + dy < row['height']:
            return cell + dx + dy * row['width']
        return self.connections.get((cell, direction))

    def seed(self, cell, mode=None, elevation=None):
        if not self.passable(cell):
            return None
        height = self.words[cell] >> 12
        if mode is None:
            mode = int(bool(self.water[cell]))
        if elevation is None:
            elevation = (1 if mode else 3) if height == 15 else height
        return cell * 32 + mode * 16 + elevation

    def successors(self, key):
        cell, state = divmod(key, 32)
        mode, current = divmod(state, 16)
        for direction in DIRS:
            target = self.step_cell(cell, direction)
            if target is None or not self.passable(target):
                continue
            sides = {'left': 'WEST', 'right': 'EAST', 'up': 'NORTH', 'down': 'SOUTH'}
            old_behavior, behavior = self.behaviors[cell], self.behaviors[target]
            if (('IMPASSABLE' in old_behavior and sides[direction] in old_behavior)
                    or ('IMPASSABLE' in behavior and sides[OPPOSITE[direction]] in behavior)
                    or (direction in ('left', 'right') and 'MB_SECRET_BASE_BREAKABLE_DOOR' in (old_behavior, behavior))):
                continue
            height = self.words[target] >> 12
            next_mode = mode
            if mode and not self.water[target] and height != 15:
                if height != 3:
                    continue
                next_mode, elevation = 0, 3  # native CanStopSurfing
            elif not mode and self.water[target] and height != 15:
                if current != 3 or height != 1:
                    continue
                next_mode, elevation = 1, 1  # explicit Surf action, party/gates assumed
            else:
                elevation = elevation_step(current, self.words[cell], self.words[target])
                if elevation is None:
                    continue
            yield target * 32 + next_mode * 16 + elevation
        for target, event_height in self.warps.get(cell, ()):
            if event_height != 0 and current != 0 and event_height != current:
                continue
            seed = self.seed(target)
            if seed is not None:
                yield seed
        for target in self.dives.get(cell, ()):
            seed = self.seed(target)
            if seed is not None:
                yield seed

    def compile(self):
        keys, index = array('Q'), {}
        def add(key):
            if key not in index:
                if len(keys) >= self.max_states:
                    raise ValueError('Physical graph state budget exceeded; narrow audited scope')
                index[key] = len(keys)
                keys.append(key)
            return index[key]
        for cell in range(len(self.words)):
            key = self.seed(cell)
            if key is not None:
                add(key)
                if self.words[cell] >> 12 == 15:
                    add(self.seed(cell, 1, 1))
                    add(self.seed(cell, 0, 3))
        offsets, edges = array('I', [0]), array('I')
        node = 0
        while node < len(keys):
            for target in set(self.successors(keys[node])):
                edges.append(add(target))
            offsets.append(len(edges))
            node += 1
        labels, count = _scc(offsets, edges)
        self.keys, self.index, self.labels = keys, index, labels
        return dict(states=len(keys), edges=len(edges), strong_components=count,
                    graph_array_bytes=sum(a.itemsize * len(a) for a in (keys, offsets, edges, labels)))

    def component(self, point, mode=None):
        cell = self.point(point)
        key = self.seed(cell, mode)
        return self.labels[self.index[key]] if key is not None and key in self.index else None


def _points(requirements):
    for kind in KINDS:
        for row in requirements.get(kind, []):
            for field in ('dry', 'water', 'point', 'surface_point', 'depth_point'):
                if row.get(field):
                    yield row[field]


def audit(source, *, plan, requirements=None, strict=False, max_states=1000000, return_graph=False):
    """Return source-only SCC evidence; missing final mappings are explicit.

    Requirements use final coordinates: ports{dry,water}; caves{surface,
    surface_warp,interior,interior_warp}; dives{surface,depth,points:[[x,y]]};
    adapters{point}; native_pixels{point,atlas,authenticated}. Each point is
    [map,x,y]. ``complete`` must authenticate the final obligation inventory.
    No historical-inventory fallback is performed. ``return_graph=True``
    returns (report, graph); ecology can require graph.component(point) ==
    graph.ocean_component before counting a real encounter trigger.
    """
    if isinstance(source, (str, Path)):
        source = Source(source)
    requirements = requirements or {}
    names = {chunk['name'] for chunk in plan['chunks']}
    names.update(requirements.get('transit_maps', []))
    names.update(point[0] for point in _points(requirements))
    for kind in ('caves', 'dives'):
        for row in requirements.get(kind, []):
            names.update(row[key] for key in ('surface', 'interior', 'depth') if row.get(key))
    atlas_header=None;atlas_header_error=None
    if hasattr(source,'read'):
        try:atlas_header=source.read('src/data/journey_atlas_dives.h').decode()
        except FileNotFoundError:pass
        if atlas_header is not None:
            try:
                by_identity={value:name for name,value in getattr(source,'identities',{}).items()}
                names.update(by_identity[row[0]] for row in _literal_rows(atlas_header,'sAtlasDiveSites',9)
                             if row[0] in by_identity)
            except ValueError as error:atlas_header_error=str(error)
    origins = dict(requirements.get('physical_origins', {}))
    origins.update({row['name']: row['origin'] for row in plan['chunks'] if 'origin' in row})
    graph = PhysicalGraph(source, names, max_states=max_states,
                          bank_witnesses=requirements.get('authenticated_bank_pairs', []), origins=origins)
    if not requirements.get('complete'):
        graph.pending.append(dict(kind='final-obligation-inventory-not-authenticated'))
    for kind in KINDS:
        if kind not in requirements:
            graph.pending.append(dict(kind='final-mapping-missing', category=kind))
    atlas_model=None
    if atlas_header is not None:
        try:
            if atlas_header_error:raise ValueError(atlas_header_error)
            atlas_model=AtlasDiveSource(source,graph,atlas_header)
            atlas_model.add_edges()
            atlas_model.requirements(requirements.get('dives',[]))
        except ValueError as error:
            graph.errors.append(dict(kind='atlas-dive-source-contract-invalid',detail=str(error)))
    elif any(row.get('model')=='atlas-affine' for row in requirements.get('dives',[])):
        graph.errors.append(dict(kind='atlas-dive-c-header-missing'))
    for row in requirements.get('dives', []) if atlas_header is None else []:
        surface, depth = row.get('surface'), row.get('depth')
        if not surface or not depth or not row.get('points'):
            graph.pending.append(dict(kind='final-dive-coordinates-missing', key=row.get('key')))
            continue
        down = [edge for edge in source.maps[surface].get('connections') or []
                if edge['direction'] == 'dive' and edge['map'] == source.maps[depth]['id'] and int(edge['offset']) == 0]
        up = [edge for edge in source.maps[depth].get('connections') or []
              if edge['direction'] == 'emerge' and edge['map'] == source.maps[surface]['id'] and int(edge['offset']) == 0]
        if len(down) != 1 or len(up) != 1:
            graph.errors.append(dict(kind='dive-coordinate-link-not-reciprocal', surface=surface, depth=depth))
            continue
        for x, y in row['points']:
            a, b = graph.point([surface, x, y]), graph.point([depth, x, y])
            if not graph.water[a] or not graph.passable(b):
                graph.errors.append(dict(kind='dive-terrain-blocked', surface=surface, depth=depth, tile=[x, y]))
                continue
            if source.maps[depth].get('map_type') != 'MAP_TYPE_UNDERWATER':
                graph.errors.append(dict(kind='dive-destination-is-not-underwater', surface=surface, depth=depth))
                continue
            if graph.behaviors[a] not in ('MB_INTERIOR_DEEP_WATER', 'MB_DEEP_WATER', 'MB_SOOTOPOLIS_DEEP_WATER'):
                graph.pending.append(dict(kind='dive-activation-behavior-unproven', surface=surface, tile=[x, y]))
                continue
            if graph.behaviors[b] in ('MB_NO_SURFACING', 'MB_SEAWEED_NO_SURFACING', 'MB_WATER_DOOR'):
                graph.errors.append(dict(kind='emerge-behavior-blocked', depth=depth, tile=[x, y]))
                continue
            graph.dives.setdefault(a, []).append(b)
            graph.dives.setdefault(b, []).append(a)
    metrics = graph.compile()
    generated = set()
    generated_cells = 0
    for chunk in plan['chunks']:
        name = chunk['name']
        layout = source.layout(name)
        chunk_water = 0
        for y in range(layout['height']):
            for x in range(layout['width']):
                cell = graph.point([name, x, y])
                if graph.water[cell]:
                    chunk_water += 1
                    component = graph.component([name, x, y], 1)
                    if component is not None:
                        generated.add(component)
                        generated_cells += 1
                    else:
                        graph.errors.append(dict(kind='generated-water-state-unmodelled', map=name, tile=[x, y]))
        if not chunk_water:
            graph.errors.append(dict(kind='generated-chunk-has-no-physical-water', map=name))
    if not generated:
        graph.errors.append(dict(kind='no-generated-physical-water'))
    elif len(generated) != 1:
        graph.errors.append(dict(kind='generated-water-not-strongly-connected', components=len(generated)))
    ocean = next(iter(generated)) if len(generated) == 1 else None
    graph.ocean_component = ocean
    checks = {kind: [] for kind in KINDS}
    for row in requirements.get('ports', []):
        if not row.get('dry') or not row.get('water'):
            graph.pending.append(dict(kind='final-port-mapping-missing', key=row.get('key')))
            continue
        dry, wet = graph.point(row['dry']), graph.point(row['water'])
        a, b = graph.component(row['dry'], 0), graph.component(row['water'], 1)
        terrain = (graph.words[dry] >> 12 == 3 and not graph.water[dry]
                   and graph.words[wet] >> 12 == 1 and graph.water[wet]
                   and graph.passable(dry) and graph.passable(wet))
        passed = terrain and a is not None and a == b == ocean
        checks['ports'].append(dict(key=row.get('key'), passed=passed, dry_component=a, water_component=b,
                                    dry_height=graph.words[dry] >> 12, water_height=graph.words[wet] >> 12))
        if not passed:
            graph.errors.append(dict(kind='port-dry-surf-roundtrip-failed', key=row.get('key')))
    for row in requirements.get('caves', []):
        required = ('surface', 'surface_warp', 'interior', 'interior_warp')
        if any(key not in row for key in required):
            graph.pending.append(dict(kind='final-cave-mapping-missing', key=row.get('key')))
            continue
        events = []
        valid = True
        for name_key, warp_key, other_key, other_warp in (
                ('surface', 'surface_warp', 'interior', 'interior_warp'),
                ('interior', 'interior_warp', 'surface', 'surface_warp')):
            rows = source.maps[row[name_key]].get('warp_events') or []
            index = row[warp_key]
            if not isinstance(index, int) or not 0 <= index < len(rows):
                valid = False
                break
            event = rows[index]
            valid &= (event['dest_map'] == source.maps[row[other_key]]['id']
                      and str(event['dest_warp_id']) == str(row[other_warp]))
            events.append([row[name_key], event['x'], event['y']])
        components = [graph.component(point) for point in events]
        passed = valid and len(components) == 2 and all(c is not None and c == ocean for c in components)
        checks['caves'].append(dict(key=row.get('key'), passed=passed, components=components,
                                   interior_height_three_not_required=True))
        if not passed:
            graph.errors.append(dict(kind='cave-directed-warp-roundtrip-failed', key=row.get('key')))
    for kind in ('adapters', 'native_pixels'):
        for row in requirements.get(kind, []):
            if not row.get('point'):
                graph.pending.append(dict(kind='final-point-mapping-missing', category=kind, key=row.get('key')))
                continue
            if kind == 'native_pixels' and not row.get('authenticated'):
                graph.pending.append(dict(kind='native-pixel-not-authenticated', key=row.get('key')))
                continue
            if kind == 'native_pixels':
                name, x, y = row['point']
                origin = origins.get(name)
                if origin is None or not row.get('atlas'):
                    graph.pending.append(dict(kind='native-pixel-physical-binding-missing', key=row.get('key')))
                    continue
                physical_pixel = [(origin[0] + x) // 8, (origin[1] + y) // 8]
                if physical_pixel != row['atlas']:
                    graph.errors.append(dict(kind='native-pixel-physical-binding-mismatch', key=row.get('key'),
                                             physical_atlas=physical_pixel, required_atlas=row['atlas']))
                    continue
            component = graph.component(row['point'], 1)
            passed = component is not None and component == ocean
            checks[kind].append(dict(key=row.get('key'), passed=passed, component=component))
            if not passed:
                graph.errors.append(dict(kind='required-physical-point-unreachable', category=kind, key=row.get('key')))
    if atlas_header is not None:
        for row,resolved,valid in atlas_model.resolved_requirements if atlas_model is not None else []:
            components=[graph.component(point) for pair in resolved for point in pair]
            passed=valid and bool(resolved) and all(c is not None and c==ocean for c in components)
            checks['dives'].append(dict(key=row.get('key'),passed=passed,components=components,
                model='actual-C-table-affine-tri-state',resolved_points=[dict(surface=a,depth=b) for a,b in resolved],
                identical_source_and_depth_coordinates=False,legacy_json_links_required=False))
            if not passed:graph.errors.append(dict(kind='dive-emerge-roundtrip-failed',key=row.get('key')))
    for row in requirements.get('dives', []) if atlas_header is None else []:
        points = row.get('points', [])
        components = [graph.component([row[side], x, y]) for side in ('surface', 'depth')
                      for x, y in points if row.get(side)]
        passed = bool(points) and all(c is not None and c == ocean for c in components)
        checks['dives'].append(dict(key=row.get('key'), passed=passed, components=components,
                                   identical_source_and_depth_coordinates=True))
        if points and not passed:
            graph.errors.append(dict(kind='dive-emerge-roundtrip-failed', key=row.get('key')))
    if hasattr(source, 'assert_unchanged'):
        source.assert_unchanged()
    result = dict(kind='atlas-source-physical-reachability', passed=not graph.errors and not graph.pending,
                  source_only=True, compiled_rom_validated=False, native_controller_validated=False,
                  gps_used_for_edges=False, plan_connections_trusted=False,
                  physical_maps=len(names), generated_water_cells=generated_cells,
                  generated_water_sccs=len(generated), metrics=metrics,
                  checks=checks, errors=graph.errors, pending=graph.pending,
                  connections=graph.connection_witnesses,
                  dive_resolution_model='actual-C-table-affine-tri-state' if atlas_header is not None else 'legacy-native-json-connections',
                  dive_source_contract=(dict(table_sha256=atlas_model.input_sha256,
                      depth_sites=list(atlas_model.sites.values()),runtime_owners=len(atlas_model.chunks),
                      tri_state_hook_precedes_legacy_lookup=True,actual_runtime_indexes_checked=True,
                      native_dive_avatar_and_effect_not_certified=True) if atlas_model is not None else None),
                  unmodelled_behavior_blockers=dict(graph.unmodelled),
                  input_sha256=dict(getattr(source, 'inputs', {})),
                  limitations=['party/HM/story access prerequisites assumed',
                               'moving actors and script-conditioned collision require native checks',
                               'warp spawn offsets and activation frames require native controller checks'])
    if strict and not result['passed']:
        raise AssertionError(('Physical source reachability failed', graph.errors, graph.pending))
    return (result, graph) if return_graph else result
