"""Read one frozen in-memory candidate through the same native Source API.

No staged file is written merely to run an independent source audit. A new
view is required after changing the overlay; mutation of a read input fails.
"""
import hashlib
import json
from pathlib import Path
import re

from atlas_surf_source import Source
from badge_story_layer import read


class OverlaySource(Source):
    def __init__(self, layer):
        self.layer=layer
        registry_path='data/maps/map_groups.json'
        original_raw=(Path(layer.source)/registry_path).read_bytes()
        if hashlib.sha256(original_raw).hexdigest()!=layer.expected[registry_path]:
            raise ValueError('Historical map registry changed behind the candidate overlay')
        original_registry=json.loads(original_raw)
        original_ids={name:(group<<8)|number
                      for group,label in enumerate(original_registry['group_order'])
                      for number,name in enumerate(original_registry[label])}
        super().__init__(layer.source)
        original_names=set(self.maps)
        for name,identity in original_ids.items():
            if self.identities.get(name)!=identity:
                raise ValueError(('Candidate changed a historical compiled map identity',name))
        for path in sorted(layer.outputs):
            match=re.fullmatch(r'data/maps/([^/]+)/map.json',path)
            if match:
                self.maps[match[1]]=self.js(path)
        self.by_id={}
        for name,row in self.maps.items():
            if row['id'] in self.by_id:
                raise ValueError(('Duplicate staged map constant',row['id']))
            # Upstream contains unused map JSONs without compiled IDs. Keep
            # them as source records; never invent a registry identity. Only
            # newly introduced maps must be registered by this overlay.
            if name not in self.identities and name not in original_names:
                raise ValueError(('Staged map missing from compiled registry',name))
            self.by_id[row['id']]=name

    def read(self, name):
        name=str(name);path=Path(name)
        if path.is_absolute() or '..' in path.parts or '\\' in name:
            raise ValueError(('Unsafe staged source path',name))
        raw=read(self.layer,name)
        value=hashlib.sha256(raw).hexdigest()
        if name in self.inputs and self.inputs[name]!=value:
            raise ValueError(('Candidate overlay changed while auditing',name))
        self.inputs[name]=value
        return raw

    def assert_unchanged(self):
        for name,expected in list(self.inputs.items()):
            if hashlib.sha256(read(self.layer,name)).hexdigest()!=expected:
                raise ValueError(('Candidate overlay changed while auditing',name))
        return len(self.inputs)

    @property
    def behavior_flags(self):
        # The host compiler includes the immutable native enum from disk.
        # Reject an overlay which changes that include behind the compiler.
        name='include/constants/metatile_behaviors.h'
        if name in self.layer.outputs and self.layer.outputs[name]!=(self.source/name).read_bytes():
            raise ValueError('Staged behavior enums need an isolated native compiler snapshot')
        return super().behavior_flags
