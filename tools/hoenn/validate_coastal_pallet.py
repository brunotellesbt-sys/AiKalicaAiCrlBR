"""Walk Pallet's repaired native trees, terminal and Surf connection.

Reuse the controller route, but require the complete native standalone-tree
pattern introduced by this layer. Initial party/story/location are fixtures;
doors, ferry registration and all subsequent walking/Surf use controls.
"""
import hashlib
import json
from pathlib import Path
from pallet_shore_controller import verify_pallet_shore_controller

ROOT = Path(__file__).resolve().parents[2]
controller = (ROOT/'tools/hoenn/validate_pallet_harbor.py').read_text()
old = '[0xE,0xF,0x1C,0x1F,0x24,0x27]'
new = '[0xE,0xF,0x1E,0x1F,0x26,0x27]'
assert controller.count(old) == 1, 'The independently checked tree assertion changed'
controller = controller.replace(old, new)
# The closures layer replaced the old transition-height footbridge with
# native multilevel height 15, retaining foot level 3 and Surf level 1.
old = "native('MapGridGetElevationAt', 18+7, 25+7) == 0"
assert controller.count(old) == 1
controller = controller.replace(old, "native('MapGridGetElevationAt', 18+7, 25+7) == 15")
anchor = "\nlayout = json.loads((source/'.journey-pallet-harbor').read_text())"
assert controller.count(anchor) == 1
controller = controller.replace(anchor, """
# Movement-only fixture; wild battles have a separate validator.
native('DisableWildEncounters', 1)
native_pallet_captures = {}
native_pallet_picture = picture
def picture(name):
    native_pallet_picture(name)
    path = args.output / (name + '.png')
    native_pallet_captures[path.name] = dict(file=path.name,
        sha256=hashlib.sha256(path.read_bytes()).hexdigest())
""" + anchor)
anchor = '\n# The added sea rows must stay open to the original Route 21 channel.'
assert controller.count(anchor) == 1
controller = controller.replace(anchor,
    '\npallet_shore_observations = verify_pallet_shore_controller(globals())\n' + anchor)
exec(compile(controller, str(ROOT/'tools/hoenn/validate_pallet_harbor.py'), 'exec'))
marker = json.loads((source/'.journey-coastal-ecology').read_text())
output = args.output/'pallet-harbor.json'
report = json.loads(output.read_text())
assert report['passed'] is True and report['complete_trees_checked'] is True
report.update(kind='coastal-pallet', compiled_rom=True,
              elf_sha256=hashlib.sha256((source/'pokeemerald.elf').read_bytes()).hexdigest(),
              native_validation_performed=True,
              whole_standalone_tree_pattern=[0xE,0xF,0x1E,0x1F,0x26,0x27],
              all_tree_parts_checked_through_native_map_grid=True,
              walking_surf_doors_and_ferry_use_controller=True,
              fixture_wild_encounters_disabled=True,
              captures=list(native_pallet_captures.values()),
              **pallet_shore_observations)
assert report['captures']
output.write_text(json.dumps(report, indent=2)+'\n')
