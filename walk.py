#!/usr/bin/env python3
"""Sloped walkway joining axis_42 to m_axis_790 and m_merged_721,
following the S corridor.  Runs last:

    mirror.py -> stitch.py -> bridge.py -> seam.py -> walk.py

WIDTH RATIO
-----------
axis_42 is 933.5 wide in a 960.2 channel, a ratio of 0.97219.  That
ratio is held on all three legs:

    south channel  interior 960.2   -> deck  933.50   x 2800.55..3734.05
    cross leg      interior 800.1   -> deck  777.85   y 5696.13..6473.98
    north channel  interior 1146.8  -> deck 1114.90   x 1936.40..3051.30

GRADE
-----
An axis-aligned plate cannot slope round a 90 degree turn without a
crease, so each corner has to be FLAT, and here the two corner pads
overlap in x: the corners are 773.45 apart but the legs are 933.5 and
1114.9 wide.  So the whole cross leg is one flat pad, and only the two
straight runs can slope.  That leaves 254.98 + 441.72 = 696.70 of run
for the 121.10 drop from axis_42 to m_axis_790, which is 9.8639 deg.

Every sloped piece uses that one grade.  Nothing here exceeds 10 deg,
there is not a single step, and the three existing decks keep their
current heights.

PIECES (each emitted with its 180 degree twin)
    walk_ramp_s   401.15 -> 356.84   over 254.98, descending north
    walk_pad_c    flat at 356.84, the whole cross band
    walk_ramp_n   356.84 -> 280.05   over 441.72, lands flush on m_axis_790
    walk_spur_w   280.05 -> 213.35   over 383.73, lands flush on m_merged_721

The spur is the west strip only, x 1936.40..2413.85, so the east strip
stays on m_axis_790 at 280.05 and m_axis_786 keeps its 40.0 rise above
that deck untouched.
"""

import json
import math
import sys

MAT = "materials/dev/reflectivity_30.vmat"
XP, YP = 460.1, 6085.05
T = 26.7                                  # deck and ramp thickness
GRADE = math.degrees(math.atan2(121.10, 696.70))

SX = (2800.55, 3734.05)                   # south leg deck, 933.50
NX = (1936.40, 3051.30)                   # north leg deck, 1114.90
CY = (5696.13, 6473.98)                   # cross leg deck, 777.85
WX = (1936.40, 2413.85)                   # spur, west strip only

TOP_42 = 401.15
TOP_PAD = 356.84
TOP_790 = 280.05
TOP_721 = 213.35


def flat(name, x, y, top):
    return {
        "name": name,
        "origin": [round((x[0]+x[1])/2, 4), round((y[0]+y[1])/2, 4),
                   round(top - T/2, 4)],
        "extents": [round(x[1]-x[0], 4), round(y[1]-y[0], 4), T],
        "angles": [0.0, 0.0, 0.0],
        "material": MAT,
    }


def ramp_n(name, x, y0, y1, ztop0, ztop1):
    """A slab descending toward +y.  yaw 90 puts local +x on world +y,
    and positive pitch descends along local +x, so the pitch is positive
    for a fall northward.  The box centre is the midpoint of the TOP
    surface pushed back half a thickness along the slab's own +z, which
    is (0, sin, cos) at this yaw."""
    th = math.radians(GRADE)
    run = y1 - y0
    length = run / math.cos(th)
    ty = (y0 + y1) / 2.0
    tz = (ztop0 + ztop1) / 2.0
    return {
        "name": name,
        "origin": [round((x[0]+x[1])/2, 4),
                   round(ty - (T/2)*math.sin(th), 4),
                   round(tz - (T/2)*math.cos(th), 4)],
        "extents": [round(length, 4), round(x[1]-x[0], 4), T],
        "angles": [0.0, 90.0, round(GRADE, 4)],
        "material": MAT,
    }


def seeds():
    return [
        ramp_n("walk_ramp_s", SX, 5441.15, CY[0], TOP_42, TOP_PAD),
        flat("walk_pad_c", (NX[0], SX[1]), CY, TOP_PAD),
        ramp_n("walk_ramp_n", NX, CY[1], 6915.70, TOP_PAD, TOP_790),
        ramp_n("walk_spur_w", WX, 6915.70, 7299.43, TOP_790, TOP_721),
    ]


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
    print("grade %.4f deg; added %d, plan now %d boxes"
          % (GRADE, added, len(plan["boxes"])))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_full.json")
