"""Read immutable native terrain and compile its real behavior enum/flags.

Used by source planning inventories. No source writes, guessed enum values,
universal metatile IDs, GPS interpolation or ROM certification live here.
"""
from collections import deque
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile


CARDINAL = {'left': (-1, 0), 'right': (1, 0), 'up': (0, -1), 'down': (0, 1)}
OPPOSITE = {'left': 'right', 'right': 'left', 'up': 'down', 'down': 'up'}
POINT = re.compile(r'\{\(MAP_GROUP\((MAP_\w+)\)<<8\)\|MAP_NUM\(\1\), '
                   r'(MAPSEC_\w+), (\d+), (\d+), COMPOUND_STRING\("([^"]+)"\)\}')


def compatible_height(first, second):
    a, b = first >> 12, second >> 12
    return a == b or a in (0, 15) or b in (0, 15)


class Source:
    def __init__(self, source):
        self.source = Path(source).resolve()
        self.inputs, self._words, self._attrs, self._components = {}, {}, {}, {}
        self._flags = None
        self.layouts = {row['id']: row for row in self.js('data/layouts/layouts.json')['layouts']}
        self.groups = self.js('data/maps/map_groups.json')
        self.identities = {}
        for group, label in enumerate(self.groups['group_order']):
            if group > 255:
                raise ValueError('Map group exceeds native byte identity')
            for number, name in enumerate(self.groups[label]):
                if name in self.identities or number > 255:
                    raise ValueError(('Invalid or duplicate native map identity', name))
                self.identities[name] = (group << 8) | number
        self.maps = {p.parent.name: self.js(p.relative_to(self.source).as_posix())
                     for p in sorted((self.source/'data/maps').glob('*/map.json'))}
        self.by_id = {}
        for name, row in self.maps.items():
            if row['id'] in self.by_id:
                raise ValueError(('Duplicate map constant', row['id']))
            self.by_id[row['id']] = name

    def read(self, name):
        path = Path(name)
        if path.is_absolute() or '..' in path.parts or '\\' in str(name):
            raise ValueError(('Unsafe source path', str(name)))
        raw = (self.source/path).read_bytes()
        value = hashlib.sha256(raw).hexdigest()
        if name in self.inputs and self.inputs[name] != value:
            raise ValueError(('Source changed while planning', name))
        self.inputs[name] = value
        return raw

    def js(self, name):
        return json.loads(self.read(name))

    def assert_unchanged(self):
        for name, expected in list(self.inputs.items()):
            if hashlib.sha256((self.source/name).read_bytes()).hexdigest() != expected:
                raise ValueError(('Source changed while planning', name))
        return len(self.inputs)

    def layout(self, name):
        return self.layouts[self.maps[name]['layout']]

    def words(self, name):
        row = self.layout(name)
        path = row['blockdata_filepath']
        if path not in self._words:
            raw = self.read(path)
            if len(raw) != 2*row['width']*row['height']:
                raise ValueError(('Blockdata does not match layout dimensions', name))
            self._words[path] = struct.unpack('<'+'H'*(len(raw)//2), raw)
        return self._words[path]

    def word(self, name, x, y):
        row = self.layout(name)
        if not (0 <= x < row['width'] and 0 <= y < row['height']):
            raise ValueError(('Cell outside native map', name, x, y))
        return self.words(name)[y*row['width']+x]

    def behavior(self, name, word):
        row = self.layout(name)
        cutoff, size = (640, 4) if row['layout_version'] == 'frlg' else (512, 2)
        mid = word & 1023
        bank = row['primary_tileset'] if mid < cutoff else row['secondary_tileset']
        key = bank, size
        if key not in self._attrs:
            headers = self.read('src/data/tilesets/headers.h').decode()
            defs = self.read('src/data/tilesets/metatiles.h').decode()
            body = re.search(r'const struct Tileset '+re.escape(bank)+r'\s*=\s*\{(.*?)\};', headers, re.S)
            if body is None:
                raise ValueError(('Unknown native tileset', bank))
            symbol = re.search(r'\.metatileAttributes\s*=\s*(\w+)', body[1])[1]
            definition = re.search(r'\b'+re.escape(symbol)+r'\[\].*?"([^"]+)"', defs)
            if definition is None:
                raise ValueError(('Missing native attribute definition', bank))
            raw = self.read(definition[1])
            if len(raw) % size:
                raise ValueError(('Truncated native attribute table', bank))
            self._attrs[key] = [int.from_bytes(raw[i:i+size], 'little') & (511 if size == 4 else 255)
                                for i in range(0, len(raw), size)]
        index = mid if mid < cutoff else mid-cutoff
        if index >= len(self._attrs[key]):
            raise ValueError(('Metatile outside its bank attribute table', name, mid, bank))
        return self._attrs[key][index]

    @property
    def behavior_flags(self):
        if self._flags is None:
            compiler = shutil.which('cc') or shutil.which('gcc')
            if compiler is None:
                raise RuntimeError('Host C compiler required; do not guess native enum values')
            enum_path = 'include/constants/metatile_behaviors.h'
            self.read(enum_path)
            text = self.read('src/metatile_behavior.c').decode()
            definitions = '\n'.join(re.findall(r'^#define\s+TILE_FLAG_\w+[^\n]*', text, re.M))
            table = re.search(r'static const u8 sTileBitAttributes\s*\[[^]]+\]\s*=\s*\{.*?\};', text, re.S)
            if table is None or not definitions:
                raise ValueError('Native behavior flags or initializer missing')
            code = ('#include <stdint.h>\n#include <stdio.h>\n'
                    '#include "constants/metatile_behaviors.h"\n'
                    'typedef uint8_t u8;\n'+definitions+'\n'+table[0]+'\n'
                    'int main(void) { putchar(TILE_FLAG_SURFABLE); putchar(TILE_FLAG_HAS_ENCOUNTERS); '
                    'return fwrite(sTileBitAttributes,1,sizeof(sTileBitAttributes),stdout) != sizeof(sTileBitAttributes); }\n')
            with tempfile.TemporaryDirectory(prefix='atlas-native-behaviors-') as temporary:
                executable = Path(temporary)/'flags'
                subprocess.run([compiler, '-std=gnu17', '-Wall', '-Wextra', '-Werror',
                                '-iquote', str(self.source/'include'), '-x', 'c', '-', '-o', str(executable)],
                               input=code, text=True, check=True, capture_output=True)
                raw = subprocess.check_output([str(executable)])
            if not 2 < len(raw) <= 514 or not raw[0] or not raw[1] or raw[0] == raw[1]:
                raise ValueError('Invalid compiled native behavior table')
            self._flags = dict(surf_flag=raw[0], encounter_flag=raw[1], values=raw[2:])
        return self._flags

    def water(self, name, x, y):
        word = self.word(name, x, y)
        if word & 0xC00:
            return False
        behavior = self.behavior(name, word)
        flags = self.behavior_flags
        if behavior >= len(flags['values']):
            raise ValueError(('Behavior outside compiled native enum', name, behavior))
        return bool(flags['values'][behavior] & flags['surf_flag'])

    def water_components(self, name):
        """Strict four-neighbor water components, preserving native 0/15 transitions.

        These are local terrain components, not a controller-travel certificate.
        Bridge-specific runtime paths remain a separate audit requirement.
        """
        if name not in self._components:
            row = self.layout(name)
            remaining = {(x, y) for y in range(row['height']) for x in range(row['width'])
                         if self.water(name, x, y)}
            labels, components = {}, []
            while remaining:
                seed = min(remaining, key=lambda p: (p[1], p[0]))
                queue = deque([seed]); remaining.remove(seed)
                cells = []
                while queue:
                    point = queue.popleft(); labels[point] = len(components); cells.append(point)
                    a = self.word(name, *point)
                    for dx, dy in CARDINAL.values():
                        target = point[0]+dx, point[1]+dy
                        if target in remaining and compatible_height(a, self.word(name, *target)):
                            remaining.remove(target); queue.append(target)
                components.append(cells)
            self._components[name] = labels, components
        return self._components[name]

    def anchors(self):
        header = self.read('src/data/journey_world_map.h').decode()
        result = {}
        for match in POINT.finditer(header):
            name = self.by_id.get(match[1])
            if name is None:
                continue
            value = dict(atlas=[int(match[3]), int(match[4])], section=match[2], label=match[5])
            if name in result and result[name] != value:
                raise ValueError(('Conflicting fixed map anchors', name))
            result[name] = value
        return result
