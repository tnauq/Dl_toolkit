#!/usr/bin/env python3
"""
Manual tail step: eighth batch from the 2026-08-17 crosshair session.
Runs after apply_batch_20260817g.py. Name-keyed and idempotent.

op 1: patch the hole between the axis_363_slab_ew south edge and the
      axis_127 / axis_363 north faces.
op 2: enclose the open span of the sky bridge with side walls and a roof,
      between the two arch door walls.

Usage:  python3 apply_batch_20260817h.py docs/plans/dust2_half.json
"""
import json, sys

MAT = "materials/dev/reflectivity_30.vmat"

SLAB_Z = (640.1, 666.9)
BRIDGE_X = (1093.5, 1346.5)
SPAN_Y = (3147.3, 3440.7)     # axis_79 north face to the axis_80_cross south face
WALL_T = 26.7
TOP = 1280.3                  # matches both door walls and both openings
BASE = 640.1                  # below the ramp underside at every point (min 660.2)

def box(name, x, y, z):
    return {"name": name,
            "origin": [round((x[0] + x[1]) / 2.0, 1), round((y[0] + y[1]) / 2.0, 1), round((z[0] + z[1]) / 2.0, 1)],
            "extents": [round(x[1] - x[0], 1), round(y[1] - y[0], 1), round(z[1] - z[0], 1)],
            "angles": [0.0, 0.0, 0.0], "material": MAT}

NEW = [
    # op 1
    box("gapfill_363_127", (160.0, 387.1), (3627.8, 3694.5), SLAB_Z),
    # op 2: side walls sit outside the 253.0 deck so the walkable width is unchanged
    box("axis_473_bridge_wall_w", (BRIDGE_X[0] - WALL_T, BRIDGE_X[0]), SPAN_Y, (BASE, TOP)),
    box("axis_473_bridge_wall_e", (BRIDGE_X[1], BRIDGE_X[1] + WALL_T), SPAN_Y, (BASE, TOP)),
    box("axis_473_bridge_roof",
        (BRIDGE_X[0] - WALL_T, BRIDGE_X[1] + WALL_T), SPAN_Y, (TOP - 26.6, TOP)),
]

def main(path):
    plan = json.load(open(path))
    boxes = plan["boxes"]
    idx = {b["name"]: i for i, b in enumerate(boxes)}
    log = []
    for nb in NEW:
        if nb["name"] in idx:
            log.append("skip add %s (present)" % nb["name"])
            continue
        boxes.append(nb)
        idx[nb["name"]] = len(boxes) - 1
        log.append("add %s" % nb["name"])
    json.dump(plan, open(path, "w"), indent=1)
    for line in log:
        print(line)
    print("boxes: %d" % len(boxes))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_half.json")
