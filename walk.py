#!/usr/bin/env python3
"""Two parallel tracks carried around the S, extending m_axis_790
(deck 1) and m_merged_721 (deck 3) south to axis_42, with m_axis_786
(the railing) carried along on deck 1's profile.

    mirror.py -> stitch.py -> bridge.py -> seam.py -> walk.py

ANGLE ORDER.  angles is [PITCH, YAW, ROLL].  ramp-slab_383 in the source
plan is [23.96, 90.0, 0.0] and the viewer reads index 0 as pitch, so the
grade goes in index 0.  An earlier version of this file put it in index
2, which is roll: every ramp tilted sideways across its width instead of
falling along its run, and every check agreed with itself because it
read the same wrong index back.

SQUARE PADS, at the cost of the per-leg ratio.  A corner pad can only be
square if the track is the same width on both legs it joins, so each
track now holds ONE width all the way round.  The narrowest leg is the
cross leg at 800.10, so the band is sized to that:

    track 1  431.66     railing  26.70     track 3  341.74

That still splits in the source ratio 640.10 : 506.75, so the ratio
survives; what is given up is filling the wider legs.  The south leg has
133.40 of slack and the north leg 346.70, both left on the LEFT hand of
travel, since track 1 rides the right hand throughout.

The north leg band is anchored so track 3's east edge lands on 2413.85,
which is deck 1's west edge.  That keeps track 3 clear of deck 1
entirely; anchoring it any further east would run track 3 underneath
deck 1's lip on its way down to 213.35.

GRADES.  Two square pads per track, three sloped runs each:

    track 1   rise 121.10 over 1473.07 of slope   4.7009 deg
    track 3   rise 187.80 over 1839.66 of slope   5.8296 deg

RAILING.  Track 1's profile plus 40.00 everywhere, including at the
axis_42 end, where track 1 finishes at 401.15 and the railing therefore
finishes at 441.15, not flat at 401.15.
"""

import json
import math
import sys

MAT = "materials/dev/reflectivity_30.vmat"
XP, YP = 460.1, 6085.05
T = 26.7
RAIL_T = 106.7
RAIL_RISE = 40.00

W1, WR, W3 = 431.66, 26.70, 341.74

# Band anchoring, from the crosshairs.  The band is 800.10 and only the
# cross leg is that wide, so the slack in the other two legs has to be
# pushed to one side.  It goes to the INSIDE of each turn, which is what
# puts each square pad's corner on the corresponding wall corner:
#   south leg  flush WEST  against seam_w_a at 2800.55
#   north leg  flush EAST  against seam_e_c at 3067.25
T3_S = (2800.55, 2800.55 + W3)
R_S = (T3_S[1], T3_S[1] + WR)
T1_S = (R_S[1], R_S[1] + W1)

T1_C = (6485.10 - W1, 6485.10)
R_C = (T1_C[0] - WR, T1_C[0])
T3_C = (R_C[0] - W3, R_C[0])

T1_N = (3067.25 - W1, 3067.25)
R_N = (T1_N[0] - WR, T1_N[0])
T3_N = (R_N[0] - W3, R_N[0])

# m_axis_786's own line, which the railing has to finish on
SRC_RAIL = (2387.15, 2413.85)

START_Y, TOP_42 = 5441.15, 401.15
END1_Y, TOP_790 = 6915.70, 280.05
END3_Y, TOP_721 = 7102.35, 213.35

# run lengths, slope only: start->pad1, pad1->pad2, pad2->finish
R1 = (T1_C[0] - START_Y, T1_S[0] - T1_N[1], END1_Y - T1_C[1])
R3 = (T3_C[0] - START_Y, T3_S[0] - T3_N[1], END3_Y - T3_C[1])
G1 = math.degrees(math.atan2(TOP_42 - TOP_790, sum(R1)))
G3 = math.degrees(math.atan2(TOP_42 - TOP_721, sum(R3)))
K1 = (TOP_42 - TOP_790) / sum(R1)
K3 = (TOP_42 - TOP_721) / sum(R3)

T1_P1 = TOP_42 - R1[0]*K1
T1_P2 = T1_P1 - R1[1]*K1
T3_P1 = TOP_42 - R3[0]*K3
T3_P2 = T3_P1 - R3[1]*K3


def flat(name, x, y, top, thick=T):
    return {"name": name,
            "origin": [round((x[0]+x[1])/2, 4), round((y[0]+y[1])/2, 4),
                       round(top - thick/2, 4)],
            "extents": [round(x[1]-x[0], 4), round(y[1]-y[0], 4), thick],
            "angles": [0.0, 0.0, 0.0], "material": MAT}


def ramp(name, x, y, top_hi, top_lo, yaw, grade, thick=T):
    """Slab falling along `yaw`: 90 is toward +y, 180 is toward -x.
    Local +x is the run and positive pitch descends along it, so pitch
    goes in angles[0].  Local +z is then
    (cos yaw sin p, sin yaw sin p, cos p), and the box centre is the top
    surface midpoint pushed back half a thickness along that."""
    th = math.radians(grade)
    run = (y[1]-y[0]) if yaw == 90 else (x[1]-x[0])
    width = (x[1]-x[0]) if yaw == 90 else (y[1]-y[0])
    lz = [math.cos(math.radians(yaw))*math.sin(th),
          math.sin(math.radians(yaw))*math.sin(th), math.cos(th)]
    return {"name": name,
            "origin": [round((x[0]+x[1])/2 - (thick/2)*lz[0], 4),
                       round((y[0]+y[1])/2 - (thick/2)*lz[1], 4),
                       round((top_hi+top_lo)/2 - (thick/2)*lz[2], 4)],
            "extents": [round(run/math.cos(th), 4), round(width, 4), thick],
            "angles": [round(grade, 4), float(yaw), 0.0], "material": MAT}


def seeds():
    b = []
    b.append(ramp("t1_ramp1", T1_S, (START_Y, T1_C[0]), TOP_42, T1_P1, 90, G1))
    b.append(flat("t1_pad1", T1_S, T1_C, T1_P1))
    b.append(ramp("t1_ramp2", (T1_N[1], T1_S[0]), T1_C, T1_P1, T1_P2, 180, G1))
    b.append(flat("t1_pad2", T1_N, T1_C, T1_P2))
    b.append(ramp("t1_ramp3", T1_N, (T1_C[1], END1_Y), T1_P2, TOP_790, 90, G1))

    b.append(ramp("t3_ramp1", T3_S, (START_Y, T3_C[0]), TOP_42, T3_P1, 90, G3))
    b.append(flat("t3_pad1", T3_S, T3_C, T3_P1))
    b.append(ramp("t3_ramp2", (T3_N[1], T3_S[0]), T3_C, T3_P1, T3_P2, 180, G3))
    b.append(flat("t3_pad2", T3_N, T3_C, T3_P2))
    b.append(ramp("t3_ramp3", T3_N, (T3_C[1], END3_Y), T3_P2, TOP_721, 90, G3))

    RR = RAIL_RISE
    b.append(ramp("rail_s", R_S, (START_Y, T1_C[0]),
                  TOP_42+RR, T1_P1+RR, 90, G1, RAIL_T))
    b.append(ramp("rail_c_ramp", (T1_N[1], T1_S[0]), R_C,
                  T1_P1+RR, T1_P2+RR, 180, G1, RAIL_T))
    b.append(flat("rail_c_flat", (R_N[0], T1_N[1]), R_C, T1_P2+RR, RAIL_T))
    b.append(flat("rail_n_pad", R_N, T1_C, T1_P2+RR, RAIL_T))
    b.append(ramp("rail_n_ramp", R_N, (T1_C[1], END1_Y),
                  T1_P2+RR, TOP_790+RR, 90, G1, RAIL_T))
    # Terminus.  The corridor railing line and m_axis_786's line are
    # 221.74 apart in x, so the railing dog-legs west along deck 1's
    # south edge and then runs north ON m_axis_786's own line, flat at
    # 320.05, which is deck 1's 280.05 plus the same 40.00.
    b.append(flat("rail_n_jog", (SRC_RAIL[0], R_N[1]),
                  (END1_Y, END1_Y+WR), TOP_790+RR, RAIL_T))
    b.append(flat("rail_n_end", SRC_RAIL, (END1_Y+WR, 7102.40),
                  TOP_790+RR, RAIL_T))
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
                continue
            plan["boxes"].append(bx)
            have.add(bx["name"])
            added += 1
    with open(path, "w") as f:
        json.dump(plan, f, indent=1)
        f.write("\n")
    print("track1 %.4f deg pads %.2f %.2f | track3 %.4f deg pads %.2f %.2f"
          % (G1, T1_P1, T1_P2, G3, T3_P1, T3_P2))
    print("added %d, plan now %d boxes" % (added, len(plan["boxes"])))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_full.json")
