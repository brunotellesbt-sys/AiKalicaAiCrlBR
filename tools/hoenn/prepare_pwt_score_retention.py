"""Keep real defeated-Pokémon totals until the PWT resolves its standings."""
import argparse,json,re
from pathlib import Path
from candidate_layer import Layer
from prepare_special_encounter_field_rules import PRIOR,LAYER as PREVIOUS
LAYER='pwt-score-retention';PRIOR=PRIOR+[PREVIOUS]
ROOT=Path(__file__).resolve().parents[2]
def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if old:=layer.existing():return old
    p='src/battle_main.c';text=(layer.source/p).read_text()
    old='if (!(gBattleTypeFlags & (BATTLE_TYPE_FRONTIER | BATTLE_TYPE_ROAMER)))'
    assert text.count(old)==1
    layer.stage(p,text.replace(old,'if (!(gBattleTypeFlags & (BATTLE_TYPE_FRONTIER | BATTLE_TYPE_ROAMER | BATTLE_TYPE_PWT)))'))
    ref=json.loads((ROOT/'tools/hoenn/catalog_metadata.json').read_text())['species']
    info=json.loads((layer.source/'.journey-special-encounter-workshop').read_text())
    event_names={ref[str(row['root'])]['name'] for row in info['event_families']}
    # Older native pools contain whitespace before the inner initializer.
    # Parse both formats and refill each removed slot from its own habitat.
    for p in ['include/journey_wild_data.h','include/journey_generation4_pools.h']:
        text=(layer.source/p).read_text()
        def clean(m):
            values=[v.strip() for v in m[4].split(',') if v.strip()]
            if not event_names.intersection(values):return m[0]
            kept=[v for v in values if v not in event_names]
            replaced=[v if v not in event_names else kept[i%len(kept)] for i,v in enumerate(values)] if kept else []
            return '{'+m[1]+','+m[2]+','+str(len(replaced))+',{'+','.join(replaced)+'}}'+m[5]
        text=re.sub(r'^\{(MAP_\w+),\s*(\d+),\s*(\d+),\s*\{([^}]*)\}\}(,?)$',clean,text,flags=re.M)
        assert not any(event_names.intersection(v.strip() for v in m[3].split(',')) for m in re.findall(r'^\{(MAP_\w+),\s*(\d+),\s*(\d+),\s*\{([^}]*)\}\}(,?)$',text,re.M))
        layer.stage(p,text)
    return layer.finish(pwt_enemy_hp_preserved_until_scoring=True,event_families_removed_from_both_generation_pools=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    print(prepare(p.parse_args().source)['layer'])
