#!/usr/bin/env python3
"""
Manual tail step: twenty-first batch from the 2026-08-17 crosshair session.
Runs after apply_batch_20260817t.py. Name-keyed and idempotent.

op 1: copy of the d195 standard door into axis_265, sill on floor2_195_bay.
op 2: same door into axis_333, centred on the axis_328..344 steps, sill on
      axis_331.
op 3: tunnel joining the two, hugging axis_337 then axis_333, with a flat
      landing at the exterior corner and a second at the axis_333 door.
      10 degree grade throughout, split across the two legs.

All three walls share the x normal and the 26.7 thickness of axis_195, so
the arch pieces translate across with no rotation.

Usage:  python3 apply_batch_20260817u.py docs/plans/dust2_half.json
"""
import json, math, sys, copy

MAT = "materials/dev/reflectivity_30.vmat"

DOOR_W, DOOR_H = 253.0, 586.8
SRC = "_d195"
SRC_WALL_X, SRC_OPEN_Y, SRC_TOP = 2280.5, 839.0, 586.95

BORE = DOOR_W
WALL_T = 26.7
GRADE = 10.0
CEIL_TOP = 1200.4              # axis_265 door head, carried the whole way
ROOF = (CEIL_TOP - 26.6, CEIL_TOP)
WALL_BASE = 240.0

# doors: wall, wall y span, wall x span, arch centre y, sill, suffix
DOORS = [
    ("axis_265", (960.2, 2067.2), (2747.2, 2773.9), 1207.1, 613.6, "_d265"),
    ("axis_333", (1333.5, 2773.8), (3974.2, 4000.8), 2500.5, 293.3, "_d333"),
]

A_SILL, B_SILL = 613.6, 293.3
X0, X1 = 2773.9, 4000.8        # leg 1, from the axis_265 face to axis_333
Y0 = 1080.6                    # tunnel south edge, arch A opening
Y1 = Y0 + BORE                 # 1333.6, flush under axis_337
XL0, XL1 = X1, X1 + BORE       # leg 2 band, east of axis_333
YB0, YB1 = 2374.0, 2627.0      # arch B opening
RUN2 = YB0 - Y1                # leg 2 ramp run
DROP2 = RUN2 * math.tan(math.radians(GRADE))
MID = B_SILL + DROP2           # landing height at the corner
RUN1 = (A_SILL - MID) / math.tan(math.radians(GRADE))
XR = X1 - RUN1                 # where the leg 1 ramp starts

def box(name, x, y, z):
    return {"name": name,
            "origin": [round((x[0] + x[1]) / 2.0, 1), round((y[0] + y[1]) / 2.0, 1), round((z[0] + z[1]) / 2.0, 1)],
            "extents": [round(x[1] - x[0], 1), round(y[1] - y[0], 1), round(z[1] - z[0], 1)],
            "angles": [0.0, 0.0, 0.0], "material": MAT}

def ramp(name, x, y, top0, top1, yaw, thick=53.3):
    """Top surface descends from top0 to top1 along +x (yaw 0) or +y (yaw 90)."""
    run = (x[1] - x[0]) if yaw == 0 else (y[1] - y[0])
    pitch = math.degrees(math.atan2(top0 - top1, run))
    cz = (top0 + top1) / 2.0 - (thick / 2.0) / math.cos(math.radians(pitch))
    length = math.hypot(run, top0 - top1)
    width = (y[1] - y[0]) if yaw == 0 else (x[1] - x[0])
    return {"name": name,
            "origin": [round((x[0] + x[1]) / 2.0, 1), round((y[0] + y[1]) / 2.0, 1), round(cz, 1)],
            "extents": [round(length, 1), round(width, 1), thick],
            "angles": [round(pitch, 3), float(yaw), 0.0], "material": MAT}

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

    src = [b for b in boxes if b["name"].endswith(SRC) and not b["name"].startswith("axis_")]
    if not src:
        log.append("FAIL no %s arch pieces" % SRC)

    for wall, wy, wx, cy, sill, suffix in DOORS:
        o_lo, o_hi = cy - DOOR_W / 2.0, cy + DOOR_W / 2.0
        hdr = sill + DOOR_H
        if wall not in idx:
            log.append("FAIL %s absent" % wall)
            continue
        w = boxes[idx[wall]]
        lo = w["origin"][1] - w["extents"][1] / 2.0
        hi = w["origin"][1] + w["extents"][1] / 2.0
        if abs(hi - o_lo) < 0.1:
            log.append("skip trim %s (already %.1f)" % (wall, o_lo))
        elif abs(hi - wy[1]) > 0.1:
            log.append("FAIL trim %s: expected y max %.1f, found %.1f" % (wall, wy[1], hi))
        else:
            w["origin"][1] = round((lo + o_lo) / 2.0, 1)
            w["extents"][1] = round(o_lo - lo, 1)
            log.append("trim %s y max %.1f -> %.1f" % (wall, hi, o_lo))

        add(box(wall + "_far", wx, (o_hi, wy[1]), (0.1, 1280.3)))
        add(box(wall + "_low", wx, (o_lo, o_hi), (0.1, sill)))
        add(box(wall + "_hdr", wx, (o_lo, o_hi), (hdr, 1280.3)))

        dx = (wx[0] + wx[1]) / 2.0 - SRC_WALL_X
        dy = cy - SRC_OPEN_Y
        dz = hdr - SRC_TOP
        for b in src:
            nb = copy.deepcopy(b)
            nb["name"] = b["name"][: -len(SRC)] + suffix
            nb["origin"] = [round(b["origin"][0] + dx, 1),
                            round(b["origin"][1] + dy, 1),
                            round(b["origin"][2] + dz, 1)]
            add(nb)
        log.append("arch cloned to %s" % suffix)

    # ---- tunnel -----------------------------------------------------------
    # leg 1: flat off the axis_265 door, then ramp down to the corner
    add(box("bay_tun_pad", (X0, XR), (Y0, Y1), (A_SILL - 26.8, A_SILL)))
    add(ramp("bay_tun_ramp1", (XR, X1), (Y0, Y1), A_SILL, MID, 0))
    # flat landing at the exterior corner
    add(box("bay_tun_landing1", (XL0, XL1), (Y0, Y1), (MID - 26.8, MID)))
    # leg 2: ramp north along axis_333
    add(ramp("bay_tun_ramp2", (XL0, XL1), (Y1, YB0), MID, B_SILL, 90))
    # flat landing at the axis_333 door
    add(box("bay_tun_landing2", (XL0, XL1), (YB0, YB1), (B_SILL - 26.8, B_SILL)))

    # shell: axis_337 and axis_333 are the inner walls, so only the outer
    # faces are new
    add(box("bay_tun_wall_s", (X0, XL1 + WALL_T), (Y0 - WALL_T, Y0), (WALL_BASE, CEIL_TOP)))
    add(box("bay_tun_wall_e", (XL1, XL1 + WALL_T), (Y0 - WALL_T, YB1 + WALL_T), (WALL_BASE, CEIL_TOP)))
    add(box("bay_tun_wall_n", (XL0, XL1 + WALL_T), (YB1, YB1 + WALL_T), (WALL_BASE, CEIL_TOP)))
    add(box("bay_tun_roof1", (X0, XL1 + WALL_T), (Y0 - WALL_T, Y1 + WALL_T), ROOF))
    add(box("bay_tun_roof2", (XL0, XL1 + WALL_T), (Y1, YB1 + WALL_T), ROOF))

    json.dump(plan, open(path, "w"), indent=1)
    for line in log:
        print(line)
    print("boxes: %d" % len(boxes))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_half.json")
