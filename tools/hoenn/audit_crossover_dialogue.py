"""Check the bytes of every active rival speech against the compiled normal font."""
import hashlib
import re
import subprocess
from pathlib import Path

from prepare_crossover_badges import PROGRESSION

ROOT = Path(__file__).resolve().parents[2]
HINT = 'JourneyGalactic_Text_MissingRivals'
VARIABLES = {'{STR_VAR_1}': bytes.fromhex('fd02'), '{STR_VAR_2}': bytes.fromhex('fd03')}
CONTROLS = {r'\n': b'\xfe', r'\p': b'\xfb', '$': b'\xff', **VARIABLES}


def audit(source):
    raw = (source / 'pokeemerald.gba').read_bytes()
    elf = source / 'pokeemerald.elf'
    table = subprocess.check_output([ROOT / '.local/arm-binutils/usr/bin/arm-none-eabi-nm',
                                     '--defined-only', elf], text=True)
    offsets = {m[2]: int(m[1], 16) - 0x08000000 for m in re.finditer(r'^(\w+) [DR] (\w+)$', table, re.M)}
    source_map = (source / 'charmap.txt').read_text()
    glyphs = {m[1]: int(m[2], 16) for m in re.finditer(r"^'(.)'\s*=\s*([0-9A-F]{2})$", source_map, re.M)}
    font = offsets['gFontNormalLatinGlyphWidths']
    names = re.findall(r'COMPOUND_STRING\("([^"]+)"\)', PROGRESSION.read_text())
    texts = PROGRESSION.with_name('late_encounters.inc').read_text()
    gate = (source/'data/scripts/journey_galactic.inc').read_text().split(HINT + '::\n', 1)[1].split('\n\n', 1)[0]
    blocks = dict(re.findall(r'(?m)^(JourneyCrossover_Text_\w+)::\n((?:\t\.string .*\n)+)', texts))
    assert len(blocks) == 17 and len(names) == 8
    blocks[HINT] = gate
    results = {}
    for label, block in blocks.items():
        lines = re.findall(r'\.string "([^"]+)"', block)
        assert lines[-1].endswith('$')
        encoded = bytearray()
        widths = []
        for line in lines:
            for token in re.findall(r'\\[np]|\{STR_VAR_[12]\}|.', line):
                encoded.extend(CONTROLS[token] if token in CONTROLS else bytes((glyphs[token],)))
            for name in names if '{STR_VAR_2}' in line else ('',):
                visible = re.sub(r'(\\[np]|\$)$', '', line).replace('{STR_VAR_1}', 'LUFFY').replace('{STR_VAR_2}', name)
                widths.append(sum(raw[font + glyphs[letter]] for letter in visible))
        at = offsets[label]
        assert raw[at:at + len(encoded)] == encoded, ('Compiled speech differs', label)
        assert max(widths) <= 208, ('Dialogue too wide', label, max(widths))
        results[label] = dict(offset=at, text_sha256=hashlib.sha256(encoded).hexdigest(),
                              bytes=len(encoded), max_pixels=max(widths), lines=len(lines))
    return dict(rom_sha256=hashlib.sha256(raw).hexdigest(), elf_sha256=hashlib.sha256(elf.read_bytes()).hexdigest(),
                normal_font_offset=font, speeches=results)
