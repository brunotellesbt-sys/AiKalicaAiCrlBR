#!/usr/bin/env python3
"""Extract the verified Unova Emerald 2.0.3 catalog, without copying game code."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import zipfile

HERE = Path(__file__).resolve().parent
TARGET_SHA = 'b3007eaccb1ae087dcb33389c4a0f1c0092e6b5b1650a28e3f9482929c55176b'
TYPES = ['NORMAL','FIGHTING','FLYING','POISON','GROUND','ROCK','BUG','GHOST','STEEL','MYSTERY','FIRE','WATER','GRASS','ELECTRIC','PSYCHIC','ICE','DRAGON','DARK','FAIRY']

def decode(raw):
    chars = {0:' ',0xAD:'.',0xAE:'-',0xB4:"'",0xB5:'♂',0xB6:'♀',0x1B:'é',0xB8:',',0xBA:'/',0xAC:'?'}
    chars.update({0xBB+i:chr(65+i) for i in range(26)})
    chars.update({0xD5+i:chr(97+i) for i in range(26)})
    chars.update({0xA1+i:str(i) for i in range(10)})
    return ''.join(chars.get(c, f'<{c:02x}>') for c in raw.split(b'\xff')[0])

def lz77(rom, pointer):
    p = pointer - 0x08000000
    if not 0 <= p < len(rom)-4 or rom[p] != 0x10:
        raise ValueError(f'Invalid LZ77 pointer {pointer:08x}')
    size = int.from_bytes(rom[p+1:p+4], 'little')
    if not 1 <= size <= 16384: raise ValueError('Invalid decoded size')
    cursor = p+4; result = bytearray()
    while len(result) < size:
        flags = rom[cursor]; cursor += 1
        for bit in range(7,-1,-1):
            if len(result) == size: break
            if flags & (1 << bit):
                v = int.from_bytes(rom[cursor:cursor+2],'big'); cursor += 2
                length, distance = (v >> 12)+3, (v & 4095)+1
                if distance > len(result) or len(result)+length > size:
                    raise ValueError('Invalid LZ77 reference')
                for _ in range(length): result.append(result[-distance])
            else:
                result.append(rom[cursor]); cursor += 1
    return bytes(result), rom[p:cursor]

def macro(name):
    return 'SPECIES_'+name.upper().replace('♀','_F').replace('♂','_M').replace('.','').replace("'",'').replace(' ','_').replace('-','_')

def mapping(source):
    names = json.loads((HERE/'donor-names.json').read_text())
    forms = json.loads((HERE/'donor-forms.json').read_text())
    text = (source/'include/constants/species.h').read_text()
    enums = dict(re.findall(r'#define (SPECIES_\w+)\s+([^\n/]+)',text))
    def ident(n):
        v = enums[n].strip()
        return int(v) if v.isdigit() else ident(v)
    result = {r['species_id']:macro(r['name']) for r in names if r['national_dex'] > 0}
    # Family form tables preserve order; these distinguish base aliases and
    # special forms whose order differs between the two engines.
    suffixes = {
        'Pikachu':['COSPLAY','ROCK_STAR','BELLE','POP_STAR','PHD','LIBRE','ORIGINAL','HOENN','SINNOH','UNOVA','KALOS','ALOLA','PARTNER','WORLD','GMAX'],
        'Meowth':['ALOLA','GALAR','GMAX'], 'Eevee':['GMAX'],
        'Castform':['SUNNY','RAINY','SNOWY'], 'Deoxys':['ATTACK','DEFENSE','SPEED'],
        'Burmy':['SANDY','TRASH'], 'Wormadam':['SANDY','TRASH'],
        'Cherrim':['SUNSHINE'], 'Shellos':['EAST'], 'Gastrodon':['EAST'],
        'Giratina':['ORIGIN'], 'Shaymin':['SKY'],
        'Basculin':['BLUE_STRIPED','WHITE_STRIPED'],
        'Darmanitan':['ZEN','GALAR_STANDARD','GALAR_ZEN'],
        'Deerling':['SUMMER','AUTUMN','WINTER'], 'Sawsbuck':['SUMMER','AUTUMN','WINTER'],
        'Tornadus':['THERIAN'], 'Thundurus':['THERIAN'], 'Landorus':['THERIAN'],
        'Kyurem':['WHITE','BLACK'], 'Keldeo':['RESOLUTE'], 'Meloetta':['PIROUETTE'],
        'Genesect':['DOUSE','SHOCK','BURN','CHILL'],
    }
    for name, ids in forms.items():
        root = macro(name)
        mega = [i for i in ids if 894 <= i <= 949 and i not in [924,927,928,929,930,931,932,944,945]]
        mega_suffix = ['MEGA_X','MEGA_Y'] if name in ['Charizard','Mewtwo'] else ['MEGA']
        for i,s in zip(mega,mega_suffix): result[i] = root+'_'+s
        if name in ['Kyogre','Groudon']: result[ids[1]] = root+'_PRIMAL'
        others = [i for i in ids[1:] if i not in result]
        if not others: continue
        if name == 'Arceus':
            ss = TYPES[1:9]+TYPES[10:18]+['FAIRY']
        else:
            ss = suffixes.get(name)
            if ss is None:
                ss = [n[len(root)+1:] for n in enums if n.startswith(root+'_') and 'MEGA' not in n and 'TOTEM' not in n]
        if len(ss) != len(others): raise ValueError(f'Ambiguous forms: {name}: {others}, {ss}')
        for i,s in zip(others,ss): result[i] = root+'_'+s
    result.update({1476:'SPECIES_WOOPER_PALDEA',1477:'SPECIES_TAUROS_PALDEA_COMBAT',1478:'SPECIES_TAUROS_PALDEA_BLAZE',1479:'SPECIES_TAUROS_PALDEA_AQUA'})
    # The Unown A base is already in result; aliases resolve to the same ID.
    return result, {n:ident(n) for n in result.values()}

def norm(name): return re.sub(r'[^a-z0-9]','',name.lower())

def name_map(source, kind):
    path = 'abilities.h' if kind == 'ABILITY' else 'moves_info.h'
    text = (source/'src/data'/path).read_text()
    pattern = r'\[('+kind+r'_\w+)\]\s*=\s*\{\s*\.name = (?:_|COMPOUND_STRING)\("([^"\n]*)"\)'
    return {norm(name):key for key,name in re.findall(pattern,text)}

def extract(rom, source, output):
    if hashlib.sha256(rom).hexdigest() != TARGET_SHA: raise ValueError('Wrong donor ROM')
    mapped, enums = mapping(source)
    ability_map, move_map = name_map(source,'ABILITY'), name_map(source,'MOVE')
    ability_map.update({'none':'ABILITY_NONE','-------':'ABILITY_NONE'})
    for short, full in {'GorillaTacti':'GORILLA_TACTICS','PwrOfAlchemy':'POWER_OF_ALCHEMY','PrimrdialSea':'PRIMORDIAL_SEA','ScreenCleanr':'SCREEN_CLEANER','CuriusMedicn':'CURIOUS_MEDICINE','NeutrlzngGas':'NEUTRALIZING_GAS','WandrngSprit':'WANDERING_SPIRIT'}.items():
        ability_map[norm(short)] = 'ABILITY_'+full
    move_map[norm('SmellngSalts')] = 'MOVE_SMELLING_SALTS'
    assets = {}; catalog = []; errors = []
    u16 = lambda p:struct.unpack_from('<H',rom,p)[0]
    u32 = lambda p:struct.unpack_from('<I',rom,p)[0]
    for i in range(1483):
        p = 0x6c7f00+i*84
        if not rom[p]: continue
        key = mapped[i]; abilities = []
        for a in struct.unpack_from('<3H',rom,p+24):
            name = decode(rom[0x3ce1d5+a*13:0x3ce1d5+(a+1)*13])
            if a == 0: abilities.append('ABILITY_NONE')
            elif norm(name) in ability_map: abilities.append(ability_map[norm(name)])
            else: errors.append(f'{key}: unknown ability {a} {name}')
        learnset = []; q = u32(p+72)-0x08000000
        for j in range(256):
            if q < 0: break
            move,level = struct.unpack_from('<HH',rom,q+j*4)
            if move == 65535: break
            name = decode(rom[0x3b57a8+move*13:0x3b57a8+(move+1)*13])
            if norm(name) in move_map: learnset.append([move_map[norm(name)],level])
            else: errors.append(f'{key}: unknown move {move} {name}')
        else: raise ValueError('Unterminated learnset')
        for kind, table in [('front',0x39be3c),('back',0x389f5c),('palette',0x38cdb4)]:
            raw, compressed = lz77(rom,u32(table+i*4))
            # Keep complete sprite frame streams, pad shortened palettes to 16
            # colors. GBA DMA palettes are always exactly 32 bytes.
            if kind == 'palette': assets[f'{i}/{kind}.gbapal'] = raw[:32].ljust(32,b'\0')
            else: assets[f'{i}/{kind}.4bpp.lz'] = compressed.ljust((len(compressed)+3)//4*4,b'\0')
        catalog.append(dict(donor_id=i,species=key,species_id=enums[key],national_dex=u16(p+44),stats=list(rom[p:p+6]),types=[TYPES[t] for t in rom[p+6:p+8]],catch_rate=rom[p+8],exp_yield=u16(p+10),ev_yields=[(u16(p+12)>>(2*j))&3 for j in range(6)],gender=rom[p+18],egg_cycles=rom[p+19],friendship=rom[p+20],growth=rom[p+21],egg_groups=list(rom[p+22:p+24]),abilities=abilities,learnset=learnset,mega=bool(u32(p+68)&0x40000)))
    if errors: raise ValueError('\n'.join(sorted(set(errors))))
    ids = [r['species_id'] for r in catalog]
    if len(ids) != len(set(ids)): raise ValueError('Duplicate mapped species')
    report = dict(donor_sha256=TARGET_SHA,species_count=len(catalog),base_species_count=len({r['national_dex'] for r in catalog}),form_count=len(catalog)-649,mega_count=sum(r['mega'] for r in catalog),missing_base_species=list(range(650,1026)),missing_mega_species=['Diancie'],catalog=catalog)
    assets['catalog.json'] = (json.dumps(report,indent=2)+'\n').encode()
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for name,data in sorted(assets.items()):
            info = zipfile.ZipInfo(name,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o644<<16; archive.writestr(info,data)
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    report = extract(args.rom.read_bytes(),args.source,args.output)
    print(json.dumps({k:v for k,v in report.items() if k != 'catalog'},indent=2))
