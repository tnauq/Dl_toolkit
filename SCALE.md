# Scale reference

**1 unit = 1 inch = 0.0254 m. 1 m = 39.37 u.**

Not assumed: Deadlock reports distance in metres but works in hammer
units where 1 unit is about 1 inch. The figure checks against a second
number from the same source — the slide threshold is given as both
8.9 m/s and 350 hu/s, and 350 / 39.37 = 8.89.

## Why this changed the examples

The first pass sized everything against a 72-unit Source player. Deadlock
heroes are much bigger: Bebop is about 3.05 m (~120 u) and Lady Geist
2.57 m (~101 u). Every clearance was roughly 40% too tight, and both
"cover" blocks were actually full cover.

## Working figures, in units

| | units | metres | note |
|---|---|---|---|
| hero (tall end) | 120 | 3.05 | Bebop, to the head |
| eye height | 96 | 2.44 | what the viewer stands you at |
| partial cover | 96 | 2.44 | breaks a sightline, movable over |
| full cover | 192 | 4.88 | clears the tallest hero |
| min passage width | 192 | 4.88 | two abreast wants ~256 |
| min ceiling | 256 | 6.50 | below this reads as oppressive |
| cell | 64 | 1.63 | the grid, unchanged |

**Caveat.** Those hero heights are published character heights, which may
be lore or model figures rather than collision hulls. The hull is what
decides whether you fit through a gap, and only the game can confirm it.
Treat the table as `[I]`, inferred, not `[V]`.

## The grid stayed at 64

Deriving metres per unit does not derive the right cell size — it only
tells you what a cell is worth. 64 u is 1.63 m, which is a sensible
snapping increment for a hero of 120 u, and every figure above is a
multiple of it. Origins snap to 64, extents stay free.

## Regenerating

`mkplans.py` builds both example plans from the constants above. Editing
the numbers there and re-running beats hand-editing JSON, because the
relationships (wall thickness against interior span, step height against
ledge height) are what matter and they are easy to break by hand.
