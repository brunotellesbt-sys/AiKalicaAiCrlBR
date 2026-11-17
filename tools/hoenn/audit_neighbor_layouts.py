"""Find header/live-layout differences inside seven-tile connection aprons.

Candidates require native reproduction. Conditional layouts and literal tile
patches are reported, never silently applied or equated with confirmed bugs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
from atlas_surf_source import Source

def apron(x,y,width,height,direction):
    return {'left':x<7,'right':x>=width-7,'up':y<7,'down':y>=height-7}.get(direction,False)

def audit(source):
    s=source if hasattr(source,'identities') else Source(source)
    variants=[];patches=[];connected=0
    for name in sorted(s.identities):
        connections=s.maps[name].get('connections') or []
        if not connections:continue
        connected+=1;path='data/maps/'+name+'/scripts.inc'
        if not (s.source/path).exists():continue
        text=s.read(path).decode();layout=s.layout(name);w,h=layout['width'],layout['height']
        for key in sorted(set(re.findall(r'^\s*setmaplayoutindex\s+(LAYOUT_\w+)',text,re.M))-{layout['id']}):
            other=s.layouts[key];raw=s.read(other['blockdata_filepath'])
            row=dict(map=name,header_layout=layout['id'],script_layout=key,script_sha256=hashlib.sha256(text.encode()).hexdigest(),
                same_dimensions=[w,h]==[other['width'],other['height']],banks_changed=any(layout[k]!=other[k] for k in ('primary_tileset','secondary_tileset','layout_version')),seams=[])
            if row['same_dimensions']:
                words=struct.unpack('<'+'H'*(w*h),raw)
                for c in connections:
                    if c['direction'] not in ('left','right','up','down'):continue
                    cells=[dict(tile=[i%w,i//w],header_word=a,live_word=b,physical_bits_changed=(a&~1023)!=(b&~1023))
                        for i,(a,b) in enumerate(zip(s.words(name),words)) if a!=b and apron(i%w,i//w,w,h,c['direction'])]
                    row['seams'].append(dict(direction=c['direction'],neighbor=s.by_id[c['map']],changed_apron_cells=cells))
            variants.append(row)
        for x,y,metatile in re.findall(r'^\s*setmetatile\s+(\d+),\s*(\d+),\s*(\w+)',text,re.M):
            x,y=int(x),int(y)
            edges=[c for c in connections if apron(x,y,w,h,c['direction']) and 0<=x<w and 0<=y<h]
            if edges:patches.append(dict(map=name,tile=[x,y],metatile_expression=metatile,script_sha256=hashlib.sha256(text.encode()).hexdigest(),
                nearby_connections=[dict(direction=c['direction'],neighbor=s.by_id[c['map']]) for c in edges]))
    s.assert_unchanged()
    return dict(kind='connected-header-versus-script-layout-apron-census',connected_maps_checked=connected,
        alternate_layouts=variants,literal_script_tile_patches_near_connections=patches,input_sha256=s.inputs,
        native_defects_confirmed=False,conditional_execution_and_C_generated_changes_require_separate_analysis=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=audit(a.source);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps(dict(connected_maps=r['connected_maps_checked'],alternate_layouts=len(r['alternate_layouts']),
        variants_with_changed_aprons=sum(any(s['changed_apron_cells'] for s in v['seams']) for v in r['alternate_layouts']),
        nearby_literal_tile_patches=len(r['literal_script_tile_patches_near_connections']),source_only=True)))
