"""Replay a battle overlay from its validated preceding layer."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from prepare_abilities import prepare


def verify(source, candidate, output, layer='abilities'):
    source, candidate, output = map(Path, [source, candidate, output])
    if layer == 'eastern-sea-union':
        from prepare_eastern_sea_union import prepare as prepare_layer
    elif layer == 'sea-landscapes':
        from prepare_sea_landscapes import prepare as prepare_layer
    elif layer == 'rusturf-reunion':
        from prepare_rusturf_reunion import prepare as prepare_layer
    elif layer == 'sixteen-badge-leagues':
        from prepare_sixteen_badge_leagues import prepare as prepare_layer
    elif layer == 'mandatory-native-missions':
        from prepare_mandatory_native_missions import prepare as prepare_layer
    elif layer == 'early-story-tools':
        from prepare_early_story_tools import prepare as prepare_layer
    elif layer == 'tower-habitats':
        from prepare_tower_habitats import prepare as prepare_layer
    elif layer == 'lostelle-habitats':
        from prepare_lostelle_habitats import prepare as prepare_layer
    elif layer == 'route131-sea-access':
        from prepare_route131_sea_access import prepare as prepare_layer
    elif layer == 'special-ball':
        from prepare_special_ball import prepare as prepare_layer
    elif layer == 'english-text':
        from prepare_english_text import prepare as prepare_layer
    elif layer == 'sky-pillar-access':
        from prepare_sky_pillar_access import prepare as prepare_layer
    elif layer == 'cave-access':
        from prepare_cave_access import prepare as prepare_layer
    elif layer == 'water-continue':
        from prepare_water_continue import prepare as prepare_layer
    elif layer == 'seafloor-access':
        from prepare_seafloor_access import prepare as prepare_layer
    elif layer == 'aqua-episodes':
        from prepare_aqua_episodes import prepare as prepare_layer
    elif layer == 'story-puzzles':
        from prepare_story_puzzles import prepare as prepare_layer
    elif layer == 'frontier-travel':
        from prepare_frontier_travel import prepare as prepare_layer
    elif layer == 'pwt':
        from prepare_pwt import prepare as prepare_layer
    elif layer == 'family-postgame':
        from prepare_family_postgame import prepare as prepare_layer
    elif layer == 'league-display':
        from prepare_league_display import prepare as prepare_layer
    elif layer == 'league-history':
        from prepare_league_history import prepare as prepare_layer
    elif layer == 'league-completion':
        from prepare_league_completion import prepare as prepare_layer
    elif layer == 'league-access':
        from prepare_league_access import prepare as prepare_layer
    elif layer == 'story-aftermath':
        from prepare_story_aftermath import prepare as prepare_layer
    elif layer == 'mega-art':
        from prepare_mega_art import prepare as prepare_layer
    else:
        prepare_layer = prepare
    installed = json.loads((candidate / ('.journey-' + layer)).read_text())
    with tempfile.TemporaryDirectory(prefix='ability-replay-', dir='/tmp') as directory:
        replay = Path(directory)
        shutil.copy2(source / '.source-acquired.json', replay)
        for marker in source.glob('.journey-*'):
            if marker.is_file() and marker.name != '.journey-' + layer:
                shutil.copy2(marker, replay)
        required = dict(installed.get('preserved_native_sha256', {}))
        required.update(installed['original_sha256'])
        for path, digest in required.items():
            assert hashlib.sha256((source / path).read_bytes()).hexdigest() == digest, path
            (replay / path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source / path, replay / path)
        generated = prepare_layer(replay)
        assert generated == installed
        assert prepare_layer(replay) == installed  # Same-layer idempotence checks installed bytes.
        for path, digest in installed['prepared_sha256'].items():
            assert hashlib.sha256((candidate / path).read_bytes()).hexdigest() == digest, path
    output.mkdir(parents=True, exist_ok=True)
    (output / 'preparation.json').write_text(json.dumps(installed, indent=2) + '\n')
    result = dict(passed=True, files=len(installed['prepared_sha256']),
                  baseline_rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
                  rom_sha256=hashlib.sha256((candidate / 'pokeemerald.gba').read_bytes()).hexdigest(),
                  deterministic_replay=True, idempotent=True)
    (output / 'reproduction.json').write_text(json.dumps(result, indent=2) + '\n')
    print(result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--layer', choices=['abilities', 'mega-art', 'story-aftermath', 'league-access', 'league-completion', 'league-history', 'league-display', 'family-postgame', 'pwt', 'frontier-travel', 'story-puzzles', 'aqua-episodes', 'seafloor-access', 'water-continue', 'cave-access', 'sky-pillar-access', 'english-text', 'special-ball', 'route131-sea-access', 'lostelle-habitats', 'tower-habitats', 'early-story-tools', 'mandatory-native-missions', 'sixteen-badge-leagues', 'rusturf-reunion', 'sea-landscapes', 'eastern-sea-union'], default='abilities')
    args = parser.parse_args()
    verify(args.source, args.candidate, args.output, args.layer)
