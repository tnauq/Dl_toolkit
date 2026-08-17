#!/usr/bin/env python3
"""
Manual tail step: sixth batch from the 2026-08-17 crosshair session.
Runs after apply_batch_20260817e.py. Name-keyed and idempotent.

Sky bridge from the axis_473 upper floor across the open y 3147..3467 gap
to the axis_80_fill deck, door width throughout, with an arch door at each
end (through axis_79 and through axis_80_cross).

The two decks differ by 94.5 u, so the bridge is a single ramp. Its run is
extended over the top of axis_80_fill so the grade comes out at 9.15 deg,
landing flush with merged_84 at y 3734.1.

Usage:  python3 apply_batch_20260817f.py docs/plans/dust2_half.json
"""
import json, math, sys, copy

MAT = "materials/dev/reflectivity_30.vmat"

DOOR_W = 253.0
BRIDGE_X = (1093.5, 1346.5)      # centred on x 1220, between both crosshairs
HIGH_TOP = 761.4                 # axis_473 top
LOW_TOP = 666.9                  # axis_80_fill top
RAMP_Y = (3147.3, 3734.1)        # axis_79 north face to the merged_84 edge
WALL_TOP = 1280.3

# arch template: d479 sits in a wall with the same normal (y)
SRC, SRC_WALL_Y, SRC_OPEN_X, SRC_HDR_BOT = "d479", -226.65, 3.0, 800.2

DOORS = [
    # dst, wall name, far name, wall y span, wall thickness centre, sill z
    ("d79",  "axis_79",       (906.9, 1947.1), (3120.7, 3147.3), 0.1,   HIGH_TOP),
    ("d80c", "axis_80_cross", (666.9, 1467.0), (3440.7, 3467.4), 213.3, LOW_TOP),
]

def box(name, x, y, z):
    return {"name": name,
            "origin": [round((x[0] + x[1]) / 2.0, 1), round((y[0] + y[1]) / 2.0, 1), round((z[0] + z[1]) / 2.0, 1)],
            "extents": [round(x[1] - x[0], 1), round(y[1] - y[0], 1), round(z[1] - z[0], 1)],
            "angles": [0.0, 0.0, 0.0], "material": MAT}

def ramp_north_down(name, x, y0, y1, ztop0, ztop1, thick=53.3):
    run, drop = y1 - y0, ztop0 - ztop1
    pitch = math.degrees(math.atan2(drop, run))
    length = math.hypot(run, drop)
    cz = (ztop0 + ztop1) / 2.0 - (thick / 2.0) / math.cos(math.radians(pitch))
    return {"name": name,
            "origin": [round((x[0] + x[1]) / 2.0, 1), round((y0 + y1) / 2.0, 1), round(cz, 1)],
            "extents": [round(length, 1), round(x[1] - x[0], 1), thick],
            "angles": [round(pitch, 3), 90.0, 0.0], "material": MAT}

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

    # level threshold pad inside the axis_79 doorway, flush with axis_473
    add(box("axis_473_bridge_pad", BRIDGE_X, (3120.6, 3147.3), (734.6, HIGH_TOP)))
    # the bridge itself
    add(ramp_north_down("axis_473_bridge", BRIDGE_X, RAMP_Y[0], RAMP_Y[1], HIGH_TOP, LOW_TOP))

    for dst, wall, wall_x, wall_y, wall_z0, sill in DOORS:
        if wall not in idx:
            log.append("FAIL %s absent" % wall)
            continue
        w = boxes[idx[wall]]
        lo = w["origin"][0] - w["extents"][0] / 2.0
        hi = w["origin"][0] + w["extents"][0] / 2.0
        if abs(hi - BRIDGE_X[0]) < 0.1:
            log.append("skip trim %s (already %.1f)" % (wall, BRIDGE_X[0]))
        elif abs(hi - wall_x[1]) > 0.1:
            log.append("FAIL trim %s: expected x max %.1f, found %.1f" % (wall, wall_x[1], hi))
            continue
        else:
            w["origin"][0] = round((lo + BRIDGE_X[0]) / 2.0, 1)
            w["extents"][0] = round(BRIDGE_X[0] - lo, 1)
            log.append("trim %s x max %.1f -> %.1f" % (wall, wall_x[1], BRIDGE_X[0]))

        wy = wall_y
        add(box(wall + "_far", (BRIDGE_X[1], wall_x[1]), wy, (wall_z0, WALL_TOP)))
        add(box(wall + "_low", BRIDGE_X, wy, (wall_z0, sill)))
        # no header: the opening runs to the wall top, see notes

        dx = (BRIDGE_X[0] + BRIDGE_X[1]) / 2.0 - SRC_OPEN_X
        dy = (wy[0] + wy[1]) / 2.0 - SRC_WALL_Y
        dz = WALL_TOP - SRC_HDR_BOT
        n = 0
        for b in list(boxes):
            if not b["name"].endswith("_" + SRC) or b["name"].startswith("axis_"):
                continue
            nb = copy.deepcopy(b)
            nb["name"] = b["name"][: -len(SRC)] + dst
            nb["origin"] = [round(b["origin"][0] + dx, 1),
                            round(b["origin"][1] + dy, 1),
                            round(b["origin"][2] + dz, 1)]
            add(nb)
            n += 1
        log.append("arch pieces cloned from %s to %s: %d" % (SRC, dst, n))

    json.dump(plan, open(path, "w"), indent=1)
    for line in log:
        print(line)
    print("boxes: %d" % len(boxes))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_half.json")
