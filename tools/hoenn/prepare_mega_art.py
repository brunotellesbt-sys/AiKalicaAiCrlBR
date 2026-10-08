"""Install pinned upstream battle art for the previously incomplete Mega Garchomp Z."""
import argparse
import hashlib
import json
from pathlib import Path
from prepare_crossing import PIN
from prepare_family import LAYERS_BEFORE

ASSETS = Path(__file__).resolve().parents[2] / 'mods/hoenn/assets/mega-garchomp-z'


def prepare(source):
    source = Path(source)
    marker = source / '.journey-mega-art'
    if marker.exists():
        report = json.loads(marker.read_text())
        for path, digest in report['prepared_sha256'].items():
            assert hashlib.sha256((source / path).read_bytes()).hexdigest() == digest, path
        return report
    acquired = json.loads((source / '.source-acquired.json').read_text())
    assert acquired['commit'] == PIN
    expected = dict(acquired['sha256'])
    for layer in LAYERS_BEFORE + ['family', 'travel-rules', 'birth', 'wild', 'habitats',
                                 'sanctuaries', 'ecology', 'abilities']:
        expected.update(json.loads((source / ('.journey-' + layer)).read_text())['prepared_sha256'])
    originals, inputs, outputs = {}, {}, {}
    def read(path):
        raw = (source / path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected[path], path
        originals[path] = expected[path]
        if path in acquired['sha256']:
            inputs[path] = acquired['sha256'][path]
        return raw.decode()
    path = 'src/data/graphics/pokemon.h'
    text = read(path)
    for prefix in ['gMonFrontPic_', 'gMonBackPic_', 'gMonPalette_', 'gMonShinyPalette_']:
        lines = [line for line in text.splitlines() if prefix + 'GarchompMegaZ[]' in line]
        assert len(lines) == 1 and lines[0].startswith('//'), prefix
        text = text.replace(lines[0], lines[0][2:])
    outputs[path] = text.encode()
    path = 'src/data/pokemon/species_info/gen_4_families.h'
    text = read(path)
    start = text.index('    [SPECIES_GARCHOMP_MEGA_Z] =')
    end = text.index('\n    },', start)
    body = text[start:end]
    a = body.index('        //.frontPic =')
    b = body.index('        .iconSprite =', a)
    body = body[:a] + '''        .frontPic = gMonFrontPic_GarchompMegaZ,
        .frontPicSize = MON_COORDS_SIZE(64, 64),
        .frontPicYOffset = 0,
        .frontAnimFrames = sAnims_SingleFramePlaceHolder,
        .enemyMonElevation = 8,
        .backPic = gMonBackPic_GarchompMegaZ,
        .backPicSize = MON_COORDS_SIZE(64, 64),
        .backPicYOffset = 0,
        .palette = gMonPalette_GarchompMegaZ,
        .shinyPalette = gMonShinyPalette_GarchompMegaZ,
''' + body[b:]
    body = body.replace('        //SHADOW(-1, 0, SHADOW_SIZE_M)', '        SHADOW(0, 18, SHADOW_SIZE_L)')
    outputs[path] = (text[:start] + body + text[end:]).encode()
    provenance = json.loads((ASSETS / 'provenance.json').read_text())
    for name, record in provenance['files'].items():
        raw = (ASSETS / name).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == record['sha256'], name
        assert hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == record['git_blob'], name
        path = 'graphics/pokemon/garchomp/mega_z/' + name
        assert not (source / path).exists(), path
        outputs[path] = raw
    report = dict(status='mega_garchomp_z_battle_art_candidate', source_commit=PIN,
                  upstream=provenance, stones_distributed=False,
                  input_sha256=inputs, original_sha256=originals,
                  prepared_sha256={p: hashlib.sha256(raw).hexdigest() for p, raw in outputs.items()})
    for path, raw in outputs.items():
        (source / path).parent.mkdir(parents=True, exist_ok=True)
        (source / path).write_bytes(raw)
    marker.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    print(json.dumps(prepare(parser.parse_args().source), indent=2))
