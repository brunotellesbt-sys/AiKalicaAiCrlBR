"""Stage the verified, self-contained browser player for GitHub Pages."""
import argparse,shutil
from pathlib import Path
from verify_playable import ROOT, verify, ROM_NAME

def stage(output):
    output=Path(output)
    verify(ROOT/'mods/hoenn/playable')
    output.mkdir(parents=True,exist_ok=True)
    shutil.copytree(ROOT/'web',output,dirs_exist_ok=True)
    games=output/'games';games.mkdir(exist_ok=True)
    for name in [ROM_NAME,'release.json']:
        shutil.copyfile(ROOT/'mods/hoenn/playable'/name,games/name)
    shutil.copyfile(ROOT/'mods/hoenn/playable/START-HERE.md',output/'START-HERE.md')
    (output/'.nojekyll').write_text('')
    print('Static player, bundled mGBA and verified ROM staged:',output)
    return output

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    stage(p.parse_args().output)
