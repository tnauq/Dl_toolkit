#!/usr/bin/env python3
"""batch7.py - thirteenth build step, run after batch6.py.

Carries the two V leg mouths out to the two open doors, crossing once in
plan so the pair reads as an X from above, with the higher door's tunnel
riding over the lower one.

ASSIGNMENT
  north mouth (m_vtun_leg_s, y 6163.91)  ->  axis_553_mid door, sill 720.20
  south mouth (m_vtun_leg_n, y 5664.45)  ->  m_axis_47 door,    sill 213.40
Each mouth is served by the door on the opposite side, so the two paths
must swap sides. That swap is the crossing.

HOW THE VERTICAL SEPARATION IS WON
Both mouths sit at floor 364.62, and a bore plus two shells needs 640.20
of floor-to-floor clearance, so neither tunnel can cross the other where
they start. Each leg is therefore extended 1200 further along the bearing
it already has, ramping in opposite directions by 320.10 each: the upper
to 684.72, the lower to 44.52. At the crossing the lower's ceiling tops
out at 658.02 and the upper's floor starts at 658.02, flush, no overlap.
Splitting the change between the two halves the grade each has to climb.

The remaining height to each sill is picked up late, well past the
crossing, where there is length to do it gently.

The last stub into axis_553_mid steps down to that door's 238.93 x 554.16,
since that opening was itself shrunk to fit its corner. It is a step at
the landing rather than a taper, which boxes cannot do.

Every box is made on the half side and the m_ twin derived by the plan
transform (x' = 920.2 - x, y' = 12170.1 - y, yaw' = yaw + 180). Name-keyed
and rerunnable.

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
# The lower drops straight to its own door sill and then stays flat, so
# there is no second ramp anywhere the upper has to clear. The upper then
# only has to clear the TALLEST thing the lower ever presents, which is the
# top of the lower's own ramp at its mouth: 364.62 + 266.70 + 26.70 = 658.02.
UP_EXT_LEN = 1500.0
LO_EXT_LEN = 1200.0
UP_MID = 684.72            # floor bottom 658.02, flush with that worst case
LO_MID = 213.40            # m_axis_47 sill, reached on the ext and held

# axis_553_mid door: wall x -2187.05..-2133.75, opening y 3041.72..3280.65
UP_DOOR_FACE = -2187.05
UP_DOOR_Y = 3161.185
UP_DOOR_SILL = 720.20
UP_DOOR_W = 238.93
UP_DOOR_H = 554.16
UP_LANDING_X = -2600.0
ROOM = 400.05              # turnaround rooms, 15 grid units square

# m_axis_47 door: wall x -3080.65..-3053.95, opening y 7795.95..8048.95
LO_DOOR_FACE = -3080.65
LO_DOOR_Y = 7922.45
LO_DOOR_SILL = 213.40
LO_DOOR_W = 253.00
LO_DOOR_H = 586.80

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


def room(name, centre, z, bore_h, out):
    """A turnaround room: floor and ceiling only, walls left open so every
    corridor meeting here passes straight through the opening."""
    for tag, oz, ez in (("floor", z - SHELL / 2.0, SHELL),
                        ("ceil", z + bore_h + SHELL / 2.0, SHELL)):
        out.append({
            "name": "%s_%s" % (name, tag),
            "origin": [round(centre[0], 4), round(centre[1], 4), round(oz, 4)],
            "extents": [ROOM, ROOM, ez],
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

    # ---- upper: extend the north leg, climbing ------------------------
    up_a = along(UP_MOUTH, UP_BEAR, UP_EXT_LEN)
    i = seg(PREFIX + "up_ext", UP_MOUTH, up_a, MOUTH_FLOOR, UP_MID,
            BORE_W, BORE_H, made)
    print("UPPER ext: to (%.2f, %.2f), floor %.2f -> %.2f, pitch %+.2f deg"
          % (up_a[0], up_a[1], MOUTH_FLOOR, UP_MID, i["pitch"]))

    # ---- lower: extend the south leg, dropping to its own sill --------
    lo_a = along(LO_MOUTH, LO_BEAR, LO_EXT_LEN)
    i = seg(PREFIX + "lo_ext", LO_MOUTH, lo_a, MOUTH_FLOOR, LO_MID,
            BORE_W, BORE_H, made)
    print("LOWER ext: to (%.2f, %.2f), floor %.2f -> %.2f, pitch %+.2f deg"
          % (lo_a[0], lo_a[1], MOUTH_FLOOR, LO_MID, i["pitch"]))

    room(PREFIX + "up_room_w", up_a, UP_MID, BORE_H, made)
    room(PREFIX + "lo_room_w", lo_a, LO_MID, BORE_H, made)

    # ---- upper: east along the top, then south ------------------------
    up_b = (UP_LANDING_X, up_a[1])
    i = seg(PREFIX + "up_east", up_a, up_b, UP_MID, UP_MID,
            BORE_W, BORE_H, made)
    print("UPPER east: to (%.2f, %.2f), flat at %.2f, length %.2f"
          % (up_b[0], up_b[1], UP_MID, i["run"]))
    room(PREFIX + "up_room_n", up_b, UP_MID, BORE_H, made)

    up_c = (UP_LANDING_X, UP_DOOR_Y)
    i = seg(PREFIX + "up_south", up_b, up_c, UP_MID, UP_MID,
            BORE_W, BORE_H, made)
    print("UPPER south: to (%.2f, %.2f), flat at %.2f, length %.2f"
          % (up_c[0], up_c[1], UP_MID, i["run"]))
    room(PREFIX + "up_room_s", up_c, UP_MID, BORE_H, made)

    i = seg(PREFIX + "up_stub", up_c, (UP_DOOR_FACE, UP_DOOR_Y),
            UP_MID, UP_DOOR_SILL, UP_DOOR_W, UP_DOOR_H, made)
    print("UPPER stub: to face %.2f, floor %.2f -> %.2f, pitch %+.2f deg, "
          "bore stepped up to %.2f x %.2f"
          % (UP_DOOR_FACE, UP_MID, UP_DOOR_SILL, i["pitch"],
             UP_DOOR_W, UP_DOOR_H))

    # ---- lower: north along a fixed band, then east into its door -----
    lo_b = (lo_a[0], LO_DOOR_Y)
    i = seg(PREFIX + "lo_north", lo_a, lo_b, LO_MID, LO_MID,
            BORE_W, BORE_H, made)
    print("LOWER north: to (%.2f, %.2f), flat at %.2f, length %.2f"
          % (lo_b[0], lo_b[1], LO_MID, i["run"]))
    room(PREFIX + "lo_room_n", lo_b, LO_MID, BORE_H, made)

    i = seg(PREFIX + "lo_stub", lo_b, (LO_DOOR_FACE, LO_DOOR_Y),
            LO_DOOR_SILL, LO_DOOR_SILL, LO_DOOR_W, LO_DOOR_H, made)
    print("LOWER stub: to face %.2f, flat at %.2f, length %.2f, "
          "bore stepped up to %.2f x %.2f"
          % (LO_DOOR_FACE, LO_DOOR_SILL, i["run"], LO_DOOR_W, LO_DOOR_H))

    twins = [mirror_box(b, "m_" + b["name"]) for b in made]
    boxes.extend(made)
    boxes.extend(twins)
    print("batch7.py: added %d half boxes + %d twins, %d boxes in plan"
          % (len(made), len(twins), len(boxes)))

    with open(path, "w") as f:
        json.dump(plan, f, indent=1)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_full.json")
