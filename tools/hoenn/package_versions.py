"""Export four variants by patching only a verified, compiled build-rules record."""
import argparse,hashlib,json,re,shutil,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sync_roms(output,rows):
 """Keep the requested GitHub download folder aligned with the release."""
 output=Path(output)
 if output.resolve()!=(ROOT/'mods/hoenn/versions').resolve():return
 destination=ROOT/'roms';destination.mkdir(exist_ok=True)
 for row in rows:
  pending=destination/(row['file']+'.tmp')
  shutil.copyfile(output/row['file'],pending)
  assert hashlib.sha256(pending.read_bytes()).hexdigest()==row['sha256']
  pending.replace(destination/row['file'])
 (destination/'SHA256SUMS').write_bytes((output/'SHA256SUMS').read_bytes())

def package(source,output):
 source=Path(source);output=Path(output);output.mkdir(parents=True,exist_ok=True);base=(source/'pokeemerald.gba').read_bytes()
 nm=subprocess.check_output([str(ROOT/'.local/arm-binutils/usr/bin/arm-none-eabi-nm'),'-S',str(source/'pokeemerald.elf')],text=True)
 m=re.search(r'^(\w+) (\w+) R gJourneyBuildRules$',nm,re.M);assert m,'Build rules must be a separate ROM record'
 at,size=int(m[1],16)-0x08000000,int(m[2],16);assert size==4 and base[at:at+4]==struct.pack('<HBB',1025,1,0)
 rows=[]
 for generation,maxdex in [(4,493),(9,1025)]:
  for difficulty,perfect in [('Normal',0),('Hard',1)]:
   raw=bytearray(base);raw[at:at+4]=struct.pack('<HBB',maxdex,perfect,0)
   title=f'JOURNEY G{generation} {difficulty[0]}'.encode().ljust(12,b' ')[:12];raw[0xA0:0xAC]=title;raw[0xBD]=(-sum(raw[0xA0:0xBD])-0x19)&255
   name=f'Pokemon-Journey-Gen1-{generation}-{difficulty}.gba';(output/name).write_bytes(raw)
   changes=[i for i,(a,b) in enumerate(zip(base,raw)) if a!=b];assert all(at<=i<at+4 or 0xA0<=i<0xAC or i==0xBD for i in changes)
   rows.append(dict(file=name,max_national=maxdex,perfect_trainer_ivs=bool(perfect),important_opponents_only=True,evs=510,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),patched_byte_offsets=changes,requires_new_save=True))
 r=dict(parent_rom_sha256=hashlib.sha256(base).hexdigest(),build_rules_offset=at,
        parent_header_hex=base[0xA0:0xBE].hex(),parent_rules_hex=base[at:at+4].hex(),
        variants=rows,all_other_bytes_identical=True,validated=False)
 if (source/'.journey-badge-story').exists():
  from prepare_badge_story import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-coastal-closures').exists():
  from prepare_coastal_closures import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-sevii-integrated-piers').exists():
  from prepare_sevii_integrated_piers import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-dewford-coast-safety').exists():
  from prepare_dewford_coast_safety import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-extra-gyms').exists():
  from prepare_extra_gyms import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-ever-grande-market').exists():
  from prepare_ever_grande_market import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-dewford-competitive-shop').exists():
  from prepare_dewford_competitive_shop import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-surf-review').exists():
  from prepare_surf_review import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-surf-cave-coasts').exists():
  from prepare_surf_cave_coasts import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-annotated-world-links').exists():
  from prepare_annotated_world_links import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-dewford-island-harbor').exists():
  from prepare_dewford_island_harbor import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-mossdeep-harbor').exists():
  from prepare_mossdeep_harbor import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-sevii-harbors').exists():
  from prepare_sevii_harbors import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-three-harbor-terminals').exists():
  from prepare_three_harbor_terminals import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-fuchsia-harbor').exists():
  from prepare_fuchsia_harbor import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-lavender-harbor').exists():
  from prepare_lavender_harbor import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-world-route-chart').exists():
  from prepare_world_route_chart import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-sevii-arrival-layout').exists():
  from prepare_sevii_arrival_layout import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-sevii-surf-embarkation').exists():
  from prepare_sevii_surf_embarkation import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-sevii-coast-camera').exists():
  from prepare_sevii_coast_camera import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-sevii-surf-connections').exists():
  from prepare_sevii_surf_connections import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-pallet-harbor').exists():
  from prepare_pallet_harbor import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-sootopolis-harbor').exists():
  from prepare_sootopolis_harbor import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-navigated-sea-atlas').exists():
  from prepare_navigated_sea_atlas import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-complete-marine-atlas').exists():
  from prepare_complete_marine_atlas import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-offscreen-rival-entrances').exists():
  from prepare_offscreen_rival_entrances import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-diglett-scout-battles').exists():
  from prepare_diglett_scout_battles import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-native-coastal-fragments').exists():
  from prepare_native_coastal_fragments import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-diglett-galactic-scouts').exists():
  from prepare_diglett_galactic_scouts import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-close-vertical-boats').exists():
  from prepare_close_vertical_boats import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-port-orientation-finish').exists():
  from prepare_port_orientation_finish import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-final-port-alignment').exists():
  from prepare_final_port_alignment import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-port-houses-and-ships').exists():
  from prepare_port_houses_and_ships import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-cinnabar-shore-polish').exists():
  from prepare_cinnabar_shore_polish import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-continuous-atlas-marker').exists():
  from prepare_continuous_atlas_marker import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-final-moorings').exists():
  from prepare_final_moorings import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-atlas-route-tracking').exists():
  from prepare_atlas_route_tracking import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-pwt-obedience').exists():
  from prepare_pwt_obedience import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-workshop-graphics-rules').exists():
  from prepare_workshop_graphics_rules import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-pwt-score-retention').exists():
  from prepare_pwt_score_retention import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-special-encounter-field-rules').exists():
  from prepare_special_encounter_field_rules import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-special-encounter-workshop').exists():
  from prepare_special_encounter_workshop import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-form-move-legality').exists():
  from prepare_form_move_legality import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-nonlevel-moves').exists():
  from prepare_nonlevel_moves import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-battle-interactions').exists():
  from prepare_battle_interactions import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-move-history-rules').exists():
  from prepare_move_history_rules import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-pwt-encore-guard').exists():
  from prepare_pwt_encore_guard import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 elif (source/'.journey-pwt-entrance-wait').exists():
  from prepare_pwt_entrance_wait import PRIOR,LAYER
  r['integration_layers']=PRIOR+[LAYER]
 (output/'versions.json').write_text(json.dumps(r,indent=2)+'\n');(output/'SHA256SUMS').write_text(''.join(row['sha256']+'  '+row['file']+'\n' for row in rows))
 sync_roms(output,rows)
 return r
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(package(a.source,a.output),indent=2))
