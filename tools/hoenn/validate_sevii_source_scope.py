"""Audit the compiled coast GPS and prove unrelated source/ports stayed intact."""
import argparse,hashlib,json,re,struct,subprocess
from pathlib import Path
import numpy as np
from prepare_world_route_chart import PRIOR,LAYER
from prepare_sevii_surf_connections import PRIOR as BASE

ROOT=Path(__file__).resolve().parents[2]

def audit(source,output):
    source,output=Path(source),Path(output);output.mkdir(parents=True,exist_ok=True)
    layers=PRIOR+[LAYER];base=layers[:len(BASE)];delta=layers[len(BASE):];expected=json.loads((source/'.source-acquired.json').read_text())['sha256'].copy()
    for n in base:expected.update(json.loads((source/('.journey-'+n)).read_text())['prepared_sha256'])
    final={};reports=[]
    for n in delta:
        r=json.loads((source/('.journey-'+n)).read_text());reports.append(r);final.update(r['prepared_sha256'])
    changed={n:h for n,h in final.items() if expected.get(n)!=h}
    unchanged={n:h for n,h in expected.items() if n not in changed}
    for n,h in unchanged.items():assert hashlib.sha256((source/n).read_bytes()).hexdigest()==h,('Unrelated source changed',n)
    for n,h in final.items():assert hashlib.sha256((source/n).read_bytes()).hexdigest()==h,n
    assert not any('sootopolis' in n.lower() or 'pallet' in n.lower() for n in final)
    shared='data/layouts/Island_Harbor_Frlg/map.bin'
    assert final[shared]==expected[shared],'Birth/Navel shared arrival layout changed'
    assert all(r['native_land_unchanged'] for r in reports[0]['terrain'])
    assert reports[0]['port_buildings_boats_captains_and_warps_unchanged']
    nm=subprocess.check_output([str(ROOT/'.local/arm-binutils/usr/bin/arm-none-eabi-nm'),'-S',str(source/'pokeemerald.elf')],text=True)
    symbols={n:(int(a,16)-0x08000000,int(z,16)) for a,z,_,n in re.findall(r'^(\w+) (\w+) (\w) (\S+)$',nm,re.M)};rom=(source/'pokeemerald.gba').read_bytes()
    at,z=symbols['sWorldNavigationPixels'];packed=np.frombuffer(rom[at:at+z],dtype='<u2');values=np.stack([packed&255,packed>>8],axis=1).astype(int)
    assert len(values)==reports[-1]['gps']['compiled_gps_tiles']
    projections=json.loads((source/'.journey-world-route-chart').read_text())['projections'];grids={};at,z=symbols['sWorldTileGrids'];stride=z//len(projections);maximum=0
    for i,p in enumerate(projections):
        first,ident,w,h=struct.unpack_from('<IHHH',rom,at+i*stride);assert [w,h]==[p['width'],p['height']]
        grid=values[first:first+w*h].reshape(h,w,2);grids[p['map']]=grid
        for axis in [0,1]:
            if grid.shape[axis]>1:maximum=max(maximum,int(abs(np.diff(grid,axis=axis)).max()))
    maps={p.parent.name:json.loads(p.read_text()) for p in (source/'data/maps').glob('*/map.json')};byid={m['id']:n for n,m in maps.items()};seams=0
    for n,a in grids.items():
        h,w=a.shape[:2]
        for c in maps[n].get('connections') or []:
            o=byid.get(c['map']);d=c['direction'];off=c['offset']
            if o not in grids or d not in ['left','right','up','down']:continue
            b=grids[o];oh,ow=b.shape[:2]
            for t in range(max(0,off),min(h if d in ['left','right'] else w,off+(oh if d in ['left','right'] else ow))):
                x,y=(0 if d=='left' else w-1,t) if d in ['left','right'] else (t,0 if d=='up' else h-1)
                xx,yy=(ow-1 if d=='left' else 0,t-off) if d in ['left','right'] else (t-off,oh-1 if d=='up' else 0)
                assert np.array_equal(a[y,x],b[yy,xx]),(n,o,x,y,xx,yy)
            seams+=1
    assert maximum<=2
    proof=dict(passed=True,rom_sha256=hashlib.sha256(rom).hexdigest(),layers=layers,base_layers=len(BASE),new_layers=delta,
               changed_source_files=sorted(changed),overlay_output_files=sorted(final),unchanged_source_inputs_checked=len(unchanged),
               preserved_port_paths={n:h for n,h in unchanged.items() if 'sootopolis' in n.lower() or 'pallet' in n.lower()},
               port_buildings_boats_captains_and_warps_unchanged=True,native_sevii_land_unchanged=True,
               birth_and_navel_arrival_layout_preserved=True,
               compiled_gps_tiles=len(values),maximum_neighbor_pixel_step=maximum,maximum_seam_delta=0,compiled_shared_edges=seams,
               full_campaign_playthrough=False)
    (output/'sevii-source-scope.json').write_text(json.dumps(proof,indent=2)+'\n');print('Sevii scope/GPS passed:',len(unchanged),'unchanged inputs;',len(changed),'changed files;',len(values),'GPS tiles')
    return proof

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();audit(a.source,a.output)
