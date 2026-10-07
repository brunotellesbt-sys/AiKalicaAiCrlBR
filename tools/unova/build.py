#!/usr/bin/env python3
"""Build expanded LeafGreen while preserving the reviewed journey overlay."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from prepare import COMMIT, ROOT, prepare
from import_catalog import apply as import_catalog
from configure import apply as configure
sys.path.insert(0,str(ROOT/'tools/rom_hacks'))
from remove_hm_walls import BASE, REFERENCE, bps, sha, transform

def symbols(source,nm):
    return {name:int(addr,16) for addr,kind,name in re.findall(r'^(\w+) (\w) (\S+)$',subprocess.check_output([str(nm),'-n',str(source/'pokeleafgreen.elf')],text=True),re.M)}

def export(source,nm,output):
    syms = symbols(source,nm)
    built = (source/'pokeleafgreen.gba').read_bytes()
    original = (ROOT/'Pokemon - Leaf Green Version (U) (V1.1).gba').read_bytes()
    ref = json.loads(REFERENCE.read_text())
    if sha(original) != ref['source']['baseline_sha256']: raise ValueError('Wrong original LeafGreen ROM')
    dynamic = copy.deepcopy(ref); dynamic['symbols'].update(syms)
    dynamic['source']['baseline_sha256'] = sha(built)
    dynamic['object_graphics_bytes'] = 2
    groups = json.loads((source/'data/maps/map_groups.json').read_text())
    dynamic['groups'] = [groups[g] for g in groups['group_order']]
    dynamic['layouts'] = [l['name'] for l in json.loads((source/'data/layouts/layouts.json').read_text())['layouts']]
    for t in dynamic['attribute_tables']: t['address'] = syms[t['symbol']]
    result,hm = transform(built,dynamic)
    output.mkdir(parents=True,exist_ok=True)
    (output/'LeafGreen-Journey-Unova.gba').write_bytes(result)
    patch = bps(original,result)
    (output/'LeafGreen-Journey-Unova.bps').write_bytes(patch)
    homes = json.loads((source/'.journey-prepared').read_text())
    donor = json.loads((source/'.unova-prepared').read_text())
    manifest = dict(source_repository='kerrymilan/roguemon-expansion',source_commit=COMMIT,original_sha256=sha(original),target_sha256=sha(result),patch_sha256=sha(patch),size=len(result),donor_asset_sha256=sha((output/'donor-assets.zip').read_bytes()),terrestrial_hm_changes=hm,homes=homes['homes'],open_world=json.loads((source/'.open-world-prepared').read_text()),wild_world=json.loads((source/'.wild-world-prepared').read_text()),imported={k:v for k,v in donor.items() if k != 'catalog'},overlay_hashes={str(p.relative_to(ROOT)):sha(p.read_bytes()) for folder in ['tools/unova','tools/journey'] for p in sorted((ROOT/folder).iterdir()) if p.is_file() and p.suffix in ['.py','.json','.c','.h','.inc']})
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    (output/'catalog.json').write_text(json.dumps(donor,indent=2)+'\n')
    fields = json.loads((source/'.unova-layout').read_text()); addr = syms['gUnovaLayout']-BASE
    import struct
    layout = dict(zip(fields,struct.unpack_from('<'+str(len(fields))+'I',result,addr)))
    # Export the symbols used by both validation suites and map references,
    # rather than tens of thousands of compiler-local graphics labels.
    needed = {'gSpeciesInfo','gUnovaLayout','gBattleMons','gBattleStruct','gBattlerPositions','gBattlerPartyIndexes','gBattlersCount','HandleInputChooseMove','gBattlerControllerFuncs','gBattleOutcome'}
    needed.update(json.loads((ROOT/'mods/choose-starting-city/debug-reference.json').read_text())['symbols'])
    for folder in ['tools/unova','tools/journey']:
        for p in (ROOT/folder).glob('*.py'):
            needed.update(re.findall(r"(?:s\[|native\()\s*['\"](\w+)['\"]",p.read_text()))
    needed.update(n for names in dynamic['groups'] for n in names)
    public_syms = {n:syms[n] for n in sorted(needed) if n in syms}
    debug = dict(layout=layout,symbols=public_syms,groups=dynamic['groups'],attribute_tables=dynamic['attribute_tables'],homes=homes['homes'],specials={n:i for i,n in enumerate(re.findall(r'^\s*def_special\s+(\w+)',(source/'data/specials.inc').read_text(),re.M))},map_symbols={n:syms[n] for names in dynamic['groups'] for n in names})
    (output/'debug-reference.json').write_text(json.dumps(debug,indent=2)+'\n')
    print(json.dumps(dict(target_sha256=sha(result),size=len(result),species=donor['species_count'],mega_forms=donor['mega_count'],hm_counts=hm['counts']),indent=2))

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--toolchain',type=Path,default=ROOT/'.local/arm-gcc/usr/bin')
    p.add_argument('--nm',type=Path,default=ROOT/'.local/arm-binutils/usr/bin/arm-none-eabi-nm')
    p.add_argument('--output',type=Path,default=ROOT/'mods/unova-catalog')
    p.add_argument('--export-only',action='store_true')
    p.add_argument('--jobs',type=int,default=4)
    a = p.parse_args(); source = a.source.resolve()
    if not (source/'.unova-prepared').exists():
        prepare(source)
        import_catalog(source,a.toolchain.resolve()/'arm-none-eabi-cpp',a.output/'donor-assets.zip')
        configure(source)
    if not a.export_only:
        env = os.environ.copy();env['PATH'] = str(a.toolchain.resolve())+os.pathsep+str(a.nm.resolve().parent)+os.pathsep+env['PATH']
        subprocess.run(['make','-j'+str(a.jobs),'GAME_VERSION=LEAFGREEN','REVISION=1'],cwd=source,env=env,check=True)
    export(source,a.nm.resolve(),a.output.resolve())
