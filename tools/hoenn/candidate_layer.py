"""Strict file hashing shared by the final integration overlays."""
import hashlib
import json
from pathlib import Path


class Layer:
    def __init__(self, source, name, prior):
        self.source = Path(source)
        self.name = name
        self.marker = self.source / ('.journey-' + name)
        self.outputs, self.originals = {}, {}
        self.expected = dict(json.loads((self.source / '.source-acquired.json').read_text())['sha256'])
        for layer in prior:
            self.expected.update(json.loads((self.source / ('.journey-' + layer)).read_text())['prepared_sha256'])

    def existing(self):
        if not self.marker.exists():
            return None
        result = json.loads(self.marker.read_text())
        for name, digest in result['prepared_sha256'].items():
            assert hashlib.sha256((self.source / name).read_bytes()).hexdigest() == digest, name
        return result

    def stage(self, name, content):
        path = self.source / name
        before = path.read_bytes() if path.exists() else None
        digest = hashlib.sha256(before).hexdigest() if before is not None else None
        assert digest == self.expected.get(name), name
        if digest is not None:
            self.originals[name] = digest
        self.outputs[name] = content.encode() if isinstance(content, str) else content

    def finish(self, **metadata):
        for name, content in self.outputs.items():
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        result = dict(layer=self.name, **metadata, original_sha256=self.originals,
                      prepared_sha256={name: hashlib.sha256(content).hexdigest()
                                       for name, content in self.outputs.items()})
        self.marker.write_text(json.dumps(result, indent=2) + '\n')
        return result
