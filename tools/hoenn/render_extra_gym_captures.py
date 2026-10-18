"""Arrange unaltered emulator frames; label the tested ROM and locations."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw
from extra_gyms import GYMS

def render(native,rom,output,captures=None):
    native,rom,output=map(Path,[native,rom,output]);r=json.loads((native/'extra-gyms.json').read_text())
    assert r['passed'] and r['rom_sha256']==hashlib.sha256(rom.read_bytes()).hexdigest()
    captures=Path(captures) if captures else native
    if captures!=native:
        presentation=json.loads((captures/'presentation-captures.json').read_text())
        assert presentation['rom_sha256']==r['rom_sha256'] and presentation['native_emulator_frames']
    canvas=Image.new('RGB',(980,792),'#202d35');draw=ImageDraw.Draw(canvas);frames=[]
    for i,g in enumerate(GYMS):
        x=i%2*490;y=i//2*198;leader='Valerie' if g['key']=='WHITNEY' and r['max_national']>493 else g['leader']
        draw.text((x+6,y+4),g['city']+' - '+leader,fill='white')
        draw.text((x+6,y+20),'FORA',fill='white');draw.text((x+250,y+20),'DENTRO',fill='white')
        for j,kind in enumerate(['outside','inside']):
            p=captures/(g['key'].lower()+'-'+kind+'.png');im=Image.open(p);assert im.size==(240,160)
            canvas.paste(im,(x+4+j*244,y+36));frames.append(dict(file=p.as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    output.parent.mkdir(parents=True,exist_ok=True);canvas.save(output)
    output.with_suffix('.json').write_text(json.dumps(dict(rom_sha256=r['rom_sha256'],unaltered_emulator_frames=True,frames=frames),indent=2)+'\n')
    # Keep the four unobstructed approaches reviewable without stitching or
    # altering any game pixels. Each row contains the same gym's four views.
    checkpoints=Image.new('RGB',(960,1520),'#202d35');labels=ImageDraw.Draw(checkpoints);frames=[]
    for i,g in enumerate(GYMS):
        for j in range(4):
            p=captures/(g['key'].lower()+'-checkpoint-'+str(j+1)+'.png')
            im=Image.open(p);assert im.size==(240,160)
            x,y=j*240,i*190
            labels.text((x+4,y+5),g['key']+' '+str(j+1),fill='white')
            checkpoints.paste(im,(x,y+25));frames.append(dict(file=p.as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    p=output.parent/'quatro-treinadores-ginasios.png';checkpoints.save(p)
    p.with_suffix('.json').write_text(json.dumps(dict(rom_sha256=r['rom_sha256'],native_emulator_frames=True,unaltered_emulator_frames=True,
        defeated_flags_are_presentation_fixtures=True,approach_tests_are_separate=True,frames=frames),indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--native',required=True);p.add_argument('--rom',required=True);p.add_argument('--output',required=True);p.add_argument('--captures');a=p.parse_args();render(a.native,a.rom,a.output,a.captures)
