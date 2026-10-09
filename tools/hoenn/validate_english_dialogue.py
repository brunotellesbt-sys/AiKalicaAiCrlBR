"""Show English family/professor dialogue in both starting regions.
Travel and direct NPC script entry are fixtures; menus and gifts run natively.
"""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
exec(compile((ROOT / 'tools/hoenn/validate_family.py').read_text().split('\nwater =')[0],
             str(ROOT / 'tools/hoenn/validate_family.py'), 'exec'))
assert city != 0
event('Journey_Family', 1)
step(240); picture('english-family-gift-dialogue'); finish()
for person in range(1, home['people']):
    event('Journey_Family', person + 1); finish()
assert var(0x40F8) == 7
assert all(native('CountTotalItemQuantityInBag', item) == 1 for item in abi[17:20])
event('Journey_Oak', home['people'] + 1)
step(240); picture('english-professor-first-page')
advance_until(lambda: task('Task_HandleMultichoiceInput'))
picture('english-starter-menu'); press(1); finish()
assert lib.read8(s['gPartiesCount']) == 1
assert native('GetMonData3', s['gParties'], abi[7], 0) == starter_species[0]
assert native('GetMonData3', s['gParties'], abi[6], 0) == 5
assert native('IsNationalPokedexEnabled')
assert native('JourneyGymBadgeCount', 0) == native('JourneyGymBadgeCount', 1) == 0
lib.stop()
(args.output / 'english-dialogue.json').write_text(json.dumps(dict(
    passed=True, rom_sha256=hashlib.sha256((source / 'pokeemerald.gba').read_bytes()).hexdigest(),
    city=home['city'], region='Hoenn' if hoenn else 'Kanto',
    native_city_choice_and_arrival=True, all_three_water_hms_given=True,
    native_starter_menu=True, starter_species=starter_species[0], starter_level=5,
    national_dex_enabled=True, screenshots_require_visual_review=True,
    travel_and_npc_script_entries_are_fixtures=True, full_campaign_playthrough=False), indent=2) + '\n')
print('Native English dialogue and gifts passed:', home['city'], flush=True)
