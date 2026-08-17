#!/usr/bin/env python3
"""
Manual tail step: twelfth batch from the 2026-08-17 crosshair session.
Runs after apply_batch_20260817k.py. Name-keyed and idempotent.

op 1: raise axis_479, axis_479_far, axis_572, axis_567 and yaw_573 to the
      axis_547 top elevation.
op 2: ceiling the two spaces those raises now fully enclose.

Usage:  python3 apply_batch_20260817l.py docs/plans/dust2_half.json
"""
import json, sys

MAT = "materials/dev/reflectivity_30.vmat"
TOP = 1280.3
CEIL = (1253.7, TOP)

RAISE = [
    ("axis_479",     1067.0, TOP),
    ("axis_479_far", 1067.0, TOP),
    ("axis_572",     1067.0, TOP),
    ("axis_567",     1067.0, TOP),
    ("yaw_573",      1067.0, TOP),
]

def box(name, x, y, z):
    return {"name": name,
            "origin": [round((x[0] + x[1]) / 2.0, 1), round((y[0] + y[1]) / 2.0, 1), round((z[0] + z[1]) / 2.0, 1)],
            "extents": [round(x[1] - x[0], 1), round(y[1] - y[0], 1), round(z[1] - z[0], 1)],
            "angles": [0.0, 0.0, 0.0], "material": MAT}

NEW = [
    # north-south corridor: axis_547 west, axis_457 east, the axis_479 door
    # wall south, axis_463 north
    box("ceiling_547_457", (-213.3, 186.7), (-213.3, 880.1), CEIL),
    # west hall: axis_547 east, axis_574 west, the axis_567 / yaw_573 /
    # axis_572 line south, axis_769_wall_s north
    box("ceiling_547_574", (-600.1, -240.0), (613.5, 2240.5), CEIL),
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
