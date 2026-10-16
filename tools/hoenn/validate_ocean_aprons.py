"""Prove foreign-bank rock limits are visible before crossing and stay animated safely."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_sevii_surf_connections.py').read_text().split('\nstart=nearest(')[0]
exec(compile(bootstrap,__file__,'exec'))
r=json.loads((source/'.journey-surf-review').read_text());checks=[]
def graphics(slots):
    return [bytes(lib.read8(0x06000000+32*t+i) for i in range(32)).hex() for t in slots]
for b in r['branches']:
    if b['surface']==b['parent']:continue
    parent,child=b['parent'],b['surface'];pl=layouts[maps[parent]['layout']];cl=layouts[maps[child]['layout']]
    if pl['layout_version']==cl['layout_version']:continue
    d=b['direction'];assert d in ['down','up'],d
    pw,ph,_=blocks[parent];start=(parent,b['offset']+3,ph-3 if d=='down' else 2)
    warp(*start);native('SetPlayerAvatarTransitionFlags',8);step(60)
    # This tile is still outside the loaded parent rectangle, inside the
    # visible connection apron. It must already display the foreign rock.
    xx,yy=b['offset']+7,ph+7 if d=='down' else 6
    expected=0x243 if pl['layout_version']=='frlg' else 0x1F9
    actual=native('MapGridGetMetatileIdAt',xx,yy);assert actual==expected,(parent,actual,expected)
    assert native('MapGridGetCollisionAt',xx,yy)!=0
    own=next(a['graphics'] for a in r['rock_art'] if a['primary']==pl['primary_tileset']);before=graphics(own);step(256);assert graphics(own)==before
    picture(b['theme']+'-rocks-before-seam')
    walk((child,3,3 if d=='down' else cl['height']-4));assert lib.read8(s['gPlayerAvatar'])&8
    own=next(a['graphics'] for a in r['rock_art'] if a['primary']==cl['primary_tileset']);before=graphics(own);step(256);assert graphics(own)==before
    picture(b['theme']+'-rocks-after-seam');walk(start);assert lib.read8(s['gPlayerAvatar'])&8
    checks.append(dict(parent=parent,child=child,foreign_rock_rendered_before_map_transition=True,apron_collision_blocks_rock=True,rock_graphics_unchanged_over_256_frames_in_both_banks=True,controller_roundtrip=True))
    print('Visible rock apron and animation passed:',parent,child,flush=True)
assert len(checks)==3
lib.stop();(args.output/'ocean-aprons.json').write_text(json.dumps(dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),checks=checks,no_midroute_warps_or_coordinate_writes=True),indent=2)+'\n')
