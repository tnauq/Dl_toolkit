#!/usr/bin/env python3
"""
Manual tail step: ninth batch from the 2026-08-17 crosshair session.
Runs after apply_batch_20260817h.py. Name-keyed and idempotent.

op 1: gapfill_25_36 east to the axis_81 west face.
op 2: gapfill_378_366 north to the axis_371 south face.
op 3: close both gaps around the compound_478 pillar (axis_467 to the
      west, axis_450_south to the north), same defect class as the
      yaw_* corner columns in batch g.

Usage:  python3 apply_batch_20260817i.py docs/plans/dust2_half.json
"""
import json, sys

MAT = "materials/dev/reflectivity_30.vmat"

# name, axis, side, pre-edit value, post-edit value
GROW = [
    ("gapfill_25_36",   0, "max",  613.5,  640.1),
    ("gapfill_378_366", 1, "max", 4494.2, 4907.7),
]

FILLERS = [
    ("gapfill_478_467", (1280.2, 1326.8), (   0.0,   26.6), (213.4, 1067.0)),
    ("gapfill_478_450", (1467.0, 1493.6), ( 132.8,  186.8), (213.4, 1067.0)),
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

    for name, axis, side, pre, post in GROW:
        if name not in idx:
            log.append("skip grow %s (absent)" % name)
            continue
        b = boxes[idx[name]]
        o, e = b["origin"], b["extents"]
        lo, hi = o[axis] - e[axis] / 2.0, o[axis] + e[axis] / 2.0
        cur = hi if side == "max" else lo
        if abs(cur - post) < 0.1:
            log.append("skip grow %s (already %.1f)" % (name, post))
            continue
        if abs(cur - pre) > 0.1:
            log.append("FAIL grow %s: expected %.1f, found %.1f" % (name, pre, cur))
            continue
        if side == "max":
            hi = post
        else:
            lo = post
        o[axis] = round((lo + hi) / 2.0, 1)
        e[axis] = round(hi - lo, 1)
        log.append("grow %s axis%d %s %.1f -> %.1f" % (name, axis, side, cur, post))

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
