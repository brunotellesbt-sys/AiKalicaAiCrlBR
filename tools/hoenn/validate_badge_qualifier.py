"""Exercise the campaign qualifier in the compiled ROM, independently of PWT.

Party, eighteen badges, birth identity, an RNG seed, initial map placement and
accelerated player battle statistics are declared fixtures. The normal field
scripts, controllers, battles, results, scoreboard, healing, defeat/retry,
celebration and save routines perform the actual progression. No fixture may
write a battle outcome or award the qualifier flag.

Without --library this writes a source-only, non-passing preflight. Run native
checks only against an immutable source/ELF/ROM snapshot.
"""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
KIND = 'qualifier-event'
OUTSIDE = 'BattleFrontier_OutsideWest'
ARENA = 'JourneyPWTArena'
CENTER = 'BattleFrontier_PokemonCenter_1F'
WON = 0x1050
CELEBRATED = 0x1051
STATE = 0x40DB
PARTICIPANT_IDS = tuple(range(26, 31))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def preflight(source):
    marker = source / '.journey-badge-story'
    return dict(kind=KIND, passed=False, preflight=True,
                native_validation_performed=False, compiled_rom=False,
                source_prepared=marker.is_file(),
                required_native_scenarios=['group_elimination', 'final_defeat',
                                           'championship', 'interrupted_arena'],
                full_campaign_playthrough=False)


def compiled_probe(source, declarations, expressions):
    command = [str(ROOT / '.local/arm-gcc/usr/bin/arm-none-eabi-gcc'),
               '-S', '-mabi=apcs-gnu', '-mthumb', '-march=armv4t',
               '-iquote', str(source / 'include'), '-DMODERN=1', '-DPOKEEMERALD',
               '-D_(x)=x', '-DCOMPOUND_STRING(x)=((const u8 *)(x))',
               '-x', 'c', '-', '-o', '-']
    code = declarations + '\nconst u32 qualifier_probe[]={' + ','.join(expressions) + '};\n'
    assembly = subprocess.check_output(command, input=code, text=True)
    section = assembly.split('qualifier_probe:', 1)[1].split('.size', 1)[0]
    values = [int(value) for value in re.findall(r'\.word\s+(\d+)', section)]
    assert len(values) == len(expressions), (expressions, values)
    return dict(zip(expressions, values))


class QualifierNative:
    def __init__(self, options):
        self.options = options
        self.source, self.output = options.source.resolve(), options.output.resolve()
        self.rom_sha = sha(self.source / 'pokeemerald.gba')
        self.elf_sha = sha(self.source / 'pokeemerald.elf')
        self.output.mkdir(parents=True, exist_ok=True)
        bootstrap = (ROOT / 'tools/hoenn/validate_trainer_levels.py').read_text().split('\nchecks=[]')[0]
        arguments = sys.argv
        namespace = {'__file__': str(ROOT / 'tools/hoenn/validate_trainer_levels.py')}
        try:
            sys.argv = [sys.argv[0], '--source', str(self.source), '--library',
                        str(options.library), '--output', str(self.output)]
            exec(compile(bootstrap, namespace['__file__'], 'exec'), namespace)
        finally:
            sys.argv = arguments
        self.ns = namespace
        self.lib, self.s = namespace['lib'], namespace['s']
        self.abi, self.pabi = namespace['abi'], namespace['pabi']
        self.native = namespace['native']
        self.step, self.press = namespace['step'], namespace['press']
        self.location, self.position = namespace['location'], namespace['position']
        self.map_id, self.warp = namespace['map_id'], namespace['warp']
        self.rawflag, self.flag = namespace['rawflag'], namespace['flag']
        self.save = namespace['save']
        self.party, self.enemy = namespace['party'], namespace['enemy']
        self.actions, self.moves = namespace['actions'], namespace['moves']
        self.targets = {int(a, 16) for a, _, n in re.findall(r'^(\w+) (\w) (\S+)$', namespace['raw'], re.M)
                        if n in ['HandleInputChooseTarget', 'HandleInputShowTargets',
                                 'HandleInputShowEntireFieldTargets']}
        self.captures, self.inputs, self.greetings = [], [], {}
        self._compile_layout()
        self.char_map = {}
        for character,value in re.findall(r"^'([^']+)'\s*=\s*([0-9A-F]{2})\s*$",
                                           (self.source / 'charmap.txt').read_text(),re.M):
            # English uses the first mappings. Later Japanese aliases reuse
            # several byte values but are not the active event font encoding.
            self.char_map.setdefault(int(value,16),character)
        self.char_map[0] = ' '
        self.reverse_chars = {value: key for key, value in self.char_map.items() if len(value) == 1}
        self.cap = self.lib.read16(self.s['gJourneyBuildRules'])
        self.hard = bool(self.lib.read8(self.s['gJourneyBuildRules'] + 2))
        self.review_mode = bool(self.lib.read8(self.s['gJourneyReviewMode']))
        self.original_pwt = self.bytes(self.s['sPWT'], self.pabi[0])
        self.original_bp = self.bp()
        self.fixture = dict(player_hero=1, start_region=0, family_home=17,
                            qualifying_badges=18, random_encounters_disabled=True,
                            initial_map_placement=True, birth_identity=True,
                            player_battle_stats_boosted=True,
                            defeat_trials_player_stats_weakened_enemy_stats_boosted=True,
                            controlled_five_x_attacks_and_initial_bag_cursor=True,
                            player_hp_status_for_berry_test=True,
                            native_flash_negative_control_after_actual_victory=True,
                            continuation_callback_is_fixture=True,
                            actual_battle_outcomes_and_qualifier_flag_not_written=True)

    def _compile_layout(self):
        declarations = ('#include "global.h"\n#include "pokemon.h"\n#include "battle.h"\n'
                        '#include "move.h"\n#include "event_object_movement.h"\n'
                        '#include "item_menu.h"\n'
                        '#include "constants/items.h"\n#include "constants/moves.h"\n'
                        '#include "constants/vars.h"\n#include <stddef.h>\n'
                        '#include "' + str(self.source / 'src/journey_badge_qualifier.c') + '"\n')
        expressions = ['sizeof(struct JourneyQualifierRuntime)',
                       'offsetof(struct JourneyQualifierRuntime, core)',
                       'offsetof(struct JourneyQualifierRuntime, active)',
                       'offsetof(struct JourneyQualifierRuntime, battleReturned)',
                       'sizeof(struct JourneyQualifierCore)',
                       'sizeof(struct JourneyQualifierMatch)',
                       'NUM_SUBSTRUCT_BYTES', 'offsetof(struct BoxPokemon, secure)',
                       'offsetof(struct BoxPokemon, checksum)',
                       'offsetof(struct Pokemon, status)', 'offsetof(struct Pokemon, level)',
                       'offsetof(struct Pokemon, hp)', 'offsetof(struct Pokemon, maxHP)',
                       'offsetof(struct Pokemon, attack)', 'offsetof(struct Pokemon, speed)',
                       'offsetof(struct Pokemon, spAttack)',
                       'sizeof(struct BattlePokemon)', 'offsetof(struct BattlePokemon, attack)',
                       'offsetof(struct BattlePokemon, speed)',
                       'offsetof(struct BattlePokemon, spAttack)',
                       'offsetof(struct BattlePokemon, hp)', 'offsetof(struct BattlePokemon, maxHP)',
                       'offsetof(struct BattlePokemon, status1)',
                       'offsetof(struct BattlePokemon, item)',
                       'offsetof(struct BattlePokemon, pp)', 'offsetof(struct BattlePokemon, moves)',
                       'sizeof(struct SpeciesInfo)', 'offsetof(struct SpeciesInfo, height)-2',
                       'sizeof(struct MoveInfo)', 'offsetof(struct MoveInfo, pp)',
                       'offsetof(struct SaveBlock1, vars)', 'offsetof(struct SaveBlock2, playerGender)',
                       'VAR_EVER_GRANDE_CITY_STATE', 'VAR_JOURNEY_START_REGION',
                       'VAR_JOURNEY_FAMILY_HOME', 'ITEM_SITRUS_BERRY', 'ITEM_LEFTOVERS',
                       'ITEM_X_ATTACK', 'BATTLE_TYPE_IS_MASTER', 'POCKET_ITEMS', 'sizeof(struct BagPosition)',
                       'offsetof(struct BagPosition, pocket)',
                       'sizeof(struct BagPocket)', 'sizeof(struct ItemSlot)',
                       'offsetof(struct ItemSlot, quantity)', 'offsetof(struct SaveBlock2, encryptionKey)',
                       'MOVE_WATERFALL', 'MOVE_SURF', 'MOVE_ICE_BEAM',
                       'MOVE_EARTHQUAKE', 'MON_DATA_MET_LEVEL']
        for field in ['hero', 'groups', 'wins', 'balance', 'survivors', 'playedMask',
                      'tieOrder', 'ledger', 'cursor', 'stage', 'opponent', 'finalists',
                      'finalWinner', 'prepared', 'finalPlayed', 'immediateGroupLoss']:
            expressions.append('offsetof(struct JourneyQualifierCore, ' + field + ')')
        for field in ['a', 'b', 'leftA', 'leftB', 'resolved']:
            expressions.append('offsetof(struct JourneyQualifierMatch, ' + field + ')')
        self.c = compiled_probe(self.source, declarations, expressions)
        self.core_at = self.s['sQualifier'] + self.c['offsetof(struct JourneyQualifierRuntime, core)']
        assert self.c['NUM_SUBSTRUCT_BYTES'] == 12, 'Review changed packed Pokemon layout'

    def bytes(self, address, count):
        return bytes(self.lib.read8(address + i) for i in range(count))

    def var(self, value):
        return self.lib.read16(self.save() + self.c['offsetof(struct SaveBlock1, vars)'] + (value - 0x4000) * 2)

    def callback(self):
        return self.lib.read32(self.s['gMain'] + 4) & ~1

    def idle(self):
        return self.callback() == self.s['CB2_Overworld'] and not self.lib.read8(self.s['sLockFieldControls'])

    def task(self, name):
        return name in self.s and self.ns['task'](name)

    def bp(self):
        return self.lib.read16(self.lib.read32(self.s['gSaveBlock2Ptr']) + self.pabi[6])

    def money_raw(self):
        # Native money is encrypted with the save key, so use this only as a
        # stable identity while the event is running. GetMoney is called idle.
        return self.bytes(self.save() + self.pabi[7], 4)

    def bag_quantity(self, item):
        # Read-only observer: do not replace a live battle/menu callback with a
        # native-call fixture merely to inspect the encrypted Bag quantity.
        pocket = self.s['gBagPockets'] + self.c['POCKET_ITEMS'] * self.c['sizeof(struct BagPocket)']
        slots, capacity = self.lib.read32(pocket), self.lib.read16(pocket + 4) & 1023
        save2 = self.lib.read32(self.s['gSaveBlock2Ptr'])
        key = self.lib.read16(save2 + self.c['offsetof(struct SaveBlock2, encryptionKey)'])
        return sum(self.lib.read16(slots + i * self.c['sizeof(struct ItemSlot)']
                                  + self.c['offsetof(struct ItemSlot, quantity)']) ^ key
                   for i in range(capacity)
                   if self.lib.read16(slots + i * self.c['sizeof(struct ItemSlot)']) == item)

    def capture(self, name):
        self.ns['picture'](name)
        file = self.output / (name + '.png')
        row = dict(file=file.name, sha256=sha(file))
        self.captures.append(row)
        return row

    def decode(self, address, limit=768):
        result = []
        for i in range(limit):
            byte = self.lib.read8(address + i)
            if byte == 255:
                return ''.join(result)
            if byte in (250, 251, 254):
                result.append('\n')
            elif byte == 252:
                return ''  # A printer-control buffer is not a dialogue body.
            else:
                result.append(self.char_map.get(byte, '<%02x>' % byte))
        return ''

    def party_data(self, enemy=False):
        """Observe encrypted native Pokemon without replacing the live script.

        The modern bit fields are independently decoded from a compiled ABI,
        the game's read-only permutation table and the native checksum. Native
        GetMonData controls below verify this observer before any field scene.
        """
        count = self.lib.read8(self.s['gPartiesCount'] + int(enemy))
        start = self.enemy if enemy else self.party
        rows = []
        for i in range(count):
            at = start + i * self.abi[2]
            personality, ot_id = self.lib.read32(at), self.lib.read32(at + 4)
            secure = self.bytes(at + self.c['offsetof(struct BoxPokemon, secure)'], 48)
            key = personality ^ ot_id
            decrypted = b''.join(struct.pack('<I', value ^ key) for value in struct.unpack('<12I', secure))
            checksum = self.lib.read16(at + self.c['offsetof(struct BoxPokemon, checksum)'])
            if sum(struct.unpack('<24H', decrypted)) & 65535 != checksum:
                assert sum(struct.unpack('<24H', secure)) & 65535 == checksum, ('Invalid native Pokemon checksum', i)
                decrypted = secure
            permutation = personality % 24
            chunks = [decrypted[self.lib.read8(self.s['sSubstructOffsets'] + block * 24 + permutation) * 12:]
                      for block in range(4)]
            species = struct.unpack_from('<H', chunks[0], 0)[0] & 2047
            held = struct.unpack_from('<H', chunks[0], 2)[0] & 1023
            exp = struct.unpack_from('<I', chunks[0], 4)[0] & 0x1FFFFF
            moves = [struct.unpack_from('<H', chunks[1], j * 2)[0] & 2047 for j in range(4)]
            pp = [chunks[1][8 + j] & 127 for j in range(4)]
            bonus = chunks[0][8]
            max_pp = []
            for slot, move in enumerate(moves):
                base = self.lib.read8(self.s['gMovesInfo'] + move * self.c['sizeof(struct MoveInfo)']
                                      + self.c['offsetof(struct MoveInfo, pp)']) if move else 0
                max_pp.append(base * (5 + ((bonus >> (slot * 2)) & 3)) // 5)
            dex = self.lib.read16(self.s['gSpeciesInfo'] + species * self.c['sizeof(struct SpeciesInfo)']
                                  + self.c['offsetof(struct SpeciesInfo, height)-2'])
            rows.append(dict(slot=i, personality=personality, ot_id=ot_id,
                             species=species, national_dex=dex, item=held, experience=exp,
                             moves=moves, pp=pp, max_pp=max_pp,
                             level=self.lib.read8(at + self.c['offsetof(struct Pokemon, level)']),
                             hp=self.lib.read16(at + self.c['offsetof(struct Pokemon, hp)']),
                             max_hp=self.lib.read16(at + self.c['offsetof(struct Pokemon, maxHP)']),
                             status=self.lib.read32(at + self.c['offsetof(struct Pokemon, status)']),
                             ivs=struct.unpack_from('<I', chunks[3], 4)[0] & 0x3FFFFFFF,
                             evs=list(chunks[2][:6])))
        return rows

    def assert_healed(self, rows):
        assert rows and all(row['hp'] == row['max_hp'] and row['hp'] > 0
                            and row['status'] == 0 and row['pp'] == row['max_pp'] for row in rows), rows

    def core(self):
        at = self.core_at
        def offset(name):
            return at + self.c['offsetof(struct JourneyQualifierCore, ' + name + ')']
        fields = {'hero': 'hero', 'wins': 'wins', 'survivors': 'survivors',
                  'tie_order': 'tieOrder', 'played_mask': 'playedMask'}
        result = {target: list(self.bytes(offset(field), 6)) for target, field in fields.items()}
        result['balance'] = list(struct.unpack('<6b', self.bytes(offset('balance'), 6)))
        values = list(self.bytes(offset('groups'), 6))
        result['groups'] = [values[:3], values[3:]]
        for target, field in [('cursor', 'cursor'), ('stage', 'stage'), ('opponent', 'opponent'),
                              ('final_winner', 'finalWinner')]:
            result[target] = self.lib.read8(offset(field))
        result['finalists'] = list(self.bytes(offset('finalists'), 2))
        for target, field in [('prepared', 'prepared'), ('final_played', 'finalPlayed'),
                              ('immediate_group_loss', 'immediateGroupLoss')]:
            result[target] = bool(self.lib.read8(offset(field)))
        result['ledger'] = []
        for i in range(6):
            record = offset('ledger') + self.c['sizeof(struct JourneyQualifierMatch)'] * i
            values = {target: self.lib.read8(record + self.c['offsetof(struct JourneyQualifierMatch, ' + field + ')'])
                      for target, field in [('a', 'a'), ('b', 'b'), ('left_a', 'leftA'), ('left_b', 'leftB')]}
            values['resolved'] = bool(self.lib.read8(record + self.c['offsetof(struct JourneyQualifierMatch, resolved)']))
            result['ledger'].append(values)
        return result

    @staticmethod
    def audit_ledger(core, scenario, battles):
        """Recompute scores from native match records, without calling C rank."""
        assert core['hero']==[0,4,2,3,5,6], ('Wrong birth-region rival identities',core['hero'])
        assert sorted(sum(core['groups'],[]))==list(range(6))
        assert 0 in core['groups'][0]
        assert sorted(core['tie_order'])==list(range(6))
        wins=[0]*6;balance=[0]*6;survivors=[0]*6;mask=[0]*6;pairs=set()
        expected={tuple(sorted((group[i],group[j]))) for group in core['groups']
                  for i in range(3) for j in range(i+1,3)}
        for match in core['ledger']:
            a,b,la,lb=(match[key] for key in ['a','b','left_a','left_b'])
            pair=tuple(sorted((a,b)))
            assert match['resolved'] and pair in expected and pair not in pairs
            assert 0<=la<=6 and 0<=lb<=6 and bool(la)!=bool(lb)
            pairs.add(pair);wins[a if la else b]+=1
            balance[a]+=la-lb;balance[b]+=lb-la
            survivors[a]+=la;survivors[b]+=lb
            mask[a]|=1<<b;mask[b]|=1<<a
        assert pairs==expected
        assert core['wins']==wins and core['balance']==balance
        assert core['survivors']==survivors and core['played_mask']==mask
        finalists=[max(group,key=lambda i:(wins[i],balance[i],survivors[i],core['tie_order'][i]))
                   for group in core['groups']]
        assert core['finalists']==finalists
        assert len([battle for battle in battles if battle['stage']==0])==2
        actual_opponents={battle['hero'] for battle in battles if battle['stage']==0}
        assert actual_opponents=={core['hero'][i] for i in core['groups'][0] if i}
        if scenario=='group_elimination':
            assert finalists[0]!=0 and not core['final_played'] and len(battles)==2
        else:
            assert finalists[0]==0 and core['final_played'] and len(battles)==3
            assert battles[-1]['hero']==core['hero'][finalists[1]] and battles[-1]['stage']==1
            assert core['final_winner']==(0 if scenario=='championship' else finalists[1])
        assert core['stage']==(2 if scenario=='championship' else 3)
        return dict(recomputed_from_six_unique_matches=True,wins=wins,balance=balance,
                    survivors=survivors,finalists=finalists,
                    exactly_two_real_player_group_battles=True)

    def configure_fixture(self, count=3):
        assert self.idle(), 'Never replace party/progress during a live event'
        for flag in self.ns['kanto_flags'] + self.ns['hoenn_flags'] + list(range(0x1040, 0x1048)):
            self.rawflag(flag, False)
        for flag in (self.ns['kanto_flags'] + self.ns['hoenn_flags'] + list(range(0x1040, 0x1048)))[:18]:
            self.rawflag(flag, True)
        assert self.native('JourneyTotalBadgeCount') == 18
        for flag in [WON, CELEBRATED]:
            self.rawflag(flag, False)
        for variable, value in [(STATE, 0), (self.c['VAR_EVER_GRANDE_CITY_STATE'], 1),
                                 (self.c['VAR_JOURNEY_START_REGION'], 0),
                                 (self.c['VAR_JOURNEY_FAMILY_HOME'], 17)]:
            self.native('VarSet', variable, value)
        save2 = self.lib.read32(self.s['gSaveBlock2Ptr'])
        self.lib.write8(save2 + self.c['offsetof(struct SaveBlock2, playerGender)'], 0)
        name = bytes(self.reverse_chars[character] for character in 'TESTER') + b'\xff'
        for i, value in enumerate(name):
            self.lib.write8(save2 + i, value)
        for i in range(6 * self.abi[2]):
            self.lib.write8(self.party + i, 0)
        self.lib.write8(self.s['gPartiesCount'], 0)
        for i in range(count):
            assert self.native('ScriptGiveMon', [260, 149, 376][i], 91 + i, 0) == 0
            for slot, move in enumerate(['MOVE_WATERFALL', 'MOVE_SURF', 'MOVE_ICE_BEAM', 'MOVE_EARTHQUAKE']):
                self.native('ScriptSetMonMoveSlot', i, self.c[move], slot)
            scratch = self.s['gStringVar4'] + 800
            self.lib.write8(scratch, 5)
            self.native('SetMonData', self.party + i * self.abi[2], self.c['MON_DATA_MET_LEVEL'], scratch)
            self.lib.write16(scratch, self.c['ITEM_SITRUS_BERRY'] if i == 0 else self.c['ITEM_LEFTOVERS'])
            self.native('SetMonData', self.party + i * self.abi[2], self.abi[107], scratch)
        self.native('HealPlayerParty')
        self.native('DisableWildEncounters', 1)
        # A controlled one-item Bag makes its ordinary battle UI deterministic.
        # Quantities are consumed only by the game, never by this observer.
        self.native('ClearBag')
        assert self.native('AddBagItem', self.c['ITEM_X_ATTACK'], 5)
        for i in range(self.c['sizeof(struct BagPosition)']):
            self.lib.write8(self.s['gBagPosition'] + i, 0)
        self.lib.write8(self.s['gBagPosition'] + self.c['offsetof(struct BagPosition, pocket)'], self.c['POCKET_ITEMS'])
        assert self.bag_quantity(self.c['ITEM_X_ATTACK']) == 5
        assert self.native('CountTotalItemQuantityInBag', self.c['ITEM_X_ATTACK']) == 5
        rows = self.party_data()
        self.assert_healed(rows)
        # The observational decoder is checked against native getters before
        # the script starts. During the event only RAM/ROM reads are used.
        for row in rows:
            mon = self.party + row['slot'] * self.abi[2]
            assert self.native('GetMonData3', mon, self.abi[7], 0) == row['species']
            assert self.native('GetMonData3', mon, self.abi[107], 0) == row['item']
            assert self.native('GetMonData3', mon, self.pabi[11], 0) == row['experience']
        return rows

    def pwt_isolation(self):
        current = self.bytes(self.s['sPWT'], self.pabi[0])
        assert current == self.original_pwt, 'Campaign event modified PWT state'
        assert self.bp() == self.original_bp, 'Campaign event awarded facility points'
        return dict(state_sha256=hashlib.sha256(current).hexdigest(),
                    initial_state_sha256=hashlib.sha256(self.original_pwt).hexdigest(),
                    state_bytes=len(current), battle_points=self.bp(),
                    initial_battle_points=self.original_bp)

    def observe_characters(self):
        objects = []
        for index in range(16):
            address = self.s['gObjectEvents'] + index * 36
            if not self.lib.read8(address) & 1:
                continue
            local = self.lib.read8(address + 8)
            if local not in PARTICIPANT_IDS and index != self.lib.read8(self.s['gPlayerAvatar'] + 5):
                continue
            sprite_id = self.lib.read8(address + 35)
            objects.append(dict(local_id=local, object_index=index, sprite_id=sprite_id,
                                position=[self.lib.read16(address + 16) - 7,
                                          self.lib.read16(address + 18) - 7],
                                graphics_id=self.lib.read16(address + 4),
                                native_obj_pixels=self.obj_pixels(sprite_id)))
        assert len(objects) == 6, ('All six actors must be loaded', objects)
        assert {row['local_id'] for row in objects if row['local_id'] in PARTICIPANT_IDS} == set(PARTICIPANT_IDS)
        regular = [row['native_obj_pixels']['opaque_bbox'][3] for row in objects
                   if row['local_id'] not in (29, 30)]
        for row in objects:
            height = row['native_obj_pixels']['opaque_bbox'][3]
            assert min(regular) - 2 <= height <= max(regular) + 2, ('Character scale differs from native rivals', row, regular)
        return dict(map=OUTSIDE, player=list(self.position()), objects=objects,
                    native_source_frames_compared_with_scanout=True,
                    capture=self.capture('qualifier-outdoor-six-participants'))

    def obj_pixels(self, sprite_id):
        sprite = self.s['gSprites'] + sprite_id * 68
        source_attr2 = self.lib.read16(sprite + 4)
        dims = [[(8,8),(16,16),(32,32),(64,64)],
                [(16,8),(32,8),(32,16),(64,32)],
                [(8,16),(8,32),(16,32),(32,64)]]
        xoff = ctypes.c_int16(self.lib.read16(self.s['gSpriteCoordOffsetX'])).value
        yoff = ctypes.c_int16(self.lib.read16(self.s['gSpriteCoordOffsetY'])).value
        sx = ctypes.c_int16(self.lib.read16(sprite + 0x20)).value + ctypes.c_int16(self.lib.read16(sprite + 0x24)).value + xoff
        sy = ctypes.c_int16(self.lib.read16(sprite + 0x22)).value + ctypes.c_int16(self.lib.read16(sprite + 0x26)).value + yoff
        candidates = []
        for index in range(128):
            a0, a1, a2 = [self.lib.read16(0x07000000 + index * 8 + 2 * j) for j in range(3)]
            if a0 & 0x0300 == 0x0200 or a0 >> 14 > 2 or (a2 & 0xF3FF) != (source_attr2 & 0xF3FF):
                continue
            width, height = dims[a0 >> 14][a1 >> 14]
            x, y = a1 & 511, a0 & 255
            if x >= 256: x -= 512
            if y >= 160: y -= 256
            if abs(x + width // 2 - sx) <= 8 and abs(y + height // 2 - sy) <= 20:
                candidates.append((index,a0,a1,a2,x,y,width,height))
        assert len(candidates) == 1, ('Native actor OAM not unique', sprite_id, candidates)
        index,a0,a1,a2,x,y,width,height = candidates[0]
        assert not a0 & 0x0100 and not a0 & 0x2000
        stride = width // 8 if self.lib.read16(0x04000000) & 0x40 else 32
        palette = a2 >> 12 & 15
        frame = ctypes.string_at(self.lib.image(), 240 * 160 * 4)
        opaque = []
        matched = 0
        for py in range(height):
            source_y = height - 1 - py if a1 & 0x2000 else py
            for px in range(width):
                source_x = width - 1 - px if a1 & 0x1000 else px
                tile = (a2 & 1023) + source_y // 8 * stride + source_x // 8
                value = self.lib.read8(0x06010000 + tile * 32 + source_y % 8 * 4 + source_x % 8 // 2)
                color = value >> (4 * (source_x & 1)) & 15
                if not color:
                    continue
                assert 0 <= x + px < 240 and 0 <= y + py < 160, ('Actor clipped', sprite_id, x,y)
                packed = self.lib.read16(0x05000200 + 2 * (16 * palette + color))
                expected = [((packed >> shift) & 31) * 8 for shift in (0,5,10)]
                observed = frame[4 * ((y + py) * 240 + x + px):][:3]
                matched += all(abs(a-b) <= 7 for a,b in zip(expected, observed))
                opaque.append((px,py))
        assert len(opaque) >= 100 and matched >= len(opaque) * 0.80, ('Actor hidden by map/window',sprite_id,matched,len(opaque))
        xs, ys = zip(*opaque)
        return dict(hardware_oam_index=index, frame=[width,height],
                    screen_rectangle=[x,y,width,height],
                    opaque_bbox=[min(xs),min(ys),max(xs)-min(xs)+1,max(ys)-min(ys)+1],
                    opaque_pixels=len(opaque), matching_scanout_pixels=matched,
                    exact_vram_obj_palette_and_current_frame=True)

    def _observe_greeting(self):
        if self.location() != self.map_id(OUTSIDE) or self.var(STATE) != 2:
            return
        slot = self.lib.read16(self.s['gSpecialVar_0x8004'])
        if slot > 4:
            return
        pc = self.lib.read32(self.s['sGlobalScriptContext'] + 8)
        text = self.decode(self.s['gStringVar4'])
        # Slot changes before msgbox expands its text. Require the contextual
        # speech itself so a previous speaker/scoreboard cannot be relabelled.
        phrases = {
            'LEAF': 'You kept reading our next move.',
            'BRENDAN': 'Every journey made us stronger.',
            'MAY': 'You trusted every POKeMON.',
            'Luffy': 'You never gave up on your crew!',
            'Eren': 'You chose your path and held on.',
            'RED': 'You earned this.',
        }
        speaker = self.decode(self.s['gStringVar1'], 32)
        if (speaker in phrases and phrases[speaker] in text
                and text.startswith(speaker + ':') and slot not in self.greetings):
            # B held while the native printer runs speeds its text. One new
            # edge is sent before it reaches the page wait; it is not repeated
            # to acknowledge pages. Capture a readable first speech page.
            self.step(120, 2)
            self.greetings[slot] = dict(slot=slot, map=OUTSIDE, player=list(self.position()),
                                       speaker=speaker, text=text, native_script_pointer=pc,
                                       printer_accelerated_with_held_b=True,
                                       capture=self.capture('qualifier-congratulations-' + str(slot)))

    def _field_input(self):
        self._observe_greeting()
        if self.task('Task_HandleYesNoInput'):
            # Yes is the first entry in these non-wrapping native menus.
            self.step(1, 64); self.step(8); self.step(1, 1); self.step(8)
        else:
            self.press(1)

    def _boost(self, lose=False, berry=False):
        if lose:
            for i in range(self.lib.read8(self.s['gPartiesCount'])):
                at = self.party + i * self.abi[2]
                if self.lib.read16(at + self.c['offsetof(struct Pokemon, hp)']):
                    self.lib.write16(at + self.c['offsetof(struct Pokemon, hp)'], 1)
                for field in ['attack', 'spAttack', 'speed']:
                    self.lib.write16(at + self.c['offsetof(struct Pokemon, ' + field + ')'], 1)
            if self.lib.read16(self.s['gBattleMons'] + self.c['offsetof(struct BattlePokemon, hp)']):
                self.lib.write16(self.s['gBattleMons'] + self.c['offsetof(struct BattlePokemon, hp)'], 1)
            for field in ['attack', 'spAttack', 'speed']:
                self.lib.write16(self.s['gBattleMons'] + self.c['offsetof(struct BattlePokemon, ' + field + ')'], 1)
                self.lib.write16(self.s['gBattleMons'] + self.c['sizeof(struct BattlePokemon)']
                                 + self.c['offsetof(struct BattlePokemon, ' + field + ')'], 16000)
            return
        for i in range(self.lib.read8(self.s['gPartiesCount'])):
            at = self.party + i * self.abi[2]
            for field,value in [('attack',16000),('spAttack',16000),('speed',10000)]:
                self.lib.write16(at + self.c['offsetof(struct Pokemon, ' + field + ')'],value)
        for field,value in [('attack',16000),('spAttack',16000),('speed',10000)]:
            self.lib.write16(self.s['gBattleMons'] + self.c['offsetof(struct BattlePokemon, ' + field + ')'],value)
        if not berry:
            for i in range(self.lib.read8(self.s['gPartiesCount'])):
                at=self.party+i*self.abi[2]
                if self.lib.read16(at+self.c['offsetof(struct Pokemon, hp)']):
                    self.lib.write16(at+self.c['offsetof(struct Pokemon, hp)'],
                                     self.lib.read16(at+self.c['offsetof(struct Pokemon, maxHP)']))
            hp_at=self.s['gBattleMons']+self.c['offsetof(struct BattlePokemon, hp)']
            if self.lib.read16(hp_at):
                self.lib.write16(hp_at,self.lib.read16(self.s['gBattleMons']+self.c['offsetof(struct BattlePokemon, maxHP)']))

    def _battle_input(self, attacks):
        controllers = {self.lib.read32(self.s['gBattlerControllerFuncs'] + i * 4) & ~1 for i in range(4)}
        if controllers & self.targets:
            self.press(1)
        elif controllers & self.moves:
            move_at=self.s['gBattleMons']+self.c['offsetof(struct BattlePokemon, moves)']
            pp_at=self.s['gBattleMons']+self.c['offsetof(struct BattlePokemon, pp)']
            slots=[j for j in range(4) if self.lib.read16(move_at+j*2) and self.lib.read8(pp_at+j)]
            desired=(slots or [0])[attacks % max(1,len(slots))]
            current=self.lib.read8(self.s['gMoveSelectionCursor'])
            if current & 1 != desired & 1:
                self.press(16 if desired & 1 else 32)
            elif current >> 1 != desired >> 1:
                self.press(128 if desired >> 1 else 64)
            else:
                self.press(1); attacks+=1
        elif controllers & self.actions:
            self.step(1,64);self.step(8);self.step(1,32);self.step(8);self.press(1)
        else:
            self.press(2)
        return attacks

    def attempt(self, scenario, outcomes, seed, capture_intro=False):
        assert self.idle(), ('Attempt started while another script owns the field',scenario)
        self.native('SeedRng', seed) if 'SeedRng' in self.s else self.lib.write32(self.s['gRngValue'], seed)
        before_party=self.party_data()
        before_bag=self.bag_quantity(self.c['ITEM_X_ATTACK'])
        before_money=self.native('GetMoney', self.save()+self.pabi[7])
        assert not self.flag(WON)
        self.warp(OUTSIDE,26,67)
        self.step(8)
        intro=None
        if capture_intro:
            intro=self.observe_characters()
        # Step from the central gathering position onto the real arrival
        # trigger. Merely facing left here would talk to an empty tile.
        if self.idle():
            self.step(20,32);self.step(8)
        battles=[];last_core=None;initial_draw=None;healed=[]
        current=None;berry_observed=False;berry_armed=False;seen_orders=[]
        bag_requested=False;bag_opened=False;bag_consumed=False
        switch_requested=False;switch_selected=False
        for tick in range(30000):
            if tick in (100,300):
                self.capture(scenario+'-progress-'+str(tick))
                print('Qualifier early',scenario,tick,self.location(),self.position(),
                      'idle',self.idle(),'scriptpc',hex(self.lib.read32(self.s['sGlobalScriptContext']+8)),
                      'contextstatus',self.lib.read8(self.s['sGlobalScriptContextStatus']),
                      'text',self.decode(self.s['gStringVar4']),flush=True)
            if tick and tick%1000==0:
                print('Qualifier progress',scenario,tick,self.location(),self.position(),
                      len(battles),self.var(STATE),hex(self.callback()),flush=True)
            callback=self.callback()
            if (self.location()==self.map_id(ARENA)
                    and self.lib.read8(self.s['sQualifier'] + self.c['offsetof(struct JourneyQualifierRuntime, active)'])):
                last_core=self.core()
                if initial_draw is None and self.var(STATE)==1:
                    initial_draw=dict(hero=last_core['hero'],groups=last_core['groups'],tie_order=last_core['tie_order'])
                    assert all(not m['resolved'] for m in last_core['ledger'])
            if callback==self.s['BattleMainCB2']:
                if current is None:
                    index=len(battles)
                    assert index<len(outcomes),('Unexpected extra player battle',scenario,index)
                    core=self.core()
                    trainer=self.lib.read16(self.s['gTrainerBattleParameter']+self.abi[13])
                    flags=self.lib.read32(self.s['gBattleTypeFlags'])
                    assert flags==(self.abi[10]|self.c['BATTLE_TYPE_IS_MASTER']),('Qualifier acquired facility/special flags',flags)
                    player=self.party_data();enemy=self.party_data(True)
                    self.assert_healed(player)
                    assert len(enemy)==6
                    assert all(row['national_dex']<=self.cap and row['national_dex']>0 for row in enemy)
                    assert all(sum(row['evs'])==510 for row in enemy)
                    if self.hard:assert all(row['ivs']==0x3FFFFFFF for row in enemy)
                    else:assert any(row['ivs']!=0x3FFFFFFF for row in enemy)
                    assert [row['level'] for row in player] != [50]*len(player), 'Player normalized to facility level'
                    hero=core['hero'][core['opponent']]
                    assert trainer==1800+hero
                    current=dict(trainer=trainer,hero=hero,stage=core['stage'],battle_flags=flags,
                                 entry_party=player,enemy_party=enemy,actions=0,
                                 outcome=None,berry_consumed_natively=False,active_party_indices=[],
                                 command_menu_capture=False)
                    berry_armed=False
                index=len(battles)
                active_index=self.lib.read8(self.s['gBattlerPartyIndexes'])
                if active_index not in current['active_party_indices']:
                    current['active_party_indices'].append(active_index)
                lose=outcomes[index]==2
                if not lose and scenario=='championship' and index==0 and not berry_armed:
                    # Player-side low HP and poison are deliberate functional
                    # fixtures. The berry is removed by the real battle item
                    # controller, not by writing its item field.
                    hp=self.lib.read16(self.s['gBattleMons']+self.c['offsetof(struct BattlePokemon, maxHP)'])
                    self.lib.write16(self.s['gBattleMons']+self.c['offsetof(struct BattlePokemon, hp)'],max(2,hp*2//5))
                    self.lib.write32(self.s['gBattleMons']+self.c['offsetof(struct BattlePokemon, status1)'],8)
                    berry_armed=True
                held=self.lib.read16(self.s['gBattleMons']+self.c['offsetof(struct BattlePokemon, item)'])
                if berry_armed and held==0:
                    berry_observed=True;current['berry_consumed_natively']=True
                self._boost(lose,berry=berry_armed and not berry_observed)
                controllers = {self.lib.read32(self.s['gBattlerControllerFuncs'] + i * 4) & ~1 for i in range(4)}
                if controllers & self.actions and not current['command_menu_capture']:
                    self.capture(scenario+'-battle-'+str(index+1))
                    current['command_menu_capture']=True
                if scenario=='championship' and index==0 and not bag_requested and controllers & self.actions:
                    # Select Bag from the normal action menu. X Attack is the
                    # only fixture item; the native Bag use controller removes it.
                    cursor=self.lib.read8(self.s['gActionSelectionCursor'])
                    if cursor & 2:self.press(64)
                    elif not cursor & 1:self.press(16)
                    else:
                        self.press(1);bag_requested=True
                elif (scenario=='championship' and index==0 and bag_consumed
                      and berry_observed and not switch_requested and controllers & self.actions):
                    cursor=self.lib.read8(self.s['gActionSelectionCursor'])
                    if cursor&1:self.press(32)
                    elif not cursor&2:self.press(128)
                    else:
                        self.press(1);switch_requested=True
                else:
                    current['actions']=self._battle_input(current['actions'])
            elif callback in {self.s.get('CB2_Bag'),self.s.get('CB2_BagMenuRun')}:
                assert scenario=='championship' and bag_requested and len(battles)==0
                if callback==self.s.get('CB2_BagMenuRun'):
                    if not bag_opened:
                        self.capture('qualifier-normal-bag-ui');bag_opened=True
                    self.press(1)
                else:self.step(8)
                bag_consumed |= self.bag_quantity(self.c['ITEM_X_ATTACK'])==before_bag-1
            elif callback in {self.s['CB2_InitPartyMenu'],self.s['CB2_UpdatePartyMenu']}:
                if self.task('Task_HandleChooseMonInput'):
                    # The party screen uses its battle-order slots, which can
                    # differ from physical party indices after a native switch.
                    rows=self.party_data()
                    alive=[]
                    for menu_slot in range(1,len(rows)):
                        order=self.lib.read8(self.s['gBattlePartyCurrentOrder']+menu_slot//2)
                        physical=(order&15) if menu_slot&1 else order>>4
                        if physical<len(rows) and rows[physical]['hp']>0:alive.append(menu_slot)
                    assert alive,('Party menu after all Pokemon fainted',scenario)
                    target=alive[0]
                    slot=self.lib.read8(self.s['gPartyMenu']+self.abi[100])
                    switch_selected |= switch_requested and slot==target
                    self.press(128 if slot!=target else 1)
                else:self.press(1)
            else:
                if current is not None and callback==self.s['CB2_Overworld']:
                    current['outcome']=self.lib.read8(self.s['gBattleOutcome'])
                    assert current['outcome']==outcomes[len(battles)],(scenario,current)
                    assert current['actions']>0
                    assert current['command_menu_capture'], 'Battle never presented an actual command-menu frame'
                    battles.append(current);current=None
                    seen_orders.append([r['personality'] for r in self.party_data()])
                if self.location()==self.map_id(ARENA) and self.var(STATE)==1:
                    rows=self.party_data()
                    if rows and all(r['hp']==r['max_hp'] and r['status']==0 and r['pp']==r['max_pp'] for r in rows):
                        identity=tuple((r['personality'],r['item'],r['experience']) for r in rows)
                        if not healed or healed[-1]['identity']!=identity:
                            healed.append(dict(after_battles=len(battles),identity=identity,party=rows))
                if self.idle() and self.location() in {self.map_id(CENTER),self.map_id(OUTSIDE)}:
                    if len(battles)==len(outcomes) and (self.flag(WON) or self.location()==self.map_id(CENTER)):
                        break
                self._field_input()
        else:
            self.capture(scenario+'-timeout')
            raise AssertionError(('Qualifier event timeout',scenario,self.location(),self.position(),len(battles),self.var(STATE),last_core))
        assert len(battles)==len(outcomes)
        assert last_core is not None and initial_draw is not None
        assert all(m['resolved'] for m in last_core['ledger']),last_core
        ledger_audit=self.audit_ledger(last_core,scenario,battles)
        won=scenario=='championship'
        assert self.flag(WON)==won
        assert self.location()==self.map_id(OUTSIDE if won else CENTER)
        assert self.var(STATE)==(3 if won else 0)
        if won:
            assert self.flag(CELEBRATED)
            assert len(self.greetings)==5,self.greetings
            assert len({row['text'] for row in self.greetings.values()})==5
            assert berry_observed,'Native held berry was not consumed before restoration'
            assert bag_requested and bag_opened and bag_consumed, 'Ordinary Bag item was not used through the UI'
            assert switch_requested and switch_selected, 'No native party switch exercised item identity restoration'
            assert len(battles[0]['active_party_indices'])>1, 'Party selection never changed the active battler'
        else:
            assert not self.flag(CELEBRATED)
        after_party=self.party_data()
        self.assert_healed(after_party)
        originals={(r['personality'],r['ot_id']):r['item'] for r in before_party}
        assert {(r['personality'],r['ot_id']):r['item'] for r in after_party}==originals
        after_money=self.native('GetMoney',self.save()+self.pabi[7])
        # This uses ordinary trainer battles. Defeat retains the native prize
        # money payment; there is no additional registration charge. A clean
        # championship must retain its earned prizes rather than restore an
        # old party/save snapshot over the winnings.
        assert after_money>=0
        if won:assert after_money>=before_money
        after_bag=self.bag_quantity(self.c['ITEM_X_ATTACK'])
        assert after_bag==before_bag-int(won), ('Qualifier rolled back or consumed extra Bag items',before_bag,after_bag)
        old_experience={(r['personality'],r['ot_id']):r['experience'] for r in before_party}
        experience_gain=sum(r['experience']-old_experience[(r['personality'],r['ot_id'])] for r in after_party)
        assert experience_gain>=0
        if any(outcome==1 for outcome in outcomes):assert experience_gain>0, 'Qualifier discarded normal battle EXP'
        self.pwt_isolation()
        return dict(scenario=scenario,draw_seed=seed,initial_draw=initial_draw,
                    initial_party=before_party,final_core=last_core,
                    independent_ledger_audit=ledger_audit,
                    player_battles=battles,healed_intermission_observations=healed,
                    after=dict(map=OUTSIDE if won else CENTER,position=list(self.position()),
                               state=self.var(STATE),won=won,money_before=before_money,
                               money_after=after_money,battle_points=self.bp(),party=after_party,
                               x_attack_before=before_bag,x_attack_after=after_bag,
                               bag_ui_opened=bag_opened,bag_item_consumed_natively=bag_consumed,
                               native_party_switch=switch_selected,post_battle_party_orders=seen_orders,
                               total_experience_gain=experience_gain),
                    outdoor_intro=intro,
                    capture=self.capture(scenario+'-finished'))

    def run(self):
        assert '.journey-badge-story' in {p.name for p in self.source.glob('.journey-*')}
        self.configure_fixture(count=1)
        # No synthetic battle outcome is used: the enemy knocks out the weak
        # one-member test party through the normal battle controller.
        group=self.attempt('group_elimination',[2,2],0x2281,capture_intro=True)
        self.configure_fixture(count=3)
        final_loss=self.attempt('final_defeat',[1,1,2],0x2282)
        self.configure_fixture(count=3)
        championship=self.attempt('championship',[1,1,1],0x2283)
        before_save=self.party_data()
        assert self.native('TrySavingData',0,max_frames=6000)==1
        # Negative control proves loading restores the actually won state.
        self.rawflag(WON,False);self.rawflag(CELEBRATED,False)
        self.native('VarSet',STATE,0)
        assert not self.flag(WON)
        assert self.native('LoadGameSave',0,max_frames=6000)==1
        assert self.flag(WON) and self.flag(CELEBRATED) and self.var(STATE)==3
        self.lib.write32(self.s['gMain']+4,self.s['CB2_ContinueSavedGame']|1)
        for _ in range(300):
            if self.idle():break
            self.press(1)
        assert self.idle() and self.location()==self.map_id(OUTSIDE)
        assert self.party_data()==before_save
        saved=dict(native_flash_roundtrip=True,qualifier_won=True,celebrated=True,state=3,
                   temporary_clear_is_negative_control=True,continuation_callback_is_fixture=True,
                   capture=self.capture('qualifier-champion-save-continue'))
        # A saved arena marker without its volatile controller must recover to
        # the Center, never enter a stale PWT cup or manufacture qualification.
        self.rawflag(WON,False);self.rawflag(CELEBRATED,False)
        self.native('VarSet',STATE,1)
        self.warp(ARENA,9,6)
        for _ in range(400):
            if self.idle() and self.location()==self.map_id(CENTER):break
            self._field_input()
        assert self.idle() and self.location()==self.map_id(CENTER)
        assert not self.flag(WON) and self.var(STATE)==0
        recovery=dict(inactive_volatile_controller_and_arena_state_are_fixtures=True,
                      recovered_map=CENTER,state=0,qualifier_won=False,
                      capture=self.capture('qualifier-interrupted-arena-recovery'))
        isolation=self.pwt_isolation()
        assert sha(self.source/'pokeemerald.gba')==self.rom_sha
        assert sha(self.source/'pokeemerald.elf')==self.elf_sha
        report=dict(kind=KIND,passed=True,preflight=False,compiled_rom=True,
                    native_validation_performed=True,rom_sha256=self.rom_sha,
                    elf_sha256=self.elf_sha,review_mode=self.review_mode,
                    max_national=self.cap,perfect_trainer_ivs=self.hard,
                    fixtures=self.fixture,attempts=[group,final_loss,championship],
                    celebrations=[self.greetings[i] for i in range(5)],
                    saved_win=saved,interrupted_arena=recovery,pwt_isolation=isolation,
                    native_mon_decoder_checked_against_GetMonData=True,
                    captures=self.captures,full_campaign_playthrough=False)
        self.lib.stop()
        return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--library',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--preflight',action='store_true')
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    report=preflight(args.source) if args.preflight or not args.library else QualifierNative(args).run()
    (args.output/(KIND+'.json')).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({key:report.get(key) for key in ['kind','passed','preflight','rom_sha256']}))


if __name__=='__main__':
    main()
