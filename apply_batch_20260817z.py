#!/usr/bin/env python3
"""
Manual tail step: twenty-sixth batch from the 2026-08-17 crosshair session.
Runs after apply_batch_20260817y.py. Name-keyed and idempotent.

op 1: railing on the open north edge of axis_363_slab_ns.
op 2: railing on the open east edge of level_473_east, left open at the
      north end.
op 3: extend hex2_tun_e_roof east to meet axis_d553s_hdr.
op 4/5: run axis_563, axis_454 and axis_467 into their neighbouring
      compound_ pillars. Depths measured by marching each wall's own
      cross-section into the rotated pillar, same method as batch g.

Usage:  python3 apply_batch_20260817z.py docs/plans/dust2_half.json
"""
import json, sys

MAT = "materials/dev/reflectivity_30.vmat"
RAIL_H = 160.1
RAIL_T = 26.7

# name, axis, side, pre-edit value, post-edit value
GROW = [
    ("hex2_tun_e_roof", 0, "max", -2311.9, -2133.8),
    ("axis_563",        1, "max",  -693.4,   -652.4),
    ("axis_454",        1, "min",   106.7,     55.5),
    ("axis_467",        0, "min",   560.2,    519.0),
]

def box(name, x, y, z):
    return {"name": name,
            "origin": [round((x[0] + x[1]) / 2.0, 1), round((y[0] + y[1]) / 2.0, 1), round((z[0] + z[1]) / 2.0, 1)],
            "extents": [round(x[1] - x[0], 1), round(y[1] - y[0], 1), round(z[1] - z[0], 1)],
            "angles": [0.0, 0.0, 0.0], "material": MAT}

NEW = [
    # north edge of the axis_363 slab, between axis_370 and merged_97
    box("hex_rail_363", (160.0, 640.1), (3920.8, 3947.5), (666.9, 666.9 + RAIL_H)),
    # east edge of level_473_east, from axis_191 up to 253 short of axis_24
    box("hex_rail_473", (2200.3 - RAIL_T, 2200.3), (2773.9, 3667.8), (761.4, 761.4 + RAIL_H)),
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
        if abs(cur - post) < 0.15:
            log.append("skip grow %s (already %.1f)" % (name, post))
            continue
        if abs(cur - pre) > 0.15:
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
        boxes.append(nb)
        idx[nb["name"]] = len(boxes) - 1
        log.append("add %s" % nb["name"])

    json.dump(plan, open(path, "w"), indent=1)
    for line in log:
        print(line)
    print("boxes: %d" % len(boxes))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_half.json")
