"""Replay the frozen C8 source in memory before the user's next redesign.

Neither C8 nor171 is edited. A new preparation must carry this exact base
and explicitly reset the old source/native/edition validation status.
"""
from copy import deepcopy
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile

from candidate_layer import Layer
from prepare_generated_area_review import PRIOR,LAYER
from restore_generated_area_review import verify_prefix

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'docs/design/atlas-surf-layout/unified-native-review'


def load(parent,evidence=EVIDENCE):
    parent=Path(parent).resolve();evidence=Path(evidence).resolve();proof=verify_prefix(parent,complete=True)
    sums={row.split('  ',1)[1]:row.split('  ',1)[0] for row in (evidence/'SHA256SUMS').read_text().splitlines()}
    blobs={}
    for name in ['compiled-freeze.json.gz','prepared-source.tar.gz']:
        raw=(evidence/name).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=sums[name]:raise ValueError(('C8 base snapshot changed',name))
        blobs[name]=raw
    frozen=json.loads(gzip.decompress(blobs['compiled-freeze.json.gz']));expected=frozen['prepared_sha256']
    layer=Layer(parent,'atlas-surf-layout',PRIOR+[LAYER]);found={}
    for name,wanted in proof['layer_marker_sha256'].items():layer.expected['.journey-'+name]=wanted
    with tarfile.open(fileobj=io.BytesIO(blobs['prepared-source.tar.gz']),mode='r:gz') as bundle:
        for member in bundle.getmembers():
            path=Path(member.name)
            if not member.isfile() or path.is_absolute() or '..' in path.parts or member.name in found:
                raise ValueError('Unsafe or duplicate C8 prepared snapshot member')
            found[member.name]=bundle.extractfile(member).read()
    if set(found)!=set(expected)|{'.journey-atlas-surf-layout'}:
        raise ValueError('C8 snapshot is not the complete2180-file preparation')
    marker=found.pop('.journey-atlas-surf-layout')
    if hashlib.sha256(marker).hexdigest()!=frozen['marker_sha256']:raise ValueError('C8 marker changed')
    metadata=json.loads(marker)
    if metadata['parent']!=proof or metadata['prepared_sha256']!=expected:
        raise ValueError('Redesign parent differs from the authenticated C8 source')
    for name,raw in found.items():
        if hashlib.sha256(raw).hexdigest()!=expected[name]:raise ValueError(('C8 prepared file changed',name))
        layer.stage(name,raw)
    metadata=deepcopy(metadata)
    for key in ['layer','original_sha256','prepared_sha256']:metadata.pop(key,None)
    metadata.update(source_audit_passed=False,native_validated=False,release_eligible=False,
                    NATIVE_CONTRACT_FINALIZED=False,public_roms_updated=False)
    metadata['redesign_base']=dict(ROM_sha256=frozen['rom_sha256'],ELF_sha256=frozen['elf_sha256'],
        marker_sha256=frozen['marker_sha256'],snapshot_files=len(expected),
        previous_native_proofs_are_historical_for_the_redesign=True)
    return layer,metadata
