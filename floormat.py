#!/usr/bin/env python3
"""floormat.py - nineteenth build step, run after batch11.py.

Gives every box that a player actually stands on a different grey dev
material, so floors read against walls in the viewer and in Hammer.

HOW A FLOOR IS IDENTIFIED
Not by shape. A box is a floor if the walkability pass says a reachable
standing cell sits directly on top of one of its voxels. That means
ramps, ledges, platforms and stair boxes are all caught, and a wall top
that nobody can get to is not. The pass is the one in walkcheck.py, at
26.70 voxels with 98.00 of headroom and a one-voxel step.

Consequence worth knowing: a surface that is unreachable today gets the
wall material, so re-run this after any change that opens a new route.

Idempotent: it sets the material outright, so a rerun on an unchanged
plan writes the same values. It records nothing, because there is nothing
to undo beyond setting the material back.

Usage: python3 floormat.py docs/plans/dust2_full.json
"""

import json
import sys

import walkcheck

FLOOR_MAT = "materials/dev/reflectivity_50.vmat"
WALL_MAT = "materials/dev/reflectivity_30.vmat"


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_full.json"
    with open(path) as f:
        plan = json.load(f)

    lo, dims, solid, stand = walkcheck.build_grid(plan)
    seeds = walkcheck.seed_cells(plan, lo, dims, stand)
    reach = walkcheck.flood(stand, dims, seeds)

    floors = 0
    walls = 0
    for b in plan["boxes"]:
        i0, i1, inside = walkcheck.box_range(b, lo, dims)
        is_floor = False
        if i0 is not None:
            sub = reach[i0[0]:i1[0] + 1, i0[1]:i1[1] + 1, i0[2] + 1:i1[2] + 2]
            m = inside[:, :, :sub.shape[2]]
            if sub.shape[2] and (sub & m).any():
                is_floor = True
        b["material"] = FLOOR_MAT if is_floor else WALL_MAT
        if is_floor:
            floors += 1
        else:
            walls += 1

    with open(path, "w") as f:
        json.dump(plan, f, indent=1)

    print("floor boxes %d, other boxes %d, total %d" % (floors, walls, floors + walls))
    print("floor material %s" % FLOOR_MAT)


if __name__ == "__main__":
    main()
