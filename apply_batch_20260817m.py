#!/usr/bin/env python3
"""
Manual tail step: thirteenth batch from the 2026-08-17 crosshair session.
Runs after apply_batch_20260817l.py. Name-keyed and idempotent.

Cap the remaining unroofed void east and north of axis_547 (the backwards J).
Traced by rasterising solidity at z = 1266 and following the wall faces, so
each slab lands on real geometry rather than a guessed rectangle.

Usage:  python3 apply_batch_20260817m.py docs/plans/dust2_half.json
"""
import json, sys

MAT = "materials/dev/reflectivity_30.vmat"
CEIL = (1253.7, 1280.3)

def box(name, x, y, z):
    return {"name": name,
            "origin": [round((x[0] + x[1]) / 2.0, 1), round((y[0] + y[1]) / 2.0, 1), round((z[0] + z[1]) / 2.0, 1)],
            "extents": [round(x[1] - x[0], 1), round(y[1] - y[0], 1), round(z[1] - z[0], 1)],
            "angles": [0.0, 0.0, 0.0], "material": MAT}

NEW = [
    # stroke, narrow section: axis_547 west, axis_462 / axis_462_far east
    box("ceiling_547_129_a", (-213.3,  -26.6), ( 880.1, 1546.9), CEIL),
    # stroke, widening at axis_461: axis_460 east
    box("ceiling_547_129_b", (-213.3,  106.7), (1546.9, 1707.0), CEIL),
    # stroke, full width: axis_129 east
    box("ceiling_547_129_c", (-213.3,  186.7), (1707.0, 2560.6), CEIL),
    # west lobe, north of axis_769_wall_s, west of axis_547
    box("ceiling_547_129_d", (-533.6, -213.3), (2267.2, 2560.6), CEIL),
    # the hook: axis_547 ends at 2560.6 so the space opens west to the
    # ceiling_553_block edge, closed north by axis_711 over axis_716
    box("ceiling_547_129_e", (-533.6,  186.7), (2560.6, 3147.2), CEIL),
]

def main(path):
    plan = json.load(open(path))
    boxes = plan["boxes"]
    idx = {b["name"]: i for i, b in enumerate(boxes)}
    log = []
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
