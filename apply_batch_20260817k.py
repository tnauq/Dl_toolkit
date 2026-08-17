#!/usr/bin/env python3
"""
Manual tail step: eleventh batch from the 2026-08-17 crosshair session.
Runs after apply_batch_20260817j.py. Name-keyed and idempotent.

op 1: ceiling over the hall between gapfill_80_61 and axis_68_upper.
op 2: ceiling over the room between axis_364 and axis_366.
op 3: raise axis_547, axis_769_wall_s, axis_479_hdr and axis_457 to the
      axis_574 top elevation.

Usage:  python3 apply_batch_20260817k.py docs/plans/dust2_half.json
"""
import json, sys

MAT = "materials/dev/reflectivity_30.vmat"
TOP = 1280.3          # axis_574 top
CEIL = (1253.7, TOP)  # flush with the wall tops, 26.6 thick

# name, pre-edit z max, post-edit z max
RAISE = [
    ("axis_547",        1067.0, TOP),
    ("axis_769_wall_s", 1067.0, TOP),
    ("axis_479_hdr",    1067.0, TOP),
    ("axis_457",        1067.0, TOP),
]

def box(name, x, y, z):
    return {"name": name,
            "origin": [round((x[0] + x[1]) / 2.0, 1), round((y[0] + y[1]) / 2.0, 1), round((z[0] + z[1]) / 2.0, 1)],
            "extents": [round(x[1] - x[0], 1), round(y[1] - y[0], 1), round(z[1] - z[0], 1)],
            "angles": [0.0, 0.0, 0.0], "material": MAT}

NEW = [
    # between the inner faces of gapfill_80_61 and axis_68_upper,
    # over the gapfill_80_61 y run
    box("ceiling_80_68", (666.9, 1467.0), (3867.4, 5067.6), CEIL),
    # between axis_747 and axis_365, over the axis_364 to axis_366 gap
    box("ceiling_364_366", (-973.5, 106.7), (3627.3, 4027.5), CEIL),
]

def main(path):
    plan = json.load(open(path))
    boxes = plan["boxes"]
    idx = {b["name"]: i for i, b in enumerate(boxes)}
    log = []

    for name, pre, post in RAISE:
        if name not in idx:
            log.append("skip raise %s (absent)" % name)
            continue
        b = boxes[idx[name]]
        o, e = b["origin"], b["extents"]
        lo, hi = o[2] - e[2] / 2.0, o[2] + e[2] / 2.0
        if abs(hi - post) < 0.1:
            log.append("skip raise %s (already %.1f)" % (name, post))
            continue
        if abs(hi - pre) > 0.1:
            log.append("FAIL raise %s: expected z max %.1f, found %.1f" % (name, pre, hi))
            continue
        o[2] = round((lo + post) / 2.0, 1)
        e[2] = round(post - lo, 1)
        log.append("raise %s z max %.1f -> %.1f" % (name, hi, post))

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
