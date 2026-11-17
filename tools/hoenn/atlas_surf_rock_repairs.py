"""Repair the103 reviewed General fragments without changing physical cells.

Fused shore/cliff pieces receive complete native shores. Isolated quarters
receive native one-tile boulders. Route108 uses the native shallow-water
variant. All tile definitions, graphics, palettes and animation stay intact.
"""
import hashlib
import json
from pathlib import Path
import re
import struct

from audit_atlas_rock_fragments import census,quarter_classes
from atlas_surf_overlay import OverlaySource
from badge_story_layer import read
from render_sea_maps import _braced

PLAN=Path(__file__).parent/'data/native-General-rock-repairs.json'


def bank_paths(view,bank):
    headers=view.read('src/data/tilesets/headers.h').decode();definitions=view.read('src/data/tilesets/metatiles.h').decode()
    body=re.search(r'const struct Tileset '+re.escape(bank)+r'\s*=\s*\{(.*?)\};',headers,re.S)[1]
    paths={}
    for field in ('metatiles','metatileAttributes'):
        symbol=re.search(r'\.'+field+r'\s*=\s*(\w+)',body)[1]
        paths[field]=re.search(r'\b'+re.escape(symbol)+r'\[\].*?"([^"]+)"',definitions,re.S)[1]
    return paths


def stage(layer):
    plan=json.loads(PLAN.read_bytes());view=OverlaySource(layer)
    primary=bank_paths(view,'gTileset_General');raw=view.read(primary['metatiles'])
    words=struct.unpack('<'+'H'*(len(raw)//2),raw);classes=quarter_classes(words)
    attrs=view.read(primary['metatileAttributes'])
    for donor in plan['native_whole_boulder_donors']:
        mid=donor['metatile']
        if (list(words[8*mid:8*mid+8])!=donor['eight_words']
            or int.from_bytes(attrs[2*mid:2*mid+2],'little')!=donor['attribute']
            or donor['native_definition']!=primary['metatiles']):
            raise ValueError('Reviewed whole-boulder artwork or donor changed')
    names=sorted(n for n in view.identities if view.layout(n)['primary_tileset']=='gTileset_General'
                 and view.layout(n)['layout_version']!='frlg')
    before=census(view,names,classes)
    actual={(r['map'],*r['tile'],r['word']) for r in before['suspect_orphan_pieces']}
    expected={(r['map'],*r['tile'],r['before']) for r in plan['repairs']}
    if actual!=expected or len(actual)!=103 or len(before['complete_objects'])!=462:
        raise ValueError(('The103 reviewed fragments changed',len(actual),len(expected)))
    files={};rows=[]
    for row in plan['repairs']:
        name=row['map'];x,y=row['tile'];layout=view.layout(name)
        if view.word(name,x,y)!=row['before'] or not row['before']&0xc00:
            raise ValueError(('Reviewed fragment or collision changed',name,x,y))
        if (row['before']&~1023)!=(row['after']&~1023):raise ValueError('Rock repair changed elevation/collision')
        for field in ('object_events','warp_events','coord_events','bg_events'):
            if any((e.get('x'),e.get('y'))==(x,y) for e in view.maps[name].get(field) or []):
                raise ValueError(('Rock repair overlaps an event',name,x,y,field))
        path=layout['blockdata_filepath']
        if path not in files:files[path]=list(view.words(name))
        files[path][y*layout['width']+x]=row['after'];rows.append(dict(row))
    view.assert_unchanged()
    hashes={}
    for path,values in files.items():
        raw=struct.pack('<'+'H'*len(values),*values);hashes[path]=hashlib.sha256(raw).hexdigest();layer.stage(path,raw)
    after=census(OverlaySource(layer),names,classes)
    if after['suspect_orphan_pieces'] or before['complete_objects']!=after['complete_objects']:
        raise ValueError('Rock repair left a fragment or changed a complete native boulder')
    return dict(kind='103-native-General-rock-fragments-repaired',repairs=rows,
        suspect_pieces_before=103,suspect_pieces_after=0,maps=len({r['map'] for r in rows}),
        complete_native_boulders_preserved=462,before=before,after=after,
        native_whole_boulder_donors=plan['native_whole_boulder_donors'],
        output_sha256=hashes,only_graphical_IDs_changed=True,
        all_graphics_palettes_metatile_definitions_attributes_and_callbacks_preserved=True,
        collision_elevation_events_dimensions_connections_warps_and_atlas_preserved=True,
        other_banks_not_certified=True,native_ROM_validation_pending=True)


def stage_view_refresh(layer):
    path='src/load_save.c';text=read(layer,path).decode();signature='static void JourneyMigrateSeviiSaveGeometry(void)\n{'
    if text.count(signature)!=1:raise ValueError('Expected the reviewed version4 wrapper')
    body=_braced(text,text.index(signature)+len(signature)-1)
    if 'if(version>=4) return;' not in body or 'VarSet(VAR_JOURNEY_SEVII_GEOMETRY_VERSION,4);' not in body:
        raise ValueError('Previous version4 migration changed')
    old=signature+body+'}'
    new=old.replace(signature,'static void JourneyMigrateSeviiSaveGeometryVersion4(void)\n{',1)+'''
static void JourneyMigrateSeviiSaveGeometry(void)
{
    if(VarGet(VAR_JOURNEY_SEVII_GEOMETRY_VERSION)>=5) return;
    JourneyMigrateSeviiSaveGeometryVersion4();
    // Geometry and actors are unchanged by the rock repair. Refresh only
    // saved background cells, once, including existing version4 batteries.
    CpuFill16(0,gSaveBlock1Ptr->mapView,sizeof(gSaveBlock1Ptr->mapView));
    VarSet(VAR_JOURNEY_SEVII_GEOMETRY_VERSION,5);
}
'''
    layer.stage(path,text.replace(old,new,1))
    path='include/constants/vars.h';text=read(layer,path).decode()
    text,n=re.subn(r'(#define\s+JOURNEY_SEVII_GEOMETRY_VERSION_CURRENT\s+)4\b',r'\g<1>5',text)
    if n!=1:raise ValueError('Expected current save version4')
    layer.stage(path,text)
    return dict(version=5,prior_migrations_preserved=True,only_saved_map_view_refreshed_for_version4=True,
        positions_NPC_templates_and_capture_flags_unchanged_for_version4=True,one_time=True)
