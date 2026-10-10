"""Refresh the native world atlas after joining Kanto's actual coast."""
import argparse,json
from prepare_world_map import prepare as refresh_map
from prepare_kanto_open_sea import CHAIN,LAYER
LAYER_MAP='coastal-world-map'
def prepare(source):return refresh_map(source,layer=LAYER_MAP,chain=CHAIN+[LAYER],refresh=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);print(json.dumps(prepare(p.parse_args().source),indent=2))
