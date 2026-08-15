# Inbox drop — eight doors removed (2026-08-14)

REPLACES `docs/plans/dust2_half.json`. Adds `tools/remove.py`,
`tools/unlift.py`, `tools/gapfill.py`.

Pipeline order, now complete:

    final.py -> (copy to orig_snapshot.json) -> roofs.py -> archfix.py
    -> unlift.py -> gapfill.py -> remove.py

## Eight door leaves gone

    compound_117  compound_118      compound_196  compound_197
    compound_201  compound_203      compound_374  compound_375

All four openings, two leaves each. Plan 1090 -> 1082 boxes.

**Why doors.py missed them.** Its shortlist required axis-aligned,
door-shaped solids. These are `compound` brushes — angled panels that
became bounding boxes — so they were never candidates. The wall doubling
then stretched them to between 13 and 16 m.

## Reachability jumped

    7,320 -> 8,116 reachable cells (+796, +11%)

The doors were sealing real ground. axis_199's reachable-on-top went
34% -> 52% (after the un-lift) -> **74%** now, which is the same fix
showing up from a different direction: with the doors gone that whole
floor connects.

## 18 compound brushes remain, 10 look door-shaped

Not removed, because "narrow, tall, yawed" also describes an angled wall
corner, and I cannot tell them apart from geometry:

| name | width | height | yaw |
|---|---|---|---|
| compound_757 | 1.4 m | 32.5 m | 20.0 |
| compound_204 | 2.0 m | 32.5 m | 59.0 |
| compound_349 | 2.4 m | 32.5 m | 32.0 |
| compound_776 | 2.4 m | 32.5 m | 48.8 |
| compound_266 | 2.7 m | 32.5 m | 56.3 |
| compound_477 | 2.7 m | 21.7 m | 51.3 |
| compound_564 | 2.7 m | 21.7 m | 51.3 |
| compound_748 | 4.4 m | 32.5 m | 47.1 |
| compound_478 | 4.7 m | 21.7 m | 40.6 |
| compound_12  | 4.7 m | 16.3 m | 36.9 |

The 32.5 m ones are full wall height, so they are probably corners rather
than doors. `compound_477` and `compound_564` are an identical pair at the
same yaw, which is the signature the removed ones had — worth a look.

Crosshair any that are wrong and add them to the list in `remove.py`.

## Still ahead

No mirror, no 180-degree rotation, no 30 m band.
