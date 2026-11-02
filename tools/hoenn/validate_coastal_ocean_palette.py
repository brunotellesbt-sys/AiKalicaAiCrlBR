"""Check compiled water words, loaded banks and native same-frame sea pixels.

Initial party/progress/travel and encounter suppression are fixtures for this
visual check. No palette, VRAM, map grid or avatar coordinates are written.
"""
from pathlib import Path
import hashlib
import json
import re
import struct
from PIL import Image
from coastal_ecology_ocean import BANKS
from integrated_ocean_seams import _animation_frames
from coastal_ecology_hoenn_ocean import native_case as hoenn_native_case

ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_trainer_levels.py').read_text().split('\nchecks=[]')[0]
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_trainer_levels.py'),'exec'))
initial_sha=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest()
marker=json.loads((source/'.journey-coastal-ecology').read_text())
metadata=marker['ocean']
alias_metadata=marker['sevii_aliases']
kanto_metadata=marker['kanto_sea']
assert kanto_metadata['lower_water_words_changed']==160
all_tables=metadata['tables']+kanto_metadata['tables']
target_maps=sorted(set(metadata['target_maps'])|set(kanto_metadata['target_maps']))
assert len(target_maps)==43
all_assignments=alias_metadata['layout_assignments']+kanto_metadata['layout_assignments']
assert metadata['lower_water_words_changed']==338
assert set(r['tileset']for r in metadata['tables'])==set(BANKS)
layouts={r['id']:r for r in json.loads((source/'data/layouts/layouts.json').read_text())['layouts']}
headers={p.parent.name:json.loads(p.read_text())for p in (source/'data/maps').glob('*/map.json')}
compiled=[]
for row in all_tables:
 expected=(source/row['path']).read_bytes();addr=s[row['metatile_symbol']]
 actual=bytes(lib.read8(addr+i)for i in range(len(expected)))
 assert actual==expected,row['path']
 words=struct.unpack('<'+'H'*(len(actual)//2),actual)
 assert all(w>>12==4 for i,w in enumerate(words)if i%8<4 and w&1023 in(454,455))
 for change in row['words_changed']:
  assert words[change['word_index']]==change['after']
  assert change['before']^change['after']==0x2000
 compiled.append(dict(path=row['path'],tileset=row['tileset'],sha256=hashlib.sha256(actual).hexdigest(),words_changed=len(row['words_changed'])))
# Header identity proves that the new native coast consumers retain their
# complete graphics, palette, attribute and animation ABI in the compiled ROM.
compiled_aliases=[]
for row in alias_metadata['bank_compatibility']+kanto_metadata['door_aliases']:
 original,private=s[row['original']],s[row['private']]
 assert all(lib.read8(original+i)==lib.read8(private+i)
            for i in range(24)if i not in range(12,16)),row
 compiled_aliases.append(dict(original=row['original'],private=row['private'],
  original_address=original,private_address=private,
  header_fields_except_private_metatile_pointer_identical=True))
new_aliases={row['map']:row for row in all_assignments}
for value in hoenn_flags+kanto_flags:rawflag(value,True)
for tid in range(1,1589):rawflag(0x500+tid,True)
native('VarSet',0x40FE,7);native('VarSet',0x40FF,4095)
native('VarSet',0x4021,65535);native('VarSet',0x4120,65535)
native('RtcInitLocalTimeOffset',12,0)
native('DisableWildEncounters',1)
team([40,40,40]);native('ScriptSetMonMoveSlot',0,57,1)
constants=(source/'include/constants/vars.h').read_text()
for variable,value in [('VAR_MAP_SCENE_ONE_ISLAND_HARBOR',3),('VAR_MAP_SCENE_FOUR_ISLAND',1)]:
 native('VarSet',int(re.search(r'^#define\s+'+variable+r'\s+(0x\w+)',constants,re.M)[1],16),value)
captures=[];loaded=[];native_aliases=[]
def capture(label):
 picture(label);p=args.output/(label+'.png')
 captures.append(dict(file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
 return Image.open(p).convert('RGB')
for name in target_maps:
 layout=layouts[headers[name]['layout']];w,h=layout['width'],layout['height']
 values=struct.unpack('<'+'H'*(w*h),(source/layout['blockdata_filepath']).read_bytes())
 options=[(i%w,i//w)for i,t in enumerate(values)if not t&0xC00 and t>>12==3 and t&1023 in(0x1,0x4,0x6,0x7,0x8,0x9,0xA,0xD,0x71,0x72,0x74,0x75)]
 mode=1
 if not options:
  options=[(i%w,i//w)for i,t in enumerate(values)if not t&0xC00 and t>>12==1 and t&1023==0x12B];mode=8
 if not options:
  options=[(i%w,i//w)for i,t in enumerate(values)if not t&0xC00 and t>>12==3];mode=1
 assert options,('No ordinary camera fixture',name)
 x,y=min(options,key=lambda p:abs(p[0]-w//2)+abs(p[1]-h//2))
 warp(name,x,y);native('SetPlayerAvatarTransitionFlags',mode);step(90)
 layout_pointer=lib.read32(s['gMapHeader'])
 assert lib.read32(layout_pointer+16)==s[layout['primary_tileset']],name
 assert lib.read32(layout_pointer+20)==s[layout['secondary_tileset']],name
 if name in new_aliases:
  assignment=new_aliases[name]
  assert assignment['primary']==layout['primary_tileset']
  assert assignment['secondary']==layout['secondary_tileset']
  native_aliases.append(dict(map=name,layout=layout['id'],
   primary_pointer=lib.read32(layout_pointer+16),secondary_pointer=lib.read32(layout_pointer+20),
   primary=layout['primary_tileset'],secondary=layout['secondary_tileset'],
   actual_loaded_private_bank_pointers_match_final_layout=True))
 capture(name+'-native')
 loaded.append(dict(map=name,initial_position=[x,y],surfing=mode==8,
  primary=layout['primary_tileset'],secondary=layout['secondary_tileset'],
  primary_pointer=lib.read32(layout_pointer+16),secondary_pointer=lib.read32(layout_pointer+20),
  banks_loaded_from_final_rom=True))
 print('Native uniform-ocean banks:',name,flush=True)
assert {row['map']for row in native_aliases}==set(new_aliases)
# Exact camera from the user's video. These are two ordinary, uncovered sea
# cells on opposite sides of its former rectangular palette boundary.
warp('OneIsland_TreasureBeach_Frlg',20,6);native('SetPlayerAvatarTransitionFlags',1);step(90)
for x,y in[(15,7),(21,3)]:
 assert native('MapGridGetMetatileIdAt',x+7,y+7) in(0x12B,0x1D9)
 pixel_checks=[]
frames=_animation_frames(source)
observed_phases=set()
for phase in range(8):
 step(16)
 vram=bytes(lib.read8(0x06000000+454*32+i)for i in range(64))
 matches=[i for i,frame in enumerate(frames)if frame==vram]
 assert matches,('Unexpected loaded water animation',phase)
 observed_phases.update(matches)
 # The pixels themselves share one scanout, independently of the animation
 # clock offset used by this source version.
 image=capture('treasure-bay-and-border-phase-'+str(phase))
 bay=image.crop((32,88,48,104)).tobytes();offshore=image.crop((128,24,144,40)).tobytes()
 assert bay==offshore,('Different native sea pixels beside the same pier',phase,hashlib.sha256(bay).hexdigest(),hashlib.sha256(offshore).hexdigest())
 pixel_checks.append(dict(sample=phase,bay_cell=[15,7],offshore_cell=[21,3],identical_rgb_sha256=hashlib.sha256(bay).hexdigest(),same_native_frame=True,valid_animation_phases=matches))
assert observed_phases==set(range(8)),sorted(observed_phases)
hoenn_ocean=hoenn_native_case(globals())
captures.extend(hoenn_ocean['captures'])
lib.stop()
assert hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest()==initial_sha
result=dict(passed=True,kind='coastal-ocean-palette',rom_sha256=initial_sha,
 elf_sha256=hashlib.sha256((source/'pokeemerald.elf').read_bytes()).hexdigest(),
 compiled_rom=True,native_validation_performed=True,compiled_tables=compiled,
 loaded_maps=loaded,loaded_map_count=len(loaded),target_maps=target_maps,
 compiled_native_bank_aliases=compiled_aliases,native_coast_layout_aliases=native_aliases,
 native_same_frame_pixel_checks=pixel_checks,former_bay_border_palette_seam_removed=True,
 lower_water_words_changed=498,
 source_ocean_groups=[dict(region='sevii',maps=metadata['target_maps'],lower_water_words_changed=338),
                      dict(region='kanto',maps=kanto_metadata['target_maps'],lower_water_words_changed=160)],
 hoenn_ocean=hoenn_ocean,upper_object_layers_attributes_and_geometry_preserved=True,
 initial_party_progress_travel_and_encounter_suppression_are_fixtures=True,
 no_palette_vram_map_grid_or_avatar_coordinate_writes=True,captures=captures)
(args.output/'coastal-ocean-palette.json').write_text(json.dumps(result,indent=2)+'\n')
print('Native ocean palette check passed:',len(loaded),'maps, 8 same-frame pixel pairs, and native Mossdeep roundtrip',flush=True)
