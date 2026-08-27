#!/usr/bin/env python3
"""batch17 - the two teleporter rooms, built from the _d574 arch design.

RUNS AFTER batch13 and BEFORE batch16. batch13 rebuilds the box list from
scratch, so this has to come after it or the walls it splits come back whole.
batch16 only touches entities and reads no geometry, so it can follow.

    SCRIPTS: batch13.py batch14.py batch15.py batch17.py batch16.py

TWO ROOMS, same dimensions, same arch, different surroundings. Both are
authored on the BASE half and mirrored, so every number here is the mirror of
what was read on the m_ half.

    room     arch wall   floor                what had to be built
    tele_a   axis_571    axis_546 + strip     1 wall, 1 ceiling
    tele_b   axis_451    gapfill_39_8 + slab  3 walls, 1 ceiling

A room sits on ONE side of its arch wall, given by "side": +1 puts it on the
+y face, -1 on the -y face. Room A opens off the alcove in front of its wall;
room B sits BEHIND its wall, so from the gapfill_39_8 floor you see only
axis_451 with an arch in it, and the room is through the arch. That side has
no floor of its own, so the floor is carried past the wall to meet it.

"Identical" means the interior: 226.7 wide, 160 deep, 373.3 floor to ceiling,
with a 160 u arch opening whose crown is 371.1 above the floor. It does not
mean the same part count. Room A drops into an existing alcove that already
had three sides and a ceiling above it; room B stands in open floor, so it
brings its own sides.

HOW AN ARCH IS SET INTO A WALL. Nothing subtracts from a box list, so the
wall is REMOVED and rebuilt as a sill, two jambs and a header around the
hole, and the 16-piece _d574 assembly is scaled into the gap. The jambs run
to the wall's own ends, so a wall longer than the room simply gets longer
jambs - which is what "centred in the wall" means for room B, whose wall is
320.1 long against a 226.7 room.

THE ARCH IS SCALED UNIFORMLY. Its pieces carry pitch as well as yaw - they
are tilted wedges, not axis boxes - and only a uniform scale preserves the
angles of a rotated box. The copy is 0.6324 in all three axes, so it is 16.9
thick where the original is 26.7 and sits recessed in the wall rather than
flush with both faces. Scaling width and height but not thickness would have
skewed every tilted piece.

THE BOX COUNT MOVES. Each room removes 1 box per half and adds its parts, and
every one is mirrored. EXPECT_BOXES in batch.yml moves with it deliberately;
that is what the tripwire is for.

ROOM B LANDS ON A DECORATIVE COLUMN. angled-wall_488 through _497 lean up
through the room's north-east corner, 118 u in from the arch wall, and the
new north wall passes through them. Nothing here deletes them: they clear the
arch and the teleporter, and a leaning column inside the room may well be
wanted. The check below names every piece it finds, so keeping them is an
explicit choice rather than an oversight.

INVENTED HERE
  - the 160 u opening width, hence the 0.6324 scale.
  - the ceiling height, 2.2 u above the arch crown.
  - room A's new wall is 53.3 thick to fill the yaw_570/yaw_573 gap exactly;
    room B's three walls use the 26.7 the axis walls use.

    python3 batch17.py [docs/plans/dust2_full.json]
"""

import json
import math
import sys

X_PLANE = 460.1
Y_PLANE = 6085.05
PREFIX = "m_"
MARK = "_batch17"

MAT_WALL = "materials/dev/reflectivity_30.vmat"
MAT_FLOOR = "materials/dev/dev_measuregeneric01.vmat"

# ---------------------------------------------------------------------------
# The arch source: the _d574 family set into axis_574. All READ off the plan.
# ---------------------------------------------------------------------------
ARCH_PIECES = [
    "ramp-slab_820_d574", "ramp-slab_821_d574", "ramp-slab_822_d574",
    "ramp-slab_833_d574", "ramp-slab_834_d574", "ramp-slab_835_d574",
    "ramp_823_d574", "ramp_824_d574", "ramp_825_d574", "ramp_826_d574",
    "ramp_829_d574", "ramp_830_d574", "ramp_831_d574", "ramp_832_d574",
    "shallow_827_d574", "shallow_828_d574",
]
SRC_WALL_X = -613.5        # face plane of axis_574, the arch's thickness axis
SRC_OPEN_C = 1312.05       # centre of the source opening, across
SRC_CROWN = 800.1          # top of the source arch head
SRC_OPEN_W = 253.0         # source opening width
SRC_SILL = 213.3           # top of axis_574_low, the source opening's floor

NEW_OPEN_W = 160.0         # INVENTED
SCALE = NEW_OPEN_W / SRC_OPEN_W
OPEN_H = (SRC_CROWN - SRC_SILL) * SCALE   # floor to crown, 371.1
ROOM_H = OPEN_H + 2.2                     # floor to ceiling underside
CEIL_T = 26.7
DEPTH = 160.0

# ---------------------------------------------------------------------------
# The rooms, in base-half coordinates. Every face here is READ off a box that
# already exists; only the depth and the wall thicknesses are chosen.
#
# Both arch walls happen to be thin in y with the room on the +y side, so one
# code path builds both.
# ---------------------------------------------------------------------------
ROOMS = [
    {
        "name": "tele_a",
        "side": +1,
        "wall": "axis_571",
        "wall_x0": -466.75, "wall_x1": -240.05,
        "wall_y0": 400.05, "wall_y1": 426.75,
        "wall_z0": 213.45, "wall_z1": 1280.35,
        "room_x0": -466.75, "room_x1": -240.05,
        "floor_top": 426.75, "floor_bot": 400.05,
        # axis_546 stops 80 u short of axis_572; this closes it
        "floor_ext": ("axis_546_ext571", 506.79),
        # the yaw_570 / yaw_573 gap, filled at their own 53.3 thickness
        "walls": [("axis_571_room_w", "x", -520.05, -466.75)],
        "wall_top": 1280.35,
        "needs": ["axis_546", "axis_572", "yaw_570", "yaw_573"],
    },
    # ARCH ONLY, no room: batch18 builds the shrine rooms these open into,
    # because they are boxes rather than the rectangular alcove this file's
    # builder makes. All this does here is cut the door.
    #
    # The doors sit at the INNER corner of each room, not the middle of its
    # south face: hex_wall_n_l only spans x -826.8..-200, so a door centred
    # on the room at x -765 would open into the gap beside the wall rather
    # than into the base.
    {
        "name": "shrine_door_w",
        "side": +1,
        "arch_only": True,
        "wall": "hex_wall_n_l",
        "wall_x0": -826.8, "wall_x1": -200.0,
        "wall_y0": -2413.75, "wall_y1": -2387.05,
        "wall_z0": 426.8, "wall_z1": 1707.2,
        "room_x0": -445.0, "room_x1": -285.0,
        "floor_top": 426.8, "floor_bot": None,
        "floor_ext": None,
        "walls": [],
        "wall_top": None,
        "needs": ["hex_wall_nw_r"],
    },
    {
        "name": "shrine_door_e",
        "side": +1,
        "arch_only": True,
        "wall": "hex_wall_n_r",
        "wall_x0": 200.0, "wall_x1": 826.8,
        "wall_y0": -2413.75, "wall_y1": -2387.05,
        "wall_z0": 426.8, "wall_z1": 1707.2,
        "room_x0": 285.0, "room_x1": 445.0,
        "floor_top": 426.8, "floor_bot": None,
        "floor_ext": None,
        "walls": [],
        "wall_top": None,
        "needs": ["hex_wall_ne_l"],
    },
    {
        "name": "tele_b",
        "side": -1,             # behind the wall, not out on the open floor
        "wall": "axis_451",
        "wall_x0": 1947.0, "wall_x1": 2267.2,
        "wall_y0": 0.0, "wall_y1": 26.6,
        "wall_z0": 213.4, "wall_z1": 1067.0,
        # centred in a wall longer than the room: 46.65 of wall each side
        "room_x0": 1993.75, "room_x1": 2220.45,
        "floor_top": 213.4, "floor_bot": 0.0,
        # There is no floor behind axis_451 for most of this span - only
        # gapfill_40_7, which stops at x 2080 and y -80. So the floor is
        # carried past the wall under the whole room and its walls, from the
        # wall's own far face out to the back wall.
        "floor_ext": ("gapfill_39_8_ext451", 26.6),
        "walls": [("axis_451_room_w", "x", 1967.05, 1993.75),
                  ("axis_451_room_e", "x", 2220.45, 2247.15),
                  ("axis_451_room_n", "y", -186.6, -160.0)],
        "wall_top": None,       # only as tall as the room
        "needs": ["gapfill_39_8", "gapfill_40_7"],
    },
]


def norm(a):
    while a > 180.0:
        a -= 360.0
    while a <= -180.0:
        a += 360.0
    return round(a, 4)


def twin_box(b):
    """180 degrees about the mirror point. Pitch and roll are unchanged:
    composing a z-rotation with the piece's own rotation only moves yaw."""
    t = json.loads(json.dumps(b))
    t["name"] = PREFIX + b["name"]
    t["origin"] = [round(2.0 * X_PLANE - b["origin"][0], 4),
                   round(2.0 * Y_PLANE - b["origin"][1], 4),
                   b["origin"][2]]
    a = b.get("angles", [0.0, 0.0, 0.0])
    t["angles"] = [a[0], norm(a[1] + 180.0), a[2]]
    return t


MIN_EXTENT = 0.1


def box(name, x0, x1, y0, y1, z0, z1, mat=MAT_WALL):
    """None if the piece has no thickness in some axis.

    A sill is only needed where the wall starts BELOW the room floor. On
    axis_451 the two are the same height, so the sill is nothing at all -
    and a zero-extent box is exactly what batch14's check fails on. Better
    to not make it than to make it and have the next script reject it.
    """
    if min(x1 - x0, y1 - y0, z1 - z0) < MIN_EXTENT:
        return None
    return {
        "name": name,
        "origin": [round((x0 + x1) / 2.0, 4), round((y0 + y1) / 2.0, 4),
                   round((z0 + z1) / 2.0, 4)],
        "extents": [round(x1 - x0, 4), round(y1 - y0, 4), round(z1 - z0, 4)],
        "angles": [0.0, 0.0, 0.0],
        "material": mat,
        MARK: True,
    }


def aabb(b):
    """Conservative world extent. A piece at an odd yaw gets its diagonal,
    which over-states it - right for a check that must not miss an overlap."""
    e = b["extents"]
    # Exact for a yaw-only box: project the half-extents onto the world axes.
    # The earlier version used the diagonal for any odd angle, which reported
    # the two 45 degree yaw_ walls as being inside room A when they only
    # touch its corner.
    a = math.radians(b["angles"][1])
    c, s_ = abs(math.cos(a)), abs(math.sin(a))
    hx = (e[0] * c + e[1] * s_) / 2.0
    hy = (e[0] * s_ + e[1] * c) / 2.0
    o = b["origin"]
    return (o[0] - hx, o[0] + hx, o[1] - hy, o[1] + hy,
            o[2] - e[2] / 2.0, o[2] + e[2] / 2.0)


def scaled_arch(src, tag, open_c, crown, wall_c):
    """The _d574 assembly, uniformly scaled and set into a new wall.

    Source frame: u across the opening (its y), t through the wall (its x),
    w down from the crown (its z). Target frame: u becomes x, t becomes y.
    That is a 90 degree turn, so every piece's yaw turns with it.
    """
    out = []
    for b in src:
        u = b["origin"][1] - SRC_OPEN_C
        t = b["origin"][0] - SRC_WALL_X
        w = b["origin"][2] - SRC_CROWN
        a = b["angles"]
        out.append({
            "name": b["name"].replace("_d574", "_" + tag),
            "origin": [round(open_c + SCALE * u, 4),
                       round(wall_c + SCALE * t, 4),
                       round(crown + SCALE * w, 4)],
            "extents": [round(v * SCALE, 4) for v in b["extents"]],
            "angles": [a[0], norm(a[1] + 90.0), a[2]],
            "material": b.get("material", MAT_WALL),
            MARK: True,
        })
    return out


def build_room(spec, src, log, problems):
    w = spec["wall"]
    tag = w.split("_")[-1]
    wx0, wx1 = spec["wall_x0"], spec["wall_x1"]
    rx0, rx1 = spec["room_x0"], spec["room_x1"]
    ft = spec["floor_top"]
    wy0, wy1 = spec["wall_y0"], spec["wall_y1"]
    side = spec["side"]
    if side > 0:
        ry0, ry1 = wy1, wy1 + DEPTH
    else:
        ry0, ry1 = wy0 - DEPTH, wy0
    crown = ft + OPEN_H
    ceil_bot = ft + ROOM_H
    open_c = (rx0 + rx1) / 2.0
    ox0, ox1 = open_c - NEW_OPEN_W / 2.0, open_c + NEW_OPEN_W / 2.0
    top = spec["wall_top"] or (ceil_bot + CEIL_T)

    new = []
    skipped = []

    def add(b, why=""):
        if b is None:
            skipped.append(why)
        else:
            new.append(b)

    add(box("%s_sill" % w, wx0, wx1, wy0, wy1, spec["wall_z0"], ft), "sill")
    add(box("%s_jamb_w" % w, wx0, ox0, wy0, wy1, ft, crown), "west jamb")
    add(box("%s_jamb_e" % w, ox1, wx1, wy0, wy1, ft, crown), "east jamb")
    add(box("%s_hdr" % w, wx0, wx1, wy0, wy1, crown, spec["wall_z1"]),
        "header")
    arch = scaled_arch(src, tag, open_c, crown, (wy0 + wy1) / 2.0)
    new += arch

    if spec["floor_ext"]:
        # Floor from wherever the existing floor stops, to the room's back
        # wall, and wide enough to carry the side walls too.
        nm, from_y = spec["floor_ext"]
        fy0, fy1 = (from_y, ry1) if side > 0 else (ry0 - 26.7, from_y)
        pad = 0.0 if side > 0 else 26.7
        add(box(nm, rx0 - pad, rx1 + pad, fy0, fy1,
                spec["floor_bot"], ft, MAT_FLOOR), "floor extension")

    for nm, axis, a, b_ in spec["walls"]:
        if axis == "x":
            add(box(nm, a, b_, ry0, ry1, ft, top), nm)
        else:
            add(box(nm, rx0 - 26.7, rx1 + 26.7, a, b_, ft, top), nm)
    if not spec.get("arch_only"):
        add(box("ceiling_%s" % tag, rx0, rx1, ry0, ry1,
                ceil_bot, ceil_bot + CEIL_T), "ceiling")

    tele = [round(open_c, 2), round((ry0 + ry1) / 2.0, 2), ft]

    log.append("")
    log.append("%s  room x %.2f..%.2f  y %.2f..%.2f  floor %.2f  ceiling %.2f"
               % (spec["name"], rx0, rx1, ry0, ry1, ft, ceil_bot))
    log.append("        opening %.1f wide at x %.2f..%.2f, crown %.2f"
               % (NEW_OPEN_W, ox0, ox1, crown))
    log.append("        jambs %.2f and %.2f" % (ox0 - wx0, wx1 - ox1))
    if not spec.get("arch_only"):
        log.append("        teleporter at %s" % tele)
    if skipped:
        log.append("        no %s needed here: the wall does not extend "
                   "below the floor" % ", ".join(skipped))

    ax0 = min(aabb(b)[0] for b in arch)
    ax1 = max(aabb(b)[1] for b in arch)
    log.append("        arch spans x %.2f..%.2f in a wall of %.2f..%.2f"
               % (ax0, ax1, wx0, wx1))
    if ax0 < wx0 or ax1 > wx1:
        problems.append("%s: the scaled arch is %.1f wide and overhangs its "
                        "wall" % (spec["name"], ax1 - ax0))
    return new, tele, (rx0, rx1, ry0, ry1, ft, ceil_bot + CEIL_T)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_full.json"
    with open(path) as f:
        plan = json.load(f)

    log = []
    boxes = plan["boxes"]
    start = len(boxes)
    boxes = [b for b in boxes if not b.get(MARK)]
    rebuilt = start != len(boxes)
    log.append("stripped %d boxes from a previous batch17 run"
               % (start - len(boxes)))

    by = {b["name"]: b for b in boxes}
    need = list(ARCH_PIECES)
    for spec in ROOMS:
        need += spec["needs"]
        # An arch wall is expected to be gone on a rerun in a chain where
        # batch13 did not regenerate it - this file ate it last time. That is
        # only acceptable if this run also found its own boxes to strip.
        if not rebuilt:
            need.append(spec["wall"])
    for n in need:
        if n not in by:
            print("::error::batch17: %s is missing; batch13 may have "
                  "renamed it" % n)
            sys.exit(1)

    src = [by[n] for n in ARCH_PIECES]
    problems = []
    new, teles, volumes = [], [], []
    for spec in ROOMS:
        w = spec["wall"]
        boxes = [b for b in boxes if b["name"] not in (w, PREFIX + w)]
        made, tele, vol = build_room(spec, src, log, problems)
        new += made
        if not spec.get("arch_only"):
            teles.append((spec["name"], tele))
            volumes.append((spec["name"], vol))

    boxes.extend(new)
    boxes.extend([twin_box(b) for b in new])
    plan["boxes"] = boxes

    # What already stands inside a room. Overlapping solids are harmless to
    # the converter, but a column through the middle of a room is a decision,
    # not a detail. Named, not deleted.
    log.append("")
    for nm, (rx0, rx1, ry0, ry1, z0, z1) in volumes:
        found = []
        for b in boxes:
            if b.get(MARK):
                continue
            x0, x1, y0, y1, bz0, bz1 = aabb(b)
            if (x1 > rx0 + 1 and x0 < rx1 - 1 and y1 > ry0 + 1
                    and y0 < ry1 - 1 and bz1 > z0 + 1 and bz0 < z1 - 1):
                # How far in it reaches matters more than that it touches:
                # a 45 degree wall clipping a corner by a few units is not
                # the same finding as a column standing in the middle.
                found.append((b["name"],
                              min(x1, rx1) - max(x0, rx0),
                              min(y1, ry1) - max(y0, ry0),
                              min(bz1, z1) - max(bz0, z0)))
        if found:
            log.append("%s already contains %d box(es), by how far they "
                       "reach in:" % (nm, len(found)))
            for n2, dx, dy, dz in sorted(found, key=lambda f: -f[1] * f[2]):
                log.append("        %-18s %6.1f x %6.1f x %6.1f"
                           % (n2, dx, dy, dz))
            log.append("        left in place on purpose - say so and a "
                       "later drop can delete them")
        else:
            log.append("%s is clear of existing geometry" % nm)

    log.append("")
    for nm, t in teles:
        log.append("%s teleporter -> %s   (paste into batch16)" % (nm, t))
    log.append("")
    log.append("added %d boxes per half across %d rooms; boxes %d -> %d"
               % (len(new), len(ROOMS), start, len(boxes)))

    if problems:
        print("\n".join(log))
        print("")
        for p in problems:
            print("::error::batch17: " + p)
        sys.exit(1)

    with open(path, "w") as f:
        json.dump(plan, f, indent=1)
    print("\n".join(log))


if __name__ == "__main__":
    main()
