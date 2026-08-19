#!/usr/bin/env python3
"""
Manual tail step: twenty-seventh batch from the 2026-08-17 crosshair session.
Runs after apply_batch_20260817z.py. Name-keyed and idempotent.

op 1: double the three north walls of the big hexagon, header the three
      arches that were previously open to the old wall top, and roof the
      whole structure including the three southern platform decks.
op 2: double the small hexagon room the same way, lift its ceiling, and
      put a two step hexagonal dais in the middle. Total dais height is
      the old room height, each step half of it.

Usage:  python3 apply_batch_20260817aa.py docs/plans/dust2_half.json
"""
import json, math, sys

MAT = "materials/dev/reflectivity_30.vmat"
WALL_T = 26.7

# ---- big hexagon ----------------------------------------------------------
R = 1600.25
A = R * math.sqrt(3) / 2.0
CX, CY = 0.0, -813.5 - R - A
PIT = 426.8
OLD_TOP = 1067.0
NEW_TOP = PIT + 2 * (OLD_TOP - PIT)        # 1707.2
WALL_DIST = A + WALL_T / 2.0
JAMB_OUT = 200.05
ROOF = (NEW_TOP - 26.6, NEW_TOP)
PLAT_D = OLD_TOP - PIT
PLAT_OUT = A + WALL_T / 2.0 + PLAT_D / 2.0
OUTER_SIDE = 2.0 * (A + WALL_T / 2.0 + PLAT_D) / math.sqrt(3)
FACE_N, FACE_NE, FACE_SE, FACE_S, FACE_SW, FACE_NW = 90, 30, -30, -90, -150, 150

# ---- small hexagon room ---------------------------------------------------
R2 = 800.1
A2 = R2 * math.sqrt(3) / 2.0
CX2, CY2 = -2187.1 - R2 - A2 - WALL_T / 2.0, 2913.9
F2 = 280.1
OLD_TOP2 = 866.9
NEW_TOP2 = F2 + 2 * (OLD_TOP2 - F2)        # 1453.7
CEIL2 = (NEW_TOP2 - 26.6, NEW_TOP2)
WALL_DIST2 = A2 + WALL_T / 2.0
BORE2 = 253.0
DAIS_H = OLD_TOP2 - F2                     # 586.8 total
DAIS_STEP = DAIS_H / 2.0                   # 293.4 each
DAIS_R = [400.05, 213.4]

def rad(d):
    return math.radians(d)

def yawbox(name, cx, cy, cz, length, width, height, yaw):
    return {"name": name,
            "origin": [round(cx, 1), round(cy, 1), round(cz, 1)],
            "extents": [round(length, 1), round(width, 1), round(height, 1)],
            "angles": [0.0, round(yaw, 3), 0.0], "material": MAT}

def facebox(name, cx, cy, normal, s0, s1, dist, thick, z0, z1):
    n, t = rad(normal), rad(normal - 90)
    s = (s0 + s1) / 2.0
    return yawbox(name, cx + dist * math.cos(n) + s * math.cos(t),
                  cy + dist * math.sin(n) + s * math.sin(t),
                  (z0 + z1) / 2.0, s1 - s0, thick, z1 - z0, normal - 90)

# name, pre-edit z max, post-edit z max
RAISE = ([("hex_wall_%s_%s" % (t, p), OLD_TOP, NEW_TOP)
          for t in ("n", "ne", "nw") for p in ("l", "r")] +
         [("hex2_wall_%s_%s" % (t, p), OLD_TOP2, NEW_TOP2)
          for t in ("e", "ne", "se") for p in ("l", "r")] +
         [("hex2_wall_%s" % t, OLD_TOP2, NEW_TOP2) for t in ("nw", "w", "sw")])

def main(path):
    plan = json.load(open(path))
    boxes = plan["boxes"]
    idx = {b["name"]: i for i, b in enumerate(boxes)}
    log = []

    def add(nb):
        if nb["name"] in idx:
            log.append("skip add %s (present)" % nb["name"])
            return
        boxes.append(nb)
        idx[nb["name"]] = len(boxes) - 1
        log.append("add %s" % nb["name"])

    for name, pre, post in RAISE:
        if name not in idx:
            log.append("skip raise %s (absent)" % name)
            continue
        b = boxes[idx[name]]
        o, e = b["origin"], b["extents"]
        lo, hi = o[2] - e[2] / 2.0, o[2] + e[2] / 2.0
        if abs(hi - post) < 0.1:
            log.append("skip raise %s (already %.1f)" % (name, post))
            continue
        if abs(hi - pre) > 0.1:
            log.append("FAIL raise %s: expected z max %.1f, found %.1f" % (name, pre, hi))
            continue
        o[2] = round((lo + post) / 2.0, 1)
        e[2] = round(post - lo, 1)
        log.append("raise %s z max %.1f -> %.1f" % (name, hi, post))

    # headers over the openings that used to run to the old wall top
    for normal, tag in ((FACE_N, "n"), (FACE_NE, "ne"), (FACE_NW, "nw")):
        add(facebox("hex_wall_%s_hdr" % tag, CX, CY, normal, -JAMB_OUT, JAMB_OUT,
                    WALL_DIST, WALL_T, OLD_TOP, NEW_TOP))
    for normal, tag in ((0, "e"), (60, "ne"), (300, "se")):
        add(facebox("hex2_wall_%s_hdr" % tag, CX2, CY2, normal,
                    -BORE2 / 2.0, BORE2 / 2.0, WALL_DIST2, WALL_T, OLD_TOP2, NEW_TOP2))

    # roof over the hexagon proper, three rectangles as with the floor
    for i, yaw in enumerate((0.0, 60.0, 120.0)):
        add(yawbox("hex_roof_%d" % i, CX, CY, (ROOF[0] + ROOF[1]) / 2.0,
                   R, 2 * A, ROOF[1] - ROOF[0], yaw))
    # and over the three southern platform decks, matching their footprints
    for normal, tag in ((FACE_SE, "se"), (FACE_S, "s"), (FACE_SW, "sw")):
        s0, s1 = -OUTER_SIDE / 2.0, OUTER_SIDE / 2.0
        if normal == FACE_SE:
            s0 = -R / 2.0
        elif normal == FACE_SW:
            s1 = R / 2.0
        add(facebox("hex_roof_plat_%s" % tag, CX, CY, normal, s0, s1,
                    PLAT_OUT, PLAT_D, ROOF[0], ROOF[1]))

    # lift the small room's ceiling with its walls
    for i in range(3):
        n = "hex2_ceil_%d" % i
        if n not in idx:
            log.append("skip lift %s (absent)" % n)
            continue
        b = boxes[idx[n]]
        hi = b["origin"][2] + b["extents"][2] / 2.0
        if abs(hi - CEIL2[1]) < 0.1:
            log.append("skip lift %s (already %.1f)" % (n, CEIL2[1]))
            continue
        if abs(hi - OLD_TOP2) > 0.1:
            log.append("FAIL lift %s: expected z max %.1f, found %.1f" % (n, OLD_TOP2, hi))
            continue
        b["origin"][2] = round((CEIL2[0] + CEIL2[1]) / 2.0, 1)
        log.append("lift %s to %.1f" % (n, CEIL2[1]))

    # two step dais in the middle of the small room
    for tier in (0, 1):
        rr = DAIS_R[tier]
        aa = rr * math.sqrt(3) / 2.0
        z0 = F2 + tier * DAIS_STEP
        for i, yaw in enumerate((0.0, 60.0, 120.0)):
            add(yawbox("hex2_dais%d_%d" % (tier, i), CX2, CY2,
                       (z0 + z0 + DAIS_STEP) / 2.0, rr, 2 * aa, DAIS_STEP, yaw))

    json.dump(plan, open(path, "w"), indent=1)
    for line in log:
        print(line)
    print("boxes: %d" % len(boxes))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_half.json")
