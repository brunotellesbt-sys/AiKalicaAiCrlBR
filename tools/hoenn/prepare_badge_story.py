"""Add the eighteen-badge qualifier, twenty-two-badge Galactic chapter and rivals."""
import argparse
import json
from pathlib import Path

from candidate_layer import Layer
from badge_story_layer import read
from prepare_coastal_closures import PRIOR as PREVIOUS_LAYERS, LAYER as PREVIOUS

LAYER = 'badge-story'
PRIOR = PREVIOUS_LAYERS + [PREVIOUS]


def stage_constants(layer):
    flags = read(layer, 'include/constants/flags.h').decode()
    for name, value in [('FLAG_JOURNEY_QUALIFIER_WON', 0x1050),
                        ('FLAG_JOURNEY_QUALIFIER_CELEBRATED', 0x1051),
                        ('FLAG_JOURNEY_QUALIFIER_NOTIFIED', 0x1052),
                        ('FLAG_JOURNEY_GALACTIC_NOTIFIED', 0x1053)]:
        assert name not in flags
        flags += f'\n#define {name} 0x{value:04X}\n'
    layer.stage('include/constants/flags.h', flags)
    variables = read(layer, 'include/constants/vars.h').decode()
    assert 'VAR_JOURNEY_QUALIFIER_STATE' not in variables
    variables += '\n#define VAR_JOURNEY_QUALIFIER_STATE 0x40DB\n'
    layer.stage('include/constants/vars.h', variables)


def stage_repairs(layer):
    from badge_story_rivals import repair as rivals
    from badge_story_tournament import repair as tournament
    from badge_story_gates import repair as gates
    from badge_story_event import repair as event
    from badge_story_sprites import repair as sprites
    stage_constants(layer)
    return dict(rivals=rivals(layer), qualifier=tournament(layer),
                campaign_gates=gates(layer), field_event=event(layer), avatars=sprites(layer),
                qualifier_badges=18, galactic_badges=22,
                league_requirement='18 badges and qualifier championship',
                uses_pwt_arena_only=True, independent_pwt_state=True)


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
