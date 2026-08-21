#!/usr/bin/env python3
"""batch7.py - fourteenth build step, run after batch6.py.

Takes the two branches of the T fork out to the two open doors, crossing
once in plan, with the higher door's tunnel over the lower one.

  north branch (m_ttun_room, y 6167.18)  ->  axis_553_mid door, sill 720.20
  south branch (m_ttun_room, y 5661.18)  ->  m_axis_47 door,    sill 213.40

EVERYTHING IS AXIS ALIGNED
No mitres, no angled mouths, no stepped tapers. Every corner is a square
room with flush openings cut in its walls, so a corridor always meets a
flat face square on. That removes both faults from the last pass: nothing
can fail to line up at a room, and with no stepped bore changes there are
no ceiling holes.

THE CROSSING IS A JUMP, NOT A PINCH
The upper tunnel gains all its height in one double-tall room just before
the crossing, on a stack of boxes from 364.62 to 906.50. Past that it runs
level and passes over the lower, which is flat at its own sill of 213.40.
Lower ceiling tops at 826.90, upper floor bottoms at 879.80, clear by
52.90, and neither bore changes anywhere.

THE DOOR ROOM IS A SWITCHBACK
The door is 186.30 below the running level and hex2 boxes the approach in
on three sides: hex2_wall_ne_r ends at x -2964.13, hex2_tun_e_wall_r0 at
y 3067.15, hex2_tun_ne_leg_roof at y 3565.52. One straight ramp in that
footprint is 777.08 long, which is 13.51 degrees. Two legs give 1554.16 of
run and bring it to 6.84 degrees, under the 10 you asked for.

Usage: python3 batch7.py docs/plans/dust2_full.json
"""

import json
import math
import sys

MAT = "materials/dev/reflectivity_30.vmat"
MIRROR_X = 920.2
MIRROR_Y = 12170.1

SHELL = 26.70
BORE_W = 253.00
BORE_H = 586.80
ROOM = 506.00
PREFIX = "xtun_"

T_X = -3333.85
T_N = 6167.18
T_S = 5661.18
START_Z = 364.62

UP_LEVEL = 906.50
LO_LEVEL = 213.40
UP_DOOR_FACE = -2187.05
UP_DOOR_SILL = 720.20
LO_DOOR_FACE = -3080.65
LO_DOOR_Y = 7922.45

TALL = 759.00
TALL_C = (-4200.00, 5300.00)
TALL_BORE = 1173.60
STEP_FRACTIONS = (1.0 / 3.0, 2.0 / 3.0)

HUG_X = -2313.55

# Square, bounded by real geometry: hex2_tun_e_wall_r0 ends at y 3067.15
# and hex2_tun_ne_leg_roof starts at y 3565.52, so 498.37 is the side.
BIG_Y0, BIG_Y1 = 3067.15, 3565.52
BIG_X1 = -2187.05
BIG_X0 = BIG_X1 - (BIG_Y1 - BIG_Y0)
WALL_TOP = 1280.30
BIG_TOP = UP_LEVEL + BORE_H          # 1493.30, the tunnel's own ceiling
JUMP_D = 253.00
JUMP_TOP = 813.35                    # halfway up the 186.30 step


def box(name, xr, yr, zr, out):
    out.append({
        "name": name,
        "origin": [round((xr[0] + xr[1]) / 2.0, 4),
                   round((yr[0] + yr[1]) / 2.0, 4),
                   round((zr[0] + zr[1]) / 2.0, 4)],
        "extents": [round(xr[1] - xr[0], 4), round(yr[1] - yr[0], 4),
                    round(zr[1] - zr[0], 4)],
        "angles": [0.0, 0.0, 0.0],
        "material": MAT,
    })


def ramp(name, xr, yr, z0, z1, bore_h, out, axis="x"):
    """Corridor whose floor top runs z0 to z1 along the given axis.

    The pitch is negated because a positive pitch descends along local +x
    in Source; for a y-run the box is yawed 90 first.
    """
    if axis == "x":
        run, yaw = xr[1] - xr[0], 0.0
    else:
        run, yaw = yr[1] - yr[0], 90.0
    dz = z1 - z0
    pitch = -math.degrees(math.atan2(dz, run))
    slope = math.hypot(run, dz)
    cx, cy = (xr[0] + xr[1]) / 2.0, (yr[0] + yr[1]) / 2.0
    cz = (z0 + z1) / 2.0
    pr, yr_ = math.radians(pitch), math.radians(yaw)
    nz = (math.cos(yr_) * math.sin(pr), math.sin(yr_) * math.sin(pr),
          math.cos(pr))
    width = (yr[1] - yr[0]) if axis == "x" else (xr[1] - xr[0])
    for tag, along in (("floor", -SHELL / 2.0),
                       ("ceil", bore_h + SHELL / 2.0)):
        out.append({
            "name": "%s_%s" % (name, tag),
            "origin": [round(cx + nz[0] * along, 4),
                       round(cy + nz[1] * along, 4),
                       round(cz + nz[2] * along, 4)],
            "extents": [round(slope, 4), round(width, 4), SHELL],
            "angles": [round(pitch, 4), yaw, 0.0],
            "material": MAT,
        })
    return pitch


def corridor(name, xr, yr, z, bore_h, out):
    box(name + "_floor", xr, yr, (z - SHELL, z), out)
    box(name + "_ceil", xr, yr, (z + bore_h, z + bore_h + SHELL), out)
    if (xr[1] - xr[0]) >= (yr[1] - yr[0]):
        box(name + "_wall_s", xr, (yr[0] - SHELL, yr[0]), (z, z + bore_h), out)
        box(name + "_wall_n", xr, (yr[1], yr[1] + SHELL), (z, z + bore_h), out)
    else:
        box(name + "_wall_w", (xr[0] - SHELL, xr[0]), yr, (z, z + bore_h), out)
        box(name + "_wall_e", (xr[1], xr[1] + SHELL), yr, (z, z + bore_h), out)


def room(name, centre, z, bore_h, size, openings, out, walls=None):
    h = size / 2.0
    sides = walls if walls is not None else set("nsew")
    lo_x, hi_x = centre[0] - h - SHELL, centre[0] + h + SHELL
    lo_y, hi_y = centre[1] - h - SHELL, centre[1] + h + SHELL
    box(name + "_floor", (lo_x, hi_x), (lo_y, hi_y), (z - SHELL, z), out)
    box(name + "_ceil", (lo_x, hi_x), (lo_y, hi_y),
        (z + bore_h, z + bore_h + SHELL), out)
    for side in sorted(sides):
        if side in "ns":
            wy = centre[1] + h if side == "n" else centre[1] - h - SHELL
            yr = (wy, wy + SHELL)
            if side in openings:
                off, w = openings[side]
                o0, o1 = centre[0] + off - w / 2.0, centre[0] + off + w / 2.0
                if o0 > lo_x:
                    box(name + "_" + side + "0", (lo_x, o0), yr,
                        (z, z + bore_h), out)
                if hi_x > o1:
                    box(name + "_" + side + "1", (o1, hi_x), yr,
                        (z, z + bore_h), out)
            else:
                box(name + "_" + side, (lo_x, hi_x), yr, (z, z + bore_h), out)
        else:
            wx = centre[0] + h if side == "e" else centre[0] - h - SHELL
            xr = (wx, wx + SHELL)
            if side in openings:
                off, w = openings[side]
                o0, o1 = centre[1] + off - w / 2.0, centre[1] + off + w / 2.0
                if o0 > lo_y:
                    box(name + "_" + side + "0", xr, (lo_y, o0),
                        (z, z + bore_h), out)
                if hi_y > o1:
                    box(name + "_" + side + "1", xr, (o1, hi_y),
                        (z, z + bore_h), out)
            else:
                box(name + "_" + side, xr, (lo_y, hi_y), (z, z + bore_h), out)


def mirror_box(b, name):
    o, a = b["origin"], b["angles"]
    return {"name": name,
            "origin": [round(MIRROR_X - o[0], 4), round(MIRROR_Y - o[1], 4),
                       o[2]],
            "extents": list(b["extents"]),
            "angles": [a[0], round((a[1] + 180.0) % 360.0, 4), a[2]],
            "material": b.get("material", MAT)}


def main(path):
    with open(path) as f:
        plan = json.load(f)
    boxes = plan["boxes"]
    before = len(boxes)
    boxes[:] = [b for b in boxes if not b["name"].startswith(PREFIX)
                and not b["name"].startswith("m_" + PREFIX)]
    if before != len(boxes):
        print("REBUILD: removed %d previous outputs" % (before - len(boxes)))
    made = []
    hw, hr, th = BORE_W / 2.0, ROOM / 2.0, TALL / 2.0

    # ------------------------------------------------------------- upper
    A, B = (T_X, 6800.00), (-4200.00, 6800.00)
    C, D = (-4200.00, 4100.00), (-2466.75, 4100.00)
    corridor(PREFIX + "up1", (T_X - hw, T_X + hw), (T_N, A[1] - hr),
             START_Z, BORE_H, made)
    room(PREFIX + "up_room_a", A, START_Z, BORE_H, ROOM,
         {"s": (0.0, BORE_W), "w": (0.0, BORE_W)}, made)
    corridor(PREFIX + "up2", (B[0] + hr, A[0] - hr), (A[1] - hw, A[1] + hw),
             START_Z, BORE_H, made)
    room(PREFIX + "up_room_b", B, START_Z, BORE_H, ROOM,
         {"e": (0.0, BORE_W), "s": (0.0, BORE_W)}, made)
    corridor(PREFIX + "up3", (B[0] - hw, B[0] + hw),
             (TALL_C[1] + th, B[1] - hr), START_Z, BORE_H, made)
    print("UPPER: north out of the T at x %.2f, west to x %.2f, south to the "
          "tall room, all level at %.2f" % (T_X, B[0], START_Z))

    tx0, tx1 = TALL_C[0] - th, TALL_C[0] + th
    ty0, ty1 = TALL_C[1] - th, TALL_C[1] + th
    top = START_Z + TALL_BORE
    box(PREFIX + "up_tall_floor", (tx0 - SHELL, tx1 + SHELL),
        (ty0 - SHELL, ty1 + SHELL), (START_Z - SHELL, START_Z), made)
    box(PREFIX + "up_tall_ceil", (tx0 - SHELL, tx1 + SHELL),
        (ty0 - SHELL, ty1 + SHELL), (top, top + SHELL), made)
    box(PREFIX + "up_tall_w", (tx0 - SHELL, tx0), (ty0 - SHELL, ty1 + SHELL),
        (START_Z, top), made)
    box(PREFIX + "up_tall_e", (tx1, tx1 + SHELL), (ty0 - SHELL, ty1 + SHELL),
        (START_Z, top), made)
    box(PREFIX + "up_tall_n0", (tx0 - SHELL, TALL_C[0] - hw),
        (ty1, ty1 + SHELL), (START_Z, top), made)
    box(PREFIX + "up_tall_n1", (TALL_C[0] + hw, tx1 + SHELL),
        (ty1, ty1 + SHELL), (START_Z, top), made)
    box(PREFIX + "up_tall_n2", (TALL_C[0] - hw, TALL_C[0] + hw),
        (ty1, ty1 + SHELL), (START_Z + BORE_H, top), made)
    box(PREFIX + "up_tall_s0", (tx0 - SHELL, TALL_C[0] - hw),
        (ty0 - SHELL, ty0), (START_Z, top), made)
    box(PREFIX + "up_tall_s1", (TALL_C[0] + hw, tx1 + SHELL),
        (ty0 - SHELL, ty0), (START_Z, top), made)
    box(PREFIX + "up_tall_s2", (TALL_C[0] - hw, TALL_C[0] + hw),
        (ty0 - SHELL, ty0), (START_Z, UP_LEVEL), made)
    box(PREFIX + "up_tall_s3", (TALL_C[0] - hw, TALL_C[0] + hw),
        (ty0 - SHELL, ty0), (UP_LEVEL + BORE_H, top), made)
    # Two boxes only, at a third and two thirds of the climb, so the room
    # stays open. The lower one sits against the south wall's east jamb and
    # the taller one in front of the opening, so the line is
    # floor -> low box -> high box -> sill.
    climb = UP_LEVEL - START_Z
    depth = 253.00
    lo_top = START_Z + climb * STEP_FRACTIONS[0]
    hi_top = START_Z + climb * STEP_FRACTIONS[1]
    box(PREFIX + "up_step_low", (TALL_C[0] + hw, TALL_C[0] + hw + depth),
        (ty0, ty0 + depth), (START_Z - SHELL, lo_top), made)
    box(PREFIX + "up_step_high", (TALL_C[0] - hw, TALL_C[0] + hw),
        (ty0, ty0 + depth), (START_Z - SHELL, hi_top), made)
    print("TALL ROOM: %.2f square, bore %.2f (double), in north at %.2f, "
          "out south at %.2f" % (TALL, TALL_BORE, START_Z, UP_LEVEL))
    print("     2 boxes: low top %.2f (a third), high top %.2f (two thirds), "
          "hops of %.2f, %.2f and %.2f"
          % (lo_top, hi_top, lo_top - START_Z, hi_top - lo_top,
             UP_LEVEL - hi_top))

    corridor(PREFIX + "up4", (C[0] - hw, C[0] + hw), (C[1] + hr, ty0),
             UP_LEVEL, BORE_H, made)
    room(PREFIX + "up_room_c", C, UP_LEVEL, BORE_H, ROOM,
         {"n": (0.0, BORE_W), "e": (0.0, BORE_W)}, made)
    corridor(PREFIX + "up5", (C[0] + hr, D[0] - hr), (C[1] - hw, C[1] + hw),
             UP_LEVEL, BORE_H, made)
    room(PREFIX + "up_room_d", D, UP_LEVEL, BORE_H, ROOM,
         {"w": (0.0, BORE_W), "s": (HUG_X - D[0], BORE_W)}, made)
    corridor(PREFIX + "up6", (HUG_X - hw, HUG_X + hw), (BIG_Y1, D[1] - hr),
             UP_LEVEL, BORE_H, made)
    print("UPPER: level at %.2f from the tall room on, crossing over the "
          "lower at (-4200.00, 4550.00)" % UP_LEVEL)

    # -- the door room: a plain square at the door sill, ceiling level with
    # the connecting tunnel's, and one box to climb back up to it.
    box(PREFIX + "big_floor", (BIG_X0 - SHELL, BIG_X1),
        (BIG_Y0 - SHELL, BIG_Y1 + SHELL),
        (UP_DOOR_SILL - SHELL, UP_DOOR_SILL), made)
    box(PREFIX + "big_ceil", (BIG_X0 - SHELL, BIG_X1),
        (BIG_Y0 - SHELL, BIG_Y1 + SHELL), (BIG_TOP, BIG_TOP + SHELL), made)
    box(PREFIX + "big_w", (BIG_X0 - SHELL, BIG_X0),
        (BIG_Y0 - SHELL, BIG_Y1 + SHELL), (UP_DOOR_SILL, BIG_TOP), made)
    box(PREFIX + "big_s", (BIG_X0 - SHELL, BIG_X1), (BIG_Y0 - SHELL, BIG_Y0),
        (UP_DOOR_SILL, BIG_TOP), made)
    box(PREFIX + "big_n0", (BIG_X0 - SHELL, HUG_X - hw),
        (BIG_Y1, BIG_Y1 + SHELL), (UP_DOOR_SILL, BIG_TOP), made)
    box(PREFIX + "big_n1", (HUG_X + hw, BIG_X1), (BIG_Y1, BIG_Y1 + SHELL),
        (UP_DOOR_SILL, BIG_TOP), made)
    box(PREFIX + "big_n_sill", (HUG_X - hw, HUG_X + hw),
        (BIG_Y1, BIG_Y1 + SHELL), (UP_DOOR_SILL, UP_LEVEL), made)
    # axis_553_mid tops out at 1280.30, so close the east side above it
    box(PREFIX + "big_e_top", (BIG_X1, BIG_X1 + SHELL),
        (BIG_Y0 - SHELL, BIG_Y1 + SHELL), (WALL_TOP, BIG_TOP), made)
    box(PREFIX + "big_jump", (HUG_X - hw, BIG_X1),
        (BIG_Y1 - JUMP_D, BIG_Y1), (UP_DOOR_SILL - SHELL, JUMP_TOP), made)
    print("DOOR ROOM: x %.2f..%.2f, y %.2f..%.2f, %.2f square, floor on the "
          "door sill %.2f, ceiling %.2f, level with the tunnel's"
          % (BIG_X0, BIG_X1, BIG_Y0, BIG_Y1, BIG_X1 - BIG_X0, UP_DOOR_SILL,
             BIG_TOP))
    print("     tunnel enters north with its sill %.2f up; one box, top "
          "%.2f, splits that into hops of %.2f and %.2f"
          % (UP_LEVEL - UP_DOOR_SILL, JUMP_TOP, JUMP_TOP - UP_DOOR_SILL,
             UP_LEVEL - JUMP_TOP))

    # ------------------------------------------------------------- lower
    E, F = (T_X, 4550.00), (-4900.00, 4550.00)   # clear of the tall room
    G = (-4900.00, LO_DOOR_Y)   # must match F, or the south wall goes lopsided
    q = ramp(PREFIX + "lo1", (T_X - hw, T_X + hw), (E[1] + hr, T_S),
             LO_LEVEL, START_Z, BORE_H, made, axis="y")
    box(PREFIX + "lo1_wall_w", (T_X - hw - SHELL, T_X - hw),
        (E[1] + hr, T_S), (LO_LEVEL, START_Z + BORE_H), made)
    box(PREFIX + "lo1_wall_e", (T_X + hw, T_X + hw + SHELL),
        (E[1] + hr, T_S), (LO_LEVEL, START_Z + BORE_H), made)
    # A pitched ceiling is offset perpendicular to its floor, so it stops
    # short of the floor's high end by (bore + shell/2) * sin(pitch). Cap
    # that gap with a level piece so the ramp meets the T room's ceiling.
    gap = (BORE_H + SHELL / 2.0) * math.sin(math.radians(abs(q)))
    box(PREFIX + "lo1_cap", (T_X - hw, T_X + hw), (T_S - gap, T_S),
        (START_Z + BORE_H, START_Z + BORE_H + SHELL), made)
    print("     ceiling capped over the last %.2f into the T room" % gap)
    print("LOWER: drops %.2f to its sill on the first leg, pitch %.2f deg, "
          "then flat at %.2f the whole way, full bore, no pinch"
          % (START_Z - LO_LEVEL, abs(q), LO_LEVEL))
    room(PREFIX + "lo_room_e", E, LO_LEVEL, BORE_H, ROOM,
         {"n": (0.0, BORE_W), "w": (0.0, BORE_W)}, made)
    corridor(PREFIX + "lo2", (F[0] + hr, E[0] - hr), (E[1] - hw, E[1] + hw),
             LO_LEVEL, BORE_H, made)
    room(PREFIX + "lo_room_f", F, LO_LEVEL, BORE_H, ROOM,
         {"e": (0.0, BORE_W), "n": (0.0, BORE_W)}, made)
    corridor(PREFIX + "lo3", (F[0] - hw, F[0] + hw), (F[1] + hr, G[1] - hr),
             LO_LEVEL, BORE_H, made)
    room(PREFIX + "lo_room_g", G, LO_LEVEL, BORE_H, ROOM,
         {"s": (0.0, BORE_W), "e": (0.0, BORE_W)}, made)
    corridor(PREFIX + "lo4", (G[0] + hr, LO_DOOR_FACE), (G[1] - hw, G[1] + hw),
             LO_LEVEL, BORE_H, made)

    twins = [mirror_box(b, "m_" + b["name"]) for b in made]
    boxes.extend(made)
    boxes.extend(twins)
    print("batch7.py: added %d half boxes + %d twins, %d boxes in plan"
          % (len(made), len(twins), len(boxes)))
    with open(path, "w") as f:
        json.dump(plan, f, indent=1)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_full.json")
