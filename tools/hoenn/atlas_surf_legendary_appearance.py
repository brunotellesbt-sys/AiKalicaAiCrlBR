"""Replace the seven remaining sanctuary statues with their native species.

The room redesign can move these exact objects afterward. Capture scripts,
flags, IDs, movement and positions are preserved by this appearance repair.
No guessed universal graphics ID or new artwork is used.
"""
import copy
import hashlib
import json
import re

from badge_story_layer import read


def repair_objects(mapping,captures):
    result=copy.deepcopy(mapping);changes=[]
    by_dex={row['national_dex']:row for row in captures}
    if len(by_dex)!=len(captures):raise ValueError('Duplicate legendary capture identity')
    for index,event in enumerate(result.get('object_events') or []):
        match=re.fullmatch(r'JourneySanctuary_(\d+)',event.get('script',''))
        if match is None or 'STATUE' not in event.get('graphics_id',''):continue
        dex=int(match[1]);capture=by_dex.get(dex)
        if capture is None or event.get('flag')!=capture['flag']:
            raise ValueError(('Statue does not match its preserved capture flag',mapping['name'],dex))
        species=capture['species']
        if not re.fullmatch(r'SPECIES_[A-Z0-9_]+',species):raise ValueError('Invalid native legendary species symbol')
        before=event['graphics_id'];after='OBJ_EVENT_GFX_SPECIES('+species.removeprefix('SPECIES_')+')'
        event['graphics_id']=after
        changes.append(dict(map=mapping['name'],object_index=index,national_dex=dex,species=species,
            script=event['script'],flag=event['flag'],before=before,after=after,
            native_local_id=event.get('native_local_id'),local_id=event.get('local_id')))
    for old,new in zip(mapping.get('object_events') or [],result.get('object_events') or []):
        if {k:v for k,v in old.items() if k!='graphics_id'}!={k:v for k,v in new.items() if k!='graphics_id'}:
            raise ValueError('Appearance repair changed gameplay identity or placement')
    return result,changes


def stage(layer,captures,groups):
    changes=[];inputs={}
    for group in groups:
        path='data/maps/'+group['map']+'/map.json';raw=read(layer,path);mapping=json.loads(raw)
        updated,rows=repair_objects(mapping,captures)
        if rows:
            layer.stage(path,json.dumps(updated,indent=2)+'\n');changes.extend(rows)
            inputs[path]=hashlib.sha256(raw).hexdigest()
    return dict(kind='native-legendary-appearance-repair',changes=changes,input_sha256=inputs,
                capture_flags_scripts_positions_and_local_ids_preserved=True,
                saved_NPC_template_refresh_required_maps=sorted({r['map'] for r in changes}),
                native_species_artwork_required=True,source_preview_not_native_ROM_proof=True,
                native_sprite_pixels_validated=False,final_release_validated=False)
