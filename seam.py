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

1. S CORRIDOR across the open ground band, replacing the earlier pair
   of angled walls.  Six axis-aligned segments, 26.7 thick, z 0.1..1280.3
   to match axis_43/45.  It links the same four things:

     east side  axis_45 (3747.4) -> m_axis_553_far (3080.6)
     west side  axis_43 (2787.2) -> m_gapfill_378_366 (1907.1)

   The cross leg sits on y 5685.00..6485.10, which is the windowed
   bridge's cross leg exactly, so both middle runs share the centreline
   y 6085.05.  Note m_gapfill_378_366 only occupies z 893.65..1280.35;
   seam_w_c is carried full height anyway, because the band below it is
   open ground and a wall starting at 893 would float.

2. RESTORED WALL between axis_43 and the bridge's east wall.  This is
   the stretch of the old axis_61/60/59 line east of the bridge, put
   back as ONE box on the axis_61 footprint, x 1493.65..2773.85.  It
   butts the outer face of bridge_wall_e and the west face of axis_43.

3. PILLARS under the bridge, 266.7 square, the same width as the floor
   hole, one in each of the four corners of the S, flush into the
   corner.  They stand on stitch_ground at -0.05 and carry up to the
   underside of the bridge floor at 640.15, a 640.2 rise.
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
    # 1. the S corridor across the ground band.  Same handedness as the
    #    windowed bridge: north, west, north.  Its cross leg occupies
    #    y 5685.00..6485.10, EXACTLY the bridge's cross leg, so the two
    #    middle runs are aligned and share a centreline at y 6085.05.
    #
    #    Interior rectangles:
    #      south channel  x 2787.2..3747.4  y 5494.50..6485.10
    #      cross leg      x 1907.1..3747.4  y 5685.00..6485.10
    #      north channel  x 1907.1..3080.6  y 5685.00..7262.45
    #
    #    Wall centrelines are the neighbours' own centrelines, so the
    #    east wall lands on the axis_45 footprint to the unit and the
    #    west wall on axis_43.
    b.append(box("seam_e_a", (3734.05, 3760.75), (5441.10, 6498.45), FULL_Z))
    b.append(box("seam_e_n", (3067.25, 3760.75), (6485.10, 6511.80), FULL_Z))
    b.append(box("seam_e_c", (3067.25, 3093.95), (6485.10, 6915.75), FULL_Z))
    b.append(box("seam_w_a", (2773.85, 2800.55), (5494.50, 5685.00), FULL_Z))
    b.append(box("seam_w_s", (1893.75, 2800.55), (5658.30, 5685.00), FULL_Z))
    b.append(box("seam_w_c", (1893.75, 1920.45), (5658.30, 7262.45), FULL_Z))
    # 2. restored wall, on the old axis_61 footprint
    b.append(box("seam_wall_restore", (1493.65, 2773.85), (5067.60, 5254.40), FULL_Z))
    # 3. bridge pillars, 266.7 square, the hole width, one flush into
    #    each corner of the S.  They stand ON stitch_ground (top -0.05)
    #    and carry up to the underside of the bridge floor at 640.15.
    P = 266.7
    PZ = (-0.05, 640.15)
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
