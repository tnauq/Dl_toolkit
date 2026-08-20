#!/usr/bin/env python3
"""thin.py - seventh build step, run after arch.py.

Shrinks seam_wall_restore (and its m_ twin) from 186.8 thick to 26.7,
matching seam_w_s. The face that touches merged_84 is held fixed, so the
connection to the upper floor plate is preserved; the wall loses its
material on the far side only.

Idempotent and name-keyed: the pre-edit origin/extents are recorded in
the box under _thin_pre, so a rerun sees the record and skips.

Usage: python3 thin.py docs/plans/dust2_full.json
"""

import json
import sys

TARGET_THICK = 26.7

# name -> which y face is held. "min" holds the low-y face, "max" the high-y.
# seam_wall_restore touches merged_84 on its low-y face (y 5067.6 meets the
# plate edge at 5067.7). The mirrored twin touches m_merged_84 on its
# high-y face (y 7102.5 meets 7102.4).
EDITS = {
    "seam_wall_restore": "min",
    "m_seam_wall_restore": "max",
}


def main(path):
    with open(path) as f:
        plan = json.load(f)

    by_name = {b["name"]: b for b in plan["boxes"]}
    changed = 0

    for name, hold in EDITS.items():
        box = by_name.get(name)
        if box is None:
            print("SKIP %s: not in plan" % name)
            continue
        if "_thin_pre" in box:
            print("SKIP %s: already thinned (pre %s)"
                  % (name, box["_thin_pre"]["extents"]))
            continue

        origin = list(box["origin"])
        extents = list(box["extents"])
        old_thick = extents[1]

        if abs(old_thick - TARGET_THICK) < 1e-6:
            print("SKIP %s: already %.1f thick" % (name, TARGET_THICK))
            continue
        if old_thick < TARGET_THICK:
            print("SKIP %s: %.1f is thinner than target %.1f"
                  % (name, old_thick, TARGET_THICK))
            continue

        y_min = origin[1] - old_thick / 2.0
        y_max = origin[1] + old_thick / 2.0

        if hold == "min":
            new_y = y_min + TARGET_THICK / 2.0
        else:
            new_y = y_max - TARGET_THICK / 2.0

        box["_thin_pre"] = {"origin": list(origin), "extents": list(extents)}
        box["origin"][1] = round(new_y, 4)
        box["extents"][1] = TARGET_THICK
        changed += 1

        print("THIN %s: thickness %.1f -> %.1f, y %.2f..%.2f -> %.2f..%.2f "
              "(held %s face)"
              % (name, old_thick, TARGET_THICK, y_min, y_max,
                 new_y - TARGET_THICK / 2.0, new_y + TARGET_THICK / 2.0,
                 hold))

    print("thin.py: %d changed, %d boxes in plan" % (changed, len(plan["boxes"])))

    with open(path, "w") as f:
        json.dump(plan, f, indent=1)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_full.json")
