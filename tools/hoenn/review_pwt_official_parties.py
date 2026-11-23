"""Compare Journey rosters with PWT and late-game League battle records.

The inputs are snapshots of the regional, World Leaders and Champions
battle listings. This tool extracts only the factual party species.
"""
import argparse
from collections import defaultdict
import hashlib
from html import unescape
import json
from pathlib import Path
import re

from pwt_catalog import eligible, load

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / 'data/pwt-official-party-review.json'
SOURCES = {
    'kanto': ('0619177105beb244fb8dd6747e1713206feb70c1db3626e11fce962be7e0739a', 8),
    'johto': ('d6fe82d3bd3f830832ef5fc0a1904672d395942ffcffed48778e6bb28063df45', 8),
    'hoenn': ('72278e89d5152ea8d8a3247e32e6ad74352ae226fe404e76e0b2d9b044534413', 9),
    'sinnoh': ('2b9fb07cbce2c8cf6b4492c352de8cc4219b36ff6661fc6d9fbefa84cf1cbeb1', 8),
    'unova': ('78c647bc8ce2cd8c7219cf71a129485e95b12d27b1468adcb34e55abcd121fa5', 14),
    'worldleaders': ('92a605f8623c8715e93c6343cd69bc337b444f8b1e5120036dba6d595a707327', 47),
    'champion': ('eccdfb71459331f84b4dd896a803d7fec4be80976bdb7a3475f9dcc49d18849a', 7),
}

TRAINER = re.compile(r'<td\b[^>]*>\s*Pok.mon Trainer\s+(.*?)\s*</td>', re.S)
SPECIES = re.compile(r'<a href="/pokedex-bw/(\d{3})\.shtml">([^<]+)</a>')
REGIONAL = {'kanto': 1, 'johto': 2, 'hoenn': 3, 'sinnoh': 4, 'unova': 5}
LEAGUE_SOURCES = {
    'letsgopikachueevee': ('8dec06f3c2b57b2ea63b40caf3f3bcc52b03c6eef6a0823aed0a04e2f753fedd',
                          ('Lorelei', 'Agatha'), 'League rematch'),
    'heartgoldsoulsilver': ('48df169fbe962ad98cc9d21a960963f6eced20fae3f10d4981358f62f636216b',
                          ('Will', 'Bruno', 'Karen'), 'League rematch'),
    'omegarubyalphasapphire': ('93749f09b0d95230df8c79a587ecc42c25a2e535d0c05869186ef1d4bd0dbc69',
                              ('Sidney', 'Phoebe', 'Glacia', 'Drake'), 'League rematch'),
    'black2white2': ('0c3f63c053bea2d6ec509f2cbb8bb432feed8ffd51c61cf4c7f3d6b45e87f8db',
                    ('Shauntal', 'Grimsley', 'Caitlin', 'Marshal', 'Iris'), 'Challenge Mode League rematch'),
}
LEAGUE_CAP4_REPLACEMENTS = {
    'Lorelei': {'SANDSLASH_ALOLA': 'PILOSWINE'},
    'Agatha': {'MAROWAK_ALOLA': 'HAUNTER'},
    'Sidney': {'SCRAFTY': 'MIGHTYENA', 'ZOROARK': 'CACTURNE', 'MANDIBUZZ': 'HOUNDOOM'},
    'Phoebe': {'CHANDELURE': 'DUSCLOPS'},
    'Glacia': {'BEARTIC': 'MAMOSWINE', 'VANILLUXE': 'SEALEO'},
    'Drake': {'DRAGALGE': 'SHELGON', 'HAXORUS': 'DRAGONITE'},
}


def review_league(directory, trainers, gen4, by_number):
    result, sources = [], []
    for game, (sha, names, battle) in LEAGUE_SOURCES.items():
        raw = (directory / (game + '-elitefour.html')).read_bytes()
        if hashlib.sha256(raw).hexdigest() != sha:
            raise ValueError(('The League source snapshot changed', game))
        table_rows = re.findall(r'<tr\b[^>]*>(.*?)</tr>', raw.decode('latin1'), re.S)
        for name in names:
            heading = re.compile(r'<td\b[^>]*>\s*(?:(?:Elite Four|Champion) )?' + name + r'</td>')
            matches = [row for row in table_rows if heading.search(row)]
            # The pinned pages list the postgame rematch last. For B2W2 the
            # Challenge Mode rematch follows the normal-mode rematch.
            row = matches[-1]
            if game == 'heartgoldsoulsilver':
                team = [mon.upper().replace(' ', '_') for mon in re.findall(r'<td class="cen">(\w+)<br', row)]
            else:
                numbers = re.findall(r'<a href="/pokedex-\w+/(\d{3})\.shtml">[^<]+</a>', row)
                team = [by_number[int(number)] for number in numbers]
            if game == 'letsgopikachueevee':
                alolan = {'SANDSLASH': 'SANDSLASH_ALOLA', 'MAROWAK': 'MAROWAK_ALOLA'}
                team = [alolan.get(mon, mon) for mon in team]
            if len(team) != 6:
                raise ValueError(('Expected a six-member late-game party', game, name, team))
            prior = trainers[name]
            replacements = LEAGUE_CAP4_REPLACEMENTS.get(name, {})
            limit = [replacements.get(mon, mon) for mon in team] if name in gen4 else None
            result.append(dict(key=prior['key'], name=name, section=game, battle=battle,
                               previous=prior['species'], reference=team, gen1_4=limit,
                               gen1_4_additions=[mon for mon in limit or () if mon not in team]))
        sources.append(dict(section=game, url=f'https://www.serebii.net/{game}/elitefour.shtml',
                            page_sha256=sha, teams=len(names)))
    return result, sources


def species_catalog():
    catalog = json.loads((HERE / 'catalog_metadata.json').read_bytes())
    by_name = {row['name'].removeprefix('SPECIES_'): row['national_dex']
               for row in catalog['species'].values()}
    by_number = {int(num): catalog['species'][str(species)]['name'].removeprefix('SPECIES_')
                 for num, species in catalog['canonical_species'].items()}
    return by_name, by_number


def review(directory):
    by_name, by_number = species_catalog()
    rows = load()
    trainers = {row['name']: row for row in rows}
    gen4 = {row['name'] for row in eligible(rows, 4)}
    candidates = defaultdict(list)
    sources = []
    for key, (sha, count) in SOURCES.items():
        raw = (directory / (key + '.html')).read_bytes()
        if hashlib.sha256(raw).hexdigest() != sha:
            raise ValueError(('The PWT source snapshot changed', key))
        names = set()
        for row in re.findall(r'<tr\b[^>]*>(.*?)</tr>', raw.decode('latin1'), re.S):
            match = TRAINER.search(row)
            if not match:
                continue
            name = unescape(match[1])
            species = [int(number) for number, _ in SPECIES.findall(row)]
            if name not in trainers or name in names or len(species) != 6 or len(set(species)) != 6:
                raise ValueError(('Unexpected official trainer team', key, name, species))
            names.add(name)
            candidates[name].append((key, [by_number[number] for number in species]))
        if len(names) != count:
            raise ValueError(('Incomplete official PWT page', key, len(names)))
        sources.append(dict(section=key, url=f'https://www.serebii.net/black2white2/pwt/{key}.shtml',
                            page_sha256=sha, teams=count))

    reviewed = []
    for row in rows:
        name = row['name']
        if name not in candidates:
            continue
        # Prefer the unrestricted World Leaders team and Champions team.
        # When the entry exists in different regional cups, prefer its own.
        priority = lambda p: (p[0] == 'champion', p[0] == 'worldleaders',
                              REGIONAL.get(p[0]) == min(row['generations']), p[0])
        section, team = max(candidates[name], key=priority)
        gen4_team = None
        if name in gen4:
            gen4_team = []
            # Use the same character's legal choices from the reviewed cups.
            # The previous Journey team supplies any remaining thematic slots.
            pool = team + [mon for _, other in sorted(candidates[name], key=priority, reverse=True)
                           for mon in other] + row['species']
            used = set()
            for mon in pool:
                number = by_name[mon]
                if number > 493 or number in used:
                    continue
                gen4_team.append(mon)
                used.add(number)
                if len(gen4_team) == 6:
                    break
            if len(gen4_team) != 6:
                raise ValueError(('Additional Gen 1–4 choices need author review', name, gen4_team))
        reviewed.append(dict(key=row['key'], name=name, section=section,
                             previous=row['species'], reference=team, gen1_4=gen4_team,
                             gen1_4_additions=[mon for mon in gen4_team or () if mon not in team]))
    league, league_sources = review_league(directory, trainers, gen4, by_number)
    covered = {row['key'] for row in reviewed + league}
    return dict(kind='pwt-and-league-party-references', sources=sources + league_sources, reviewed=reviewed,
                league_reviewed=league, remaining=[row['key'] for row in rows if row['key'] not in covered])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference_directory', type=Path)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    report = review(args.reference_directory)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(f"{len(report['reviewed'])} tournament teams, {len(report['league_reviewed'])} League teams, "
          f"{len(report['remaining'])} other entries")
