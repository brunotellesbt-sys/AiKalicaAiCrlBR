"""Overlay verified donor data onto the pinned expanded LeafGreen engine."""
import ast
import json
from pathlib import Path
import re
import subprocess
import zipfile

def matching(text, start, opening='{', closing='}'):
    depth = 0; quote = False; escape = False
    for i in range(start,len(text)):
        c = text[i]
        if quote:
            if escape: escape = False
            elif c == '\\': escape = True
            elif c == '"': quote = False
        elif c == '"': quote = True
        elif c == opening: depth += 1
        elif c == closing:
            depth -= 1
            if depth == 0: return i
    raise ValueError('Unbalanced initializer')

def fields(body):
    result = {}; start = 0; depth = 0; quote = False; escape = False
    for i,c in enumerate(body):
        if quote:
            if escape: escape = False
            elif c == '\\': escape = True
            elif c == '"': quote = False
        elif c == '"': quote = True
        elif c in '({[': depth += 1
        elif c in ')}]': depth -= 1
        elif c == ',' and depth == 0:
            part = body[start:i].strip(); start = i+1
            m = re.fullmatch(r'\.(\w+)\s*=\s*(.*)',part,re.S)
            if not m: raise ValueError(f'Unexpected field: {part[:80]}')
            result[m[1]] = m[2]
    return result

def integer_expression(value):
    def number(node):
        if isinstance(node,ast.Constant) and isinstance(node.value,int): return node.value
        if isinstance(node,ast.BinOp) and isinstance(node.op,(ast.Add,ast.Sub)):
            left,right = number(node.left),number(node.right)
            return left+right if isinstance(node.op,ast.Add) else left-right
        raise ValueError('Unexpected species index expression')
    return number(ast.parse(value.strip(),mode='eval').body)

def apply(source, cpp, archive, raw=None):
    # Let the engine's own preprocessor expand inherited form macros. This
    # preserves icon, cry, animation and form-change references, including
    # Unown and regional forms that don't have separate literal initializers.
    if raw is None: raw = subprocess.check_output([str(cpp),'-P','-iquote','include','-Wno-trigraphs','-DMODERN=1','-DTESTING=0','-DLEAFGREEN','-std=gnu17','src/pokemon.c'],cwd=source,text=True)
    start = re.search(r'const struct SpeciesInfo gSpeciesInfo\[[^]]*\] =',raw).start()
    start = raw.index('{',start); end = matching(raw,start)
    table = raw[start+1:end]; entries = {}
    pos = 0
    while pos < len(table):
        m = re.search(r'\[([0-9()+\-\s]+)\]\s*=\s*\{',table[pos:])
        if not m: break
        begin = pos+m.end()-1; finish = matching(table,begin)
        entries[integer_expression(m[1])] = fields(table[begin+1:finish]); pos = finish+1
    with zipfile.ZipFile(archive) as z:
        report = json.loads(z.read('catalog.json'))
        for name in z.namelist():
            if name == 'catalog.json': continue
            path = source/'graphics/unova'/name
            path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(z.read(name))
    allowed = {r['species_id'] for r in report['catalog']}
    definitions = []; generated = []; corrected = []; fallbacks = []
    for r in report['catalog']:
        ident = r['species_id']; donor = r['donor_id']; f = entries[ident]
        for key,value in zip(['baseHP','baseAttack','baseDefense','baseSpeed','baseSpAttack','baseSpDefense'],r['stats']): f[key] = str(value)
        if not r.get('native_metadata'):
            # Retain the engine's canonical Fairy typings, including regional forms
            # such as Alolan Ninetales; otherwise honor the donor's two types.
            if 'TYPE_FAIRY' in f['types']:
                if 'FAIRY' not in r['types']: corrected.append(r['species'])
            else: f['types'] = '{'+', '.join('TYPE_'+t for t in r['types'])+'}'
            for key,value in [('catchRate',r['catch_rate']),('expYield',r['exp_yield']),('genderRatio',r['gender']),('eggCycles',r['egg_cycles']),('friendship',r['friendship']),('growthRate',r['growth'])]: f[key] = str(value)
            for key,value in zip(['evYield_HP','evYield_Attack','evYield_Defense','evYield_Speed','evYield_SpAttack','evYield_SpDefense'],r['ev_yields']): f[key] = str(value)
            f['eggGroups'] = '{'+','.join(map(str,r['egg_groups']))+'}'
            f['abilities'] = '{'+','.join(r['abilities'])+'}'
        if r.get('ability_override'):
            f['abilities'] = '{'+','.join(r['ability_override'])+'}'
        if not r.get('native_graphics'):
            for kind,field,ext,ctype in [('front','frontPic','4bpp.lz','U32'),('back','backPic','4bpp.lz','U32'),('palette','palette','gbapal','U16')]:
                symbol = f'gUnova{kind.title()}{donor}'
                definitions.append(f'static const u{32 if ctype == "U32" else 16} {symbol}[] = INCBIN_{ctype}("graphics/unova/{donor}/{kind}.{ext}");')
                f[field] = symbol
        f['frontAnimFrames'] = 'sAnims_SingleFramePlaceHolder'
        f['frontAnimId'] = '0'
        for key in list(f):
            if key.endswith('Female'): del f[key]
        if r['learnset']:
            symbol = f'sUnovaLearnset{donor}'
            definitions.append('static const struct LevelUpMove '+symbol+'[] = {'+','.join('{%s,%d}' % tuple(pair) for pair in r['learnset'])+', {0xFFFF,0}};')
            f['levelUpLearnset'] = symbol
        else: fallbacks.append(r['species'])
        # Do not enable evolutions into species absent from the donor. The
        # engine's battle-only Mega changes are retained separately.
        if 'evolutions' in f:
            evo = f['evolutions']; kept = []
            m = re.search(r'\)\s*\{',evo)
            if not m: raise ValueError('Unexpected evolution initializer')
            p = m.end()
            while p < len(evo):
                b = evo.find('{',p)
                if b < 0: break
                e = matching(evo,b); item = evo[b:e+1]
                target = re.match(r'\{\s*EVO_\w+,\s*[^,]+,\s*(\d+)',item)
                if not target or int(target[1]) in allowed: kept.append(item)
                p = e+1
            f['evolutions'] = '(const struct Evolution[]) {'+', '.join(kept)+'}'
        if report.get('disabled_mechanics') and f.get('formSpeciesIdTable') not in [None, 'NULL']:
            table_name = f['formSpeciesIdTable']
            match = re.search(r'static const u16 '+re.escape(table_name)+r'\[\] =\s*\{',raw)
            if not match: raise ValueError('Missing form species table '+table_name)
            body = raw[match.end():matching(raw,match.end()-1)]
            values = [int(v) for v in re.findall(r'\b\d+\b',body) if int(v) != 0]
            # Preserve index positions; excluded size/Tera forms safely resolve
            # to the family's normal form instead of shifting native indexes.
            base = next(v for v in values if v in allowed)
            values = [v if v in allowed else base for v in values]
            symbol = f'sCatalogFormSpecies{ident}'
            definitions.append('static const u16 '+symbol+'[] = {'+','.join(map(str,values))+',0xFFFF};')
            f['formSpeciesIdTable'] = symbol
        if report.get('disabled_mechanics') and f.get('formChangeTable') not in [None, 'NULL']:
            table_name = f['formChangeTable']
            match = re.search(r'static const struct FormChange '+re.escape(table_name)+r'\[\] =\s*\{',raw)
            if not match: raise ValueError('Missing form table '+table_name)
            body = raw[match.end():matching(raw,match.end()-1)]
            kept = []
            for item in re.findall(r'\{[^{}]*\}',body):
                target = re.match(r'\{\s*(FORM_CHANGE_\w+),\s*(\d+)',item)
                if target and (int(target[2]) not in allowed or any(k in target[1] for k in ['GIGANTAMAX','ULTRA_BURST','TERASTALLIZATION'])): continue
                kept.append(item)
            symbol = f'sCatalogFormChanges{ident}'
            definitions.append('static const struct FormChange '+symbol+'[] = {'+','.join(kept)+'};')
            f['formChangeTable'] = symbol
        generated.append(f'    [{r["species"]}] = {{\n'+''.join(f'        .{k} = {v},\n' for k,v in f.items())+'    },\n')
    # Keep exactly the imported catalog, NONE and EGG. Other species remain
    # zero-filled and cannot be created by ordinary game evolution paths.
    for ident in [0,max(entries)]:
        generated.append(f'    [{ident}] = {{\n'+''.join(f'        .{k} = {v},\n' for k,v in entries[ident].items())+'    },\n')
    (source/'src/data/pokemon/unova_assets.h').write_text('\n'.join(definitions)+'\n')
    (source/'src/data/pokemon/unova_species.h').write_text(''.join(generated))
    header = source/'src/data/pokemon/species_info.h'; s = header.read_text().replace('#include "unova_assets.h"\n','')
    start = re.search(r'const struct SpeciesInfo gSpeciesInfo\[[^]]*\] =',s).start(); begin = s.index('{',start); end = matching(s,begin)
    s = s[:start]+'#include "unova_assets.h"\nconst struct SpeciesInfo gSpeciesInfo[NUM_SPECIES + 1] =\n{\n#include "unova_species.h"\n}'+';\n'
    header.write_text(s)
    report['corrected_fairy_species'] = corrected
    report['native_learnset_fallbacks'] = fallbacks
    (source/'.unova-prepared').write_text(json.dumps(report,indent=2)+'\n')
    return report
