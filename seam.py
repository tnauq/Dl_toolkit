#!/usr/bin/env python3
"""Seam work east of the bridge: two angled connectors, one restored
wall, and the bridge support pillars.

Runs LAST:
    python3 mirror.py docs/plans/dust2_half.json
    python3 stitch.py docs/plans/dust2_full.json
    python3 bridge.py docs/plans/dust2_full.json
    python3 seam.py   docs/plans/dust2_full.json

Everything is authored once and emitted with its 180 degree twin about
(460.1, 6085.05), so the map stays rotationally symmetric.

1. ANGLED CONNECTORS across the open ground band.  Both run from the
   north end of a CT spawn side wall to the south end of its opposite
   number on the mirrored side, on the wall CENTRELINES, extended 13.35
   into each neighbour so no joint can open:

     seam_wall_e   axis_45 (3747.4, 5441.10) -> m_axis_553_far (3080.6, 6915.75)
     seam_wall_w   axis_43 (2787.2, 5494.50) -> m_gapfill_378_366 (1907.1, 7262.45)

   Both are 26.7 thick and run z 0.1..1280.3, matching axis_43/45.  Note
   m_gapfill_378_366 only occupies z 893.65..1280.35; seam_wall_w is
   carried full height anyway, because the band below it is open ground
   and a wall starting at 893 would float.

2. RESTORED WALL between axis_43 and the bridge's east wall.  This is
   the stretch of the old axis_61/60/59 line east of the bridge, put
   back as ONE box on the axis_61 footprint, x 1493.65..2773.85.  It
   butts the outer face of bridge_wall_e and the west face of axis_43.

3. PILLARS in the bridge, 266.7 square, the same width as the floor
   hole, one in each of the four corners of the S, flush into the
   corner.  They run floor top 666.85 to ceiling underside 1253.70.
"""

import json
import math
import sys

MAT = "materials/dev/reflectivity_30.vmat"
XP, YP = 460.1, 6085.05
THICK = 26.7
FULL_Z = (0.1, 1280.3)


def box(name, x, y, z, yaw=0.0):
    return {
        "name": name,
        "origin": [round((x[0]+x[1])/2, 4), round((y[0]+y[1])/2, 4),
                   round((z[0]+z[1])/2, 4)],
        "extents": [round(x[1]-x[0], 4), round(y[1]-y[0], 4),
                    round(z[1]-z[0], 4)],
        "angles": [0.0, yaw, 0.0],
        "material": MAT,
    }


def link(name, a, b, z, thick=THICK):
    """A wall on the segment a->b, extended half a thickness into each
    end so the joints cannot open."""
    dx, dy = b[0]-a[0], b[1]-a[1]
    length = math.hypot(dx, dy) + thick
    yaw = math.degrees(math.atan2(dy, dx))
    cx, cy = (a[0]+b[0])/2.0, (a[1]+b[1])/2.0
    return {
        "name": name,
        "origin": [round(cx, 4), round(cy, 4), round((z[0]+z[1])/2, 4)],
        "extents": [round(length, 4), thick, round(z[1]-z[0], 4)],
        "angles": [0.0, round(yaw, 4), 0.0],
        "material": MAT,
    }


def seeds():
    b = []
    # 1. angled connectors
    b.append(link("seam_wall_e", (3747.40, 5441.10), (3080.60, 6915.75), FULL_Z))
    b.append(link("seam_wall_w", (2787.20, 5494.50), (1907.10, 7262.45), FULL_Z))
    # 2. restored wall, on the old axis_61 footprint
    b.append(box("seam_wall_restore", (1493.65, 2773.85), (5067.60, 5254.40), FULL_Z))
    # 3. bridge pillars, 266.7 square, flush into two corners of the S
    P = 266.7
    PZ = (666.85, 1253.70)
    b.append(box("bridge_pillar_ne", (1466.95-P, 1466.95), (6485.10-P, 6485.10), PZ))
    b.append(box("bridge_pillar_sw", (666.95, 666.95+P), (5685.00, 5685.00+P), PZ))
    return b


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


def main(path):
    with open(path) as f:
        plan = json.load(f)
    have = {b["name"] for b in plan["boxes"]}
    added = 0
    for s in seeds():
        for bx in (s, rotate(s)):
            if bx["name"] in have:
                print("SKIP add %s (already present)" % bx["name"])
                continue
            plan["boxes"].append(bx)
            have.add(bx["name"])
            added += 1
            print("ADD  %s" % bx["name"])
    with open(path, "w") as f:
        json.dump(plan, f, indent=1)
        f.write("\n")
    print("added %d, plan now %d boxes" % (added, len(plan["boxes"])))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_full.json")
