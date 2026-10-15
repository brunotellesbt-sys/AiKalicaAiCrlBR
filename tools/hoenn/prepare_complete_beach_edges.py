"""Close generated beach edges with native eight-pixel shoreline quadrants.

No terrain is removed or added. Original town beaches and approved ports are
untouched. Shared metatile meanings also work in the connected map buffers.
"""
import argparse,json,re,struct
from pathlib import Path
from candidate_layer import Layer
from render_sea_maps import MapRenderer
from prepare_native_coastal_fragments import PRIOR,LAYER as PREVIOUS
LAYER='complete-beach-edges';PRIOR=PRIOR+[PREVIOUS]

def prepare(source):
 layer=Layer(source,LAYER,PRIOR)
 if old:=layer.existing():return old
 s=layer.source;r=MapRenderer(s);maps={p.parent.name:json.loads(p.read_text()) for p in (s/'data/maps').glob('*/map.json')};byid={m['id']:n for n,m in maps.items()};records=[];patterns={'frlg':{},'emerald':{}};bankthemes={};updates={}
 for name,m in sorted(maps.items()):
  if not name.startswith('Journey') or m['map_type'] not in ['MAP_TYPE_ROUTE','MAP_TYPE_OCEAN_ROUTE'] or 'Shipyard' in name:continue
  l=r.layouts[m['layout']];theme=l['layout_version'];fr=theme=='frlg';w,h=l['width'],l['height'];p=l['blockdata_filepath'];v=list(struct.unpack('<'+'H'*w*h,(s/p).read_bytes()));original=v[:]
  shore=[0x10C,0x10D,0x10E,0x114,0x115,0x116,0x11C,0x11D,0x11E] if fr else [0x11B,0x11C,0x11D,0x123,0x124,0x125,0x12B,0x12C,0x12D];water=0x12B if fr else 0x170;primary=r.tileset(l['primary_tileset'])[2];native={tuple(primary[mid*8:(mid+1)*8]):mid for mid in shore};cells=[]
  def sea(x,y):return 0<=x<w and 0<=y<h and original[y*w+x]&1023==water
  for y in range(h):
   for x in range(w):
    old=original[y*w+x]&1023
    if old not in shore:continue
    words=list(primary[shore[4]*8:(shore[4]+1)*8]);inner=0
    for q,(dx,dy) in enumerate([(-1,-1),(1,-1),(-1,1),(1,1)]):
     horizontal=sea(x+dx,y);vertical=sea(x,y+dy)
     if not horizontal and not vertical and sea(x+dx,y+dy):
      # The opposite native rounded corner, flipped, closes the inside bend.
      mid=shore[[8,6,2,0][q]];opp=3-q;inner|=1<<q
      for lev in [0,1]:words[lev*4+q]=primary[mid*8+lev*4+opp]^0xC00
     else:
      row=(0 if dy<0 else 2) if vertical else 1;col=(0 if dx<0 else 2) if horizontal else 1;mid=shore[row*3+col]
      for lev in [0,1]:words[lev*4+q]=primary[mid*8+lev*4+q]
    words=tuple(words)
    if words in native:v[y*w+x]=(original[y*w+x]&~1023)|native[words]
    else:patterns[theme].setdefault(words,len(patterns[theme]));cells.append((x,y,words))
  # Reuse common map-buffer meanings in every neighboring exterior bank.
  if cells:
   affected=[name]+[byid[c['map']] for c in m.get('connections') or [] if c['direction'] in ['up','down','left','right'] and c['map'] in byid]
   for n in affected:
    ll=r.layouts[maps[n]['layout']]
    if ll['layout_version']==theme:bankthemes[ll['secondary_tileset']]=theme
   updates[p]=(l,v,original,cells);records.append(dict(map=name,compound_shore_tiles=len(cells),native_edge_tiles_adjusted=sum(a!=b for a,b in zip(original,v))))
  elif v!=original:updates[p]=(l,v,original,cells);records.append(dict(map=name,compound_shore_tiles=0,native_edge_tiles_adjusted=sum(a!=b for a,b in zip(original,v))))
 assert len(patterns['emerald'])<=20 and len(patterns['frlg'])<=48,[(k,len(v)) for k,v in patterns.items()]
 ids={'emerald':dict(zip(patterns['emerald'],range(1004,1024))),'frlg':dict(zip(patterns['frlg'],range(976,1024)))}
 headers=(s/'src/data/tilesets/headers.h').read_text();metas=(s/'src/data/tilesets/metatiles.h').read_text();banks=[]
 for bank,theme in sorted(bankthemes.items()):
  fr=theme=='frlg';cutoff=640 if fr else 512;body=re.search(r'const struct Tileset '+bank+r'\s*=\s*\{(.*?)\};',headers,re.S)[1]
  files={}
  for field in ['metatiles','metatileAttributes']:
   sym=re.search(r'\.'+field+r'\s*=\s*(\w+)',body)[1];match=re.search(r'const u(16|32) '+sym+r'\[\] = INCBIN_U(?:16|32)\("([^"]+)"\)',metas);assert match,(bank,field);files[field]=(match[2],4 if fr and field=='metatileAttributes' else int(match[1])//8)
  p,size=files['metatiles'];raw=(s/p).read_bytes();values=list(struct.unpack('<'+'H'*(len(raw)//2),raw));existing=len(values)//8;first=min(ids[theme].values())-cutoff
  assert existing<=first,(bank,'Would overwrite native metatiles',existing,first)
  count=max(ids[theme].values())-cutoff+1;values.extend([0]*(count*8-len(values)))
  for words,mid in ids[theme].items():at=(mid-cutoff)*8;values[at:at+8]=words
  layer.stage(p,struct.pack('<'+'H'*len(values),*values))
  p,size=files['metatileAttributes'];raw=bytearray((s/p).read_bytes());assert len(raw)//size<=first
  layout=next(l for l in r.layouts.values() if l['secondary_tileset']==bank and l['layout_version']==theme);primarybody=re.search(r'const struct Tileset '+layout['primary_tileset']+r'\s*=\s*\{(.*?)\};',headers,re.S)[1];sym=re.search(r'\.metatileAttributes\s*=\s*(\w+)',primarybody)[1];primarypath=re.search(r'\b'+sym+r'\[\].*?"([^"]+)"',metas)[1];flat=0x115 if fr else 0x124;attribute=(s/primarypath).read_bytes()[flat*size:(flat+1)*size];assert len(attribute)==size
  raw.extend(bytes(count*size-len(raw)))
  for mid in ids[theme].values():at=(mid-cutoff)*size;raw[at:at+size]=attribute
  layer.stage(p,raw);banks.append(dict(bank=bank,theme=theme,original_metatiles=existing,complete_beach_ids=list(ids[theme].values())))
 for p,(l,v,original,cells) in updates.items():
  for x,y,words in cells:v[y*l['width']+x]=(original[y*l['width']+x]&~1023)|ids[l['layout_version']][words]
  layer.stage(p,struct.pack('<'+'H'*len(v),*v))
 return layer.finish(maps=records,banks=banks,patterns={k:[dict(id=ids[k][words],words=words) for words in v] for k,v in patterns.items()},native_corner_art_only=True,terrain_and_collisions_unchanged=True,approved_ports_and_original_town_beaches_preserved=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);print(prepare(p.parse_args().source)['layer'])
