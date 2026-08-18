#!/usr/bin/env python3
"""
Manual tail step: eighteenth batch from the 2026-08-17 crosshair session.
Runs after apply_batch_20260817q.py. Name-keyed and idempotent.

op 1: copy of the axis_468 big arch into the middle of axis_562.
op 2: third copy on axis_468, the same distance west of the first as the
      axis_562 one is east of it.

Both target walls share the axis_468 normal, thickness, bottom and top, so
the d468 arch clones across by pure translation with no angle changes.
axis_562 sits on the 213.3 floor rather than the axis_470 deck, so it gets
no sill block; the axis_468 copy does.

Usage:  python3 apply_batch_20260817r.py docs/plans/dust2_half.json
"""
import json, sys, copy

MAT = "materials/dev/reflectivity_30.vmat"

SRC_WALL_Y = -813.5
SRC_ARCH_X = 0.0
Z_BOT, Z_TOP = 213.4, 1067.0
SPRING = 911.8
JAMB_OUT, JAMB_IN = 200.05, 165.2

# arch 2: middle of axis_562
A2_X = (1280.2 + 1920.3) / 2.0        # 1600.25
A2_WALL_Y = -573.4
# arch 3: mirrors the lower arch in axis_468_far, which stays put
A3_X = -1600.25                           # mirrors the axis_468_far arch

# wall, x span, wall y centre, arch centre x, sill (None = no sill block),
# suffix, kept-segment side
JOBS = [
    ("axis_562", (1280.2, 1920.3), A2_WALL_Y, A2_X,   None,  "_d562",  "max"),
    ("axis_468", (-2000.4, -200.0), SRC_WALL_Y, A3_X,  426.8, "_d468b", "min"),
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

    src = [b for b in boxes if b["name"].endswith("_d468")]
    if not src:
        log.append("FAIL no _d468 arch pieces to clone")

    for wall, wx, wall_y, ax, sill, suffix, keep in JOBS:
        o_lo, o_hi = ax - JAMB_OUT, ax + JAMB_OUT
        i_lo, i_hi = ax - JAMB_IN, ax + JAMB_IN
        wy = (wall_y - 13.4, wall_y + 13.4)

        if wall not in idx:
            log.append("FAIL %s absent" % wall)
        else:
            w = boxes[idx[wall]]
            lo = w["origin"][0] - w["extents"][0] / 2.0
            hi = w["origin"][0] + w["extents"][0] / 2.0
            want = o_lo if keep == "max" else o_hi
            cur = hi if keep == "max" else lo
            if abs(cur - want) < 0.1:
                log.append("skip trim %s (already %.1f)" % (wall, want))
            elif abs(cur - (wx[1] if keep == "max" else wx[0])) > 0.1:
                log.append("FAIL trim %s: expected %.1f, found %.1f" % (wall, wx[1] if keep == "max" else wx[0], cur))
            else:
                if keep == "max":
                    hi = want
                else:
                    lo = want
                w["origin"][0] = round((lo + hi) / 2.0, 1)
                w["extents"][0] = round(hi - lo, 1)
                log.append("trim %s -> x[%.1f,%.1f]" % (wall, lo, hi))

        far = (o_hi, wx[1]) if keep == "max" else (wx[0], o_lo)
        add(box(wall + suffix + "_far", far, wy, (Z_BOT, Z_TOP)))
        add(box(wall + suffix + "_jamb_w", (o_lo, i_lo), wy, (Z_BOT, SPRING)))
        add(box(wall + suffix + "_jamb_e", (i_hi, o_hi), wy, (Z_BOT, SPRING)))
        if sill is not None:
            add(box(wall + suffix + "_low", (o_lo, o_hi), wy, (Z_BOT, sill)))

        dx = ax - SRC_ARCH_X
        dy = wall_y - SRC_WALL_Y
        n = 0
        for b in src:
            nb = copy.deepcopy(b)
            nb["name"] = b["name"][: -len("_d468")] + suffix
            nb["origin"] = [round(b["origin"][0] + dx, 1),
                            round(b["origin"][1] + dy, 1),
                            b["origin"][2]]
            add(nb)
            n += 1
        log.append("arch pieces cloned to %s: %d" % (suffix, n))

    json.dump(plan, open(path, "w"), indent=1)
    for line in log:
        print(line)
    print("boxes: %d" % len(boxes))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_half.json")
