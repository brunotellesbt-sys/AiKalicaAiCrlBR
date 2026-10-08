"""Check the family's S.S. Ticket before boarding at both native Hoenn ports."""
import argparse
import hashlib
import json
from pathlib import Path
from prepare_crossing import PIN
from prepare_family import LAYERS_BEFORE


def prepare(source):
    source = Path(source)
    marker = source / '.journey-frontier-travel'
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
                                 'league-access', 'league-completion', 'league-history',
                                 'league-display', 'family-postgame', 'pwt']:
        expected.update(json.loads((source / ('.journey-' + layer)).read_text())['prepared_sha256'])
    originals, inputs, outputs, preserved = {}, {}, {}, {}
    for city, anchor in [('Slateport', 'SlateportCity_Harbor_EventScript_AskForTicket::\n'),
                         ('Lilycove', '\tgoto_if_unset FLAG_SYS_GAME_CLEAR, LilycoveCity_Harbor_EventScript_FerryUnavailable\n')]:
        path = f'data/maps/{city}City_Harbor/scripts.inc'
        raw = (source / path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected[path], path
        body = raw.decode()
        assert body.count(anchor) == 1
        guard = f'\tcheckitem ITEM_SS_TICKET\n\tgoto_if_eq VAR_RESULT, FALSE, {city}City_Harbor_EventScript_NoTicket\n'
        outputs[path] = body.replace(anchor, anchor + guard).encode()
        originals[path] = expected[path]
        inputs[path] = acquired['sha256'][path]
    # The first crossing still plays Scott's native invitation; no bypass flags.
    for path in ['data/maps/SSTidalCorridor/scripts.inc', 'src/script_menu.c',
                 'data/maps/BattleFrontier_OutsideWest/scripts.inc', 'src/journey_pwt.c',
                 'src/journey_family.c', 'src/journey_gym_scaling.c']:
        assert hashlib.sha256((source / path).read_bytes()).hexdigest() == expected[path], path
        preserved[path] = expected[path]
    report = dict(status='native_hoenn_ferry_ticket_candidate', source_commit=PIN,
                  native_scott_invitation_retained=True, ss_ticket_required_at_both_ports=True,
                  hoenn_champion_requirement_retained=True, ticket_not_consumed=True,
                  save_layout_unchanged=True, full_campaign_validated=False,
                  input_sha256=inputs, original_sha256=originals,
                  preserved_native_sha256=preserved,
                  prepared_sha256={p: hashlib.sha256(raw).hexdigest() for p, raw in outputs.items()})
    for path, raw in outputs.items(): (source / path).write_bytes(raw)
    marker.write_text(json.dumps(report, indent=2) + '\n')
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    print(json.dumps(prepare(parser.parse_args().source), indent=2))
