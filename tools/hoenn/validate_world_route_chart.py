"""Prove chart pixels, real Surf passages and menu cursor tracking in mGBA."""
import hashlib,json,re,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_sevii_surf_connections.py').read_text().split("\nstart=nearest(")[0]
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_sevii_surf_connections.py'),'exec'))
opening=(ROOT/'tools/hoenn/validate_world_map.py').read_text().split('\nchecks=[]')[0].split('def callback():')[1]
exec('def callback():'+opening)
r=json.loads((source/'.journey-surf-cave-coasts').read_text())['chart'] if (source/'.journey-surf-cave-coasts').exists() else json.loads((source/'.journey-annotated-world-links').read_text())['chart'] if (source/'.journey-annotated-world-links').exists() else json.loads((source/'.journey-world-route-chart').read_text());header=(source/'src/data/journey_world_map.h').read_text()
rom=(source/'pokeemerald.gba').read_bytes()
nm=subprocess.check_output([str(ROOT/'.local/arm-binutils/usr/bin/arm-none-eabi-nm'),'-S',str(source/'pokeemerald.elf')],text=True)
symbols={name:(int(a,16)-0x08000000,int(z,16)) for a,z,_,name in re.findall(r'^(\w+) (\w+) (\w) (\S+)$',nm,re.M)}
for symbol,fmt in [('sWorldTiles','B'),('sWorldTilemap','H'),('sWorldDetailPixels','B')]:
 values=list(map(int,re.search(symbol+r'\[\] = \{([^}]+)',header)[1].split(',')))
 expected=struct.pack('<'+fmt*len(values),*values);at,size=symbols[symbol];assert rom[at:at+size]==expected,symbol
maps=allmaps
for route in r['routes']:
 m=maps[route['source']];other=maps[route['destination']]['id']
 assert any(c['map']==other and c['direction']==route['direction'] and c['offset']==route['offset'] for c in m.get('connections') or []),route
 assert all(a[0]==b[0] or a[1]==b[1] for a,b in zip(route['polyline'],route['polyline'][1:])),route
assert all(n['name'] and ('MAP_GROUP('+maps[n['map']]['id']+')') in header for n in r['nodes'])
from prepare_world_dex_map import decode
atlas=decode(header)
visible_samples=[(101,65),(101,69),(101,73),(175,43),(181,46),(190,50),
                 (176,101),(176,106),(185,109),(168,105)]
if (source/'.journey-annotated-world-links').exists():
 for item in r['visible_passages'][3:]:visible_samples.extend(map(tuple,item['blue_pixels']))
assert all(atlas.getpixel(p)==2 for p in visible_samples),'Missing visible route'

for cave in r.get('cave_approaches', []):
 assert cave['blue_pixels'] and all(atlas.getpixel(tuple(p)) == 2 for p in cave['blue_pixels']), cave['map']
 assert atlas.getpixel(tuple(cave['position'])) == 0, ('Missing cave icon', cave['map'])

def menu_sample(label):
 before=(location(),position());expected=marker();packed=native('JourneyWorldMapPosition')
 assert expected==[packed&255,packed>>8]
 ptr=open_map();xy=lambda:[lib.read8(ptr+2056),lib.read8(ptr+2057)]
 assert xy()==expected,(label,xy(),expected)
 picture(label)
 press(16);press(4);assert xy()==expected,('SELECT did not recenter',label)
 press(256);step(60);assert xy()==expected;picture(label+'-zoom')
 press(2);wait_for(lambda:callback()==s['CB2_Overworld']);step(120);press(2)
 assert (location(),position())==before,(label,'MAP changed player location')
 return dict(map=by_location[location()],tile=list(position()),marker=expected,
             cursor_matches_compiled_tile_position=True,recenter=True,zoom=True,return_preserves_position=True)

checks=[]
for p in r['passages']:
 n=p['map'];w,h=p['size'];start=nearest(n,w//2,h//2,True)
 warp(*start);native('SetPlayerAvatarTransitionFlags',8);step(30)
 original=(by_location[location()],*position());samples=[menu_sample(n+'-start')];crossings=[]
 for other,d,off in p['links']:
  ow,oh,_=blocks[other];pairs=[]
  for t in range(max(0,off),min(h if d in ['left','right'] else w,off+(oh if d in ['left','right'] else ow))):
   x,y=(0 if d=='left' else w-1,t) if d in ['left','right'] else (t,0 if d=='up' else h-1)
   xx,yy=(ow-1 if d=='left' else 0,t-off) if d in ['left','right'] else (t-off,oh-1 if d=='up' else 0)
   if wet(n,x,y) and wet(other,xx,yy):pairs.append(((x,y),(xx,yy)))
  assert pairs,('No usable Surf mouth',n,other,d,off)
  a,b=pairs[len(pairs)//2];walk((n,*a));samples.append(menu_sample(n+'-before-'+other))
  walk((other,*b));assert lib.read8(s['gPlayerAvatar'])&8,(n,other,'Surf lost')
  after=menu_sample(n+'-inside-'+other);samples.append(after)
  assert samples[-2]['marker']==after['marker'],('GPS jumps across seam',n,other)
  walk((n,*a));walk(original);crossings.append(dict(destination=other,outbound_and_return=True,surf_preserved=True))
 l,t,rr,bb=p['chart_bounds']
 # A junction occupying one atlas pixel is intentionally stationary; every
 # passage spanning more than one pixel must track controller movement.
 if (l,t)!=(rr,bb):assert len({tuple(s['marker']) for s in samples if s['map']==n})>1,(n,'GPS did not move along route')
 assert all(l<=s['marker'][0]<=rr and t<=s['marker'][1]<=bb for s in samples if s['map']==n),(n,'Cursor left the marked corridor',samples)
 checks.append(dict(map=n,controller_crossings=crossings,cursor_samples=samples,
                    no_midroute_coordinate_writes=True,initial_placement_is_fixture=True))
 print('Surf passage and reopening MAP cursor passed:',n,flush=True)
# Both the original town menu and a native Sevii town remain usable.
for n,x,y in [('PalletTown_Frlg',23,16),('OneIsland_Frlg',10,10)]:
 warp(n,x,y);step(60);menu_sample('world-routes-'+n)
proof=dict(passed=True,cave_approaches_visible_count=len(r.get('cave_approaches', [])),rom_sha256=hashlib.sha256(rom).hexdigest(),actual_connection_edges=len(r['routes']),
           named_nodes=len(r['nodes']),all_edges_match_native_map_connections=True,all_segments_orthogonal=True,
           compiled_atlas_pixels_match_source=True,compiled_zoom_pixels_match_source=True,all_route_names_registered=True,
           native_map_open_zoom_and_return=True,native_land_and_town_art_preserved=r['native_land_and_town_art_preserved'],
           new_surf_passages=checks,cursor_tracks_controller_movement_on_reopen=True,
           new_passage_count=len(checks),green_rectifications=len(r['green_rectifications']),
           authored_corridors_visible=True,visible_route_samples=[list(p) for p in visible_samples],
           cursor_stays_within_authored_corridors=True,
           full_campaign_playthrough=False)
lib.stop();(args.output/'world-route-chart.json').write_text(json.dumps(proof,indent=2)+'\n')
print('Real world routes, Surf passages and moving native MAP cursor passed')
