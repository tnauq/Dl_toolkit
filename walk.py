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

# All four outer corners of the S are pinned to wall corners, so every
# leg is flush on BOTH sides and the band fills it.  That forces the
# track width to change leg by leg, and a corner pad therefore cannot be
# square: it spans its track's width on both legs it joins, and those
# two widths differ.  The pads below are the full corner rectangles,
# which is the only shape that closes the turn with no hole and no
# crease.  The railing keeps its 26.70 and the rest splits in the source
# ratio 640.10 : 506.75.
RATIO1 = 640.10 / (640.10 + 506.75)
WR = 26.70

# leg interiors, wall face to wall face
LEG_S = (2800.55, 3734.05)          # 933.50
LEG_C = (5685.00, 6485.10)          # 800.10
LEG_N = (1920.45, 3067.25)          # 1146.80


def split(lo, hi, one_high):
    """Divide a leg into track 3, railing, track 1.  Track 1 rides the
    right hand of travel, so it takes the HIGH side in the south and
    north legs and the high (north) side of the cross leg too."""
    w1 = (hi - lo - WR) * RATIO1
    if one_high:
        t1 = (hi - w1, hi)
        r = (t1[0] - WR, t1[0])
        t3 = (lo, r[0])
    else:
        t1 = (lo, lo + w1)
        r = (t1[1], t1[1] + WR)
        t3 = (r[1], hi)
    return t1, r, t3


T1_S, R_S, T3_S = split(LEG_S[0], LEG_S[1], True)
T1_C, R_C, T3_C = split(LEG_C[0], LEG_C[1], True)
# North leg is NOT split by ratio: the railing is placed on
# m_axis_786's own line so the two run as one, which is what kills the
# dog-leg.  Both walls stay flush, so the two tracks simply take what is
# left either side (653.40 and 466.70 rather than the ratio's 625.17 and
# 494.93).
R_N = (2387.15, 2413.85)
T1_N = (R_N[1], LEG_N[1])
T3_N = (LEG_N[0], R_N[0])

SRC_RAIL = (2387.15, 2413.85)       # m_axis_786's own line

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

# Pad heights are now SET, not derived from one grade: the pad nearest
# the deck sits at 33% of that track's total rise and the next at 66%.
T1_P2 = TOP_790 + 0.33*(TOP_42 - TOP_790)
T1_P1 = TOP_790 + 0.66*(TOP_42 - TOP_790)
T3_P2 = TOP_721 + 0.33*(TOP_42 - TOP_721)
T3_P1 = TOP_721 + 0.66*(TOP_42 - TOP_721)

# Each ramp therefore gets its OWN grade, from its own run and rise.
def grade(rise, run):
    return math.degrees(math.atan2(rise, run))

G1A = grade(TOP_42 - T1_P1, R1[0])
G1B = grade(T1_P1 - T1_P2, R1[1])
G1C = grade(T1_P2 - TOP_790, R1[2])
G3A = grade(TOP_42 - T3_P1, R3[0])
G3B = grade(T3_P1 - T3_P2, R3[1])
G3C = grade(T3_P2 - TOP_721, R3[2])


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
    b.append(ramp("t1_ramp1", T1_S, (START_Y, T1_C[0]), TOP_42, T1_P1, 90, G1A))
    b.append(flat("t1_pad1", T1_S, T1_C, T1_P1))
    b.append(ramp("t1_ramp2", (T1_N[1], T1_S[0]), T1_C, T1_P1, T1_P2, 180, G1B))
    b.append(flat("t1_pad2", T1_N, T1_C, T1_P2))
    b.append(ramp("t1_ramp3", T1_N, (T1_C[1], END1_Y), T1_P2, TOP_790, 90, G1C))

    b.append(ramp("t3_ramp1", T3_S, (START_Y, T3_C[0]), TOP_42, T3_P1, 90, G3A))
    b.append(flat("t3_pad1", T3_S, T3_C, T3_P1))
    b.append(ramp("t3_ramp2", (T3_N[1], T3_S[0]), T3_C, T3_P1, T3_P2, 180, G3B))
    b.append(flat("t3_pad2", T3_N, T3_C, T3_P2))
    b.append(ramp("t3_ramp3", T3_N, (T3_C[1], END3_Y), T3_P2, TOP_721, 90, G3C))

    RR = RAIL_RISE
    b.append(ramp("rail_s", R_S, (START_Y, T1_C[0]),
                  TOP_42+RR, T1_P1+RR, 90, G1A, RAIL_T))
    b.append(ramp("rail_c_ramp", (T1_N[1], T1_S[0]), R_C,
                  T1_P1+RR, T1_P2+RR, 180, G1B, RAIL_T))
    b.append(flat("rail_c_flat", (R_N[0], T1_N[1]), R_C, T1_P2+RR, RAIL_T))
    b.append(flat("rail_n_pad", R_N, T1_C, T1_P2+RR, RAIL_T))
    b.append(ramp("rail_n_ramp", R_N, (T1_C[1], END1_Y),
                  T1_P2+RR, TOP_790+RR, 90, G1C, RAIL_T))
    # Terminus: the railing is already on m_axis_786's line, so it just
    # runs straight on to meet it.  No dog-leg.
    b.append(flat("rail_n_end", R_N, (END1_Y, 7102.40), TOP_790+RR, RAIL_T))
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
    print("track1 pads %.2f %.2f  grades %.4f %.4f %.4f"
          % (T1_P1, T1_P2, G1A, G1B, G1C))
    print("track3 pads %.2f %.2f  grades %.4f %.4f %.4f"
          % (T3_P1, T3_P2, G3A, G3B, G3C))
    print("added %d, plan now %d boxes" % (added, len(plan["boxes"])))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_full.json")
