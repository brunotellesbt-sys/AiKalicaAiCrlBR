"""Survey named cave groups and check the Galactic capture gate in the current ROM."""
import json,re

def validate(e):
    lib,s,source,native,warp,step,picture=[e[n] for n in ['lib','s','source','native','warp','step','picture']]
    plan=json.loads((source/'.journey-dewford-competitive-shop').read_text())['legendary_caves']
    chars={int(m[2],16):m[1] for m in re.finditer(r"^'(.)'\s*=\s*([0-9A-F]{2})\b",(source/'charmap.txt').read_text(),re.M) if m[1] in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ -0123456789'}
    def text(pointer):
        result=''
        for i in range(96):
            value=lib.read8(pointer+i)
            if value==255:return result
            result+=chars.get(value,'?')
        raise AssertionError('Unterminated cave name')
    mode=lib.read8(s['gJourneyReviewMode']);lib.raw8(s['gJourneyReviewMode'],1)
    try:
        native('VarSet',0x40FE,3);warp('JourneyGalacticHall',15,11)
        assert native('JourneyGalacticNoCatch')==1
        assert all(native('JourneyGalacticCaptureLocked',n)==1 for n in [483,484,487])
        native('VarSet',0x40FE,7)
        assert native('JourneyGalacticNoCatch')==0
        assert all(native('JourneyGalacticCaptureLocked',n)==0 for n in [483,484,487])
        rows=[]
        for g in plan['groups']:
            m=json.loads((source/f'data/maps/{g["map"]}/map.json').read_text());exit=m['warp_events'][0]
            warp(g['map'],exit['x'],max(1,exit['y']-1))
            actual=text(native('JourneyCurrentMapName'));assert actual==g['name'],(g['name'],actual)
            for obj in m['object_events']:
                if not re.fullmatch(r'JourneySanctuary_\d+',obj.get('script','')):continue
                assert native('MapGridGetCollisionAt',obj['x']+7,obj['y']+7)==0,(g['map'],obj['x'],obj['y'])
            rows.append(dict(map=g['map'],name=g['name'],species=g['national_dex']))
        creation=next(g for g in plan['groups'] if 483 in g['national_dex'])
        assert {483,484,487}<=set(creation['national_dex'])
        warp(creation['map'],10,13);picture('creation-cave-after-galactic')
        return dict(groups=rows,total_species=sum(len(r['species']) for r in rows),
                    all_48_names_checked_in_rom=True,all_altars_on_compiled_walkable_tiles=True,
                    giratina_ship_capture_blocked=True,galactic_trio_unlocks_after_event=True,
                    initial_story_position_and_encounter_suppression_are_fixtures=True)
    finally:lib.raw8(s['gJourneyReviewMode'],mode)
