"""Port native-habitat adaptive wild encounters to the connected-world candidate."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from prepare_family import LAYERS_BEFORE, HERE
from prepare_crossing import PIN


def prepare(source):
    source = Path(source)
    marker = source / '.journey-wild'
    if marker.exists():
        report = json.loads(marker.read_text())
        for p, digest in report['prepared_sha256'].items():
            assert hashlib.sha256((source/p).read_bytes()).hexdigest() == digest, p
        return report
    acquired = json.loads((source/'.source-acquired.json').read_text())
    assert acquired['commit'] == PIN
    expected = dict(acquired['sha256'])
    for layer in LAYERS_BEFORE + ['family', 'travel-rules', 'birth']:
        expected.update(json.loads((source/('.journey-'+layer)).read_text())['prepared_sha256'])
    outputs, inputs, originals = {}, {}, {}
    def read(p):
        if p in outputs: return outputs[p]
        raw = (source/p).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected[p], p
        if p in acquired['sha256']: inputs[p] = acquired['sha256'][p]
        return raw
    def stage(p, body):
        if p in expected and p not in originals: originals[p] = hashlib.sha256(read(p)).hexdigest()
        outputs[p] = body.encode()
    def replace(p, a, b):
        body = read(p).decode(); assert body.count(a) == 1, (p,a)
        stage(p, body.replace(a,b))
    ids = {n:int(v) for n,v in re.findall(r'\b(SPECIES_\w+)\s*=\s*(\d+)', read('include/constants/species.h').decode()) if int(v) <= 386}
    children = {}
    for p in sorted(acquired['sha256']):
        if not p.startswith('src/data/pokemon/species_info/') or not p.endswith('.h'): continue
        body = read(p).decode()
        entries = re.split(r'\[(SPECIES_\w+)\]\s*=\s*\{',body)
        for name, value in zip(entries[1::2],entries[2::2]):
            if name not in ids: continue
            evo = re.search(r'\.evolutions\s*=\s*EVOLUTION\((.*?)(?=\n\s*\.[A-Za-z]|\n\s*\},)',value,re.S)
            if not evo: continue
            targets = re.findall(r'\{EVO_\w+,\s*[^,]+,\s*(SPECIES_\w+)',evo[1])
            children.setdefault(name,set()).update(t for t in targets if t in ids and t != 'SPECIES_NONE')
    parent = {}
    for n, targets in children.items():
        for t in targets:
            assert t not in parent or parent[t] == n, ('Two parents', t)
            parent[t] = n
    def root(n):
        seen = set()
        while n in parent:
            assert n not in seen, n
            seen.add(n); n = parent[n]
        return n
    def stages(n):
        result = [[root(n)]]
        for _ in range(2):
            result.append(sorted({t for p in result[-1] for t in children.get(p,[])}, key=lambda t:ids[t]) or result[-1])
        assert all(1 <= len(s) <= 8 for s in result), n
        return result
    stages_by_id = {v:stages(n) for n,v in ids.items()}
    stages_by_id[0] = [['SPECIES_NONE']]*3
    encounters = json.loads(read('src/data/wild_encounters.json'))['wild_encounter_groups'][0]['encounters']
    fields = ['land_mons','water_mons','rock_smash_mons','fishing_mons','hidden_mons']
    pools = {}
    versions = {'FireRed':set(),'LeafGreen':set()}
    for e in encounters:
        version = e['base_label'].rsplit('_',1)[-1]
        for area, field in enumerate(fields):
            names = {m['species'] for m in e.get(field,{}).get('mons',[])}
            if version in versions: versions[version].update(names)
            pools.setdefault((e['map'],area),set()).update(root(n) for n in names if n in ids and n != 'SPECIES_UNOWN')
    rows, report_pools = [], []
    for (m,area), names in sorted(pools.items()):
        if not names: continue
        assert len(names) <= 24, (m,area)
        names = sorted(names,key=lambda n:ids[n])
        rows.append('{'+', '.join([m,str(area),str(len(names)),'{'+', '.join(names)+'}'])+'}')
        report_pools.append(dict(map=m,area=area,families=names))
    families = []
    for i in range(387):
        ss = stages_by_id[i]
        families.append('{'+', '.join([ss[0][0],'{'+', '.join(str(len(x)) for x in ss)+'}',
            '{'+', '.join('{'+', '.join(x)+'}' for x in ss)+'}'])+'}')
    stage('include/journey_wild_data.h','static const struct JourneyWildStages sJourneyWildStages[] = {\n'+',\n'.join(families)+'\n};\nstatic const struct JourneyWildPool sJourneyWildPools[] = {\n'+',\n'.join(rows)+'\n};\n')
    for ext,target in [('c','src'),('h','include')]: stage(target+'/journey_wild.'+ext,(HERE/('wild.'+ext)).read_text())
    for name in ['wild_encounter','script_pokemon_util','roamer']:
        replace('src/'+name+'.c','#include "global.h"','#include "global.h"\n#include "journey_wild.h"')
    p = 'src/wild_encounter.c'
    body = read(p).decode()
    body,count = re.subn(r'static u8 ChooseWildMonLevel\(.*?\)\n\{.*?\n\}', 'static u8 ChooseWildMonLevel(const struct WildPokemon *wildPokemon, u8 wildMonIndex, enum WildPokemonArea area)\n{\n    return JourneyWildLevel();\n}',body,count=1,flags=re.S)
    assert count == 1; stage(p,body)
    replace(p,'void CreateWildMon(enum Species species, u8 level)\n{','void CreateWildMon(enum Species species, u8 level)\n{\n    level = JourneyWildNormalizeLevel(level);')
    replace(p,'CreateWildMon(wildMonInfo->wildPokemon[wildMonIndex].species, level);','CreateWildMon(JourneyWildSpecies(wildMonInfo->wildPokemon[wildMonIndex].species, area), level);')
    replace(p,'enum Species wildMonSpecies = wildMonInfo->wildPokemon[wildMonIndex].species;', 'enum Species wildMonSpecies = JourneyWildSpecies(wildMonInfo->wildPokemon[wildMonIndex].species, WILD_AREA_FISHING);')
    # Fixed/scripted species are preserved, while every wild level stays in bounds.
    p = 'src/script_pokemon_util.c'
    replace(p,'void CreateScriptedWildMon(enum Species species, u8 level, enum Item item)\n{','void CreateScriptedWildMon(enum Species species, u8 level, enum Item item)\n{\n    level = JourneyWildNormalizeLevel(level);')
    replace(p,'void CreateScriptedDoubleWildMon(enum Species species1, u8 level1, enum Item item1, enum Species species2, u8 level2, enum Item item2)\n{','void CreateScriptedDoubleWildMon(enum Species species1, u8 level1, enum Item item1, enum Species species2, u8 level2, enum Item item2)\n{\n    level1 = JourneyWildNormalizeLevel(level1);\n    level2 = JourneyWildNormalizeLevel(level2);')
    p = 'src/roamer.c'
    replace(p,'static void CreateInitialRoamerMon(u8 index, enum Species species, u8 level)\n{','static void CreateInitialRoamerMon(u8 index, enum Species species, u8 level)\n{\n    level = JourneyWildNormalizeLevel(level);')
    replace(p,'    struct Pokemon *mon = &gParties[B_TRAINER_1][0];','    u32 oldMax, newMax;\n    struct Pokemon *mon = &gParties[B_TRAINER_1][0];')
    a='    CreateMonWithIVsPersonality(mon, ROAMER(roamerIndex)->species, ROAMER(roamerIndex)->level, ROAMER(roamerIndex)->ivs, ROAMER(roamerIndex)->personality);'
    replace(p,a,a+'\n    oldMax = GetMonData(mon, MON_DATA_MAX_HP);\n    ROAMER(roamerIndex)->level = JourneyWildNormalizeLevel(ROAMER(roamerIndex)->level);\n'+a+'\n    newMax = GetMonData(mon, MON_DATA_MAX_HP);\n    ROAMER(roamerIndex)->hp = oldMax ? (ROAMER(roamerIndex)->hp * newMax + oldMax - 1) / oldMax : newMax;\n    if (ROAMER(roamerIndex)->hp > newMax) ROAMER(roamerIndex)->hp = newMax;')
    report = dict(status='native_adaptive_wild_candidate',source_commit=PIN, level_range=[-5,2],
        mean='floor arithmetic mean of nonempty non-Egg party, including fainted', empty_party_mean=5,
        evolution_phases={'0-2 badges':[1],'3-5 badges':[1,2],'6+ badges':[2,3]},
        progress='floor mean of both regional badge counts', fixed_species_preserved=True, unown_preserved=True,
        new_generations_not_added_to_wild=True, species_cap=386, pools=report_pools,
        fire_red_exclusive_species=sorted(versions['FireRed']-versions['LeafGreen']),
        families={n:stages(n) for n in ids}, full_campaign_validated=False,
        input_sha256=inputs,original_sha256=originals,prepared_sha256={p:hashlib.sha256(v).hexdigest() for p,v in outputs.items()})
    for p,v in outputs.items(): (source/p).parent.mkdir(parents=True,exist_ok=True); (source/p).write_bytes(v)
    marker.write_text(json.dumps(report,indent=2)+'\n')
    return report

if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True)
    print(json.dumps(prepare(p.parse_args().source),indent=2))
