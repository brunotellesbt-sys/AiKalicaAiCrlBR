"""Audit translated literals, event logic and fixed dialogue line widths."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from prepare_english_text import PRIOR

ROOT = Path(__file__).resolve().parents[2]
QUOTED = re.compile(r'"(?:\\.|[^"\\])*"')
PORTUGUESE = re.compile(r'\b(?:voce|Você|MAE|Escolha|insignias|recepcao|QUARTAS|Parabens|'
    r'Parabéns|lideres|campeoes|regiao|torneio|santuarios|Sou|seu|sua|presente)\b|[ãõç]', re.I)

def audit(baseline, candidate):
    rows = json.loads((ROOT / 'tools/hoenn/english_text.json').read_text())
    early_marker = candidate / '.journey-early-story-tools'
    early = json.loads(early_marker.read_text()) if early_marker.exists() else None
    checked = []
    for path in rows:
        before, after = [(p / path).read_text() for p in [baseline, candidate]]
        translated = after
        approved_edits = [e for e in early['edits'] if e['path'] == path] if early else []
        # Reconstruct the translated file before the independently hash-checked
        # gameplay overlay. Do not claim its new event logic is text-only.
        for edit in reversed(approved_edits):
            assert translated.count(edit['after']) == 1, path
            translated = translated.replace(edit['after'], edit['before'])
        assert QUOTED.sub('""', before) == QUOTED.sub('""', translated), path
        assert len(QUOTED.findall(before)) == len(QUOTED.findall(translated)), path
        for row in rows[path]:
            assert '"' + row['after'] + '"' in after, (path, row)
            assert '"' + row['before'] + '"' not in after, (path, row)
        checked.append(dict(path=path, non_text_bytes_unchanged=not bool(approved_edits),
            translation_layer_non_text_bytes_unchanged=True,
            approved_early_story_tools_edits=len(approved_edits)))
    expected = json.loads((candidate / '.source-acquired.json').read_text())['sha256']
    for layer in PRIOR + ['english-text', 'special-ball']:
        marker = candidate / ('.journey-' + layer)
        expected.update(json.loads(marker.read_text())['prepared_sha256'])
    for layer in ['route131-sea-access', 'lostelle-habitats', 'tower-habitats', 'early-story-tools', 'mandatory-native-missions', 'sixteen-badge-leagues', 'rusturf-reunion']:
        marker = candidate / ('.journey-' + layer)
        if marker.exists(): expected.update(json.loads(marker.read_text())['prepared_sha256'])
    scanned, literal_count = 0, 0
    for path, digest in expected.items():
        if not path.endswith(('.inc', '.c', '.h', '.s')): continue
        raw = (candidate / path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == digest, path
        literals = QUOTED.findall(raw.decode())
        assert not any(PORTUGUESE.search(t) for t in literals), path
        scanned += 1; literal_count += len(literals)
    charmap = {m[1].replace("\\'", "'"): int(m[2], 16) for m in re.finditer(
        r"^'(.+?)'\s*=\s*([0-9A-F]{2})$", (candidate / 'charmap.txt').read_text(), re.M)}
    font = (candidate / 'src/fonts.c').read_text().split('gFontNormalLatinGlyphWidths[] = {', 1)[1].split('};', 1)[0]
    widths = [int(x) for x in re.findall(r'\d+', font)]
    measured = []
    for path, translations in rows.items():
        if not path.endswith('.inc'): continue
        for row in translations:
            for line in re.split(r'\\[npl]', row['after'].rstrip('$')):
                if '{STR_VAR_1}' in line:
                    value = 'SURF, DIVE and WATERFALL' if 'family' in path else 'quarterfinals' if 'pwt' in path else 'W' * 12
                    line = line.replace('{STR_VAR_1}', value)
                line = line.replace('{STR_VAR_2}', 'W' * 10)
                pixels = sum(widths[charmap[c]] for c in line)
                assert pixels <= 208, (path, line, pixels)
                measured.append(pixels)
    extra = []
    if early:
        from prepare_early_story_tools import TOOLS_SCRIPT
        for text in QUOTED.findall(TOOLS_SCRIPT):
            for line in re.split(r'\\[npl]', text[1:-1].rstrip('$')):
                line = line.replace('{STR_VAR_1}', 'WAILMER PAIL')
                pixels = sum(widths[charmap[c]] for c in line)
                assert pixels <= 208, (line, pixels)
                extra.append(pixels)
        measured.extend(extra)
    mission_marker = candidate / '.journey-mandatory-native-missions'
    mission_lines = []
    if mission_marker.exists():
        for line in json.loads(mission_marker.read_text())['new_dialogue_lines']:
            pixels = sum(widths[charmap[c]] for c in line)
            assert pixels <= 208, (line, pixels)
            mission_lines.append(pixels)
        measured.extend(mission_lines)
    league_lines = []
    league_marker = candidate / '.journey-sixteen-badge-leagues'
    if league_marker.exists():
        for line in json.loads(league_marker.read_text())['dialogue_lines']:
            pixels = sum(widths[charmap[c]] for c in line)
            assert pixels <= 208, (line, pixels)
            league_lines.append(pixels)
        measured.extend(league_lines)
    reunion_lines = []
    reunion_marker = candidate / '.journey-rusturf-reunion'
    if reunion_marker.exists():
        for line in json.loads(reunion_marker.read_text())['dialogue_lines']:
            pixels = sum(widths[charmap[c]] for c in line)
            assert pixels <= 208, (line, pixels)
            reunion_lines.append(pixels)
        measured.extend(reunion_lines)
    return dict(passed=True, rusturf_reunion_lines=len(reunion_lines), game_language='English', translated_literals=sum(map(len, rows.values())),
        text_files=checked, scanned_manifest_source_files=scanned, scanned_quoted_literals=literal_count,
        portuguese_marker_matches=0, checked_dialogue_lines=len(measured),
        maximum_normal_font_line_pixels=max(measured), normal_font_limit_pixels=208,
        early_story_tools_additional_lines=len(extra), mandatory_mission_additional_lines=len(mission_lines), sixteen_badge_league_lines=len(league_lines),
        placeholder_widths_are_known_gift_round_or_name_bounds=True,
        every_dialogue_visually_reviewed=False, full_campaign_playthrough=False,
        rom_sha256=hashlib.sha256((candidate / 'pokeemerald.gba').read_bytes()).hexdigest())

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.baseline, args.candidate)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(result)
