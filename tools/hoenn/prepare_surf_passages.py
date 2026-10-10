"""Remove obsolete coastal rock banks and scale ordinary trainer parties."""
import argparse, hashlib, json, re, struct
from pathlib import Path
from prepare_remote_islands import PRIOR, LAYER as REMOTE

LAYER = 'surf-passages'
PRIOR = PRIOR + [REMOTE]
ROCKS = {
    'emerald': {0x150, 0x151, 0x158, 0x159, 0x162, 0x163, 0x168, 0x169, 0x16A, 0x16B},
    'frlg': {0x110, 0x111, 0x118, 0x119, 0x112, 0x11A},
}

def prepare(source):
    source = Path(source); marker = source / ('.journey-' + LAYER)
    if marker.exists():
        report = json.loads(marker.read_text())
        for p, h in (report['prepared_sha256'] | report['preserved_native_sha256']).items():
            assert hashlib.sha256((source / p).read_bytes()).hexdigest() == h, p
        return report
    expected = dict(json.loads((source / '.source-acquired.json').read_text())['sha256'])
    for layer in PRIOR:
        expected.update(json.loads((source / ('.journey-' + layer)).read_text())['prepared_sha256'])
    outputs, originals, preserved = {}, {}, {}
    def read(p):
        raw = (source / p).read_bytes(); h = hashlib.sha256(raw).hexdigest()
        assert h == expected[p], p
        preserved[p] = h
        return raw
    def stage(p, raw):
        originals[p] = hashlib.sha256(read(p)).hexdigest(); preserved.pop(p, None)
        outputs[p] = raw if isinstance(raw, bytes) else raw.encode()
    layouts = {l['id']: l for l in json.loads(read('data/layouts/layouts.json'))['layouts']}
    maps = {p.parent.name: json.loads(read(str(p.relative_to(source)))) for p in (source / 'data/maps').glob('*/map.json')}
    by_id = {m['id']: n for n, m in maps.items()}
    rows = []
    for n, m in sorted(maps.items()):
        l = layouts[m['layout']]; version = l['layout_version']
        if m['map_type'] not in ['MAP_TYPE_OCEAN_ROUTE', 'MAP_TYPE_ROUTE', 'MAP_TYPE_CITY', 'MAP_TYPE_TOWN']:
            continue
        # General outdoor tiles only: these IDs mean different things indoors.
        if l['primary_tileset'] not in ['gTileset_General', 'gTileset_General_Frlg']:
            continue
        w, h = l['width'], l['height']; path = l['blockdata_filepath']
        v = list(struct.unpack('<'+'H'*(w*h), read(path)))
        connected = {side: set() for side in ['up','down','left','right']}
        for c in m.get('connections') or []:
            if c['direction'] not in connected: continue
            dst = layouts[maps[by_id[c['map']]]['layout']]
            extent = dst['width'] if c['direction'] in ['up','down'] else dst['height']
            connected[c['direction']].update(range(c['offset'], c['offset'] + extent))
        changed = []
        for i, t in enumerate(v):
            if t & 1023 not in ROCKS[version] or t >> 12 not in [0, 1] or not t & 0xC00:
                continue
            x, y = i % w, i // w
            edges = [('left',y,x<2),('right',y,x>=w-2),('up',x,y<2),('down',x,y>=h-2)]
            # Retain the complete outer reef where the world really ends.
            if any(on and pos not in connected[side] for side,pos,on in edges): continue
            # New seas already have sparse decorative reefs. Clear their seams;
            # native routes retain old enclosing rock banks, which all go away.
            if n.startswith('Journey') and min(x,y,w-1-x,h-1-y) >= 3: continue
            v[i] = 0x112B if version == 'frlg' else 0x1170
            changed.append(dict(x=x,y=y,old=t,new=v[i]))
        # Never leave half a formerly complete boulder at the map boundary.
        old = struct.unpack('<'+'H'*(w*h), (source/path).read_bytes())
        patterns = ([[0x150,0x151,0x158,0x159],[0x162,0x163,0x16A,0x16B],[0x168,0x169,0x16A,0x16B]]
                    if version == 'emerald' else [[0x110,0x111,0x118,0x119],[0x112,0x111,0x11A,0x119]])
        changed_ids = {e['y']*w+e['x'] for e in changed}
        for y in range(h-1):
            for x in range(w-1):
                cells = [y*w+x,y*w+x+1,(y+1)*w+x,(y+1)*w+x+1]
                if [old[i]&1023 for i in cells] in patterns and 0 < len(changed_ids.intersection(cells)) < 4:
                    for i in cells: v[i]=old[i]; changed_ids.discard(i)
        changed = [e for e in changed if e['y']*w+e['x'] in changed_ids]
        if changed:
            stage(path,struct.pack('<'+'H'*len(v),*v))
            rows.append(dict(map=n,tiles=changed,connections_unchanged=True))
    p = 'src/journey_gym_scaling.c'; text = read(p).decode()
    assert text.count('return originalLevel;') == 1
    text = text.replace('#include "journey_gym_scaling.h"', '#include "journey_gym_scaling.h"\n#include "journey_wild.h"')
    text = text.replace('return originalLevel;', 'return JourneyWildNormalizeLevel(originalLevel);')
    stage(p,text)
    # Region selection is a visible New Game step, not a title-screen shortcut.
    p='include/constants/vars.h';text=read(p).decode()
    text=text.replace('#define VAR_UNUSED_0x40FD', '#define VAR_JOURNEY_START_REGION 0x40FD\n#define VAR_UNUSED_0x40FD',1);stage(p,text)
    p='include/constants/script_menu.h';text=read(p).decode()
    # Append to the enum so all existing script-menu IDs stay unchanged.
    assert text.count('    MULTI_LAVENDER_SEVII8,')==1
    text=text.replace('    MULTI_LAVENDER_SEVII8,','    MULTI_LAVENDER_SEVII8,\n    MULTI_JOURNEY_START_REGIONS,\n    MULTI_JOURNEY_START_SEVII,');stage(p,text)
    p='src/data/script_menu.h';text=read(p).decode()
    menu='static const struct MenuAction sJourneyStartRegions[] = {\n    {COMPOUND_STRING("HOENN")},\n    {COMPOUND_STRING("KANTO")},\n    {COMPOUND_STRING("SEVII ISLANDS")},\n};\n'
    menu+='static const struct MenuAction sJourneyStartSevii[] = {\n'+''.join('    {COMPOUND_STRING("'+s+' ISLAND")},\n' for s in ['ONE','TWO','THREE','FOUR','FIVE','SIX','SEVEN'])+'};\n'
    text=text.replace('static const struct MultichoiceListStruct sMultichoiceLists[] =',menu+'\nstatic const struct MultichoiceListStruct sMultichoiceLists[] =')
    text=text.replace('[MULTI_JOURNEY_START_HOENN]', '[MULTI_JOURNEY_START_REGIONS] = MULTICHOICE(sJourneyStartRegions),\n    [MULTI_JOURNEY_START_SEVII] = MULTICHOICE(sJourneyStartSevii),\n    [MULTI_JOURNEY_START_HOENN]',1)
    for i,s in enumerate(['ONE','TWO','THREE','FOUR','FIVE','SIX','SEVEN'],1):text=text.replace('"Ilha '+str(i)+'"','"'+s+' ISLAND"')
    # Mainland menu has nine entries; the seven island entries get their own menu.
    start=text.index('static const struct MenuAction sJourneyStartCities[]')
    end=text.index('};',start)
    body=text[start:end]
    body=re.sub(r'    \{COMPOUND_STRING\("(?:ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN) ISLAND"\)\},\n','',body)
    text=text[:start]+body+text[end:];stage(p,text)
    p='src/journey_birth.c';text=read(p).decode()
    text=text.replace('void JourneyBirthChooseCity(void)', '''void JourneyBirthSelectRegion(void)
{
    u16 region = gSpecialVar_Result;
    if (region > 2) region = 0;
    VarSet(VAR_JOURNEY_START_REGION, region);
    gSaveBlock2Ptr->playerRegion = region == 0 ? REGION_HOENN : REGION_KANTO;
}

void JourneyBirthChooseCity(void)''')
    text=text.replace('if (choice >= (hoenn ? 15 : 16)) choice = 0;', 'if (VarGet(VAR_JOURNEY_START_REGION) == 2)\n    {\n        if (choice >= 7) choice = 0;\n        choice += 9;\n    }\n    else if (choice >= (hoenn ? 15 : 16)) choice = 0;')
    stage(p,text)
    p='include/journey_birth.h';text=read(p).decode().replace('void JourneyBirthChooseCity(void);','void JourneyBirthSelectRegion(void);\nvoid JourneyBirthChooseCity(void);');stage(p,text)
    p='data/specials.inc';stage(p,read(p).decode()+'\n\tdef_special JourneyBirthSelectRegion\n')
    p='data/scripts/journey_birth.inc';text=read(p).decode()
    text=text.replace('\tspecial JourneyBirthRegion\n\tgoto_if_eq VAR_RESULT, TRUE, JourneyBirth_ChooseKanto', '\tmultichoice 0, 0, MULTI_JOURNEY_START_REGIONS, TRUE\n\tspecial JourneyBirthSelectRegion\n\tgoto_if_eq VAR_JOURNEY_START_REGION, 2, JourneyBirth_ChooseSevii\n\tgoto_if_eq VAR_JOURNEY_START_REGION, 1, JourneyBirth_ChooseKanto',1)
    text=text.replace('JourneyBirth_ConfirmCity::','\tgoto JourneyBirth_ConfirmCity\nJourneyBirth_ChooseSevii::\n\tmultichoicegrid 0, 0, MULTI_JOURNEY_START_SEVII, 2, TRUE\nJourneyBirth_ConfirmCity::',1)
    # Native grid menus require complete rows: 9 mainland towns use 3 columns;
    # seven islands use a vertical menu so the last island stays selectable.
    text=text.replace('MULTI_JOURNEY_START_CITIES, 2, TRUE','MULTI_JOURNEY_START_CITIES, 3, TRUE')
    text=text.replace('multichoicegrid 0, 0, MULTI_JOURNEY_START_SEVII, 2, TRUE','multichoice 0, 0, MULTI_JOURNEY_START_SEVII, TRUE')
    text=text.replace('Choose your starting city.', 'Choose your starting region.')
    text=text.replace('Let us travel to your new home!', 'Then choose your home town!');stage(p,text)
    p='data/text/birch_speech.inc';text=read(p).decode()
    text=text.replace("You're {PLAYER}{KUN} who's moving to my", "You're {PLAYER}{KUN}, ready to explore")
    text=text.replace('hometown of LITTLEROOT.', 'KANTO, HOENN and the SEVII ISLANDS.')
    text=text.replace('Come see me in my POKéMON LAB.', 'Choose where your journey begins.');stage(p,text)
    # The default title is shared by all starting regions; its banner no longer
    # advertises Emerald as the only campaign.
    stage('graphics/title_screen/emerald_version.png',(Path(__file__).parent/'assets/journey_version.png').read_bytes())
    for p in ['src/journey_campaign_gates.c','src/journey_wild.c','src/journey_pwt.c','src/journey_family.c',
              'src/data/trainers.party','data/layouts/JourneyRoute12Shipyard/map.bin']:
        read(p)
    for p, raw in outputs.items(): (source / p).write_bytes(raw)
    report = dict(prepared_sha256={p:hashlib.sha256(b).hexdigest() for p,b in outputs.items()},
                  original_sha256=originals,preserved_native_sha256=preserved,maps=rows,
                  ordinary_trainer_levels='party_mean_minus_5_to_plus_2_clamped_1_100',
                  explicit_start_regions=['HOENN','KANTO','SEVII ISLANDS'],start_cities=[15,9,7],
                  regional_gym_rank_levels_unchanged=True,waterfall_dive_and_map_connections_unchanged=True)
    marker.write_text(json.dumps(report,indent=2)+'\n')
    return report

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--source',type=Path,required=True)
    print(json.dumps(prepare(p.parse_args().source),indent=2))
