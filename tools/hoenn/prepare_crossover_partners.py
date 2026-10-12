"""Register custom back-facing throw animations and the two approved tag teams."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image
from pack_crossover_assets import indexed,DATA
from prepare_evolution_coherence import PRIOR,LAYER as PREVIOUS
ROOT=Path(__file__).resolve().parents[2];LAYER='crossover-partners';PRIOR=PRIOR+[PREVIOUS]
def prepare(source):
 source=Path(source);marker=source/('.journey-'+LAYER)
 if marker.exists():
  r=json.loads(marker.read_text())
  for p,h in r['prepared_sha256'].items():assert hashlib.sha256((source/p).read_bytes()).hexdigest()==h,p
  return r
 expected=dict(json.loads((source/'.source-acquired.json').read_text())['sha256'])
 for layer in PRIOR:expected.update(json.loads((source/('.journey-'+layer)).read_text())['prepared_sha256'])
 outputs={};originals={}
 def stage(p,text):
  old=(source/p).read_bytes() if (source/p).exists() else None;h=hashlib.sha256(old).hexdigest() if old else None;assert h==expected.get(p),p
  if h:originals[p]=h
  outputs[p]=text.encode() if isinstance(text,str) else text
 sheet=Image.open(DATA/'partner-back-sheet.png').convert('RGBA')
 for row,hero in enumerate(['EREN','LUFFY']):
  frames=[]
  for a,b in [(0,350),(350,708),(708,1020),(1020,1480),(1490,1774)]:
   image=sheet.crop((a,0 if row==0 else 438,b,438 if row==0 else 887));frames.append(image.crop(image.getbbox()))
  scale=min(62/max(f.width for f in frames),62/max(f.height for f in frames));canvas=Image.new('RGBA',(64,320))
  for i,frame in enumerate(frames):
   frame=frame.resize((max(1,round(frame.width*scale)),max(1,round(frame.height*scale))),Image.Resampling.NEAREST);canvas.alpha_composite(frame,((64-frame.width)//2,64*(i+1)-frame.height))
  from io import BytesIO
  raw=BytesIO();indexed(canvas).save(raw,format='PNG');stage('graphics/trainers/back_pics/journey_'+hero.lower()+'.png',raw.getvalue())
 p='src/data/graphics/trainers.h';t=(source/p).read_text();at=t.index('#define TRAINER_FRONT_PIC');decl=''.join('const u8 gTrainerBackPic_Journey'+hero+'[] = INCBIN_U8("graphics/trainers/back_pics/journey_'+hero.lower()+'.4bpp");\nconst u16 gTrainerBackPalette_Journey'+hero+'[] = INCBIN_U16("graphics/trainers/back_pics/journey_'+hero.lower()+'.gbapal");\n' for hero in ['EREN','LUFFY'])
 decl+='static const union AnimCmd sJourneyPartnerThrow[] = {ANIMCMD_FRAME(0,20),ANIMCMD_FRAME(1,8),ANIMCMD_FRAME(2,8),ANIMCMD_FRAME(3,20),ANIMCMD_FRAME(4,1),ANIMCMD_END};\nstatic const union AnimCmd *const sJourneyPartnerAnims[]={sAnim_GeneralFrame0,sJourneyPartnerThrow,sAnim_GeneralFrame0};\n';t=t[:at]+decl+t[at:]
 for hero in ['EREN','LUFFY']:
  old='[TRAINER_PIC_JOURNEY_'+hero+'] = {.frontPic = TRAINER_FRONT_PIC(gTrainerFrontPic_Journey'+hero+', gTrainerPalette_Journey'+hero+')}'
  assert old in t;t=t.replace(old,old[:-1]+', .backPic = TRAINER_BACK_PIC(4,gTrainerBackPic_Journey'+hero+',gTrainerBackPalette_Journey'+hero+',sJourneyPartnerAnims)}')
 stage(p,t)
 p='include/constants/battle_partner.h';t=(source/p).read_text();assert '#define PARTNER_COUNT 3' in t;t=t.replace('#define PARTNER_COUNT 3','#define PARTNER_EREN 3\n#define PARTNER_LUFFY 4\n#define PARTNER_COUNT 5');stage(p,t)
 spec=json.loads((ROOT/'tools/hoenn/data/galactic-chapter.json').read_text());rows=[]
 for hero,team in spec['partners'].items():
  upper=hero.upper()
  rows.append('\n=== PARTNER_'+upper+' ===\nName: '+upper+'\nClass: Rival\nPic: Journey '+hero.title()+'\nGender: Male\nMusic: Male\nAI: Basic Trainer\n\n')
  for name in team:
   rows.append(name.title().replace('_','-')+'\nLevel: 70\nIVs: 20 HP / 20 Atk / 20 Def / 20 SpA / 20 SpD / 20 Spe\nHardy Nature\n\n')
 p='src/data/battle_partners.party';stage(p,(source/p).read_text()+'\n'+''.join(rows))
 r=dict(layer=LAYER,partners=spec['partners'],five_frame_custom_back_animations=True,original_sha256=originals,prepared_sha256={p:hashlib.sha256(raw).hexdigest() for p,raw in outputs.items()})
 for p,raw in outputs.items():(source/p).parent.mkdir(parents=True,exist_ok=True);(source/p).write_bytes(raw)
 marker.write_text(json.dumps(r,indent=2)+'\n');return r
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);a=p.parse_args();print(json.dumps(prepare(a.source),indent=2))
