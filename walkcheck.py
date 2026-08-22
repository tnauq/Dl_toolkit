#!/usr/bin/env python3
"""walkcheck.py - offline walkability check on a plan file.

Voxelises every box with true oriented-box tests, not AABBs, so ramps are
handled correctly, then flood fills standing positions from the
info_team_spawn entities.

MODEL
  voxel          26.70 on all three axes, matching the plan grid
  thin plates    a box thinner than one voxel on an axis is treated as one
                 voxel thick on that axis, so 13.30 stair treads register
  player height  98.00 (gen_man), 4 voxels of headroom
  step up        26.70, one voxel
  jump up        80.10, three voxels, from JUMP_UP below
  drop           400.50 max, 15 voxels
  moves          4-neighbour, no jumping

A cell is standable if its voxel is empty, the voxel below is solid, and
the voxels above are empty for the full player height.

This is a coarse model. A 26.70 voxel cannot see a gap narrower than
itself, so it will not find a doorway one unit too tight, and it treats
the step limit as exactly one voxel. Treat the island list as leads to
crosshair, not as proof.

Also importable: build_grid() and flood() are used by floormat.py.

Usage: python3 walkcheck.py docs/plans/dust2_full.json [report.txt]
"""

import json
import math
import sys
from collections import deque

VOX = 26.7
PLAYER_H = 98.0
STEP_UP = 1
MAX_DROP = 15
# Jump height, in units. Deadlock's geometry is 1:16 imperial, one unit
# to 0.75 inch, where Source is 1:12. Source's 56-unit jump is therefore
# 56 * 16/12 = 74.70 here. Converted DOWN to whole voxels, so it buys 2
# voxels, 53.40. An earlier value of 93 came from scaling against a
# 120-unit hero; the gen_man model is 98, which is also what PLAYER_H
# above uses.
JUMP_UP = 74.7
JUMP_VOX = int(JUMP_UP // VOX)


def rot(angles):
    p, y, r = [math.radians(v) for v in angles]
    cy, sy = math.cos(y), math.sin(y)
    cp, sp = math.cos(p), math.sin(p)
    cr, sr = math.cos(r), math.sin(r)
    return [
        [cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
        [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
        [-sp, cp * sr, cp * cr],
    ]


def box_range(box, lo, dims):
    """Voxel index window and inside-mask for one box."""
    import numpy as np

    o = box["origin"]
    e = box["extents"]
    R = rot(box.get("angles", [0.0, 0.0, 0.0]))
    cs = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                v = [sx * e[0] / 2, sy * e[1] / 2, sz * e[2] / 2]
                cs.append([o[i] + sum(R[i][j] * v[j] for j in range(3))
                           for i in range(3)])
    clo = [min(c[i] for c in cs) for i in range(3)]
    chi = [max(c[i] for c in cs) for i in range(3)]
    i0 = [max(0, int((clo[i] - VOX - lo[i]) / VOX)) for i in range(3)]
    i1 = [min(dims[i] - 1, int((chi[i] + VOX - lo[i]) / VOX) + 1) for i in range(3)]
    if any(i1[i] < i0[i] for i in range(3)):
        return None, None, None
    xs = lo[0] + (np.arange(i0[0], i1[0] + 1) + 0.5) * VOX
    ys = lo[1] + (np.arange(i0[1], i1[1] + 1) + 0.5) * VOX
    zs = lo[2] + (np.arange(i0[2], i1[2] + 1) + 0.5) * VOX
    X, Y, Z = np.meshgrid(xs - o[0], ys - o[1], zs - o[2], indexing="ij")
    inside = np.ones(X.shape, dtype=bool)
    for k in range(3):
        local = X * R[0][k] + Y * R[1][k] + Z * R[2][k]
        # A voxel is solid when its CENTRE is inside the box, which misses a
        # plate thinner than a voxel unless a centre happens to land in it.
        # Half the 13.30 stair treads disappeared that way. So the half-extent
        # is floored at half a voxel on any axis thinner than one voxel, and
        # left alone on every other axis, which captures thin plates without
        # inflating real geometry or closing a gap.
        inside &= np.abs(local) <= max(e[k] / 2, VOX / 2)
    return i0, i1, inside


def build_grid(plan):
    """Returns lo, dims, solid, stand."""
    import numpy as np

    boxes = plan["boxes"]
    lo = [1e18] * 3
    hi = [-1e18] * 3
    for b in boxes:
        o = b["origin"]
        e = b["extents"]
        R = rot(b.get("angles", [0.0, 0.0, 0.0]))
        for sx in (-1, 1):
            for sy in (-1, 1):
                for sz in (-1, 1):
                    v = [sx * e[0] / 2, sy * e[1] / 2, sz * e[2] / 2]
                    for i in range(3):
                        w = o[i] + sum(R[i][j] * v[j] for j in range(3))
                        lo[i] = min(lo[i], w)
                        hi[i] = max(hi[i], w)
    lo = [v - VOX for v in lo]
    hi = [v + VOX for v in hi]
    dims = [int(math.ceil((hi[i] - lo[i]) / VOX)) + 1 for i in range(3)]

    solid = np.zeros(dims, dtype=bool)
    for b in boxes:
        i0, i1, inside = box_range(b, lo, dims)
        if i0 is None:
            continue
        solid[i0[0]:i1[0] + 1, i0[1]:i1[1] + 1, i0[2]:i1[2] + 1] |= inside

    head = int(math.ceil(PLAYER_H / VOX))
    empty = ~solid
    clear = empty.copy()
    for k in range(1, head):
        clear[:, :, :-k] &= empty[:, :, k:]
        clear[:, :, -k:] = False
    stand = np.zeros_like(clear)
    stand[:, :, 1:] = clear[:, :, 1:] & solid[:, :, :-1]
    return lo, dims, solid, stand


def seed_cells(plan, lo, dims, stand):
    seeds = []
    for ent in plan.get("entities", []):
        if ent.get("classname") != "info_team_spawn":
            continue
        o = ent["origin"]
        ix = int((o[0] - lo[0]) / VOX)
        iy = int((o[1] - lo[1]) / VOX)
        best = None
        for iz in range(dims[2]):
            if stand[ix, iy, iz]:
                if best is None or abs(lo[2] + iz * VOX - o[2]) < abs(lo[2] + best * VOX - o[2]):
                    best = iz
        if best is not None:
            seeds.append((ix, iy, best))
    return seeds


def flood(stand, dims, seeds):
    import numpy as np

    reach = np.zeros_like(stand)
    q = deque()
    for s in seeds:
        if stand[s] and not reach[s]:
            reach[s] = True
            q.append(s)
    nb = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    while q:
        x, y, z = q.popleft()
        for dx, dy in nb:
            nx, ny = x + dx, y + dy
            if nx < 0 or ny < 0 or nx >= dims[0] or ny >= dims[1]:
                continue
            # Search from the highest cell a jump can reach down to the
            # deepest survivable drop, and take the FIRST hit: that is the
            # surface you would actually land on coming from this cell.
            for nz in range(z + max(STEP_UP, JUMP_VOX), z - MAX_DROP - 1, -1):
                if nz < 0 or nz >= dims[2]:
                    continue
                if stand[nx, ny, nz]:
                    if not reach[nx, ny, nz]:
                        reach[nx, ny, nz] = True
                        q.append((nx, ny, nz))
                    break
    return reach


def main():
    import numpy as np

    path = sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_full.json"
    out_path = sys.argv[2] if len(sys.argv) > 2 else None
    with open(path) as f:
        plan = json.load(f)

    lo, dims, solid, stand = build_grid(plan)
    seeds = seed_cells(plan, lo, dims, stand)
    reach = flood(stand, dims, seeds)

    # roofed vs open sky, so rooftops do not count against the score
    above = np.flip(np.maximum.accumulate(np.flip(solid, 2), 2), 2)
    covered = np.zeros_like(stand)
    covered[:, :, :-1] = above[:, :, 1:]

    tot = int(stand.sum())
    nre = int(reach.sum())
    cov = int((stand & covered).sum())
    cre = int((reach & covered).sum())

    lines = [
        "grid %s at %.2f, origin %s" % (dims, VOX, [round(v, 1) for v in lo]),
        "seeds %s" % (seeds,),
        "standable %d, reachable %d (%.1f%%)" % (tot, nre, 100.0 * nre / max(1, tot)),
        "roofed standable %d, roofed reachable %d (%.1f%%)"
        % (cov, cre, 100.0 * cre / max(1, cov)),
    ]

    left = stand & ~reach & covered
    seen = np.zeros_like(left)
    islands = []
    for start in map(tuple, np.argwhere(left)):
        if seen[start]:
            continue
        comp = []
        seen[start] = True
        dq = deque([start])
        while dq:
            x, y, z = dq.popleft()
            comp.append((x, y, z))
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = x + dx, y + dy
                if nx < 0 or ny < 0 or nx >= dims[0] or ny >= dims[1]:
                    continue
                for nz in range(z + max(STEP_UP, JUMP_VOX), z - MAX_DROP - 1, -1):
                    if nz < 0 or nz >= dims[2]:
                        continue
                    if stand[nx, ny, nz]:
                        if left[nx, ny, nz] and not seen[nx, ny, nz]:
                            seen[nx, ny, nz] = True
                            dq.append((nx, ny, nz))
                        break
        islands.append(comp)
    islands.sort(key=len, reverse=True)

    lines.append("roofed unreachable islands: %d" % len(islands))
    for comp in islands[:20]:
        xs = [c[0] for c in comp]
        ys = [c[1] for c in comp]
        zs = [c[2] for c in comp]
        lines.append("  %5d cells  x %8.1f..%8.1f  y %9.1f..%9.1f  z %7.1f..%7.1f"
                     % (len(comp),
                        lo[0] + min(xs) * VOX, lo[0] + max(xs) * VOX,
                        lo[1] + min(ys) * VOX, lo[1] + max(ys) * VOX,
                        lo[2] + min(zs) * VOX, lo[2] + max(zs) * VOX))

    report = "\n".join(lines)
    print(report)
    if out_path:
        with open(out_path, "w") as f:
            f.write(report + "\n")


if __name__ == "__main__":
    main()
