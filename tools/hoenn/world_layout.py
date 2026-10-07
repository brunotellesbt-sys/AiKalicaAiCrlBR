"""Render one square world chart from native coordinates and the ocean graph.

The chart describes the integration candidate, not the released game's save
position or a proof that story progression is finished.
"""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)
PLACEMENT = {
    'kanto': (32, 70, 528, 360),
    'hoenn': (32, 820, 672, 408),
    'sevii_123': (672, 240, 528, 360),
    'sevii_45': (848, 630, 352, 240),
    'sevii_67': (848, 930, 352, 240),
}


def build():
    atlas_path = ROOT / 'web/world-map.json'
    atlas = json.loads(atlas_path.read_text())
    old_panels = {p['id']: p for p in atlas['panels']}
    points = {}
    for p in atlas['points']:
        old = old_panels[p['panel']]
        x, y, w, h = PLACEMENT[p['panel']]
        points[p['id']] = dict(p, x=x + (p['x'] - old['x']) * w / old['width'],
                                y=y + (p['y'] - old['y']) * h / old['height'])
    # Route131 is immediately east of Pacifidlog; Route114 is the western
    # lake. Read the native sections instead of inventing regional positions.
    native = json.loads((ROOT / '.local/emerald-base/src/data/region_map/region_map_sections.json').read_text())
    x, y, w, h = PLACEMENT['hoenn']
    for ident in ['MAPSEC_ROUTE_131', 'MAPSEC_ROUTE_114', 'MAPSEC_ROUTE_115', 'MAPSEC_ROUTE_105']:
        section = next(s for s in native['map_sections'] if s['id'] == ident)
        points[ident] = dict(id=ident, name=section['name'].title(), panel='hoenn',
            x=x + (section['x'] + section['width'] / 2) * 8 * w / 224,
            y=y + (section['y'] + section['height'] / 2) * 8 * h / 136)
    def sid(n): return 'MAPSEC_' + n + '_ISLAND'
    links = [('MAPSEC_VERMILION_CITY', sid('ONE')), (sid('ONE'), sid('TWO')),
             (sid('TWO'), sid('THREE')), (sid('FOUR'), sid('FIVE')),
             (sid('SIX'), sid('SEVEN')), (sid('ONE'), sid('FOUR')),
             (sid('TWO'), sid('FIVE')), (sid('FOUR'), sid('SIX')),
             (sid('FIVE'), sid('SEVEN')), ('MAPSEC_ROUTE_131', sid('SIX')),
             (sid('THREE'), 'MAPSEC_BIRTH_ISLAND_FRLG'),
             ('MAPSEC_BIRTH_ISLAND_FRLG', 'MAPSEC_NAVEL_ROCK_FRLG'),
             (sid('FIVE'), 'MAPSEC_BIRTH_ISLAND_FRLG'),
             (sid('SEVEN'), 'MAPSEC_NAVEL_ROCK_FRLG')]
    svg = ET.Element('{' + NS + '}svg', dict(viewBox='0 0 1288 1288', role='img',
        **{'aria-labelledby': 'title description'}))
    def add(tag, attrs=None, text=None):
        node = ET.SubElement(svg, '{' + NS + '}' + tag, {k: str(v) for k, v in (attrs or {}).items()})
        node.text = text
        return node
    add('title', {'id': 'title'}, 'Mundo conectado: Kanto ao norte, Hoenn ao sul e Sevii a leste')
    add('desc', {'id': 'description'}, 'Projeção quadrada da integração experimental. Surf no setor leste e de Cinnabar ao lago da Rota 114, costa de Rustboro e Dewford. Não representa uma campanha concluída.')
    add('rect', dict(width=1288, height=1288, fill='#80b8f8'))
    add('text', dict(x=32, y=36, fill='#16344d', **{'font-size': 23, 'font-family': 'sans-serif', 'font-weight': 'bold'}), 'MAPA DO MUNDO · INTEGRAÇÃO EM DESENVOLVIMENTO')
    for panel_id, (x, y, w, h) in PLACEMENT.items():
        panel = old_panels[panel_id]
        add('image', dict(x=x, y=y, width=w, height=h, href=panel['image'], **{'image-rendering': 'pixelated'}))
        add('text', dict(x=x, y=y-12, fill='#16344d', **{'font-size': 22, 'font-family': 'sans-serif', 'font-weight': 'bold'}), panel['name'])
    for a, b in links:
        p, q = points[a], points[b]
        add('path', dict(d=f'M {p["x"]} {p["y"]} L {q["x"]} {q["y"]}', fill='none',
                        stroke='#0d6890', **{'stroke-width': 5, 'stroke-dasharray': '8 6', 'opacity': '.8'}))
    # Replace the earlier Route21/Route127 design with the user's southern
    # crossing. Draw the coastal trunk outside Hoenn's native land contour.
    p = points['MAPSEC_CINNABAR_ISLAND']
    trunk = f'M {p["x"]} {p["y"]} L {p["x"]} 740 L 16 740 L 16 {points["MAPSEC_ROUTE_105"]["y"]}'
    add('path', dict(d=trunk, fill='none', stroke='#0d6890', **{'stroke-width': 5, 'stroke-dasharray': '8 6'}))
    western_links = []
    for ident in ['MAPSEC_ROUTE_114', 'MAPSEC_ROUTE_115', 'MAPSEC_ROUTE_105']:
        q = points[ident]
        add('path', dict(d=f'M 16 {q["y"]} L {q["x"]} {q["y"]}', fill='none', stroke='#0d6890',
                        **{'stroke-width': 5, 'stroke-dasharray': '8 6'}))
        western_links.append(dict(source='MAPSEC_CINNABAR_ISLAND', target=ident))
    for text, y in [('PASSAGEM AO SUL DE CINNABAR', 655), ('Rota 114 → costa oeste → Dewford', 683),
                    ('Oceano norte de Hoenn', 748)]:
        add('text', dict(x=200, y=y, fill='#754119', **{'font-size': 20, 'font-family': 'sans-serif'}), text)
    for p in points.values():
        add('circle', dict(cx=p['x'], cy=p['y'], r=6, fill='#fff7c7', stroke='#174a5c', **{'stroke-width': 2}))
    for ident in ['MAPSEC_VERMILION_CITY', 'MAPSEC_CINNABAR_ISLAND', 'MAPSEC_ROUTE_131', 'MAPSEC_EVER_GRANDE_CITY']:
        p = points[ident]
        add('text', dict(x=p['x']+10, y=p['y']-12, fill='#0d3647', stroke='#ebfaff',
                        **{'stroke-width': 3, 'paint-order': 'stroke', 'font-size': 18, 'font-family': 'sans-serif'}), p['name'])
    destination = ROOT / 'web/world-layout.svg'
    ET.ElementTree(svg).write(destination, encoding='unicode', xml_declaration=False)
    report = dict(status='experimental_cartography_not_complete_game', width=1288, height=1288,
        projection='Square regional chart. Native land contours; proposed ocean connections; not a metric tile-coordinate map.',
        placements=PLACEMENT, points=list(points.values()), surf_links=[dict(source=a, target=b) for a, b in links] + western_links,
        cinnabar_south_endpoint='MAPSEC_ROUTE_114', full_story_validated=False,
        generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        atlas_sha256=hashlib.sha256(atlas_path.read_bytes()).hexdigest(),
        section_source_sha256=hashlib.sha256((ROOT / '.local/emerald-base/src/data/region_map/region_map_sections.json').read_bytes()).hexdigest(),
        svg_sha256=hashlib.sha256(destination.read_bytes()).hexdigest())
    (ROOT / 'web/world-layout.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print('Square world chart generated with Route114/131 crossings; full campaign remains pending')


if __name__ == '__main__': build()
