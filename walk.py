#!/usr/bin/env python3
"""Two parallel tracks carried around the S corridor, extending
m_axis_790 (deck 1) and m_merged_721 (deck 3) south to axis_42, with
m_axis_786 (the railing) carried along on deck 1's profile.

    mirror.py -> stitch.py -> bridge.py -> seam.py -> walk.py

WHAT THE SOURCE LOOKS LIKE
--------------------------
The three are side by side, not stacked:
    deck 3   x 1880.40..2387.15   top 213.35
    railing  x 2387.15..2413.85   top 320.05   (106.7 tall)
    deck 1   x 2413.85..3053.95   top 280.05
Total 1173.55, and the railing top is exactly 40.00 above deck 1.

WIDTH
-----
Corridor interiors, wall face to wall face:
    south leg  933.50   cross leg  800.10   north leg  1146.80
The railing keeps its 26.70 on every leg; the rest is split between the
two tracks in the source ratio 640.10 : 506.75.

              track 1    railing    track 3
    south      506.13      26.70      400.67
    cross      431.66      26.70      341.74
    north      625.19      26.70      494.91

Track 1 is on the right hand of travel throughout: east in the south
leg, north in the cross leg, east again in the north leg.  That keeps
the railing between the two tracks the whole way round.

GRADE
-----
Each track gets two pads, one per corner, each covering the full corner
rectangle, with three sloped runs: start to pad 1, pad 1 to pad 2, pad 2
to finish.  Track 3 climbs more over a longer path, so it is the steeper
of the two, as expected:

    track 1   rise 121.10 over 1203.56 of slope   5.7455 deg
    track 3   rise 187.80 over 1704.64 of slope   6.2871 deg

Both are inside 10 degrees and there is no step anywhere on either.

A note on "square" pads: they cannot be square.  A corner pad has to
span its track's width on BOTH legs it joins, and the width ratio makes
those two widths different (506.13 by 431.66 at corner 1 for track 1,
625.19 by 431.66 at corner 2).  The pads below are the full corner
rectangles, which is the only shape that covers the turn without
leaving a crease.
"""

import json
import math
import sys

MAT = "materials/dev/reflectivity_30.vmat"
XP, YP = 460.1, 6085.05
T = 26.7
RAIL_T = 106.7
RAIL_RISE = 40.00

# ---- strip boundaries, from the wall faces outward ------------------
S_E, S_W = 3734.05, 2800.55          # south leg interior
C_N, C_S = 6485.10, 5685.00          # cross leg interior
N_E, N_W = 3067.25, 1920.45          # north leg interior

T1_S = (3227.92, 3734.05)            # track 1, south leg
R_S = (3201.22, 3227.92)
T3_S = (2800.55, 3201.22)

T1_C = (6053.44, 6485.10)            # track 1, cross leg (north strip)
R_C = (6026.74, 6053.44)
T3_C = (5685.00, 6026.74)

T1_N = (2442.06, 3067.25)            # track 1, north leg
R_N = (2415.36, 2442.06)
T3_N = (1920.45, 2415.36)

START_Y = 5441.15                    # axis_42 north edge
TOP_42 = 401.15
END1_Y, TOP_790 = 6915.70, 280.05
END3_Y, TOP_721 = 7102.35, 213.35

G1 = math.degrees(math.atan2(121.10, 1203.56))
G3 = math.degrees(math.atan2(187.80, 1704.64))

# track 1 pad heights
T1_P1 = 339.54
T1_P2 = 323.37
# track 3 pad heights
T3_P1 = 374.28
T3_P2 = 331.84


def flat(name, x, y, top, thick=T):
    return {
        "name": name,
        "origin": [round((x[0]+x[1])/2, 4), round((y[0]+y[1])/2, 4),
                   round(top - thick/2, 4)],
        "extents": [round(x[1]-x[0], 4), round(y[1]-y[0], 4), thick],
        "angles": [0.0, 0.0, 0.0],
        "material": MAT,
    }


def ramp(name, x, y, top_hi, top_lo, yaw, grade, thick=T):
    """Slab descending along `yaw` (90 = toward +y, 180 = toward -x).
    Positive pitch descends along local +x, and local +z works out to
    (cos yaw * sin, sin yaw * sin, cos), so the box centre is the top
    surface midpoint pushed back half a thickness along that."""
    th = math.radians(grade)
    run = (y[1]-y[0]) if yaw == 90 else (x[1]-x[0])
    length = run / math.cos(th)
    cx, cy = (x[0]+x[1])/2.0, (y[0]+y[1])/2.0
    tz = (top_hi + top_lo)/2.0
    lz = [math.cos(math.radians(yaw))*math.sin(th),
          math.sin(math.radians(yaw))*math.sin(th),
          math.cos(th)]
    width = (x[1]-x[0]) if yaw == 90 else (y[1]-y[0])
    return {
        "name": name,
        "origin": [round(cx - (thick/2)*lz[0], 4),
                   round(cy - (thick/2)*lz[1], 4),
                   round(tz - (thick/2)*lz[2], 4)],
        "extents": [round(length, 4), round(width, 4), thick],
        "angles": [0.0, float(yaw), round(grade, 4)],
        "material": MAT,
    }


def seeds():
    b = []
    # ---- track 1 -----------------------------------------------------
    b.append(ramp("t1_ramp1", T1_S, (START_Y, T1_C[0]), TOP_42, T1_P1, 90, G1))
    b.append(flat("t1_pad1", T1_S, T1_C, T1_P1))
    b.append(ramp("t1_ramp2", (N_E, T1_S[0]), T1_C, T1_P1, T1_P2, 180, G1))
    b.append(flat("t1_pad2", T1_N, T1_C, T1_P2))
    b.append(ramp("t1_ramp3", T1_N, (T1_C[1], END1_Y), T1_P2, TOP_790, 90, G1))
    # ---- track 3 -----------------------------------------------------
    b.append(ramp("t3_ramp1", T3_S, (START_Y, T3_C[0]), TOP_42, T3_P1, 90, G3))
    b.append(flat("t3_pad1", T3_S, T3_C, T3_P1))
    b.append(ramp("t3_ramp2", (T3_N[1], T3_S[0]), T3_C, T3_P1, T3_P2, 180, G3))
    b.append(flat("t3_pad2", T3_N, T3_C, T3_P2))
    b.append(ramp("t3_ramp3", T3_N, (T3_C[1], END3_Y), T3_P2, TOP_721, 90, G3))
    # ---- railing: track 1's profile, plus 40.00, 106.7 tall ----------
    b.append(ramp("rail_s", R_S, (START_Y, T1_C[0]),
                  TOP_42+RAIL_RISE, T1_P1+RAIL_RISE, 90, G1, RAIL_T))
    b.append(ramp("rail_c_ramp", (N_E, T1_S[0]), R_C,
                  T1_P1+RAIL_RISE, T1_P2+RAIL_RISE, 180, G1, RAIL_T))
    b.append(flat("rail_c_flat", (R_N[0], N_E), R_C, T1_P2+RAIL_RISE, RAIL_T))
    b.append(flat("rail_n_pad", R_N, T1_C, T1_P2+RAIL_RISE, RAIL_T))
    b.append(ramp("rail_n_ramp", R_N, (T1_C[1], END1_Y),
                  T1_P2+RAIL_RISE, TOP_790+RAIL_RISE, 90, G1, RAIL_T))
    b.append(flat("rail_n_end", R_N, (END1_Y, 7102.40), TOP_790+RAIL_RISE, RAIL_T))
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
    with open(path, "w") as f:
        json.dump(plan, f, indent=1)
        f.write("\n")
    print("track1 %.4f deg, track3 %.4f deg; added %d, plan now %d boxes"
          % (G1, G3, added, len(plan["boxes"])))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_full.json")
