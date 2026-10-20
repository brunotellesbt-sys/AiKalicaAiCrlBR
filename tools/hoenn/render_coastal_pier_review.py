"""Render all seven Sevii towns, connected Treasure Beach and full terminals.

These native source renders include NPCs; they are separate from emulator
captures and do not establish functional passage or collision behavior.
"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw
from render_sea_maps import MapRenderer


def render(source, baseline, output):
    source, baseline, output = map(Path, (source, baseline, output))
    output.mkdir(parents=True, exist_ok=True)
    piers = json.loads((source/'.journey-dewford-coast-safety').read_text())['piers']
    renderers = {False: MapRenderer(baseline), True: MapRenderer(source)}
    records = []
    for row in piers['town_bridges']:
        island = row['island']
        panels = []
        for after in (False, True):
            renderer = renderers[after]
            town, _ = renderer.render(row['town'])
            maps = [row['town']]
            if island == 'One':
                beach_name = 'OneIsland_TreasureBeach_Frlg'
                beach, _ = renderer.render(beach_name)
                assert town.width == beach.width
                joined = Image.new('RGB', (town.width, town.height + beach.height))
                joined.paste(town, (0, 0))
                joined.paste(beach, (0, town.height))
                town = joined
                maps.append(beach_name)
            harbor, _ = renderer.render(row['harbor'])
            maps.append(row['harbor'])
            panel = Image.new('RGB', (town.width + harbor.width + 16,
                                      max(town.height, harbor.height) + 24), '#17232b')
            ImageDraw.Draw(panel).text((0, 4), island + (' - after: wooden endpoint (native source)' if after
                                                      else ' - before (native source layer 160)'), fill='white')
            panel.paste(town, (0, 24))
            panel.paste(harbor, (town.width + 16, 24))
            filename = island + ('-after.png' if after else '-before.png')
            panel.save(output/filename)
            panels.append(panel)
        comparison = Image.new('RGB', (sum(panel.width for panel in panels) + 16,
                                       max(panel.height for panel in panels)), '#17232b')
        comparison.paste(panels[0], (0, 0))
        comparison.paste(panels[1], (panels[0].width + 16, 0))
        comparison.save(output/(island+'-comparison.png'))
        end_map, x, y = row['end']
        end, _ = renderers[True].render(end_map)
        crop = end.crop(((x-3)*16, (y-3)*16, (x+4)*16, (y+2)*16))
        crop.resize((crop.width*3, crop.height*3), Image.Resampling.NEAREST).save(output/(island+'-wooden-end.png'))
        records.append(dict(island=island, maps=maps,
                            before_png=island+'-before.png', after_png=island+'-after.png',
                            comparison_png=island+'-comparison.png',
                            endpoint_detail_png=island+'-wooden-end.png',
                            wooden_endpoint=row['end']))
    contact = Image.new('RGB', (3 * 352, 3 * 272), '#17232b')
    for index, record in enumerate(records):
        x, y = index % 3 * 352, index // 3 * 272
        ImageDraw.Draw(contact).text((x + 8, y + 4), record['island'] + ' - native wood finish', fill='white')
        contact.paste(Image.open(output/record['endpoint_detail_png']), (x + 8, y + 24))
    contact.save(output/'seven-wooden-ends.png')
    result = dict(kind='full native source renders, including all NPCs; not emulator screenshots',
                  baseline_rom_sha256=hashlib.sha256((baseline/'pokeemerald.gba').read_bytes()).hexdigest(),
                  rom_sha256=hashlib.sha256((source/'pokeemerald.gba').read_bytes()).hexdigest(),
                  all_seven_endpoints_use_native_wood=True, no_metal_endcaps=True,
                  private_wooden_metatiles=piers['wooden_endcaps']['private_metatile_ids'],
                  wooden_endcap_contact='seven-wooden-ends.png', maps=records)
    (output/'renders.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(render(a.source, a.baseline, a.output), indent=2))
