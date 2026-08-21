#!/usr/bin/env python3
"""batch9.py - sixteenth build step, run after batch8.py.

Sets a further set of railings to 60 units above the floor they guard,
and removes two boxes.

Each of these is a wall that runs from the ground up past a deck, so its
BASE is held and only its TOP comes down. New top = reference floor top
+ 60.00.

  railing            reference floor       top before -> after
  axis_81            axis_122     213.35     373.45 -> 273.35
  axis_267           gapfill_47_23 213.40    373.50 -> 273.40
  axis_28            axis_41      346.75     573.55 -> 406.75
  axis_31            axis_41      346.75     573.55 -> 406.75
  axis_32            axis_41      346.75     573.55 -> 406.75
  axis_30            axis_41      346.75     573.55 -> 406.75
  axis_549           axis_546     426.75     586.85 -> 486.75
  axis_548           axis_546     426.75     586.85 -> 486.75
  axis_583           axis_766     720.20     880.20 -> 780.20

Removed whole, with their m_ twins:

  yaw_584, axis_585

NOT CHANGED

  hex_rail_se / _s / _sw already stand 1066.95..1126.95 on hex_plat_s,
  whose top is 1067.00, so they are already 60.00 tall (60.05 counting
  the 0.05 they are bedded into the platform). Nothing to do.

  hex_rail_363 already stands 666.95..726.95 on axis_363_slab_ns, top
  666.90, so it is already 60.00 tall. Nothing to do.

  axis_73 is NOT touched. See the note in the reply: it is a 1280.30
  tall wall, not a railing-topped wall like the others, and cutting it to
  740.20 would remove 540.10 of full-height wall.

Every edit is applied to the half-side box and to its m_ twin with the
same z, which is correct because the plan transform leaves z untouched,
so symmetry is preserved exactly.

Idempotent and name-keyed: pre-edit origin/extents are recorded under
_batch9_pre and a rerun skips; removals are skipped if already gone.

Usage: python3 batch9.py docs/plans/dust2_full.json
"""

import json
import sys

CLEAR = 60.0

# railing name -> floor name whose top defines the height
RAILINGS = {
    "axis_81": "axis_122",
    "axis_267": "gapfill_47_23",
    "axis_28": "axis_41",
    "axis_31": "axis_41",
    "axis_32": "axis_41",
    "axis_30": "axis_41",
    "axis_549": "axis_546",
    "axis_548": "axis_546",
    "axis_583": "axis_766",
}

REMOVE = ["yaw_584", "axis_585"]


def top_of(box):
    return box["origin"][2] + box["extents"][2] / 2.0


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_full.json"
    with open(path) as f:
        plan = json.load(f)

    boxes = plan["boxes"]
    by_name = {b["name"]: b for b in boxes}

    changed = 0
    skipped = 0

    for rail, floor in RAILINGS.items():
        fbox = by_name.get(floor)
        if fbox is None:
            print("MISSING floor %s for %s" % (floor, rail))
            continue
        new_top = round(top_of(fbox) + CLEAR, 4)

        for name in (rail, "m_" + rail):
            box = by_name.get(name)
            if box is None:
                print("MISSING railing %s" % name)
                continue
            if "_batch9_pre" in box:
                skipped += 1
                continue

            ox, oy, oz = box["origin"]
            ex, ey, ez = box["extents"]
            base = oz - ez / 2.0
            if new_top <= base:
                print("SKIP %s: new top %.2f is at or below base %.2f"
                      % (name, new_top, base))
                continue

            h = round(new_top - base, 4)
            box["_batch9_pre"] = {"origin": [ox, oy, oz], "extents": [ex, ey, ez]}
            box["origin"] = [ox, oy, round(base + h / 2.0, 4)]
            box["extents"] = [ex, ey, h]
            changed += 1

            print("%-16s on %-16s base %8.2f  top %8.2f -> %8.2f  h %8.2f -> %8.2f"
                  % (name, floor, base, oz + ez / 2.0, new_top, ez, h))

    gone = []
    for name in REMOVE:
        for n in (name, "m_" + name):
            if n in by_name:
                gone.append(n)
    if gone:
        keep = set(gone)
        plan["boxes"] = [b for b in boxes if b["name"] not in keep]
        print("removed: " + ", ".join(sorted(gone)))
    else:
        print("removals already applied")

    with open(path, "w") as f:
        json.dump(plan, f, indent=1)

    print("changed %d, skipped %d, boxes %d" % (changed, skipped, len(plan["boxes"])))


if __name__ == "__main__":
    main()
