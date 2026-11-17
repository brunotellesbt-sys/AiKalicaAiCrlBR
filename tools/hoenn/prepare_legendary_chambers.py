"""Prepare a private version8 source, preserving all frozen predecessors."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil

from atlas_legendary_chambers import load_current, stage, refresh_saved_objects
from audit_legendary_chambers import audit
from prepare_atlas_surf_redesign import source_audit
from prepare_atlas_connected_layout import checked_cache
from restore_generated_area_review import verify_prefix


def clone_authenticated(reference, target, expected, *, omit_compiled_artifacts=False, resume=False):
    """Share only authenticated read-only inputs; all generated files are private."""
    reference,target = Path(reference).resolve(),Path(target).resolve()
    if (target.exists() and not resume) or target.is_relative_to(reference) or reference.is_relative_to(target):
        raise ValueError('Choose a fresh independent directory')
    if resume:
        for path in target.rglob('*'):
            if path.is_file():
                old=reference/path.relative_to(target)
                if path.is_symlink() or not old.is_file() or path.read_bytes()!=old.read_bytes():
                    raise ValueError(('Preserve changed partial preparation',str(path)))
    shared = []
    def copy_file(src,dst):
        src,dst = Path(src),Path(dst)
        name = src.relative_to(reference).as_posix()
        if name in expected:
            if hashlib.sha256(src.read_bytes()).hexdigest() != expected[name]:
                raise ValueError(('Frozen input changed',name))
            src.chmod(src.stat().st_mode & ~0o222)
        if dst.exists():
            if not resume or src.read_bytes()!=dst.read_bytes() or (name not in expected and src.samefile(dst)):
                raise ValueError('Changed or shared mutable partial clone')
            return str(dst)
        if name in expected:
            os.link(src,dst)
            shared.append(name)
            return str(dst)
        result = shutil.copy2(src,dst)
        if src.samefile(dst):
            raise ValueError('Generated or marker file shares a writable inode')
        return result
    def ignore(folder,names):
        return {'pokeemerald.gba','pokeemerald.elf','pokeemerald.map'} & set(names) if omit_compiled_artifacts and Path(folder)==reference else set()
    shutil.copytree(reference,target,copy_function=copy_file,symlinks=False,ignore=ignore,dirs_exist_ok=resume)
    return dict(shared_readonly_authenticated_inputs=shared, generated_files_independent=True)


def prepare(parent, target, reference_freeze, output, *, large_exteriors=False, cache_freeze=None, resume_clone=False):
    parent,target,output = map(lambda p:Path(p).resolve(),(parent,target,output))
    if target.exists() and not (resume_clone and cache_freeze):
        raise ValueError('Preserve the existing private candidate')
    before = verify_prefix(parent,complete=True)
    reference = checked_cache(reference_freeze,before)
    layer,metadata = load_current(parent)
    expected = dict(layer.expected)
    expected.update({n:hashlib.sha256(raw).hexdigest() for n,raw in layer.outputs.items()})
    report = stage(layer,reference)
    changed=list(report['changed_parent_maps'])
    if large_exteriors:
        from atlas_large_cave_exteriors import stage as stage_exteriors,stage_save_rescues
        exterior_report=stage_exteriors(layer,metadata)
        changed += ['MAP_'+r['map'].upper() for r in exterior_report['maps']]
        metadata['large_cave_exteriors']=exterior_report
    refresh_saved_objects(layer,changed)
    if large_exteriors:
        stage_save_rescues(layer,exterior_report)
    metadata['legendary_individual_chambers'] = report
    metadata['migration']['final_version'] = 8
    independent = audit(layer,reference,report)
    print('105 reciprocal rooms and native campaign preservation PASS',flush=True)
    _,physical,_,banks = source_audit(layer,metadata)
    print('Global physical source audit PASS',flush=True)
    metadata['source_audit_passed'] = True
    metadata['pending_obligations'] = [
        'current-ROM 105 chamber entrances, returns, species pixels and persistent captures',
        'large varied cave exteriors and bank/camera review',
        'version7 batteries -> Continue8 -> menu SAVE -> Continue8',
        'current-ROM coast/Dive/trainer/ecology/Dex/five editions and strict release/browser gates']
    output.mkdir(parents=True,exist_ok=True)
    for name,record in [('rooms',report),('rooms-source',independent),('physical-source',physical),('banks',banks)]:
        (output/(name+'.json.gz')).write_bytes(gzip.compress(json.dumps(record,sort_keys=True,separators=(',',':')).encode(),mtime=0))
    if large_exteriors:
        (output/'exteriors.json.gz').write_bytes(gzip.compress(json.dumps(exterior_report,sort_keys=True,separators=(',',':')).encode(),mtime=0))
    cache=reference
    if cache_freeze:
        from candidate_layer import Layer
        from prepare_generated_area_review import PRIOR,LAYER
        cache=checked_cache(cache_freeze,before)
        expected=Layer(cache,'atlas-surf-layout',PRIOR+[LAYER,'atlas-surf-layout']).expected
        for name,wanted in before['layer_marker_sha256'].items():
            expected['.journey-'+name]=wanted
    clone = clone_authenticated(cache,target,expected,omit_compiled_artifacts=bool(cache_freeze),resume=resume_clone)
    (output/'readonly-source-sharing.json.gz').write_bytes(gzip.compress(json.dumps(clone,sort_keys=True).encode(),mtime=0))
    layer.source=target
    layer.marker=target/'.journey-atlas-surf-layout'
    result=layer.finish(**metadata)
    # Identical staged inputs retain private timestamps to reuse the checked
    # cache. No timestamp of a shared frozen inode is changed.
    for name in layer.outputs:
        old=cache/name;new=target/name
        if old.is_file() and old.read_bytes()==new.read_bytes():
            if old.samefile(new):
                raise ValueError('Staged source unexpectedly shares an inode')
            os.utime(new,ns=(old.stat().st_atime_ns,old.stat().st_mtime_ns))
    if verify_prefix(parent,complete=True) != before:
        raise ValueError('Immutable parent changed')
    return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('parent','target','reference-freeze','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--large-exteriors',action='store_true')
    parser.add_argument('--cache-freeze',type=Path)
    parser.add_argument('--resume-clone',action='store_true')
    args=parser.parse_args()
    result=prepare(args.parent,args.target,args.reference_freeze,args.output,
                   large_exteriors=args.large_exteriors,cache_freeze=args.cache_freeze,resume_clone=args.resume_clone)
    print(json.dumps(dict(rooms=105,migration=8,source_passed=result['source_audit_passed'],native_validated=False)))
