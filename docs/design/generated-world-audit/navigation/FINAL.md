# Final native surface navigation

The complete sweep passed on raw ROM
`b04918724939a54bbe3321d274953a9311ab8c7b4eebc3cbeb844ffcd3604386`:

- 417 surface maps and 470 affected reciprocal physical edges were classified
  from compiled behavior tables, collision, elevation and signed offsets.
- All 990 planned controller cases passed: 854 with Surf and 136 on foot.
  Both directions were checked for every selected passable mode on an edge.
- Every arrival matched the expected map and tile coordinates, avatar mode,
  loaded layout format, primary/secondary bank pointers and real loaded block.
- All active generated ocean routes share the Route19 ocean component.
  Seven closed boundaries preserve native upstream cliffs or trees and are
  reported separately. The explicitly retired prototype is excluded.
- Seven initial placements beyond signed-byte coordinate range use a private
  native sixteen-bit WarpEvent fixture. Its table and bytes are restored
  before controller input; no player coordinates or elevations are written.
- Five disjoint shards of198cases were merged only after identical-ROM,
  identical-plan, no-duplicate and complete-coverage checks. ROM and ELF
  hashes remained unchanged throughout.

The proof is
`mods/hoenn/generated-world-audit-validation/common/navigation/generated-surface-navigation.json`.
It binds 25 actual mGBA arrival captures by SHA256. Source renders are not used
as movement evidence. Captures0,200,400,600,800 were also visually inspected.
Six regression tests cover offset geometry, span selection, dishonest merges
and private fixture restoration on success and failure.

This is an exhaustive sweep of the selected border cases, not a full campaign
playthrough or a test of every tile in the game. It chooses the widest usable
border span per movement mode; separate cave, beach, pier, gym and animation
validators cover entrances, landings, save/Continue, NPC approaches and timing.
Party, arrival-scene completion, defeated-trainer state and starting positions
are declared test fixtures, not claims of ordinary campaign progress.
