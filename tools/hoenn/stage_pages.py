"""Stage the verified, self-contained browser player for GitHub Pages."""
import argparse,json,shutil
from pathlib import Path
from verify_playable import ROOT, verify, ROM_NAME

VERSIONS = ROOT / 'mods/hoenn/versions'
REVIEW = ROOT / 'roms/rom-de-teste'
PRUNING = ROOT / 'mods/hoenn/atlas-route-pruning'
PWT_COMPLETE = ROOT / 'mods/hoenn/pwt-complete-rosters'
SOOTOPOLIS_RESCUE = ROOT / 'mods/hoenn/sootopolis-rescue'
TITAN_STORY = ROOT / 'mods/hoenn/titan-story'
CROSSOVER_BADGES = ROOT / 'mods/hoenn/crossover-badges'
CURRENT_BROWSER_EVIDENCE = ROOT / 'mods/hoenn/versions-validation/browser-route-pruning/browser-versions.json'
PWT_BROWSER_EVIDENCE = ROOT / 'mods/hoenn/versions-validation/browser-pwt-complete/browser-versions.json'
RESCUE_BROWSER_EVIDENCE = ROOT / 'mods/hoenn/versions-validation/browser-sootopolis-rescue/browser-versions.json'
TITAN_BROWSER_EVIDENCE = ROOT / 'mods/hoenn/versions-validation/browser-titan-story/browser-versions.json'
CROSSOVER_BROWSER_EVIDENCE = ROOT / 'mods/hoenn/versions-validation/browser-crossover-badges/browser-versions.json'


def browser_evidence(release):
    if release.get('validation_scope') == 'crossover-badges':
        return CROSSOVER_BROWSER_EVIDENCE
    if release.get('validation_scope') == 'titan-story':
        return TITAN_BROWSER_EVIDENCE
    if release.get('validation_scope') == 'sootopolis-rescue':
        return RESCUE_BROWSER_EVIDENCE
    if release.get('validation_scope') == 'pwt-complete-rosters':
        return PWT_BROWSER_EVIDENCE
    if 'atlas' in release:
        return CURRENT_BROWSER_EVIDENCE
    return ROOT / 'mods/hoenn/versions-validation/browser/browser-versions.json'


def stage_current_editions(site, release):
    """Build the exact editions served by Play and Download from sealed inputs."""
    from package_review_rom import verify as verify_review
    from verify_versions import TEST_EDITION_SCOPES
    games = site / 'games'
    games.mkdir(exist_ok=True)
    review = None
    if release.get('validation_scope') in TEST_EDITION_SCOPES:
        review = verify_review(REVIEW, VERSIONS / 'Pokemon-Journey-Gen1-9-Normal.gba')
    if release.get('validation_scope') == 'atlas-surf-layout' and (PRUNING / 'validation.json').is_file():
        from verify_atlas_route_pruning import verify as verify_pruning
        current = verify_pruning(output=games)
        profiles = {row['edition']: row for row in current['editions']}
        for row in release['variants']:
            assert profiles[row['file']]['base_sha256'] == row['sha256']
        assert profiles[review['file']]['base_sha256'] == review['sha256']
        scope = 'atlas-route-pruning'
        if (PWT_COMPLETE / 'validation.json').is_file():
            from verify_pwt_complete_rosters import verify as verify_pwt
            completed = verify_pwt(PWT_COMPLETE, output=games, base_directory=games)
            profiles = completed['editions']
            scope = completed['layer']
            if (SOOTOPOLIS_RESCUE / 'validation.json').is_file():
                from verify_sootopolis_rescue import verify as verify_rescue
                rescue = verify_rescue(SOOTOPOLIS_RESCUE, output=games, base_directory=games)
                profiles = rescue['editions']
                scope = rescue['layer']
                if (TITAN_STORY / 'validation.json').is_file():
                    from verify_titan_story import verify as verify_titans
                    titans = verify_titans(TITAN_STORY, output=games, base_directory=games)
                    profiles = titans['editions']
                    scope = titans['layer']
        if scope == 'titan-story' and (CROSSOVER_BADGES / 'validation.json').is_file():
            from verify_crossover_badges import verify as verify_crossover
            crossover = verify_crossover(CROSSOVER_BADGES, output=games, base_directory=games)
            profiles = crossover['editions']
            scope = crossover['layer']
        variants = [{key: row[key] for key in ('file', 'bytes', 'max_national', 'perfect_trainer_ivs')}
                    for row in release['variants']]
        for row in variants:
            row['sha256'] = profiles[row['file']]['rom_sha256']
        atlas = dict(file='atlas-atual.png', sha256=current['map_png_sha256'])
        release = dict(validated=True, validation_scope=scope,
                       variants=variants, atlas=atlas)
        normal = next(row for row in variants if row['file'] == review['base_normal_file'])
        review = {key: review[key] for key in ('file', 'bytes', 'base_normal_file',
                  'automatic_trainer_approaches', 'random_wild_encounters', 'separate_save_identity')}
        review.update(sha256=profiles[review['file']]['rom_sha256'], base_normal_sha256=normal['sha256'])
        shutil.copyfile(PRUNING / 'mapa-HJK.png', site / atlas['file'])
        (site / 'world-map.html').write_text(
            '<!doctype html><html lang="pt-BR"><meta charset="utf-8">'
            '<title>Mapa atual de Pokémon Journey</title>'
            '<meta http-equiv="refresh" content="0;url=atlas-atual.png">'
            '<a href="atlas-atual.png">Abrir mapa atual</a></html>\n')
    else:
        for row in release['variants']:
            shutil.copyfile(ROOT / 'roms' / row['file'], games / row['file'])
        if review:
            shutil.copyfile(REVIEW / review['file'], games / review['file'])
    (games / 'versions.json').write_text(json.dumps(release, indent=2) + '\n')
    if review:
        (games / 'review.json').write_text(json.dumps(review, indent=2) + '\n')
    return release, review


def stage(output):
    output=Path(output)
    verify(ROOT/'mods/hoenn/playable')
    output.mkdir(parents=True,exist_ok=True)
    shutil.copytree(ROOT/'web',output,dirs_exist_ok=True)
    games=output/'games';games.mkdir(exist_ok=True)
    for name in [ROM_NAME,'release.json']:
        shutil.copyfile(ROOT/'mods/hoenn/playable'/name,games/name)
    shutil.copyfile(ROOT/'mods/hoenn/playable/START-HERE.md',output/'START-HERE.md')
    versions=VERSIONS
    if (versions/'versions.json').exists():
        from verify_versions import verify as verify_versions,verify_browser
        release, review = stage_current_editions(output, verify_versions(versions))
        verify_browser(release, review=review, report_path=browser_evidence(release))
        shutil.copytree(ROOT/'docs',output/'docs',dirs_exist_ok=True)
        if (ROOT/'errors').is_dir():
            shutil.copytree(ROOT/'errors',output/'errors',dirs_exist_ok=True)
        shutil.copyfile(versions/'START-HERE.md',output/'START-HERE.md')
    (output/'.nojekyll').write_text('')
    print('Static player, bundled mGBA and verified ROM staged:',output)
    return output

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    stage(p.parse_args().output)
