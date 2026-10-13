"""Freeze multiple Smogon singles spreads for moveset-aware PWT stat matching."""
import argparse,hashlib,json
import re
from pathlib import Path
from import_competitive_profiles import norm
ROOT=Path(__file__).resolve().parents[2]
STATS=['hp','atk','def','spa','spd','spe']
def stable_symbols(source,kind,file):
    # Historical spelling aliases normalize to the same key. Resolve them in
    # stable lexical order instead of depending on Python's randomized sets.
    tokens=sorted(set(re.findall(kind+r'_\w+',(source/file).read_text())))
    return {norm(token.removeprefix(kind+'_')):token for token in tokens}
def import_builds(source,reference):
    source,reference=Path(source),Path(reference)
    old=json.loads((ROOT/'tools/hoenn/data/competitive-profiles.json').read_text())
    commit=(reference/'commit.txt').read_text().strip()
    if (reference/'sources.json').exists():
        sources=json.loads((reference/'sources.json').read_text())['references']
        assert all(r['repository']=='pkmn/smogon' and r['commit']==commit for r in sources)
        expected={r['file']:r['sha256'] for r in sources}
        assert set(expected)==set(old['reference_sha256'])
    else:
        assert commit==old['reference_commit'];expected=old['reference_sha256']
    for name,digest in expected.items():
        assert hashlib.sha256((reference/name).read_bytes()).hexdigest()==digest,name
    datasets={Path(name).stem:{norm(k):v for k,v in json.loads((reference/name).read_text()).items()} for name in expected}
    species=json.loads((ROOT/'tools/hoenn/data/scarlet-violet-database.json').read_text())['species']
    moves=stable_symbols(source,'MOVE','include/constants/moves.h');moves['highjumpkick']=moves.get('hijumpkick')
    natures=stable_symbols(source,'NATURE','include/constants/pokemon.h')
    records=[]
    for sid,profile in old['profiles'].items():
        key=species[sid]['key'];sets=[]
        for origin,priority in [('gen9ou',6),('gen9nationaldex',5),('gen8ou',4)]:
            if key in datasets.get(origin,{}):
                sets += [(origin,priority,label,build) for label,build in datasets[origin][key].items()]
        if not sets:
            tiers=datasets.get('gen9',{}).get(key,{})
            tier=profile['tier']
            if tier in tiers:sets=[('gen9/'+tier,2,label,b) for label,b in tiers[tier].items()]
            elif profile['source'] in datasets and key in datasets[profile['source']]:
                sets=[(profile['source'],1,label,b) for label,b in datasets[profile['source']][key].items()]
        for origin,priority,label,build in sets:
            groups=[]
            for group in build.get('moves',[])[:4]:
                group=group if isinstance(group,list) else [group]
                groups.append([moves[norm(m)] for m in group if norm(m) in moves][:6])
            while len(groups)<4:groups.append([])
            spreads=build.get('evs',{});spreads=spreads if isinstance(spreads,list) else [spreads]
            nature=build.get('nature',profile['nature'].removeprefix('NATURE_'))
            nature=nature if isinstance(nature,list) else [nature]
            ivs=build.get('ivs',{});ivs=ivs[0] if isinstance(ivs,list) else ivs
            for index,spread in enumerate(spreads):
                evs=[int(spread.get(stat,0)) for stat in STATS]
                if 'lc' in origin:
                    major=sorted(range(6),key=lambda i:(evs[i],i),reverse=True)[:2];evs=[0]*6
                    for i in major:evs[i]=252
                if not sum(evs):evs=profile['evs'][:]
                assert max(evs)<=252 and sum(evs)<=510,(sid,label,evs)
                # Two harmless EVs can fill the legal budget without losing a
                # level-50 breakpoint from the published spread.
                for stat in sorted(range(6),key=lambda i:(evs[i]==0,-evs[i],i)):
                    add=min(510-sum(evs),252-evs[stat]);evs[stat]+=add
                    if sum(evs)==510:break
                records.append(dict(species=profile['species'],source=origin,set=label,
                    priority=priority,moves=groups,evs=evs,
                    nature=natures[norm(nature[min(index,len(nature)-1)])],
                    zero_attack=ivs.get('atk',31)==0,zero_speed=ivs.get('spe',31)==0))
    return dict(reference_repository=old['reference_repository'],reference_commit=commit,
                reference_sha256=expected,player_moves_preserved=True,
                ou_prioritized=True,records=records)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    p.add_argument('--reference',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();result=import_builds(a.source,a.reference)
    a.output.write_text(json.dumps(result,indent=2)+'\n');print('PWT stat spreads:',len(result['records']))
