#!/usr/bin/env python3
"""
Manual tail step: twenty-second batch from the 2026-08-17 crosshair session.
Runs after apply_batch_20260817u.py. Name-keyed and idempotent.

op 1..3: three more d195 standard doors, two through axis_553 and one
         through axis_552, each sitting on its own floor plate and centred
         between the pair of props called out for it.
op 4:    small hexagon room west of them, built the same way as the big
         one: side length drives the geometry, one face per door, square
         stubs at every wall so each arch is met dead on, mitred bends.

axis_553 is 53.3 thick and axis_552 is 80.0, against the 26.7 of the
source wall, so the arch is cloned two and three times across the
thickness rather than left floating inside it.

Usage:  python3 apply_batch_20260817v.py docs/plans/dust2_half.json
"""
import json, math, sys, copy

MAT = "materials/dev/reflectivity_30.vmat"

DOOR_W, DOOR_H = 253.0, 586.8
SRC = "_d195"
SRC_WALL_X, SRC_OPEN_Y, SRC_TOP = 2280.5, 839.0, 586.95
SRC_T = 26.7

# hexagon: pointy-top, one face per door
R = 800.1
A = R * math.sqrt(3) / 2.0
CY = 2913.9                      # on the middle door
FLOOR_TOP = 280.1                # highest of the three sills
FLOOR = (FLOOR_TOP - 26.8, FLOOR_TOP)
TOP = FLOOR_TOP + DOOR_H         # 866.9, walls the height of the arch
CEIL = (TOP - 26.6, TOP)
CX = -2187.1 - R - A - 13.35     # E face one side length off the axis_553 face
BORE = DOOR_W
WALL_T = 26.7
GRADE = 10.0
STUB = 300.0
WALL_BASE = FLOOR[0]

FACE_E, FACE_NE, FACE_NW, FACE_W, FACE_SW, FACE_SE = 0, 60, 120, 180, 240, 300
WALL_DIST = A + WALL_T / 2.0

# name, wall x span, arch centre y, sill, suffix, copies, wall z top
# name, wall x span, arch centre y, sill, suffix, copies, wall z top, head
# head None means the standard DOOR_H above the sill. The middle door is
# capped at the axis_761 underside instead, which shortens the opening
# without touching the arch profile.
DOORS = [
    ("d553n", (-2187.1, -2133.8), 4627.6, 280.1, "_d553n", 2, 1280.3, None),
    ("d553s", (-2187.1, -2133.8), 2913.9, 253.4, "_d553s", 2, 1280.3, 680.2),
    ("d552",  (-2000.4, -1920.4), 1434.9, 213.3, "_d552",  3, 1067.0, None),
]

def box(name, x, y, z):
    return {"name": name,
            "origin": [round((x[0] + x[1]) / 2.0, 1), round((y[0] + y[1]) / 2.0, 1), round((z[0] + z[1]) / 2.0, 1)],
            "extents": [round(x[1] - x[0], 1), round(y[1] - y[0], 1), round(z[1] - z[0], 1)],
            "angles": [0.0, 0.0, 0.0], "material": MAT}

def yawbox(name, cx, cy, cz, length, width, height, yaw, pitch=0.0):
    return {"name": name,
            "origin": [round(cx, 1), round(cy, 1), round(cz, 1)],
            "extents": [round(length, 1), round(width, 1), round(height, 1)],
            "angles": [round(pitch, 3), round(yaw, 3), 0.0], "material": MAT}

def rad(d):
    return math.radians(d)

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

    src = [b for b in boxes if b["name"].endswith(SRC) and not b["name"].startswith("axis_")]
    if not src:
        log.append("FAIL no %s arch pieces" % SRC)

    # ---- axis_553 carries two openings, so cut it into three segments -----
    o553 = [(4627.6 - DOOR_W / 2.0, 4627.6 + DOOR_W / 2.0),
            (2913.9 - DOOR_W / 2.0, 2913.9 + DOOR_W / 2.0)]
    if "axis_553" in idx:
        w = boxes[idx["axis_553"]]
        lo = w["origin"][1] - w["extents"][1] / 2.0
        hi = w["origin"][1] + w["extents"][1] / 2.0
        if abs(hi - o553[1][0]) < 0.1:
            log.append("skip trim axis_553 (already %.1f)" % o553[1][0])
        elif abs(hi - 5254.4) > 0.1:
            log.append("FAIL trim axis_553: expected y max 5254.4, found %.1f" % hi)
        else:
            w["origin"][1] = round((lo + o553[1][0]) / 2.0, 1)
            w["extents"][1] = round(o553[1][0] - lo, 1)
            log.append("trim axis_553 y max 5254.4 -> %.1f" % o553[1][0])
        add(box("axis_553_mid", (-2187.1, -2133.8), (o553[1][1], o553[0][0]), (0.1, 1280.3)))
        add(box("axis_553_far", (-2187.1, -2133.8), (o553[0][1], 5254.4), (0.1, 1280.3)))
    else:
        log.append("FAIL axis_553 absent")

    if "axis_552" in idx:
        w = boxes[idx["axis_552"]]
        lo = w["origin"][1] - w["extents"][1] / 2.0
        hi = w["origin"][1] + w["extents"][1] / 2.0
        want = 1434.9 - DOOR_W / 2.0
        if abs(hi - want) < 0.1:
            log.append("skip trim axis_552 (already %.1f)" % want)
        elif abs(hi - 2560.6) > 0.1:
            log.append("FAIL trim axis_552: expected y max 2560.6, found %.1f" % hi)
        else:
            w["origin"][1] = round((lo + want) / 2.0, 1)
            w["extents"][1] = round(want - lo, 1)
            log.append("trim axis_552 y max 2560.6 -> %.1f" % want)
        add(box("axis_552_far", (-2000.4, -1920.4), (1434.9 + DOOR_W / 2.0, 2560.6), (213.4, 1067.0)))
    else:
        log.append("FAIL axis_552 absent")

    # ---- door low blocks, headers and arch copies -------------------------
    for tag, wx, cy, sill, suffix, copies, wtop, head in DOORS:
        o_lo, o_hi = cy - DOOR_W / 2.0, cy + DOOR_W / 2.0
        hdr = head if head else sill + DOOR_H
        wbot = 213.4 if tag == "d552" else 0.1
        if sill - wbot > 1.0:
            add(box("axis" + suffix + "_low", wx, (o_lo, o_hi), (wbot, sill)))
        add(box("axis" + suffix + "_hdr", wx, (o_lo, o_hi), (hdr, wtop)))
        wc = (wx[0] + wx[1]) / 2.0
        for k in range(copies):
            ox = wc + (k - (copies - 1) / 2.0) * SRC_T
            for b in src:
                nb = copy.deepcopy(b)
                nb["name"] = b["name"][: -len(SRC)] + suffix + ("_%d" % k)
                nb["origin"] = [round(b["origin"][0] + ox - SRC_WALL_X, 1),
                                round(b["origin"][1] + cy - SRC_OPEN_Y, 1),
                                round(b["origin"][2] + hdr - SRC_TOP, 1)]
                add(nb)
        log.append("arch cloned to %s x%d" % (suffix, copies))

    # ---- small hexagon room ----------------------------------------------
    for i, yaw in enumerate((0.0, 60.0, 120.0)):
        add(yawbox("hex2_floor_%d" % i, CX, CY, (FLOOR[0] + FLOOR[1]) / 2.0,
                   2 * A, R, FLOOR[1] - FLOOR[0], yaw))
    add(yawbox("hex2_ceil_0", CX, CY, (CEIL[0] + CEIL[1]) / 2.0, 2 * A, R, CEIL[1] - CEIL[0], 0.0))
    add(yawbox("hex2_ceil_1", CX, CY, (CEIL[0] + CEIL[1]) / 2.0, 2 * A, R, CEIL[1] - CEIL[0], 60.0))
    add(yawbox("hex2_ceil_2", CX, CY, (CEIL[0] + CEIL[1]) / 2.0, 2 * A, R, CEIL[1] - CEIL[0], 120.0))

    def facebox(name, normal, s0, s1, dist, thick, z0, z1):
        n, t = rad(normal), rad(normal - 90)
        s = (s0 + s1) / 2.0
        cx = CX + dist * math.cos(n) + s * math.cos(t)
        cy = CY + dist * math.sin(n) + s * math.sin(t)
        return yawbox(name, cx, cy, (z0 + z1) / 2.0, s1 - s0, thick, z1 - z0, normal - 90)

    half = R / 2.0 + WALL_T
    TUN = [("e", FACE_E, -2160.45, 2913.9, 253.4),
           ("ne", FACE_NE, -2160.45, 4627.6, 280.1),
           ("se", FACE_SE, -1960.4, 1434.9, 213.3)]
    used = set()
    for tag, normal, dx, dy, sill in TUN:
        used.add(normal)
        n = rad(normal)
        fx, fy = CX + WALL_DIST * math.cos(n), CY + WALL_DIST * math.sin(n)
        add(facebox("hex2_wall_%s_l" % tag, normal, -half, -BORE / 2.0, WALL_DIST, WALL_T, FLOOR_TOP, TOP))
        add(facebox("hex2_wall_%s_r" % tag, normal, BORE / 2.0, half, WALL_DIST, WALL_T, FLOOR_TOP, TOP))

        rise = FLOOR_TOP - sill
        run = rise / math.tan(rad(GRADE)) if rise > 0.5 else 0.0
        stub_d = max(STUB, run + 100.0)

        bdx, bdy = dx - stub_d, dy                    # bend at the door end
        bfx, bfy = fx + STUB * math.cos(n), fy + STUB * math.sin(n)
        legdx, legdy = bfx - bdx, bfy - bdy
        LL = math.hypot(legdx, legdy)
        straight = LL < 1.0 or abs(math.degrees(math.atan2(legdy, legdx)) - 180.0) < 1.0

        def seg(name, cx, cy_, length, yaw, top, with_floor=True, pitch=0.0, thick=26.8, floor_top=None):
            if with_floor:
                add(yawbox(name + "_floor", cx, cy_, (floor_top if floor_top else top) - 13.4,
                           length, BORE, thick, yaw))
            add(yawbox(name + "_roof", cx, cy_, (CEIL[0] + CEIL[1]) / 2.0,
                       length, BORE + 2 * WALL_T, CEIL[1] - CEIL[0], yaw))

        def polywalls(name, pts):
            """Side walls along a centreline polyline. Each segment ends where
            its own offset line meets the next one, so at a bend the outer wall
            runs to the outer corner and the inner wall stops short of the bore."""
            off = BORE / 2.0 + WALL_T / 2.0
            k = len(pts) - 1
            us, lens = [], []
            for i in range(k):
                ddx = pts[i + 1][0] - pts[i][0]
                ddy = pts[i + 1][1] - pts[i][1]
                Ls = math.hypot(ddx, ddy)
                us.append((ddx / Ls, ddy / Ls))
                lens.append(Ls)
            for sgn in (1.0, -1.0):
                side = "l" if sgn > 0 else "r"
                starts = [0.0] * k
                ends = list(lens)
                for i in range(k - 1):
                    u1, u2 = us[i], us[i + 1]
                    p1 = (-u1[1], u1[0])
                    p2 = (-u2[1], u2[0])
                    vx, vy = pts[i + 1]
                    a0 = (vx + sgn * off * p1[0], vy + sgn * off * p1[1])
                    b0 = (vx + sgn * off * p2[0], vy + sgn * off * p2[1])
                    det = u1[0] * (-u2[1]) - u1[1] * (-u2[0])
                    if abs(det) < 1e-9:
                        continue
                    rx, ry = b0[0] - a0[0], b0[1] - a0[1]
                    t1 = (rx * (-u2[1]) - ry * (-u2[0])) / det
                    t2 = (u1[0] * ry - u1[1] * rx) / det
                    ends[i] = lens[i] + t1
                    starts[i + 1] = t2
                for i in range(k):
                    length = ends[i] - starts[i]
                    if length <= 1.0:
                        continue
                    u = us[i]
                    px, py = -u[1], u[0]
                    mid = starts[i] + length / 2.0
                    add(yawbox("%s_wall_%s%d" % (name, side, i),
                               pts[i][0] + u[0] * mid + sgn * off * px,
                               pts[i][1] + u[1] * mid + sgn * off * py,
                               (WALL_BASE + TOP) / 2.0, length, WALL_T, TOP - WALL_BASE,
                               math.degrees(math.atan2(u[1], u[0]))))

        if straight:
            L = abs(fx - dx) + WALL_T
            cx_ = (dx + fx) / 2.0 - WALL_T / 2.0
            if run > 0.5:
                add(yawbox("hex2_tun_%s_ramp" % tag, dx - run / 2.0, dy,
                           (sill + FLOOR_TOP) / 2.0 - (53.3 / 2.0) / math.cos(rad(GRADE)),
                           run / math.cos(rad(GRADE)), BORE, 53.3, 0.0, GRADE))
                seg("hex2_tun_%s" % tag, (dx - run + fx) / 2.0 - WALL_T / 2.0, dy,
                    abs(fx - (dx - run)) + WALL_T, 180.0, FLOOR_TOP)
                # walls and roof span the whole run, floor only past the ramp
            else:
                seg("hex2_tun_%s" % tag, cx_, dy, L, 180.0, FLOOR_TOP)
            polywalls("hex2_tun_%s" % tag, [(dx, dy), (fx - WALL_T, dy)])
        else:
            yaw = math.degrees(math.atan2(legdy, legdx))
            mit = BORE / 2.0 * math.tan(rad(45.0)) * 1.25
            # door stub, carrying the ramp if there is one
            sl = stub_d + mit + WALL_T
            seg("hex2_tun_%s_dstub" % tag, dx - (stub_d + mit - WALL_T) / 2.0, dy, sl, 180.0,
                FLOOR_TOP, with_floor=(run <= 0.5))
            if run > 0.5:
                add(yawbox("hex2_tun_%s_ramp" % tag, dx - run / 2.0, dy,
                           (sill + FLOOR_TOP) / 2.0 - (53.3 / 2.0) / math.cos(rad(GRADE)),
                           run / math.cos(rad(GRADE)), BORE, 53.3, 0.0, GRADE))
                add(yawbox("hex2_tun_%s_dpad" % tag,
                           (dx - run + dx - stub_d - mit) / 2.0, dy, FLOOR_TOP - 13.4,
                           abs(run - stub_d - mit), BORE, 26.8, 180.0))
            # angled leg
            ux, uy = legdx / LL, legdy / LL
            seg("hex2_tun_%s_leg" % tag, (bdx + bfx) / 2.0, (bdy + bfy) / 2.0,
                LL + 2 * mit, yaw, FLOOR_TOP)
            # face stub
            seg("hex2_tun_%s_fstub" % tag,
                fx + math.cos(n) * (STUB + mit - WALL_T) / 2.0,
                fy + math.sin(n) * (STUB + mit - WALL_T) / 2.0,
                STUB + mit + WALL_T, normal, FLOOR_TOP)
            polywalls("hex2_tun_%s" % tag,
                      [(dx, dy), (bdx, bdy), (bfx, bfy), (fx, fy)])

        # arch in the face, flush. The d195 source wall normal is +x, so the
        # rotation is the face normal itself, not the face normal minus 90.
        th = normal
        for b in src:
            nb = copy.deepcopy(b)
            nb["name"] = b["name"][: -len(SRC)] + "_hx2" + tag
            ox, oy = b["origin"][0] - SRC_WALL_X, b["origin"][1] - SRC_OPEN_Y
            nb["origin"] = [round(fx + ox * math.cos(rad(th)) - oy * math.sin(rad(th)), 1),
                            round(fy + ox * math.sin(rad(th)) + oy * math.cos(rad(th)), 1),
                            round(b["origin"][2] + TOP - SRC_TOP, 1)]
            nb["angles"] = [b["angles"][0], round(b["angles"][1] + th, 3), b["angles"][2]]
            add(nb)

    for normal, tag in ((FACE_NW, "nw"), (FACE_W, "w"), (FACE_SW, "sw")):
        if normal in used:
            continue
        add(facebox("hex2_wall_%s" % tag, normal, -half, half, WALL_DIST, WALL_T, FLOOR_TOP, TOP))

    json.dump(plan, open(path, "w"), indent=1)
    for line in log:
        print(line)
    print("boxes: %d" % len(boxes))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_half.json")
