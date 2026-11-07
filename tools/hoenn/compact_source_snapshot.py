"""Materialize only mutable ancestors of a frozen source in a small workspace.

Unchanged directories point at the pinned parent and must remain read-only.
Callers must enumerate every staged/generated input before building; this is
an optimization for reviewed overlays, not a general writable source clone.
"""
import hashlib
import os
from pathlib import Path
import shutil
import tarfile
import json


def clone(source, destination, mutable_paths, *, cache=None):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    assert source.is_dir() and not destination.exists()
    assert source != destination and not destination.is_relative_to(source)
    private = {Path(p) for p in mutable_paths}
    assert all(not p.is_absolute() and '..' not in p.parts for p in private)
    full_private = {'tools', 'libagbsyscall'}
    destination.mkdir(parents=True)

    def visit(before, after, relative):
        if before.name == 'build' and relative == Path('build'):
            return
        split = relative == Path('.') or any(relative == p or relative in p.parents for p in private)
        if relative.parts and relative.parts[0] in full_private:
            if before.is_dir():
                shutil.copytree(before, after, symlinks=True)
            else:
                shutil.copy2(before, after)
        elif before.is_dir():
            if split:
                after.mkdir(exist_ok=True)
                shutil.copystat(before, after)
                for child in before.iterdir():
                    visit(child, after/child.name, relative/child.name)
            else:
                after.symlink_to(before, target_is_directory=True)
        elif before.is_symlink():
            if relative in private:
                shutil.copy2(before, after)
            else:
                after.symlink_to(before.resolve())
        elif relative in private or relative.suffix in {'.gba', '.elf', '.map', '.sym'}:
            shutil.copy2(before, after)
        else:
            os.link(before, after)

    for child in source.iterdir():
        visit(child, destination/child.name, Path(child.name))
    for relative in private:
        assert not any((destination/p).is_symlink() for p in relative.parents if p != Path('.')), relative
    if cache:
        cache = Path(cache)
        manifest = json.loads(cache.with_suffix('.manifest.json').read_bytes())
        with tarfile.open(cache) as archive:
            for member in archive.getmembers():
                name = Path(member.name)
                assert name.parts[0] == 'build' and not name.is_absolute() and '..' not in name.parts
                assert member.isfile() or member.isdir(), member.name
                if member.isfile():
                    raw = archive.extractfile(member).read()
                    assert hashlib.sha256(raw).hexdigest() == manifest[member.name]
                    target = destination/name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(raw)
                    target.chmod(member.mode)
                    os.utime(target, (member.mtime, member.mtime))
            assert set(manifest) == {m.name for m in archive.getmembers() if m.isfile()}
    return destination
