"""Launch editors in one offline desktop container, preserving original ROMs."""
import argparse
from pathlib import Path
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
SESSION = 'leafgreen-desktop'
IMAGE = 'leafgreen-editors:1'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tool', choices=['runtimes', 'hma', 'advancemap', 'xse'])
    parser.add_argument('--rom', type=Path, help='Copy this ROM; never overwrite an existing working copy.')
    args = parser.parse_args()
    if args.rom and args.tool == 'runtimes':
        parser.error('--rom requires an editor')
    work = ROOT / '.local/rom-tools'
    state = work / args.tool
    state.mkdir(parents=True, exist_ok=True)
    if args.rom:
        original = args.rom.resolve(strict=True)
        working = state / 'working.gba'
        try:
            with working.open('xb') as output, original.open('rb') as source:
                try:
                    shutil.copyfileobj(source, output)
                except BaseException:
                    working.unlink()  # Remove only the incomplete copy created by this attempt.
                    raise
        except FileExistsError:
            print('Reusing existing working.gba; existing edits are preserved.')
    config = ROOT / '.local/docker-cli'
    config.mkdir(parents=True, exist_ok=True)
    docker = ['docker', '--config', str(config)]
    existing = subprocess.run(docker + ['container', 'inspect', '--format', '{{.State.Running}}', SESSION],
                              capture_output=True, text=True)
    if existing.returncode:
        # VFS copies the entire image for each container. One shared desktop avoids
        # exhausting this cloud's disk when running the three tools together.
        subprocess.run(docker + ['run', '--detach', '--name', SESSION, '--init', '--network', 'none',
                                 '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
                                 '--memory', '3g', '--cpus', '2',
                                 '--mount', 'type=volume,src=leafgreen-desktop-state,dst=/home/editor',
                                 '--mount', f'type=bind,src={work},dst=/work', '--entrypoint', '/bin/sh',
                                 IMAGE, '-c', 'mkdir -p /home/editor/logs; Xvfb :99 -screen 0 1280x900x24 -nolisten tcp > /home/editor/logs/xvfb.log 2>&1 & exec sleep infinity'], check=True)
    elif existing.stdout.strip() != 'true':
        subprocess.run(docker + ['start', SESSION], check=True)
    for _ in range(50):
        ready = subprocess.run(docker + ['exec', '-e', 'DISPLAY=:99', SESSION, 'xdpyinfo'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if ready.returncode == 0:
            break
        time.sleep(0.2)
    else:
        raise RuntimeError('Xvfb did not become ready; inspect docker logs leafgreen-desktop')
    command = docker + ['exec', '-e', 'DISPLAY=:99']
    if args.tool != 'runtimes':
        patterns = {'hma': 'HexManiacAdvance.dll', 'advancemap': 'AdvanceMap.exe', 'xse': 'XSE.exe'}
        running = subprocess.run(docker + ['exec', SESSION, 'pgrep', '-f', patterns[args.tool]],
                                 stdout=subprocess.DEVNULL)
        if running.returncode == 0:
            print(f'{args.tool} is already running in {SESSION}.')
            return
        command += ['--detach', SESSION, 'sh', '-c',
                    'exec leafgreen-editor "$@" >"/home/editor/logs/$1.log" 2>&1', 'leafgreen-launch']
    else:
        command += [SESSION, 'leafgreen-editor']
    command += [args.tool]
    if args.rom:
        command += [f'Z:/work/{args.tool}/working.gba']
    subprocess.run(command, check=True)
    if args.tool != 'runtimes':
        print(f'Launched {args.tool}; inspect /home/editor/logs/{args.tool}.log and its visible window in {SESSION}.')


if __name__ == '__main__':
    main()
