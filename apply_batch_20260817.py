#!/usr/bin/env python3
"""
Manual tail step: batch of six edits from the 2026-08-17 crosshair session.
Runs after treefix.py. Name-keyed and idempotent: every op records the
pre-edit value, so a rerun detects the edit is already present and reports
"skip" instead of applying it twice.

Usage:  python3 apply_batch_20260817.py docs/plans/dust2_half.json
"""
import json, math, sys, copy

MAT = "materials/dev/reflectivity_30.vmat"

def box(name, x, y, z, angles=(0.0, 0.0, 0.0), material=MAT):
    """x, y, z are (min, max) world pairs. For unrotated boxes only."""
    return {
        "name": name,
        "origin": [round((x[0] + x[1]) / 2.0, 1), round((y[0] + y[1]) / 2.0, 1), round((z[0] + z[1]) / 2.0, 1)],
        "extents": [round(x[1] - x[0], 1), round(y[1] - y[0], 1), round(z[1] - z[0], 1)],
        "angles": [float(a) for a in angles],
        "material": material,
    }

def ramp_north_down(name, x, y0, y1, ztop0, ztop1, thick=53.3):
    """Slab whose TOP surface descends from ztop0 at y0 to ztop1 at y1.
    Convention verified against ramp_29_22_down / ramp-slab_53:
    R = Rz(yaw) Ry(pitch) Rx(roll); local +x is the run, positive pitch
    descends along local +x; yaw 90 maps local +x to world +y."""
    run = y1 - y0
    drop = ztop0 - ztop1
    pitch = math.degrees(math.atan2(drop, run))
    length = math.hypot(run, drop)
    cz = (ztop0 + ztop1) / 2.0 - (thick / 2.0) / math.cos(math.radians(pitch))
    return {
        "name": name,
        "origin": [round((x[0] + x[1]) / 2.0, 1), round((y0 + y1) / 2.0, 1), round(cz, 1)],
        "extents": [round(length, 1), round(x[1] - x[0], 1), thick],
        "angles": [round(pitch, 3), 90.0, 0.0],
        "material": MAT,
    }

# ---- op 1: remove the beam across the d476 opening -------------------------
REMOVE = ["axis_476"]

# ---- op 6: grow the west floor plate east to axis_129 ----------------------
# pre-edit value recorded for idempotence
GROW = [
    # name, axis, field, pre-edit value, post-edit value
    ("axis_551", 0, "max", -53.3, 186.7),
]

# ---- ops 2..6: new boxes ---------------------------------------------------
NEW = [
    # 2. ceiling over the upper room bounded by axis_123 / axis_192_face / axis_79
    box("ceiling_473_block", (880.1, 1947.1), (1440.2, 3147.3), (1253.6, 1280.3)),

    # 3. second level in the east room, one door width, hugging the west wall,
    #    top flush with axis_473, plus the bridge through the d476 opening
    box("level_473_east", (1947.0, 2200.3), (2773.9, 3920.8), (734.6, 761.4)),
    box("level_473_bridge", (1920.3, 1947.0), (2773.9, 3120.7), (734.6, 761.4)),

    # 4. raise the d479 arch door threshold to the axis_470 floor height
    box("axis_479_sill1", (-123.5, 129.5), (-240.0, -213.3), (213.4, 426.8)),

    # 5. 10 degree ramp north from the d479 threshold down to the 213.3 floor
    ramp_north_down("ramp_479_down_a", (-213.3, 186.7), -213.3, 880.1, 426.8, 234.0),
    ramp_north_down("ramp_479_down_b", (-213.3, -26.6), 880.1, 997.5, 234.0, 213.3),

    # 6. north extension of the west floor plate, held clear of the
    #    compound_753..756 / yaw_750..752 slope west of x = -320
    box("axis_551_ext", (-320.0, 186.7), (2560.6, 3147.2), (186.7, 213.3)),
]

def main(path):
    plan = json.load(open(path))
    boxes = plan["boxes"]
    idx = {b["name"]: i for i, b in enumerate(boxes)}
    log = []

    for name in REMOVE:
        if name in idx:
            boxes.pop(idx[name])
            idx = {b["name"]: i for i, b in enumerate(boxes)}
            log.append("remove %s" % name)
        else:
            log.append("skip remove %s (absent)" % name)

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
