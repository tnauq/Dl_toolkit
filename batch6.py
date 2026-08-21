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
1 m is 39.37 units in this plan. The straight run is 240.30 (9 grid
units, 6.10 m) and each leg is 280.35 (10.5 grid units, 7.12 m), chosen
to land on the grid rather than on the exact metric figure. The straight
run was doubled from its original 120.15, which moves the apex and both
legs east with it.

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
STRAIGHT = 240.30               # 9 grid units, 6.10 m
SHELL = 26.70
BORE_H = 586.80
T_ROOM = 506.00


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


def troom(spec, out):
    """Square room: floor, ceiling and four walls, with flush openings."""
    name, centre, z, bore_h, size, openings = spec
    h = size / 2.0
    outer = size + 2 * SHELL

    def put(tag, ox, oy, oz, ex, ey, ez):
        out.append({"name": "%s_%s" % (name, tag),
                    "origin": [round(ox, 4), round(oy, 4), round(oz, 4)],
                    "extents": [round(ex, 4), round(ey, 4), round(ez, 4)],
                    "angles": [0.0, 0.0, 0.0], "material": MAT})

    put("floor", centre[0], centre[1], z - SHELL / 2.0, outer, outer, SHELL)
    put("ceil", centre[0], centre[1], z + bore_h + SHELL / 2.0,
        outer, outer, SHELL)
    for side in "nsew":
        if side in "ns":
            wy = centre[1] + (h + SHELL / 2.0) * (1 if side == "n" else -1)
            lo, hi = centre[0] - h - SHELL, centre[0] + h + SHELL
            if side in openings:
                off, w = openings[side]
                o0, o1 = centre[0] + off - w / 2.0, centre[0] + off + w / 2.0
                if o0 > lo:
                    put(side + "0", (lo + o0) / 2.0, wy, z + bore_h / 2.0,
                        o0 - lo, SHELL, bore_h)
                if hi > o1:
                    put(side + "1", (o1 + hi) / 2.0, wy, z + bore_h / 2.0,
                        hi - o1, SHELL, bore_h)
            else:
                put(side, centre[0], wy, z + bore_h / 2.0, outer, SHELL,
                    bore_h)
        else:
            wx = centre[0] + (h + SHELL / 2.0) * (1 if side == "e" else -1)
            lo, hi = centre[1] - h - SHELL, centre[1] + h + SHELL
            if side in openings:
                off, w = openings[side]
                o0, o1 = centre[1] + off - w / 2.0, centre[1] + off + w / 2.0
                if o0 > lo:
                    put(side + "0", wx, (lo + o0) / 2.0, z + bore_h / 2.0,
                        SHELL, o0 - lo, bore_h)
                if hi > o1:
                    put(side + "1", wx, (o1 + hi) / 2.0, z + bore_h / 2.0,
                        SHELL, hi - o1, bore_h)
            else:
                put(side, wx, centre[1], z + bore_h / 2.0, SHELL, outer,
                    bore_h)


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
    prefixes = ["vtun_", "m_vtun_", "ttun_", "m_ttun_"]
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
    # A T fork, not a V. Every piece is axis aligned, so nothing has to be
    # mitred and no tapers are needed: the straight run ends in a square
    # room and the two branches leave it at right angles through flush
    # openings in its walls.
    bore_z0, bore_z1 = DOOR_SILL, DOOR_HEAD
    sy0 = DOOR_CENTRE_Y - BORE_W / 2.0
    sy1 = DOOR_CENTRE_Y + BORE_W / 2.0
    room_c = (DOOR_FACE_X + STRAIGHT + T_ROOM / 2.0, DOOR_CENTRE_Y)
    made.append(box("ttun_straight_floor", (DOOR_FACE_X, room_c[0] - T_ROOM / 2.0),
                    (sy0, sy1), (bore_z0 - SHELL, bore_z0)))
    made.append(box("ttun_straight_ceil", (DOOR_FACE_X, room_c[0] - T_ROOM / 2.0),
                    (sy0, sy1), (bore_z1, bore_z1 + SHELL)))
    made.append(box("ttun_straight_wall_s", (DOOR_FACE_X, room_c[0] - T_ROOM / 2.0),
                    (sy0 - SHELL, sy0), (bore_z0, bore_z1)))
    made.append(box("ttun_straight_wall_n", (DOOR_FACE_X, room_c[0] - T_ROOM / 2.0),
                    (sy1, sy1 + SHELL), (bore_z0, bore_z1)))
    print("T straight: x %.2f..%.2f, bore %.2f wide, z %.2f..%.2f"
          % (DOOR_FACE_X, room_c[0] - T_ROOM / 2.0, BORE_W, bore_z0, bore_z1))

    troom(("ttun_room", room_c, bore_z0, BORE_H, T_ROOM,
           {"w": (0.0, BORE_W), "n": (0.0, BORE_W), "s": (0.0, BORE_W)}),
          made)
    print("T room: %.2f square, centre (%.2f, %.2f), openings west (the "
          "straight run) and north and south (the two branches)"
          % (T_ROOM, room_c[0], room_c[1]))
    print("     branch faces at y %.2f and %.2f, x centre %.2f"
          % (room_c[1] + T_ROOM / 2.0, room_c[1] - T_ROOM / 2.0, room_c[0]))

    twins = [mirror_box(b, "m_" + b["name"]) for b in made]
    boxes.extend(made)
    boxes.extend(twins)
    print("batch6.py: added %d half boxes + %d twins, %d boxes in plan"
          % (len(made), len(twins), len(boxes)))

    with open(path, "w") as f:
        json.dump(plan, f, indent=1)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_full.json")
