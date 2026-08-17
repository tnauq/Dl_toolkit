#!/usr/bin/env python3
"""
Manual tail step: second batch of edits from the 2026-08-17 crosshair session.
Runs after apply_batch_20260817.py. Name-keyed and idempotent: each op records
the pre-edit value, so a rerun reports "skip" instead of applying twice.

Usage:  python3 apply_batch_20260817b.py docs/plans/dust2_half.json
"""
import json, sys, copy

MAT = "materials/dev/reflectivity_30.vmat"

def box(name, x, y, z, angles=(0.0, 0.0, 0.0), material=MAT):
    return {
        "name": name,
        "origin": [round((x[0] + x[1]) / 2.0, 1), round((y[0] + y[1]) / 2.0, 1), round((z[0] + z[1]) / 2.0, 1)],
        "extents": [round(x[1] - x[0], 1), round(y[1] - y[0], 1), round(z[1] - z[0], 1)],
        "angles": [float(a) for a in angles],
        "material": material,
    }

# ---- op 1: run the north floor plate west to the axis_733 wall face --------
# name, axis, side, pre-edit value, post-edit value
GROW = [
    ("axis_551_ext", 0, "min", -320.1, -506.8),
]

NEW = [
    # op 2: cube in the inner corner of axis_459 / axis_129.
    # 200.1 tall  = half the 400.2 clearance from axis_551 top to axis_769 underside
    # 200.0 square = half the 400.0 hall width between axis_547 and axis_129
    box("axis_129_corner_block", (-13.3, 186.7), (1707.0, 1907.0), (213.3, 413.4)),

    # op 3: wall closing the gap between axis_574 and axis_547, standing on
    # the axis_769 deck, top flush with axis_547
    box("axis_769_wall_s", (-600.1, -240.0), (2240.4, 2267.1), (653.5, 1067.0)),
]

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
