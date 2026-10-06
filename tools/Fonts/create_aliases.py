"""Generate OFL font aliases used by WPF under Wine; requires fontTools.

These are modified Carlito and Liberation fonts, not Microsoft fonts.
The glyphs remain unchanged. Only family/name records change for compatibility.
"""
from pathlib import Path
from fontTools.ttLib import TTFont
import argparse


def generate(carlito, liberation, output):
    output.mkdir(parents=True, exist_ok=True)
    mapping = []
    for source in carlito.glob('*.ttf'):
        mapping.append((source, 'Carlito', 'Calibri', source.name.replace('Carlito', 'CalibriCompat')))
    for filename, aliases in [
        ('LiberationSans-Regular.ttf', ['Arial', 'Segoe UI', 'Tahoma', 'MS Sans Serif']),
        ('LiberationMono-Regular.ttf', ['Consolas', 'Courier New']),
        ('LiberationSerif-Regular.ttf', ['Times New Roman']),
    ]:
        source = liberation / filename
        original = TTFont(source)['name'].getDebugName(1)
        for alias in aliases:
            mapping.append((source, original, alias, alias.replace(' ', '') + 'Compat.ttf'))
    for source, original, alias, filename in mapping:
        font = TTFont(source, recalcTimestamp=False)
        for record in font['name'].names:
            if record.nameID not in {1, 2, 3, 4, 6, 16, 17, 18, 21, 22}:
                continue  # Preserve copyright, manufacturer, description and license records.
            try:
                text = record.toUnicode()
            except UnicodeDecodeError:
                continue
            replacement = text.replace(original, alias)
            if original.replace(' ', '') != original:
                replacement = replacement.replace(original.replace(' ', ''), alias.replace(' ', ''))
            if replacement != text:
                record.string = replacement.encode(record.getEncoding())
        font.save(output / filename)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('carlito', type=Path)
    parser.add_argument('liberation', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    generate(args.carlito, args.liberation, args.output)
