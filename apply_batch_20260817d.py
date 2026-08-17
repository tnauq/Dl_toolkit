#!/usr/bin/env python3
"""
Manual tail step: fourth batch from the 2026-08-17 crosshair session.
Runs after apply_batch_20260817c.py. Name-keyed and idempotent.

op 1: close the room between axis_80 and the x=1467 wall stack with a
      cross wall on the axis_69 floor, then fill the enclosed volume solid
      up to the merged_84 top elevation.
op 2: shrink gapfill_39_44 flush with the south face of axis_24.
op 3: block on axis_0 in the east room, half the axis_0-to-level_473_east
      height, half the axis_70-to-axis_75 span and centred on it, north
      face flat against axis_24.

Usage:  python3 apply_batch_20260817d.py docs/plans/dust2_half.json
"""
import json, sys, copy

MAT = "materials/dev/reflectivity_30.vmat"

FLOOR_Z = 213.3        # axis_69 top, crosshair 3 of op 1
FILL_TOP = 666.9       # merged_84 top, crosshair 4 of op 1
WALL_TOP = 1280.3      # axis_80 top

# op 2: name, axis, side, pre-edit value, post-edit value
SHRINK = [
    ("gapfill_39_44", 1, "max", 3974.2, 3920.8),
]

def box(name, x, y, z):
    return {"name": name,
            "origin": [round((x[0] + x[1]) / 2.0, 1), round((y[0] + y[1]) / 2.0, 1), round((z[0] + z[1]) / 2.0, 1)],
            "extents": [round(x[1] - x[0], 1), round(y[1] - y[0], 1), round(z[1] - z[0], 1)],
            "angles": [0.0, 0.0, 0.0], "material": MAT}

NEW = [
    # op 1: cross wall on the south end of the gapfill_119_68 stack,
    # spanning the inner faces of axis_80 (x 666.9) and the stack (x 1467.0)
    box("axis_80_cross", (666.9, 1467.0), (3440.7, 3467.4), (FLOOR_Z, WALL_TOP)),
    # op 1: solid fill of the enclosed volume, top flush with merged_84
    box("axis_80_fill", (666.9, 1467.0), (3467.4, 3734.1), (FLOOR_Z, FILL_TOP)),
    # op 3
    box("axis_24_block", (2240.5, 2827.2), (3334.1, 3920.8), (-0.1, 380.7)),
]

def main(path):
    plan = json.load(open(path))
    boxes = plan["boxes"]
    idx = {b["name"]: i for i, b in enumerate(boxes)}
    log = []

    for name, axis, side, pre, post in SHRINK:
        if name not in idx:
            log.append("skip resize %s (absent)" % name)
            continue
        b = boxes[idx[name]]
        o, e = b["origin"], b["extents"]
        lo, hi = o[axis] - e[axis] / 2.0, o[axis] + e[axis] / 2.0
        cur = hi if side == "max" else lo
        if abs(cur - post) < 0.1:
            log.append("skip resize %s (already %.1f)" % (name, post))
            continue
        if abs(cur - pre) > 0.1:
            log.append("FAIL resize %s: expected %.1f, found %.1f" % (name, pre, cur))
            continue
        if side == "max":
            hi = post
        else:
            lo = post
        o[axis] = round((lo + hi) / 2.0, 1)
        e[axis] = round(hi - lo, 1)
        log.append("resize %s axis%d %s %.1f -> %.1f" % (name, axis, side, cur, post))

    for nb in NEW:
        if nb["name"] in idx:
            log.append("skip add %s (present)" % nb["name"])
            continue
        boxes.append(copy.deepcopy(nb))
        idx[nb["name"]] = len(boxes) - 1
        log.append("add %s" % nb["name"])

    json.dump(plan, open(path, "w"), indent=1)
    for line in log:
        print(line)
    print("boxes: %d" % len(boxes))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_half.json")
