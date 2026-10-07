"""Generate native-habitat pools from both versions and install wild-only hooks."""
import json
from pathlib import Path
import re
import shutil

HERE = Path(__file__).resolve().parent

def apply(source):
    def edit(name, old, new):
        p = source / name
        text = p.read_text()
        if old not in text:
            raise ValueError(f'Missing wild hook: {name}: {old[:60]}')
        p.write_text(text.replace(old, new, 1))
    for ext, target in [('c', 'src'), ('h', 'include')]:
        shutil.copyfile(HERE / f'wild_world.{ext}', source / target / f'wild_world.{ext}')
    species = {name: int(value) for name, value in re.findall(r'#define (SPECIES_\w+)\s+(\d+)\b', (source/'include/constants/species.h').read_text())}
    evos = {}
    for name, body in re.findall(r'\[(SPECIES_\w+)\]\s*=\s*\{(.*?)(?=\n\s*\[|\n\};)', (source/'src/data/pokemon/evolution.h').read_text(), re.S):
        targets = re.findall(r'\{EVO_\w+,\s*[^,]+,\s*(SPECIES_\w+)\}', body)
        if targets:
            evos[name] = targets
    parent = {child: name for name, children in evos.items() for child in children}
    def root(name):
        while name in parent:
            name = parent[name]
        return name
    def stages(name):
        chain = [name]
        while chain[-1] in evos and len(chain) < 3:
            chain.append(evos[chain[-1]][0])
        return chain + [chain[-1]] * (3-len(chain))
    groups = json.loads((source/'src/data/wild_encounters.json').read_text())['wild_encounter_groups'][0]['encounters']
    versions = {'FireRed': {}, 'LeafGreen': {}}
    for e in groups:
        version = e['base_label'].rsplit('_', 1)[-1]
        if version in versions:
            versions[version][e['map']] = e
    fields = ['land_mons', 'water_mons', 'rock_smash_mons', 'fishing_mons']
    all_species = {v: {m['species'] for e in maps.values() for field in fields for m in e.get(field, {}).get('mons', [])} for v, maps in versions.items()}
    exclusive = sorted(all_species['FireRed'] - all_species['LeafGreen'])
    pools = []
    for map_name, lg in versions['LeafGreen'].items():
        fr = versions['FireRed'].get(map_name, lg)
        for area, field in enumerate(fields):
            if field not in lg:
                continue
            families = sorted({root(m['species']) for e in (lg, fr) for m in e.get(field, {}).get('mons', [])}, key=lambda n: species[n])
            if len(families) > 24:
                raise ValueError('Pool overflow')
            pools.append({'map': map_name, 'area': area, 'families': families})
    count = max(species.values()) + 1
    roots = ['SPECIES_NONE'] * count
    chains = ['{{SPECIES_NONE, SPECIES_NONE, SPECIES_NONE}}'] * count
    for name, ident in species.items():
        roots[ident] = root(name)
        chains[ident] = '{{' + ', '.join(stages(name)) + '}}'
    rows = ['{MAP_GROUP('+p['map']+'), MAP_NUM('+p['map']+'), '+str(p['area'])+', '+str(len(p['families']))+', {'+', '.join(p['families'])+'}}' for p in pools]
    (source/'include/wild_world_data.h').write_text('static const u16 sWildWorldRoots[] = {\n'+',\n'.join(roots)+'\n};\nstatic const struct WildWorldFamily sWildWorldFamilies[] = {\n'+',\n'.join(chains)+'\n};\nstatic const struct WildWorldPool sWildWorldPools[] = {\n'+',\n'.join(rows)+'\n};\n')
    report = {'families': {name: stages(name) for name in sorted({n for pool in pools for n in pool['families']})}, 'species_ids': species, 'level_range': [-5, 2], 'mean': 'floor arithmetic mean of nonempty, non-Egg party; fainted included', 'phases': {'0-2 badges': [1], '3-5 badges': [1,2], '6-8 badges': [2,3]}, 'single_stage_and_unown_preserved': True, 'fire_red_exclusive_wild_species': exclusive, 'pools': pools}
    (source/'.wild-world-prepared').write_text(json.dumps(report, indent=2)+'\n')
    for name in ['wild_encounter.c', 'script_pokemon_util.c', 'roamer.c']:
        edit('src/'+name, '#include "global.h"', '#include "global.h"\n#include "wild_world.h"')
    p = source/'src/wild_encounter.c'
    text = p.read_text()
    text = re.sub(r'static u8 ChooseWildMonLevel\(const struct WildPokemon \* info\)\n\{.*?\n\}', 'static u8 ChooseWildMonLevel(const struct WildPokemon * info)\n{\n    return WildWorld_Level();\n}', text, count=1, flags=re.S)
    text = text.replace('GenerateWildMon(info->wildPokemon[slot].species, level, slot);\n    return TRUE;', 'GenerateWildMon(WildWorld_Species(info->wildPokemon[slot].species, area), level, slot);\n    return TRUE;')
    text = text.replace('    GenerateWildMon(info->wildPokemon[slot].species, level, slot);\n    return info->wildPokemon[slot].species;', '    u16 species = WildWorld_Species(info->wildPokemon[slot].species, WILD_AREA_FISHING);\n    GenerateWildMon(species, level, slot);\n    return species;')
    p.write_text(text)
    edit('src/script_pokemon_util.c', '    CreateMon(&gEnemyParty[0], species, level, 32,', '    level = WildWorld_Level();\n    CreateMon(&gEnemyParty[0], species, level, 32,')
    edit('src/roamer.c', '    u16 species = GetRoamerSpecies();', '    u16 species = GetRoamerSpecies();\n    u8 level = WildWorld_Level();')
    edit('src/roamer.c', 'CreateMon(mon, species, 50,', 'CreateMon(mon, species, level,')
    edit('src/roamer.c', 'ROAMER->level = 50;', 'ROAMER->level = level;')
    edit('src/roamer.c', '    u32 status;\n    struct Pokemon *mon', '    u32 status;\n    u16 oldMax, newMax;\n    struct Pokemon *mon')
    edit('src/roamer.c', '    CreateMonWithIVsPersonality(mon, ROAMER->species, ROAMER->level, ROAMER->ivs, ROAMER->personality);', '''    CreateMonWithIVsPersonality(mon, ROAMER->species, ROAMER->level, ROAMER->ivs, ROAMER->personality);
    oldMax = GetMonData(mon, MON_DATA_MAX_HP);
    ROAMER->level = WildWorld_Level();
    CreateMonWithIVsPersonality(mon, ROAMER->species, ROAMER->level, ROAMER->ivs, ROAMER->personality);
    newMax = GetMonData(mon, MON_DATA_MAX_HP);
    ROAMER->hp = oldMax ? (ROAMER->hp * newMax + oldMax - 1) / oldMax : newMax;
    if (ROAMER->hp > newMax)
        ROAMER->hp = newMax;''')
