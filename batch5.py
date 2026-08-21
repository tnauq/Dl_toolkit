#!/usr/bin/env python3
"""batch5.py - eleventh build step, run after batch4.py.

Cuts a plain rectangular door through the axis_43 / seam_w_a wall line at
jump_platform level and hangs a balcony with a railing on the far side.

No arch head. A _d195 needs 586.80 and the sill at 960.20 only leaves
320.10 before the wall top at 1280.30, so this is a short square opening
by choice, not by oversight.

The opening is centred on 5376.30, the same centre as jump_platform, and
so straddles the join between axis_43 (which ends at 5494.50) and
seam_w_a. Both walls are cut.

All work is done on the half side and the m_ twins derived by the plan
transform (x' = 920.2 - x, y' = 12170.1 - y, yaw' = yaw + 180), so
symmetry is exact by construction. Name-keyed and rerunnable: outputs are
cleared and rebuilt, and a cut is skipped if its source wall is already
gone.

Usage: python3 batch5.py docs/plans/dust2_full.json
"""

import json
import sys

MAT = "materials/dev/reflectivity_30.vmat"
MIRROR_X = 920.2
MIRROR_Y = 12170.1

CENTRE_Y = 5376.30          # jump_platform centre
SILL = 960.20               # jump_platform top
OPENING_W = 253.00          # kept at the _d195 width so it walks the same
LINTEL = 26.70              # so the opening reads as a door, not a notch
WALL_TOP = 1280.30
HEAD = WALL_TOP - LINTEL    # 1253.60, giving 293.40 of clear height

WALL_FACE_E = 2800.55       # east face of the axis_43 / seam_w_a line

BALCONY_D = 160.05
BALCONY_W = 400.10
BALCONY_TOP = SILL
THICK = 26.70
RAIL_H = 106.70

CUTS = ["axis_43", "seam_w_a"]
BALCONY_OUT = ["balcony_75", "balcony_75_rail_e",
               "balcony_75_rail_s", "balcony_75_rail_n"]


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


def main(path):
    with open(path) as f:
        plan = json.load(f)
    boxes = plan["boxes"]

    oy0 = round(CENTRE_Y - OPENING_W / 2.0, 4)
    oy1 = round(CENTRE_Y + OPENING_W / 2.0, 4)

    present = set(b["name"] for b in boxes)
    drop = set()
    for n in BALCONY_OUT:
        drop.add(n)
        drop.add("m_" + n)
    for w in CUTS:
        if w not in present:
            continue        # already cut; leave its pieces alone
        for suffix in ("_s", "_n", "_under", "_hdr"):
            drop.add(w + suffix)
            drop.add("m_" + w + suffix)
    before = len(boxes)
    boxes[:] = [b for b in boxes if b["name"] not in drop]
    if before != len(boxes):
        print("REBUILD: removed %d previous outputs" % (before - len(boxes)))

    by_name = {b["name"]: b for b in boxes}
    made = []

    print("DOOR: opening y %.2f..%.2f, sill %.2f, head %.2f, clear %.2f"
          % (oy0, oy1, SILL, HEAD, HEAD - SILL))

    for w in CUTS:
        wall = by_name.get(w)
        if wall is None:
            print("SKIP %s: not in plan, already cut on a previous run" % w)
            continue
        wx = span(wall, 0)
        wy = span(wall, 1)
        wz = span(wall, 2)
        cy0 = max(oy0, wy[0])
        cy1 = min(oy1, wy[1])
        if cy1 <= cy0:
            print("SKIP %s: opening does not reach this wall" % w)
            continue
        pieces = []
        if cy0 > wy[0]:
            pieces.append(box(w + "_s", wx, (wy[0], cy0), wz))
        if wy[1] > cy1:
            pieces.append(box(w + "_n", wx, (cy1, wy[1]), wz))
        if SILL > wz[0]:
            pieces.append(box(w + "_under", wx, (cy0, cy1), (wz[0], SILL)))
        if wz[1] > HEAD:
            pieces.append(box(w + "_hdr", wx, (cy0, cy1), (HEAD, wz[1])))
        print("CUT %s: removed y %.2f..%.2f, %d pieces"
              % (w, cy0, cy1, len(pieces)))
        boxes[:] = [b for b in boxes
                    if b["name"] != w and b["name"] != "m_" + w]
        made.extend(pieces)

    # ------------------------------------------------------------ balcony
    bx = (WALL_FACE_E, WALL_FACE_E + BALCONY_D)
    by0 = CENTRE_Y - BALCONY_W / 2.0
    by1 = CENTRE_Y + BALCONY_W / 2.0
    made.append(box("balcony_75", bx, (by0, by1),
                    (BALCONY_TOP - THICK, BALCONY_TOP)))
    made.append(box("balcony_75_rail_e",
                    (bx[1] - THICK, bx[1]), (by0, by1),
                    (BALCONY_TOP, BALCONY_TOP + RAIL_H)))
    made.append(box("balcony_75_rail_s",
                    bx, (by0, by0 + THICK),
                    (BALCONY_TOP, BALCONY_TOP + RAIL_H)))
    made.append(box("balcony_75_rail_n",
                    bx, (by1 - THICK, by1),
                    (BALCONY_TOP, BALCONY_TOP + RAIL_H)))
    print("BALCONY balcony_75: x %.2f..%.2f, y %.2f..%.2f, top %.2f, "
          "rail %.2f tall on 3 sides"
          % (bx[0], bx[1], by0, by1, BALCONY_TOP, RAIL_H))

    twins = [mirror_box(b, "m_" + b["name"]) for b in made]
    boxes.extend(made)
    boxes.extend(twins)
    print("batch5.py: added %d half boxes + %d twins, %d boxes in plan"
          % (len(made), len(twins), len(boxes)))

    with open(path, "w") as f:
        json.dump(plan, f, indent=1)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_full.json")
