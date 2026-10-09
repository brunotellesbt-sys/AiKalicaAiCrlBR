"""Check swapped family habitats, native Dex membership and evolution phases."""
from pathlib import Path
import hashlib
import json
ROOT = Path(__file__).resolve().parents[2]
exec(compile((ROOT / 'tools/hoenn/validate_abilities.py').read_text().split('\nability_field,')[0],
             str(ROOT / 'tools/hoenn/validate_abilities.py'), 'exec'))
prep = json.loads((source / '.journey-lostelle-habitats').read_text())
locations = prep['locations_data']
ids_to_names = {json.loads((source / 'data/maps' / n / 'map.json').read_text())['id']: n
               for g in groups['group_order'] for n in groups[g]}
checks = []
for root, members, section in [(96, [96, 97], 'MAPSEC_BERRY_FOREST'), (451, [451, 452], 'MAPSEC_MT_PYRE')]:
    for habitat in locations:
        for ident in habitat['maps']:
            name = ids_to_names[ident]; group, num = map_id(name)
            for member in members:
                actual = bool(native('JourneyHabitatHasSpecies', group, num, member))
                assert actual == (habitat['section'] == section), (ident, member, actual)
            checks.append(dict(map=ident, root=root, present=habitat['section'] == section))
phases = []
for phase, count in [(0, 0), (1, 3), (2, 6)]:
    for flags in [list(range(0x1AB0, 0x1AB8)), [lib.read16(s['gBadgeFlags'] + i * 2) for i in range(8)]]:
        for i, flag in enumerate(flags):
            address = save() + 4720 + flag // 8; mask = 1 << (flag & 7)
            old = lib.read8(address); lib.write8(address, old | mask if i < count else old & ~mask)
    assert native('JourneyWildPhase') == phase
    for root, section in [(96, 'MAPSEC_BERRY_FOREST'), (451, 'MAPSEC_MT_PYRE')]:
        habitat = next(h for h in locations if h['section'] == section)
        for ident in habitat['maps']:
            warp(ids_to_names[ident], 1, 1)
            observed = {native('JourneyWildSpecies', root, 0) for _ in range(80)}
            expected = {root} if phase == 0 else {root, root + 1} if phase == 1 else {root + 1}
            assert observed == expected, (ident, phase, observed)
            phases.append(dict(map=ident, phase=phase, root=root, observed=sorted(observed)))
lib.stop()
(args.output / 'lostelle-habitats.json').write_text(json.dumps(dict(passed=True,
    rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
    dex_membership=checks, phase_cases=phases, tested_species=[96, 97, 451, 452],
    initial_state_badges_and_map_positions_are_fixtures=True,
    native_functions_called_directly=True, pokedex_area_ui_visually_reviewed=False,
    full_campaign_validated=False), indent=2) + '\n')
print('Native family locations and evolution phases passed', flush=True)
