#!/usr/bin/env python3
"""
Manual tail step: fifth batch from the 2026-08-17 crosshair session.
Runs after apply_batch_20260817d.py. Name-keyed and idempotent.

op 1: L-shaped door-width slab at the merged_84 level joining axis_363,
      axis_80 and axis_370.
op 2: arch door through axis_80, sill on the new slab, opening onto
      merged_84. Arch cloned from d733 (same wall normal and thickness).

Usage:  python3 apply_batch_20260817e.py docs/plans/dust2_half.json
"""
import json, sys, copy

MAT = "materials/dev/reflectivity_30.vmat"

DOOR_W = 253.0
DOOR_H = 586.8

SLAB_Z = (640.1, 666.9)        # merged_84 span, crosshair 4
SLAB_TOP = SLAB_Z[1]

# slab arms
NS_X = (387.1, 640.1)          # 253 wide, east edge on the axis_80 west face
NS_Y = (3614.4, 3947.5)
EW_Y = (3694.5, 3947.5)        # 253 wide, north edge on the axis_370 north end
EW_X = (160.0, 387.1)          # axis_370 east face to the NS arm

# op 2: door through axis_80
WALL = "axis_80"
WALL_X = 653.5
WALL_Z = (0.1, 1280.3)
OPEN_Y = (3614.4, 3867.4)      # 253 wide, north edge on the axis_80 north end
HDR_BOT = SLAB_TOP + DOOR_H    # 1253.7
SRC, DST = "d733", "d80"
SRC_WALL_X, SRC_OPEN_Y, SRC_HDR_BOT = -520.1, 3020.0, 1240.2

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

    # ---- op 1 -------------------------------------------------------------
    add(box("axis_363_slab_ns", NS_X, NS_Y, SLAB_Z))
    add(box("axis_363_slab_ew", EW_X, EW_Y, SLAB_Z))

    # ---- op 2 -------------------------------------------------------------
    if WALL not in idx:
        log.append("FAIL %s absent" % WALL)
    else:
        w = boxes[idx[WALL]]
        lo = w["origin"][1] - w["extents"][1] / 2.0
        hi = w["origin"][1] + w["extents"][1] / 2.0
        if abs(hi - OPEN_Y[0]) < 0.1:
            log.append("skip trim %s (already %.1f)" % (WALL, OPEN_Y[0]))
        elif abs(hi - 3867.4) > 0.1:
            log.append("FAIL trim %s: expected y max 3867.4, found %.1f" % (WALL, hi))
        else:
            w["origin"][1] = round((lo + OPEN_Y[0]) / 2.0, 1)
            w["extents"][1] = round(OPEN_Y[0] - lo, 1)
            log.append("trim %s y max 3867.4 -> %.1f" % (WALL, OPEN_Y[0]))

        wx = (WALL_X - 13.35, WALL_X + 13.35)
        add(box(WALL + "_low", wx, OPEN_Y, (WALL_Z[0], SLAB_TOP)))
        add(box(WALL + "_hdr", wx, OPEN_Y, (HDR_BOT, WALL_Z[1])))

        dx = WALL_X - SRC_WALL_X
        dy = (OPEN_Y[0] + OPEN_Y[1]) / 2.0 - SRC_OPEN_Y
        dz = HDR_BOT - SRC_HDR_BOT
        n = 0
        for b in list(boxes):
            if not b["name"].endswith("_" + SRC) or b["name"].startswith("axis_"):
                continue
            nb = copy.deepcopy(b)
            nb["name"] = b["name"][: -len(SRC)] + DST
            nb["origin"] = [round(b["origin"][0] + dx, 1),
                            round(b["origin"][1] + dy, 1),
                            round(b["origin"][2] + dz, 1)]
            add(nb)
            n += 1
        log.append("arch pieces cloned from %s: %d" % (SRC, n))

    json.dump(plan, open(path, "w"), indent=1)
    for line in log:
        print(line)
    print("boxes: %d" % len(boxes))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_half.json")
