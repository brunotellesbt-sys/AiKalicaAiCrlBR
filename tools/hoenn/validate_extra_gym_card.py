"""Executed in the native gym validator context; open all three real badge pages."""
from PIL import Image

def callback():return lib.read32(s['gMain']+4)&~1
press(8);until(lambda:lib.read8(s['sNumStartMenuActions'])>0);step(80)
menu=[lib.read8(s['sCurrentStartMenuActions']+i) for i in range(lib.read8(s['sNumStartMenuActions']))]
index=next(i for i,v in enumerate(menu) if lib.read32(s['sStartMenuItems']+v*8+4)&~1==s['StartMenuPlayerNameCallback'])
for _ in range(12):
    pos=lib.read8(s['sStartMenuCursorPos'])
    if pos==index:break
    press(128 if pos<index else 64)
press(1);until(lambda:callback()==s['CB2_TrainerCard']);step(220)
# Screen snapshots include the actual badge glyphs and dynamic 24/24 total.
picture('trainer-card-first')
press(256);step(90);picture('trainer-card-second')
press(256);step(90);picture('trainer-card-third')
press(256);step(90);picture('trainer-card-restored')
# Compare the stable page caption and counts. Badge sparkles and the play
# clock animate independently, so their pixels cannot identify a page.
def band(n):return Image.open(args.output/(n+'.png')).convert('RGB').crop((20,136,232,148)).tobytes()
assert len({band('trainer-card-'+n) for n in ['first','second','third']})==3
assert band('trainer-card-first')==band('trainer-card-restored')
press(512);step(90);picture('trainer-card-left');assert band('trainer-card-left')==band('trainer-card-third')
press(4);step(90);picture('trainer-card-select');assert band('trainer-card-select')==band('trainer-card-first')
press(2);until(lambda:callback()==s['CB2_Overworld']);step(60)
