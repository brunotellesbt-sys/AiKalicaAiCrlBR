#!/usr/bin/env python3
"""Build all-region LeafGreen, with only Mega Evolution as a selectable gimmick."""
import argparse, json, os, re, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/unova'))
from prepare import prepare, COMMIT
from import_catalog import apply as import_catalog, matching
from configure import apply as configure, write_layout
from build import export
NAME='LeafGreen-Journey-AllRegions'
OUT=ROOT/'mods/all-regions'

def restrict_mechanics(source):
 p=source/'include/config/species_enabled.h';s=p.read_text();s,n=re.subn(r'(#define P_GIGANTAMAX_FORMS\s+)TRUE',r'\1FALSE',s);assert n==1;p.write_text(s)
 p=source/'src/data/gimmicks.h';s=p.read_text()
 for fn in ['CanUseZMove','ActivateZMove','CanDynamax','ActivateDynamax','CanUltraBurst','ActivateUltraBurst','CanTerastallize','ActivateTera']:
  s=s.replace('= '+fn+',','= NULL,')
 p.write_text(s)
 for file,fn in [('battle_dynamax.c','CanDynamax'),('battle_z_move.c','CanUseZMove')]:
  p=source/'src'/file;s=p.read_text();start=s.index('bool32 '+fn+'(');b=s.index('{',start);e=matching(s,b);s=s[:b]+'{\n    return FALSE;\n}'+s[e+1:];p.write_text(s)

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--toolchain',type=Path,default=ROOT/'.local/arm-gcc/usr/bin');p.add_argument('--nm',type=Path,default=ROOT/'.local/arm-binutils/usr/bin/arm-none-eabi-nm');p.add_argument('--export-only',action='store_true');p.add_argument('--prepare-only',action='store_true');p.add_argument('--reimport',action='store_true');p.add_argument('--jobs',type=int,default=4);a=p.parse_args();source=a.source.resolve()
 if subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()!=COMMIT:raise ValueError('Wrong pinned engine commit')
 toolchain=a.toolchain.resolve();nm=a.nm.resolve()
 env=os.environ.copy();env['PATH']=str(toolchain)+os.pathsep+str(nm.parent)+os.pathsep+env['PATH']
 if not (source/'.unova-prepared').exists():
  if not (source/'.journey-prepared').exists():prepare(source)
  elif not all((source/name).exists() for name in ['.open-world-prepared','.wild-world-prepared']):raise ValueError('Incomplete journey preparation; preserve it and use a fresh checkout')
  subprocess.run(['make','-f','make_tools.mk','-j'+str(a.jobs)],cwd=source,env=env,check=True)
  subprocess.run(['make','-j'+str(a.jobs),'include/constants/map_groups.h','include/constants/layouts.h','include/constants/map_event_ids.h','include/constants/region_map_sections.h','GAME_VERSION=LEAFGREEN','REVISION=1'],cwd=source,env=env,check=True)
  raw=subprocess.check_output([str(toolchain/'arm-none-eabi-cpp'),'-P','-iquote','include','-Wno-trigraphs','-DMODERN=1','-DTESTING=0','-DLEAFGREEN','-std=gnu17','src/pokemon.c'],cwd=source,text=True)
  (source/'.region-native.c').write_text(raw)
  restrict_mechanics(source)
  import_catalog(source,toolchain/'arm-none-eabi-cpp',OUT/'donor-assets.zip',raw);configure(source)
 elif a.reimport:
  import_catalog(source,toolchain/'arm-none-eabi-cpp',OUT/'donor-assets.zip',(source/'.region-native.c').read_text())
 write_layout(source)
 if a.prepare_only:sys.exit(0)
 if not a.export_only:
  subprocess.run(['make','-j'+str(a.jobs),'GAME_VERSION=LEAFGREEN','REVISION=1'],cwd=source,env=env,check=True)
 export(source,nm,OUT,NAME,['tools/unova','tools/regions','tools/journey'])
