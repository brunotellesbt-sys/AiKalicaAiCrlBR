"""Freeze legal TM/tutor and egg compatibility from the pinned Showdown source."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def collect(downloads):
    downloads=Path(downloads)
    provenance=json.loads((downloads/'provenance.json').read_text())
    assert provenance['commit']=='942cda71d14bf0618bd57991708a2e2734b6daba'
    decoded={}
    for file,key in [('learnsets','Learnsets'),('pokedex','Pokedex')]:
        row=next(r for r in provenance['files'] if r['file']==file)
        raw=(downloads/(file+'.ts')).read_bytes()
        assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==row['git_blob_sha']
        code='const m=await import('+json.dumps((downloads/(file+'.ts')).resolve().as_uri())+');process.stdout.write(JSON.stringify(m['+json.dumps(key)+']));'
        decoded[file]=json.loads(subprocess.check_output(['node','--input-type=module','-e',code]))
    stats=json.loads((ROOT/'tools/hoenn/data/species-base-stats.json').read_text())
    database=json.loads((ROOT/'tools/hoenn/data/scarlet-violet-database.json').read_text())
    moves={row['key']:int(mid) for mid,row in database['moves'].items()}
    dex,learn=decoded['pokedex'],decoded['learnsets']
    norm=lambda x:re.sub('[^a-z0-9]','',x.lower())
    def base_key(key):
        seen=set()
        while key not in learn:
            if key in seen:return None
            seen.add(key);record=dex.get(key,{})
            parent=record.get('changesFrom') or record.get('baseSpecies')
            if not parent:return None
            key=norm(parent)
        return key
    rows={};missing=[];unknown=set()
    for sid,record in stats['species'].items():
        key=base_key(record['key'])
        if key is None:
            prior=database['species'].get(sid,{})
            key=base_key(prior.get('key',''))
        if key is None:missing.append(record['species']);continue
        teach=set();egg=set();pending=[key];seen=set()
        while pending:
            current=pending.pop()
            if current in seen:continue
            seen.add(current)
            for move,tags in learn.get(current,{}).get('learnset',{}).items():
                kinds={m[1] for tag in tags if (m:=re.match(r'^[1-9]([MTE])',tag))}
                if not kinds:continue
                if move not in moves:unknown.add(move);continue
                if kinds&{'M','T'}:teach.add(moves[move])
                if 'E' in kinds:egg.add(moves[move])
            record_dex=dex.get(current,{})
            # Appliance/fusion/cosplay learnsets contain only their additional
            # moves. Showdown's changesFrom explicitly identifies the parent;
            # regional forms with complete independent learnsets do not use it.
            for parent in [record_dex.get('prevo'),record_dex.get('changesFrom')]:
                if parent and (parent_key:=base_key(norm(parent))):pending.append(parent_key)
        rows[sid]=dict(species=record['species'],reference_key=key,teachable=sorted(teach),egg=sorted(egg))
    assert not unknown,sorted(unknown)
    # Kept distinct: older official transfer sources are valid for National Dex
    # builds; egg moves do not become TM moves just because the boss can use them.
    return dict(provenance=provenance,source_sha256={k:hashlib.sha256((downloads/(k+'.ts')).read_bytes()).hexdigest() for k in decoded},
        policy='Official TM/tutor/egg sources across generations 1–9; retain legitimate transfer compatibility for National Dex builds; inherit pre-evolution compatibility; level-up remains level-gated',
        species=rows,missing_forms=missing,max_egg_moves=max(len(r['egg']) for r in rows.values()))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--downloads',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=collect(a.downloads);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    print('Frozen non-level compatibility:',len(r['species']),'forms; max egg moves',r['max_egg_moves'],'missing',len(r['missing_forms']))
