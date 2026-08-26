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

# The bridge ceiling under the room. Both halves of it reach the hole - the
# hole straddles x 460.1, the mirror line - so BOTH get cut.
# Their geometry is written out here rather than read from the plan, because
# after the first run the originals are gone - this file ate them - and a
# rerun still has to rebuild the same pieces. Same reason batch17 carries
# axis_571's extents instead of looking them up. READ off the plan 2026-08-26.
CEIL_CUT = [
    # name, x0, x1, y0, y1, z0, z1
    ("bridge_ceil_b_e", 460.1, 1467.0, 5685.0, 6485.1, 1253.7, 1280.3),
    ("m_bridge_ceil_b_e", -546.8, 460.1, 5685.0, 6485.1, 1253.7, 1280.3),
]

# Cover copied from the patron room, which is centred here and whose floor
# top is this, so a piece moves by the difference.
PATRON_C = (0.0, -3799.6)
PATRON_FLOOR_TOP = 426.8
# hex_blk_* and hex_ring_*. NOT the three-step stairs (hex_step_*), and NOT
# hex_dais_*: the dais is 480.1 x 831.6 centred on the room and would floor
# over the hole it is meant to sit around. Say the word and it comes back as
# pieces around the hole instead.
COVER_PREFIX = ("hex_blk_", "hex_ring_")
# The patron blocks carry the floor material, which reads wrong on a block.
COVER_MAT = MAT_WALL

# ---------------------------------------------------------------------------
# The triangle holes, one off each of four blocks. Two of them sit over a
# deck at the same height as the bridge ceiling, so that gets the same
# treatment - cut, not just floored over.
#
# Shape: the base lies flush on the block's outward face, the apex points
# outward with a 120 degree angle - the hexagon's own interior angle - which
# puts the two other sides parallel to hexagon edges. Base 480.2 and depth
# 138.6 follow from that angle; the depth is what leaves 206 u of walkable
# floor between the apex and the wall, and the base needs no margin because
# the block is on it.
# ---------------------------------------------------------------------------
TRI_BLOCKS = [("hex3_blk_300", 300.0), ("hex3_blk_240", 240.0),
              ("hex3_blk_120", 120.0), ("hex3_blk_60", 60.0)]
TRI_BASE = 480.2
TRI_APEX_DEG = 120.0
TRI_FACE_OFF = 106.7           # half of a block's 213.4 depth
DECK_Z = (1253.7, 1280.3)      # the deck under two of them

# THE LID over the square hole, flush with the room floor, so the midboss has
# something to stand on. SOLID GEOMETRY, not an entity: the real mechanism is
# a named brush killed by the boss's OnTrooperKilled output, and the plan
# format cannot express a connection yet - see PROBE.md item 5. Shelved on
# purpose rather than half-built.
#
# The deck cut below it stays open, so when the lid does become killable the
# shaft is already clear all the way to the bridge floor. Nothing has to be
# recut later.
#
# It is centred on the mirror point, so like the rest of the room it is not
# twinned.
LID = True
LID_NAME = "midboss_lid"

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


def triangle(block_origin, out_deg):
    """The three corners of one hole, from its block's outward face.

    Base on the face, apex out at TRI_APEX_DEG. With a 120 degree apex the
    base angles are 30, so the two sides come out parallel to hexagon edges -
    which is the whole reason for that angle.
    """
    a = math.radians(out_deg)
    n = (math.cos(a), math.sin(a))
    t = (-n[1], n[0])
    fc = (block_origin[0] + n[0] * TRI_FACE_OFF,
          block_origin[1] + n[1] * TRI_FACE_OFF)
    hb = TRI_BASE / 2.0
    depth = hb * math.tan(math.radians(90.0 - TRI_APEX_DEG / 2.0))
    return [(fc[0] - t[0] * hb, fc[1] - t[1] * hb),
            (fc[0] + t[0] * hb, fc[1] + t[1] * hb),
            (fc[0] + n[0] * depth, fc[1] + n[1] * depth)], depth


def in_tri(tri, x, y, shrink=0.0):
    """Inside the triangle, optionally pulled in from every edge."""
    inside = True
    for i in range(3):
        ax, ay = tri[i]
        bx, by = tri[(i + 1) % 3]
        cx, cy = tri[(i + 2) % 3]
        ex, ey = bx - ax, by - ay
        L = math.hypot(ex, ey)
        nx, ny = -ey / L, ex / L
        if nx * (cx - ax) + ny * (cy - ay) < 0:
            nx, ny = -nx, -ny        # inward normal
        if nx * (x - ax) + ny * (y - ay) < shrink:
            inside = False
    return inside


def split_around(b, tri, tag):
    """A box rebuilt as up to four pieces around a window holding the triangle.

    The window is the triangle's bounding box IN THIS BOX'S OWN FRAME, so the
    split is exact whatever angle the box sits at. What the window takes out
    beyond the triangle is put back by the edge slabs.
    """
    o, e = b["origin"], b["extents"]
    a = math.radians(b["angles"][1])
    ca, sa = math.cos(a), math.sin(a)

    def to_local(x, y):
        dx, dy = x - o[0], y - o[1]
        return dx * ca + dy * sa, -dx * sa + dy * ca

    pts = [to_local(x, y) for x, y in tri]
    wu0, wu1 = min(q[0] for q in pts), max(q[0] for q in pts)
    wv0, wv1 = min(q[1] for q in pts), max(q[1] for q in pts)
    hu, hv = e[0] / 2.0, e[1] / 2.0
    if wu0 >= hu or wu1 <= -hu or wv0 >= hv or wv1 <= -hv:
        return None, None            # this box does not reach the triangle
    wu0, wu1 = max(wu0, -hu), min(wu1, hu)
    wv0, wv1 = max(wv0, -hv), min(wv1, hv)

    def piece(nm, u0, u1, v0, v1):
        if u1 - u0 < 0.1 or v1 - v0 < 0.1:
            return None
        cu, cv = (u0 + u1) / 2.0, (v0 + v1) / 2.0
        return rotbox(nm, o[0] + cu * ca - cv * sa, o[1] + cu * sa + cv * ca,
                      o[2] - e[2] / 2.0, o[2] + e[2] / 2.0,
                      u1 - u0, v1 - v0, b["angles"][1],
                      b.get("material", MAT_WALL))

    out = []
    for nm, args in (("u0", (-hu, wu0, -hv, hv)), ("u1", (wu1, hu, -hv, hv)),
                     ("v0", (wu0, wu1, -hv, wv0)),
                     ("v1", (wu0, wu1, wv1, hv))):
        q = piece("%s_%s_%s" % (b["name"], tag, nm), *args)
        if q:
            out.append(q)
    # the window, back in world, so the slabs know what they must re-cover
    corners = [(o[0] + u * ca - v * sa, o[1] + u * sa + v * ca)
               for u, v in ((wu0, wv0), (wu1, wv0), (wu1, wv1), (wu0, wv1))]
    return out, corners


def edge_slabs(tri, windows, z0, z1, tag, mat, inside_ok):
    """One slab per triangle edge, on the outer side, re-covering the windows.

    Every point in a window that is not in the triangle is outside at least
    one edge, so three slabs are enough. Each is grown only as far as the
    hexagon allows: a slab that reached past a wall would hang in the air.
    """
    out = []
    pts = [q for w in windows for q in w]
    for i in range(3):
        ax, ay = tri[i]
        bx, by = tri[(i + 1) % 3]
        cx, cy = tri[(i + 2) % 3]
        ex, ey = bx - ax, by - ay
        L = math.hypot(ex, ey)
        ux, uy = ex / L, ey / L
        nx, ny = -uy, ux
        if nx * (cx - ax) + ny * (cy - ay) > 0:
            nx, ny = -nx, -ny        # outward
        # how far along and out the windows reach
        along = [(q[0] - ax) * ux + (q[1] - ay) * uy for q in pts]
        out_d = [(q[0] - ax) * nx + (q[1] - ay) * ny for q in pts]
        a0, a1 = min(along) - 5.0, max(along) + 5.0
        depth = max(max(out_d) + 5.0, 5.0)
        # shrink until every corner is inside the hexagon
        while depth > 1.0:
            cs = [(ax + ux * u + nx * d, ay + uy * u + ny * d)
                  for u in (a0, a1) for d in (0.0, depth)]
            if all(inside_ok(x, y) for x, y in cs):
                break
            depth -= 5.0
            a0, a1 = a0 + 2.5, a1 - 2.5
        cu, cd = (a0 + a1) / 2.0, depth / 2.0
        out.append(rotbox("%s_slab%d" % (tag, i),
                          ax + ux * cu + nx * cd, ay + uy * cu + ny * cd,
                          z0, z1, a1 - a0, depth,
                          math.degrees(math.atan2(uy, ux)), mat))
    return out


def cut_ceiling(by, log):
    """The marked ceiling, rebuilt as pieces around the square.

    The room's own hole only drops one step without this: the floor opens,
    and then the bridge ceiling 27 u below it is still solid.
    """
    out = []
    for n, x0, x1, y0, y1, z0, z1 in CEIL_CUT:
        b = by.get(n)
        if b is not None:
            o, e = b["origin"], b["extents"]
            got = (o[0] - e[0] / 2.0, o[0] + e[0] / 2.0,
                   o[1] - e[1] / 2.0, o[1] + e[1] / 2.0)
            if any(abs(u - v) > 0.1
                   for u, v in zip(got, (x0, x1, y0, y1))):
                log.append("WARNING: %s has moved since these extents were "
                           "read; the cut may not line up" % n)
        mat = MAT_WALL
        hx0, hx1 = max(x0, HOLE_X0), min(x1, HOLE_X1)
        # south and north of the hole, full width
        out.append(rotbox("%s_s" % n, (x0 + x1) / 2.0, (y0 + HOLE_Y0) / 2.0,
                          z0, z1, x1 - x0, HOLE_Y0 - y0, 0.0, mat))
        out.append(rotbox("%s_n" % n, (x0 + x1) / 2.0, (HOLE_Y1 + y1) / 2.0,
                          z0, z1, x1 - x0, y1 - HOLE_Y1, 0.0, mat))
        # and the part beside the hole, in the band the hole sits in
        if x1 - hx1 > 0.1:
            out.append(rotbox("%s_e" % n, (hx1 + x1) / 2.0,
                              (HOLE_Y0 + HOLE_Y1) / 2.0, z0, z1,
                              x1 - hx1, HOLE_Y1 - HOLE_Y0, 0.0, mat))
        if hx0 - x0 > 0.1:
            out.append(rotbox("%s_w" % n, (x0 + hx0) / 2.0,
                              (HOLE_Y0 + HOLE_Y1) / 2.0, z0, z1,
                              hx0 - x0, HOLE_Y1 - HOLE_Y0, 0.0, mat))
        log.append("cut %s into %d pieces around the hole%s"
                   % (n, len([q for q in out if q["name"].startswith(n)]),
                      "" if b is not None else " (original already gone, "
                      "rebuilt from this file's own extents)"))
    return out


def copy_cover(boxes, log):
    """Patron cover pieces, moved onto this room.

    Copied whole rather than re-derived: the ring and block positions carry
    the patron room's spacing, and the point is that this room matches it.
    """
    out = []
    dz = FLOOR_TOP - PATRON_FLOOR_TOP
    for b in boxes:
        n = b["name"]
        if n.startswith("m_") or not n.startswith(COVER_PREFIX):
            continue
        o = b["origin"]
        out.append({
            "name": n.replace("hex_", "hex3_"),
            "origin": [round(o[0] - PATRON_C[0] + CX, 4),
                       round(o[1] - PATRON_C[1] + CY, 4),
                       round(o[2] + dz, 4)],
            "extents": list(b["extents"]),
            "angles": list(b["angles"]),
            "material": COVER_MAT,
            MARK: True,
        })
    log.append("copied %d cover pieces from the patron room, raised %.1f"
               % (len(out), dz))
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

    if LID:
        new.append(rotbox(LID_NAME, (HOLE_X0 + HOLE_X1) / 2.0,
                          (HOLE_Y0 + HOLE_Y1) / 2.0, DECK, FLOOR_TOP,
                          HOLE_X1 - HOLE_X0, HOLE_Y1 - HOLE_Y0, 0.0,
                          MAT_FLOOR))

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

    # PUT BACK WHAT THE LAST RUN ATE. This file removes existing boxes to cut
    # holes in them - the bridge ceiling, and whatever deck sits under a
    # triangle. Their originals are stashed in the plan when they go, and
    # restored here, so a rerun starts from the same ground the first run
    # did. Without this the second run has nothing left to cut and quietly
    # produces a smaller map than the first.
    stash = plan.pop("_batch18_removed", [])
    if stash:
        have = {b["name"] for b in boxes}
        back = [b for b in stash if b["name"] not in have]
        boxes += back
        log.append("restored %d box(es) the last run cut up: %s"
                   % (len(back), ", ".join(sorted(b["name"] for b in back))))
    removed = []

    by = {b["name"]: b for b in boxes}
    rebuilt = start != len(boxes)
    need = ["bridge_floor_b_s", "m_bridge_floor_b_s", "hex_floor_0",
            "hex_roof_0", "hex_blk_0", "hex_ring_90"]
    if not rebuilt:
        need += [c[0] for c in CEIL_CUT]
    for n in need:
        if n not in by:
            print("::error::batch18: %s is missing" % n)
            sys.exit(1)

    new = build()
    new += cut_ceiling(by, log)
    cover = copy_cover(boxes, log)
    new += cover
    dead = {c[0] for c in CEIL_CUT}
    removed += [b for b in boxes if b["name"] in dead]
    boxes = [b for b in boxes if b["name"] not in dead]
    problems = []

    # ---- the four triangle holes ------------------------------------
    def in_hex(x, y, margin=0.0):
        r = math.hypot(x - CX, y - CY)
        ang = math.degrees(math.atan2(y - CY, x - CX)) % 60.0
        return r <= APOTHEM / math.cos(math.radians(ang - 30.0)) - margin

    cover_by = {b["name"]: b for b in cover}
    tris = []
    for bname, out_deg in TRI_BLOCKS:
        blk = cover_by.get(bname)
        if blk is None:
            problems.append("%s is not among the cover pieces" % bname)
            continue
        tri, depth = triangle(blk["origin"], out_deg)
        tris.append((bname, tri))

        # the room floor
        cut, windows = [], []
        keep = []
        for b in new:
            if "_floor_" not in b["name"]:
                keep.append(b)
                continue
            pieces, win = split_around(b, tri, "t")
            if pieces is None:
                keep.append(b)
            else:
                cut += pieces
                windows.append(win)
        if not windows:
            problems.append("%s: no floor piece reaches its triangle" % bname)
            continue
        new = keep + cut + edge_slabs(tri, windows, DECK, FLOOR_TOP,
                                      "hex3_tri_%s" % bname.split("_")[-1],
                                      MAT_FLOOR, lambda x, y: in_hex(x, y, 5.0))

        # the deck below, where there is one. Same cut, so the drop is the
        # same shape all the way down rather than a triangle onto a slab.
        deck_pieces = [b for b in boxes
                       if abs(b["origin"][2] - (DECK_Z[0] + DECK_Z[1]) / 2.0)
                       < 1.0 and not b["angles"][1] % 90]
        hit = []
        keep2 = []
        for b in deck_pieces:
            pieces, win = split_around(b, tri, "t")
            if pieces is None:
                continue
            hit.append((b, pieces, win))
        if hit:
            names = {h[0]["name"] for h in hit}
            removed += [b for b in boxes if b["name"] in names]
            boxes = [b for b in boxes if b["name"] not in names]
            wins = [h[2] for h in hit]
            for h in hit:
                new += h[1]
            new += edge_slabs(tri, wins, DECK_Z[0], DECK_Z[1],
                              "hex3_trideck_%s" % bname.split("_")[-1],
                              MAT_FLOOR, lambda x, y: True)
            log.append("%s: triangle cut through the floor and through %s"
                       % (bname, ", ".join(sorted(names))))
        else:
            log.append("%s: triangle cut through the floor; nothing below it "
                       "at deck height" % bname)

    # 1. THE FLOOR MUST BE SOLID EXCEPT FOR THE HOLE, and the hole must be
    # the whole hole. Sampled, because three rotated rectangles with gaps in
    # them is exactly the kind of construction that looks right and leaks.
    zf = DECK + FLOOR_T / 2.0
    floor_boxes = [q for q in new if "_floor_" in q["name"]
                   or "_tri_" in q["name"] or q["name"] == LID_NAME]
    # Bounding boxes first: the sample grid runs to tens of thousands of
    # points and an exact test against every piece is minutes, not seconds.
    bb = []
    for q in floor_boxes:
        o, e = q["origin"], q["extents"]
        r = (abs(e[0]) + abs(e[1])) / 2.0
        bb.append((q, o[0] - r, o[0] + r, o[1] - r, o[1] + r))

    def floored(x, y):
        for q, x0, x1, y0, y1 in bb:
            if x0 <= x <= x1 and y0 <= y <= y1 and covers(q, x, y, zf):
                return True
        return False

    inside_hole = miss = extra = 0
    gaps = []
    step = 20.0
    y = CY - RECT_L / 2.0
    while y <= CY + RECT_L / 2.0:
        x = CX - RECT_W
        while x <= CX + RECT_W:
            r = math.hypot(x - CX, y - CY)
            ang = math.degrees(math.atan2(y - CY, x - CX)) % 60.0
            in_hex_pt = r <= APOTHEM / math.cos(math.radians(ang - 30.0)) - 1.0
            in_hole = (HOLE_X0 + 1 <= x <= HOLE_X1 - 1
                       and HOLE_Y0 + 1 <= y <= HOLE_Y1 - 1)
            if in_hole:
                inside_hole += 1
                # With the lid in, the square must be SOLID; without it, the
                # square must be OPEN. Same sample, opposite expectation, so
                # the check follows the switch rather than being turned off.
                if floored(x, y) != LID:
                    extra += 1
            elif in_hex_pt and not floored(x, y):
                if not any(in_tri(t, x, y, -step) for _, t in tris):
                    miss += 1
                    if len(gaps) < 6:
                        gaps.append((round(x), round(y)))
            x += step
        y += step
    if extra:
        problems.append(
            "%d sample(s) inside the square are %s"
            % (extra, "not covered, but the lid is on"
               if LID else "covered, but the lid is off"))
    if miss:
        problems.append("the floor has %d unwanted gap(s), e.g. %s"
                        % (miss, gaps))
    log.append("floor sampled at %.0f u: %d points in the square, all %s, "
               "%d unwanted gaps elsewhere"
               % (step, inside_hole, "lidded" if LID else "open", miss))

    # Each triangle must be open, and open all the way to its own edges.
    for nm, t in tris:
        xs = [q[0] for q in t]
        ys = [q[1] for q in t]
        n_in = n_solid = 0
        yy = min(ys)
        while yy <= max(ys):
            xx = min(xs)
            while xx <= max(xs):
                if in_tri(t, xx, yy, 8.0):
                    n_in += 1
                    if floored(xx, yy):
                        n_solid += 1
                xx += 8.0
            yy += 8.0
        log.append("  %-14s %d interior samples, %d floored over"
                   % (nm, n_in, n_solid))
        if n_solid:
            problems.append("%s triangle is floored over at %d sample(s)"
                            % (nm, n_solid))

    # Matched by distance, not by an exact key. The bridge opening is 0.05
    # off the mirror point, so the floor pieces that line up with it are
    # 0.1 off their partners by construction - and an exact key also trips
    # on float rounding landing either side of a .5. TOL is tight enough to
    # catch a piece in the wrong place and loose enough to ignore both.
    # TOL covers extents as well as position: the bridge is 0.05 off the
    # mirror point, so a piece cut to the hole on one side is 0.1 wider than
    # its partner on the other.
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
                    or any(abs(u - v) > TOL
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
    # After the first run the deck is this file's own cut pieces, so check
    # against whichever is present.
    deck = by.get("bridge_ceil_b_e") or by.get("bridge_ceil_b_e_s")
    deck = deck or next((b for b in new
                         if b["name"] == "bridge_ceil_b_e_s"), None)
    if deck is None:
        problems.append("nothing found to stand the room on")
    else:
        top = deck["origin"][2] + deck["extents"][2] / 2.0
        if abs(top - DECK) > 0.1:
            problems.append("the deck's top is %.2f, not the %.2f this file "
                            "builds on" % (top, DECK))

    boxes.extend(new)
    plan["boxes"] = boxes
    plan["_batch18_removed"] = [json.loads(json.dumps(b)) for b in removed]

    log.append("")
    log.append("hexagon centred %.2f, %.2f   across corners %.1f, flats %.1f"
               % (CX, CY, RECT_W * 2, RECT_L))
    log.append("floor %.1f..%.1f   interior to %.1f   ceiling to %.1f"
               % (DECK, FLOOR_TOP, CEIL_BOT, CEIL_BOT + CEIL_T))
    log.append("hole  x %.1f..%.1f  y %.1f..%.1f, aligned to the bridge "
               "opening" % (HOLE_X0, HOLE_X1, HOLE_Y0, HOLE_Y1))
    log.append("lid   %s - %s"
               % ("ON" if LID else "OFF",
                  "%s fills the square flush with the floor; the deck below "
                  "is still cut, so the shaft is ready for the day the lid "
                  "can be killed" % LID_NAME if LID
                  else "the square is open all the way down"))
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
