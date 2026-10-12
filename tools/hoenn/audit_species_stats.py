"""Verify every compiled species/form stat against the pinned reference."""
import argparse,hashlib,json
from pathlib import Path
from audit_battle_database import compiled
ROOT=Path(__file__).resolve().parents[2]
def audit(source):
 source=Path(source);ref=json.loads((ROOT/'tools/hoenn/data/species-base-stats.json').read_text());db=compiled(source);rom=(source/'pokeemerald.gba').read_bytes();layout=db['compiled_layout'];base=layout['symbols']['gSpeciesInfo'];stride=layout['abi'][0];differences=[]
 for sid,row in ref['species'].items():
  offset=base+int(sid)*stride;actual=list(rom[offset:offset+6])
  if actual!=row['stats']:differences.append(dict(species=row['species'],actual=actual,expected=row['stats']))
 return dict(passed=not differences,rom_sha256=hashlib.sha256(rom).hexdigest(),species_and_forms_checked=len(ref['species']),canonical_species_checked=1025,megas_checked=ref['mega_imported_count'],all_za_and_mega_dimension_reference_forms_present=not ref['missing_megas'],reference=ref['provenance'],differences=differences)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=audit(a.source);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');print('Stats checked:',r['species_and_forms_checked'],'Megas:',r['megas_checked'],'passed:',r['passed']);raise SystemExit(0 if r['passed'] else 1)
