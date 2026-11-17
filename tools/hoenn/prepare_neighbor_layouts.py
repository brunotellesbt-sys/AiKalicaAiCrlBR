"""Create an isolated canonical-layout candidate from the exact version6 source."""
import argparse
import gzip
import json
from pathlib import Path
import shutil
from atlas_neighbor_layouts import load,stage,refresh_saved_view
from prepare_atlas_surf_redesign import source_audit
from prepare_atlas_connected_layout import checked_cache
from prepare_atlas_surf_layout import seed_build_cache
from restore_generated_area_review import verify_prefix

def prepare(parent,target,output,freeze):
    parent,target,output=map(lambda p:Path(p).resolve(),(parent,target,output))
    if target.exists() or target.is_relative_to(parent):raise ValueError('Choose a fresh private source')
    before=verify_prefix(parent,complete=True);layer,metadata=load(parent)
    metadata['neighbor_layout_repair']=stage(layer);metadata['neighbor_layout_save_refresh']=refresh_saved_view(layer)
    metadata['migration']['final_version']=7
    _,report,_,banks=source_audit(layer,metadata)
    metadata['source_audit_passed']=True
    output.mkdir(parents=True,exist_ok=True)
    for n,r in [('preparation',metadata),('source',report),('banks',banks)]:
        (output/(n+'.json.gz')).write_bytes(gzip.compress(json.dumps(r,sort_keys=True,separators=(',',':')).encode(),mtime=0))
    cache=checked_cache(freeze,before)
    shutil.copytree(parent,target,copy_function=shutil.copy2)
    metadata['build_cache']=seed_build_cache(cache,target,set(layer.expected)|set(layer.outputs)|{p.name for p in parent.glob('.journey-*')})
    layer.source=target;layer.marker=target/'.journey-atlas-surf-layout';result=layer.finish(**metadata)
    if verify_prefix(parent,complete=True)!=before:raise ValueError('Immutable parent changed')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('parent','target','output','freeze'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();r=prepare(a.parent,a.target,a.output,a.freeze);print(json.dumps(dict(source_passed=r['source_audit_passed'],migration=7,native_validated=False)))
