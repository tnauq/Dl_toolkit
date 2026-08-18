#!/usr/bin/env python3
"""
Manual tail step: nineteenth batch from the 2026-08-17 crosshair session.
Runs after apply_batch_20260817r.py. Name-keyed and idempotent.

Fourth copy of the big arch, in the centre of axis_468_far. Same wall
normal, thickness, bottom and top as axis_468, so it is a pure translation
of the _d468 pieces. Sits on the 213.3 floor, so no sill block.

Usage:  python3 apply_batch_20260817s.py docs/plans/dust2_half.json
"""
import json, sys, copy

MAT = "materials/dev/reflectivity_30.vmat"

WALL = "axis_468_far"
WALL_X = (200.0, 1920.4)
WALL_Y = -813.5
Z_BOT, Z_TOP = 213.4, 1067.0
SPRING = 911.8
JAMB_OUT, JAMB_IN = 200.05, 165.2
SUFFIX = "_d468c"
ARCH_X = 1600.25      # aligned under the axis_562 arch for a straight link

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

    def add(nb):
        if nb["name"] in idx:
            log.append("skip add %s (present)" % nb["name"])
            return
        boxes.append(copy.deepcopy(nb))
        idx[nb["name"]] = len(boxes) - 1
        log.append("add %s" % nb["name"])

    o_lo, o_hi = ARCH_X - JAMB_OUT, ARCH_X + JAMB_OUT
    i_lo, i_hi = ARCH_X - JAMB_IN, ARCH_X + JAMB_IN
    wy = (WALL_Y - 13.4, WALL_Y + 13.4)

    if WALL not in idx:
        log.append("FAIL %s absent" % WALL)
    else:
        w = boxes[idx[WALL]]
        lo = w["origin"][0] - w["extents"][0] / 2.0
        hi = w["origin"][0] + w["extents"][0] / 2.0
        if abs(hi - o_lo) < 0.1:
            log.append("skip trim %s (already %.1f)" % (WALL, o_lo))
        elif abs(hi - WALL_X[1]) > 0.1:
            log.append("FAIL trim %s: expected x max %.1f, found %.1f" % (WALL, WALL_X[1], hi))
        else:
            w["origin"][0] = round((lo + o_lo) / 2.0, 1)
            w["extents"][0] = round(o_lo - lo, 1)
            log.append("trim %s -> x[%.1f,%.1f]" % (WALL, lo, o_lo))

    add(box(WALL + SUFFIX + "_far",    (o_hi, WALL_X[1]), wy, (Z_BOT, Z_TOP)))
    add(box(WALL + SUFFIX + "_jamb_w", (o_lo, i_lo),      wy, (Z_BOT, SPRING)))
    add(box(WALL + SUFFIX + "_jamb_e", (i_hi, o_hi),      wy, (Z_BOT, SPRING)))

    src = [b for b in boxes if b["name"].endswith("_d468")]
    if not src:
        log.append("FAIL no _d468 arch pieces to clone")
    n = 0
    for b in src:
        nb = copy.deepcopy(b)
        nb["name"] = b["name"][: -len("_d468")] + SUFFIX
        nb["origin"] = [round(b["origin"][0] + ARCH_X, 1), b["origin"][1], b["origin"][2]]
        add(nb)
        n += 1
    log.append("arch pieces cloned to %s: %d" % (SUFFIX, n))

    json.dump(plan, open(path, "w"), indent=1)
    for line in log:
        print(line)
    print("boxes: %d" % len(boxes))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_half.json")
