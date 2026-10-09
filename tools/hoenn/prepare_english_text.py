"""Translate integration dialogue to English without changing event logic."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from prepare_crossing import PIN
from prepare_family import LAYERS_BEFORE

HERE = Path(__file__).resolve().parent
PRIOR = LAYERS_BEFORE + ['family', 'travel-rules', 'birth', 'wild', 'habitats',
    'sanctuaries', 'ecology', 'abilities', 'mega-art', 'story-aftermath',
    'league-access', 'league-completion', 'league-history', 'league-display',
    'family-postgame', 'pwt', 'frontier-travel', 'story-puzzles', 'aqua-episodes',
    'seafloor-access', 'water-continue', 'cave-access', 'sky-pillar-access']

def prepare(source):
    source = Path(source)
    marker = source / '.journey-english-text'
    if marker.exists():
        report = json.loads(marker.read_text())
        for path, digest in report['prepared_sha256'].items():
            if hashlib.sha256((source / path).read_bytes()).hexdigest() != digest:
                raise ValueError('Modified English text output: ' + path)
        return report
    acquired = json.loads((source / '.source-acquired.json').read_text())
    if acquired['commit'] != PIN: raise ValueError('Unexpected source revision')
    expected = dict(acquired['sha256'])
    for layer in PRIOR:
        expected.update(json.loads((source / ('.journey-' + layer)).read_text())['prepared_sha256'])
    translations = json.loads((HERE / 'english_text.json').read_text())
    outputs, originals = {}, {}
    for path, rows in translations.items():
        original = (source / path).read_bytes()
        digest = hashlib.sha256(original).hexdigest()
        if digest != expected[path]: raise ValueError('Unreviewed English input: ' + path)
        text = original.decode()
        for row in rows:
            # Replace complete quoted literals only, preserving script commands,
            # labels, C declarations, variables and placeholder identities.
            before, after = '"' + row['before'] + '"', '"' + row['after'] + '"'
            if not text.count(before): raise ValueError('Missing English text anchor: ' + path)
            if sorted(re.findall(r'\{[^}]+\}', before)) != sorted(re.findall(r'\{[^}]+\}', after)):
                raise ValueError('Changed text placeholders: ' + path)
            text = text.replace(before, after, 1)
        outputs[path] = text.encode()
        originals[path] = digest
    preserved = {}
    for path in ['src/journey_special.c', 'src/journey_campaign_gates.c',
                 'src/journey_gym_scaling.c', 'src/journey_wild.c',
                 'src/field_player_avatar.c', 'include/constants/flags.h']:
        digest = hashlib.sha256((source / path).read_bytes()).hexdigest()
        if digest != expected[path]: raise ValueError('Unreviewed preserved input: ' + path)
        preserved[path] = digest
    report = dict(status='english_game_text_candidate', source_commit=PIN,
        game_language='English', conversation_and_documents_language='Portuguese',
        translated_literals=sum(len(rows) for rows in translations.values()),
        script_and_battle_logic_unchanged=True, placeholders_preserved=True,
        save_layout_unchanged=True, full_campaign_validated=False,
        original_sha256=originals, preserved_native_sha256=preserved,
        prepared_sha256={p: hashlib.sha256(v).hexdigest() for p, v in outputs.items()})
    for path, output in outputs.items(): (source / path).write_bytes(output)
    marker.write_text(json.dumps(report, indent=2) + '\n')
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source), indent=2))
