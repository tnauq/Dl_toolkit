#!/usr/bin/env python3
"""batch7.py - thirteenth build step, run after batch6.py.

Carries the two V leg mouths out to the two open doors, crossing once in
plan, with the higher door's tunnel riding over the lower one.

ASSIGNMENT
  north mouth (m_vtun_leg_s, y 6163.91)  ->  axis_553_mid door, sill 720.20
  south mouth (m_vtun_leg_n, y 5664.45)  ->  m_axis_47 door,    sill 213.40

BORE
Full 253.00 x 586.80, the same as the V, so neither mouth has any step or
taper in it. The bore only changes in two places, both with stepped
transitions rather than a cliff:
  - the lower drops its ceiling to 293.70 over a 534.00 stretch where the
    upper crosses above it, and comes straight back up
  - the upper narrows to 186.90 x 554.16 for its last two legs, because it
    has to squeeze past hex2_wall_e_l and then fit a door that is itself
    only 238.93 x 554.16

WHY THE UPPER RUNS AT 893.60
Every box in the hex2 complex tops out at 866.90. A floor at 893.60 clears
all of it by exactly one shell, which lets the run alongside axis_553_mid_n
stay level the whole way as asked. It hugs the wall's west face at
x -2313.55 down to y 3700, past hex2_tun_ne_wall_r1 which ends at 4776.14,
then dog-legs west and south around the hex2 east tunnel before dropping to
the door sill on the final approach.

Usage: python3 batch7.py docs/plans/dust2_full.json
"""

import json
import math
import sys

MAT = "materials/dev/reflectivity_30.vmat"
MIRROR_X = 920.2
MIRROR_Y = 12170.1

SHELL = 26.70
BORE_W = 186.90        # 7 grid units
BORE_H = 266.70        # 10 grid units, 2.72 gen_man at 98 units tall

# Mouth centres and bearings, read off the m_vtun legs.
UP_MOUTH = (-3260.38, 6163.91)
UP_BEAR = 150.0
LO_MOUTH = (-3260.38, 5664.45)
LO_BEAR = 210.0

MOUTH_FLOOR = 364.62

# Full bore, identical to the V so the mouths need no transition at all.
BORE_W = 253.00
BORE_H = 586.80

UP_EXT_LEN = 1500.0
LO_EXT_LEN = 1200.0
UP_MID = 684.72            # top of the upper ext ramp
LO_MID = 213.40            # m_axis_47 sill, reached on the ext and held

# The only pinch is where the two actually cross, on the lower tunnel.
# The upper's ramp passes over the lower's band between 594.20 and 646.90,
# so its floor bottom there is 567.50 at worst. 213.40 + 293.70 + 26.70 is
# 533.80, which clears that by 33.70.
PINCH_H = 293.70
PINCH_Y = 6763.91          # where the upper ext crosses the lower band
PINCH_LEN = 534.00
TAPER_LEN = 160.20

# Upper level run. Every hex2 box tops out at 866.90, so a floor at 893.60
# clears the whole complex by exactly one shell and the run can stay level
# the way you asked.
UP_LEVEL = 906.50   # d553n voussoirs reach 873.09, not 866.90; measured
HEX2_TOP = 873.09

WALL_FACE = -2187.05       # axis_553_mid_n west face, the wall to hug
UP_HUG_X = WALL_FACE - BORE_W / 2.0 - SHELL   # outer wall face on -2187.05
UP_HUG_N = 4900.00         # past hex2_tun_ne_wall_r1, which ends at 4776.14
UP_DOGLEG_Y = 3700.00

# Squeezing past hex2_wall_e_l, x -3000.55..-2973.85, needs the narrow bore.
UP_NARROW_W = 160.20
UP_APPROACH_X = -2840.00
                           # hex2_wall_ne_r -2964.13 both cleared
UP_RAMP_END_X = -2520.00
UP_LINK_X = -4640.00
UP_APPROACH_Y = 3187.30
                           # clear of hex2_tun_e_wall_r0, which ends at 3067.15

# axis_553_mid door
UP_DOOR_FACE = -2187.05
UP_DOOR_SILL = 720.20
UP_DOOR_H = 554.16

# m_axis_47 door
LO_DOOR_FACE = -3080.65
LO_DOOR_Y = 7922.45
LO_DOOR_SILL = 213.40

ROOM = 253.00
PREFIX = "xtun_"


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


def seg(name, p0, p1, z0, z1, bore_w, bore_h, out):
    """A corridor from p0 to p1 whose floor top runs z0 to z1.

    Emits floor, ceiling and both side walls. Roll is left at zero so the
    floor stays level across its width no matter what the pitch is.
    """
    dx = p1[0] - p0[0]
    dy = p1[1] - p0[1]
    run = math.hypot(dx, dy)
    if run < 1e-6:
        return
    yaw = math.degrees(math.atan2(dy, dx))
    dz = z1 - z0
    # In Source a positive pitch DESCENDS along local +x, so a rising ramp
    # needs a negative pitch. Verified against ramp-slab_367, which carries
    # pitch +12.2 and drops as x increases.
    pitch = -math.degrees(math.atan2(dz, run))
    slope = math.hypot(run, dz)

    cx = (p0[0] + p1[0]) / 2.0
    cy = (p0[1] + p1[1]) / 2.0
    cz = (z0 + z1) / 2.0

    r = math.radians(yaw)
    vx, vy = -math.sin(r), math.cos(r)          # across the corridor

    # Local +z of a pitched, yawed box. Offsets from the ramp surface are
    # taken along this, not along world z, or the slab drifts off the ramp.
    pr = math.radians(pitch)
    nz = (math.cos(r) * math.sin(pr), math.sin(r) * math.sin(pr),
          math.cos(pr))

    def put(tag, along_n, side, ex, ey, ez):
        out.append({
            "name": "%s_%s" % (name, tag),
            "origin": [round(cx + nz[0] * along_n + vx * side, 4),
                       round(cy + nz[1] * along_n + vy * side, 4),
                       round(cz + nz[2] * along_n, 4)],
            "extents": [round(ex, 4), round(ey, 4), round(ez, 4)],
            "angles": [round(pitch, 4), round(yaw % 360.0, 4), 0.0],
            "material": MAT,
        })

    off = (bore_w + SHELL) / 2.0
    put("floor", -SHELL / 2.0, 0.0, slope, bore_w, SHELL)
    put("ceil", bore_h + SHELL / 2.0, 0.0, slope, bore_w, SHELL)
    put("wall_l", bore_h / 2.0, off, slope, SHELL, bore_h)
    put("wall_r", bore_h / 2.0, -off, slope, SHELL, bore_h)
    return dict(yaw=yaw, pitch=pitch, run=run, slope=slope)


def taper(name, p0, p1, z, w0, h0, w1, h1, out):
    """Step a bore from one size to another over three sub-segments, so the
    change reads as a shoulder rather than a cliff."""
    n = 3
    for k in range(n):
        a = (p0[0] + (p1[0] - p0[0]) * k / n,
             p0[1] + (p1[1] - p0[1]) * k / n)
        b = (p0[0] + (p1[0] - p0[0]) * (k + 1) / n,
             p0[1] + (p1[1] - p0[1]) * (k + 1) / n)
        f = (k + 1.0) / n
        seg("%s%d" % (name, k), a, b, z, z,
            w0 + (w1 - w0) * f, h0 + (h1 - h0) * f, out)


def room(name, centre, z, bore_h, size, openings, out, walls=None):
    """A room with a floor, a ceiling and real walls.

    openings maps a side ('n','s','e','w') to (offset, width). The offset is
    measured along that wall from the room centre, so a corridor that does
    not line up with the centre still gets a flush opening. A side listed in
    walls=None gets all four; pass a set to omit sides (the map's own wall
    does the job on that side).
    """
    h = size / 2.0
    outer = size + 2 * SHELL
    sides = walls if walls is not None else set("nsew")

    def put(tag, ox, oy, oz, ex, ey, ez):
        out.append({
            "name": "%s_%s" % (name, tag),
            "origin": [round(ox, 4), round(oy, 4), round(oz, 4)],
            "extents": [round(ex, 4), round(ey, 4), round(ez, 4)],
            "angles": [0.0, 0.0, 0.0],
            "material": MAT,
        })

    put("floor", centre[0], centre[1], z - SHELL / 2.0, outer, outer, SHELL)
    put("ceil", centre[0], centre[1], z + bore_h + SHELL / 2.0,
        outer, outer, SHELL)

    for side in sorted(sides):
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


def along(p, bearing, dist):
    r = math.radians(bearing)
    return (p[0] + math.cos(r) * dist, p[1] + math.sin(r) * dist)


def main(path):
    with open(path) as f:
        plan = json.load(f)
    boxes = plan["boxes"]

    before = len(boxes)
    boxes[:] = [b for b in boxes
                if not b["name"].startswith(PREFIX)
                and not b["name"].startswith("m_" + PREFIX)]
    if before != len(boxes):
        print("REBUILD: removed %d previous outputs" % (before - len(boxes)))

    made = []

    R_BIG = 652.95          # the square room that replaced the snaking bit
    BIG_CX, BIG_CY = -2513.525, 3393.625
    BIG_BORE = 347.10       # ceiling top lands on the wall top, 1280.30
    LANE_S, LANE_N = 3067.15, 3280.65   # flush with hex2_tun_e_wall_r0

    # ---------------------------------------------------------- upper
    nw = (-4938.92, 6913.91)
    sw = (-4938.92, 4900.00)
    rn = (-2466.75, 4900.00)   # outer east face lands on -2187.05
    BIG_ROOM = 759.00
    RN_SIZE = 506.00
    HUG_X = WALL_FACE - BORE_W / 2.0 - SHELL

    ext_face = nw[0] + BIG_ROOM / 2.0
    ext_end = along(UP_MOUTH, UP_BEAR,
                    (ext_face - UP_MOUTH[0]) / math.cos(math.radians(UP_BEAR)))
    i = seg(PREFIX + "up_ext", UP_MOUTH, ext_end, MOUTH_FLOOR, UP_MID,
            BORE_W, BORE_H, made)
    print("UPPER ext: to (%.2f, %.2f), %.2f -> %.2f, pitch %+.2f deg, "
          "full bore, no change at the mouth"
          % (ext_end[0], ext_end[1], MOUTH_FLOOR, UP_MID, i["pitch"]))

    room(PREFIX + "up_room_nw", nw, UP_MID, BORE_H, BIG_ROOM,
         {"e": (0.0, 380.00), "s": (0.0, BORE_W)}, made)
    i = seg(PREFIX + "up_link_s", (nw[0], nw[1] - BIG_ROOM / 2.0),
            (sw[0], sw[1] + BIG_ROOM / 2.0), UP_MID, UP_LEVEL,
            BORE_W, BORE_H, made)
    print("UPPER link south: x %.2f, %.2f -> %.2f, pitch %+.2f deg, len %.2f"
          % (nw[0], UP_MID, UP_LEVEL, i["pitch"], i["run"]))

    room(PREFIX + "up_room_sw", sw, UP_LEVEL, BORE_H, BIG_ROOM,
         {"n": (0.0, BORE_W), "e": (0.0, BORE_W)}, made)
    print("UPPER room_sw: %.2f square, tripled, entrances flush in its walls"
          % BIG_ROOM)

    i = seg(PREFIX + "up_link_e", (sw[0] + BIG_ROOM / 2.0, sw[1]),
            (rn[0] - RN_SIZE / 2.0, rn[1]), UP_LEVEL, UP_LEVEL,
            BORE_W, BORE_H, made)
    print("UPPER link east: LEVEL at %.2f, length %.2f" % (UP_LEVEL, i["run"]))

    room(PREFIX + "up_room_n", rn, UP_LEVEL, BORE_H, RN_SIZE,
         {"w": (0.0, BORE_W), "s": (HUG_X - rn[0], BORE_W)}, made)

    i = seg(PREFIX + "up_wall", (HUG_X, rn[1] - RN_SIZE / 2.0),
            (HUG_X, BIG_CY + R_BIG / 2.0), UP_LEVEL, UP_LEVEL,
            BORE_W, BORE_H, made)
    print("UPPER wall run: x %.2f, LEVEL at %.2f, length %.2f, clears the "
          "d553n voussoirs at 873.09 by %.2f"
          % (HUG_X, UP_LEVEL, i["run"], UP_LEVEL - SHELL - HEX2_TOP))

    # ---- the square room, built by hand: its east side is the map's own
    # wall, and one lane of its floor ramps down to the door sill.
    x0, x1 = BIG_CX - R_BIG / 2.0, BIG_CX + R_BIG / 2.0
    y0, y1 = BIG_CY - R_BIG / 2.0, BIG_CY + R_BIG / 2.0
    room(PREFIX + "up_big", (BIG_CX, BIG_CY), UP_LEVEL, BIG_BORE, R_BIG,
         {"n": (HUG_X - BIG_CX, BORE_W)}, made, walls={"n", "s", "w"})
    print("BIG ROOM: x %.2f..%.2f, y %.2f..%.2f, %.2f square, floor %.2f, "
          "ceiling top %.2f" % (x0, x1, y0, y1, R_BIG, UP_LEVEL,
                                UP_LEVEL + BIG_BORE + SHELL))
    # The ramp lane replaces the room floor over the door's width. Its bore
    # is kept low and the ramp stops short of the doorway, because a pitched
    # ceiling overshoots its floor by (bore + shell/2) * sin(pitch) and would
    # otherwise punch east into axis_739 at -2133.70.
    ly = (LANE_S + LANE_N) / 2.0
    LANE_BORE = 266.70
    LANE_END = -2300.00
    i = seg(PREFIX + "up_lane", (x0, ly), (LANE_END, ly),
            UP_LEVEL, UP_DOOR_SILL, LANE_N - LANE_S, LANE_BORE, made)
    over = (LANE_BORE + SHELL / 2.0) * math.sin(math.radians(abs(i["pitch"])))
    seg(PREFIX + "up_lane_flat", (LANE_END, ly), (UP_DOOR_FACE, ly),
        UP_DOOR_SILL, UP_DOOR_SILL, LANE_N - LANE_S, LANE_BORE, made)
    print("     ramp lane y %.2f..%.2f (south edge flush with "
          "hex2_tun_e_wall_r0 at 3067.15), %.2f -> %.2f, pitch %+.2f deg, "
          "ceiling overshoot %.2f reaching x %.2f, then level to the door"
          % (LANE_S, LANE_N, UP_LEVEL, UP_DOOR_SILL, i["pitch"], over,
             LANE_END + over))

    # ---------------------------------------------------------- lower
    lw = (-4299.61, 5064.45)
    ln = (-4299.61, LO_DOOR_Y)
    LO_SIZE = 506.00
    lo_face = lw[0] + LO_SIZE / 2.0
    lo_end = along(LO_MOUTH, LO_BEAR,
                   (lo_face - LO_MOUTH[0]) / math.cos(math.radians(LO_BEAR)))
    i = seg(PREFIX + "lo_ext", LO_MOUTH, lo_end, MOUTH_FLOOR, LO_MID,
            BORE_W, BORE_H, made)
    print("LOWER ext: to (%.2f, %.2f), %.2f -> %.2f, pitch %+.2f deg, "
          "full bore, no change at the mouth"
          % (lo_end[0], lo_end[1], MOUTH_FLOOR, LO_MID, i["pitch"]))
    room(PREFIX + "lo_room_w", lw, LO_MID, BORE_H, LO_SIZE,
         {"e": (0.0, 380.00), "n": (0.0, BORE_W)}, made)

    p0 = PINCH_Y - PINCH_LEN / 2.0
    p1 = PINCH_Y + PINCH_LEN / 2.0
    x = lw[0]
    seg(PREFIX + "lo_north_a", (x, lw[1] + LO_SIZE / 2.0),
        (x, p0 - TAPER_LEN), LO_MID, LO_MID, BORE_W, BORE_H, made)
    taper(PREFIX + "lo_taper_in", (x, p0 - TAPER_LEN), (x, p0), LO_MID,
          BORE_W, BORE_H, BORE_W, PINCH_H, made)
    seg(PREFIX + "lo_pinch", (x, p0), (x, p1), LO_MID, LO_MID,
        BORE_W, PINCH_H, made)
    taper(PREFIX + "lo_taper_out", (x, p1), (x, p1 + TAPER_LEN), LO_MID,
          BORE_W, PINCH_H, BORE_W, BORE_H, made)
    seg(PREFIX + "lo_north_b", (x, p1 + TAPER_LEN),
        (x, ln[1] - LO_SIZE / 2.0), LO_MID, LO_MID, BORE_W, BORE_H, made)
    print("LOWER north: flat at %.2f, full bore except a pinch to %.2f over "
          "y %.2f..%.2f, stepped in and out over %.2f"
          % (LO_MID, PINCH_H, p0, p1, TAPER_LEN))
    print("     pinched ceiling top %.2f vs upper floor bottom 567.50, "
          "clear by %.2f" % (LO_MID + PINCH_H + SHELL,
                             567.50 - (LO_MID + PINCH_H + SHELL)))
    room(PREFIX + "lo_room_n", ln, LO_MID, BORE_H, LO_SIZE,
         {"s": (0.0, BORE_W), "e": (0.0, BORE_W)}, made)
    i = seg(PREFIX + "lo_stub", (ln[0] + LO_SIZE / 2.0, ln[1]),
            (LO_DOOR_FACE, ln[1]), LO_DOOR_SILL, LO_DOOR_SILL,
            BORE_W, BORE_H, made)
    print("LOWER stub: to face %.2f, LEVEL at %.2f, length %.2f, full bore"
          % (LO_DOOR_FACE, LO_DOOR_SILL, i["run"]))

    twins = [mirror_box(b, "m_" + b["name"]) for b in made]
    boxes.extend(made)
    boxes.extend(twins)
    print("batch7.py: added %d half boxes + %d twins, %d boxes in plan"
          % (len(made), len(twins), len(boxes)))

    with open(path, "w") as f:
        json.dump(plan, f, indent=1)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_full.json")
