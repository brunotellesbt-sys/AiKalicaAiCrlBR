"""Close Six's full cliffs and repair Dewford movement and animated beaches."""
import argparse
import json
from pathlib import Path

from candidate_layer import Layer
from prepare_sevii_integrated_piers import PRIOR as PREVIOUS_LAYERS, LAYER as PREVIOUS

LAYER = 'coastal-closures'
PRIOR = PREVIOUS_LAYERS + [PREVIOUS]


def stage_repairs(layer):
    from coastal_six_cliffs import repair as repair_six
    from coastal_dewford_movement import repair as repair_dewford
    from coastal_shore_animation import repair as repair_animation
    from coastal_route_identity import repair as repair_route_identity

    return dict(six_cliffs=repair_six(layer),
                dewford_movement=repair_dewford(layer),
                shore_animation=repair_animation(layer),
                route_identity=repair_route_identity(layer),
                atlas_pixels_gyms_campaign_events_and_connections_unchanged=True)


def prepare(source):
    layer = Layer(source, LAYER, PRIOR)
    if old := layer.existing():
        return old
    return layer.finish(**stage_repairs(layer))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source), indent=2))
