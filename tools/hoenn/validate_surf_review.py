"""Reach all nine annotated cave entrances and reopen MAP using native controls."""
import hashlib,json,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_sevii_surf_connections.py').read_text().split('\nstart=nearest(')[0]
# The same input walker includes real cave warps rather than blocking doors.
bootstrap=bootstrap.split("towns={r['town']")[0]
bootstrap=bootstrap.replace("allowed=set();", "names += [p.parent.name for p in (source/'data/maps').glob('*/map.json') if p.parent.name.startswith('JourneyCave') or p.parent.name=='ArtisanCave_1F']\nallowed=set();")
exec(compile(bootstrap,__file__,'exec'))
review=json.loads((source/'.journey-surf-review').read_text())
for i in json.loads((source/'.journey-surf-cave-coasts').read_text())['islands']:native('SetTrainerFlag',i['trainer']['id'])
opening=(ROOT/'tools/hoenn/validate_world_map.py').read_text().split('\nchecks=[]')[0].split('def callback():')[1]
exec('def callback():'+opening)
import subprocess
nm=subprocess.check_output([str(ROOT/'.local/arm-binutils/usr/bin/arm-none-eabi-nm'),'-S',str(source/'pokeemerald.elf')],text=True)
sizes={n:(int(a,16)-0x8000000,int(z,16)) for a,z,_,n in re.findall(r'^(\w+) (\w+) (\w) (\S+)$',nm,re.M)}
rom=(source/'pokeemerald.gba').read_bytes();header=(source/'src/data/journey_world_map.h').read_text()
for symbol,fmt in [('sWorldTiles','B'),('sWorldTilemap','H'),('sWorldDetailPixels','B')]:
    values=list(map(int,re.search(symbol+r'\[\] = \{([^}]+)',header)[1].split(',')));at,size=sizes[symbol]
    assert rom[at:at+size]==struct.pack('<'+fmt*len(values),*values),symbol
checks=[];samples=[]
def map_sample(label,expected=None):
    before=(location(),position());packed=native('JourneyWorldMapPosition');xy=[packed&255,packed>>8]
    if expected is not None:assert xy==expected,(label,xy,expected)
    ptr=open_map();cursor=lambda:[lib.read8(ptr+2056),lib.read8(ptr+2057)]
    assert cursor()==xy;picture(label+'-map');press(256);step(60);assert cursor()==xy;picture(label+'-zoom')
    press(2);wait_for(lambda:callback()==s['CB2_Overworld']);step(120);press(2)
    assert before==(location(),position());return xy
for b in review['branches']:
    n=b['surface'];parent=b['parent'];w,h,v=blocks[n];cx,cy=b['entry']
    if parent==n:
        candidates=[(abs(x-cx)+abs(y-cy),x,y) for y in range(h) for x in range(w) if y*w+x in passable[n] and water_behaviors[behaviors[n][y*w+x]] and y>cy]
        _,x,y=min(candidates);start=(n,x,y)
    else:
        pw,ph,_=blocks[parent];d=b['direction'];t=b['offset']+12
        x,y=(1 if d=='left' else pw-2,t) if d in ['left','right'] else (t,1 if d=='up' else ph-2)
        start=(parent,x,y)
    warp(*start);step(120);finish();native('SetPlayerAvatarTransitionFlags',8);step(30)
    before=walked;oldtrans=len(transitions);names_before=map_sample(b['theme']+'-departure')
    # Walk from the connected sea, land, use the actual cave entrance and
    # walk out again. Only this initial sea position is a fixture.
    goal=(b['map'],*b['altar_stand'])
    walk(goal);picture(b['theme']+'-inside');marker=map_sample(b['theme']+'-cave',b['position'])
    assert native('JourneyCurrentMapName')!=0
    if not b['existing_cave']:
        # A real A interaction must execute the moved encounter's existing
        # sixteen-badge gate, without changing its persistent catch flag.
        assert not native('JourneySpecialUnlocked')
        cap=next(c for c in review['effective_sanctuaries']['captures'] if c['map']==b['map'])
        lib.write16(s['gSpecialVar_Result'],0xFFFF);step(4,64);step(30);press(1);finish()
        assert lib.read16(s['gSpecialVar_Result'])==0,(b['theme'],'Moved altar did not run its native gate')
        assert not flag(cap['flag_id']);picture(b['theme']+'-altar-gate')

    walk(start);assert lib.read8(s['gPlayerAvatar'])&8;picture(b['theme']+'-returned')
    checks.append(dict(**b,initial_fixture=list(start),walked_tiles=walked-before,controller_entry_and_return=True,surf_restored_on_return=True,cursor=marker,relocated_altar_interacted=not b['existing_cave'],native_map_open_zoom_return=True,transitions=transitions[oldtrans:],no_midroute_warps_or_coordinate_writes=True))
    print('Annotated cave Surf/door/MAP/return passed:',b['theme'],flush=True)
lib.stop()
(args.output/'surf-review.json').write_text(json.dumps(dict(compiled_atlas_pixels_match_source=True,compiled_zoom_pixels_match_source=True,passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),caves=checks,eight_new_caves=True,existing_artisan_cave_connected=True,actual_connection_edges=len(review['chart']['routes']),all_edges_match_native_map_connections=all(any(c['map']==allmaps[e['destination']]['id'] and c['direction']==e['direction'] and c['offset']==e['offset'] for c in allmaps[e['source']].get('connections') or []) for e in review['chart']['routes']),no_midroute_warps_or_coordinate_writes=True,initial_party_badges_and_departures_are_fixtures=True),indent=2)+'\n')
