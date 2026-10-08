"""Check saved continue destinations for all 31 homes and both player genders.
This checks the native destination helper and flash, not 62 credit sequences.
"""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source',type=Path,required=True)
parser.add_argument('--library',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
options=parser.parse_args()
sys.argv=[sys.argv[0],'--source',str(options.source),'--library',str(options.library),'--output',str(options.output)]
bootstrap=(ROOT/'tools/hoenn/validate_abilities.py').read_text().split('\nability_field,')[0]
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_abilities.py'),'exec'))
homes=json.loads((source/'.journey-birth').read_text())['homes']
map_names={json.loads(p.read_text())['id']:p.parent.name for p in (source/'data/maps').glob('*/map.json')}
def data():return bytes(lib.read8(save()+12+i) for i in range(8))
flags_before=bytes(lib.read8(save()+4720+i) for i in range((0x1B3F+8)//8))
cases=[]
for gender in [0,1]:
 lib.write8(lib.read32(s['gSaveBlock2Ptr'])+abi[32],gender) # ABI's playerGender offset is stable.
 for home in homes:
  native('VarSet',0x40F7,home['index'])
  assert native('JourneyFamilySetContinueWarp')==1
  expected='LittlerootTown_MaysHouse_2F' if home['index']==17 and gender==1 else map_names[home['bedroom_map']]
  g,n=map_id(expected)
  assert data()==bytes([g,n,255,0,6,0,6,0]),(home['city'],gender,data(),expected)
  assert bytes(lib.read8(save()+4720+i) for i in range(len(flags_before)))==flags_before
  assert native('TrySavingData',0,max_frames=6000)==1
  for i in range(8):lib.write8(save()+12+i,0)
  assert native('LoadGameSave',0,max_frames=6000)==1
  step(30)
  assert data()==bytes([g,n,255,0,6,0,6,0])
  assert native('VarGet',0x40F7)==home['index']
  cases.append(dict(home=home['city'],index=home['index'],gender=gender,map=expected,destination=list(data()),native_flash_save_reload=True))
 for invalid in (0,32,65535):
  native('VarSet',0x40F7,invalid)
  before=data()
  assert native('JourneyFamilySetContinueWarp')==0
  assert data()==before
 print('Home resume destinations passed for gender',gender,flush=True)
lib.stop()
result=dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),cases=cases,
            invalid_home_leaves_destination_unchanged=True,flags_unchanged=True,native_flash_save_reload=True,
            full_credit_sequences=False)
(args.output/'home-resume.json').write_text(json.dumps(result,indent=2)+'\n')
print('All',len(cases),'native home/gender destinations passed',flush=True)
