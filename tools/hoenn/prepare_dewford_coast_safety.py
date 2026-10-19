"""Repair Dewford's bridge collision and its complete neighboring coast view."""
import argparse
import json
from pathlib import Path
from candidate_layer import Layer
from prepare_extra_gyms import PRIOR, LAYER as PREVIOUS
from dewford_bridge_safety import repair as repair_bridge
from dewford_coast_landscape import repair as repair_landscape
from dewford_coast_view import repair as repair_view
from coastal_cave_finishing import repair as repair_caves
from coastal_pier_safety import repair as repair_piers

LAYER = 'dewford-coast-safety'
PRIOR = PRIOR + [PREVIOUS]


def prepare(source):
    layer = Layer(source, LAYER, PRIOR)
    if old := layer.existing():
        return old
    bridge = repair_bridge(layer)
    landscape = repair_landscape(layer)
    view = repair_view(layer)
    caves = repair_caves(layer)
    piers = repair_piers(layer)
    return layer.finish(bridge=bridge, landscape=landscape, view=view,
                        caves=caves, piers=piers,
                        atlas_unchanged=True, gyms_and_campaign_unchanged=True,
                        both_dewford_vendors_preserved=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    print(json.dumps(prepare(p.parse_args().source), indent=2))
