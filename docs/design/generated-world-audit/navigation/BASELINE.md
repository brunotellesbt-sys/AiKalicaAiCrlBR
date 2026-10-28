# Generated surface navigation audit

The immutable PR101 baseline was inspected with compiled native metatile behavior, collision, elevation and signed connection offsets. The graph includes all 417 surface maps and 519,598 source cells; it is not a controller playthrough. All 266 active generated ocean-route maps share the Route19 ocean component (262,573 water cells). The prototype JourneyHoennCrossing is explicitly retired by the navigated atlas and has no connections or incoming surface references.

470 physical edges touching created/changed terrain or connections are reciprocal. Seven edges have no ordinary passage and preserve an entire upstream cliff/tree boundary on at least one side; these are not silently counted as traversable. The plan has 990 controller cases, checking both directions and both Surf/walking wherever a clear compatible-height span exists. Native levels 0 and 15 allow transitions, and equal native levels such as Safari's level 5 remain valid. The first 12 baseline controller cases, both directions through Lavender's level1↔0 seam and Safari's level5↔5 seam passed; this is a pilot, not final-ROM coverage.

Fast water (behavior0x2C) is classified per map using the exact native Sevii coast whitelist. The same behavior on an unchanged non-coastal route is never silently reclassified as ordinary walking floor. Every measured arrival checks the destination coordinates, avatar mode, the loaded layout's FRLG decoding flag, loaded primary/secondary tileset pointers and the actual loaded block against its destination layout. The separate global `isFrlg` describes the region's presentation; mixed-region routes need not use the matching metatile format.

Reproduce the final-ROM sweep in independent slices, each with a separate output directory:

```sh
python3 tools/hoenn/validate_generated_surface_navigation.py --source SOURCE --library .local/mgba-review.so --output OUTPUT --native --start-case 0 --limit 198
```

Start subsequent slices at 198, 396, 594 and 792, deriving the slice size from `planned_native_case_count` when a repair changes the plan. Import `merge_reports` from this module to combine the five `generated-surface-navigation.json` files. The merge rejects different ROM hashes, changed case plans, duplicate cases and missing cases. The native captures are mGBA frames; each border crossing uses directional input after a declared initial placement fixture. Party, defeated-trainer flags and initial placement do not represent ordinary campaign progress.

The bounded runner automates that plan, records each process's progress and verifies that the source ROM and ELF stayed unchanged throughout:

```sh
python3 tools/hoenn/run_generated_surface_navigation.py --source SOURCE --library .local/mgba-review.so --output OUTPUT --jobs 5
```

Four Island's native rival arrival and One Island's Bill arrival are already completed in the declared fixture (`VAR_MAP_SCENE_FOUR_ISLAND=1`, `VAR_MAP_SCENE_ONE_ISLAND_HARBOR=3`). Their campaign events themselves are not bypassed in the game or claimed as part of this movement check. This prevents an automatic dialogue from taking the controls during the border test.

Six regression tests cover signed overlaps, reciprocal geometry, disjoint maps, widest open span selection, dishonest/incomplete proof merges, and restoration of the private sixteen-bit travel fixture on both success and failure.

Large starting coordinates use a temporary native WarpEvent in the emulator's private, verified padding page. The direct native warp function accepts signed bytes and would place coordinates above127 at the map's center. The fixture instead supplies signed sixteen-bit coordinates, then restores the original warp count, table pointer and padding bytes before directional input. The distributed ROM, player coordinates and player elevation are never patched by this fixture.
