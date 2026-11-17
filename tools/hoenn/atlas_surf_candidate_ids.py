"""Preserve every published candidate533 map ID while changing its geometry.

Old names keep their numeric slots. New names append after all old slots;
unused old names become inaccessible blocked placeholders outside the Atlas
runtime table. Coordinate/warp migration is a separate version3 obligation.
"""
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
import struct

ROOT=Path(__file__).resolve().parents[2]
BASELINE='docs/design/atlas-surf-layout/whole-layout-composed-source.json.gz'
BASELINE_SHA256='54067a50e3c1a019fd99e9842a628102c11b08ab38ad0074ddb98ea135380f59'
COMPILED_ROWS_SHA256='6e1efdcb1165e99dd8b79e7193393dd37682ce435f378067d33cbe5231a03852'


def load_history():
    raw=(ROOT/BASELINE).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=BASELINE_SHA256:raise ValueError('Published candidate geometry baseline changed')
    result=json.loads(gzip.decompress(raw));rows=result['geometry_plan']['chunks']
    packed=b''.join(struct.pack('<HhhBB',(r['group_index']<<8)|r['number'],*r['origin'],r['width'],r['height']) for r in rows)
    if len(rows)!=533 or hashlib.sha256(packed).hexdigest()!=COMPILED_ROWS_SHA256:
        raise ValueError('Candidate identities/rectangles differ from the authenticated compiled533 table')
    return result


def bind(plan,history):
    result=deepcopy(plan);old=history['geometry_plan']['chunks'];old_names={r['name']:r for r in old}
    if len(old_names)!=len(old):raise ValueError('Duplicate historical candidate name')
    by_group={}
    for r in sorted(old,key=lambda r:(r['group_index'],r['number'])):
        group=by_group.setdefault(r['group'],dict(name=r['group'],index=r['group_index'],members=[]))
        if group['index']!=r['group_index'] or r['number']!=len(group['members']) or r['number']>=100:
            raise ValueError('Historical candidate registry is not contiguous and WarpData safe')
        group['members'].append(r['name'])
    groups=sorted(by_group.values(),key=lambda r:r['index'])
    if [r['index'] for r in groups]!=list(range(groups[0]['index'],groups[-1]['index']+1)):
        raise ValueError('Historical candidate group registry has gaps')
    registry={name:(g['name'],g['index'],i) for g in groups for i,name in enumerate(g['members'])}
    active_names={r['name'] for r in result['chunks']}
    if len(active_names)!=len(result['chunks']):raise ValueError('Duplicate active candidate name')
    added=[]
    for r in result['chunks']:
        name=r['name']
        if name not in registry:
            if len(groups[-1]['members'])==100:
                index=groups[-1]['index']+1
                if index>=128:raise ValueError('Candidate groups exceed signed WarpData range')
                groups.append(dict(name='JourneyAtlasSeas'+str(len(groups)),index=index,members=[]))
            g=groups[-1];number=len(g['members']);g['members'].append(name)
            registry[name]=(g['name'],g['index'],number);added.append(name)
        group,index,number=registry[name]
        r.update(group=group,group_index=index,number=number)
    specs={r['map']:r for r in history['geometry']['chunks']}
    inactive=[]
    for name in sorted(old_names.keys()-active_names,key=lambda n:(old_names[n]['group_index'],old_names[n]['number'])):
        old_row=old_names[name];g,i,n=registry[name]
        inactive.append(dict(name=name,id='MAP_'+name.upper(),group=g,group_index=i,number=n,
            origin=old_row['origin'],width=2,height=2,kind='retired-candidate',water_runs=[],connections=[],
            retired_candidate_placeholder=True,donor=deepcopy(specs[name]['donor'])))
    result['candidate_registry']=groups;result['retired_candidate_placeholders']=inactive
    result['candidate_identity_history']=dict(kind='append-only-published-candidate-map-registry',
        baseline=BASELINE,baseline_sha256=BASELINE_SHA256,compiled_rows_sha256=COMPILED_ROWS_SHA256,
        published_slots=len(old_names),active_maps=len(active_names),appended_names=added,
        inactive_old_names=[r['name'] for r in inactive],coordinates_need_version3_migration=True)
    return result
