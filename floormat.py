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
Anything the model cannot reach but a player can goes in FORCE_FLOOR.

Idempotent: it sets the material outright, so a rerun on an unchanged
plan writes the same values. It records nothing, because there is nothing
to undo beyond setting the material back.

Usage: python3 floormat.py docs/plans/dust2_full.json
"""

import json
import sys

import walkcheck

FLOOR_MAT = "materials/dev/dev_measuregeneric01.vmat"
WALL_MAT = "materials/dev/reflectivity_30.vmat"

# A railing is a box that is narrower than the player AND stands proud.
# Width alone is not enough: a stair tread like axis_56 is 26.70 deep,
# the same as a railing is thick, and treads ARE floor. Height alone is
# not enough either, since plenty of wide boxes are tall. So a box is
# ruled out only when it is narrow in plan and tall enough to be a
# barrier rather than a step. A player CAN jump onto a 60-unit railing,
# which is why no jump height excludes these; the shape does.
MIN_TOP_WIDTH = 48.0    # player diameter, twice the viewer's 24 radius
MAX_STEP_RISE = 48.0    # anything taller than this is not a step

# Boxes a player can stand on but that are not floor by intent. Nothing
# geometric separates these: step_seam_w_c is a 253 cube from the ground
# to 172.25, wide enough to stand on and reached by dropping off t3_pad2
# at 344.60. Only a name can rule it out.
#
# m_ twins are added automatically, so name the half-side box only.
NOT_FLOOR = [
    "step_seam_w_c",
]

# Narrowest a top face may be and still count as a floor. A 26.70 railing
# cap is reachable, because a 60.00 rise is inside the 80.10 jump, but it
# is not somewhere anyone walks. Tightening JUMP_UP instead would break
# real 60-unit steps, so the test is width, not height: if you cannot fit
# on it, it is not a floor. 48.00 is the player diameter, 2 * RADIUS.
MIN_TOP_WIDTH = 48.0

# Boxes that ARE reachable and wide enough but are not meant to be walked
# on. No geometric rule catches these; they are a judgement call, so they
# are named. step_seam_w_c is a 253.00 block standing on the ground to
# 172.25, reachable only by dropping onto it from t3_pad2 at 344.60.
# m_ twins are added automatically.
# Floors the flood cannot get to on its own, crosshaired by hand.
#
# The walk model has no way across a horizontal gap: it steps between
# 4-adjacent columns only, so an island you reach by jumping ACROSS
# something stays unreachable however high JUMP_UP is set. Naming a box
# here does two things: it gets the floor material, and every standing
# cell on top of it becomes an extra flood SEED, so the rest of that
# floor is found normally. That matters here because these are large
# multifaceted areas, not single slabs.
#
# m_ twins are added automatically, so name the half-side box only.
FORCE_FLOOR = [
    "hex_plat_s",
    "axis_769",
    "xtun_up_room_d_floor",
    "bridge_floor_a",
    "corner_plat_n",
    "balcony_75",
    "jump_ledge_25",
    "jump_ledge_50",
]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_full.json"
    with open(path) as f:
        plan = json.load(f)

    lo, dims, solid, stand = walkcheck.build_grid(plan)
    seeds = walkcheck.seed_cells(plan, lo, dims, stand)

    forced = set()
    for n in FORCE_FLOOR:
        forced.add(n)
        forced.add("m_" + n)

    import numpy as np

    missing = forced - {b["name"] for b in plan["boxes"]}
    if missing:
        print("FORCE_FLOOR names not in plan: " + ", ".join(sorted(missing)))

    extra = 0
    for b in plan["boxes"]:
        if b["name"] not in forced:
            continue
        i0, i1, inside = walkcheck.box_range(b, lo, dims)
        if i0 is None:
            continue
        sub = stand[i0[0]:i1[0] + 1, i0[1]:i1[1] + 1, i0[2] + 1:i1[2] + 2]
        msk = inside[:, :, :sub.shape[2]]
        for c in np.argwhere(sub & msk):
            seeds.append((i0[0] + c[0], i0[1] + c[1], i0[2] + 1 + c[2]))
            extra += 1
    if extra:
        print("forced seeds %d from %d named boxes" % (extra, len(forced)))

    reach = walkcheck.flood(stand, dims, seeds)

    excluded = set()
    for n in NOT_FLOOR:
        excluded.add(n)
        excluded.add("m_" + n)
    gone = excluded - {b["name"] for b in plan["boxes"]}
    if gone:
        print("NOT_FLOOR names not in plan: " + ", ".join(sorted(gone)))

    floors = 0
    walls = 0
    narrow = 0
    for b in plan["boxes"]:
        i0, i1, inside = walkcheck.box_range(b, lo, dims)
        is_floor = False
        if i0 is not None:
            sub = reach[i0[0]:i1[0] + 1, i0[1]:i1[1] + 1, i0[2] + 1:i1[2] + 2]
            m = inside[:, :, :sub.shape[2]]
            if sub.shape[2] and (sub & m).any():
                is_floor = True
        if (is_floor
                and min(b["extents"][0], b["extents"][1]) < MIN_TOP_WIDTH
                and b["extents"][2] > MAX_STEP_RISE):
            is_floor = False
            narrow += 1
        if b["name"] in excluded:
            is_floor = False

        b["material"] = FLOOR_MAT if is_floor else WALL_MAT
        if is_floor:
            floors += 1
        else:
            walls += 1

    with open(path, "w") as f:
        json.dump(plan, f, indent=1)

    print("floor boxes %d, other boxes %d, total %d" % (floors, walls, floors + walls))
    print("ruled out: %d too narrow (under %.2f), %d named in NOT_FLOOR"
          % (narrow, MIN_TOP_WIDTH, len(excluded)))
    print("floor material %s" % FLOOR_MAT)


if __name__ == "__main__":
    main()
