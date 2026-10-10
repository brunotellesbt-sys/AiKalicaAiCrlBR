"""Restore Wanda's reunion after removing Rock Smash obstacles."""
import argparse
import hashlib
import json
from pathlib import Path
from prepare_crossing import PIN
from prepare_early_story_tools import PRECEDING

LAYER = 'rusturf-reunion'
PATH = 'data/maps/RusturfTunnel/scripts.inc'
LINES = ['The path is clear now!', 'I can finally see WANDA.', 'Thank you for helping us.', 'Please take this TM!']

def prepare(source):
    source = Path(source)
    marker = source / ('.journey-' + LAYER)
    if marker.exists():
        report = json.loads(marker.read_text())
        for path, digest in (report['prepared_sha256'] | report['preserved_native_sha256']).items():
            if hashlib.sha256((source / path).read_bytes()).hexdigest() != digest:
                raise ValueError('Modified reunion output: ' + path)
        return report
    acquired = json.loads((source / '.source-acquired.json').read_text())
    if acquired['commit'] != PIN: raise ValueError('Unexpected source revision')
    expected = dict(acquired['sha256'])
    for layer in PRECEDING + ['early-story-tools', 'mandatory-native-missions', 'sixteen-badge-leagues']:
        expected.update(json.loads((source / ('.journey-' + layer)).read_text())['prepared_sha256'])
    preserved = {}
    for path in [PATH, 'src/journey_campaign_gates.c', 'src/journey_gym_scaling.c', 'src/journey_wild.c', 'src/journey_family.c', 'data/maps/RusturfTunnel/map.json']:
        digest = hashlib.sha256((source / path).read_bytes()).hexdigest()
        if digest != expected[path]: raise ValueError('Unreviewed reunion input: ' + path)
        if path != PATH: preserved[path] = digest
    original = (source / PATH).read_text()
    body = original
    edits = []
    def replace(before, after):
        nonlocal body
        if body.count(before) != 1: raise ValueError('Ambiguous reunion anchor')
        body = body.replace(before, after)
        edits.append(dict(path=PATH, before=before, after=after))
    for position in (1, 2, 3):
        before = f'RusturfTunnel_EventScript_TunnelBlockagePos{position}::\n\tsetvar VAR_TEMP_1, {position}\n\tend'
        after = before.removesuffix('\tend') + '\tgoto_if_unset FLAG_RECOVERED_DEVON_GOODS, RusturfTunnel_Journey_ReunionEnd\n\tgoto_if_set FLAG_RUSTURF_TUNNEL_OPENED, RusturfTunnel_Journey_ReunionEnd\n\tgoto_if_set FLAG_HIDE_RUSTURF_TUNNEL_WANDA, RusturfTunnel_Journey_ReunionEnd\n\tgoto_if_set FLAG_HIDE_RUSTURF_TUNNEL_WANDAS_BOYFRIEND, RusturfTunnel_Journey_ReunionEnd\n\tsetvar VAR_RUSTURF_TUNNEL_STATE, 4\n\tend'
        replace(before, after)
    body += '\nRusturfTunnel_Journey_ReunionEnd::\n\tend\n'
    old = '\t.string "Wow! You shattered that boulder\\n"\n\t.string "blocking the way.\\p"\n\t.string "To show you how much I appreciate it,\\n"\n\t.string "I\'d like you to have this TM.$"'
    new = '\n'.join('\t.string "' + line + escape + '"' for line, escape in zip(LINES, ['\\n', '\\p', '\\n', '$']))
    replace(old, new)
    report = dict(status='rusturf_reunion_candidate', source_commit=PIN,
        original_sha256={PATH: hashlib.sha256(original.encode()).hexdigest()},
        prepared_sha256={PATH: hashlib.sha256(body.encode()).hexdigest()}, preserved_native_sha256=preserved,
        edits=edits, dialogue_lines=LINES, requires_peeko_rescue=True, no_rock_smash_or_badges_required=True,
        original_reunion_movements_and_reward_preserved=True, reward='ITEM_TM_STRENGTH',
        regional_gym_and_league_rules_preserved=True, full_campaign_validated=False)
    (source / PATH).write_text(body)
    marker.write_text(json.dumps(report, indent=2) + '\n')
    return report

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    print(json.dumps(prepare(p.parse_args().source), indent=2))
