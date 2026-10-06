"""Pinned source overlay: road access, order-based gyms, Blue and opposite-sex rival."""
import json
import re
from pathlib import Path
import shutil

GYMS=['PewterCity_Gym','CeruleanCity_Gym','VermilionCity_Gym','CeladonCity_Gym','FuchsiaCity_Gym','SaffronCity_Gym','CinnabarIsland_Gym','ViridianCity_Gym']

def apply(source):
    files=Path(__file__).resolve().parent
    def replace(relative,old,new):
        p=source/relative;s=p.read_text()
        if old not in s:raise ValueError(f'Missing {old[:70]} in {relative}')
        p.write_text(s.replace(old,new,1))
    def edit_map(name,edit):
        p=source/f'data/maps/{name}/map.json';m=json.loads(p.read_text());edit(m);p.write_text(json.dumps(m,indent=2)+'\n')
    for name,dest in [('open_world.h','include/open_world.h'),('open_world.c','src/open_world.c'),('open_world.inc','data/scripts/open_world.inc')]:shutil.copyfile(files/name,source/dest)
    with (source/'data/event_scripts.s').open('a') as f:f.write('\n\t.include "data/scripts/open_world.inc"\n')
    replace('data/specials.inc','gSpecialsEnd::','\tdef_special OpenWorld_CountBadges\ngSpecialsEnd::')
    replace('src/battle_main.c','#include "global.h"','#include "global.h"\n#include "open_world.h"')
    p=source/'src/battle_main.c';s=p.read_text();assert s.count('partyData[i].species, partyData[i].lvl, fixedIV')==4
    p.write_text(s.replace('partyData[i].species, partyData[i].lvl, fixedIV','partyData[i].species, OpenWorld_GymLevel(trainerNum, i, partyData[i].lvl), fixedIV'))
    # Blue's new trainer entry is confined to the former gym slot. Boss Giovanni
    # parties/scripts in Rocket Hideout and Silph Co remain intact.
    p=source/'src/data/trainers.h';s=p.read_text();entry=re.search(r'    \[TRAINER_LEADER_GIOVANNI\] = \{.*?\n    \},',s,re.S).group()
    blue=entry.replace('TRAINER_PIC_LEADER_GIOVANNI','TRAINER_PIC_RIVAL_LATE').replace('_("GIOVANNI")','_("BLUE")').replace('NO_ITEM_CUSTOM_MOVES(sParty_LeaderGiovanni)','NO_ITEM_DEFAULT_MOVES(sParty_OpenWorldBlue)')
    p.write_text(s.replace(entry,blue))
    with (source/'src/data/trainer_parties.h').open('a') as f:
        f.write('\nstatic const struct TrainerMonNoItemDefaultMoves sParty_OpenWorldBlue[] = {\n'+''.join('    {.iv=200, .lvl=%d, .species=SPECIES_%s},\n' % (lv,sp) for sp,lv in [('EXEGGUTOR',56),('RHYDON',58),('MACHAMP',56),('GYARADOS',58),('ARCANINE',58),('PIDGEOT',60)])+'};\n')
    # New fixed graphics ID keeps Blue separate from the old rival's graphics ID.
    replace('include/constants/event_objects.h','#define NUM_OBJ_EVENT_GFX     153','#define OBJ_EVENT_GFX_GYM_BLUE 153\n#define NUM_OBJ_EVENT_GFX     154')
    replace('src/data/object_events/object_event_graphics_info_pointers.h','    [OBJ_EVENT_GFX_BLUE]', '    [OBJ_EVENT_GFX_GYM_BLUE] = &gObjectEventGraphicsInfo_Blue,\n    [OBJ_EVENT_GFX_BLUE]')
    replace('src/event_object_movement.c','const struct ObjectEventGraphicsInfo *GetObjectEventGraphicsInfo(u8 graphicsId)\n{','const struct ObjectEventGraphicsInfo *GetObjectEventGraphicsInfo(u8 graphicsId)\n{\n    if (graphicsId == OBJ_EVENT_GFX_BLUE)\n        graphicsId = gSaveBlock2Ptr->playerGender == MALE ? OBJ_EVENT_GFX_GREEN_NORMAL : OBJ_EVENT_GFX_RED_NORMAL;')
    edit_map('ViridianCity_Gym',lambda m:[o.update(graphics_id='OBJ_EVENT_GFX_GYM_BLUE') for o in m['object_events'] if o['graphics_id']=='OBJ_EVENT_GFX_GIOVANNI'])
    # Portraits use the opposite-sex player art at every rival/champion encounter.
    for p in (source/'src').glob('*.c'):
        if p.name=='open_world.c':continue
        s=p.read_text();new=re.sub(r'gTrainers\[([^\]\n]+)\]\.trainerPic',r'OpenWorld_TrainerPic(\1)',s)
        if new!=s:p.write_text(new.replace('#include "global.h"','#include "global.h"\n#include "open_world.h"',1))
    replace('src/oak_speech.c','LoadPalette(sOakSpeech_Rival_Pal, BG_PLTT_ID(6), sizeof(sOakSpeech_Rival_Pal));\n        LZ77UnCompVram(sOakSpeech_Rival_Tiles, (void *)VRAM + 0x600 + tileOffset);','if (gSaveBlock2Ptr->playerGender == MALE) {\n            LoadPalette(sOakSpeech_Leaf_Pal, BG_PLTT_ID(6), sizeof(sOakSpeech_Leaf_Pal));\n            LZ77UnCompVram(sOakSpeech_Leaf_Tiles, (void *)VRAM + 0x600 + tileOffset);\n        } else {\n            LoadPalette(sOakSpeech_Red_Pal, BG_PLTT_ID(6), sizeof(sOakSpeech_Red_Pal));\n            LZ77UnCompVram(sOakSpeech_Red_Tiles, (void *)VRAM + 0x600 + tileOffset);\n        }')
    p=source/'src/naming_screen.c';s=p.read_text();start=s.index('static void NamingScreen_CreateRivalIcon(void)\n{');end=s.index('\n}\n',start)+3
    s=s[:start]+'''static void NamingScreen_CreateRivalIcon(void)
{
    u8 graphics = gSaveBlock2Ptr->playerGender == MALE ? OBJ_EVENT_GFX_GREEN_NORMAL : OBJ_EVENT_GFX_RED_NORMAL;
    u8 sprite = CreateObjectGraphicsSprite(graphics, SpriteCallbackDummy, 56, 37, 0);
    gSprites[sprite].oam.priority = 3;
    StartSpriteAnim(&gSprites[sprite], ANIM_STD_GO_SOUTH);
}
'''+s[end:];p.write_text(s)
    # Blue remains in his gym after defeat and never concludes a Rocket quest.
    p=source/'data/maps/ViridianCity_Gym/scripts.inc';s=p.read_text();s=re.sub(r'^\tfamechecker FAMECHECKER_GIOVANNI[^\n]*\n','',s,flags=re.M)
    s=s.replace('\tsetflag FLAG_HIDE_MISC_KANTO_ROCKETS\n','').replace('\tsetvar VAR_MAP_SCENE_ROUTE22, 3\n','')
    s=s.replace('\tclosemessage\n\tfadescreen FADE_TO_BLACK\n\tremoveobject LOCALID_VIRIDIAN_GIOVANNI\n\tfadescreen FADE_FROM_BLACK\n','')
    p.write_text(s)
    p=source/'data/maps/ViridianCity_Gym/text.inc';s=p.read_text()
    texts={'GiovanniIntro':'BLUE: Eu sou o novo líder\\ndeste ginásio.\\pMinha equipe está pronta para\\no seu próximo desafio!$', 'GiovanniPostBattle':'BLUE: Boa batalha!\\nContinue sua jornada.\\pPara entrar na LIGA, você precisa\\ndas oito insígnias.$', 'ExplainEarthBadgeTakeThis':'BLUE: Esta é a EARTHBADGE!\\pTambém tenho uma TM para você.\\nContinue desafiando os líderes!$', 'ExplainTM26':'TM26 contém EARTHQUAKE.\\nÉ um poderoso golpe de terra.$', 'GymGuyAdvice':'BLUE usa uma equipe variada.\\pA dificuldade depende de quantas\\ninsígnias você já conquistou.$', 'GymGuyPostVictory':'Você venceu BLUE!\\nContinue buscando as insígnias.$', 'SamuelPostBattle':'A LIGA exige as oito insígnias.\\nNenhum ginásio pode ficar de fora!$'}
    for label,text in texts.items():s=re.sub(r'(ViridianCity_Gym_Text_'+label+r'::\n).*?(?=\n\w+::|\Z)',lambda m:m.group(1)+'    .string "'+text+'"\n',s,flags=re.S)
    p.write_text(s.replace('GIOVANNI','BLUE').replace('LEADER: ?','LEADER: BLUE'))
    # All eight independent leaders share the first-badge flute reward and retry.
    trainers=[];trainerdata=(source/'src/data/trainers.h').read_text();partydata=(source/'src/data/trainer_parties.h').read_text()
    ids={n:int(v) for n,v in re.findall(r'#define (TRAINER_\w+)\s+(\d+)',(source/'include/constants/opponents.h').read_text())}
    for gym in GYMS:
        p=source/f'data/maps/{gym}/scripts.inc';s=p.read_text()
        lead=re.search(r'^(\w+::\n)(?=\t(?:famechecker[^\n]*\n\t)?trainerbattle_single TRAINER_LEADER_)',s,re.M)
        if not lead:raise ValueError('Leader entry missing '+gym)
        s=s[:lead.end()]+ '\tcall OpenWorld_FirstBadgeReward\n'+s[lead.end():]
        s=re.sub(r'(\tsetflag FLAG_BADGE\d\d_GET\n)',r'\1\tcall OpenWorld_FirstBadgeReward\n',s)
        p.write_text(s)
        for trainer in dict.fromkeys(re.findall(r'trainerbattle_single (TRAINER_\w+)',s)):
            entry=re.search(r'\['+trainer+r'\] = \{(.*?)\n    \},',trainerdata,re.S).group(1)
            party=re.search(r'\.party = \w+\((\w+)\)',entry).group(1)
            block=re.search(r'\b'+party+r'\[\] = \{(.*?)\n\};',partydata,re.S).group(1)
            levels=[int(l) for l in re.findall(r'\.lvl\s*=\s*(\d+)',block)]
            species=re.findall(r'\.species\s*=\s*SPECIES_(\w+)',block)
            trainers.append(dict(name=trainer,id=ids[trainer],gym=gym,highest=max(levels),levels=levels,species=species,leader=trainer.startswith('TRAINER_LEADER_'),victory_script=(re.search(r'trainerbattle_single '+trainer+r', [^,]+, [^,]+, (\w+)',s).group(1) if trainer.startswith('TRAINER_LEADER_') else None)))
    (source/'include/open_world_trainers.h').write_text('static const struct GymTrainer sGymTrainers[] = {\n'+''.join('    {%s,%d,%s},\n' % (t['name'],t['highest'],'TRUE' if t['leader'] else 'FALSE') for t in trainers)+'};\n')
    # No flute from Fuji before the first gym: rescue events remain independent.
    replace('data/maps/LavenderTown_VolunteerPokemonHouse/scripts.inc','\tmsgbox LavenderTown_VolunteerPokemonHouse_Text_IdLikeYouToHaveThis','\tgoto OpenWorld_FujiNoFlute\n\tmsgbox LavenderTown_VolunteerPokemonHouse_Text_IdLikeYouToHaveThis')
    replace('data/maps/ViridianCity/scripts.inc','\tsetworldmapflag FLAG_WORLD_MAP_VIRIDIAN_CITY','\tsetworldmapflag FLAG_WORLD_MAP_VIRIDIAN_CITY\n\tsetvar VAR_MAP_SCENE_VIRIDIAN_CITY_GYM_DOOR, 1\n\tcall_if_eq VAR_MAP_SCENE_VIRIDIAN_CITY_OLD_MAN, 0, OpenWorld_MoveOldMan')
    with (source/'data/maps/ViridianCity/scripts.inc').open('a') as f:f.write('\nOpenWorld_MoveOldMan::\n\tsetvar VAR_MAP_SCENE_VIRIDIAN_CITY_OLD_MAN, 1\n\treturn\n')
    edit_map('ViridianCity',lambda m:m.update(coord_events=[e for e in m['coord_events'] if e['script']!='ViridianCity_EventScript_RoadBlocked']))
    edit_map('PewterCity',lambda m:m.update(coord_events=[e for e in m['coord_events'] if 'GymGuideTrigger' not in e['script']]))
    replace('data/maps/CeruleanCity/scripts.inc','\tcall_if_unset FLAG_GOT_SS_TICKET, CeruleanCity_EventScript_BlockExits','\t@ Road exits remain open before Bill and the S.S. Ticket.')
    edit_map('CeruleanCity',lambda m:[o.update(x=2,y=13) for o in m['object_events'] if o.get('local_id')=='LOCALID_CERULEAN_CAVE_GUARD'])
    for name in ['Route5_SouthEntrance','Route6_NorthEntrance','Route7_EastEntrance','Route8_WestEntrance']:
        edit_map(name,lambda m:m.update(coord_events=[]))
    edit_map('SaffronCity',lambda m:[o.update(flag='FLAG_0x8E2') for o in m['object_events'] if o.get('graphics_id')=='OBJ_EVENT_GFX_ROCKET_M'])
    edit_map('CinnabarIsland',lambda m:m.update(coord_events=[e for e in m['coord_events'] if e['script']!='CinnabarIsland_EventScript_GymDoorLocked']))
    replace('data/maps/CinnabarIsland/scripts.inc','\tcall CinnabarIsland_EventScript_CheckUnlockGym','\tsetvar VAR_TEMP_1, 1')
    for name in ['Route16_NorthEntrance_1F','Route18_EastEntrance_1F']:
        edit_map(name,lambda m:m.update(coord_events=[e for e in m['coord_events'] if 'NeedBike' not in e['script']]))
    replace('src/field_specials.c','#include "global.h"','#include "global.h"\n#include "item.h"')
    replace('src/field_specials.c','void ForcePlayerOntoBike(void)\n{','void ForcePlayerOntoBike(void)\n{\n    if (!CheckBagHasItem(ITEM_BICYCLE, 1)) return;')
    # Exterior Sevii entrance obstacles are removed without completing gem quests.
    replace('data/maps/MtEmber_Exterior/scripts.inc','\tcall_if_ge VAR_MAP_SCENE_ONE_ISLAND_POKEMON_CENTER_1F, 4, MtEmber_Exterior_EventScript_OpenCave','\tcall MtEmber_Exterior_EventScript_OpenCave')
    edit_map('MtEmber_Exterior',lambda m:[o.update(x=44+i,y=40) for i,o in enumerate([o for o in m['object_events'] if o.get('local_id') in ['LOCALID_MT_EMBER_GRUNT1','LOCALID_MT_EMBER_GRUNT2']])])
    replace('data/maps/SixIsland_RuinValley/scripts.inc','\tcall_if_set FLAG_USED_CUT_ON_RUIN_VALLEY_BRAILLE, SixIsland_RuinValley_EventScript_OpenDottedHoleDoor','\tsetobjectxyperm LOCALID_RUIN_VALLEY_SCIENTIST, 26, 25\n\tcall SixIsland_RuinValley_EventScript_OpenDottedHoleDoor')
    # Keep Route22/23 badge checkpoints unchanged; also guard the League doorway
    # against arriving by Surf/other entrances before obtaining all eight badges.
    replace('data/maps/IndigoPlateau_PokemonCenter_1F/scripts.inc','\tsetrespawn HEAL_LOCATION_INDIGO_PLATEAU','\tsetrespawn HEAL_LOCATION_INDIGO_PLATEAU\n\tcall OpenWorld_LeagueTransition')
    replace('data/maps/IndigoPlateau_PokemonCenter_1F/scripts.inc','IndigoPlateau_PokemonCenter_1F_EventScript_DoorGuard::\n\tlock\n\tfaceplayer','IndigoPlateau_PokemonCenter_1F_EventScript_DoorGuard::\n\tlock\n\tfaceplayer\n\tspecial OpenWorld_CountBadges\n\tgoto_if_lt VAR_RESULT, 8, OpenWorld_LeagueBlocked')
    # Report is emitted alongside the ROM and drives exhaustive party-level tests.
    report=dict(ace_levels=[14,21,28,35,42,48,54,60],trainers=trainers,first_badge_item='ITEM_POKE_FLUTE',league_requires_badges=8,rival='opposite-sex player sprite',viridian_leader='BLUE')
    (source/'.open-world-prepared').write_text(json.dumps(report,indent=2)+'\n')
