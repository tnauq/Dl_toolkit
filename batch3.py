#!/usr/bin/env python3
"""batch3.py - ninth build step, run after batch2.py.

  1. seam_gap_wall_n: closes the ground-level gap north of the bridge,
     running from bridge_pillar_ne's outside corner east to seam_w_c_n,
     on the same line as bridge_wall_n_pier4.
  2. jump_platform: a shelf on the axis_43 / seam_w_a wall line at 75%
     of the ground-to-wall-top height, centred between seam_wall_restore
     and seam_w_s.
  3. jump_ledge_25: a ledge on seam_wall_restore's north face at 25%.
  4. jump_ledge_50: a ledge on seam_w_s's south face at 50%.

The arch doorway and balcony are deliberately NOT built here. See the
note at the bottom of this docstring.

Every box is generated on the half side and its m_ twin derived by the
plan transform (x' = 920.2 - x, y' = 12170.1 - y, yaw' = yaw + 180), so
symmetry is exact by construction. Name-keyed: the script deletes its own
outputs and rebuilds them, so the box count is stable across reruns.

Height reference: stitch_ground top -0.05, axis_43 top 1280.30, so the
difference is 1280.35. 25/50/75 percent land on 320.04 / 640.13 / 960.21;
the map's existing levels 320.05 / 640.15 / 960.20 are used instead, all
within 0.02, so the new surfaces line up with what is already there.

NOT BUILT: the doorway needs 586.80 of headroom above its sill. A sill at
960.20 leaves 320.10 before the wall top at 1280.30, so a standard _d195
will not fit and neither will anything a hero can walk through. Left for
the next pass once the tradeoff is chosen.

Usage: python3 batch3.py docs/plans/dust2_full.json
"""

import json
import sys

MAT = "materials/dev/reflectivity_30.vmat"
MIRROR_X = 920.2
MIRROR_Y = 12170.1

GROUND_TOP = -0.05
WALL_TOP = 1280.30

# ---------------------------------------------------------------- change 1
GAP_WALL = dict(
    name="seam_gap_wall_n",
    x=(1466.95, 1893.75),   # bridge_pillar_ne east face to seam_w_c_n west face
    y=(6485.10, 6511.80),   # same line as bridge_wall_n_pier4
    z=(0.10, 1280.30),
)

# ------------------------------------------------------------- changes 2-4
BAY_X = (2507.15, 2773.85)  # 266.7 deep, hard against the axis_43 wall face
CENTRE_Y = 5376.30          # midpoint of seam_wall_restore 5094.30
                            # and seam_w_s 5658.30
PLATFORM_W = 400.10
LEDGE_D = 133.35
THICK = 26.70

LEVEL_25 = 320.05
LEVEL_50 = 640.15
LEVEL_75 = 960.20

SEAM_RESTORE_N = 5094.30    # seam_wall_restore north face
SEAM_W_S_S = 5658.30        # seam_w_s south face

OUTPUTS = ("seam_gap_wall_n", "jump_platform",
           "jump_ledge_25", "jump_ledge_50")


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


def main(path):
    with open(path) as f:
        plan = json.load(f)
    boxes = plan["boxes"]

    drop = set(OUTPUTS) | set("m_" + n for n in OUTPUTS)
    before = len(boxes)
    boxes[:] = [b for b in boxes if b["name"] not in drop]
    if before != len(boxes):
        print("REBUILD: removed %d previous outputs" % (before - len(boxes)))

    by_name = {b["name"]: b for b in boxes}
    made = []

    # ---------------------------------------------------------- change 1
    for dep in ("bridge_pillar_ne", "seam_w_c_n"):
        if dep not in by_name:
            print("WARN: %s not in plan, gap wall may not meet it" % dep)
    w = box(GAP_WALL["name"], GAP_WALL["x"], GAP_WALL["y"], GAP_WALL["z"])
    made.append(w)
    print("WALL %s: x %.2f..%.2f, y %.2f..%.2f, z %.2f..%.2f"
          % (w["name"], GAP_WALL["x"][0], GAP_WALL["x"][1],
             GAP_WALL["y"][0], GAP_WALL["y"][1],
             GAP_WALL["z"][0], GAP_WALL["z"][1]))

    # ---------------------------------------------------------- change 2
    py0 = CENTRE_Y - PLATFORM_W / 2.0
    py1 = CENTRE_Y + PLATFORM_W / 2.0
    p = box("jump_platform", BAY_X, (py0, py1), (LEVEL_75 - THICK, LEVEL_75))
    made.append(p)
    print("PLATFORM jump_platform: top %.2f, y %.2f..%.2f, depth %.2f"
          % (LEVEL_75, py0, py1, BAY_X[1] - BAY_X[0]))

    # -------------------------------------------------------- changes 3/4
    l25 = box("jump_ledge_25", BAY_X,
              (SEAM_RESTORE_N, SEAM_RESTORE_N + LEDGE_D),
              (LEVEL_25 - THICK, LEVEL_25))
    l50 = box("jump_ledge_50", BAY_X,
              (SEAM_W_S_S - LEDGE_D, SEAM_W_S_S),
              (LEVEL_50 - THICK, LEVEL_50))
    made.extend([l25, l50])
    print("LEDGE jump_ledge_25: top %.2f on seam_wall_restore, y %.2f..%.2f"
          % (LEVEL_25, SEAM_RESTORE_N, SEAM_RESTORE_N + LEDGE_D))
    print("LEDGE jump_ledge_50: top %.2f on seam_w_s, y %.2f..%.2f"
          % (LEVEL_50, SEAM_W_S_S - LEDGE_D, SEAM_W_S_S))

    gap_y = (SEAM_W_S_S - LEDGE_D) - (SEAM_RESTORE_N + LEDGE_D)
    print("     ledge to ledge: rise %.2f, horizontal gap %.2f"
          % (LEVEL_50 - LEVEL_25, gap_y))
    print("     ledge_50 to platform: rise %.2f, horizontal gap %.2f"
          % (LEVEL_75 - LEVEL_50, (SEAM_W_S_S - LEDGE_D) - py1))

    twins = [mirror_box(b, "m_" + b["name"]) for b in made]
    boxes.extend(made)
    boxes.extend(twins)
    print("batch3.py: added %d half boxes + %d twins, %d boxes in plan"
          % (len(made), len(twins), len(boxes)))

    with open(path, "w") as f:
        json.dump(plan, f, indent=1)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_full.json")
