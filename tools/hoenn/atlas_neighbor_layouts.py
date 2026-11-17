"""Authenticate the current preparation and canonicalize permanent layouts.

Conditional scenery must keep its real state predicate. A header may be
canonicalized only when the transition script always selects the same layout.
"""
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import tarfile

from atlas_surf_redesign_overlay import load as load_c8
from badge_story_layer import read
from render_sea_maps import _braced

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'docs/design/native-rock-fragments-review'
BASE_ROM='5b5b1ace4c9b681c22540168d0d142abd30b57628d26da9264d508a82bed929c'

def load(parent):
    layer,_=load_c8(parent)
    sums=dict((n,h) for h,n in (line.split('  ',1) for line in (EVIDENCE/'SHA256SUMS').read_text().splitlines()))
    blobs={}
    for n in ('compiled-freeze-v6.json.gz','prepared-source-delta-v6.tar.gz'):
        raw=(EVIDENCE/n).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=sums[n]:raise ValueError('Changed frozen version6 source')
        blobs[n]=raw
    frozen=json.loads(gzip.decompress(blobs['compiled-freeze-v6.json.gz']))
    if frozen['rom_sha256']!=BASE_ROM:raise ValueError('Unexpected version6 parent ROM')
    found={}
    with tarfile.open(fileobj=io.BytesIO(blobs['prepared-source-delta-v6.tar.gz']),mode='r:gz') as bundle:
        for member in bundle.getmembers():
            path=Path(member.name)
            if not member.isfile() or path.is_absolute() or '..' in path.parts or member.name in found:
                raise ValueError('Unsafe prepared source delta')
            found[member.name]=bundle.extractfile(member).read()
    raw=found.pop('.journey-atlas-surf-layout')
    if hashlib.sha256(raw).hexdigest()!=frozen['marker_sha256']:raise ValueError('Version6 marker differs')
    metadata=json.loads(raw)
    for n,raw in found.items():layer.stage(n,raw)
    if set(layer.outputs)!=set(frozen['prepared_sha256']):raise ValueError('Incomplete current source replay')
    for n,h in frozen['prepared_sha256'].items():
        if hashlib.sha256(layer.outputs[n]).hexdigest()!=h:raise ValueError(('Current source replay differs',n))
    for key in ('layer','original_sha256','prepared_sha256'):metadata.pop(key,None)
    metadata.update(source_audit_passed=False,native_validated=False,release_eligible=False,
        public_roms_updated=False,NATIVE_CONTRACT_FINALIZED=False)
    metadata['neighbor_layout_base']=dict(ROM_sha256=BASE_ROM,ELF_sha256=frozen['elf_sha256'],marker_sha256=frozen['marker_sha256'])
    return layer,metadata

def stage(layer):
    path='data/maps/Route131/map.json';mapping=json.loads(read(layer,path))
    script=read(layer,'data/maps/Route131/scripts.inc').decode()
    if mapping['layout']!='LAYOUT_ROUTE131':raise ValueError('Unexpected Route131 header layout')
    transition=script.split('Route131_OnTransition:',1)[1].split('Route131_EventScript_SetLayout::',1)[0]
    setter=script.split('Route131_EventScript_SetLayout::',1)[1].split('Route131_EventScript_CheckSetAbnormalWeather::',1)[0]
    if transition.strip()!='call_if_ge VAR_SOOTOPOLIS_CITY_STATE, 4, Route131_EventScript_CheckSetAbnormalWeather\n\tcall Route131_EventScript_SetLayout\n\tend':
        raise ValueError('Route131 layout is no longer unconditionally selected')
    if setter.strip()!='setmaplayoutindex LAYOUT_ROUTE131_SKY_PILLAR\n\treturn':raise ValueError('Route131 live layout changed')
    mapping['layout']='LAYOUT_ROUTE131_SKY_PILLAR';layer.stage(path,json.dumps(mapping,indent=2)+'\n')
    return dict(map='Route131',old_layout='LAYOUT_ROUTE131',canonical_layout=mapping['layout'],
        unconditional_transition_script_sha256=hashlib.sha256(script.encode()).hexdigest(),
        live_terrain_and_all_events_unchanged=True,conditional_maps_not_canonicalized=['Route130','Route111'])

def refresh_saved_view(layer):
    path='src/load_save.c';text=read(layer,path).decode();signature='static void JourneyMigrateSeviiSaveGeometry(void)\n{'
    body=_braced(text,text.index(signature)+len(signature)-1)
    guard='if(VarGet(VAR_JOURNEY_SEVII_GEOMETRY_VERSION)>=6) return;'
    if body.count(guard)!=1 or body.count('VarSet(VAR_JOURNEY_SEVII_GEOMETRY_VERSION,6);')!=1:
        raise ValueError('The version6 migration wrapper changed')
    updated=body.replace(guard,guard.replace('>=6','>=7')).replace('VarSet(VAR_JOURNEY_SEVII_GEOMETRY_VERSION,6);','VarSet(VAR_JOURNEY_SEVII_GEOMETRY_VERSION,7);')
    layer.stage(path,text.replace(signature+body+'}',signature+updated+'}',1))
    path='include/constants/vars.h';text=read(layer,path).decode()
    text,n=re.subn(r'(#define\s+JOURNEY_SEVII_GEOMETRY_VERSION_CURRENT\s+)6\b',r'\g<1>7',text)
    if n!=1:raise ValueError('Expected save version6')
    layer.stage(path,text)
    return dict(version=7,one_time_saved_background_refresh=True,positions_flags_and_NPCs_unchanged_for_version6=True)
