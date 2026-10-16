"""Check Mossdeep's exact terminal, both pier rows, physical doors and ferry."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_sootopolis_harbor.py').read_text().split('\n# Disable Sootopolis')[0]
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_sootopolis_harbor.py'),'exec'))
from prepare_mossdeep_harbor import HARBOR,ARRIVAL,TERMINAL
layout=json.loads((source/'.journey-mossdeep-harbor').read_text())
assert layout['terminal']==[3,26,5,5]
assert layout['pier']==[[x,y] for y in (29,30) for x in range(8,12)]
warp('MossdeepCity',5,31);native('SetPlayerAvatarTransitionFlags',1);step(30)
walk_to(8,31);walk_to(8,30);walk_to(11,30);walk_to(11,29);walk_to(8,29);walk_to(8,30);walk_to(8,31);walk_to(5,31)
assert not lib.read8(s['gPlayerAvatar'])&8
picture('Mossdeep-pier-walked')
for x,y in layout['outside_hull']:
 assert native('MapGridGetCollisionAt',x+7,y+7)!=0
 assert native('MetatileBehavior_IsSurfableWaterOrUnderwater',native('MapGridGetMetatileBehaviorAt',x+7,y+7))
change_map(64,HARBOR);picture('Mossdeep-interior-entered');walk_to(*ARRIVAL)
room=json.loads((source/f'data/maps/{HARBOR}/map.json').read_text());assert len(room['object_events'])==2
for x,y in layout['inside_hull']:
 assert native('MapGridGetCollisionAt',x+7,y+7)!=0
 assert native('MetatileBehavior_IsSurfableWaterOrUnderwater',native('MapGridGetMetatileBehaviorAt',x+7,y+7))
talk_up();choose(0);choose(2);trips=[voyage('JourneyPalletHarbor',ARRIVAL)]
talk_up();choose(1);choose(1);choose(2);trips.append(voyage(HARBOR,ARRIVAL))
picture('Mossdeep-network-return')
walk_to(11,13);change_map(128,'MossdeepCity');assert position()==(5,31)
walk_to(8,31);walk_to(8,30);walk_to(11,30);picture('Mossdeep-return-to-pier')
old=json.loads((source/'data/maps/JourneyMossdeepSailorsLodge/map.json').read_text());exit=old['warp_events'][0]
warp('JourneyMossdeepSailorsLodge',exit['x'],exit['y']-1);change_map(128,'MossdeepCity');assert position()==(5,31)
picture('Mossdeep-legacy-exit')
lib.stop()
report=dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),terminal=list(TERMINAL),pier=layout['pier'],controller_entry_and_exit=True,both_pier_rows_walked_without_surf=True,outside_boat_over_water=True,inside_ship_over_water=True,legacy_exit_preserved=True,trips=trips,initial_story_state_and_position_are_fixtures=True,full_campaign_playthrough=False)
(args.output/'mossdeep-harbor.json').write_text(json.dumps(report,indent=2)+'\n')
print('Mossdeep: both pier rows, doors, ship hulls, Pallet roundtrip and legacy exit passed.')
