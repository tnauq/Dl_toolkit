#!/usr/bin/env python3
"""
Manual tail step: twenty-fifth batch from the 2026-08-17 crosshair session.
Runs after apply_batch_20260817x.py. Name-keyed and idempotent.

op 1: drop shaft from the spawn room floor into a tunnel at pit level. The
      tunnel starts at the shaft's own 253 bore and steps out to the 400.1
      of the arch it exits through, so it opens up as you walk it.
op 2: pit cover, following the Patron pit references: a low central dais,
      a ring wall inboard of the perimeter broken by six gaps, and six
      chunky blocks outboard of the gaps.
op 3: flanking descents down the SE and SW faces, both stepping down
      toward the S face so they land either side of the tunnel mouth.
      Three large steps rather than a ramp: a ramp over the available run
      came out at 21.8 degrees, which reads too steep, so the drop is taken
      as three 213.4 platform steps instead.
op 4: railing along the inner edge of the three southern platforms, open
      at the head of each descent, plus scattered crates on the deck.

Usage:  python3 apply_batch_20260817y.py docs/plans/dust2_half.json
"""
import json, math, sys, copy

MAT = "materials/dev/reflectivity_30.vmat"

R = 1600.25
A = R * math.sqrt(3) / 2.0
CX, CY = 0.0, -813.5 - R - A
PIT = 426.8                       # hexagon floor top
WALL_T = 26.7
PLAT_TOP = 1067.0                 # perimeter wall top and spawn room floor
WALL_DIST = A + WALL_T / 2.0
S_WALL_Y = CY - WALL_DIST         # hex_wall_s centre line

BORE = 400.1                      # arch bore, the wide end of the tunnel
NARROW = 253.0                    # shaft bore, the narrow end
JAMB_OUT, JAMB_IN = 200.05, 165.2
DOOR_H = 586.8
HEAD = PIT + DOOR_H               # 1013.6, tunnel ceiling and arch head
SPRING = PIT + 485.0

SHW = NARROW / 2.0
SHY = (-6300.0, -6047.0)          # shaft, clear of the shop
PLAT_Y = (-6479.2, -5198.8)
PLAT_X = (-1177.45, 1177.45)

# tunnel flare: three equal runs from the shaft to the arch
FLARE = [NARROW, (NARROW + BORE) / 2.0, BORE]

SRC_TAG = "_d468"
SRC_CX, SRC_CY = 0.0, -813.5

# pit cover
DAIS_R = 480.1
DAIS_A = DAIS_R * math.sqrt(3) / 2.0
DAIS_TOP = PIT + 106.7
RING_D, RING_L, RING_T = 900.0, 800.0, 53.4
RING_TOP = PIT + 160.1
BLK_D, BLK_L, BLK_W = 1150.0, 320.1, 213.4
BLK_TOP = PIT + 213.4
NORMALS = (90, 30, -30, -90, -150, 150)

# flanking descents
STAIR_IN, STAIR_OUT = A - BORE, A     # band hugging the perimeter wall
NSTEP = 3
STEP_RISE = (PLAT_TOP - PIT) / (NSTEP + 1)   # 160.05 per level... see below
STEP_RISE = (PLAT_TOP - PIT) / NSTEP         # 213.4, a jump-up per step
STEP_TREAD = R / NSTEP                       # 533.4

# railing, height taken from axis_548 measured off the axis_546 deck
RAIL_H = 160.1
RAIL_T = 26.7
RAIL_HALF = R / 2.0 + WALL_T
RAIL_GAP = BORE                        # opening at the head of each descent

# crates, duplicates of axis_585
CRATE = (120.0, 120.0, 106.7)
CRATE_SPOTS = [(-30, -520.0, 200.0, 12.0), (-30, 40.0, 430.0, -25.0),
               (-30, 610.0, 250.0, 40.0),
               (-90, -430.0, 180.0, -15.0), (-90, 110.0, 420.0, 30.0),
               (-90, 620.0, 300.0, -40.0),
               (-150, -600.0, 260.0, 20.0), (-150, -60.0, 430.0, -35.0),
               (-150, 500.0, 190.0, 8.0)]

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

def facebox(name, normal, s, dist, length, thick, z0, z1):
    """Box in a face-parallel band. s is the along-face offset."""
    n, t = rad(normal), rad(normal - 90)
    return yawbox(name,
                  CX + dist * math.cos(n) + s * math.cos(t),
                  CY + dist * math.sin(n) + s * math.sin(t),
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

    # ---- op 1: shaft hole in the spawn room floor ------------------------
    if "hex_plat_s" in idx:
        b = boxes[idx["hex_plat_s"]]
        if abs(b["extents"][1] - (PLAT_Y[1] - SHY[1])) < 0.1:
            log.append("skip cut hex_plat_s (already cut)")
        elif abs(b["extents"][1] - (PLAT_Y[1] - PLAT_Y[0])) > 0.1:
            log.append("FAIL cut hex_plat_s: expected width %.1f, found %.1f"
                       % (PLAT_Y[1] - PLAT_Y[0], b["extents"][1]))
        else:
            b["extents"][1] = round(PLAT_Y[1] - SHY[1], 1)
            b["origin"][1] = round((SHY[1] + PLAT_Y[1]) / 2.0, 1)
            log.append("cut hex_plat_s back to the strip north of the shaft")
        add(box("hex_plat_s_s", PLAT_X, (PLAT_Y[0], SHY[0]), (PLAT_TOP - 26.6, PLAT_TOP)))
        add(box("hex_plat_s_w", (PLAT_X[0], -SHW), SHY, (PLAT_TOP - 26.6, PLAT_TOP)))
        add(box("hex_plat_s_e", (SHW, PLAT_X[1]), SHY, (PLAT_TOP - 26.6, PLAT_TOP)))
    else:
        log.append("FAIL hex_plat_s absent")

    add(box("hex_drop_wall_w", (-SHW - WALL_T, -SHW), (SHY[0] - WALL_T, SHY[1] + WALL_T), (PIT, PLAT_TOP)))
    add(box("hex_drop_wall_e", (SHW, SHW + WALL_T), (SHY[0] - WALL_T, SHY[1] + WALL_T), (PIT, PLAT_TOP)))
    add(box("hex_drop_wall_s", (-SHW - WALL_T, SHW + WALL_T), (SHY[0] - WALL_T, SHY[0]), (PIT, PLAT_TOP)))
    # the north side is closed only ABOVE the tunnel ceiling: that opening
    # is what makes this a drop into the tunnel rather than a dead well
    add(box("hex_drop_wall_n", (-SHW - WALL_T, SHW + WALL_T), (SHY[1], SHY[1] + WALL_T), (HEAD, PLAT_TOP)))
    add(box("hex_drop_floor", (-SHW - WALL_T, SHW + WALL_T), (SHY[0] - WALL_T, SHY[1]), (PIT - 26.8, PIT)))

    # tunnel, stepping out from the shaft bore to the arch bore
    y0, y1 = SHY[1], S_WALL_Y + WALL_T / 2.0
    seg = (y1 - y0) / len(FLARE)
    for k, w in enumerate(FLARE):
        h = w / 2.0
        sy = (y0 + k * seg, y0 + (k + 1) * seg)
        add(box("hex_drop_tun%d_floor" % k, (-h, h), sy, (PIT - 26.8, PIT)))
        add(box("hex_drop_tun%d_wall_w" % k, (-h - WALL_T, -h), sy, (PIT, HEAD)))
        add(box("hex_drop_tun%d_wall_e" % k, (h, h + WALL_T), sy, (PIT, HEAD)))
        add(box("hex_drop_tun%d_roof" % k, (-h - WALL_T, h + WALL_T), sy, (HEAD - 26.6, HEAD)))
        if k:
            # close the step-out on both sides so the widening is a jamb
            pw = FLARE[k - 1] / 2.0
            add(box("hex_drop_step%d_w" % k, (-h - WALL_T, -pw), (sy[0], sy[0] + WALL_T), (PIT, HEAD)))
            add(box("hex_drop_step%d_e" % k, (pw, h + WALL_T), (sy[0], sy[0] + WALL_T), (PIT, HEAD)))

    # ---- op 1b: open hex_wall_s for the tunnel ---------------------------
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
        wy = (S_WALL_Y - WALL_T / 2.0, S_WALL_Y + WALL_T / 2.0)
        add(box("hex_wall_s_far", (JAMB_OUT, half_w), wy, (PIT, PLAT_TOP)))
        add(box("hex_wall_s_hdr", (-JAMB_OUT, JAMB_OUT), wy, (HEAD, PLAT_TOP)))
        add(box("hex_wall_s_jl", (-JAMB_OUT, -JAMB_IN), wy, (PIT, SPRING)))
        add(box("hex_wall_s_jr", (JAMB_IN, JAMB_OUT), wy, (PIT, SPRING)))
        th = -180.0
        for b2 in [x for x in boxes if x["name"].endswith(SRC_TAG)]:
            nb = copy.deepcopy(b2)
            nb["name"] = b2["name"][: -len(SRC_TAG)] + "_hexdrop"
            ox, oy = b2["origin"][0] - SRC_CX, b2["origin"][1] - SRC_CY
            nb["origin"] = [round(ox * math.cos(rad(th)) - oy * math.sin(rad(th)), 1),
                            round(S_WALL_Y + ox * math.sin(rad(th)) + oy * math.cos(rad(th)), 1),
                            b2["origin"][2]]
            nb["angles"] = [b2["angles"][0], round(b2["angles"][1] + th, 3), b2["angles"][2]]
            add(nb)
    else:
        log.append("FAIL hex_wall_s absent")

    # ---- op 2: pit cover ---------------------------------------------------
    for i, yaw in enumerate((0.0, 60.0, 120.0)):
        add(yawbox("hex_dais_%d" % i, CX, CY, (PIT + DAIS_TOP) / 2.0,
                   DAIS_R, 2 * DAIS_A, DAIS_TOP - PIT, yaw))
    for normal in NORMALS:
        add(facebox("hex_ring_%d" % ((normal + 360) % 360), normal, 0.0,
                    RING_D, RING_L, RING_T, PIT, RING_TOP))
    for k in range(6):
        ang = 60 * k
        add(yawbox("hex_blk_%d" % ang,
                   CX + BLK_D * math.cos(rad(ang)), CY + BLK_D * math.sin(rad(ang)),
                   (PIT + BLK_TOP) / 2.0, BLK_L, BLK_W, BLK_TOP - PIT, ang - 90))

    # ---- op 3: flanking descents -----------------------------------------
    # Both sit in the band just inside the perimeter wall and both step down
    # TOWARDS the S face, so they arrive either side of the tunnel mouth.
    mid = (STAIR_IN + STAIR_OUT) / 2.0
    for normal, tag, sgn in ((-30, "se", 1.0), (-150, "sw", -1.0)):
        for k in range(NSTEP):
            sc = sgn * (-R / 2.0 + (k + 0.5) * STEP_TREAD)
            add(facebox("hex_step_%s_%d" % (tag, k), normal, sc, mid,
                        STEP_TREAD, STAIR_OUT - STAIR_IN,
                        PIT - 26.8, PLAT_TOP - k * STEP_RISE))

    # ---- op 4: railing and crates -----------------------------------------
    # Open for one bore width at the head of each descent, which is the far
    # end of the SE face and the far end of the SW face.
    for normal, tag, s0, s1 in (
            (-30,  "se", -RAIL_HALF + RAIL_GAP, RAIL_HALF),
            (-90,  "s",  -RAIL_HALF, RAIL_HALF),
            (-150, "sw", -RAIL_HALF, RAIL_HALF - RAIL_GAP)):
        add(facebox("hex_rail_%s" % tag, normal, (s0 + s1) / 2.0, WALL_DIST,
                    s1 - s0, RAIL_T, PLAT_TOP, PLAT_TOP + RAIL_H))
    for i, (normal, sc, out, yaw) in enumerate(CRATE_SPOTS):
        n = rad(normal)
        t = rad(normal - 90)
        d = WALL_DIST + out
        add(yawbox("hex_crate_%d" % i,
                   CX + d * math.cos(n) + sc * math.cos(t),
                   CY + d * math.sin(n) + sc * math.sin(t),
                   PLAT_TOP + CRATE[2] / 2.0,
                   CRATE[0], CRATE[1], CRATE[2], normal - 90 + yaw))

    json.dump(plan, open(path, "w"), indent=1)
    for line in log:
        print(line)
    print("boxes: %d" % len(boxes))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_half.json")
