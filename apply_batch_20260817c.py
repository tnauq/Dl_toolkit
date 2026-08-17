#!/usr/bin/env python3
"""
Manual tail step: third batch from the 2026-08-17 crosshair session.
Runs after apply_batch_20260817b.py. Name-keyed and idempotent.

op 1: cut an arch door through axis_574 at y = 1312, sill on the axis_551
      floor top (213.3). The arch itself is cloned from the d733 assembly,
      which sits in a wall of the same thickness and the same normal (x),
      so the pieces translate straight across with no rotation.
op 2: box on merged_721 at (-1744, 1168), footprint taken from
      angled-wall_656 and height set to half of that object's top elevation.

Usage:  python3 apply_batch_20260817c.py docs/plans/dust2_half.json
"""
import json, sys, copy

MAT = "materials/dev/reflectivity_30.vmat"

DOOR_W = 253.0      # standard opening width (d479, d191, d733)
DOOR_H = 586.8      # standard opening height

# --- op 1 parameters -------------------------------------------------------
SRC = "d733"                  # template assembly
DST = "d574"
WALL = "axis_574"
WALL_X = -613.5               # centre of axis_574 in x (unchanged)
OPEN_Y = 1312.0               # crosshair 1
FLOOR_Z = 213.3               # crosshair 2, axis_551 top
WALL_Z = (0.1, 1280.3)        # existing axis_574 z span
SRC_WALL_X = -520.1           # d733 wall centre
SRC_OPEN_Y = 3020.0           # d733 opening centre
SRC_HDR_BOT = 1240.2          # d733 header underside

OPEN_Y0, OPEN_Y1 = OPEN_Y - DOOR_W / 2.0, OPEN_Y + DOOR_W / 2.0
HDR_BOT = FLOOR_Z + DOOR_H

# --- op 2 parameters -------------------------------------------------------
BOX2_NAME = "axis_721_block"
BOX2_CENTRE = (-1744.0, 1168.0)
BOX2_REF = "angled-wall_656"
BOX2_BASE_Z = 213.3

def box(name, x, y, z):
    return {"name": name,
            "origin": [round((x[0] + x[1]) / 2.0, 1), round((y[0] + y[1]) / 2.0, 1), round((z[0] + z[1]) / 2.0, 1)],
            "extents": [round(x[1] - x[0], 1), round(y[1] - y[0], 1), round(z[1] - z[0], 1)],
            "angles": [0.0, 0.0, 0.0], "material": MAT}

def main(path):
    plan = json.load(open(path))
    boxes = plan["boxes"]
    idx = {b["name"]: i for i, b in enumerate(boxes)}
    log = []

    def add(nb):
        if nb["name"] in idx:
            log.append("skip add %s (present)" % nb["name"])
            return
        boxes.append(copy.deepcopy(nb))
        idx[nb["name"]] = len(boxes) - 1
        log.append("add %s" % nb["name"])

    # ---- op 1 -------------------------------------------------------------
    if WALL not in idx:
        log.append("FAIL %s absent" % WALL)
    else:
        w = boxes[idx[WALL]]
        lo = w["origin"][1] - w["extents"][1] / 2.0
        hi = w["origin"][1] + w["extents"][1] / 2.0
        if abs(hi - OPEN_Y0) < 0.1:
            log.append("skip trim %s (already %.1f)" % (WALL, OPEN_Y0))
        elif abs(hi - 2667.2) > 0.1:
            log.append("FAIL trim %s: expected y max 2667.2, found %.1f" % (WALL, hi))
        else:
            w["origin"][1] = round((lo + OPEN_Y0) / 2.0, 1)
            w["extents"][1] = round(OPEN_Y0 - lo, 1)
            log.append("trim %s y max 2667.2 -> %.1f" % (WALL, OPEN_Y0))

        wx = (WALL_X - 13.35, WALL_X + 13.35)
        add(box(WALL + "_far", wx, (OPEN_Y1, 2667.2), WALL_Z))
        add(box(WALL + "_low", wx, (OPEN_Y0, OPEN_Y1), (WALL_Z[0], FLOOR_Z)))
        add(box(WALL + "_hdr", wx, (OPEN_Y0, OPEN_Y1), (HDR_BOT, WALL_Z[1])))

        dx = WALL_X - SRC_WALL_X
        dy = OPEN_Y - SRC_OPEN_Y
        dz = HDR_BOT - SRC_HDR_BOT
        n = 0
        for b in list(boxes):
            if not b["name"].endswith("_" + SRC):
                continue
            if b["name"].startswith("axis_"):
                continue          # wall/header/sill pieces, rebuilt above
            nb = copy.deepcopy(b)
            nb["name"] = b["name"][: -len(SRC)] + DST
            nb["origin"] = [round(b["origin"][0] + dx, 1),
                            round(b["origin"][1] + dy, 1),
                            round(b["origin"][2] + dz, 1)]
            add(nb)
            n += 1
        log.append("arch pieces cloned from %s: %d" % (SRC, n))

    # ---- op 2 -------------------------------------------------------------
    if BOX2_REF not in idx:
        log.append("FAIL %s absent" % BOX2_REF)
    else:
        r = boxes[idx[BOX2_REF]]
        sx, sy, _ = r["extents"]
        # half of the reference's TOP elevation, not half its own height
        h = (r["origin"][2] + r["extents"][2] / 2.0) / 2.0
        add(box(BOX2_NAME,
                (BOX2_CENTRE[0] - sx / 2.0, BOX2_CENTRE[0] + sx / 2.0),
                (BOX2_CENTRE[1] - sy / 2.0, BOX2_CENTRE[1] + sy / 2.0),
                (BOX2_BASE_Z, BOX2_BASE_Z + h)))

    json.dump(plan, open(path, "w"), indent=1)
    for line in log:
        print(line)
    print("boxes: %d" % len(boxes))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_half.json")
