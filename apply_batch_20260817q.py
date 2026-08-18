#!/usr/bin/env python3
"""
Manual tail step: seventeenth batch from the 2026-08-17 crosshair session.
Runs after apply_batch_20260817p.py. Name-keyed and idempotent.

Big arch through axis_468, the back wall of T spawn, centred on x = 0 in
the span between the axis_547 line and the ramp-slab_466 / _471 ramps.

The arch is the existing large T spawn arch (the axis_480 / axis_481
assembly in the x = -226.65 wall) rotated -90 degrees about z into the
y = -813.5 wall. That maps source yaw +90 to 0 and -90 to 180, which is
exactly the d479 convention, and the two walls are the same thickness and
share the same sill (426.8) and top (1067.0), so no scaling or z shift.

Usage:  python3 apply_batch_20260817q.py docs/plans/dust2_half.json
"""
import json, sys, copy

MAT = "materials/dev/reflectivity_30.vmat"

SRC_WALL_X = -226.65      # source wall centre
SRC_ARCH_Y = -520.15      # source arch centre
DST_WALL_Y = -813.5       # axis_468 centre
DST_ARCH_X = 0.0

WALL = "axis_468"
WALL_X = (-2000.4, 1920.4)
WALL_Z = (213.4, 1067.0)
SILL = 426.8              # axis_470 top
SPRING = 911.8            # jamb top, where the arch curve starts

JAMB_OUT = 200.05         # clear span at the springing
JAMB_IN = 165.2           # clear span at the floor

SRC_PIECES = [
    "ramp-slab_861", "ramp-slab_862", "ramp-slab_863", "ramp-slab_864",
    "ramp-slab_865", "ramp-slab_866", "ramp-slab_871", "ramp-slab_872",
    "ramp-slab_873", "ramp-slab_874", "ramp-slab_875", "ramp-slab_876",
    "shallow_867", "shallow_868", "shallow_869", "shallow_870",
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

    def add(nb):
        if nb["name"] in idx:
            log.append("skip add %s (present)" % nb["name"])
            return
        boxes.append(copy.deepcopy(nb))
        idx[nb["name"]] = len(boxes) - 1
        log.append("add %s" % nb["name"])

    # ---- trim the back wall to the west jamb -------------------------------
    if WALL not in idx:
        log.append("FAIL %s absent" % WALL)
    else:
        w = boxes[idx[WALL]]
        lo = w["origin"][0] - w["extents"][0] / 2.0
        hi = w["origin"][0] + w["extents"][0] / 2.0
        if abs(hi - (-JAMB_OUT)) < 0.1:
            log.append("skip trim %s (already %.1f)" % (WALL, -JAMB_OUT))
        elif abs(hi - WALL_X[1]) > 0.1:
            log.append("FAIL trim %s: expected x max %.1f, found %.1f" % (WALL, WALL_X[1], hi))
        else:
            w["origin"][0] = round((lo - JAMB_OUT) / 2.0, 1)
            w["extents"][0] = round(-JAMB_OUT - lo, 1)
            log.append("trim %s x max %.1f -> %.1f" % (WALL, hi, -JAMB_OUT))

    wy = (DST_WALL_Y - 13.4, DST_WALL_Y + 13.4)
    add(box(WALL + "_far",    ( JAMB_OUT, WALL_X[1]), wy, WALL_Z))
    add(box(WALL + "_low",    (-JAMB_OUT,  JAMB_OUT), wy, (WALL_Z[0], SILL)))
    add(box(WALL + "_jamb_w", (-JAMB_OUT, -JAMB_IN),  wy, (WALL_Z[0], SPRING)))
    add(box(WALL + "_jamb_e", ( JAMB_IN,   JAMB_OUT), wy, (WALL_Z[0], SPRING)))

    # ---- clone the arch, rotated -90 about z -------------------------------
    n = 0
    for name in SRC_PIECES:
        if name not in idx:
            log.append("FAIL source %s absent" % name)
            continue
        s = boxes[idx[name]]
        u = s["origin"][0] - SRC_WALL_X          # through-wall offset
        v = s["origin"][1] - SRC_ARCH_Y          # along-wall offset
        nb = copy.deepcopy(s)
        nb["name"] = name + "_d468"
        nb["origin"] = [round(DST_ARCH_X + v, 1),
                        round(DST_WALL_Y - u, 1),
                        s["origin"][2]]
        nb["angles"] = [s["angles"][0], round(s["angles"][1] - 90.0, 2), s["angles"][2]]
        add(nb)
        n += 1
    log.append("arch pieces rotated into %s: %d" % (WALL, n))

    json.dump(plan, open(path, "w"), indent=1)
    for line in log:
        print(line)
    print("boxes: %d" % len(boxes))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_half.json")
