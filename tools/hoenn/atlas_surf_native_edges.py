"""Authenticate the new Slateport outlet without replacing its Route134 seam.

This is an authored physical exit, not a recovered historical connection.
Route134 occupies rows0..39 on the eastern boundary. The new exit uses
existing native sea in rows45..58, beyond that connection's actual extent.
Neither native terrain nor events move. Its atlas target follows the drawn
Route134/Pacifidlog line east of Slateport.
"""
from copy import deepcopy
import hashlib

from atlas_surf_source import OPPOSITE

NAME='SlateportCity'
DIRECTION='right'
CONTACTS=tuple((39,y) for y in range(45,59))
ATLAS=(57,98)


def derive(inputs):
    layout=inputs.layout(NAME)
    if (layout['width'],layout['height'],layout['primary_tileset'],layout['secondary_tileset'],layout['layout_version'])!=(
            40,60,'gTileset_General','gTileset_Slateport','emerald'):
        raise ValueError('Slateport native outlet layout changed')
    labels,components=inputs.water_components(NAME)
    if not all(inputs.water(NAME,*p) and inputs.word(NAME,*p)>>12==1 and labels[p]==0 for p in CONTACTS):
        raise ValueError('Slateport outlet is not the reviewed existing native height-one sea')
    for c in inputs.maps[NAME].get('connections') or []:
        if c['direction']!=DIRECTION:continue
        target=inputs.by_id[c['map']];height=inputs.layout(target)['height']
        if any(c['offset']<=y<c['offset']+height for x,y in CONTACTS):
            raise ValueError(('Slateport new outlet would shadow a native connection',target))
    cells=sorted(components[0],key=lambda p:(p[1],p[0]))
    path=layout['blockdata_filepath'];digest=hashlib.sha256(inputs.read(path)).hexdigest()
    return dict(native_map=NAME,component=0,seed=list(cells[0]),water_cells=len(cells),
        component_sha256=hashlib.sha256(';'.join(f'{x},{y}' for x,y in cells).encode()).hexdigest(),
        authored_new_native_edge='slateport-eastern-ocean-outside-route134',
        source_wet_edge_witnesses=[],authored_native_edge_witnesses=[dict(native_tile=list(p),
            direction=OPPOSITE[DIRECTION],native_word=inputs.word(NAME,*p),
            native_blockdata_sha256=digest,existing_connection_overlap=False) for p in CONTACTS])


def extend_inventory(inputs,inventory):
    result=deepcopy(inventory);row=derive(inputs)
    if any((r['native_map'],r['component'])==(NAME,0) for r in result['adapters']):
        raise ValueError('Slateport authored outlet duplicates an inventory component')
    result['adapters'].append(row)
    return result


def authenticate(inputs,row):
    actual=deepcopy(row);actual.pop('allow_extended_native_contacts',None)
    if actual!=derive(inputs):raise ValueError('Authored Slateport outlet differs from actual free native edge')


def donor(inputs):
    """Sample complete native water/reef from Route109's identical bank pair."""
    source='Route109';layout=inputs.layout(source)
    if [layout[k] for k in ('primary_tileset','secondary_tileset','layout_version')]!=[
            'gTileset_General','gTileset_Slateport','emerald']:
        raise ValueError('Slateport donor bank pair changed')
    words=inputs.words(source);width=layout['width']
    wet=words.index(0x1170);reef=words.index(0x15f9)
    spec=dict(map=source,water_tile=[wet%width,wet//width],reef_tile=[reef%width,reef//width])
    if not inputs.water(source,*spec['water_tile']):raise ValueError('Slateport native donor lost Surf behavior')
    return spec,dict(map=source,banks=[layout[k] for k in ('primary_tileset','secondary_tileset','layout_version')],
        water_word=0x1170,reef_word=0x15f9,blockdata=layout['blockdata_filepath'],
        blockdata_sha256=hashlib.sha256(inputs.read(layout['blockdata_filepath'])).hexdigest(),
        reef_basis='complete one-metatile reef from native Route109 in the identical General/Slateport banks',
        visual_review_pending=True)
