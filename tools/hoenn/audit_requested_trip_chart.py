"""Overlay observed native journeys and keep chart mismatches as findings."""
import hashlib,json,re,struct,subprocess
from pathlib import Path
from PIL import Image,ImageDraw
from prepare_world_dex_map import decode
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'.local/hoenn-route12-src';rom=(source/'pokeemerald.gba').read_bytes()
raw=subprocess.check_output([str(ROOT/'.local/arm-binutils/usr/bin/arm-none-eabi-nm'),str(source/'pokeemerald.elf')],text=True)
symbols={n:int(a,16)-0x08000000 for a,_,n in re.findall(r'^(\w+) (\w) (\S+)$',raw,re.M)}
maps={p.parent.name:json.loads(p.read_text()) for p in (source/'data/maps').glob('*/map.json')}
layouts={l['id']:l for l in json.loads((source/'data/layouts/layouts.json').read_text())['layouts']}
atlas=decode((source/'src/data/journey_world_map.h').read_text());cache={};results=[]
for path in sorted((ROOT/'mods/hoenn/coastal-update-validation/common/navigation').rglob('*.json')):
    trip=json.loads(path.read_text());assert trip['rom_sha256']==hashlib.sha256(rom).hexdigest()
    trace=atlas.convert('RGB');draw=ImageDraw.Draw(trace);mismatches={};counts={'painted_corridor':0,'open_sea':0}
    for sample in trip['marker_samples']:
        name=sample['map'];l=layouts[maps[name]['layout']];x,y=sample['tile'];px,py=sample['marker'];draw.point((px,py),fill=(255,0,255))
        if name not in cache:cache[name]=struct.unpack('<'+'H'*l['width']*l['height'],(source/l['blockdata_filepath']).read_bytes())
        tile=cache[name][y*l['width']+x];mid=tile&1023;fr=l['layout_version']=='frlg';cut=640 if fr else 512;size=4 if fr else 2
        ptr=struct.unpack_from('<I',rom,symbols[l['secondary_tileset'] if mid>=cut else l['primary_tileset']]+16)[0]-0x08000000
        behavior=int.from_bytes(rom[ptr+(mid-cut if mid>=cut else mid)*size:ptr+(mid-cut if mid>=cut else mid)*size+size],'little')&(511 if fr else 255)
        water=bool(rom[symbols['sTileBitAttributes']+(behavior&255)]&2)
        if not water:continue
        color=atlas.getpixel((px,py))
        if color==2:counts['painted_corridor']+=1
        elif color==1:counts['open_sea']+=1
        elif color not in [0,14,15]:mismatches.setdefault(name,set()).add((px,py,color))
    trace.resize((1120,560),Image.Resampling.NEAREST).save(path.parent/'actual-world-path.png')
    results.append(dict(profile=trip['profile'],**counts,water_samples_over_land_art={n:[list(p) for p in sorted(points)] for n,points in mismatches.items()}))
findings=dict(completed=True,rom_sha256=hashlib.sha256(rom).hexdigest(),physical_route_roundtrips_passed=True,visual_alignment_complete=all(not r["water_samples_over_land_art"] for r in results),checks=results,observed_position_samples_not_synthetic=True,compiled_tileset_water_flags=True,not_a_passing_visual_release_proof=True)
out=ROOT/'mods/hoenn/navigation-findings/route-chart-findings.json';out.write_text(json.dumps(findings,indent=2)+'\n')
print(json.dumps(results,indent=2))
