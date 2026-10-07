#!/usr/bin/env python3
"""Merge verified donor graphics/stats with the pinned engine's official catalog."""
import argparse, hashlib, json, re, struct, sys, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/unova'))
from extract import decode, lz77, norm, TYPES
from import_catalog import matching, fields, integer_expression
SPECS=[
 ('swsh','PKM SwSh ULTIMATE+_pokebat.net.gba','ef386f9da97995914fea4caa0e5e52f8f95fe53aa309fef4cb153cbe3850aa11',1268),
 ('sun','PK Sun Sky 15.10.20.gba','f91251fb5e3a848541609ad3b9ada271f6cb807c8936c88ba9096b96f9d3dfaa',861),
 ('scarlet','Scarlet-Violet-Indigo.gba','37b4c10670e639d36a2fb6e63490e546dcbc0ac5b40a68f8aca32313dcc31a77',412),
 ('xy','Pokemon X and Y GBA.gba','6e28d1954442b9e8bf56a2ad290e3934db3c878265030060c6750f860779873d',412),
]
ALIASES={'kilowatrel':'kilowattrel','fletchindr':'fletchinder','crabminble':'crabominable','poltegeist':'polteageist','corvsquire':'corvisquire','corvknight':'corviknight','baraskewda':'barraskewda','centskorch':'centiskorch','stonjorner':'stonjourner','blacphalon':'blacephalon','meowscarad':'meowscarada','squakabily':'squawkabilly','brablegast':'brambleghast','brutebonet':'brutebonnet','sandyshock':'sandyshocks','sliterwing':'slitherwing','roaringmon':'roaringmoon','flutermane':'fluttermane','walk ingwak':'walkingwake','walkingwak':'walkingwake','typef0null':'typenull','chesnaugh':'chesnaught','tortunator':'turtonator','xurketree':'xurkitree','blacephalo':'blacephalon'}
FORMS={829:'HOOPA_UNBOUND',832:'MEOWSTIC_F',833:'AEGISLASH_BLADE',835:'ZYGARDE_10_AURA_BREAK',836:'ZYGARDE_10_POWER_CONSTRUCT',837:'ZYGARDE_50_POWER_CONSTRUCT',838:'ZYGARDE_COMPLETE',839:'GRENINJA_ASH',918:'DIANCIE_MEGA',1043:'ORICORIO_POM_POM',1044:'ORICORIO_PAU',1045:'ORICORIO_SENSU',1046:'LYCANROC_MIDNIGHT',1047:'WISHIWASHI_SCHOOL',1072:'MIMIKYU_BUSTED',1073:'MAGEARNA_ORIGINAL',1079:'NECROZMA_DUSK_MANE',1080:'NECROZMA_DAWN_WINGS',1081:'NECROZMA_ULTRA',1082:'LYCANROC_DUSK',1101:'XERNEAS_ACTIVE',1191:'CRAMORANT_GULPING',1192:'CRAMORANT_GORGING',1193:'TOXTRICITY_LOW_KEY',1194:'SINISTEA_ANTIQUE',1195:'POLTEAGEIST_ANTIQUE',1202:'EISCUE_NOICE',1203:'INDEEDEE_F',1204:'MORPEKO_HANGRY',1205:'ZACIAN_CROWNED',1206:'ZAMAZENTA_CROWNED',1208:'URSHIFU_RAPID_STRIKE',1209:'ZARUDE_DADA',1210:'CALYREX_ICE',1211:'CALYREX_SHADOW'}
for i,s in enumerate(['FIGHTING','FLYING','POISON','GROUND','ROCK','BUG','GHOST','STEEL','FIRE','WATER','GRASS','ELECTRIC','PSYCHIC','ICE','DRAGON','DARK','FAIRY'],1048):FORMS[i]='SILVALLY_'+s
for i,s in enumerate(['BLUE','YELLOW','ORANGE','WHITE'],840):FORMS[i]='FLABEBE_'+s
for i,s in enumerate(['BLUE','YELLOW','ORANGE','WHITE','ETERNAL'],844):FORMS[i]='FLOETTE_'+s
for i,s in enumerate(['BLUE','YELLOW','ORANGE','WHITE'],849):FORMS[i]='FLORGES_'+s
for i,s in enumerate(['SMALL','LARGE','SUPER'],853):FORMS[i]='PUMPKABOO_'+s
for i,s in enumerate(['SMALL','LARGE','SUPER'],856):FORMS[i]='GOURGEIST_'+s
for i,s in enumerate(['HEART','STAR','DIAMOND','DEBUTANTE','MATRON','DANDY','LA_REINE','KABUKI','PHARAOH'],859):FORMS[i]='FURFROU_'+s
# SwSh uses meadow as its default Vivillon. The numbered extra patterns follow
# its family table order; names alone cannot distinguish them.
FORMS[774]='VIVILLON_MEADOW'; FORMS[868]='VIVILLON_FANCY'
for i,s in enumerate(['ARCHIPELAGO','CONTINENTAL','ELEGANT','GARDEN','HIGH_PLAINS','ICY_SNOW','JUNGLE','MARINE','MODERN','MONSOON','OCEAN','POKEBALL','POLAR','RIVER','SANDSTORM','SAVANNA','SUN','TUNDRA'],921):FORMS[i]='VIVILLON_'+s
SCARLET_FORMS={250:'TERAPAGOS_TERASTAL',13:'WOOPER_PALDEA',50:'ZORUA_HISUI',51:'ZOROARK_HISUI',59:'ARCANINE_HISUI',128:'TAUROS_PALDEA_COMBAT'}

def native_tables(raw,source):
 m=re.search(r'const struct SpeciesInfo gSpeciesInfo\[[^]]*\] =',raw);b=raw.index('{',m.start());t=raw[b+1:matching(raw,b)];pos=0;entries={}
 while pos<len(t):
  m=re.search(r'\[([0-9()+\-\s]+)\]\s*=\s*\{',t[pos:])
  if not m:break
  b=pos+m.end()-1;e=matching(t,b);entries[integer_expression(m[1])]=fields(t[b+1:e]);pos=e+1
 defs=dict(re.findall(r'#define (SPECIES_\w+)\s+([^\n/]+)',(source/'include/constants/species.h').read_text()))
 def ident(n):
  v=defs[n].strip();return int(v) if v.isdigit() else ident(v)
 ids={n:ident(n) for n in defs if n not in ['SPECIES_EGG'] and re.fullmatch(r'\d+|SPECIES_\w+',defs[n].strip())}
 dextext=(source/'include/constants/pokedex.h').read_text().split('enum NationalDexOrder')[1].split('};')[0]
 dex={n:i for i,n in enumerate(re.findall(r'\bNATIONAL_DEX_\w+\b',dextext))}
 bases={dex[n]:('SPECIES_'+n.removeprefix('NATIONAL_DEX_'),ids['SPECIES_'+n.removeprefix('NATIONAL_DEX_')]) for n in dex if n!='NATIONAL_DEX_NONE' and 'SPECIES_'+n.removeprefix('NATIONAL_DEX_') in ids}
 return entries,ids,dex,bases

def extract(source,raw,donors,output):
 entries,ids,dex,bases=native_tables(raw,source)
 lookup={};names={}
 for nat,(key,ident) in bases.items():
  name=re.search(r'"([^"]+)"',entries[ident]['speciesName'])[1];names[nat]=name
  for v in [name,key.removeprefix('SPECIES_'),name[:10]]:lookup[norm(v)]=(key,ident,nat)
 prior=json.loads((ROOT/'mods/unova-catalog/catalog.json').read_text());rows={};assets={}
 with zipfile.ZipFile(ROOT/'mods/unova-catalog/donor-assets.zip') as z:
  for row in prior['catalog']:
   if '_GMAX' in row['species']:continue
   row=dict(row,origin='unova');rows[row['species_id']]=row
   for n in ['front.4bpp.lz','back.4bpp.lz','palette.gbapal']:assets[f'{row["donor_id"]}/{n}']=z.read(f'{row["donor_id"]}/{n}')
 rejected=[];sources=[];candidates={};inventories={}
 for sn,(tag,filename,sha,count) in enumerate(SPECS):
  data=(donors/filename).read_bytes()
  if hashlib.sha256(data).hexdigest()!=sha:raise ValueError('Unexpected donor '+tag)
  ptr=lambda p:struct.unpack_from('<I',data,p)[0]-0x08000000
  tables={k:ptr(o) for k,o in [('names',0x144),('stats',0x1bc),('front',0x128),('back',0x12c),('palette',0x130)]}
  sources.append(dict(tag=tag,filename=filename,sha256=sha,bytes=len(data),tables=tables,slots=count))
  seen=set();inventories[tag]=[]
  for i in range(1,count):
   name=decode(data[tables['names']+i*11:tables['names']+(i+1)*11]);target=lookup.get(ALIASES.get(norm(name),norm(name)))
   form=FORMS.get(i) if tag=='swsh' else SCARLET_FORMS.get(i) if tag=='scarlet' else None
   if form:
    key='SPECIES_'+form
    if key not in ids:raise ValueError('Unknown form '+key)
    ident=ids[key];target=(key,ident,dex[entries[ident]['natDexNum']])
   elif tag=='swsh' and (831<=i<=938 or 1020<=i<=1073 or 1079<=i<=1082 or 1085<=i<=1101 or 1191<=i):continue
   if not target:continue
   key,ident,nat=target
   if ident in seen:continue
   seen.add(ident)
   inventories[tag].append(dict(slot=i,name=name,species=key,national_dex=nat))
   if ident in rows or ident in candidates:continue
   try:
    imported={};pointers={}
    for kind in ['front','back','palette']:
     p=struct.unpack_from('<I',data,tables[kind]+i*8)[0];gfx,compressed=lz77(data,p);pointers[kind]=p
     if kind=='palette':
      if len(gfx)!=32:raise ValueError('Invalid palette size')
      imported['palette.gbapal']=gfx
     else:
      if len(gfx) not in [2048,4096,6144,8192]:raise ValueError('Invalid sprite size')
      if len(set(gfx[:2048]))<3:raise ValueError('Empty/placeholder sprite')
      imported[kind+'.4bpp.lz']=compressed.ljust((len(compressed)+3)//4*4,b'\0')
    stats=list(data[tables['stats']+i*28:tables['stats']+i*28+6])
    if len(stats)!=6 or not all(stats):raise ValueError('Invalid stats')
   except (ValueError,IndexError,struct.error) as e:
    rejected.append(dict(donor=tag,slot=i,species=key,reason=str(e)));continue
   donor_id=10000+sn*2000+i
   for ext,v in imported.items():assets[f'{donor_id}/{ext}']=v
   row=dict(species=key,species_id=ident,national_dex=nat,donor_id=donor_id,origin=tag,donor_slot=i,donor_name=name,donor_pointers=pointers,stats=stats,types=re.findall(r'TYPE_(\w+)',entries[ident]['types']),mega='_MEGA' in key,learnset=[],native_metadata=True)
   candidates[ident]=row
 rows.update(candidates)
 def native_row(key,ident,nat):
  f=entries[ident];stats=[int(f[k]) for k in ['baseHP','baseAttack','baseDefense','baseSpeed','baseSpAttack','baseSpDefense']]
  return dict(species=key,species_id=ident,national_dex=nat,donor_id=20000+ident,origin='native-expansion',stats=stats,types=re.findall(r'TYPE_(\w+)',f['types']),mega='_MEGA' in key,learnset=[],native_metadata=True,native_graphics=True)
 supplied={r['national_dex'] for r in rows.values()}
 missing_from_uploads=sorted(set(range(1,1026))-supplied)
 for nat,(key,ident) in bases.items():
  if ident not in rows:rows[ident]=native_row(key,ident,nat)
 # Close normal form-change dependencies, excluding size and Z/Ultra mechanics.
 formtables={};idtables={}
 for m in re.finditer(r'static const u16 (\w+)\[\] =\s*\{',raw):
  b=m.end()-1;idtables[m[1]]=[int(v) for v in re.findall(r'\b\d+\b',raw[b+1:matching(raw,b)])]
 for m in re.finditer(r'static const struct FormChange (\w+)\[\] =\s*\{',raw):
  b=m.end()-1;formtables[m[1]]=raw[b+1:matching(raw,b)]
 changed=True
 while changed:
  changed=False
  for r in list(rows.values()):
   table=entries[r['species_id']].get('formChangeTable')
   dependencies=[]
   for method,target in re.findall(r'\{\s*(FORM_CHANGE_\w+),\s*(\d+)',formtables.get(table,'')):
    if not any(s in method for s in ['GIGANTAMAX','ULTRA_BURST','TERASTALLIZATION']):dependencies.append(int(target))
   dependencies+=idtables.get(entries[r['species_id']].get('formSpeciesIdTable'),[])
   for ident in dependencies:
    if ident in rows or ident not in entries or ident==0:continue
    if entries[ident].get('isTeraForm') in ['1','TRUE']:continue
    keys=[n for n,v in ids.items() if v==ident and not any(x in n for x in ['GMAX','ETERNAMAX','_MEGA'])]
    if not keys:continue
    key=max(keys,key=len);nat=dex[entries[ident]['natDexNum']]
    rows[ident]=native_row(key,ident,nat);changed=True
 report=dict(species_count=len(rows),base_species_count=1025,form_count=len(rows)-1025,mega_count=sum(r['mega'] for r in rows.values()),missing_base_species=[],missing_mega_species=[],missing_base_species_from_uploads=missing_from_uploads,native_graphics_fallbacks=[r['species'] for r in rows.values() if r.get('native_graphics')],excluded_gmax_from_previous=[r['species'] for r in prior['catalog'] if '_GMAX' in r['species']],disabled_mechanics=['Dynamax','Gigantamax','Z-Moves'],sources=sources,donor_inventories=inventories,rejected_assets=rejected,catalog=sorted(rows.values(),key=lambda r:r['species_id']))
 output.mkdir(parents=True,exist_ok=True);assets['catalog.json']=(json.dumps(report,indent=2)+'\n').encode()
 with zipfile.ZipFile(output/'donor-assets.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for name,data in sorted(assets.items()):
   info=zipfile.ZipInfo(name,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16;z.writestr(info,data)
 (output/'donor-inventory.json').write_text(json.dumps({k:v for k,v in report.items() if k!='catalog'},indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k in ['species_count','base_species_count','form_count','mega_count','missing_base_species_from_uploads']},indent=2))
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--preprocessed',type=Path,required=True);p.add_argument('--donors',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();extract(a.source,a.preprocessed.read_text(),a.donors,a.output)
