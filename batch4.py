#!/usr/bin/env python3
"""batch4.py - tenth build step, run after batch3.py.

  1. step_seam_w_c: a box against seam_w_c's west face, top at half the
     height of seam_w_c_under measured from stitch_ground, centred on
     arch_w_shallow_828.
  2. A _d195 arch door through seam_e_a, centred on t1_pad1, sill on the
     pad.
  3. A _d195 arch door through axis_47, tucked against axis_46, sill on
     gapfill_56_41.

The fourth request, a door through axis_553_mid, is NOT built. It does
not fit twice over. See the note at the bottom of this docstring.

All work is done on the half side and the m_ twins are derived by the
plan transform (x' = 920.2 - x, y' = 12170.1 - y, yaw' = yaw + 180), so
symmetry is exact by construction. Name-keyed and rerunnable: the script
deletes its own outputs and rebuilds, and skips a cut whose source wall
is already gone.

All three target walls are x-normal, the same as the arch_w_* source
wall, so each clone is a pure translation with no rotation.

NOT BUILT, request 4, both failures measured against the plan:
  Width. axis_553_mid runs from y 3040.45 and axis_739's south face is
  at 3280.65, so a door tucked into that corner has 240.20 to sit in.
  A _d195 is 253.00 wide. Short by 12.80.
  Height. axis_761's top is 720.20 and axis_553_mid's top is 1280.30,
  leaving 560.10. A _d195 needs 586.80. Short by 26.70.
Also note axis_553_mid is 53.30 thick, twice the 26.70 arch source, so
whatever is agreed there needs the head cloned twice across the
thickness rather than one thin arch floating inside.

Usage: python3 batch4.py docs/plans/dust2_full.json
"""

import json
import sys

MAT = "materials/dev/reflectivity_30.vmat"
MIRROR_X = 920.2
MIRROR_Y = 12170.1

ARCH_PREFIX = "arch_w_"
ARCH_SRC_X = 1907.10
ARCH_SRC_Y = 5818.40
ARCH_SRC_SILL = 344.55
OPENING_W = 253.00
OPENING_H = 586.80

GROUND_TOP = -0.05

# ---------------------------------------------------------------- change 1
STEP_NAME = "step_seam_w_c"
STEP_X = (1640.75, 1893.75)     # 253.00 deep, against seam_w_c's west face
STEP_CENTRE_Y = 5807.15         # arch_w_shallow_828's centre
STEP_W = 253.00
STEP_TOP = 172.25               # half of 344.60, measured up from -0.05

# ------------------------------------------------------------- changes 2/3
DOORS = [
    dict(tag="e_a", wall="seam_e_a", centre_y=6255.92, sill=364.62),
    dict(tag="47", wall="axis_47", centre_y=4247.65, sill=213.40),
]

STEP_OUTPUTS = (STEP_NAME,)


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


def cut_wall(wall, centre_y, sill, boxes):
    """Cut an x-normal wall for a _d195 and clone the arch head into it.

    Returns (pieces, heads) or (None, reason).
    """
    wx = span(wall, 0)
    wy = span(wall, 1)
    wz = span(wall, 2)

    oy0 = round(centre_y - OPENING_W / 2.0, 4)
    oy1 = round(centre_y + OPENING_W / 2.0, 4)
    head = round(sill + OPENING_H, 4)

    if oy0 < wy[0] or oy1 > wy[1]:
        return None, ("opening %.2f..%.2f is outside the wall %.2f..%.2f"
                      % (oy0, oy1, wy[0], wy[1]))
    if head > wz[1]:
        return None, ("head %.2f is above the wall top %.2f, short by %.2f"
                      % (head, wz[1], head - wz[1]))
    if sill < wz[0]:
        return None, ("sill %.2f is below the wall base %.2f"
                      % (sill, wz[0]))

    n = wall["name"]
    pieces = []
    if oy0 > wy[0]:
        pieces.append(box(n + "_s", wx, (wy[0], oy0), wz))
    if wy[1] > oy1:
        pieces.append(box(n + "_n", wx, (oy1, wy[1]), wz))
    if sill > wz[0]:
        pieces.append(box(n + "_under", wx, (oy0, oy1), (wz[0], sill)))
    if wz[1] > head:
        pieces.append(box(n + "_hdr", wx, (oy0, oy1), (head, wz[1])))

    cx = (wx[0] + wx[1]) / 2.0
    dx = cx - ARCH_SRC_X
    dy = centre_y - ARCH_SRC_Y
    dz = sill - ARCH_SRC_SILL

    heads = []
    for b in boxes:
        if not b["name"].startswith(ARCH_PREFIX):
            continue
        heads.append({
            "name": b["name"].replace(ARCH_PREFIX, "arch_" + n + "_", 1),
            "origin": [round(b["origin"][0] + dx, 4),
                       round(b["origin"][1] + dy, 4),
                       round(b["origin"][2] + dz, 4)],
            "extents": list(b["extents"]),
            "angles": list(b["angles"]),
            "material": b.get("material", MAT),
        })
    return (pieces, heads), (oy0, oy1, head, dx, dy, dz)


def main(path):
    with open(path) as f:
        plan = json.load(f)
    boxes = plan["boxes"]

    # ------------------------------------------------------------ cleanup
    present = set(b["name"] for b in boxes)
    drop = set()
    prefixes = []
    for n in STEP_OUTPUTS:
        drop.add(n)
        drop.add("m_" + n)
    for d in DOORS:
        # Only clear a door's outputs if its source wall is still there to
        # cut again. If the wall is gone the cut already happened, and
        # clearing would delete it with nothing to rebuild from.
        if d["wall"] not in present:
            continue
        for suffix in ("_s", "_n", "_under", "_hdr"):
            drop.add(d["wall"] + suffix)
            drop.add("m_" + d["wall"] + suffix)
        prefixes.append("arch_" + d["wall"] + "_")
        prefixes.append("m_arch_" + d["wall"] + "_")
    before = len(boxes)
    boxes[:] = [b for b in boxes
                if b["name"] not in drop
                and not any(b["name"].startswith(p) for p in prefixes)]
    if before != len(boxes):
        print("REBUILD: removed %d previous outputs" % (before - len(boxes)))

    by_name = {b["name"]: b for b in boxes}
    made = []

    # ---------------------------------------------------------- change 1
    s = box(STEP_NAME, STEP_X,
            (STEP_CENTRE_Y - STEP_W / 2.0, STEP_CENTRE_Y + STEP_W / 2.0),
            (GROUND_TOP, STEP_TOP))
    made.append(s)
    print("STEP %s: top %.2f, x %.2f..%.2f, y %.2f..%.2f"
          % (STEP_NAME, STEP_TOP, STEP_X[0], STEP_X[1],
             STEP_CENTRE_Y - STEP_W / 2.0, STEP_CENTRE_Y + STEP_W / 2.0))

    # -------------------------------------------------------- changes 2/3
    for d in DOORS:
        wall = by_name.get(d["wall"])
        if wall is None:
            print("SKIP %s: wall not in plan, already cut on a previous run"
                  % d["wall"])
            continue
        result, info = cut_wall(wall, d["centre_y"], d["sill"], boxes)
        if result is None:
            print("ABORT %s: %s" % (d["wall"], info))
            continue
        pieces, heads = result
        oy0, oy1, head, dx, dy, dz = info
        print("DOOR %s: opening y %.2f..%.2f, sill %.2f, head %.2f"
              % (d["wall"], oy0, oy1, d["sill"], head))
        print("     %d wall pieces, %d head pieces, offset %.2f / %.2f / %.2f"
              % (len(pieces), len(heads), dx, dy, dz))
        boxes[:] = [b for b in boxes
                    if b["name"] != d["wall"] and b["name"] != "m_" + d["wall"]]
        made.extend(pieces + heads)

    twins = [mirror_box(b, "m_" + b["name"]) for b in made]
    boxes.extend(made)
    boxes.extend(twins)
    print("batch4.py: added %d half boxes + %d twins, %d boxes in plan"
          % (len(made), len(twins), len(boxes)))

    with open(path, "w") as f:
        json.dump(plan, f, indent=1)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_full.json")
