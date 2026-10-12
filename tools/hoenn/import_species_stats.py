"""Freeze main-series and ZA Mega stats from a pinned Pokémon Showdown snapshot."""
import argparse,hashlib,json,re,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def norm(name):return re.sub('[^a-z0-9]','',unicodedata.normalize('NFKD',name).encode('ascii','ignore').decode().lower())
def collect(reference):
 reference=Path(reference);raw=(reference/'pokedex.json').read_bytes();dex=json.loads(raw);catalog=json.loads((ROOT/'tools/hoenn/catalog_metadata.json').read_text());prior=json.loads((ROOT/'tools/hoenn/data/scarlet-violet-database.json').read_text())
 lookup={norm(k):v for k,v in dex.items() if v.get('num',0)>0}
 for key,value in dex.items():
  if value.get('isCosmeticForme') and norm(value.get('baseSpecies','')) in lookup:
   lookup[norm(key)]={**lookup[norm(value['baseSpecies'])],**value}
 rows={};unmatched=[]
 aliases={'vivillonmeadow':'vivillon','wormadamplant':'wormadam','giratinaaltered':'giratina','shayminland':'shaymin','hoopaconfined':'hoopa','basculinredstriped':'basculin','zygarde50':'zygarde','miniorcore':'minior','oricoriobaile':'oricorio','toxtricityamped':'toxtricity','indeedeemale':'indeedee','basculegionmale':'basculegion','oinkolognemale':'oinkologne','mausholdfamilyoffour':'maushold','dudunsparcetwosegment':'dudunsparce','gimmighoulchest':'gimmighoul','taurospaldeacombat':'taurospaldeacombat','palafinzero':'palafin','darmanitanstandard':'darmanitan'}
 for sid,sp in catalog['species'].items():
  key=norm(sp['name'].removeprefix('SPECIES_'));key=aliases.get(key,key)
  if key=='darmanitangalarstandard':key='darmanitangalar'
  elif key.startswith('zygarde10'):key='zygarde10'
  elif key=='zygarde50powerconstruct':key='zygarde'
  elif key.startswith('miniormeteor'):key='miniormeteor'
  elif key.startswith('miniorcore'):key='minior'
  elif key=='rockruffowntempo':key='rockruff'
  elif key=='xerneasactive':key='xerneas'
  elif key.startswith('unown'):key='unown'
  elif key.startswith('sawsbuck'):key='sawsbuck'
  elif key.startswith('flabebe'):key='flabebe'
  elif key.startswith('floette') and key not in lookup:key='floette'
  elif key.startswith('florges'):key='florges'
  elif key.startswith('furfrou'):key='furfrou'
  elif key.startswith('alcremie') and key not in lookup:key='alcremie'
  elif key.startswith('mothim'):key='mothim'
  elif key.startswith('scatterbug'):key='scatterbug'
  elif key.startswith('spewpa'):key='spewpa'
  elif key=='mimikyutotemdisguised':key='mimikyutotem'
  elif key=='toxtricityampedgmax':key='toxtricitygmax'
  elif key=='urshifusinglestrikegmax':key='urshifugmax'
  record=lookup.get(key)
  if record is None and sid in prior['species']:record=lookup.get(prior['species'][sid]['key'])
  if record is None:unmatched.append(dict(species=sp['name'],id=int(sid),dex=sp['national_dex'],flags=sp['flags']));continue
  stats=record['baseStats'];rows[sid]=dict(species=sp['name'],key=norm(record['name']),reference_name=record['name'],stats=[stats[k] for k in ['hp','atk','def','spe','spa','spd']],mega=record.get('forme','').startswith('Mega'))
 missing_canonical=[sp for sp in catalog['canonical_species'].values() if str(sp) not in rows]
 mega_reference={norm(k) for k,v in lookup.items() if v.get('forme','').startswith('Mega')};mega_imported={r['key'] for r in rows.values() if r['mega']}
 result=dict(provenance=dict(project='smogon/pokemon-showdown',commit=(reference/'commit.txt').read_text().strip(),source_sha256=hashlib.sha256(raw).hexdigest(),url='https://github.com/smogon/pokemon-showdown'),stat_order=['HP','Attack','Defense','Speed','SpAttack','SpDefense'],species=rows,missing_canonical=missing_canonical,unmatched_forms=unmatched,mega_reference_count=len(mega_reference),mega_imported_count=len(mega_imported),missing_megas=sorted(mega_reference-mega_imported))
 assert not missing_canonical,missing_canonical
 assert not result['missing_megas'],result['missing_megas']
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--reference',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=collect(a.reference);a.output.write_text(json.dumps(r,indent=2)+'\n');print('Species:',len(r['species']),'Megas:',r['mega_imported_count'],'unmatched forms:',len(r['unmatched_forms']))
