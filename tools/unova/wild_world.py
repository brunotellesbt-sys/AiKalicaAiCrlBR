"""Port the reviewed wild progression pools without introducing donor species."""
import json
from pathlib import Path
import re
import shutil

HERE = Path(__file__).resolve().parent

def apply(source):
    def edit(name,old,new):
        path = source/name; text = path.read_text()
        if old not in text: raise ValueError(f'Missing wild hook {name}: {old[:60]}')
        path.write_text(text.replace(old,new,1))
    for ext,target in [('c','src'),('h','include')]:
        shutil.copyfile(HERE.parent/'journey'/f'wild_world.{ext}',source/target/f'wild_world.{ext}')
    report = json.loads((HERE/'wild-pools.json').read_text())
    families = report['families']; roots = {}; chains = {}
    for root,stages in families.items():
        for name in stages: roots[name] = root
        chains[root] = stages
    pools = report['pools']
    data = 'static const u16 sWildWorldRoots[NUM_SPECIES+1] = {\n'+''.join(f'[{s}]={r},\n' for s,r in roots.items())+'};\n'
    data += 'static const struct WildWorldFamily sWildWorldFamilies[NUM_SPECIES+1] = {\n'+''.join('['+r+']={{'+','.join(stages)+'}},\n' for r,stages in chains.items())+'};\n'
    data += 'static const struct WildWorldPool sWildWorldPools[] = {\n'+''.join('{MAP_GROUP('+p['map']+'), MAP_NUM('+p['map']+'), '+str(p['area'])+', '+str(len(p['families']))+', {'+', '.join(p['families'])+'}},\n' for p in pools)+'};\n'
    (source/'include/wild_world_data.h').write_text(data)
    (source/'.wild-world-prepared').write_text(json.dumps(report,indent=2)+'\n')
    for name in ['wild_encounter.c','script_pokemon_util.c','roamer.c']:
        edit('src/'+name,'#include "global.h"','#include "global.h"\n#include "wild_world.h"')
    path = source/'src/wild_encounter.c';text = path.read_text()
    text,n = re.subn(r'static u8 ChooseWildMonLevel\(const struct WildPokemon \*wildPokemon, u8 wildMonIndex, u8 area\)\n\{.*?\n\}', 'static u8 ChooseWildMonLevel(const struct WildPokemon *wildPokemon, u8 wildMonIndex, u8 area)\n{\n    return WildWorld_Level();\n}',text,count=1,flags=re.S)
    if n != 1: raise ValueError('Missing level hook')
    path.write_text(text)
    edit('src/wild_encounter.c','CreateWildMon(wildMonInfo->wildPokemon[wildMonIndex].species, level, wildMonIndex);','CreateWildMon(WildWorld_Species(wildMonInfo->wildPokemon[wildMonIndex].species, area), level, wildMonIndex);')
    edit('src/wild_encounter.c','u16 wildMonSpecies = wildMonInfo->wildPokemon[wildMonIndex].species;','u16 wildMonSpecies = WildWorld_Species(wildMonInfo->wildPokemon[wildMonIndex].species, WILD_AREA_FISHING);')
    edit('src/script_pokemon_util.c','void CreateScriptedWildMon(u16 species, u8 level, u16 item)\n{\n    u8 heldItem[2];','void CreateScriptedWildMon(u16 species, u8 level, u16 item)\n{\n    u8 heldItem[2];\n    level = WildWorld_Level();')
    edit('src/roamer.c','    ClearRoamerLocationHistory(index);','    level = WildWorld_Level();\n    ClearRoamerLocationHistory(index);')
    old = '    CreateMonWithIVsPersonality(mon, ROAMER(roamerIndex)->species, ROAMER(roamerIndex)->level, ROAMER(roamerIndex)->ivs, ROAMER(roamerIndex)->personality);'
    edit('src/roamer.c',old,old+'\n    u16 oldMax = GetMonData(mon, MON_DATA_MAX_HP);\n    ROAMER(roamerIndex)->level = WildWorld_Level();\n'+old+'\n    u16 newMax = GetMonData(mon, MON_DATA_MAX_HP);\n    ROAMER(roamerIndex)->hp = oldMax ? (ROAMER(roamerIndex)->hp * newMax + oldMax - 1) / oldMax : newMax;\n    if (ROAMER(roamerIndex)->hp > newMax) ROAMER(roamerIndex)->hp = newMax;')
