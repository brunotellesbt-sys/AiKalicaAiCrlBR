"""Display four-digit National Dex numbers in Kanto Hall of Fame."""
import argparse
import hashlib
import json
from pathlib import Path
from prepare_crossing import PIN
from prepare_family import LAYERS_BEFORE


def prepare(source):
    source = Path(source)
    marker = source / '.journey-league-display'
    if marker.exists():
        report = json.loads(marker.read_text())
        for path, digest in report['prepared_sha256'].items():
            assert hashlib.sha256((source / path).read_bytes()).hexdigest() == digest, path
        return report
    acquired = json.loads((source / '.source-acquired.json').read_text())
    assert acquired['commit'] == PIN
    expected = dict(acquired['sha256'])
    for layer in LAYERS_BEFORE + ['family', 'travel-rules', 'birth', 'wild', 'habitats',
                                 'sanctuaries', 'ecology', 'abilities', 'mega-art', 'story-aftermath',
                                 'league-access', 'league-completion', 'league-history']:
        expected.update(json.loads((source / ('.journey-' + layer)).read_text())['prepared_sha256'])
    originals, inputs, outputs = {}, {}, {}

    def read(path):
        raw = (source / path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected[path], path
        originals[path] = expected[path]
        if path in acquired['sha256']:
            inputs[path] = acquired['sha256'][path]
        return raw.decode()

    path = 'src/hall_of_fame_frlg.c'
    body = read(path)
    needle = """            text[0] = (dexNumber / 100) + CHAR_0;
            text[1] = ((dexNumber %= 100) / 10) + CHAR_0;
            text[2] = (dexNumber % 10) + CHAR_0;"""
    assert body.count(needle) == 1
    body = body.replace(needle, """            ConvertIntToDecimalStringN(text, dexNumber, STR_CONV_MODE_LEADING_ZEROS, dexNumber >= 1000 ? 4 : 3);""")
    needle = """            text[0] = text[1] = text[2] = CHAR_QUESTION_MARK;
        }
        text[3] = EOS;"""
    assert body.count(needle) == 1
    body = body.replace(needle, """            text[0] = text[1] = text[2] = CHAR_QUESTION_MARK;
            text[3] = EOS;
        }""")
    outputs[path] = body.encode()
    report = dict(status='four_digit_kanto_hall_of_fame_candidate', source_commit=PIN,
                  dex_numbers_above_999=True, three_digit_style_below_1000_preserved=True,
                  unknown_species_question_marks_preserved=True, save_layout_unchanged=True,
                  species_and_battle_rules_unchanged=True, full_campaign_validated=False,
                  input_sha256=inputs, original_sha256=originals,
                  prepared_sha256={p: hashlib.sha256(raw).hexdigest() for p, raw in outputs.items()})
    for path, raw in outputs.items():
        (source / path).write_bytes(raw)
    marker.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    print(json.dumps(prepare(parser.parse_args().source), indent=2))
