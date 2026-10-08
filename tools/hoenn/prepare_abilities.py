"""Migrate Hidden Abilities and classic Battle Bond after the ecology layer."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from prepare_crossing import PIN
from prepare_family import LAYERS_BEFORE


def prepare(source):
    source = Path(source)
    marker = source / '.journey-abilities'
    if marker.exists():
        report = json.loads(marker.read_text())
        for path, digest in report['prepared_sha256'].items():
            assert hashlib.sha256((source / path).read_bytes()).hexdigest() == digest, path
        return report
    acquired = json.loads((source / '.source-acquired.json').read_text())
    assert acquired['commit'] == PIN
    expected = dict(acquired['sha256'])
    for layer in LAYERS_BEFORE + ['family', 'travel-rules', 'birth', 'wild',
                                 'habitats', 'sanctuaries', 'ecology']:
        expected.update(json.loads((source / ('.journey-' + layer)).read_text())['prepared_sha256'])
    outputs, originals, inputs = {}, {}, {}

    def read(path):
        raw = (source / path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected[path], path
        originals[path] = expected[path]
        if path in acquired['sha256']:
            inputs[path] = acquired['sha256'][path]
        return raw.decode()

    def stage(path, text):
        outputs[path] = text.encode()

    path = 'include/config/battle.h'
    text, count = re.subn(r'(#define B_BATTLE_BOND\s+)GEN_LATEST', r'\g<1>GEN_7', read(path))
    assert count == 1
    stage(path, text)
    path = 'src/data/pokemon/species_info/gen_6_families.h'
    text = read(path)
    for name in ['FROAKIE', 'FROGADIER', 'GRENINJA', 'GRENINJA_ASH']:
        start = text.index('    [SPECIES_' + name + '] =')
        end = text.index('\n    },', start)
        body = text[start:end]
        first = 'ABILITY_BATTLE_BOND' if name == 'GRENINJA_ASH' else 'ABILITY_TORRENT'
        body, count = re.subn(r'\.abilities = \{[^}]+\}',
                             '.abilities = { ' + first + ', ABILITY_PROTEAN, ABILITY_BATTLE_BOND }', body)
        assert count == 1, name
        text = text[:start] + body + text[end:]
    stage(path, text)
    path = 'src/battle_util.c'
    text = read(path)
    old = 'GetBattlerPartyState(battler)->battleBondBoost || gBattleMons[battler].species != SPECIES_GRENINJA_BATTLE_BOND'
    new = 'GetBattlerPartyState(battler)->battleBondBoost || (gBattleMons[battler].species != SPECIES_GRENINJA_BATTLE_BOND && gBattleMons[battler].species != SPECIES_GRENINJA)'
    assert text.count(old) == 1
    text = text.replace(old, new)
    old = 'if (IsBattlerMegaEvolved(battler) || IsBattlerUltraBursted(battler) || IsBattlerInTeraForm(battler) || IsGigantamaxed(battler))'
    assert text.count(old) == 1
    text = text.replace(old, old.replace('if (', 'if (gBattleMons[battler].species == SPECIES_GRENINJA_ASH || '))
    old = 'if (targetSpecies == SPECIES_NONE\n        && battlePartyState != NULL'
    new = 'if ((targetSpecies == SPECIES_NONE || (currentSpecies == SPECIES_GRENINJA_ASH && targetSpecies == SPECIES_GRENINJA_ASH))\n        && battlePartyState != NULL'
    assert text.count(old) == 1
    stage(path, text.replace(old, new))
    # Ash uses the remembered original, preserving ordinary and event Greninja.
    path = 'src/data/pokemon/form_change_tables.h'
    text = read(path)
    start = text.index('static const struct FormChange sGreninjaBattleBondFormChangeTable[]')
    end = text.index('\n};', start)
    body, count = re.subn(r'(FORM_CHANGE_(?:FAINT|END_BATTLE),\s*)SPECIES_GRENINJA_BATTLE_BOND',
                         r'\g<1>SPECIES_GRENINJA_ASH', text[start:end])
    assert count == 2
    stage(path, text[:start] + body + text[end:])
    path = 'src/pokemon.c'
    text = read(path)
    assert text.count(old) == 1
    stage(path, text.replace(old, new))
    path = 'src/wild_encounter.c'
    text = read(path)
    anchor = '    GiveMonInitialMoveset(&gParties[B_TRAINER_1][0]);'
    assert text.count(anchor) == 1
    stage(path, text.replace(anchor, anchor + '''
    // Encounter-only roll: gifts and trainer Pokemon keep their native slots.
    if (GetSpeciesAbility(species, 2) != ABILITY_NONE && Random() % 100 < 5)
    {
        u8 abilityNum = 2;
        SetMonData(&gParties[B_TRAINER_1][0], MON_DATA_ABILITY_NUM, &abilityNum);
    }'''))
    # Export the existing inheritance implementation for the native ABI validator.
    path = 'src/daycare.c'
    text = read(path)
    anchor = 'static void InheritAbility('
    assert text.count(anchor) == 1
    stage(path, text.replace(anchor, 'void InheritAbility('))
    report = dict(status='native_classic_battle_bond_candidate', source_commit=PIN,
                  wild_hidden_percent=5, hidden_slot=2, ordinary_second_slot=1,
                  battle_bond_generation=7, hidden_inheritance='native Gen6+: 60%',
                  no_gift_or_trainer_ability_roll=True, no_new_gimmick_unlock=True,
                  input_sha256=inputs, original_sha256=originals,
                  prepared_sha256={p: hashlib.sha256(v).hexdigest() for p, v in outputs.items()})
    for path, raw in outputs.items():
        (source / path).write_bytes(raw)
    marker.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    print(json.dumps(prepare(parser.parse_args().source), indent=2))
