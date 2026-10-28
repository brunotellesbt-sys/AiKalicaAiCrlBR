"""Run the full native surface-seam plan in independent bounded shards.

Each process owns its emulator and output directory. A successful merge binds
every planned case to the same frozen ROM and rejects gaps or duplicate cases.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from validate_generated_surface_navigation import merge_reports

ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(source, library, output, jobs=5):
    source, library, output = [Path(p).resolve() for p in (source, library, output)]
    assert 1 <= jobs <= 6
    output.mkdir(parents=True, exist_ok=True)
    frozen = {name:digest(source/name) for name in ('pokeemerald.gba','pokeemerald.elf')}
    tool = ROOT/'tools/hoenn/validate_generated_surface_navigation.py'
    base = [sys.executable,str(tool),'--source',str(source),'--library',str(library)]
    plan_dir = output/'plan'
    with (output/'plan.log').open('w') as stream:
        subprocess.run([*base,'--output',str(plan_dir)],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,check=True)
    plan = json.loads((plan_dir/'generated-surface-navigation.json').read_text())
    assert plan['graph_passed'] and plan['rom_sha256'] == frozen['pokeemerald.gba']
    count = plan['planned_native_case_count']
    assert count and count == len(plan['planned_native_cases'])
    span = (count+jobs-1)//jobs
    slices = [(start,min(span,count-start)) for start in range(0,count,span)]
    paths = [output/f'shard-{index:02d}'/'generated-surface-navigation.json' for index in range(len(slices))]
    journal = dict(kind='generated-navigation-batch',rom_sha256=frozen['pokeemerald.gba'],
                   native_case_count=count,shards=[dict(index=i,start=start,limit=limit,completed=False)
                   for i,(start,limit) in enumerate(slices)])
    def save():
        (output/'batch.json').write_text(json.dumps(journal,indent=2)+'\n')
    save()
    def shard(index,start,limit):
        directory = paths[index].parent
        with (output/f'shard-{index:02d}.log').open('w') as stream:
            result = subprocess.run([*base,'--output',str(directory),'--native',
                                     '--start-case',str(start),'--limit',str(limit)],
                                    cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
        return index,result.returncode
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        futures = [pool.submit(shard,i,start,limit) for i,(start,limit) in enumerate(slices)]
        for future in as_completed(futures):
            index,code = future.result()
            journal['shards'][index].update(completed=True,exit_code=code)
            save()
            print('Surface-seam shard completed:',index,'exit',code,flush=True)
    assert all(digest(source/name) == value for name,value in frozen.items()), 'Frozen input changed during native checks'
    failed = [row['index'] for row in journal['shards'] if row['exit_code']]
    assert not failed, ('Native seam shards failed; inspect their logs and progress reports',failed)
    merged = merge_reports(paths,output/'generated-surface-navigation.json')
    assert merged['passed'] and merged['rom_sha256'] == frozen['pokeemerald.gba']
    journal.update(passed=True,native_all_planned_cases_executed=True)
    save()
    print('All native surface seams passed:',len(merged['native_cases']),flush=True)
    return merged


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--library',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--jobs',type=int,default=5)
    args = parser.parse_args()
    run(args.source,args.library,args.output,args.jobs)
