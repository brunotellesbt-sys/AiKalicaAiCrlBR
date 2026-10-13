"""Resolve habitat records to the integrated atlas, including Sevii interiors."""
import json
import re
from pathlib import Path
from PIL import Image
from prepare_world_dex_map import PAT, ROOT


def compile_locations(source, headers):
    source = Path(source)
    maps = {p.parent.name: json.loads(p.read_text()) for p in (source / 'data/maps').glob('*/map.json')}
    byid = {m['id']: n for n, m in maps.items()}
    header = (source / 'src/data/journey_world_map.h').read_text()
    coords = {byid[m[1]]: (int(m[3]), int(m[4])) for m in re.finditer(PAT, header)}
    sections = json.loads((source / 'src/data/region_map/region_map_sections.json').read_text())['map_sections']
    bysec = {s['id']: s for s in sections}
    section_points = {}
    for m in re.finditer(PAT, header):
        section_points.setdefault(m[2], (int(m[3]), int(m[4])))
    panels = json.loads((source / '.journey-coastal-world-map').read_text())['panels']
    known = {p['id']: p['panel'] for p in json.loads((ROOT / 'web/world-layout.json').read_text())['points'] if p['panel'] in panels}
    indices = {row['id']: i for i, row in enumerate(sections)}
    regions = (source / 'src/regions.c').read_text()
    for key, panel in [('SEVII123', 'sevii_123'), ('SEVII45', 'sevii_45'), ('SEVII67', 'sevii_67')]:
        block = re.search(r'\[KANTO_SUBREGION_' + key + r'\]\s*=\s*\{(.*?)\}', regions, re.S)[1]
        for sec in re.findall(r'MAPSEC_\w+', block):
            if sec != 'MAPSEC_NONE':
                known[sec] = panel

    def location(name):
        if name in coords:
            return coords[name]
        m = maps[name]
        for c in m.get('connections') or []:
            if c['direction'] == 'emerge' and c['map'] in byid:
                return location(byid[c['map']])
        sec = m['region_map_section']
        if sec in section_points:
            return section_points[sec]
        d = bysec[sec]
        panel = known.get(sec, 'hoenn' if indices[sec] < indices['MAPSEC_PALLET_TOWN'] else 'kanto')
        x, y, w, h = panels[panel]
        sw, sh = Image.open(ROOT / 'web/atlas' / (panel + '.png')).size
        return (max(4, min(219, round(x + (d['x'] + d['width'] / 2) * 8 * w / sw))),
                max(4, min(107, round(y + (d['y'] + d['height'] / 2) * 8 * h / sh))))

    records = {}
    for cap, habitat in headers.items():
        for ident, members in re.findall(r'\{(MAP_\w+),\s*\d+,\s*\{([^}]+)\}\}', habitat):
            xy = location(byid[ident])
            for species in re.findall(r'SPECIES_\w+', members):
                records.setdefault((species, xy, cap), (ident, False))
    captures = json.loads((source / '.journey-sanctuaries').read_text())['captures']
    captures += json.loads((source / '.journey-paradox-caves').read_text())['paradox_captures']
    for c in captures:
        records[(c['species'], location(c['map']), 0)] = (maps[c['map']]['id'], True)
    body = 'struct JourneyWorldDexLocation {u16 species,map;u8 x,y,fixed,cap;};\nstatic const struct JourneyWorldDexLocation sWorldDexLocations[]={\n'
    for (species, (x, y), cap), (ident, fixed) in sorted(records.items()):
        body += f'{{{species},{ident},{x},{y},{int(fixed)},{cap}}},\n'
    return body + '};\n', dict(records=len(records), per_generation={cap: sum(k[2] == cap for k in records) for cap in headers})
