#!/usr/bin/env python3
"""
Manual tail step: fifteenth batch from the 2026-08-17 crosshair session.
Runs after apply_batch_20260817n.py. Name-keyed and idempotent.

Ceiling over the keyhole-shaped room west of axis_547, traced by
rasterising solidity at z = 1053. Two slabs: the wide western bulb between
axis_568 and axis_567, and the narrower eastern stem between axis_571 and
axis_572. Height matches the 1067.0 walls that bound it, same band as the
existing ceiling_467_room.

Usage:  python3 apply_batch_20260817o.py docs/plans/dust2_half.json
"""
import json, sys

MAT = "materials/dev/reflectivity_30.vmat"
CEIL = (1040.4, 1067.0)

def box(name, x, y, z):
    return {"name": name,
            "origin": [round((x[0] + x[1]) / 2.0, 1), round((y[0] + y[1]) / 2.0, 1), round((z[0] + z[1]) / 2.0, 1)],
            "extents": [round(x[1] - x[0], 1), round(y[1] - y[0], 1), round(z[1] - z[0], 1)],
            "angles": [0.0, 0.0, 0.0], "material": MAT}

NEW = [
    # bulb: axis_565 west, axis_568 south, axis_567 north
    box("ceiling_565_571_bulb", (-733.4, -520.1), (373.5, 640.1), CEIL),
    # stem: axis_571 south, axis_572 north, axis_547 east
    box("ceiling_565_571_stem", (-520.1, -240.0), (426.8, 586.8), CEIL),
    # seam over the yaw_570 / yaw_573 chamfer corners, where the diagonal
    # leaves the bulb and stem edges short of each other
    box("ceiling_565_571_seam", (-520.1, -446.3), (373.5, 640.1), CEIL),
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
