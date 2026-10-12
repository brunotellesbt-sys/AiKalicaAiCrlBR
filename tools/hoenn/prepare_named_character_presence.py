"""Keep Silph's trigger-only Giovanni actor out of his earlier hideout phase."""
import argparse
from pathlib import Path
from candidate_layer import Layer
from prepare_prison_visibility import PRIOR,LAYER as PREVIOUS
LAYER='named-character-presence';PRIOR=PRIOR+[PREVIOUS]


def prepare(source):
    layer=Layer(source,LAYER,PRIOR)
    if result:=layer.existing():return result
    source=layer.source;p='src/journey_galactic.c';text=(source/p).read_text()
    anchor=' const u8 *script=o->script;'
    assert anchor in text
    text=text.replace(anchor,anchor+'''
 if(group==MAP_GROUP(MAP_SILPH_CO_11F) && num==MAP_NUM(MAP_SILPH_CO_11F)
    && o->graphicsId==OBJ_EVENT_GFX_GIOVANNI)
     return JourneyPendingCampaignEvent(TRUE)==2;
''',1)
    layer.stage(p,text)
    return layer.finish(giovanni_silph_actor_visible_only_in_silph_story_phase=True,trigger_only_null_script_actor_handled=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    print(prepare(p.parse_args().source)['layer'])
