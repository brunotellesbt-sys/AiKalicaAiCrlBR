"""Put Sevii's terminals on their town piers and restore two-way Surf access."""
import argparse
import json
from pathlib import Path

from candidate_layer import Layer
from prepare_dewford_coast_safety import PRIOR as PREVIOUS_LAYERS, LAYER as PREVIOUS
from integrated_sevii_harbors import repair as repair_harbors
from integrated_pier_movement import repair as repair_movement
from integrated_dewford_view import repair as repair_dewford
from integrated_six_landscape import repair as repair_six
from integrated_ocean_seams import repair as repair_ocean

LAYER = 'sevii-integrated-piers'
PRIOR = PREVIOUS_LAYERS + [PREVIOUS]


def prepare(source):
    layer = Layer(source, LAYER, PRIOR)
    if old := layer.existing():
        return old
    harbors = repair_harbors(layer)
    movement = repair_movement(layer)
    six_landscape = repair_six(layer)
    ocean = repair_ocean(layer)
    dewford = repair_dewford(layer)
    return layer.finish(harbors=harbors, movement=movement, dewford=dewford,
                        six_landscape=six_landscape, ocean_seams=ocean,
                        atlas_unchanged=True, gyms_and_campaign_unchanged=True,
                        both_dewford_vendors_preserved=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    result = prepare(parser.parse_args().source)
    print(json.dumps(result, indent=2))
