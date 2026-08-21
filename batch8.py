#!/usr/bin/env python3
"""batch8.py - fifteenth build step, run after batch7.py.

Sets every true railing in the map to 60 units tall, holding its BASE
fixed so the piece still stands on the surface it stands on now. Only
the top comes down.

WHAT COUNTS AS A RAILING HERE

Eight named pieces plus their m_ twins:

  hex_rail_se, hex_rail_s, hex_rail_sw   160.1 -> 60.0   (hexagon parapets)
  hex_rail_363, hex_rail_473             160.1 -> 60.0
  balcony_75_rail_e / _s / _n            106.7 -> 60.0   (batch5 balcony)

NOT TOUCHED, and why:

  rail_c_fill / m_rail_c_fill  is not a railing. It is a 26.70 square
  section strip 800.10 long lying flat between the two walk.py tracks at
  z 331.20, filling the slot where the cross leg splits. It is the piece
  named "rail" that is not one.

  rail_n_end, rail_n_fade and the original railings they extend
  (axis_786, axis_788, axis_789) are all 106.70 boxes based at 213.35,
  which is merged_721's top, deck 3. They stand only 40.00 proud of
  deck 1 (axis_790 top, 280.05). Making them 60 would make them TALLER
  from the deck-1 side, not shorter, so they are left alone pending a
  decision.

Both the half-side box and its m_ twin are edited with the same z, which
is correct because the plan transform leaves z untouched, so symmetry is
preserved exactly.

Idempotent and name-keyed: the pre-edit origin/extents are recorded on
the box under _batch8_pre, so a rerun sees the record and skips.

Usage: python3 batch8.py docs/plans/dust2_full.json
"""

import json
import sys

TARGET_H = 60.0

RAILINGS = [
    "hex_rail_se",
    "hex_rail_s",
    "hex_rail_sw",
    "hex_rail_363",
    "hex_rail_473",
    "balcony_75_rail_e",
    "balcony_75_rail_s",
    "balcony_75_rail_n",
]


def targets():
    out = []
    for n in RAILINGS:
        out.append(n)
        out.append("m_" + n)
    return out


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_full.json"
    with open(path) as f:
        plan = json.load(f)

    boxes = plan["boxes"]
    by_name = {b["name"]: b for b in boxes}

    changed = 0
    skipped = 0
    missing = []

    for name in targets():
        box = by_name.get(name)
        if box is None:
            missing.append(name)
            continue
        if "_batch8_pre" in box:
            skipped += 1
            continue

        ox, oy, oz = box["origin"]
        ex, ey, ez = box["extents"]
        base = oz - ez / 2.0

        box["_batch8_pre"] = {"origin": [ox, oy, oz], "extents": [ex, ey, ez]}
        box["origin"] = [ox, oy, round(base + TARGET_H / 2.0, 4)]
        box["extents"] = [ex, ey, TARGET_H]
        changed += 1

        print(
            "%-22s h %8.2f -> %5.2f   base %9.2f held   top %9.2f -> %9.2f"
            % (name, ez, TARGET_H, base, base + ez, base + TARGET_H)
        )

    if missing:
        print("MISSING (not in plan): " + ", ".join(missing))

    with open(path, "w") as f:
        json.dump(plan, f, indent=1)

    print("changed %d, skipped %d, boxes %d" % (changed, skipped, len(boxes)))


if __name__ == "__main__":
    main()
