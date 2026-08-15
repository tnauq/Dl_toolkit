# Inbox drop — arch raised (2026-08-14)

REPLACES `docs/plans/dust2_half.json`. Adds `tools/archfix.py`.

## The crosshair worked, and it found a real class of bug

`ramp-slab_872` is one voussoir of an actual masonry arch: a fan of 16
wedges (`ramp-slab_861`..`876`) plus four crown slabs on two piers
(`axis_480`, `axis_481`). Every one of them stayed put while the wall
panels either side (`axis_482`, `axis_483`) doubled and the wall behind
(`axis_468`) doubled. One wall assembly, scaled in pieces.

Two classifier mistakes caused it:

- **The voussoirs are 27 u (0.7 m) thick.** I treated anything pitched as
  walkable terrain. You cannot walk on something 0.7 m wide — that is
  masonry.
- **The piers are 136 u tall**, under the 192 u wall threshold, so they
  were called cover and left alone.

The arch is now scaled about z=427, the same datum the wall used, so the
whole assembly moves together. Piers 426 -> 698, crown 853, against a wall
top of 854. 19 boxes raised.

## I could not solve this generally, and stopped trying

Four attempts, each failing for a different reason worth recording:

1. **Classify by width.** Swept 373 terrain wedges into "structure" —
   dust2's sloped ground is built from narrow strips too, so a 0.7 m
   voussoir and a 0.7 m ground strip are identical by shape.
2. **Classify by "is it standable on top".** Left the arch alone: an
   arch's outer curve IS standable, if you could get there.
3. **Use reachability instead.** Better, but most terrain wedges are
   BURIED FILL beneath the surface, so "reachable on top" is false for
   ground too.
4. **Classify by elevation relative to the walkable floor, then group
   touching boxes into assemblies.** Closest yet, but the voussoirs do
   not quite touch each other, so they landed in different assemblies and
   the arch still fragmented.

The honest position: separating "ground" from "envelope" in a brush soup
is not reliably automatable at this resolution, and each failed attempt
cost a full pipeline run. Cap the yak-shave.

**So the workflow is now: you crosshair a broken spot, I fix that
assembly.** `tools/archfix.py` is the pattern — a bounding region and the
datum to scale about, about ten lines. That is cheaper and more reliable
than another classifier, and it is exactly what the copy-pos button was
for.

## Unchanged from the last good state

158 walls doubled, 9 ceilings raised, 407 ramps and 465 cover and 24
floors untouched. Ramp pitches unchanged, max 58.9 degrees. Tallest point
32.5 m.
