"""Capture full gym facades from a real adjacent standing tile, without banners.

Placement, noon and progress are fixtures. No map pixels or camera coordinates
are written. Complete map renders complement the limited GBA camera indoors.
"""
import hashlib,json
from pathlib import Path
from extra_gyms import GYMS
from extra_gym_interiors import plan
ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_trainer_levels.py').read_text().split('\nchecks=[]')[0]
exec(compile(bootstrap,__file__,'exec'))
native('RtcInitLocalTimeOffset',12,0);native('VarSet',0x40FE,7);native('VarSet',0x40FF,4095)
# Suppress approach dialogue only in the presentation fixture. The separate
# function validator clears these flags and tests native six-tile approaches.
for i in range(32):rawflag(0x1009+i,True)
positions=dict(MORTY=[23,11],WHITNEY=[43,23],STEVEN=[7,52],BUGSY=[10,20],CANDICE=[9,19],CLAIR=[8,15],KAREN=[7,16],OAK=[5,7])
checks=[]
for g in GYMS:
    outside_position=positions[g['key']];x,y=outside_position;warp(g['city'],x,y);native('SetPlayerAvatarTransitionFlags',1);step(360)
    assert position()==(x,y) and lib.read8(s['gPlayerAvatar'])&25==1
    assert native('MapGridGetCollisionAt',x+7,y+7)==0,(g['city'],x,y)
    picture(g['key'].lower()+'-outside')
    inside_position=plan(g['key'])['capture'];warp(g['name'],*inside_position);step(360);picture(g['key'].lower()+'-inside')
    for j,student in enumerate(plan(g['key'])['students']):
        x,y=student['position'];dx,dy={'RIGHT':(1,0),'LEFT':(-1,0),'DOWN':(0,1),'UP':(0,-1)}[student['facing']]
        warp(g['name'],x+3*dx,y+3*dy);step(360);picture(g['key'].lower()+'-checkpoint-'+str(j+1))
    checks.append(dict(map=g['city'],inside=g['name'],outside_fixture=outside_position,inside_fixture=inside_position))
lib.stop()
(args.output/'presentation-captures.json').write_text(json.dumps(dict(rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
    native_emulator_frames=True,fixture_positions_and_noon=True,camera_and_map_pixels_not_written=True,
    subordinate_defeated_flags_are_presentation_fixtures=True,
    function_tests_are_separate=True,captures=checks),indent=2)+'\n')
