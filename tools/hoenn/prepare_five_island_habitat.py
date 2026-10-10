"""Make Five Island's four assigned families reachable through native grass encounters."""
import argparse,copy,hashlib,json,re,struct
from pathlib import Path
from prepare_battle_database import PRIOR,LAYER as PREVIOUS
from prepare_ecology import LAND_RATES,weighted_slots
LAYER='five-island-habitat';PRIOR=PRIOR+[PREVIOUS]
ROOT=Path(__file__).resolve().parents[2]
def prepare(source):
 source=Path(source);marker=source/('.journey-'+LAYER)
 if marker.exists():
  r=json.loads(marker.read_text())
  for p,h in (r['prepared_sha256']|r['preserved_native_sha256']).items():assert hashlib.sha256((source/p).read_bytes()).hexdigest()==h,p
  return r
 expected=dict(json.loads((source/'.source-acquired.json').read_text())['sha256'])
 for layer in PRIOR:expected.update(json.loads((source/('.journey-'+layer)).read_text())['prepared_sha256'])
 originals={};outputs={};preserved={}
 def read(p):
  raw=(source/p).read_bytes();h=hashlib.sha256(raw).hexdigest();assert h==expected[p],p;preserved[p]=h;return raw
 def stage(p,raw):
  if isinstance(raw,str):raw=raw.encode()
  before=read(p);originals[p]=hashlib.sha256(before).hexdigest();outputs[p]=raw;preserved.pop(p,None)
 ecology=json.loads((source/'.journey-remote-islands').read_text());h=next(h for h in ecology['locations_data'] if h['section']=='MAPSEC_FIVE_ISLAND');ident='MAP_FIVE_ISLAND'
 assert len(h['families'])==4 and not any(p['map']==ident for p in ecology['pools'])
 m=json.loads(read('data/maps/FiveIsland_Frlg/map.json'));layout=next(l for l in json.loads(read('data/layouts/layouts.json'))['layouts'] if l['id']==m['layout'])
 path=layout['blockdata_filepath'];w=layout['width'];tiles=list(struct.unpack('<'+'H'*(w*layout['height']),read(path)))
 grass=[[x,y] for y in [7,8] for x in range(13,17)]
 for x,y in grass:
  before=tiles[y*w+x];assert before>>12==3 and not before&0xC00,(x,y,hex(before));tiles[y*w+x]=0x300D
 stage(path,struct.pack('<'+'H'*len(tiles),*tiles))
 metadata=json.loads((ROOT/'tools/hoenn/catalog_metadata.json').read_text())['species'];slots=weighted_slots(h['families'],LAND_RATES)
 path='src/data/wild_encounters.json';encounters=json.loads(read(path));rows=encounters['wild_encounter_groups'][0]['encounters']
 row=next(e for e in rows if e['map']==ident);assert 'land_mons' not in row
 row['land_mons']=copy.deepcopy(next(e['land_mons'] for e in rows if e['map']=='MAP_ROUTE101'))
 for mon,sid in zip(row['land_mons']['mons'],slots):mon['species']=metadata[str(sid)]['name']
 stage(path,json.dumps(encounters,indent=2)+'\n')
 ecology['pools'].append(dict(map=ident,area=0,roots=slots))
 ecology['map_species'][ident]=sorted({m['id'] for f in h['families'] for m in f['species']})
 ecology['field_slots'][ident]['land_mons']=dict(slots=[metadata[str(sid)]['name'] for sid in slots])
 path='include/journey_wild_data.h';wild=read(path).decode();pool='{'+', '.join([ident,'0',str(len(slots)),'{'+', '.join(metadata[str(sid)]['name'] for sid in slots)+'}'])+'}'
 pattern=r'(static const struct JourneyWildPool sJourneyWildPools\[\] = \{\n)(.*?)(\n\};)'
 wild,count=re.subn(pattern,lambda match:match[1]+match[2]+',\n'+pool+match[3],wild,flags=re.S);assert count==1;stage(path,wild)
 path='include/journey_habitat_data.h';dex=read(path).decode()
 members=ecology['map_species'][ident];new='{'+', '.join([ident,str(len(members)),'{'+', '.join(metadata[str(sid)]['name'] for sid in members)+'}'])+'}'
 dex,count=re.subn(r'\{MAP_FIVE_ISLAND,\s*0,\s*\{\}\}',lambda match:new,dex);assert count==1;stage(path,dex)
 r=dict(layer=LAYER,map='FiveIsland_Frlg',grass=grass,family_roots=[f['root'] for f in h['families']],locations_data=ecology['locations_data'],map_species=ecology['map_species'],pools=ecology['pools'],field_slots=ecology['field_slots'],original_sha256=originals,prepared_sha256={p:hashlib.sha256(raw).hexdigest() for p,raw in outputs.items()},preserved_native_sha256=preserved,native_maps_npcs_warps_and_stories_preserved=True,all_families_have_active_pools=all(any(p['map'] in h['maps'] for p in ecology['pools']) for h in ecology['locations_data']))
 assert r['all_families_have_active_pools']
 for p,raw in outputs.items():(source/p).write_bytes(raw)
 marker.write_text(json.dumps(r,indent=2)+'\n');return r
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);a=p.parse_args();r=prepare(a.source);print('Five Island active grass habitat:',r['family_roots'])
