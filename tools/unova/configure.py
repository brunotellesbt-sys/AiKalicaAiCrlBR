"""Release configuration and read-only ABI metadata for emulator validation."""
import json

def apply(source):
    def edit(path,old,new):
        p = source/path; s = p.read_text()
        if old not in s: raise ValueError(f'Missing configuration {path}: {old}')
        p.write_text(s.replace(old,new,1))
    for name in ['DEBUG_OVERWORLD_MENU','DEBUG_BATTLE_MENU','DEBUG_POKEMON_SPRITE_VISUALIZER']:
        p = source/'include/config/debug.h';s = p.read_text()
        import re
        s,n = re.subn(r'(#define '+name+r'\s+)TRUE',r'\1FALSE',s)
        if n != 1: raise ValueError('Debug configuration changed')
        p.write_text(s)
    edit('include/config/overworld.h','OW_FIELD_MOVES_WITHOUT_HMS          TRUE','OW_FIELD_MOVES_WITHOUT_HMS          FALSE')
    edit('include/config/pokemon.h','P_GENDER_DIFFERENCES            TRUE','P_GENDER_DIFFERENCES            FALSE')
    edit('include/config/species_enabled.h','#define P_GEN_9_MEGA_EVOLUTIONS          P_MEGA_EVOLUTIONS','#define P_GEN_9_MEGA_EVOLUTIONS          FALSE')
    edit('data/specials.inc','gSpecialsEnd::','\tdef_special UnovaInspectLayout\ngSpecialsEnd::')
    write_layout(source)

def write_layout(source):
    layout = {
        'save_flags':'offsetof(struct SaveBlock1, flags)',
        'save_vars':'offsetof(struct SaveBlock1, vars)',
        'rival_name':'offsetof(struct SaveBlock1, rivalName)',
        'player_name':'offsetof(struct SaveBlock2, playerName)',
        'player_gender':'offsetof(struct SaveBlock2, playerGender)',
        'main_state':'offsetof(struct Main, state)',
        'pokemon_size':'sizeof(struct Pokemon)',
        'pokemon_level':'offsetof(struct Pokemon, level)',
        'pokemon_hp':'offsetof(struct Pokemon, hp)',
        'pokemon_max_hp':'offsetof(struct Pokemon, maxHP)',
        'species_size':'sizeof(struct SpeciesInfo)',
        'species_count':'NUM_SPECIES',
        'form_change_size':'sizeof(struct FormChange)',
        'end_battle_method':'FORM_CHANGE_END_BATTLE',
        'species_front':'offsetof(struct SpeciesInfo, frontPic)',
        'species_back':'offsetof(struct SpeciesInfo, backPic)',
        'species_palette':'offsetof(struct SpeciesInfo, palette)',
        'species_types':'offsetof(struct SpeciesInfo, types)',
        'species_abilities':'offsetof(struct SpeciesInfo, abilities)',
        'species_learnset':'offsetof(struct SpeciesInfo, levelUpLearnset)',
        'species_evolutions':'offsetof(struct SpeciesInfo, evolutions)',
        'species_form_ids':'offsetof(struct SpeciesInfo, formSpeciesIdTable)',
        'species_form_changes':'offsetof(struct SpeciesInfo, formChangeTable)',
        'evolution_size':'sizeof(struct Evolution)',
        'battle_mon_size':'sizeof(struct BattlePokemon)',
        'battle_species':'offsetof(struct BattlePokemon, species)',
        'battle_item':'offsetof(struct BattlePokemon, item)',
        'battle_moves':'offsetof(struct BattlePokemon, moves)',
        'mon_data_species':'MON_DATA_SPECIES',
        'mon_data_level':'MON_DATA_LEVEL',
        'mon_data_hp':'MON_DATA_HP',
        'mon_data_held_item':'MON_DATA_HELD_ITEM',
        'mon_data_ability_num':'MON_DATA_ABILITY_NUM',
        'battle_hp':'offsetof(struct BattlePokemon, hp)',
        'special_status_size':'sizeof(struct SpecialStatus)',
        'special_physical_damage':'offsetof(struct SpecialStatus, physicalDmg)',
        'ability_torrent':'ABILITY_TORRENT',
        'ability_protean':'ABILITY_PROTEAN',
        'ability_battle_bond':'ABILITY_BATTLE_BOND',
        'faint_method':'FORM_CHANGE_FAINT',
        'mega_item_method':'FORM_CHANGE_BATTLE_MEGA_EVOLUTION_ITEM',
        'mega_move_method':'FORM_CHANGE_BATTLE_MEGA_EVOLUTION_MOVE',
        'player_avatar_object':'offsetof(struct PlayerAvatar, objectEventId)',
        'object_size':'sizeof(struct ObjectEvent)',
        'object_graphics':'offsetof(struct ObjectEvent, graphicsId)',
        'object_local_id':'offsetof(struct ObjectEvent, localId)',
        'bag_size':'sizeof(struct Bag)',
    }
    code = '#include "global.h"\n#include "pokemon.h"\n#include "battle.h"\n#include "main.h"\n#include "event_data.h"\n#include <stddef.h>\n'
    code += 'const u32 gUnovaLayout[] = {'+','.join(layout.values())+'};\n'
    code += 'void UnovaInspectLayout(void) { gSpecialVar_Result = gSpecialVar_0x8004 < ARRAY_COUNT(gUnovaLayout) ? gUnovaLayout[gSpecialVar_0x8004] : 0; }\n'
    (source/'src/unova_layout.c').write_text(code)
    (source/'.unova-layout').write_text(json.dumps(list(layout),indent=2)+'\n')
