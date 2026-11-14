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
        super().__init__(layer.source)
        for path in sorted(layer.outputs):
            match=re.fullmatch(r'data/maps/([^/]+)/map.json',path)
            if match:
                self.maps[match[1]]=self.js(path)
        self.by_id={}
        for name,row in self.maps.items():
            if row['id'] in self.by_id:
                raise ValueError(('Duplicate staged map constant',row['id']))
            if name not in self.identities:
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
