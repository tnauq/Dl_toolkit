#!/usr/bin/env python3
"""Batch ab: close the two open platform-end gaps in the big hexagon.

Adds one wall on each side of the arena, joining the outer end of the
NE/NW hexagon wall to the outer end of the SE/SW platform parapet:

  hex_wall_ne_r end (1625.2, -3816.1)  ->  hex_par_se end (2177.8, -4133.1)
  hex_wall_nw_l end (-1625.2, -3816.1) ->  hex_par_sw end (-2177.8, -4133.1)

Both run on the SE/SW face normal (yaw -30 / 210), are 26.7 thick, and
span z 1067.0 to 1707.2, matching the parapets exactly.

Name-keyed and idempotent: adds skip if the box name is already present.

    python3 apply_batch_20260817ab.py docs/plans/dust2_half.json
"""

import json
import sys

MAT = "materials/dev/reflectivity_30.vmat"

# centre = midpoint of the two wall-centreline ends
# length  = 637.1 span + 13.35 buried into each neighbour = 663.8
ADDS = [
    {
        "name": "hex_par_se_end",
        "origin": [1901.5, -3974.6, 1387.1],
        "extents": [663.8, 26.7, 640.2],
        "angles": [0.0, -30.0, 0.0],
        "material": MAT,
    },
    {
        "name": "hex_par_sw_end",
        "origin": [-1901.5, -3974.6, 1387.1],
        "extents": [663.8, 26.7, 640.2],
        "angles": [0.0, 210.0, 0.0],
        "material": MAT,
    },
]


def main(path):
    with open(path) as f:
        plan = json.load(f)

    have = {b["name"] for b in plan["boxes"]}
    added = 0
    for box in ADDS:
        if box["name"] in have:
            print("SKIP add %s (already present)" % box["name"])
            continue
        plan["boxes"].append(json.loads(json.dumps(box)))
        have.add(box["name"])
        added += 1
        print("ADD  %s" % box["name"])

    with open(path, "w") as f:
        json.dump(plan, f, indent=1)
        f.write("\n")

    print("added %d, plan now %d boxes" % (added, len(plan["boxes"])))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_half.json")
