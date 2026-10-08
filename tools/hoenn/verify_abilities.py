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
    if layer == 'league-display':
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
    parser.add_argument('--layer', choices=['abilities', 'mega-art', 'story-aftermath', 'league-access', 'league-completion', 'league-history', 'league-display'], default='abilities')
    args = parser.parse_args()
    verify(args.source, args.candidate, args.output, args.layer)
