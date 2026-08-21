#!/usr/bin/env python3
"""batch6.py - twelfth build step, run after batch5.py.

  1. A shrunk _d195 through axis_553_mid, tucked into the corner with
     axis_739, sill on axis_761.
  2. A straight tunnel east out of the seam_e_a door, then a V, each leg
     carried further.

WHY THE DOOR IS SCALED RATHER THAN SHORTENED
The space is 240.20 wide (axis_553_mid's south end 3040.45 to axis_739's
south face 3280.65) by 560.10 tall (axis_761's top 720.20 to the wall top
1280.30). A _d195 is 253.00 by 586.80, so it is over on both axes.

Shortening alone does not fix the width, and narrowing alone does not fix
the height, so the whole opening is scaled by 240.20 / 253.00 = 0.949407,
giving 240.20 by 557.10. Width is the binding constraint; the height
lands 3.00 under the wall top, which becomes a thin header.

The scale is applied in the world y-z plane only, so it is a uniform
scale in that plane and every pitch angle is preserved exactly. Wall
thickness, which lies along world x for this wall, is untouched. Head
pieces sit at yaw 0 or +/-90, so the two extents to scale are picked per
piece from its yaw rather than assumed.

axis_553_mid is 53.30 thick, twice the 26.70 arch source, so the head is
cloned three times across the thickness with overlap, per the standing
convention on thick walls.

THE V TUNNEL
1 m is 39.37 units in this plan. The straight run is 120.15 (4.5 grid
units, 3.05 m) and each leg is 280.35 (10.5 grid units, 7.12 m), chosen
to land on the grid rather than on the exact metric figure.

Each leg is built from its apex outward: the inner faces of the two legs
both start at the split point on the centreline, so the nose of the V is
a point rather than a blunt end. The leg boxes overlap each other in the
crotch, which is intended and harmless.

Every box is made on the half side and its m_ twin derived by the plan
transform (x' = 920.2 - x, y' = 12170.1 - y, yaw' = yaw + 180). Name-keyed
and rerunnable.

Usage: python3 batch6.py docs/plans/dust2_full.json
"""

import json
import math
import sys

MAT = "materials/dev/reflectivity_30.vmat"
MIRROR_X = 920.2
MIRROR_Y = 12170.1

ARCH_PREFIX = "arch_w_"
ARCH_SRC_Y = 5818.40
ARCH_SRC_SILL = 344.55
D195_W = 253.00
D195_H = 586.80
# The head assembly is bigger than the nominal opening: its voussoirs bed
# 25.92 into each jamb and the crown sits 6.29 above the nominal head.
# Measured off arch_w_* in the plan, not assumed.
HEAD_BED = 25.92
HEAD_CROWN_ABOVE_SILL = 593.09

# ---------------------------------------------------------------- change 1
WALL = "axis_553_mid"
SPACE_Y = (3040.45, 3280.65)    # wall south end to axis_739's south face
SILL = 720.20                   # axis_761 top
WALL_TOP = 1280.30
CLONES_ACROSS = 3

# ---------------------------------------------------------------- change 2
UNITS_PER_M = 39.37
DOOR_FACE_X = 3760.75           # seam_e_a east face
DOOR_CENTRE_Y = 6255.92
DOOR_SILL = 364.62
DOOR_HEAD = 951.42
BORE_W = 253.00
STRAIGHT = 120.15               # 3.05 m
LEG = 280.35                    # 7.12 m
LEG_YAW = 30.0                  # each leg off the axis, so 60 total
SHELL = 26.70


def box(name, xr, yr, zr):
    return {
        "name": name,
        "origin": [round((xr[0] + xr[1]) / 2.0, 4),
                   round((yr[0] + yr[1]) / 2.0, 4),
                   round((zr[0] + zr[1]) / 2.0, 4)],
        "extents": [round(xr[1] - xr[0], 4),
                    round(yr[1] - yr[0], 4),
                    round(zr[1] - zr[0], 4)],
        "angles": [0.0, 0.0, 0.0],
        "material": MAT,
    }


def rot_box(name, centre, extents, yaw):
    return {
        "name": name,
        "origin": [round(centre[0], 4), round(centre[1], 4),
                   round(centre[2], 4)],
        "extents": [round(e, 4) for e in extents],
        "angles": [0.0, round(yaw, 4), 0.0],
        "material": MAT,
    }


def mirror_box(b, name):
    o = b["origin"]
    a = b["angles"]
    return {
        "name": name,
        "origin": [round(MIRROR_X - o[0], 4),
                   round(MIRROR_Y - o[1], 4),
                   o[2]],
        "extents": list(b["extents"]),
        "angles": [a[0], round((a[1] + 180.0) % 360.0, 4), a[2]],
        "material": b.get("material", MAT),
    }


def span(b, i):
    return (b["origin"][i] - b["extents"][i] / 2.0,
            b["origin"][i] + b["extents"][i] / 2.0)


def scale_head_piece(b, name, cx, cy, sill, s):
    """Clone an arch_w_ piece scaled by s in the world y-z plane.

    The piece's local axes are axis-aligned in world for yaw 0 and +/-90,
    so a uniform y-z scale maps to scaling exactly two of its extents and
    leaves every angle untouched. Which two depends on the yaw.
    """
    yaw = round(b["angles"][1]) % 180
    e = list(b["extents"])
    if yaw == 0:
        e[1] *= s          # local y is world y
        e[2] *= s
    elif yaw == 90:
        e[0] *= s          # local x is in the world y-z plane
        e[2] *= s
    else:
        raise ValueError("unexpected yaw %r on %s" % (b["angles"][1],
                                                      b["name"]))
    o = b["origin"]
    return {
        "name": name,
        "origin": [round(cx, 4),
                   round(cy + (o[1] - ARCH_SRC_Y) * s, 4),
                   round(sill + (o[2] - ARCH_SRC_SILL) * s, 4)],
        "extents": [round(v, 4) for v in e],
        "angles": list(b["angles"]),
        "material": b.get("material", MAT),
    }


def main(path):
    with open(path) as f:
        plan = json.load(f)
    boxes = plan["boxes"]
    present = set(b["name"] for b in boxes)

    # ------------------------------------------------------------ cleanup
    drop = set()
    prefixes = ["vtun_", "m_vtun_"]
    # Only clear the door's outputs if the source wall is still there to cut
    # again. If the wall is gone the cut already happened, and clearing would
    # delete it with nothing to rebuild from.
    if WALL in present:
        for suffix in ("_s", "_n", "_under", "_hdr"):
            drop.add(WALL + suffix)
            drop.add("m_" + WALL + suffix)
        prefixes.append("arch_" + WALL + "_")
        prefixes.append("m_arch_" + WALL + "_")
    before = len(boxes)
    boxes[:] = [b for b in boxes
                if b["name"] not in drop
                and not any(b["name"].startswith(p) for p in prefixes)]
    if before != len(boxes):
        print("REBUILD: removed %d previous outputs" % (before - len(boxes)))

    by_name = {b["name"]: b for b in boxes}
    made = []

    # ---------------------------------------------------------- change 1
    wall = by_name.get(WALL)
    if wall is None:
        print("SKIP %s: not in plan, already cut on a previous run" % WALL)
    else:
        wx = span(wall, 0)
        wy = span(wall, 1)
        wz = span(wall, 2)
        avail_w = SPACE_Y[1] - SPACE_Y[0]
        avail_h = WALL_TOP - SILL
        # Height is limited by the crown, not by the nominal head, or the
        # top of the arch pokes above the wall.
        s = min(avail_w / D195_W, avail_h / HEAD_CROWN_ABOVE_SILL)
        ow = D195_W * s
        oh = D195_H * s
        oy0 = SPACE_Y[1] - ow
        oy1 = SPACE_Y[1]
        head = SILL + oh
        crown = SILL + HEAD_CROWN_ABOVE_SILL * s
        cy = (oy0 + oy1) / 2.0

        print("DOOR %s: space %.2f x %.2f, scale %.6f, clear %.2f x %.2f"
              % (WALL, avail_w, avail_h, s, ow, oh))
        print("     y %.2f..%.2f, sill %.2f, head %.2f, crown %.2f, top %.2f"
              % (oy0, oy1, SILL, head, crown, wz[1]))
        print("     south jamb %.2f, head beds %.2f into each jamb so it "
              "overhangs the wall end by %.2f"
              % (oy0 - wy[0], HEAD_BED * s, HEAD_BED * s - (oy0 - wy[0])))

        pieces = []
        if oy0 > wy[0]:
            pieces.append(box(WALL + "_s", wx, (wy[0], oy0), wz))
        if wy[1] > oy1:
            pieces.append(box(WALL + "_n", wx, (oy1, wy[1]), wz))
        if SILL > wz[0]:
            pieces.append(box(WALL + "_under", wx, (oy0, oy1), (wz[0], SILL)))
        if wz[1] > crown + 0.01:
            pieces.append(box(WALL + "_hdr", wx, (oy0, oy1), (crown, wz[1])))
        else:
            print("     no header piece: the crown reaches the wall top")

        thickness = wx[1] - wx[0]
        src_t = 26.70
        step = (thickness - src_t) / (CLONES_ACROSS - 1)
        heads = []
        for i in range(CLONES_ACROSS):
            cx = wx[0] + src_t / 2.0 + step * i
            for b in list(boxes):
                if not b["name"].startswith(ARCH_PREFIX):
                    continue
                nm = b["name"].replace(ARCH_PREFIX,
                                       "arch_%s_%d_" % (WALL, i), 1)
                heads.append(scale_head_piece(b, nm, cx, cy, SILL, s))
        print("     %d wall pieces, %d head pieces in %d layers across %.2f"
              % (len(pieces), len(heads), CLONES_ACROSS, thickness))

        boxes[:] = [b for b in boxes
                    if b["name"] != WALL and b["name"] != "m_" + WALL]
        made.extend(pieces + heads)

    # ---------------------------------------------------------- change 2
    bore_z = (DOOR_SILL, DOOR_HEAD)
    sy0 = DOOR_CENTRE_Y - BORE_W / 2.0
    sy1 = DOOR_CENTRE_Y + BORE_W / 2.0
    sx0 = DOOR_FACE_X
    sx1 = DOOR_FACE_X + STRAIGHT

    made.append(box("vtun_straight_floor", (sx0, sx1), (sy0, sy1),
                    (bore_z[0] - SHELL, bore_z[0])))
    made.append(box("vtun_straight_ceil", (sx0, sx1), (sy0, sy1),
                    (bore_z[1], bore_z[1] + SHELL)))
    made.append(box("vtun_straight_wall_s", (sx0, sx1),
                    (sy0 - SHELL, sy0), bore_z))
    made.append(box("vtun_straight_wall_n", (sx0, sx1),
                    (sy1, sy1 + SHELL), bore_z))
    print("TUNNEL straight: x %.2f..%.2f (%.2f, %.2f m), bore %.2f wide, "
          "z %.2f..%.2f" % (sx0, sx1, STRAIGHT, STRAIGHT / UNITS_PER_M,
                            BORE_W, bore_z[0], bore_z[1]))

    apex = (sx1, DOOR_CENTRE_Y)
    zc_bore = (bore_z[0] + bore_z[1]) / 2.0
    bore_h = bore_z[1] - bore_z[0]
    for tag, sign in (("n", 1.0), ("s", -1.0)):
        yaw = LEG_YAW * sign
        r = math.radians(yaw)
        u = (math.cos(r), math.sin(r))            # along the leg
        v = (-math.sin(r) * sign, math.cos(r) * sign)   # outward from apex

        def at(du, dv, z):
            return (apex[0] + u[0] * du + v[0] * dv,
                    apex[1] + u[1] * du + v[1] * dv,
                    z)

        mid_u = LEG / 2.0
        made.append(rot_box("vtun_leg_%s_floor" % tag,
                            at(mid_u, BORE_W / 2.0, bore_z[0] - SHELL / 2.0),
                            (LEG, BORE_W, SHELL), yaw))
        made.append(rot_box("vtun_leg_%s_ceil" % tag,
                            at(mid_u, BORE_W / 2.0, bore_z[1] + SHELL / 2.0),
                            (LEG, BORE_W, SHELL), yaw))
        made.append(rot_box("vtun_leg_%s_wall_out" % tag,
                            at(mid_u, BORE_W + SHELL / 2.0, zc_bore),
                            (LEG, SHELL, bore_h), yaw))
        made.append(rot_box("vtun_leg_%s_wall_in" % tag,
                            at(mid_u, -SHELL / 2.0, zc_bore),
                            (LEG, SHELL, bore_h), yaw))
        tip = at(LEG, BORE_W / 2.0, 0.0)
        print("TUNNEL leg %s: yaw %+.1f, length %.2f (%.2f m), "
              "centre of mouth ends at x %.2f y %.2f"
              % (tag, yaw, LEG, LEG / UNITS_PER_M, tip[0], tip[1]))

    twins = [mirror_box(b, "m_" + b["name"]) for b in made]
    boxes.extend(made)
    boxes.extend(twins)
    print("batch6.py: added %d half boxes + %d twins, %d boxes in plan"
          % (len(made), len(twins), len(boxes)))

    with open(path, "w") as f:
        json.dump(plan, f, indent=1)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_full.json")
