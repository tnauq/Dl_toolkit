#!/usr/bin/env python3
"""batch2.py - eighth build step, run after thin.py.

Four changes, each applied on the half side and then mirrored, so both
sides of the map match:

  1. axis_62 trimmed flush with seam_wall_restore's north face (5094.30).
  2. link_34_pillar cut for a _d195 arched opening centred on the bridge
     floor hole at y 6085.05, sill on the pillar floor. The pillar is
     replaced by three pieces and the 16-piece arch_w_* head is cloned in.
  3. ramp-slab_367's under-void filled with a pitch-matched slab.
  4. ramp_42_27_down's under-void filled the same way.

Every box this writes is generated on the half side and the m_ twin is
derived by the plan transform (x' = 920.2 - x, y' = 12170.1 - y,
yaw' = yaw + 180), so symmetry is exact by construction.

Name-keyed and rerunnable. It deletes its own outputs first and rebuilds
them, so the box count is stable across reruns. The axis_62 trim records
its pre-edit values under _batch2_pre and skips if already applied.

Usage: python3 batch2.py docs/plans/dust2_full.json
"""

import json
import math
import sys

MAT = "materials/dev/reflectivity_30.vmat"

MIRROR_X = 920.2
MIRROR_Y = 12170.1

# ---------------------------------------------------------------- change 1
AXIS62_NEW_NORTH = 5094.30   # seam_wall_restore north face after thin.py

# ---------------------------------------------------------------- change 2
PILLAR = "link_34_pillar"
ARCH_PREFIX = "arch_w_"      # 16-piece _d195 head, source wall is x-normal
ARCH_SRC_X = 1907.10         # source wall centreline
ARCH_SRC_Y = 5818.40         # source opening centre
ARCH_SRC_SILL = 344.55       # source sill top
OPENING_W = 253.00           # _d195 width
OPENING_H = 586.80           # _d195 height
TARGET_Y = 6085.05           # centre of the bridge floor hole
TARGET_SILL = 0.00           # pillar floor

# ---------------------------------------------------------------- changes 3/4
FILL_T = 186.90              # 7 grid units, enough to seal both wedges
FILLS = [
    ("ramp-slab_367", "fill_under_367"),
    ("ramp_42_27_down", "fill_under_42_27"),
]


def mirror_box(b, name):
    """Twin of b under the plan transform."""
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


def box(name, xr, yr, zr):
    """Axis-aligned box from min/max pairs."""
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


def slab_normal(pitch, yaw):
    """Local +z of a slab, i.e. the direction its top face looks."""
    p = math.radians(pitch)
    y = math.radians(yaw)
    return (math.cos(y) * math.sin(p),
            math.sin(y) * math.sin(p),
            math.cos(p))


def main(path):
    with open(path) as f:
        plan = json.load(f)

    boxes = plan["boxes"]
    by_name = {b["name"]: b for b in boxes}
    made = []

    # ---------------------------------------------------------- change 1
    for name, hold_low in (("axis_62", True), ("m_axis_62", False)):
        b = by_name.get(name)
        if b is None:
            print("SKIP %s: not in plan" % name)
            continue
        if "_batch2_pre" in b:
            print("SKIP %s: already trimmed" % name)
            continue
        y0 = b["origin"][1] - b["extents"][1] / 2.0
        y1 = b["origin"][1] + b["extents"][1] / 2.0
        if hold_low:
            new0, new1 = y0, AXIS62_NEW_NORTH
        else:
            new0, new1 = MIRROR_Y - AXIS62_NEW_NORTH, y1
        if new1 - new0 <= 0:
            print("SKIP %s: trim would delete the box" % name)
            continue
        b["_batch2_pre"] = {"origin": list(b["origin"]),
                            "extents": list(b["extents"])}
        b["origin"][1] = round((new0 + new1) / 2.0, 4)
        b["extents"][1] = round(new1 - new0, 4)
        print("TRIM %s: y %.2f..%.2f -> %.2f..%.2f (removed %.2f)"
              % (name, y0, y1, new0, new1, (y1 - y0) - (new1 - new0)))

    # ---------------------------------------------------------- change 2
    src = by_name.get(PILLAR)
    made_names = (PILLAR + "_s_cut", PILLAR + "_n_cut", PILLAR + "_lintel")
    prev = [b for b in boxes
            if b["name"] in made_names
            or b["name"] in tuple("m_" + n for n in made_names)
            or b["name"].startswith("arch2_")
            or b["name"].startswith("m_arch2_")]
    if src is None and prev:
        # Already cut on a previous run: the source pillar is gone and the
        # replacement pieces are present. Leave them exactly as they are.
        print("SKIP change 2: %s already cut (%d pieces present)"
              % (PILLAR, len(prev)))
    elif src is None:
        print("SKIP change 2: %s not in plan and no source to cut" % PILLAR)
    else:
        if prev:
            keep = set(id(b) for b in prev)
            boxes[:] = [b for b in boxes if id(b) not in keep]
            by_name = {b["name"]: b for b in boxes}
            print("REBUILD: removed %d previous change-2 boxes" % len(prev))
            src = by_name.get(PILLAR)
        px = src["origin"][0]
        pe = src["extents"][0]
        x0, x1 = px - pe / 2.0, px + pe / 2.0
        py0 = src["origin"][1] - src["extents"][1] / 2.0
        py1 = src["origin"][1] + src["extents"][1] / 2.0
        pz0 = src["origin"][2] - src["extents"][2] / 2.0
        pz1 = src["origin"][2] + src["extents"][2] / 2.0

        oy0 = TARGET_Y - OPENING_W / 2.0
        oy1 = TARGET_Y + OPENING_W / 2.0
        oz1 = TARGET_SILL + OPENING_H

        if oy0 < py0 or oy1 > py1:
            print("ABORT change 2: opening %.2f..%.2f is outside the pillar "
                  "%.2f..%.2f" % (oy0, oy1, py0, py1))
        elif oz1 > pz1:
            print("ABORT change 2: opening head %.2f is above the pillar top "
                  "%.2f" % (oz1, pz1))
        else:
            pieces = [
                box(PILLAR + "_s_cut", (x0, x1), (py0, oy0), (pz0, pz1)),
                box(PILLAR + "_n_cut", (x0, x1), (oy1, py1), (pz0, pz1)),
                box(PILLAR + "_lintel", (x0, x1), (oy0, oy1), (oz1, pz1)),
            ]
            print("CUT %s: opening y %.2f..%.2f, z %.2f..%.2f"
                  % (PILLAR, oy0, oy1, TARGET_SILL, oz1))
            print("     south remnant %.2f, north remnant %.2f, lintel %.2f"
                  % (oy0 - py0, py1 - oy1, pz1 - oz1))

            dx = px - ARCH_SRC_X
            dy = TARGET_Y - ARCH_SRC_Y
            dz = TARGET_SILL - ARCH_SRC_SILL
            heads = []
            for b in list(boxes):
                if not b["name"].startswith(ARCH_PREFIX):
                    continue
                c = {
                    "name": b["name"].replace(ARCH_PREFIX, "arch2_", 1),
                    "origin": [round(b["origin"][0] + dx, 4),
                               round(b["origin"][1] + dy, 4),
                               round(b["origin"][2] + dz, 4)],
                    "extents": list(b["extents"]),
                    "angles": list(b["angles"]),
                    "material": b.get("material", MAT),
                }
                heads.append(c)
            print("CLONE: %d arch head pieces, offset %.2f / %.2f / %.2f"
                  % (len(heads), dx, dy, dz))

            boxes[:] = [b for b in boxes if b["name"] != PILLAR
                        and b["name"] != "m_" + PILLAR]
            made.extend(pieces + heads)

    # ------------------------------------------------------- changes 3/4
    boxes[:] = [b for b in boxes
                if not (b["name"].startswith("fill_under_")
                        or b["name"].startswith("m_fill_under_"))]
    for ramp_name, fill_name in FILLS:
        r = by_name.get(ramp_name)
        if r is None:
            print("SKIP %s: not in plan" % fill_name)
            continue
        pitch, yaw, roll = r["angles"]
        n = slab_normal(pitch, yaw)
        step = (r["extents"][2] + FILL_T) / 2.0
        f = {
            "name": fill_name,
            "origin": [round(r["origin"][0] - step * n[0], 4),
                       round(r["origin"][1] - step * n[1], 4),
                       round(r["origin"][2] - step * n[2], 4)],
            "extents": [r["extents"][0], r["extents"][1], FILL_T],
            "angles": [pitch, yaw, roll],
            "material": MAT,
        }
        made.append(f)
        print("FILL %s: under %s, thickness %.2f, pitch %.4f"
              % (fill_name, ramp_name, FILL_T, pitch))

    # --------------------------------------------------------- mirroring
    twins = []
    for b in made:
        if b["name"].startswith("m_"):
            continue
        twins.append(mirror_box(b, "m_" + b["name"]))

    boxes.extend(made)
    boxes.extend(twins)
    print("batch2.py: added %d half boxes + %d twins, %d boxes in plan"
          % (len(made), len(twins), len(boxes)))

    with open(path, "w") as f:
        json.dump(plan, f, indent=1)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_full.json")
