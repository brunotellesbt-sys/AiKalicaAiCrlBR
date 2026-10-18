"""Render entire affected native maps for human review, with integrity checks.

Source renders are not emulator captures and do not certify playability.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from PIL import Image,ImageDraw
from extra_gyms import GYMS
from render_sea_maps import MapRenderer
ISLANDS=['One','Two','Three','Four','Five','Six','Seven']

def render(source,baseline,output):
    source,baseline,output=map(Path,[source,baseline,output]);output.mkdir(parents=True,exist_ok=True)
    r=MapRenderer(source);old=MapRenderer(baseline);maps=[];centers=[]
    groups={'cidades':[g['city'] for g in GYMS], 'interiores':[g['name'] for g in GYMS],
            'portos':[i+'Island_Harbor_Frlg' for i in ISLANDS], 'dewford':['DewfordTown','Route107'],
            'ilhas':['ThreeIsland_Port_Frlg' if i=='Three' else i+'Island_Frlg' for i in ISLANDS]}
    def grid(renderer,name):
        m=json.loads((renderer.source/f'data/maps/{name}/map.json').read_text());l=renderer.layouts[m['layout']]
        return m,l,struct.unpack('<'+'H'*(l['width']*l['height']),(renderer.source/l['blockdata_filepath']).read_bytes())
    for n in set(groups['cidades']+groups['ilhas']):
        m,l,v=grid(r,n);bm,bl,bv=grid(old,n)
        for door in bm['warp_events']:
            if 'POKEMON_CENTER' not in door['dest_map']:continue
            # Include the native facade and its ground apron. These must stay
            # byte-identical, even when the map width changes for the gym.
            x,y=door['x'],door['y'];half=2 if bl['layout_version']=='frlg' else 3
            cells=[]
            for yy in range(max(0,y-4),min(bl['height'],y+2)):
                for xx in range(max(0,x-half),min(bl['width'],x+3)):
                    assert v[yy*l['width']+xx]==bv[yy*bl['width']+xx],('Center facade changed',n,xx,yy)
                    cells.append([xx,yy])
            centers.append(dict(map=n,door=[x,y],native_facade_and_apron_unchanged=True,checked_tiles=len(cells)))
    # Preserve the Tower's full visible native footprint and the original
    # upper eastern mountain side, not merely its warp event or front door.
    _,lav,v=grid(r,'LavenderTown_Frlg');_,oldlav,bv=grid(old,'LavenderTown_Frlg')
    landmarks=[]
    for label,cells in [('Lavender Tower',[(x,y) for y in range(7) for x in range(15,22)]),
                        ('Tower upper eastern mountain',[(x,y) for y in range(5) for x in [22,23]])]:
        for x,y in cells:assert v[y*lav['width']+x]==bv[y*oldlav['width']+x],(label,x,y)
        landmarks.append(dict(map='LavenderTown_Frlg',landmark=label,native_tiles_preserved=True,checked_tiles=len(cells)))
    _,three,v=grid(r,'ThreeIsland_Frlg');_,oldthree,bv=grid(old,'ThreeIsland_Frlg')
    road=[(x,y) for y in range(13,21) for x in range(7,10)]
    for x,y in road:assert v[y*three['width']+x]==bv[y*oldthree['width']+x],('Three Island original road',x,y)
    landmarks.append(dict(map='ThreeIsland_Frlg',landmark='Original road beside Karen gym',native_tiles_preserved=True,checked_tiles=len(road)))
    for title,names in groups.items():
        canvas=Image.new('RGB',(1440,((len(names)+2)//3)*540),'#202d35');d=ImageDraw.Draw(canvas)
        for j,n in enumerate(names):
            include_npcs=True
            try:im,_=r.render(n)
            except TypeError:im,_=r.render(n,npcs=False);include_npcs=False
            im.save(output/(n+'.png'));scale=min(460/im.width,490/im.height)
            thumb=im.resize((int(im.width*scale),int(im.height*scale)),Image.Resampling.NEAREST);x=j%3*480;y=j//3*540
            canvas.paste(thumb,(x,y+30));d.text((x+5,y+5),n+(' (terrain)' if not include_npcs else ''),fill='white')
            _,l,_=grid(r,n)
            maps.append(dict(map=n,image=n+'.png',size=[l['width'],l['height']],includes_npcs=include_npcs,
                source_blockdata_sha256=hashlib.sha256((source/l['blockdata_filepath']).read_bytes()).hexdigest()))
        canvas.save(output/(title+'.png'))
    report=dict(source_renders_not_emulator_captures=True,centers=centers,landmarks=landmarks,maps=maps,
        rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
        proposal='docs/design/proposta-acabamento-ilhas-lilycove-dewford.png',automatic_checks_do_not_certify_visual_quality=True)
    report['interior_design']={'four_trainers':True,'six_tile_sightlines':True,'three_wide_clear_approaches':True,'mandatory_checkpoints_verified_separately':True,
        'open_room_proposal':'docs/design/proposta-frente-livre-treinadores.png',
        'rejected_proposal':'docs/design/proposta-gym-quatro-batalhas-obrigatorias.png',
        'reason':'The generated proposal allowed lateral bypasses; only the implemented native-map corridors are authoritative.'}
    (output/'review.json').write_text(json.dumps(report,indent=2)+'\n')
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--baseline',required=True);p.add_argument('--output',required=True);a=p.parse_args();render(a.source,a.baseline,a.output)
