"""Launch an editor headlessly in an offline container, preserving the original ROM."""
import argparse
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tool', choices=['runtimes', 'hma', 'advancemap', 'xse'])
    parser.add_argument('--rom', type=Path, help='Copy this ROM to an ignored working directory; never overwrite an existing copy.')
    args = parser.parse_args()
    if args.rom and args.tool == 'runtimes':
        parser.error('--rom requires an editor')
    state = ROOT / '.local/rom-tools' / args.tool
    state.mkdir(parents=True, exist_ok=True)
    if args.rom:
        original = args.rom.resolve(strict=True)
        working = state / 'working.gba'
        # Exclusive creation preserves any existing edits.
        try:
            with working.open('xb') as output, original.open('rb') as source:
                shutil.copyfileobj(source, output)
        except FileExistsError:
            print('Reusing existing working.gba; existing edits are preserved.')
    config = ROOT / '.local/docker-cli'
    config.mkdir(parents=True, exist_ok=True)
    command = ['docker', '--config', str(config), 'run', '--init', '--network', 'none',
               '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--memory', '2g', '--cpus', '2',
               '--mount', f'type=volume,src=leafgreen-{args.tool}-state,dst=/home/editor',
               '--mount', f'type=bind,src={state},dst=/work']
    if args.tool == 'runtimes':
        command += ['--rm']
    else:
        command += ['--detach', '--name', 'leafgreen-' + args.tool]
    command += ['leafgreen-editors:1', args.tool]
    if args.rom:
        command += ['Z:/work/working.gba']
    subprocess.run(command, check=True)


if __name__ == '__main__':
    main()
