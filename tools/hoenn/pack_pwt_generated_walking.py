"""Pack authored walking sheets into uniform GBA frames with shared palettes.

Only technical cropping, nearest-neighbor fitting, frame ordering and indexed
palette conversion are performed. Designs and animation poses are authored in
the stored source sheets.
"""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2]
def occupied_bands(image,count):
    alpha=image.getchannel('A');width,height=image.size
    rows=[sum(v>=128 for v in alpha.crop((0,y,width,y+1)).getdata())>=12 for y in range(height)]
    runs=[];start=None
    for y,value in enumerate(rows+[False]):
        if value and start is None:start=y
        if not value and start is not None:
            if runs and start-runs[-1][1]<4:runs[-1][1]=y
            else:runs.append([start,y])
            start=None
    assert len(runs)==count,('Expected one authored row per identity',runs,count)
    return [(max(0,a-3),min(height,b+3)) for a,b in runs]
def palette_indexed(canvas):
    alpha=canvas.getchannel('A');pixels=list(canvas.convert('RGB').getdata())
    visible=[c for c,a in zip(pixels,alpha.getdata()) if a>=128]
    assert visible
    sample=Image.new('RGB',(len(visible),1));sample.putdata(visible)
    quantized=sample.quantize(colors=15,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
    palette=quantized.getpalette()[:45]
    quant=canvas.convert('RGB').quantize(palette=quantized,dither=Image.Dither.NONE)
    result=Image.new('P',canvas.size);result.putpalette([0,0,0]+palette+[0]*(768-48))
    result.putdata([q+1 if a>=128 else 0 for q,a in zip(quant.getdata(),alpha.getdata())])
    result.info['transparency']=0
    return result
def pack(directory,output):
    directory,output=Path(directory),Path(output);output.mkdir(parents=True,exist_ok=True)
    batches=json.loads((directory/'batches.json').read_text());records=[]
    for batch in batches:
        path=directory/('sheet-'+str(batch['index']).zfill(2)+'.png')
        image=Image.open(path).convert('RGBA');bands=occupied_bands(image,len(batch['keys']))
        for row,(key,name) in enumerate(zip(batch['keys'],batch['names'])):
            cells=[];boxes=[]
            for column in range(9):
                left=round(column*image.width/9);right=round((column+1)*image.width/9)
                cell=image.crop((left,bands[row][0],right,bands[row][1]))
                box=cell.getchannel('A').point(lambda x:255 if x>=128 else 0).getbbox()
                assert box is not None,(key,column)
                boxes.append([left+box[0],bands[row][0]+box[1],left+box[2],bands[row][0]+box[3]])
                cells.append(cell.crop(box))
            ratio=min(30/max(c.width for c in cells),30/max(c.height for c in cells))
            canvas=Image.new('RGBA',(32,32*9))
            for frame,cell in enumerate(cells):
                sprite=cell.resize((max(1,round(cell.width*ratio)),max(1,round(cell.height*ratio))),Image.Resampling.NEAREST)
                canvas.alpha_composite(sprite,((32-sprite.width)//2,frame*32+31-sprite.height))
            target=output/(key.lower()+'-walking.png');palette_indexed(canvas).save(target)
            records.append(dict(key=key,name=name,file=target.name,frames=9,width=32,height=32,
                source_sheet=path.name,source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                source_reference=Path(batch['reference']).name,source_boxes=boxes,
                converted_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                frame_order=['front_idle','back_idle','left_idle','front_left','front_right','back_left','back_right','left_left','left_right']))
    assert len(records)==79 and len({r['key'] for r in records})==79
    manifest=dict(authored_with='image_gen',records=records)
    (output/'sources.json').write_text(json.dumps(manifest,indent=2)+'\n')
    contact=Image.new('RGB',(8*150,10*100),(230,235,241));draw=ImageDraw.Draw(contact)
    for i,r in enumerate(records):
        sheet=Image.open(output/r['file']).convert('RGBA');x=(i%8)*150;y=(i//8)*100
        for f in range(3):contact.paste(sheet.crop((0,f*32,32,(f+1)*32)).resize((44,44),Image.Resampling.NEAREST),(x+f*48,y+2),sheet.crop((0,f*32,32,(f+1)*32)).resize((44,44),Image.Resampling.NEAREST))
        draw.text((x+2,y+56),r['name'],fill=(10,20,30))
    contact.save(output/'contact.png')
    return manifest
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--directory',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print('Packed characters:',len(pack(a.directory,a.output)['records']))
