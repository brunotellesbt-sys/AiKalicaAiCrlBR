"""Retarget the seven obsolete ferry arrivals to authentic integrated piers.

Keep the native Seagallop scene and existing terminal/NPC scripts. This changes
only seven destination rows and seven old immediate-arrival warp commands.
"""
import hashlib
import re

from atlas_surf_pois import current_ports
from badge_story_layer import read


def stage(layer, inputs):
    ports=current_ports(inputs)
    if len(ports)!=7 or {p['island'] for p in ports}!={'One','Two','Three','Four','Five','Six','Seven'}:
        raise ValueError('Ferry arrival repair requires all seven authenticated integrated piers')
    c_path='src/seagallop.c';script_path='data/scripts/journey_campaign_gates.inc'
    original_c=read(layer,c_path).decode();original_script=read(layer,script_path).decode()
    c,script=original_c,original_script;records=[]
    for number,port in enumerate(ports,2):
        island=port['island']
        expected_order=('One','Two','Three','Four','Five','Six','Seven')[number-2]
        if island!=expected_order:
            raise ValueError('Parent pier order changed; do not silently target another island')
        old_name=island+'Island_Harbor_Frlg'
        old_id=inputs.maps[old_name]['id']
        new_name,x,y=port['boarding']['dry']
        new_id=inputs.maps[new_name]['id'];packed=inputs.identities[new_name]
        if not (packed>>8)<128 or not (packed&255)<128 or not 0<=x<128 or not 0<=y<128:
            raise ValueError('Seagallop destination exceeds native signed byte fields')
        label='SEAGALLOP_'+island.upper()+'_ISLAND'
        pattern=(r'(\['+label+r'\]\s*=\s*)\{MAP_GROUP\('+old_id+r'\),\s*MAP_NUM\('
                 +old_id+r'\),\s*0x08,\s*0x05\}')
        c,count=re.subn(pattern,lambda m:m[1]+'{MAP_GROUP('+new_id+'), MAP_NUM('+new_id+'), '+str(x)+', '+str(y)+'}',c)
        if count!=1:
            raise ValueError(('Old Seagallop row changed or was already repaired',label,count))
        anchor='Journey_Ferry_Destination'+str(number)+'::'
        match=re.search(re.escape(anchor)+r'\n.*?(?=\n[A-Za-z_]\w*::|\Z)',script,re.S)
        if match is None:
            raise ValueError(('Old ferry arrival script missing',anchor))
        block=match[0]
        command='\twarp '+old_id+', 8, 5'
        if block.count(command)!=1:
            raise ValueError(('Old ferry command changed or was already repaired',anchor))
        updated=block.replace(command,'\twarp '+new_id+', '+str(x)+', '+str(y))
        script=script[:match.start()]+updated+script[match.end():]
        records.append(dict(island=island,old_map=old_name,old_id=old_id,
                            destination=[new_name,x,y],destination_id=new_id,
                            native_dry_terrain=port['dry_terrain'],wet_return=port['water_terrain']))
    layer.stage(c_path,c);layer.stage(script_path,script)
    return dict(kind='atlas-integrated-pier-ferry-arrivals',arrivals=records,
                old_seven_destination_rows_repointed=True,old_seven_arrival_scripts_repointed=True,
                terminal_npcs_events_layouts_and_ferry_scene_unchanged=True,
                source_before_sha256={c_path:hashlib.sha256(original_c.encode()).hexdigest(),
                                      script_path:hashlib.sha256(original_script.encode()).hexdigest()},
                native_boarding_roundtrip_pending=True,native_validated=False)
