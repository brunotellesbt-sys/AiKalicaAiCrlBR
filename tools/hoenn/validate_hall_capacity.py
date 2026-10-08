"""Exercise the native Hall of Fame rollover at 50 shared teams.
Archive records and championships are fixtures; the native save, Hall of Fame,
credits and Continue perform each append. This does not win another League.
"""
import argparse, hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source',type=Path,required=True)
parser.add_argument('--library',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
configuration=parser.parse_args()
sys.argv=[sys.argv[0],'--source',str(configuration.source),'--library',str(configuration.library),
          '--output',str(configuration.output),'--region','kanto']
program=(ROOT/'tools/hoenn/validate_league_completion.py').read_text()
initialization=program.split("\nentry='IndigoPlateau",1)[0]
exec(compile(initialization,str(ROOT/'tools/hoenn/validate_league_completion.py'),'exec'))
# Shared archive encoding: six 24-byte mons, species bitfield at offset 8.
def read_archive():
 pointer=native('AllocZeroed_',8192,0);assert pointer
 assert lib.read32(s['gHoFSaveBuffer'])==0
 lib.write32(s['gHoFSaveBuffer'],pointer)
 try:
  assert native('LoadGameSave',3,max_frames=6000)==1
  return [bytes(lib.read8(pointer+j*144+i) for i in range(144)) for j in range(50)]
 finally:
  lib.write32(s['gHoFSaveBuffer'],0);native('Free',pointer)
records=[]
for j in range(50):
 mon=(1000+j).to_bytes(4,'little')+(2000+j).to_bytes(4,'little')+(abi[68]<<1).to_bytes(2,'little')+bytes([100])+bytes([0xBB,0xFF])+bytes(10)
 assert len(mon)==23
 records.append((mon+bytes(1))*6)
pointer=native('AllocZeroed_',8192,0);assert pointer
lib.write32(s['gHoFSaveBuffer'],pointer)
for j,record in enumerate(records):
 for i,b in enumerate(record):lib.write8(pointer+j*144+i,b)
assert native('TrySavingData',3,max_frames=6000)==1
lib.write32(s['gHoFSaveBuffer'],0);native('Free',pointer)
assert read_archive()==records
# Both completions already set. The native entry must load the shared archive.
for f in (champion,game_clear,0x1AC2,0x1AB8):raw_flag(f,True)
second_league=True
# Reuse the existing credit/Continue checks without running its five battles.
aftermath='# Follow'+program.split('# Follow',1)[1]
aftermath=aftermath.replace('lib.stop()','').replace('assert not any(raw_get(f) for f in other_flags)','assert all(raw_get(f) for f in other_flags)').replace('and not any(raw_get(f) for f in other_flags)','and all(raw_get(f) for f in other_flags)').replace('other_region_uncompleted=True','other_region_uncompleted=False')
# The existing idle/task helpers live between entry setup and room traversal.
helpers=program.split('def idle():',1)[1].split('warp(entry,',1)[0]
exec(compile('def idle():'+helpers,str(ROOT/'tools/hoenn/validate_league_completion.py'),'exec'))
cases=[]
for region,map_name,function in [('hoenn','Route101','GameClear'),('kanto','Route1_Frlg','EnterHallOfFame')]:
 run_options.region=region;kanto=region=='kanto';wins=[]
 warp(map_name,5,12 if kanto else 10)
 native(function)
 exec(compile(aftermath,str(ROOT/'tools/hoenn/validate_league_completion.py'),'exec'))
 actual=read_archive()
 assert actual[:49]==records[1:], 'Rollover must drop only the oldest team'
 assert all(int.from_bytes(actual[-1][j*24+4:j*24+8],'little')==identity[j] for j in range(6))
 records=actual
 cases.append(dict(region=region,records=50,oldest_only_removed=True,remaining_records_byte_identical=True,
                   new_team_identity_preserved=True,native_credits_and_continue=True,native_flash_reload=True))
 print('Shared Hall of Fame capacity passed:',region,flush=True)
lib.stop()
report=dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
            cases=cases,shared_capacity=50,archive_and_champion_states_are_fixtures=True,
            native_hall_of_fame_append=True,pc_viewer_validated=False,full_campaign_playthrough=False)
(args.output/'hall-capacity.json').write_text(json.dumps(report,indent=2)+'\n')
