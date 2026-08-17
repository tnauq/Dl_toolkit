#!/usr/bin/env python3
"""
Manual tail step: seventh batch from the 2026-08-17 crosshair session.
Runs after apply_batch_20260817f.py. Name-keyed and idempotent.

op 1: widen axis_721_block to a jumpable footprint.
op 2: close the wall leaks where an axis-aligned wall stops short of a
      45 degree corner column. Twelve found map-wide, on yaw_453, yaw_455,
      yaw_566, yaw_569, yaw_570 and yaw_573. Each filler spans the wall's
      own cross-section and z range, and runs back to the deepest point of
      the column face, so it never protrudes past the diagonal.

Usage:  python3 apply_batch_20260817g.py docs/plans/dust2_half.json
"""
import json, sys, copy

MAT = "materials/dev/reflectivity_30.vmat"

# name, axis, pre-edit extent, post-edit extent (centre held)
RESIZE = [
    ("axis_721_block", 0, 53.8, 160.0),
    ("axis_721_block", 1, 53.8, 160.0),
]

FILLERS = [
    ("gapfill_453_449", (1280.2, 1342.5), (1093.6, 1120.2), (213.4, 1067.0)),
    ("gapfill_453_450", (1467.0, 1493.6), ( 906.9,  969.1), (213.4, 1067.0)),
    ("gapfill_455_449", ( 577.9,  640.2), (1093.6, 1120.2), (213.4, 1067.0)),
    ("gapfill_455_454", ( 426.8,  453.5), ( 906.9,  969.2), (213.4, 1067.0)),
    ("gapfill_566_565", (-760.1, -733.4), ( 586.8,  610.0), (213.4, 1067.0)),
    ("gapfill_566_567", (-703.4, -680.1), ( 640.1,  666.9), (213.4, 1067.0)),
    ("gapfill_569_565", (-760.1, -733.4), ( 403.6,  426.8), (213.4, 1067.0)),
    ("gapfill_569_568", (-703.4, -680.1), ( 346.8,  373.5), (213.4, 1067.0)),
    ("gapfill_570_568", (-520.1, -491.6), ( 346.8,  373.5), (213.4, 1067.0)),
    ("gapfill_570_571", (-496.0, -466.8), ( 400.0,  426.8), (213.4, 1067.0)),
    ("gapfill_573_567", (-520.1, -510.4), ( 640.1,  666.9), (213.4, 1067.0)),
    ("gapfill_573_572", (-476.5, -466.8), ( 586.8,  613.5), (213.4, 1067.0)),
]

def box(name, x, y, z):
    return {"name": name,
            "origin": [round((x[0] + x[1]) / 2.0, 1), round((y[0] + y[1]) / 2.0, 1), round((z[0] + z[1]) / 2.0, 1)],
            "extents": [round(x[1] - x[0], 1), round(y[1] - y[0], 1), round(z[1] - z[0], 1)],
            "angles": [0.0, 0.0, 0.0], "material": MAT}

def main(path):
    plan = json.load(open(path))
    boxes = plan["boxes"]
    idx = {b["name"]: i for i, b in enumerate(boxes)}
    log = []

    for name, axis, pre, post in RESIZE:
        if name not in idx:
            log.append("skip resize %s (absent)" % name)
            continue
        e = boxes[idx[name]]["extents"]
        if abs(e[axis] - post) < 0.1:
            log.append("skip resize %s axis%d (already %.1f)" % (name, axis, post))
            continue
        if abs(e[axis] - pre) > 0.1:
            log.append("FAIL resize %s axis%d: expected %.1f, found %.1f" % (name, axis, pre, e[axis]))
            continue
        e[axis] = post
        log.append("resize %s axis%d %.1f -> %.1f" % (name, axis, pre, post))

    for name, x, y, z in FILLERS:
        if name in idx:
            log.append("skip add %s (present)" % name)
            continue
        boxes.append(box(name, x, y, z))
        idx[name] = len(boxes) - 1
        log.append("add %s" % name)

    json.dump(plan, open(path, "w"), indent=1)
    for line in log:
        print(line)
    print("boxes: %d" % len(boxes))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_half.json")
