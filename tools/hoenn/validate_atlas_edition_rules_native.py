"""Native edition APIs: full Dex, allowed species, pools, boss IV/EV and TESTE.

Party, progress, clock and map identity are explicit API-test fixtures. This
does not claim controller travel or a balance playthrough. Separate current
controller reports prove trainer battles, manual TESTE battles and cold saves.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from battle_interaction_fixture import compile_probe
from validate_coast_scenery_objects import bootstrap

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(source, library, census_path, output):
    source, library, census_path, output = (Path(p).resolve() for p in (source, library, census_path, output))
    output.mkdir(parents=True, exist_ok=True)
    census = json.loads(gzip.decompress(census_path.read_bytes()))
    catalog = json.loads((ROOT/'tools/hoenn/catalog_metadata.json').read_bytes())
    metadata = json.loads((source/'.journey-atlas-surf-layout').read_bytes())
    artifacts = {n: sha(source/n) for n in ('pokeemerald.gba', 'pokeemerald.elf', '.journey-atlas-surf-layout')}
    # The bounded census authenticates local trigger cells, not a full
    # controller journey through every native campaign map.
    assert census['graph_reachable_cells_supplied'] is True
    physical = json.loads(gzip.decompress((census_path.parent/'physical-source.json.gz').read_bytes()))
    assert physical['passed'] is True and not physical['errors']
    for name, expected in census['source_inputs_sha256'].items():
        assert sha(source/name) == expected, ('Compiled census source changed', name)
    groups = json.loads((source/'data/maps/map_groups.json').read_bytes())
    identities = {name: (g<<8)|n for g, label in enumerate(groups['group_order']) for n, name in enumerate(groups[label])}
    fields = ['MON_DATA_IVS', 'MON_DATA_SPECIES', 'MON_DATA_LEVEL', 'MON_DATA_HP_EV',
              'MON_DATA_ATK_EV', 'MON_DATA_DEF_EV', 'MON_DATA_SPATK_EV', 'MON_DATA_SPDEF_EV', 'MON_DATA_SPEED_EV']
    _, values, probe_sha = compile_probe(source, set(fields))
    ns = bootstrap(source, library, output, ['JourneyAtlasSea000', 'RustboroCity_Gym'])
    lib, symbols, abi = ns['lib'], ns['s'], ns['abi']
    native = ns['native']
    counts, aliases, samples, bosses, review_checks = {}, [], [], [], {}
    dex_gaps = []
    try:
        cap = lib.read16(symbols['gJourneyBuildRules'])
        hard = bool(lib.read8(symbols['gJourneyBuildRules']+2))
        review = bool(lib.read8(symbols['gJourneyReviewMode']))
        assert cap in (493, 1025)
        assert bool(native('JourneyPerfectTrainerIvs')) == hard
        assert native('JourneyPWTMaxGeneration') == (4 if cap == 493 else 9)
        for number, species in catalog['canonical_species'].items():
            allowed = bool(native('JourneySpeciesAllowed', species))
            count = native('JourneyWorldDexLocationCount', species)
            assert allowed == (int(number) <= cap), ('Wrong species cap', number, species)
            if bool(count) != allowed:
                dex_gaps.append(dict(national_dex=int(number), species=species, count=count, allowed=allowed))
            counts[number] = count
        (output/'native-Dex-diagnostic.json').write_text(json.dumps(dict(
            artifact_sha256=artifacts,max_national=cap,missing_or_forbidden=dex_gaps,
            canonical_location_counts=counts,passed=not dex_gaps),indent=2)+'\n')
        assert not dex_gaps, ('Missing or forbidden native AREA entries', cap, dex_gaps)
        species_ids = {r['name']: int(sid) for sid, r in catalog['species'].items()}
        for name in ('SPECIES_RAICHU_ALOLA', 'SPECIES_CHARIZARD_MEGA_X'):
            assert native('JourneySpeciesAllowed', species_ids[name])
        for name, owner in census['aliases'].items():
            actual = native('JourneyAtlasEcologyOwner', identities[name])
            assert actual == identities[owner], ('Compiled native alias differs', name, owner, actual)
            aliases.append(dict(map=name, owner=owner, native_owner=actual))
        pool_rows = {}
        for row in census['map_areas']:
            if row['map'].startswith('JourneyAtlas') and row['area'] in (1, 3) and row['species'][str(cap)] and row['terrain_trigger_cells']:
                pool_rows.setdefault((row['owner'], row['area']), row)
        assert pool_rows
        for phase, badges in ((0, 0), (1, 4), (2, 8)):
            for bank in (ns['kanto_flags'], ns['hoenn_flags']):
                for i, flag in enumerate(bank):
                    ns['rawflag'](flag, i < badges)
            assert native('JourneyWildPhase') == phase
            for row in pool_rows.values():
                packed = identities[row['map']]
                lib.write8(ns['save']()+4, packed>>8)
                lib.write8(ns['save']()+5, packed&255)
                assert native('JourneyWildPoolAvailable', row['area']), ('Missing current pool', row['map'], cap)
                expected = set(row['species'][str(cap)])
                observed = []
                for _ in range(3):
                    species = native('JourneyWildSpecies', min(expected), row['area'])
                    assert species in expected, ('Native sample outside exact source census', row['map'], phase, species)
                    assert native('JourneySpeciesAllowed', species) and native('JourneyAquaticSpecies', species)
                    observed.append(species)
                samples.append(dict(map=row['map'], owner=row['owner'], area=row['area'], phase=phase,
                                    native_species=observed, graph_trigger=row['trigger_sample'][0]))
            print('Current native pool APIs PASS:', cap, 'phase', phase, 'owner/areas', len(pool_rows), flush=True)
        for bank in (ns['kanto_flags'], ns['hoenn_flags']):
            for flag in bank:
                ns['rawflag'](flag, False)
        ns['team']([25, 25])
        ns['warp']('RustboroCity_Gym', 4, 13)
        lib.write8(symbols['isFrlg'], 0)
        trainer = ns['ids']['TRAINER_ROXANNE_1']
        assert native('JourneyCompetitiveAiFlags', trainer)&0x80000000
        levels = ns['generated'](ns['base']+trainer*abi[0])
        assert levels
        for index, level in enumerate(levels):
            pointer = ns['enemy']+index*abi[2]
            observed = {name: native('GetMonData3', pointer, values[name], 0) for name in fields}
            assert native('JourneySpeciesAllowed', observed['MON_DATA_SPECIES'])
            assert observed['MON_DATA_LEVEL'] == level
            if hard:
                assert observed['MON_DATA_IVS']&0x3FFFFFFF == 0x3FFFFFFF
            evs = [observed[name] for name in fields[3:]]
            assert sum(evs) == 510 and all(0 <= value <= 252 for value in evs)
            bosses.append(observed)
        if review:
            native('DisableWildEncounters', 0)
            native('VarSet', 0x4021, 0)
            native('VarSet', 0x4120, 0)
            assert not native('DoesCurrentMapHaveFishingMons')
            assert not native('SweetScentWildEncounter')
            native('RockSmashWildEncounter')
            assert lib.read16(symbols['gSpecialVar_Result']) == 0
            for behavior in (2, 3, 16, 17, 18):
                for _ in range(40):
                    assert not native('StandardWildEncounter', behavior, behavior)
            review_checks = dict(random_wild_attempts=200, no_random_encounters=True,
                no_fishing_encounters=True, no_sweet_scent_encounters=True,
                no_rock_smash_encounters=True, fixture_wild_encounters_disabled=False, fixture_repel_steps=0)
        ns['picture']('native-edition-API-fixture')
        assert artifacts == {n: sha(source/n) for n in artifacts}
    finally:
        lib.stop()
        ns['emulator_workspace'].cleanup()
    report = dict(kind='atlas-edition-native-rules', passed=True, artifact_sha256=artifacts,
        max_national=cap, perfect_trainer_ivs=hard, review_mode=review,
        canonical_location_counts=counts, aliases=aliases, aquatic_samples=samples,
        generated_boss_party=bosses, review_checks=review_checks,
        ARM_probe_sha256=probe_sha, census_sha256=sha(census_path),
        native_API_party_progress_and_map_identities_are_fixtures=True,
        enemy_party_created_by_native_generator_only=True,
        controller_travel_and_balance_playthrough_claimed=False, final_release_validated=False)
    (output/'edition-native-rules.json').write_text(json.dumps(report, indent=2)+'\n')
    print('Native edition/Dex/pools/boss/review APIs PASS:', cap, hard, review, flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'library', 'census', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    run(args.source, args.library, args.census, args.output)
