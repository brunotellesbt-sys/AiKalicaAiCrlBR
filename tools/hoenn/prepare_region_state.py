"""Separate FRLG story flags, badges and champion state on the candidate.

Expands saved flag storage: this candidate REQUIRES A NEW SAVE. Does not
replace the released game, migrate old saves or finish either campaign.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

from prepare_crossing import PIN


def prepare(source):
    source = Path(source)
    markers = ['.journey-hoenn-crossing', '.journey-worldsea', '.journey-westsea']
    previous = [json.loads((source / p).read_text()) for p in markers]
    acquired = json.loads((source / '.source-acquired.json').read_text())
    if acquired['commit'] != PIN: raise ValueError('Unexpected base')
    marker = source / '.journey-region-state'
    if marker.exists():
        report = json.loads(marker.read_text())
        for p, digest in report['prepared_sha256'].items():
            if hashlib.sha256((source / p).read_bytes()).hexdigest() != digest:
                raise ValueError('Modified regional state output: ' + p)
        return report
    expected = dict(acquired['sha256'])
    for r in previous: expected.update(r['prepared_sha256'])
    outputs, originals = {}, {}

    def stage(path, value):
        digest = hashlib.sha256((source / path).read_bytes()).hexdigest()
        if digest != expected[path]: raise ValueError('Unreviewed modification: ' + path)
        originals[path] = digest; outputs[path] = value.encode()

    path = 'include/constants/flags.h'
    text = (source / path).read_text()
    before, frlg = text.split('// FRLG flags\n', 1)
    renamed = {}
    def move(match):
        name, value = match.group(2), int(match.group(3), 16)
        if not 0x15C <= value <= 0xAAD: return match.group(0)
        new = value + 0x1000
        renamed[name] = dict(original=value, allocated=new)
        return match.group(1) + name + ' ' + hex(new)
    frlg = re.sub(r'^(#define\s+)(FLAG_\w+)\s+(0x[0-9a-fA-F]+)\b', move, frlg, flags=re.M)
    if len(renamed) != 763: raise ValueError('Unexpected FRLG flag catalog')
    before = before.replace('#define FLAGS_COUNT (DAILY_FLAGS_END + 1)', '#define FLAGS_COUNT (JOURNEY_FLAGS_END + 1)')
    definitions = '\n// Persistent region-specific state. Not daily or temporary flags.\n'
    for i in range(8): definitions += f'#define FLAG_KANTO_BADGE{i+1:02d}_GET {hex(0x1AB0+i)}\n'
    definitions += '#define FLAG_KANTO_GAME_CLEAR 0x1AB8\n#define JOURNEY_FLAGS_END 0x1ABF\n'
    stage(path, before + '// FRLG flags\n' + definitions + frlg)

    path = 'src/event_data.c'
    text = (source / path).read_text()
    anchor = 'u8 *GetFlagPointer(u16 id)\n'
    helper = '''// Badge and champion checks in shared engine code follow the active
// region. Trainer flags and unrelated global features are never remapped.
static u16 ResolveJourneyRegionFlag(u16 id)
{
    if (isFrlg)
    {
        if (id >= FLAG_BADGE01_GET && id <= FLAG_BADGE08_GET)
            return FLAG_KANTO_BADGE01_GET + id - FLAG_BADGE01_GET;
        if (id == FLAG_SYS_GAME_CLEAR)
            return FLAG_KANTO_GAME_CLEAR;
    }
    return id;
}

'''
    if text.count(anchor) != 1: raise ValueError('Unexpected event_data source')
    text = text.replace(anchor, helper + anchor)
    for signature in ['u8 FlagSet(u16 id)', 'u8 FlagToggle(u16 id)', 'u8 FlagClear(u16 id)', 'bool8 FlagGet(u16 id)']:
        anchor = signature + '\n{\n'
        if text.count(anchor) != 1: raise ValueError('Unexpected flag operation')
        text = text.replace(anchor, anchor + '    id = ResolveJourneyRegionFlag(id);\n')
    # GetFlagPointer is also used by engine code directly. Resolve the same
    # bank there; the flag operations already updated id for correct bit masks.
    text = text.replace('u8 *GetFlagPointer(u16 id)\n{\n', 'u8 *GetFlagPointer(u16 id)\n{\n    id = ResolveJourneyRegionFlag(id);\n')
    stage(path, text)

    path = 'data/maps/EverGrandeCity_PokemonLeague_1F/scripts.inc'
    text = (source / path).read_text()
    anchor = '\tgoto_if_unset FLAG_BADGE06_GET, EverGrandeCity_PokemonLeague_1F_EventScript_NotAllBadges\n'
    if text.count(anchor) != 1: raise ValueError('Unexpected Hoenn league guard')
    checks = ''.join(f'\tgoto_if_unset FLAG_BADGE{i:02d}_GET, EverGrandeCity_PokemonLeague_1F_EventScript_NotAllBadges\n' for i in range(1, 9))
    text = text.replace(anchor, checks)
    text = text.replace('@ The door guards only check for FLAG_BADGE06_GET because Winonas badge is the only one that can be skipped', '@ Journey: all eight regional badges are required, regardless of gym order.')
    stage(path, text)
    for p, raw in outputs.items(): (source / p).write_bytes(raw)
    report = dict(status='experimental_regional_state_not_complete_campaign', source_commit=PIN,
        requires_new_save=True, frlg_flags=renamed, kanto_badges=list(range(0x1AB0, 0x1AB8)),
        kanto_champion=0x1AB8, flags_count=0x1AC0, original_sha256=originals,
        prepared_sha256={p: hashlib.sha256(raw).hexdigest() for p, raw in outputs.items()},
        full_story_validated=False, custom_journey_migrated=False)
    marker.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args(); print(json.dumps(prepare(args.source), indent=2))
