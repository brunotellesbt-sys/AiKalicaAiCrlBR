"""Record the real pre-repair walking-water regression as a legacy battery.

This diagnostic is intentionally valid only on the faulty parent ROM: the
fixed version must refuse the controller step. Travel/party/progress are
initial fixtures; the incorrect water entry itself is reproduced by input.
"""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source',type=Path,required=True)
parser.add_argument('--library',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
a=parser.parse_args()
path=ROOT/'tools/hoenn/validate_integrated_piers.py'
code=path.read_text().split('\nchecks = []\ntry:')[0]
sys.argv=[sys.argv[0],'--source',str(a.source),'--library',str(a.library),'--output',str(a.output)]
ns={'__file__':str(path),'__name__':'coastal_transition_regression'}
exec(compile(code,str(path),'exec'),ns)
lib,native,step=(ns[k]for k in('lib','native','step'))
try:
    native('DisableWildEncounters',1)
    ns['warp']('OneIsland_TreasureBeach_Frlg',20,6)
    native('SetPlayerAvatarTransitionFlags',1);step(90)
    initial=ns['assert_foot']()
    assert native('MapGridGetElevationAt',28,13)==0
    step(24,16);step(24)
    transition=ns['player_state']()
    assert transition['tile']==[21,6] and transition['elevation']==3 and not transition['surfing']
    step(24,128);step(90)
    broken=ns['player_state']()
    assert broken['tile']==[21,7] and broken['elevation']==1 and not broken['surfing']
    ns['picture']('parent-walking-on-water')
    assert native('TrySavingData',0,max_frames=6000)==1
    destination=a.output/'legacy-walking-water.sav'
    lib.export_save.argtypes=[ctypes.c_char_p];lib.export_save.restype=ctypes.c_int
    assert lib.export_save(str(destination.resolve()).encode())
    assert destination.stat().st_size==131072
    report=dict(kind='coastal-transition-parent-regression',passed=True,
                rom_sha256=hashlib.sha256((a.source/'pokeemerald.gba').read_bytes()).hexdigest(),
                elf_sha256=hashlib.sha256((a.source/'pokeemerald.elf').read_bytes()).hexdigest(),
                initial=initial,transition=transition,broken=broken,
                walking_water_reproduced_by_controller=True,
                no_midtrip_coordinate_elevation_or_avatar_writes=True,
                initial_placement_party_and_progress_are_fixtures=True,
                battery=destination.name,battery_sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),
                map_id=list(ns['location']()),tile=list(ns['position']()))
    (a.output/'legacy-walking-water.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
finally:
    lib.stop()
