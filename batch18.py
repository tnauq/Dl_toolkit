#!/usr/bin/env python3
"""batch18 - the hexagon room on top of the sky bridge ceiling.

RUNS AFTER batch17, BEFORE batch14, for the same reason batch17 does: batch14
is the zero-extent check and should see what the geometry scripts just made.

    SCRIPTS: batch13.py batch17.py batch18.py batch14.py batch15.py batch16.py

WHAT IT BUILDS. A hexagon the size of the patron rooms, sitting on top of
bridge_ceil_b_e, centred on the map centre, with a square hole in its floor
lined up with the opening in the bridge floor below.

    footprint     3200.4 across corners, 2771.7 across flats  (= hex_floor_*)
    floor         top of the bridge ceiling, 1280.3, slab 26.8 thick
    interior      1253.8 tall, the patron room's own height
    hole          326.8..593.5 x 5951.7..6218.4, READ off the bridge floor

IT IS NOT MIRRORED, AND THAT IS THE POINT. The room is centred on the mirror
point itself, so its twin would be the room again, in the same place, doubling
every box. Instead all six walls are authored and the piece set is checked for
being its own mirror image before the plan is written. Nothing else in this
repo works that way, so the check is not optional.

HOW A HEXAGON GETS A SQUARE HOLE. The patron room's floor is three rectangles
1600.2 x 2771.7 at 0, 60 and 120 degrees; their corners land on the hexagon's
vertices, so the union is the hexagon exactly. Nothing subtracts from a box
list, so each rectangle is instead built as four pieces around a central gap:

    the 0 degree one leaves exactly the square, refilled above and below it
    the 60 and 120 degree ones leave a 377.2 gap in their own frame

377.2 is chosen so the square fits inside the rotated gaps whatever the angle
- the square's half-diagonal is 188.6 - which makes the three gaps intersect
in the square and nothing more. 12 floor pieces instead of 3, same hexagon.

THE BOX COUNT MOVES. +21, none mirrored: 12 floor, 6 walls, 3 ceiling.

WHAT IS INVENTED
  - the interior height is copied from the patron room rather than read here.
  - THE ROOM HAS NO DOOR. Six solid walls; the floor hole is the only way in
    or out. Say where a door goes and it is four more boxes.
  - the walls are one piece per side, where the patron room's are split into
    jambs and headers around its doorways.

    python3 batch18.py [docs/plans/dust2_full.json]
"""

import json
import math
import sys

X_PLANE = 460.1
Y_PLANE = 6085.05
MARK = "_batch18"

MAT_WALL = "materials/dev/reflectivity_30.vmat"
MAT_FLOOR = "materials/dev/dev_measuregeneric01.vmat"

# ---------------------------------------------------------------------------
# READ off the plan.
# ---------------------------------------------------------------------------
CX, CY = X_PLANE, Y_PLANE          # the map centre, and the reading
DECK = 1280.3                      # top of bridge_ceil_b_e, the room's floor

RECT_W = 1600.2                    # hex_floor_* extents
RECT_L = 2771.7
FLOOR_T = 26.8                     # hex_floor_* thickness
CEIL_T = 26.6                      # hex_roof_* thickness
WALL_T = 26.7                      # hex_wall_* thickness
INTERIOR = 1253.8                  # hex_floor_* top to hex_roof_* underside

# The opening in the bridge floor below, read off bridge_floor_b_s and its
# twin. It is 0.05 off the mirror point in x - the bridge is a hair
# asymmetric - so the hole is aligned to the OPENING, not to the centre.
HOLE_X0, HOLE_X1 = 326.8, 593.5
HOLE_Y0, HOLE_Y1 = 5951.7, 6218.4

# Half-gap for the 60 and 120 degree rectangles: the square's half-diagonal,
# rounded up. Smaller and a corner of the square would be floored over.
HALF_DIAG = math.hypot(HOLE_X1 - HOLE_X0, HOLE_Y1 - HOLE_Y0) / 2.0
GAP = math.ceil(HALF_DIAG * 10) / 10.0

APOTHEM = RECT_L / 2.0             # 1385.85, centre to a wall face
SIDE = RECT_W                      # a hexagon's side equals its circumradius

FLOOR_TOP = DECK + FLOOR_T
CEIL_BOT = FLOOR_TOP + INTERIOR


def rotbox(name, cx, cy, z0, z1, ex, ey, yaw, mat):
    return {
        "name": name,
        "origin": [round(cx, 4), round(cy, 4), round((z0 + z1) / 2.0, 4)],
        "extents": [round(ex, 4), round(ey, 4), round(z1 - z0, 4)],
        "angles": [0.0, round(yaw, 4), 0.0],
        "material": mat,
        MARK: True,
    }


def local(dx, dy, yaw):
    """A point offset in a rectangle's own frame, put back into world."""
    a = math.radians(yaw)
    return (CX + dx * math.cos(a) - dy * math.sin(a),
            CY + dx * math.sin(a) + dy * math.cos(a))


def floor_ring(yaw, half_gap, tag, square=False):
    """One of the three rectangles, as four pieces around a central gap.

    In the rectangle's own frame the gap is |x| < half_gap and |y| <
    half_gap_y. The two side pieces take everything beyond the gap in x; the
    two stub pieces refill the gap column beyond the gap in y. What is left
    uncovered is exactly the gap rectangle.
    """
    out = []
    hx, hy = RECT_W / 2.0, RECT_L / 2.0
    gy = (HOLE_Y1 - HOLE_Y0) / 2.0 if square else half_gap

    side_w = hx - half_gap
    for i, s in enumerate((-1, 1)):
        cx, cy = local(s * (half_gap + side_w / 2.0), 0.0, yaw)
        out.append(rotbox("hex3_floor_%s_side%d" % (tag, i), cx, cy,
                          DECK, FLOOR_TOP, side_w, RECT_L, yaw, MAT_FLOOR))
    stub_l = hy - gy
    for i, s in enumerate((-1, 1)):
        cx, cy = local(0.0, s * (gy + stub_l / 2.0), yaw)
        out.append(rotbox("hex3_floor_%s_stub%d" % (tag, i), cx, cy,
                          DECK, FLOOR_TOP, half_gap * 2.0, stub_l, yaw,
                          MAT_FLOOR))
    return out


def build():
    new = []

    # floor: the 0 degree rectangle carries the square itself, the other two
    # only need to keep clear of it
    hole_hx = (HOLE_X1 - HOLE_X0) / 2.0
    new += floor_ring(0.0, hole_hx, "0", square=True)
    new += floor_ring(60.0, GAP, "60")
    new += floor_ring(120.0, GAP, "120")

    # The 0 degree rectangle is centred on the room, but the hole is 0.05
    # off it. Shift that one rectangle's pieces so the gap lands on the
    # opening below rather than on the centre.
    dx = (HOLE_X0 + HOLE_X1) / 2.0 - CX
    dy = (HOLE_Y0 + HOLE_Y1) / 2.0 - CY
    for b in new:
        if "_0_" in b["name"]:
            b["origin"][0] = round(b["origin"][0] + dx, 4)
            b["origin"][1] = round(b["origin"][1] + dy, 4)

    # six walls, one per side, standing just outside the floor edge
    for k in range(6):
        theta = 30.0 + 60.0 * k
        r = APOTHEM + WALL_T / 2.0
        cx = CX + r * math.cos(math.radians(theta))
        cy = CY + r * math.sin(math.radians(theta))
        # Longer than the side by a thickness at each end. Standing the
        # walls on the OUTSIDE of the apothem pushes their ends apart, so
        # walls cut to the exact side length leave a slot at all six
        # vertices - which a perimeter sweep at wall height found. They
        # overlap at the corners instead; overlapping solids are free.
        new.append(rotbox("hex3_wall_%d" % int(theta), cx, cy,
                          FLOOR_TOP, CEIL_BOT, SIDE + 2 * WALL_T, WALL_T,
                          theta + 90.0, MAT_WALL))

    # ceiling: the same three rectangles, solid
    for yaw, tag in ((0.0, "0"), (60.0, "60"), (120.0, "120")):
        new.append(rotbox("hex3_ceil_%s" % tag, CX, CY,
                          CEIL_BOT, CEIL_BOT + CEIL_T, RECT_W, RECT_L,
                          yaw, MAT_WALL))
    return new


def covers(b, x, y, z):
    """Is the point inside this box? Yaw only, which is all this file makes."""
    o, e = b["origin"], b["extents"]
    if not (o[2] - e[2] / 2.0 <= z <= o[2] + e[2] / 2.0):
        return False
    a = math.radians(b["angles"][1])
    dx, dy = x - o[0], y - o[1]
    u = dx * math.cos(a) + dy * math.sin(a)
    v = -dx * math.sin(a) + dy * math.cos(a)
    return abs(u) <= e[0] / 2.0 + 1e-6 and abs(v) <= e[1] / 2.0 + 1e-6


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_full.json"
    with open(path) as f:
        plan = json.load(f)

    log = []
    boxes = plan["boxes"]
    start = len(boxes)
    boxes = [b for b in boxes if not b.get(MARK)]
    log.append("stripped %d boxes from a previous batch18 run"
               % (start - len(boxes)))

    by = {b["name"]: b for b in boxes}
    for n in ("bridge_ceil_b_e", "bridge_floor_b_s", "m_bridge_floor_b_s",
              "hex_floor_0", "hex_roof_0"):
        if n not in by:
            print("::error::batch18: %s is missing" % n)
            sys.exit(1)

    new = build()
    problems = []

    # 1. THE FLOOR MUST BE SOLID EXCEPT FOR THE HOLE, and the hole must be
    # the whole hole. Sampled, because three rotated rectangles with gaps in
    # them is exactly the kind of construction that looks right and leaks.
    zf = DECK + FLOOR_T / 2.0
    inside_hole = miss = extra = 0
    step = 12.0
    y = CY - RECT_L / 2.0
    while y <= CY + RECT_L / 2.0:
        x = CX - RECT_W
        while x <= CX + RECT_W:
            # inside the hexagon?
            r = math.hypot(x - CX, y - CY)
            ang = math.degrees(math.atan2(y - CY, x - CX)) % 60.0
            lim = APOTHEM / math.cos(math.radians(ang - 30.0))
            in_hex = r <= lim - 1.0
            in_hole = (HOLE_X0 + 1 <= x <= HOLE_X1 - 1
                       and HOLE_Y0 + 1 <= y <= HOLE_Y1 - 1)
            solid = any(covers(b, x, y, zf) for b in new)
            if in_hole:
                inside_hole += 1
                if solid:
                    extra += 1
            elif in_hex and not solid:
                miss += 1
            x += step
        y += step
    if extra:
        problems.append("the floor covers %d sample(s) inside the hole" % extra)
    if miss:
        problems.append("the floor has %d hole(s) it should not have" % miss)
    log.append("floor sampled: %d points in the hole, all open; %d gaps "
               "elsewhere in the hexagon" % (inside_hole, miss))

    # 2. THE ROOM MUST BE ITS OWN MIRROR IMAGE, since nothing here is twinned.
    # Every piece must map onto some piece under the 180 degree rotation.
    # Matched by distance, not by an exact key. The bridge opening is 0.05
    # off the mirror point, so the floor pieces that line up with it are
    # 0.1 off their partners by construction - and an exact key also trips
    # on float rounding landing either side of a .5. TOL is tight enough to
    # catch a piece in the wrong place and loose enough to ignore both.
    TOL = 0.25
    worst = 0.0
    for b in new:
        mx = 2 * X_PLANE - b["origin"][0]
        my = 2 * Y_PLANE - b["origin"][1]
        myaw = (b["angles"][1] + 180.0) % 180.0
        best = None
        for c in new:
            if (abs(c["angles"][1] % 180.0 - myaw) > 0.01
                    or abs(c["origin"][2] - b["origin"][2]) > 0.01
                    or any(abs(u - v) > 0.01
                           for u, v in zip(c["extents"], b["extents"]))):
                continue
            d = math.hypot(c["origin"][0] - mx, c["origin"][1] - my)
            if best is None or d < best:
                best = d
        if best is None or best > TOL:
            problems.append("%s has no mirror partner (nearest %s); the room "
                            "is not symmetric and would need twinning after "
                            "all" % (b["name"],
                                     "%.2f" % best if best else "none"))
        else:
            worst = max(worst, best)
    if not problems:
        log.append("all %d pieces map onto the set under the mirror (worst "
                   "offset %.2f u), so no twins are made" % (len(new), worst))

    # 3. It must actually sit on the bridge ceiling.
    deck = by["bridge_ceil_b_e"]
    top = deck["origin"][2] + deck["extents"][2] / 2.0
    if abs(top - DECK) > 0.1:
        problems.append("bridge_ceil_b_e's top is %.2f, not the %.2f this "
                        "file builds on" % (top, DECK))

    boxes.extend(new)
    plan["boxes"] = boxes

    log.append("")
    log.append("hexagon centred %.2f, %.2f   across corners %.1f, flats %.1f"
               % (CX, CY, RECT_W * 2, RECT_L))
    log.append("floor %.1f..%.1f   interior to %.1f   ceiling to %.1f"
               % (DECK, FLOOR_TOP, CEIL_BOT, CEIL_BOT + CEIL_T))
    log.append("hole  x %.1f..%.1f  y %.1f..%.1f, aligned to the bridge "
               "opening" % (HOLE_X0, HOLE_X1, HOLE_Y0, HOLE_Y1))
    log.append("NO DOOR: six solid walls, the floor hole is the only way in")
    log.append("")
    log.append("added %d boxes, none mirrored; boxes %d -> %d"
               % (len(new), start, len(boxes)))

    if problems:
        print("\n".join(log))
        print("")
        for p in problems:
            print("::error::batch18: " + p)
        sys.exit(1)

    with open(path, "w") as f:
        json.dump(plan, f, indent=1)
    print("\n".join(log))


if __name__ == "__main__":
    main()
