"""Keep the Surf arrival tile private to the seven connected Sevii coasts."""
import argparse,copy,hashlib,json,struct
from pathlib import Path
from candidate_layer import Layer
from prepare_sevii_surf_embarkation import PRIOR,LAYER as PREVIOUS
from prepare_sevii_surf_connections import ISLANDS

LAYER='sevii-arrival-layout';PRIOR=PRIOR+[PREVIOUS]

def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if old:=layer.existing():return old
    s=layer.source;data=json.loads((s/'data/layouts/layouts.json').read_text());layouts={l['id']:l for l in data['layouts']}
    original=layouts['LAYOUT_ISLAND_HARBOR_FRLG'];path=original['blockdata_filepath'];raw=(s/path).read_bytes()
    dedicated=copy.deepcopy(original);dedicated.update(id='LAYOUT_JOURNEY_SEVII_SURF_ARRIVAL',name='JourneySeviiSurfArrival_Layout',blockdata_filepath='data/layouts/JourneySeviiSurfArrival/map.bin')
    layer.stage(dedicated['blockdata_filepath'],raw);data['layouts'].append(dedicated)
    layer.stage('data/layouts/layouts.json',json.dumps(data,indent=2)+'\n')
    # Restore the original shared non-Sevii arrival tile byte-for-byte.
    restored=bytearray(raw);struct.pack_into('<H',restored,2*(2*original['width']+8),0x32D2)
    expected=json.loads((s/'.journey-sevii-surf-connections').read_text())['original_sha256'][path]
    assert hashlib.sha256(restored).hexdigest()==expected
    layer.stage(path,restored)
    for island in ISLANDS:
        p=f'data/maps/{island}Island_Harbor_Frlg/map.json';m=json.loads((s/p).read_text());assert m['layout']==original['id']
        m['layout']=dedicated['id'];layer.stage(p,json.dumps(m,indent=2)+'\n')
    return layer.finish(shared_harbor_blockdata_restored_sha256=expected,private_layout=dedicated,
                        affected_maps=[i+'Island_Harbor_Frlg' for i in ISLANDS],birth_and_navel_arrival_tiles_unchanged=True,
                        no_port_buildings_boats_or_npcs_changed=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);print(prepare(p.parse_args().source)['layer'])
