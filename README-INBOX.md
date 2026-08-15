# Inbox drop — dead void filled, live routes kept (2026-08-14)

REPLACES `docs/plans/dust2_half.json`. Adds `tools/gapfill.py`,
`tools/twolevel.py`. Pipeline order: `final.py` -> `roofs.py` ->
`archfix.py` -> `gapfill.py`.

## Why a global raise was wrong

You were right to push back. The base plate is not merely a floor under a
void: **z=0 is real ground for about half the map.**

| | cells |
|---|---|
| both a z=0 floor and a z=128 floor | 1,542 |
| **only a z=0 floor** | **1,602** |
| only a z=128 floor | 184 |

Raising the base to 112 would have buried 1,602 cells of legitimate ground
under a plateau. Surface area by height: z=0 at 46%, z=128 at 23%,
z=384 at 11%.

## What was done instead

Fill the gap under a raised floor ONLY where the gap is dead:

    cells with a gap under a raised floor : 1,671
      LIVE  (reachable route beneath)     : 1,191  left alone
      DEAD  (filled)                      :   480  -> 27 merged boxes

3,525 m2 filled, in 27 boxes rather than 480, by merging runs.

## The dilation, and the run that needed it

The first attempt filled 698 cells and **cost 465 reachable cells**.
`gap_is_live` samples only each cell's centre column, so a cell that is
half open corridor reads as dead, and filling it ate the edges of real
routes.

Fixed by dilating the live mask one cell before filling. Reachable cells
went 7,341 -> 6,876 (bad) -> **7,296** (fine, and the 45 lost are edge
quantisation at 64 u).

## Two-level spaces confirmed intact

| plate | on top | underneath | |
|---|---|---|---|
| axis_470 | 79% | 86% | genuine two-level, preserved |
| axis_546 | 77% | 100% | genuine two-level, preserved |
| axis_355 | 0% | 64% | route beneath preserved |
| axis_764 | 0% | 100% | route beneath preserved |
| axis_199 | 34% | 0% | **filled**, as intended |

`axis_355` briefly dropped to 45% underneath before the dilation and is
back to 64%.

## Still dead, and deliberately left

`axis_42`, `axis_473`, `axis_475`, `axis_62`, `axis_63` are reachable
from neither side. They are geometry nobody can see or touch. Deleting
them would shrink the plan, but they cost nothing and may become
meaningful once the map is mirrored and modified.
