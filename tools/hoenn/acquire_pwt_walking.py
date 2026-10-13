"""Acquire a pinned walking-sheet catalog and convert verified nine-frame sheets.

Missing identities are reported explicitly, never substituted with generic NPCs.
"""
import argparse,hashlib,json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
from PIL import Image
from acquire_pwt_references import acquire
from pack_crossover_assets import fit,indexed
from pwt_catalog import load
ROOT=Path(__file__).resolve().parents[2]
REPO='jbfish00/Unbound-Character-Mode'
COMMIT='1dbb46d3e1609cadade70cf2efe246cc75d7f8e8'
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'.local/pwt-walking-assets');a=p.parse_args()
    out=a.output;out.mkdir(parents=True,exist_ok=True)
    tree=json.loads(subprocess.run(['gh','api',f'repos/{REPO}/git/trees/{COMMIT}?recursive=1'],check=True,capture_output=True).stdout)
    assert not tree['truncated']
    paths={r['path'] for r in tree['tree'] if r['type']=='blob'}
    def work(row):
        key=row['key'];path=f'assets/donor_sprites_staged/{key.lower()}/ow.png'
        if path not in paths:return dict(key=key,status='missing')
        raw=out/(key.lower()+'-raw.png');record=acquire(REPO,COMMIT,path,raw)
        image=Image.open(raw).convert('RGBA')
        horizontal = image.height == 32 and image.width in (144,288)
        assert horizontal or (image.width in (16,32) and image.height>=9*32 and image.height%32==0),(key,image.size)
        canvas=Image.new('RGBA',(16,288))
        for frame in range(9):
            crop=image.crop((frame*image.width//9,0,(frame+1)*image.width//9,32)) if horizontal else image.crop((0,32*frame,image.width,32*(frame+1)))
            assert crop.getbbox() is not None,(key,frame)
            canvas.alpha_composite(fit(crop,16,32),(0,frame*32))
        packed=out/(key.lower()+'-walking.png');indexed(canvas).save(packed)
        record.update(key=key,status='acquired',converted=packed.name,
                      converted_sha256=hashlib.sha256(packed.read_bytes()).hexdigest(),
                      original_size=list(image.size),frames=9)
        return record
    with ThreadPoolExecutor(max_workers=6) as pool:records=list(pool.map(work,load()))
    (out/'sources.json').write_text(json.dumps(dict(walking=records),indent=2)+'\n')
    print('Acquired walking sheets:',sum(r['status']=='acquired' for r in records),
          'Missing:',sum(r['status']=='missing' for r in records))
if __name__=='__main__':main()
