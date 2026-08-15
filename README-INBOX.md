# Inbox drop — ground plates un-lifted (2026-08-14)

REPLACES `docs/plans/dust2_half.json`. Adds `tools/unlift.py`.
Pipeline order is now:

    final.py -> (snapshot) -> roofs.py -> archfix.py -> unlift.py -> gapfill.py

`unlift.py` needs `orig_snapshot.json`, a copy of the plan taken straight
after `final.py`, to know where each box started.

## The bug you found

`roofs.py` lifts anything resting on a wall that doubled. Correct for a
roof, wrong for a floor: **axis_199 is part of dust2's main z=128 ground
level** (CS units), and it got carried 186 u into the air along with
everything standing on it.

Your second coordinate was the giveaway. `gapfill_39_9` tops out at 213 u,
which is exactly 128 CS x 1.667 — the height axis_199 should have been at
all along. The fill boxes were sitting at the right level while the plate
they were meant to close the gap under had floated above them.

## The rule applied

A box whose ORIGINAL bottom was at or below the main floor (213 u) is
ground, not roof. Restore its height and its thickness, then bring down
whatever was standing on it by the same amount.

    restored  5 ground-level boxes
      axis_199         lowered 187 u
      axis_361         lowered 213 u
      yaw_484 / 485    lowered 187 u
      angled-wall_488  lowered 187 u
    carried  16 boxes that were riding on them

axis_199 is now 187..213, flush with the fill, and six boxes sit on its
surface at 213 rather than hanging in the air.

## Verified

- reachable cells 7,320 (was 7,296 before this change; the plate rejoining
  the floor added a little)
- **axis_199 reachable on top went 34% -> 52%** — it is now part of the
  walkable floor rather than an island
- two-level spaces unaffected: axis_470 and axis_546 unchanged
- gapfill unchanged at 480 dead cells in 27 boxes

## Note on how this one was found

Two crosshair readings, one on the broken thing and one on what it should
line up with, pinned it in a single message. That is a much better bug
report than a coordinate alone, and worth repeating: **point at the fault,
then point at the reference.**
