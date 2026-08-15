# Inbox drop — dust2 half, walls and ceilings doubled (2026-08-14)

REPLACES `docs/plans/dust2_half.json`. Adds `tools/walls.py`.
**Supersedes the previous double-height drop** — that one doubled the
floorplan's elevations too and turned 255 ramps into walls. Discard it;
`tools/double.py` can go.

## What changed, and what deliberately did not

| | count | treatment |
|---|---|---|
| wall | 158 | bottom stays put, height doubles upward |
| ceiling | 9 | bottom raised so the gap beneath doubles |
| ramp | 407 | **untouched** |
| cover | 465 | **untouched** |
| floor | 24 | **untouched** |

Ramp pitches are unchanged, max still 58.9 degrees. Floor elevations are
unchanged, so nothing that was walkable stopped being walkable.

## The classification, since it is a judgement call

All in Deadlock units, hero = 120 u:

- **ramp** — anything with a pitch. Doubling it would steepen the
  gradient, which was the whole problem last time.
- **cover** — under 192 u tall (about 1.6 heroes). A crate is not a wall,
  and a 2 m box should not become 4 m.
- **ceiling** — a broad flat slab with at least hero-height clearance
  under it. Its bottom is raised so the gap below doubles, rather than the
  slab getting thicker.
- **wall** — the rest, 192 u or taller. Bottom fixed, extent doubles.

Support height per box is found by looking for the highest overlapping top
beneath it, which is what tells a ceiling apart from a floor.

Only 9 ceilings because most of dust2 is open to the sky — most of what
grew is perimeter and building walls, now 32.5 m at the tallest.

## Worth a look when you walk it

- **Cover at 465 boxes is the biggest untouched group.** If some of what I
  classified as cover reads as a low wall you wanted taller, the threshold
  is one constant (`WALL_MIN`) in `tools/walls.py`.
- **Doubling only the tops** means a wall that used to meet a ceiling now
  overshoots it where the ceiling did not qualify as one. Sky-open areas
  are unaffected; interiors are where to check.
