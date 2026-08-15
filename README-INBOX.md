# Inbox drop — dust2 half-map, extracted and verified (2026-08-14)

Unzip at repo root, run `inbox`.

## NEW
    docs/plans/dust2_half.json    1071 boxes, Deadlock scale, ONE half
    tools/extract.py              BSP -> brush bounds + classification
    tools/simplify.py             classify, flatten, merge
    tools/slab.py                 wedges -> pitched slabs
    tools/diff.py                 reachability verification

## REPLACES
    docs/plans/index.json         adds the dust2 entry

The BSP itself is NOT included. Keep it out of `docs/` — Pages would
publish it.

## THE HEADLINE: pitched slabs, not bounding boxes

This build of de_dust2 makes its GROUND out of wedges. Bounding-boxing a
wedge fills the space above its sloped face, so a pure AABB conversion
turns every sloped floor into a solid block.

Measured, not guessed:

| conversion | reachable footprint | verdict |
|---|---|---|
| pure AABB | collapsed to ~2,768 voxels | unwalkable |
| pitched slabs | 9,618 of 11,228 columns | **85.7% retained** |

345 wedges became pitched slabs, none rejected. The remaining 1,610 lost
columns cluster at (1024-1536, 1024-2048) in source coordinates: mid and
catwalk, where wedges stack instead of lying flat.

**Without the reachability check this would have shipped.** The AABB box
list was valid JSON, emitted cleanly, and would have passed the census and
the round trip while being a solid mass. Nothing but a flood fill catches
that.

## A MEASUREMENT ERROR WORTH RECORDING

The first diff compared voxel COUNTS and reported 86.5% recovered. The
slabbed floors sit at slightly different heights, so identical ground
lands in different z cells; a cell-wise diff was comparing different sets
that happened to be similar in size. Corrected to a FOOTPRINT comparison —
is the same (x,y) ground reachable at any height — the real figure is
85.7%. Close by luck. **Comparing counts is not comparing sets.**

## What this file is and is not

**Is:** one half of dust2, every solid brush, scaled 1.667x to hero scale.
156 x 160 x 19 m. 406 ramps carrying real pitch.

**Is not:** symmetric, stitched, or modified. No mirror, no 180-degree
rotation, no 30 m middle band. That is the next step and it is deliberately
separate — walk this first and confirm the geometry is worth keeping before
it gets doubled.

## Expect the viewer to struggle

1071 boxes is roughly 67,000 tiles if every face drew, against about 2,200
for the sealed room. The renderer has no distance culling and no depth
buffer, only a painter's sort over every tile. It will be slow and it may
sort wrong where boxes interpenetrate.

If it is unusable, the fix is a distance cull plus a tile-size floor in the
viewer, not a smaller map. Say so and it is a short change.

## Known soft spots

- **Ramp slab thickness is a flat 32 u** before scaling. Under a ramp that
  sat on thicker ground, there is now a gap.
- **26 compound brushes** became bounding boxes. They over-fill, which
  blocks rather than opens, which is the safer direction.
- **86 angled walls** are still AABBs; their yaw is recorded but unused.
- **The 15 dropped brushes** were 10 tool-texture (skybox shell) and 4
  ladder volumes and 1 degenerate. Ladders will need re-adding as geometry
  or ramps if those routes matter.
