"""Acquire pinned public PWT artwork/reference parties without embedding credentials.

Downloads go to the ignored cache. The overlay consumes the converted assets and
the source manifest, never a moving HEAD or a live network request.
"""
import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
from urllib.parse import quote
from PIL import Image
from pack_crossover_assets import fit, indexed
from pwt_catalog import load

ROOT = Path(__file__).resolve().parents[2]
PORTRAITS = ('josewp808/pokemon-trainer-sprites', 'ba2d41a1ed3f49c00c74fe6c94a643860c45d5cd')
EXTRAS = ('christt105/pokemon-hof-generator', 'e30aee2fab2b9d6d761e27f4fde29d33c2fef2e1')
PLATINUM = ('pret/pokeplatinum', 'fe1ea418a7364c93daf0d07ae55e195452d8803c')
PLATINUM_PARTIES = {
    'ROARK': 'leader_roark_rematch', 'GARDENIA': 'leader_gardenia_rematch',
    'MAYLENE': 'leader_maylene_rematch', 'CRASHER_WAKE': 'leader_wake_rematch',
    'FANTINA': 'leader_fantina_rematch', 'BYRON': 'leader_byron_rematch',
    'CANDICE': 'leader_candice_rematch', 'VOLKNER': 'leader_volkner_rematch',
    'AARON': 'elite_four_aaron_rematch', 'BERTHA': 'elite_four_bertha_rematch',
    'FLINT': 'elite_four_flint_rematch', 'LUCIAN': 'elite_four_lucian_rematch',
    'CYNTHIA': 'champion_cynthia_rematch', 'BARRY': 'rival_survival_area_2_turtwig',
}

def acquire(repo, commit, path, target):
    endpoint = f'repos/{repo}/contents/{quote(path, safe="/")}?ref={commit}'
    raw = subprocess.run(['gh', 'api', endpoint], check=True, capture_output=True).stdout
    obj = json.loads(raw)
    if obj['encoding'] == 'none':
        # GitHub's Contents API omits base64 for files larger than 1 MiB.
        blob=json.loads(subprocess.run(['gh','api',f'repos/{repo}/git/blobs/{obj["sha"]}'],check=True,capture_output=True).stdout)
        assert blob['encoding']=='base64' and blob['sha']==obj['sha']
        data=base64.b64decode(blob['content'],validate=False)
    else:
        assert obj['encoding'] == 'base64', path
        data = base64.b64decode(obj['content'], validate=False)
    assert len(data) == obj['size'], path
    git_blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    assert git_blob == obj['sha'], path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return dict(repository=repo, commit=commit, path=path, git_blob=git_blob,
                sha256=hashlib.sha256(data).hexdigest(), file=target.name)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, default=ROOT/'.local/pwt-reference-assets')
    a = p.parse_args(); out = a.output; out.mkdir(parents=True, exist_ok=True)
    def portrait(row):
        if row['key'] in ('EREN', 'LUFFY'):
            return dict(key=row['key'], existing='journey_'+row['key'].lower())
        repo, commit = EXTRAS if row['key'] in ('LACEY', 'ADAMAN') else PORTRAITS
        path = ('src/assets/sprites/trainers/' if (repo,commit)==EXTRAS else 'trainers/') + row['portrait']+'.png'
        target = out/(row['key'].lower()+'-raw.png')
        info = acquire(repo,commit,path,target)
        packed = out/(row['key'].lower()+'-front.png')
        image = Image.open(target).convert('RGBA')
        assert image.getbbox() is not None
        indexed(fit(image,64,64)).save(packed)
        info.update(key=row['key'], converted=packed.name,
                    converted_sha256=hashlib.sha256(packed.read_bytes()).hexdigest(),
                    original_size=list(image.size), conversion='nearest fit 64x64; shared 15 colors + transparent')
        return info
    with ThreadPoolExecutor(max_workers=6) as pool:
        records = list(pool.map(portrait,load()))
    parties = []
    for key,stem in PLATINUM_PARTIES.items():
        target = out/(key.lower()+'-party.json')
        info = acquire(*PLATINUM, 'res/trainers/data/'+stem+'.json', target)
        info.update(key=key, party=json.loads(target.read_text())['party'])
        parties.append(info)
    manifest = dict(portraits=records, party_references=parties)
    (out/'sources.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'Acquired {len(records)} portraits ({sum("existing" in r for r in records)} existing), {len(parties)} reference parties.')

if __name__ == '__main__':
    main()
