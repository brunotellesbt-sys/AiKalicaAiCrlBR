"""Cross every outdoor Hoenn/FRLG format seam and compare live ocean palettes."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bootstrap=(ROOT/'tools/hoenn/validate_sevii_surf_connections.py').read_text().split('\nstart=nearest(')[0]
exec(compile(bootstrap,str(ROOT/'tools/hoenn/validate_sevii_surf_connections.py'),'exec'))
for n,valid in passable.items():
    passable[n]={i for i in valid if water_behaviors[behaviors[n][i]] and not blocks[n][2][i]&0xC00
        and (blocks[n][2][i]>>12==1 or blocks[n][2][i]>>12==0 and bridge_behaviors[behaviors[n][i]])}
pairs={}
for n,m in maps.items():
    for c in m.get('connections') or []:
        other=by_id.get(c['map'])
        if c['direction'] not in ['left','right','up','down'] or other not in maps:continue
        if layouts[m['layout']]['layout_version']==layouts[maps[other]['layout']]['layout_version']:continue
        pairs.setdefault(tuple(sorted((n,other))),(n,other,c))
assert len(pairs)==13,len(pairs)

def palette():
    ids=[3,4,5,7]
    return [lib.read16(0x05000000+(64+i)*2) for i in ids]

checks=[]
for pair,(n,other,c) in sorted(pairs.items()):
    w,h,_=blocks[n];ow,oh,_=blocks[other];off=c['offset'];d=c['direction'];choices=[]
    for t in range(max(0,off),min(h if d in ['left','right'] else w,off+(oh if d in ['left','right'] else ow))):
        x,y=(0 if d=='left' else w-1,t) if d in ['left','right'] else (t,0 if d=='up' else h-1)
        xx,yy=(ow-1 if d=='left' else 0,t-off) if d in ['left','right'] else (t-off,oh-1 if d=='up' else 0)
        dx,dy={'left':(1,0),'right':(-1,0),'up':(0,1),'down':(0,-1)}[d]
        if wet(n,x,y) and wet(n,x+dx,y+dy) and wet(other,xx,yy) and wet(other,xx-dx,yy-dy):
            choices.append(((n,x+dx,y+dy),(other,xx-dx,yy-dy)))
    assert choices,('No open surface ocean crossing',pair)
    start,goal=choices[len(choices)//2]
    warp(*start);native('SetPlayerAvatarTransitionFlags',8);step(60)
    before=palette();walk(goal);assert lib.read8(s['gPlayerAvatar'])&8
    after=palette();assert before==after,('Ocean colours jumped',pair,before,after)
    picture(n+'-to-'+other)
    walk(start);assert lib.read8(s['gPlayerAvatar'])&8
    assert palette()==before,(pair,'Ocean changed on return')
    checks.append(dict(maps=list(pair),outbound_and_return=True,surf_preserved=True,colors_identical=True,
                       before_palette=before,after_palette=after,open_border_tiles=len(choices)))
    print('Seam colours and Surf passed:',pair,flush=True)
lib.stop();r=dict(passed=True,rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
    seams=checks,crossings=2*len(checks),all_outdoor_format_seams_covered=True,
    initial_placements_are_independent_fixtures=True,no_midcrossing_warps_or_coordinate_writes=True)
(args.output/'ocean-seams.json').write_text(json.dumps(r,indent=2)+'\n')
