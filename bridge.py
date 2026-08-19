#!/usr/bin/env python3
"""Build the S bridge joining the upper room to its mirror counterpart.

Runs on docs/plans/dust2_full.json, AFTER mirror.py and stitch.py:

    python3 mirror.py docs/plans/dust2_half.json
    python3 stitch.py docs/plans/dust2_full.json
    python3 bridge.py docs/plans/dust2_full.json

THE ROOM, measured not assumed
------------------------------
The space the three crosshairs sit in is bounded by:
    floor    merged_84        top 666.85
    ceiling  ceiling_80_68    underside 1253.70
    west     merged_97 / gapfill_80_61      x 640.15..666.95
    east     axis_68 / axis_68_upper        x 1466.95..1493.65
So the interior is 800.0 wide and 586.85 tall, and it ended at y 5067.7,
where axis_61 used to cap it.  axis_61 is gone, so the room is open there.

Window pattern, from axis_102/104/106 and axis_68_sill1/2/3:
    opening 53.3 long, z 720.15..880.20 (160.05 tall)
    sill    z 640.15..720.15
    header  z 880.20..1280.30
Existing openings start at y 4187.55, 4454.25, 4747.65, so the pitch is
NOT uniform: 266.7 then 293.4.  The bridge uses the tighter 266.7 pitch
throughout, with a 213.4 pier between openings, carried on north from the
room mouth at 5067.7.

THE SHAPE
---------
North, west, north.  Three interior rectangles, all at the room's floor
and ceiling heights:
    A  x  666.95..1466.95   y 5067.70..6485.10   (out of the room)
    B  x -546.75..1466.95   y 5685.00..6485.10   (the cross leg)
    C  x -546.75.. 253.25   y 5685.00..7102.40   (into the mirror room)
C is A rotated 180 degrees about (460.1, 6085.05), and B maps onto
itself, so the whole assembly preserves the map's rotational symmetry.
Every box below is authored once and emitted with its rotated twin; the
pieces that would otherwise be self-symmetric are split in half so that
each one has a real partner and nothing is written twice.

THE HOLE
--------
266.7 square, one third of the 800.0 room width, centred on
(460.1, 6085.05) which is the map's own centre of rotation.  It is a hole
in the FLOOR only; the ceiling above it is solid.  The drop is 666.85
down to the stitch plate at -0.05, which is 16.9 m.
"""

import json
import sys

MAT = "materials/dev/reflectivity_30.vmat"

XP, YP = 460.1, 6085.05        # the two flip planes

# --- measured levels -------------------------------------------------
FLOOR = (640.15, 666.85)
CEIL = (1253.70, 1280.30)
WALL = (640.15, 1280.30)
SILL = (640.15, 720.15)
HEAD = (880.20, 1280.30)
# --- interior rectangles ---------------------------------------------
AX = (666.95, 1466.95)
AY = (5067.70, 6485.10)
BX = (-546.75, 1466.95)
BY = (5685.00, 6485.10)
# --- wall thicknesses, taken from the room ---------------------------
W_WEST = (640.15, 666.95)       # 26.8
W_EAST = (1466.95, 1493.65)     # 26.7
W_NORTH = (6485.10, 6511.80)    # 26.7
# --- hole -------------------------------------------------------------
HOLE = 266.7
HX = (XP - HOLE/2, XP + HOLE/2)
HY = (YP - HOLE/2, YP + HOLE/2)
# --- window run -------------------------------------------------------
WIN_LEN = 53.3
PITCH = 266.7
FIRST = 5281.10                 # 213.4 of pier after the room mouth


def box(name, x, y, z):
    return {
        "name": name,
        "origin": [round((x[0]+x[1])/2, 4), round((y[0]+y[1])/2, 4),
                   round((z[0]+z[1])/2, 4)],
        "extents": [round(x[1]-x[0], 4), round(y[1]-y[0], 4),
                    round(z[1]-z[0], 4)],
        "angles": [0.0, 0.0, 0.0],
        "material": MAT,
    }


def windowed_wall(tag, x, y0, y1):
    """A north-south wall carrying the room's window pattern."""
    out = []
    runs = []
    t = FIRST
    while t + WIN_LEN <= y1:
        if t >= y0:
            runs.append((t, t + WIN_LEN))
        t += PITCH
    cur = y0
    for i, (a, b) in enumerate(runs):
        if a > cur:
            out.append(box("%s_pier%d" % (tag, i), x, (cur, a), WALL))
        out.append(box("%s_sill%d" % (tag, i), x, (a, b), SILL))
        out.append(box("%s_head%d" % (tag, i), x, (a, b), HEAD))
        cur = b
    if cur < y1:
        out.append(box("%s_pier%d" % (tag, len(runs)), x, (cur, y1), WALL))
    return out


def seeds():
    b = []
    # floor and ceiling of leg A (its twin is leg C)
    b.append(box("bridge_floor_a", AX, AY, FLOOR))
    b.append(box("bridge_ceil_a", AX, AY, CEIL))
    # cross leg ceiling, split at the flip plane so each half has a twin
    b.append(box("bridge_ceil_b_e", (XP, BX[1]), BY, CEIL))
    # cross leg floor, four pieces around the hole
    b.append(box("bridge_floor_b_e", (HX[1], BX[1]), BY, FLOOR))
    b.append(box("bridge_floor_b_s", HX, (BY[0], HY[0]), FLOOR))
    # walls
    b += windowed_wall("bridge_wall_e", W_EAST, AY[0], AY[1])
    b += windowed_wall("bridge_wall_w", W_WEST, AY[0], BY[0])
    # north wall of the cross leg: from leg C's east wall across to the
    # outside of leg A's east wall, so both corners are closed
    b.append(box("bridge_wall_n", (2*XP - AX[0], W_EAST[1]), W_NORTH, WALL))
    return b


def rotate(bx):
    o, e = bx["origin"], bx["extents"]
    r = json.loads(json.dumps(bx))
    r["name"] = "m_" + bx["name"]
    r["origin"] = [round(2*XP - o[0], 4), round(2*YP - o[1], 4), o[2]]
    r["angles"] = [bx["angles"][0], 180.0, bx["angles"][2]]
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
    print("added %d, plan now %d boxes" % (added, len(plan["boxes"])))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_full.json")
