#!/usr/bin/env python3
"""Put a big arch through seam_w_c, centred on t3_pad2, and the same on
the mirrored side.

    mirror.py -> stitch.py -> bridge.py -> seam.py -> walk.py -> arch.py

THE ARCH.  Cloned from the _d468b assembly, which is the big arch
family: 400.1 at the springing, 330.5 clear between the jambs, 586.8
tall, springing 485.0 above the sill.  Measured off the source, the
sill top is 426.8 (jamb tops land on 911.8, which is 426.8 + 485.0).

The source sits in a Y-NORMAL wall and seam_w_c is X-NORMAL, so per the
established rule the clone rotates by normal - 90: every part's offset
along the wall becomes an offset in y, and every part's yaw gains 90.
Pitch and roll are untouched, which is what keeps the 12 ramp-slabs of
the arch ring at their original angles.

PLACEMENT.  Wall centreline x 1907.1, centred on t3_pad2 at y 5855.87,
sill on that pad's floor at 344.55.

CUTTING THE WALL.  An arch is only an arch if there is a hole, so
seam_w_c is replaced by:
    seam_w_c_n       the wall north of the opening
    seam_w_c_under   below the sill, z 0.1..131.15
    seam_w_c_span    the spandrel above the arch, z 1037.99..1280.3
The opening band is the nominal 400.1, y 5655.82..6055.92.  There is no
piece south of it: the opening reaches 2.48 past the wall's own south
end, so the assembly closes that side itself.
"""

import json
import math
import sys

XP, YP = 460.1, 6085.05
WALL_X = 1907.1
CEN_Y = 5855.87
SILL = 344.55
HALF = 200.05
Y0, Y1 = CEN_Y - HALF, CEN_Y + HALF
WALL_N = 7262.45
WALL_Z = (0.1, 1280.3)
LOW_DROP = 213.4                      # sill top down to the low block's base
RING_TOP = 693.44                     # highest point of the ring, above sill
THICK = 26.7

SRC_CX, SRC_S, SRC_Y = -1600.25, 426.8, -813.5
MAT = "materials/dev/reflectivity_30.vmat"


def flat(name, x, y, z):
    return {"name": name,
            "origin": [round((x[0]+x[1])/2, 4), round((y[0]+y[1])/2, 4),
                       round((z[0]+z[1])/2, 4)],
            "extents": [round(x[1]-x[0], 4), round(y[1]-y[0], 4),
                        round(z[1]-z[0], 4)],
            "angles": [0.0, 0.0, 0.0], "material": MAT}


def load_assembly(half_path):
    with open(half_path) as f:
        plan = json.load(f)
    out = []
    for b in plan["boxes"]:
        n = b["name"]
        if not (n.endswith("_d468b") or n.startswith("axis_468_d468b")):
            continue
        if n.endswith("_far"):          # flanking wall, not the arch
            continue
        out.append(b)
    return out


def place(b):
    """Rotate the source part 90 degrees about z and drop it on the sill."""
    o = b["origin"]
    d = o[0] - SRC_CX                  # offset along the source wall
    h = o[2] - SRC_S                   # height above the source sill
    a = b["angles"]
    yaw = a[1] + 90.0
    while yaw > 180.0:
        yaw -= 360.0
    tag = b["name"].replace("_d468b", "").replace("axis_468", "j")
    return {"name": "arch_w_" + tag,
            "origin": [WALL_X, round(CEN_Y + d, 4), round(SILL + h, 4)],
            "extents": list(b["extents"]),
            "angles": [a[0], round(yaw, 4), a[2]],
            "material": b.get("material", MAT)}


def rotate(bx):
    o = bx["origin"]
    r = json.loads(json.dumps(bx))
    r["name"] = "m_" + bx["name"]
    r["origin"] = [round(2*XP - o[0], 4), round(2*YP - o[1], 4), o[2]]
    yaw = bx["angles"][1] + 180.0
    while yaw > 180.0:
        yaw -= 360.0
    r["angles"] = [bx["angles"][0], round(yaw, 4), bx["angles"][2]]
    return r


def main(path, half="docs/plans/dust2_half.json"):
    with open(path) as f:
        plan = json.load(f)

    boxes = plan["boxes"]
    before = len(boxes)
    kill = {"seam_w_c", "m_seam_w_c"} & {b["name"] for b in boxes}
    for n in sorted(kill):
        print("DEL  %s" % n)
    boxes = [b for b in boxes if b["name"] not in kill]

    seeds = [
        flat("seam_w_c_n", (WALL_X-THICK/2, WALL_X+THICK/2), (Y1, WALL_N), WALL_Z),
        flat("seam_w_c_under", (WALL_X-THICK/2, WALL_X+THICK/2), (Y0, Y1),
             (WALL_Z[0], SILL-LOW_DROP)),
        flat("seam_w_c_span", (WALL_X-THICK/2, WALL_X+THICK/2), (Y0, Y1),
             (SILL+RING_TOP, WALL_Z[1])),
    ]
    seeds += [place(b) for b in load_assembly(half)]

    have = {b["name"] for b in boxes}
    added = 0
    for s in seeds:
        for bx in (s, rotate(s)):
            if bx["name"] in have:
                continue
            boxes.append(bx)
            have.add(bx["name"])
            added += 1

    plan["boxes"] = boxes
    with open(path, "w") as f:
        json.dump(plan, f, indent=1)
        f.write("\n")
    print("opening y %.2f..%.2f, sill %.2f, clear 330.5 by 586.8"
          % (Y0, Y1, SILL))
    print("%d -> %d boxes (added %d)" % (before, len(boxes), added))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_full.json")
