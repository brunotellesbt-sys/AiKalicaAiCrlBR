"""Exercise compiled NPC stone/held-item evolution boundaries in mGBA."""
from pathlib import Path
import hashlib, json

ROOT = Path(__file__).resolve().parents[2]
bootstrap_path = ROOT / 'tools/hoenn/validate_trainer_levels.py'
bootstrap = bootstrap_path.read_text().split('\nchecks=[]')[0]
exec(compile(bootstrap, str(bootstrap_path), 'exec'))
initial_sha = hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest()

# Stone and former trade-with-item evolutions, including alternate-method cases.
cases = [
    ('Vileplume', 45, 44, 30),
    ('Clefable', 36, 35, 30),
    ('Ninetales', 38, 37, 35),
    ('Arcanine', 59, 58, 40),
    ('Scizor', 212, 123, 35),
    ('Kingdra', 230, 117, 40),
    ('Ludicolo', 272, 271, 30),
    ('Milotic', 350, 349, 40),
    ('Magnezone', 462, 82, 40),
]
checks = []
for name, evolved, previous, threshold in cases:
    below = native('JourneyTrainerSpecies', evolved, threshold - 1)
    at = native('JourneyTrainerSpecies', evolved, threshold)
    assert below == previous, (name, threshold - 1, below, previous)
    assert at == evolved, (name, threshold, at, evolved)
    checks.append(dict(species=name, minimum_level=threshold,
                       below_threshold_species=below, at_threshold_species=at))

# The ancestry check still reaches Lotad, rather than stopping at Lombre.
assert native('JourneyTrainerSpecies', 272, 5) == 270
assert hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest() == initial_sha
lib.stop()
(args.output / 'trainer-item-evolutions.json').write_text(json.dumps(dict(
    passed=True, rom_sha256=initial_sha, checks=checks,
    native_species_selection=True, full_ancestry_checked=True,
    player_item_evolution_tested=False), indent=2) + '\n')
print('Native NPC item evolution thresholds passed: 30, 35 and 40', flush=True)
