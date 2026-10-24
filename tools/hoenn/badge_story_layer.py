"""Compose independently reviewed badge-story repairs in one atomic layer."""
import hashlib


def read(layer, path):
    """Read the previous staged repair, or a verified parent file."""
    if path in layer.outputs:
        return layer.outputs[path]
    raw = (layer.source / path).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == layer.expected[path], path
    return raw
