"""Run at most ten representative edition/pool combinations."""
import argparse,concurrent.futures,json,subprocess,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def run_suite(views,library,output,release,jobs=4,max_tournaments=10):
    assert 1<=max_tournaments<=10
    tasks=[(f'Gen1-{cap}-{difficulty}',pool,'balanced')
           for pool in (0,1) for cap in (4,9) for difficulty in ('Normal','Hard')]
    tasks += [('Gen1-9-Normal',9,'balanced'),('Gen1-9-Hard',9,'balanced')]
    tasks=tasks[:max_tournaments]
    def run(task):
        edition,pool,team=task
        target=output/edition/(f'cup-{pool}' if team=='balanced' else 'developing-world')
        target.mkdir(parents=True,exist_ok=True)
        old=target/'pwt-unboosted.json'
        if old.exists():old.unlink()  # Only this runner's generated report.
        if release and team=='balanced':
            old=release/edition/f'pwt-unboosted-{pool}.json'
            if old.exists():old.unlink()
        with (target/'run.log').open('w') as log:
            result=subprocess.run(['python3',str(ROOT/'tools/hoenn/validate_pwt_unboosted.py'),
                '--source',str(views/edition),'--library',str(library),'--output',str(target),
                '--play-cup','--cup-generation',str(pool),'--team',team],stdout=log,stderr=subprocess.STDOUT)
        if result.returncode==0 and release and team=='balanced':
            shutil.copyfile(target/'pwt-unboosted.json',release/edition/f'pwt-unboosted-{pool}.json')
        print(edition,pool,team,'exit',result.returncode,flush=True)
        return dict(edition=edition,pool=pool,team=team,exit_code=result.returncode,
                    report=(target/'pwt-unboosted.json').relative_to(output).as_posix())
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as executor:
        results=list(executor.map(run,tasks))
    passed=all(r['exit_code']==0 for r in results)
    (output/'runs.json').write_text(json.dumps(dict(passed=passed,runs=results),indent=2)+'\n')
    assert passed,'Inspect failed run.log files; failed runs are never counted as balanced victories'

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--views',type=Path,required=True);p.add_argument('--library',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--release',type=Path)
    p.add_argument('--jobs',type=int,choices=range(1,9),default=4)
    a=p.parse_args();run_suite(a.views.resolve(),a.library.resolve(),a.output.resolve(),
                             a.release.resolve() if a.release else None,a.jobs)
