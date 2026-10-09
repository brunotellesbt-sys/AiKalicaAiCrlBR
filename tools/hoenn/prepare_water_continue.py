"""Restore the underwater avatar by map type when continuing a saved game."""
import argparse
import hashlib
import json
from pathlib import Path
from prepare_crossing import PIN
from prepare_family import LAYERS_BEFORE

def prepare(source):
    source = Path(source)
    marker = source / '.journey-water-continue'
    if marker.exists():
        report = json.loads(marker.read_text())
        for path, digest in report['prepared_sha256'].items():
            if hashlib.sha256((source / path).read_bytes()).hexdigest() != digest:
                raise ValueError('Modified Water Continue output: ' + path)
        return report
    acquired = json.loads((source / '.source-acquired.json').read_text())
    if acquired['commit'] != PIN: raise ValueError('Unexpected source revision')
    expected = dict(acquired['sha256'])
    for layer in LAYERS_BEFORE + ['family', 'travel-rules', 'birth', 'wild', 'habitats',
                                 'sanctuaries', 'ecology', 'abilities', 'mega-art', 'story-aftermath',
                                 'league-access', 'league-completion', 'league-history', 'league-display',
                                 'family-postgame', 'pwt', 'frontier-travel', 'story-puzzles', 'aqua-episodes', 'seafloor-access']:
        expected.update(json.loads((source / ('.journey-' + layer)).read_text())['prepared_sha256'])
    def checked(path):
        raw = (source / path).read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected[path]:
            raise ValueError('Unreviewed Water Continue input: ' + path)
        return raw
    path = 'src/field_player_avatar.c'
    body = checked(path).decode()
    anchor = 'static u8 GetPlayerAvatarStateTransitionByGraphicsId(u16 graphicsId, u8 gender)\n{\n    u8 i;\n'
    if body.count(anchor) != 1: raise ValueError('Ambiguous avatar state lookup')
    output = body.replace(anchor, anchor + '\n    // Kanto uses the same graphics for Surf and Dive. Restore by map type.\n    if (GetCurrentMapType() == MAP_TYPE_UNDERWATER)\n        return PLAYER_AVATAR_FLAG_UNDERWATER;\n').encode()
    preserved = {}
    for other in ['data/maps/SeafloorCavern_Entrance/scripts.inc',
                  'data/maps/MossdeepCity_StevensHouse/scripts.inc',
                  'data/maps/SeafloorCavern_Room9/scripts.inc', 'src/field_move.c',
                  'src/journey_campaign_gates.c', 'src/journey_gym_scaling.c',
                  'include/constants/flags.h', 'data/layouts/SeafloorCavern_Entrance/map.bin', 'src/overworld.c']:
        checked(other); preserved[other] = expected[other]
    report = dict(status='underwater_continue_candidate', source_commit=PIN,
                  map_type_restores_underwater_before_shared_sprite_lookup=True,
                  original_avatar_graphics_tables_retained=True, land_and_surface_lookup_retained=True,
                  native_dive_surf_and_boss_missions_retained=True,
                  badge_scaling_and_save_layout_unchanged=True, new_flags_allocated=False,
                  full_campaign_validated=False, original_sha256={path: expected[path]},
                  preserved_native_sha256=preserved, prepared_sha256={path: hashlib.sha256(output).hexdigest()})
    (source / path).write_bytes(output)
    marker.write_text(json.dumps(report, indent=2) + '\n')
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source), indent=2))
