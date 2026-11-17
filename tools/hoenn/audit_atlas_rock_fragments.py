"""Census native General large boulders, including actual connected seams.

The eight-word graphics definitions classify quarters, including fused
shore/cliff variants. Other primary banks are reported outside this scope.
Suspects require whole-map review; this tool never removes or completes art.
"""
import argparse
from collections import Counter
from copy import copy
import hashlib
import json
from pathlib import Path
import re

from atlas_surf_source import Source
from atlas_surf_route_borders import _neighbor
from atlas_surf_slateport_rocks import LARGE_ROCK_IDS,COMPLETE_PATTERNS
from render_sea_maps import MapRenderer


def with_layout(source,name,layout):
    result=copy(source);result.maps=dict(source.maps);result.maps[name]=dict(source.maps[name],layout=layout)
    result._words=dict(source._words);result._words.pop(name,None)
    return result


def scripted_layouts(source):
    result=[]
    for name in sorted(source.identities):
        path='data/maps/'+name+'/scripts.inc'
        if not (source.source/path).exists() and path not in getattr(getattr(source,'layer',None),'outputs',{}):continue
        raw=source.read(path)
        for symbol in sorted(set(re.findall(r'^\s*setmaplayoutindex\s+(LAYOUT_\w+)',raw.decode(),re.M))):
            layout=source.layouts[symbol]
            if (symbol==source.maps[name]['layout'] or layout['primary_tileset']!='gTileset_General'
                    or layout['layout_version']=='frlg'):continue
            result.append(dict(map=name,layout=symbol,script=path,script_sha256=hashlib.sha256(raw).hexdigest()))
    return result


def census_scripted_layouts(source,classes):
    return [dict(row,census=census(with_layout(source,row['map'],row['layout']),[row['map']],classes))
            for row in scripted_layouts(source)]


def quarter_classes(words):
    def signature(mid):
        return tuple((i%4,v) for i,v in enumerate(words[8*mid:8*mid+8]) if 0x1b0<=v&1023<=0x1bf)
    variants={}
    for pattern in COMPLETE_PATTERNS:
        for quarter,mid in enumerate(pattern):
            sig=signature(mid)
            if not sig:raise ValueError('Native boulder reference no longer uses reviewed graphics')
            if sig in variants and variants[sig]!=quarter:raise ValueError('Native boulder quarters are ambiguous')
            variants[sig]=quarter
    return {mid:variants.get(signature(mid)) for mid in LARGE_ROCK_IDS}


def census(source,names,classes):
    pieces=[];complete={};covered=set()
    def resolve(name,x,y,dx,dy):
        point=(name,x,y)
        if dx:point=_neighbor(source,*point,dx,0)
        if point is not None and dy:point=_neighbor(source,*point,0,dy)
        if point is None:return None
        row=source.layout(point[0])
        return point if row['primary_tileset']=='gTileset_General' and row['layout_version']!='frlg' else None
    for name in names:
        layout=source.layout(name)
        for i,word in enumerate(source.words(name)):
            mid=word&1023
            if mid not in classes:continue
            x,y=i%layout['width'],i//layout['width'];point=(name,x,y);pieces.append((point,mid))
            quarter=classes[mid]
            if quarter is None:continue
            cells=[]
            for q in range(4):
                p=resolve(name,x,y,q%2-quarter%2,q//2-quarter//2)
                if p is None or classes.get(source.word(*p)&1023)!=q:break
                cells.append(p)
            if len(cells)==4:
                key=tuple(cells);covered.update(cells)
                complete[key]=dict(cells=[list(p) for p in cells],metatiles=[source.word(*p)&1023 for p in cells])
    return dict(piece_count=len(pieces),complete_objects=list(complete.values()),
                suspect_orphan_pieces=[dict(map=p[0],tile=list(p[1:]),metatile=mid,
                    word=source.word(*p),quarter=classes[mid]) for p,mid in pieces if p not in covered])


def audit(path):
    path=Path(path);source=Source(path);renderer=MapRenderer(path)
    classes=quarter_classes(renderer.tileset('gTileset_General')[2])
    names=[];outside=Counter()
    for name in source.identities:
        layout=source.layout(name)
        if layout['primary_tileset']=='gTileset_General' and layout['layout_version']!='frlg':names.append(name)
        else:outside[layout['primary_tileset']]+=1
    result=census(source,sorted(names),classes);source.assert_unchanged()
    result['scripted_alternate_layouts']=census_scripted_layouts(source,classes)
    source.assert_unchanged()
    result.update(kind='native-General-large-rock-graphics-census',source=str(path.resolve()),
        ROM_sha256=hashlib.sha256((path/'pokeemerald.gba').read_bytes()).hexdigest(),
        marker_sha256=hashlib.sha256((path/'.journey-atlas-surf-layout').read_bytes()).hexdigest(),
        maps_checked=len(names),classified_native_metatiles=classes,
        other_primary_banks_not_certified=dict(outside),
        source_input_sha256=source.inputs,source_only=True,native_ROM_visual_review_complete=False,
        no_terrain_or_events_changed=True,suspects_are_not_automatic_repair_authorization=True)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args();result=audit(a.source);a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(maps=result['maps_checked'],pieces=result['piece_count'],
        complete_objects=len(result['complete_objects']),suspect_pieces=len(result['suspect_orphan_pieces']),
        suspect_maps=dict(Counter(r['map'] for r in result['suspect_orphan_pieces'])),source_only=True)))
