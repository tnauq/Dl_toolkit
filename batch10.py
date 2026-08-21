#!/usr/bin/env python3
"""batch10.py - seventeenth build step, run after batch9.py.

Adds a corner platform in the inside corner of seam_gap_wall_n and
seam_w_c_n, at half the wall height measured from stitch_ground, with a
railing on its two open edges.

GEOMETRY

  seam_gap_wall_n  x 1466.95..1893.75, y 6485.10..6511.80, z 0.10..1280.30
  seam_w_c_n       x 1893.75..1920.45, y 5944.85..7262.45, z 0.10..1280.30
  stitch_ground    top -0.05

  The open quadrant is north of seam_gap_wall_n and west of seam_w_c_n,
  which is where both crosshairs were taken, so the platform runs -x and
  +y from the corner at (1893.75, 6511.80).

  Half the wall height from the ground plate is
  (-0.05 + 1280.30) / 2 = 640.125, taken as 640.15 so it matches the
  bridge pillar tops and stays on the 6.67 sub-grid.

  platform  533.40 square, 26.70 thick, top 640.15
            x 1360.35..1893.75, y 6511.80..7045.20
            (doubled from the original 266.70 square)
  rail_w    26.70 thick, full 533.40 length, top 700.15 (60 tall)
  rail_n    26.70 thick, 506.70 long so it butts the west rail rather
            than overlapping it, top 700.15

  Nothing supports the platform from below; it is a shelf on the two
  walls, like jump_platform.

Built on the half side only; the m_ twins are derived by the plan
transform (x' = 920.2 - x, y' = 12170.1 - y, yaw' = yaw + 180), so
symmetry is exact by construction.

Name-keyed and rerunnable: it deletes its own outputs and rebuilds them,
so the box count is stable across reruns.

Usage: python3 batch10.py docs/plans/dust2_full.json
"""

import json
import sys

CORNER_X = 1893.75      # seam_w_c_n west face
CORNER_Y = 6511.80      # seam_gap_wall_n north face
TOP = 640.15            # half of stitch_ground top to wall top
SIZE = 533.40
SLAB = 26.70
RAIL_H = 60.00

NAMES = ["corner_plat_n", "corner_plat_n_rail_w", "corner_plat_n_rail_n"]


def mirror(box):
    o = box["origin"]
    a = box.get("angles", [0.0, 0.0, 0.0])
    yaw = (a[1] + 180.0) % 360.0
    if yaw > 180.0:
        yaw -= 360.0
    return {
        "name": "m_" + box["name"],
        "origin": [round(920.2 - o[0], 4), round(12170.1 - o[1], 4), o[2]],
        "extents": list(box["extents"]),
        "angles": [a[0], yaw, a[2]],
    }


def build():
    x_lo = CORNER_X - SIZE
    y_hi = CORNER_Y + SIZE

    plat = {
        "name": "corner_plat_n",
        "origin": [round(x_lo + SIZE / 2, 4), round(CORNER_Y + SIZE / 2, 4),
                   round(TOP - SLAB / 2, 4)],
        "extents": [SIZE, SIZE, SLAB],
        "angles": [0.0, 0.0, 0.0],
    }

    rail_w = {
        "name": "corner_plat_n_rail_w",
        "origin": [round(x_lo + SLAB / 2, 4), round(CORNER_Y + SIZE / 2, 4),
                   round(TOP + RAIL_H / 2, 4)],
        "extents": [SLAB, SIZE, RAIL_H],
        "angles": [0.0, 0.0, 0.0],
    }

    n_len = round(SIZE - SLAB, 4)
    rail_n = {
        "name": "corner_plat_n_rail_n",
        "origin": [round(x_lo + SLAB + n_len / 2, 4), round(y_hi - SLAB / 2, 4),
                   round(TOP + RAIL_H / 2, 4)],
        "extents": [n_len, SLAB, RAIL_H],
        "angles": [0.0, 0.0, 0.0],
    }

    out = [plat, rail_w, rail_n]
    return out + [mirror(b) for b in out]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_full.json"
    with open(path) as f:
        plan = json.load(f)

    drop = set(NAMES) | {"m_" + n for n in NAMES}
    plan["boxes"] = [b for b in plan["boxes"] if b["name"] not in drop]

    made = build()
    plan["boxes"].extend(made)

    for b in made:
        o = b["origin"]
        e = b["extents"]
        print("%-24s o=[%.2f, %.2f, %.2f] e=[%.2f, %.2f, %.2f] top %.2f"
              % (b["name"], o[0], o[1], o[2], e[0], e[1], e[2], o[2] + e[2] / 2))

    with open(path, "w") as f:
        json.dump(plan, f, indent=1)

    print("added %d, boxes %d" % (len(made), len(plan["boxes"])))


if __name__ == "__main__":
    main()
