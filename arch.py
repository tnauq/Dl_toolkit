#!/usr/bin/env python3
"""Put a door arch through seam_w_c, sized to hex2_tun_ne_dstub and
centred on bridge_pillar_sw, plus the mirrored twin.

    mirror.py -> stitch.py -> bridge.py -> seam.py -> walk.py -> arch.py

SIZE.  hex2_tun_ne_dstub_floor is 253.0 wide, which is the STANDARD DOOR
family, not the big arch: 253.0 by 586.8.  So this clones _d195, not
_d468b.  Measured off the source, that opening runs y 712.50..965.50
between axis_195 and axis_195_far, and z 0.10 up to axis_195_hdr's
underside at 586.95, which is 253.00 by 586.85.

ROTATION.  _d195 already sits in an X-NORMAL wall and seam_w_c is
x-normal, so the clone rotates by `normal`, meaning not at all.  Offsets
along the source wall are already in y and every yaw carries over
unchanged.  That is the opposite of the _d468 case, where the source is
y-normal and the clone has to turn 90.

PLACEMENT.  Wall centreline x 1907.1.  Centred on bridge_pillar_sw at
y 5818.35, sill on t3_pad2's floor at 344.55.

CUTTING THE WALL.  seam_w_c is replaced by four pieces:
    seam_w_c_s      south of the opening, y 5658.30..5691.85
    seam_w_c_n      north of it,          y 5944.85..7262.45
    seam_w_c_under  below the sill,       z 0.10..344.55
    seam_w_c_hdr    the header,           z 931.40..1280.30
"""

import json
import sys

XP, YP = 460.1, 6085.05
WALL_X = 1907.1
THICK = 26.7
CEN_Y = 5818.35                       # bridge_pillar_sw's centre
SILL = 344.55                         # t3_pad2's floor
HALF = 126.5                          # half of the 253.0 opening
Y0, Y1 = CEN_Y - HALF, CEN_Y + HALF
WALL_S, WALL_N = 5658.30, 7262.45
WALL_Z = (0.1, 1280.3)
HEAD = 586.85                         # sill to header underside

SRC_X, SRC_CY, SRC_SILL = 2280.5, 839.00, 0.10
MAT = "materials/dev/reflectivity_30.vmat"


def flat(name, y, z):
    return {"name": name,
            "origin": [WALL_X, round((y[0]+y[1])/2, 4), round((z[0]+z[1])/2, 4)],
            "extents": [THICK, round(y[1]-y[0], 4), round(z[1]-z[0], 4)],
            "angles": [0.0, 0.0, 0.0], "material": MAT}


def load_ring(half_path):
    with open(half_path) as f:
        plan = json.load(f)
    return [b for b in plan["boxes"] if b["name"].endswith("_d195")]


def place(b):
    """No rotation: source and target walls share the same normal."""
    o = b["origin"]
    return {"name": "arch_w_" + b["name"].replace("_d195", ""),
            "origin": [round(WALL_X + (o[0] - SRC_X), 4),
                       round(CEN_Y + (o[1] - SRC_CY), 4),
                       round(SILL + (o[2] - SRC_SILL), 4)],
            "extents": list(b["extents"]),
            "angles": list(b["angles"]),
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

    names = {b["name"] for b in boxes}
    kill = {n for n in names
            if n in ("seam_w_c", "m_seam_w_c")
            or n.startswith(("seam_w_c_", "m_seam_w_c_",
                             "arch_w_", "m_arch_w_"))}
    for n in sorted(kill):
        print("DEL  %s" % n)
    boxes = [b for b in boxes if b["name"] not in kill]

    seeds = [
        flat("seam_w_c_s", (WALL_S, Y0), WALL_Z),
        flat("seam_w_c_n", (Y1, WALL_N), WALL_Z),
        flat("seam_w_c_under", (Y0, Y1), (WALL_Z[0], SILL)),
        flat("seam_w_c_hdr", (Y0, Y1), (SILL + HEAD, WALL_Z[1])),
    ]
    seeds += [place(b) for b in load_ring(half)]

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
    print("opening y %.2f..%.2f (253.0), sill %.2f, head %.2f"
          % (Y0, Y1, SILL, SILL + HEAD))
    print("%d -> %d boxes (added %d)" % (before, len(boxes), added))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_full.json")
