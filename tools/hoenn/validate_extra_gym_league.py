"""Exercise real permissions with complete prior campaigns and missing badges."""
import re
import struct
import subprocess

def check_leagues(ctx):
    local=dict(ctx)
    src=ctx['source'];root=ctx['ROOT'];native=ctx['native'];rawflag=ctx['rawflag']
    prefix=(root/'tools/hoenn/validate_campaign_matrix.py').read_text().split('constants = ',1)[1].split('\nchecks = []')[0]
    exec(compile('constants = '+prefix,'extra-gym-campaign-fixture','exec'),local)
    local['reset_aqua']();local['reset_native']()
    for name in local['completion']:rawflag(local['flag_id'](name),True)
    rawflag(local['flag_id']('FLAG_SYS_WEATHER_CTRL'),False)
    for t in local['stories']['trainers']:rawflag(0x500+t['id'],True)
    native('VarSet',0x409F,3);native('VarSet',0x40FE,7)
    constants=(src/'src/journey_crossover.c').read_text()
    var=int(re.search(r'#define JOURNEY_RIVAL_VISITS\s+(0x\w+)',constants)[1],16)
    native('VarSet',var,0xFFF)
    assert native('JourneyPendingCampaignEvent',1)==native('JourneyPendingCampaignEvent',0)==0
    assert native('JourneyCrossoverComplete')
    def permission(kanto):
        native('JourneyKantoLeaguePermission' if kanto else 'JourneyHoennLeaguePermission')
        return ctx['lib'].read16(ctx['s']['gSpecialVar_Result'])
    ctx['set_badges'](24)
    assert permission(True)==permission(False)==1
    cases=[]
    for missing in ctx['all_badges']:
        rawflag(missing,False)
        assert native('JourneyTotalBadgeCount')==23
        assert permission(True)==permission(False)==0
        cases.append(dict(missing_badge=missing,both_denied=True));rawflag(missing,True)
    for count in [0,8,16,17,18,21,22,23]:
        ctx['set_badges'](count);assert permission(True)==permission(False)==0
    ctx['set_badges'](24)
    native('VarSet',0x40FE,6);assert permission(True)==permission(False)==0
    native('VarSet',0x40FE,7)
    rawflag(local['flag_id']('FLAG_RESCUED_MR_FUJI'),False)
    assert permission(True)==permission(False)==0
    rawflag(local['flag_id']('FLAG_RESCUED_MR_FUJI'),True)
    assert permission(True)==permission(False)==1
    physical=[]
    for kanto,name,x in [(True,'IndigoPlateau_PokemonCenter_1F_Frlg',4),(False,'EverGrandeCity_PokemonLeague_1F',9)]:
        ctx['set_badges'](23);ctx['warp'](name,x,3);ctx['step'](40,64);ctx['press'](1);ctx['step'](180)
        ctx['picture'](('kanto' if kanto else 'hoenn')+'-24-badges-required');ctx['finish']()
        assert ctx['location']()==ctx['map_id'](name) and ctx['position']()[1]>=3
        assert not permission(kanto)
        ctx['set_badges'](24);assert permission(kanto)
        physical.append(dict(map=name,actual_entry_denied_at_23=True,permission_at_24=True))
    return dict(missing_badge_cases=cases,thresholds=[0,8,16,17,18,21,22,23,24],both_leagues_require_24=True,
        old_story_and_galactic_completion_still_required=True,physical=physical,campaign_completion_is_fixture=True)
