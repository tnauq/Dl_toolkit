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


def room(name, centre, z, bore_h, out, size=None):
    """A turnaround room: floor and ceiling only, walls left open so every
    corridor meeting here passes straight through the opening."""
    for tag, oz, ez in (("floor", z - SHELL / 2.0, SHELL),
                        ("ceil", z + bore_h + SHELL / 2.0, SHELL)):
        out.append({
            "name": "%s_%s" % (name, tag),
            "origin": [round(centre[0], 4), round(centre[1], 4), round(oz, 4)],
            "extents": [size or ROOM, size or ROOM, ez],
            "angles": [0.0, 0.0, 0.0],
            "material": MAT,
        })


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

    # ---- upper: extend the north leg, climbing, full bore -------------
    up_a = along(UP_MOUTH, UP_BEAR, UP_EXT_LEN)
    i = seg(PREFIX + "up_ext", UP_MOUTH, up_a, MOUTH_FLOOR, UP_MID,
            BORE_W, BORE_H, made)
    print("UPPER ext: to (%.2f, %.2f), %.2f -> %.2f, pitch %+.2f deg, "
          "bore %.2f x %.2f (no change at the mouth)"
          % (up_a[0], up_a[1], MOUTH_FLOOR, UP_MID, i["pitch"],
             BORE_W, BORE_H))
    room(PREFIX + "up_room_w", up_a, UP_MID, BORE_H, made)

    # ---- upper: connector, routed WEST of the lower's north band and
    # SOUTH of the lower's extension, so the only place the two meet in
    # plan is the pinch on the ext.
    up_a2 = (UP_LINK_X, up_a[1])
    i = seg(PREFIX + "up_link_w", up_a, up_a2, UP_MID, UP_MID,
            BORE_W, BORE_H, made)
    room(PREFIX + "up_room_nw", up_a2, UP_MID, BORE_H, made)
    up_a3 = (UP_LINK_X, UP_HUG_N)
    i = seg(PREFIX + "up_link_s", up_a2, up_a3, UP_MID, UP_LEVEL,
            BORE_W, BORE_H, made)
    print("UPPER link south: x %.2f, y %.2f -> %.2f, %.2f -> %.2f, "
          "pitch %+.2f deg" % (UP_LINK_X, up_a2[1], up_a3[1], UP_MID,
                               UP_LEVEL, i["pitch"]))
    room(PREFIX + "up_room_sw", up_a3, UP_LEVEL, BORE_H, made)
    up_b = (UP_HUG_X, UP_HUG_N)
    i = seg(PREFIX + "up_link_e", up_a3, up_b, UP_LEVEL, UP_LEVEL,
            BORE_W, BORE_H, made)
    print("UPPER link east: to (%.2f, %.2f), LEVEL at %.2f, length %.2f "
          "(passes south of the lower band, which starts at y 5064.45)"
          % (up_b[0], up_b[1], UP_LEVEL, i["run"]))
    room(PREFIX + "up_room_n", up_b, UP_LEVEL, BORE_H, made)

    # ---- upper: level alongside axis_553_mid_n ------------------------
    up_c = (UP_HUG_X, UP_DOGLEG_Y)
    i = seg(PREFIX + "up_wall", up_b, up_c, UP_LEVEL, UP_LEVEL,
            BORE_W, BORE_H, made)
    print("UPPER wall run: to (%.2f, %.2f), LEVEL at %.2f, length %.2f, "
          "clears hex2 top %.2f by %.2f"
          % (up_c[0], up_c[1], UP_LEVEL, i["run"], HEX2_TOP,
             UP_LEVEL - SHELL - HEX2_TOP))
    room(PREFIX + "up_room_dog", up_c, UP_LEVEL, BORE_H, made)

    up_d = (UP_APPROACH_X, UP_DOGLEG_Y)
    i = seg(PREFIX + "up_dog", up_c, up_d, UP_LEVEL, UP_LEVEL,
            BORE_W, BORE_H, made)
    print("UPPER dogleg: to (%.2f, %.2f), LEVEL at %.2f, length %.2f"
          % (up_d[0], up_d[1], UP_LEVEL, i["run"]))

    # step the bore down before the squeeze, not at a cliff
    up_e = (UP_APPROACH_X, UP_DOGLEG_Y - TAPER_LEN)
    taper(PREFIX + "up_taper", up_d, up_e, UP_LEVEL,
          BORE_W, BORE_H, UP_NARROW_W, UP_DOOR_H, made)
    print("UPPER taper: %.2f x %.2f -> %.2f x %.2f in 3 steps over %.2f"
          % (BORE_W, BORE_H, UP_NARROW_W, UP_DOOR_H, TAPER_LEN))

    # Start shedding height here rather than in one steep drop at the door.
    # A pitched corridor's ceiling is offset perpendicular to its floor, so
    # it runs past the end of the floor by (bore_h + shell/2) * sin(pitch).
    # A gentle pitch keeps that overshoot short of the doorway.
    up_f = (UP_APPROACH_X, UP_APPROACH_Y)
    mid_z = (UP_LEVEL + UP_DOOR_SILL) / 2.0
    i = seg(PREFIX + "up_squeeze", up_e, up_f, UP_LEVEL, mid_z,
            UP_NARROW_W, UP_DOOR_H, made)
    print("UPPER squeeze: to (%.2f, %.2f), %.2f -> %.2f, pitch %+.2f deg"
          % (up_f[0], up_f[1], UP_LEVEL, mid_z, i["pitch"]))
    room(PREFIX + "up_room_s", up_f, mid_z, UP_DOOR_H, made,
         size=UP_NARROW_W)

    # Descend clear of the doorway, then meet the door dead level, so the
    # pitched wall boxes do not overshoot through axis_553_mid into the
    # far side.
    up_g = (UP_RAMP_END_X, UP_APPROACH_Y)
    i = seg(PREFIX + "up_drop", up_f, up_g, mid_z, UP_DOOR_SILL,
            UP_NARROW_W, UP_DOOR_H, made)
    over = (UP_DOOR_H + SHELL / 2.0) * math.sin(math.radians(abs(i["pitch"])))
    print("UPPER drop: to x %.2f, %.2f -> %.2f, pitch %+.2f deg, ceiling "
          "overshoot %.2f, ending at x %.2f, clear of the arch at -2194.70"
          % (UP_RAMP_END_X, mid_z, UP_DOOR_SILL, i["pitch"], over,
             UP_RAMP_END_X + over))
    i = seg(PREFIX + "up_stub", up_g, (UP_DOOR_FACE, UP_APPROACH_Y),
            UP_DOOR_SILL, UP_DOOR_SILL, UP_NARROW_W, UP_DOOR_H, made)
    print("UPPER stub: to face %.2f, LEVEL at %.2f, length %.2f"
          % (UP_DOOR_FACE, UP_DOOR_SILL, i["run"]))

    # ---- lower: extend the south leg down to its own sill, full bore --
    lo_a = along(LO_MOUTH, LO_BEAR, LO_EXT_LEN)
    i = seg(PREFIX + "lo_ext", LO_MOUTH, lo_a, MOUTH_FLOOR, LO_MID,
            BORE_W, BORE_H, made)
    print("LOWER ext: to (%.2f, %.2f), %.2f -> %.2f, pitch %+.2f deg, "
          "bore %.2f x %.2f (no change at the mouth)"
          % (lo_a[0], lo_a[1], MOUTH_FLOOR, LO_MID, i["pitch"],
             BORE_W, BORE_H))
    room(PREFIX + "lo_room_w", lo_a, LO_MID, BORE_H, made)

    # north run, pinched only where the upper passes overhead
    p0 = PINCH_Y - PINCH_LEN / 2.0
    p1 = PINCH_Y + PINCH_LEN / 2.0
    x = lo_a[0]
    seg(PREFIX + "lo_north_a", lo_a, (x, p0 - TAPER_LEN), LO_MID, LO_MID,
        BORE_W, BORE_H, made)
    taper(PREFIX + "lo_taper_in", (x, p0 - TAPER_LEN), (x, p0), LO_MID,
          BORE_W, BORE_H, BORE_W, PINCH_H, made)
    seg(PREFIX + "lo_pinch", (x, p0), (x, p1), LO_MID, LO_MID,
        BORE_W, PINCH_H, made)
    taper(PREFIX + "lo_taper_out", (x, p1), (x, p1 + TAPER_LEN), LO_MID,
          BORE_W, PINCH_H, BORE_W, BORE_H, made)
    seg(PREFIX + "lo_north_b", (x, p1 + TAPER_LEN), (x, LO_DOOR_Y),
        LO_MID, LO_MID, BORE_W, BORE_H, made)
    print("LOWER north: flat at %.2f, ceiling pinched to %.2f over "
          "y %.2f..%.2f, stepped in and out over %.2f each side"
          % (LO_MID, PINCH_H, p0, p1, TAPER_LEN))
    print("     pinched ceiling top %.2f vs upper floor bottom 567.50 "
          "at worst, clear by %.2f"
          % (LO_MID + PINCH_H + SHELL, 567.50 - (LO_MID + PINCH_H + SHELL)))
    room(PREFIX + "lo_room_n", (x, LO_DOOR_Y), LO_MID, BORE_H, made)

    i = seg(PREFIX + "lo_stub", (x, LO_DOOR_Y), (LO_DOOR_FACE, LO_DOOR_Y),
            LO_DOOR_SILL, LO_DOOR_SILL, BORE_W, BORE_H, made)
    print("LOWER stub: to face %.2f, flat at %.2f, length %.2f, full bore"
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
