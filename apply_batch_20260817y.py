#!/usr/bin/env python3
"""
Manual tail step: twenty-fifth batch from the 2026-08-17 crosshair session.
Runs after apply_batch_20260817x.py. Name-keyed and idempotent.

op 1: drop shaft from the spawn room floor into a tunnel at pit level,
      running north under the southern platform and opening into the
      hexagon through a big arch in hex_wall_s.
op 2: pit cover, following the Patron pit references: a low central dais,
      a ring wall inboard of the perimeter broken by six gaps, and six
      chunky blocks outboard of the gaps.

Usage:  python3 apply_batch_20260817y.py docs/plans/dust2_half.json
"""
import json, math, sys, copy

MAT = "materials/dev/reflectivity_30.vmat"

R = 1600.25
A = R * math.sqrt(3) / 2.0
CX, CY = 0.0, -813.5 - R - A
PIT = 426.8                       # hexagon floor top
WALL_T = 26.7
PLAT_TOP = 1067.0                 # spawn room floor top
WALL_DIST = A + WALL_T / 2.0
S_WALL_Y = CY - WALL_DIST         # hex_wall_s centre line

BORE = 400.1
HALF = BORE / 2.0
JAMB_OUT, JAMB_IN = 200.05, 165.2
DOOR_H = 586.8
HEAD = PIT + DOOR_H               # 1013.6, tunnel ceiling and arch head
SPRING = PIT + 485.0

# shaft, cut through hex_plat_s
SHX = (-HALF, HALF)
SHY = (-6300.05, -5899.95)
PLAT_Y = (-6479.2, -5198.8)
PLAT_X = (-1177.45, 1177.45)

SRC_TAG = "_d468"
SRC_CX, SRC_CY, SRC_SILL = 0.0, -813.5, 426.8

# pit cover
DAIS_R = 480.1
DAIS_A = DAIS_R * math.sqrt(3) / 2.0
DAIS_TOP = PIT + 106.7
RING_D = 900.0                    # apothem of the ring wall
RING_L = 800.0
RING_T = 53.4
RING_TOP = PIT + 160.1            # chest high against a 120 unit hero
BLK_D = 1150.0
BLK_L, BLK_W = 320.1, 213.4
BLK_TOP = PIT + 213.4
NORMALS = (90, 30, -30, -90, -150, 150)

def rad(d):
    return math.radians(d)

def box(name, x, y, z):
    return {"name": name,
            "origin": [round((x[0] + x[1]) / 2.0, 1), round((y[0] + y[1]) / 2.0, 1), round((z[0] + z[1]) / 2.0, 1)],
            "extents": [round(x[1] - x[0], 1), round(y[1] - y[0], 1), round(z[1] - z[0], 1)],
            "angles": [0.0, 0.0, 0.0], "material": MAT}

def yawbox(name, cx, cy, cz, length, width, height, yaw):
    return {"name": name,
            "origin": [round(cx, 1), round(cy, 1), round(cz, 1)],
            "extents": [round(length, 1), round(width, 1), round(height, 1)],
            "angles": [0.0, round(yaw, 3), 0.0], "material": MAT}

def ringbox(name, normal, length, thick, dist, z0, z1):
    n = rad(normal)
    return yawbox(name, CX + dist * math.cos(n), CY + dist * math.sin(n),
                  (z0 + z1) / 2.0, length, thick, z1 - z0, normal - 90)

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

    # ---- op 1: cut the shaft hole out of the spawn room floor ------------
    if "hex_plat_s" in idx:
        b = boxes[idx["hex_plat_s"]]
        if abs(b["extents"][1] - (SHY[1] - PLAT_Y[1])) < 0.1:
            log.append("skip cut hex_plat_s (already cut)")
        elif abs(b["extents"][1] - (PLAT_Y[1] - PLAT_Y[0])) > 0.1:
            log.append("FAIL cut hex_plat_s: expected width %.1f, found %.1f"
                       % (PLAT_Y[1] - PLAT_Y[0], b["extents"][1]))
        else:
            b["extents"][1] = round(PLAT_Y[1] - SHY[1], 1)
            b["origin"][1] = round((SHY[1] + PLAT_Y[1]) / 2.0, 1)
            log.append("cut hex_plat_s down to the strip north of the shaft")
            add(box("hex_plat_s_s", PLAT_X, (PLAT_Y[0], SHY[0]), (PLAT_TOP - 26.6, PLAT_TOP)))
            add(box("hex_plat_s_w", (PLAT_X[0], SHX[0]), SHY, (PLAT_TOP - 26.6, PLAT_TOP)))
            add(box("hex_plat_s_e", (SHX[1], PLAT_X[1]), SHY, (PLAT_TOP - 26.6, PLAT_TOP)))
    else:
        log.append("FAIL hex_plat_s absent")

    # shaft walls. The north side is open below the tunnel ceiling, which
    # is what makes this a drop INTO the tunnel rather than a dead well.
    add(box("hex_drop_wall_w", (SHX[0] - WALL_T, SHX[0]), (SHY[0] - WALL_T, SHY[1] + WALL_T), (PIT, PLAT_TOP)))
    add(box("hex_drop_wall_e", (SHX[1], SHX[1] + WALL_T), (SHY[0] - WALL_T, SHY[1] + WALL_T), (PIT, PLAT_TOP)))
    add(box("hex_drop_wall_s", (SHX[0] - WALL_T, SHX[1] + WALL_T), (SHY[0] - WALL_T, SHY[0]), (PIT, PLAT_TOP)))
    add(box("hex_drop_wall_n", (SHX[0] - WALL_T, SHX[1] + WALL_T), (SHY[1], SHY[1] + WALL_T), (HEAD, PLAT_TOP)))
    add(box("hex_drop_floor", (SHX[0] - WALL_T, SHX[1] + WALL_T), (SHY[0] - WALL_T, SHY[1]), (PIT - 26.8, PIT)))

    # tunnel from the shaft north to the pit
    TY = (SHY[1], S_WALL_Y + WALL_T / 2.0)
    add(box("hex_drop_tun_floor", SHX, TY, (PIT - 26.8, PIT)))
    add(box("hex_drop_tun_wall_w", (SHX[0] - WALL_T, SHX[0]), TY, (PIT, HEAD)))
    add(box("hex_drop_tun_wall_e", (SHX[1], SHX[1] + WALL_T), TY, (PIT, HEAD)))
    add(box("hex_drop_tun_roof", (SHX[0] - WALL_T, SHX[1] + WALL_T), TY, (HEAD - 26.6, HEAD)))

    # ---- op 1b: open hex_wall_s for it ------------------------------------
    if "hex_wall_s" in idx:
        b = boxes[idx["hex_wall_s"]]
        half_w = R / 2.0 + WALL_T
        if abs(b["extents"][0] - (half_w - JAMB_OUT)) < 0.1:
            log.append("skip open hex_wall_s (already open)")
        elif abs(b["extents"][0] - 2 * half_w) > 0.1:
            log.append("FAIL open hex_wall_s: expected length %.1f, found %.1f"
                       % (2 * half_w, b["extents"][0]))
        else:
            b["extents"][0] = round(half_w - JAMB_OUT, 1)
            b["origin"][0] = round(-(half_w + JAMB_OUT) / 2.0, 1)
            log.append("open hex_wall_s for the drop tunnel")
        add(box("hex_wall_s_far", (JAMB_OUT, half_w),
                (S_WALL_Y - WALL_T / 2.0, S_WALL_Y + WALL_T / 2.0), (PIT, PLAT_TOP)))
        add(box("hex_wall_s_hdr", (-JAMB_OUT, JAMB_OUT),
                (S_WALL_Y - WALL_T / 2.0, S_WALL_Y + WALL_T / 2.0), (HEAD, PLAT_TOP)))
        add(box("hex_wall_s_jl", (-JAMB_OUT, -JAMB_IN),
                (S_WALL_Y - WALL_T / 2.0, S_WALL_Y + WALL_T / 2.0), (PIT, SPRING)))
        add(box("hex_wall_s_jr", (JAMB_IN, JAMB_OUT),
                (S_WALL_Y - WALL_T / 2.0, S_WALL_Y + WALL_T / 2.0), (PIT, SPRING)))
        src = [b2 for b2 in boxes if b2["name"].endswith(SRC_TAG)]
        th = -180.0
        for b2 in src:
            nb = copy.deepcopy(b2)
            nb["name"] = b2["name"][: -len(SRC_TAG)] + "_hexdrop"
            ox, oy = b2["origin"][0] - SRC_CX, b2["origin"][1] - SRC_CY
            nb["origin"] = [round(0.0 + ox * math.cos(rad(th)) - oy * math.sin(rad(th)), 1),
                            round(S_WALL_Y + ox * math.sin(rad(th)) + oy * math.cos(rad(th)), 1),
                            b2["origin"][2]]
            nb["angles"] = [b2["angles"][0], round(b2["angles"][1] + th, 3), b2["angles"][2]]
            add(nb)
    else:
        log.append("FAIL hex_wall_s absent")

    # ---- op 2: pit cover ---------------------------------------------------
    # central dais, same three-rectangle trick as the arena floor
    for i, yaw in enumerate((0.0, 60.0, 120.0)):
        add(yawbox("hex_dais_%d" % i, CX, CY, (PIT + DAIS_TOP) / 2.0,
                   DAIS_R, 2 * DAIS_A, DAIS_TOP - PIT, yaw))
    # ring wall, one segment per face, gaps left at the six corners
    for normal in NORMALS:
        add(ringbox("hex_ring_%d" % ((normal + 360) % 360), normal,
                    RING_L, RING_T, RING_D, PIT, RING_TOP))
    # blocks outboard of each gap, so the gaps are covered approaches
    for k in range(6):
        ang = 60 * k
        add(yawbox("hex_blk_%d" % ang,
                   CX + BLK_D * math.cos(rad(ang)), CY + BLK_D * math.sin(rad(ang)),
                   (PIT + BLK_TOP) / 2.0, BLK_L, BLK_W, BLK_TOP - PIT, ang - 90))

    json.dump(plan, open(path, "w"), indent=1)
    for line in log:
        print(line)
    print("boxes: %d" % len(boxes))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_half.json")
