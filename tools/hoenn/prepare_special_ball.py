"""Keep Master Ball guaranteed capture ahead of Ultra Beast modifiers."""
import argparse
import hashlib
import json
from pathlib import Path
from prepare_crossing import PIN
from prepare_english_text import PRIOR

def prepare(source):
    source = Path(source)
    marker = source / '.journey-special-ball'
    if marker.exists():
        report = json.loads(marker.read_text())
        for path, digest in report['prepared_sha256'].items():
            if hashlib.sha256((source / path).read_bytes()).hexdigest() != digest:
                raise ValueError('Modified special ball output: ' + path)
        return report
    acquired = json.loads((source / '.source-acquired.json').read_text())
    if acquired['commit'] != PIN: raise ValueError('Unexpected source revision')
    expected = dict(acquired['sha256'])
    for layer in PRIOR + ['english-text']:
        expected.update(json.loads((source / ('.journey-' + layer)).read_text())['prepared_sha256'])
    path = 'src/battle_script_commands.c'
    raw = (source / path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected[path]:
        raise ValueError('Unreviewed ball input')
    old = '''    ball->guaranteedCapture = FALSE;

    if (gSpeciesInfo[battleMon->species].isUltraBeast)'''
    new = '''    ball->guaranteedCapture = FALSE;

    // MASTER BALL remains guaranteed, including against Ultra Beasts.
    if (ballId == BALL_MASTER)
    {
        ball->guaranteedCapture = TRUE;
        return;
    }

    if (gSpeciesInfo[battleMon->species].isUltraBeast)'''
    text = raw.decode()
    if text.count(old) != 1: raise ValueError('Ambiguous ball calculation')
    text = text.replace(old, new)
    redundant = '''    case BALL_MASTER:
        ball->guaranteedCapture = TRUE;
        break;
'''
    if text.count(redundant) != 1: raise ValueError('Ambiguous Master Ball branch')
    text = text.replace(redundant, '')
    report = dict(status='master_ball_ultra_beast_candidate', source_commit=PIN,
        master_ball_guaranteed_for_ultra_beasts=True,
        other_ball_modifiers_unchanged=True, sixteen_badges_capture_gate_unchanged=True,
        original_sha256={path: expected[path]},
        prepared_sha256={path: hashlib.sha256(text.encode()).hexdigest()},
        full_campaign_validated=False)
    (source / path).write_text(text)
    marker.write_text(json.dumps(report, indent=2) + '\n')
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source), indent=2))
