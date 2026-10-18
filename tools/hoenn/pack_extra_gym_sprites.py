"""Restore donor palette-index-0 transparency before native 4bpp conversion.

This is an indexed sprite-format repair, not new character artwork. Sources
are pinned by the existing PWT catalog and verified before conversion.
"""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
KEYS=['MORTY','WHITNEY','STEVEN','BUGSY','CANDICE','CLAIR','KAREN']
def pack(raw,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    refs={r['key']:r for r in json.loads((ROOT/'tools/hoenn/data/pwt/walking/sources.json').read_text())['walking']};records=[]
    for key in KEYS:
        p=Path(raw)/(key.lower()+'.png');ref=refs[key]
        assert hashlib.sha256(p.read_bytes()).hexdigest()==ref['sha256']
        image=Image.open(p);assert image.mode=='P' and image.width in [16,32] and image.height>=288
        colors=image.getpalette();colors=(colors+[0]*48)[:48];width=32 if key=='CANDICE' else 16
        result=Image.new('P',(width,288));result.putpalette(colors)
        boxes=[]
        for frame in range(9):
            crop=image.crop((0,frame*32,image.width,(frame+1)*32))
            # The source's tRNS was absent or marked every entry opaque. In a
            # GBA object sheet, index zero is transparent irrespective of tRNS.
            mask=crop.point(lambda v:255 if v else 0);box=mask.getbbox()
            if box is None:
                fallback=[0,1,2,0,0,1,1,2,2][frame]
                crop=image.crop((0,fallback*32,image.width,(fallback+1)*32));mask=crop.point(lambda v:255 if v else 0);box=mask.getbbox()
            assert box
            body=crop.crop(box);ratio=min((24 if key=='CANDICE' else width)/body.width,28/body.height)
            body=body.resize((max(1,round(body.width*ratio)),max(1,round(body.height*ratio))),Image.Resampling.NEAREST)
            result.paste(body,((width-body.width)//2,frame*32+31-body.height))
            boxes.append([body.width,body.height])
        target=output/(key.lower()+'.png');result.save(target,transparency=0)
        pal=output/(key.lower()+'.pal');pal.write_text('JASC-PAL\n0100\n16\n'+'\n'.join(' '.join(map(str,colors[i:i+3])) for i in range(0,48,3))+'\n')
        records.append(dict(key=key,width=width,height=32,frames=9,source_sha256=ref['sha256'],repository=ref['repository'],commit=ref['commit'],path=ref['path'],file=target.name,sha256=hashlib.sha256(target.read_bytes()).hexdigest(),palette_sha256=hashlib.sha256(pal.read_bytes()).hexdigest(),visible_frames=boxes,transparent_index=0))
    (output/'sources.json').write_text(json.dumps(dict(index_zero_is_transparent=True,records=records),indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--raw',required=True);p.add_argument('--output',required=True);a=p.parse_args();pack(a.raw,a.output)
