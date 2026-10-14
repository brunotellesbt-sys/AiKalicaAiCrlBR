"""Verify the focused coastal/campaign update without relabeling old PWT runs."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def verify_update(directory,info):
 expected={r['file']:r['sha256'] for r in info['variants']};covered=set();common=set()
 for p in info['proofs']:
  path=Path(p['file']);assert not path.is_absolute() and '..' not in path.parts
  raw=(directory/path).read_bytes();assert hashlib.sha256(raw).hexdigest()==p['sha256'];r=json.loads(raw);assert r['passed'] is True
  sha=info['parent_rom_sha256'] if p['target']=='common' else expected[p['target']]
  if p['kind']=='reproduction':assert r['layers']==info['integration_layers'] and not r['differences']
  else:assert r['rom_sha256']==sha,(p['kind'],'Stale evidence')
  if p['target']=='common':common.add(p['kind'])
  else:covered.add((p['target'],p['kind']))
  if p['kind']=='live-levels':
   assert r['current_party_mean'] and r['ace_offset']==5 and r['ordinary_offset']==[-5,2] and r['leader_offset']==[-1,5]
   assert r['native_generated_parties'] and not r['enemy_levels_written']
   assert {'MossdeepCity_Gym','VermilionCity_Gym_Frlg'}<=set(r['maps'])
  elif p['kind']=='gym-teams':
   assert len(r['checks'])==192 and len({c['leader'] for c in r['checks']})==16
   for c in r['checks']:
    levels=[m['level'] for m in c['mons']];assert levels[-1]==r['reference_party_mean']+5
    assert all(r['reference_party_mean']-1<=v<=r['reference_party_mean']+5 for v in levels)
  elif p['kind']=='coast-connectivity':assert r['all_integrated_surface_seas_reachable'] and r['compiled_collision_and_water_behaviors']
  elif p['kind']=='ports-and-actors':assert r['all_boat_footprints_blocked'] and r['native_controller_access'] and r['crossover_visible_approaches'] and r['cinnabar_complete_rocks_and_resident_off_roof']
  elif p['kind']=='compact-ferry':assert r['native_controller_menus'] and r['native_boat_animation'] and r['arrivals_on_accessible_dry_pier'] and len(r['trips'])==2
  elif p['kind']=='world-map-position':assert r['recenter_uses_real_position'] and r['short_trip_has_no_midroute_fixture_warp']
  elif p['kind']=='special-encounters':assert r['actual_tv_capture_and_form_ui'] and len(r['rotom_changes'])==6
 assert {'reproduction','coast-connectivity','ports-and-actors','world-map-position','live-levels','compact-ferry'}<=common
 assert {(name,kind) for name in expected for kind in ['gym-teams','special-encounters']}<=covered
 assert info['full_campaign_playthrough'] is False and info['historical_validation']['retested_on_current_rom'] is False
 from published_evidence import baseline,evidence_rom,evidence_release
 root,old,_=baseline();assert info['historical_validation']['manifest_sha256']==hashlib.sha256((root/'versions.json').read_bytes()).hexdigest()
 for row in old['variants']:evidence_rom(root,row['file'])
 for p in old['proofs']:
  raw=(root/p['file']).read_bytes();assert hashlib.sha256(raw).hexdigest()==p['sha256'];r=json.loads(raw);assert r['passed']
 return info
