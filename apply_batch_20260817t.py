#!/usr/bin/env python3
"""
Manual tail step: twentieth batch from the 2026-08-17 crosshair session.
Runs after apply_batch_20260817s.py. Name-keyed and idempotent.

Hexagon arena behind T spawn, with three tunnels to the three arches in
the y = -813.5 wall line (x -1060.2, 0, +1060.2).

Sizing rule: the hexagon side length and the north tunnel length are both
set to the entrance spacing, 1060.2. Flat-top hexagon, north face square
on to the centre arch. The flank tunnels run straight from their arch to
the midpoint of the NE / NW face, 9.9 degrees off north.

The east arch sits on the 213.3 floor while the other two sit on the
axis_470 deck at 426.8, so the east tunnel carries a 10 degree ramp:
331.4 flat off the arch, then 1210.8 of climb, arriving at 426.8 exactly
at the hexagon face.

Usage:  python3 apply_batch_20260817t.py docs/plans/dust2_half.json
"""
import json, math, sys

MAT = "materials/dev/reflectivity_30.vmat"

# ---- hexagon --------------------------------------------------------------
SPACING = 1060.2                     # arch-to-arch spacing, drives everything
R = SPACING                          # side length / circumradius
A = R * math.sqrt(3) / 2.0           # apothem, 918.2
WALL_Y = -813.5
CY = WALL_Y - SPACING - A            # north face is SPACING south of the wall
CX = 0.0
FLOOR = (400.0, 426.8)               # matches the axis_470 deck band
STEPS = 10                           # staircase steps per side wedge

# ---- tunnels --------------------------------------------------------------
BORE = 400.1                         # jamb-to-jamb, matches the arch
WALL_T = 26.7
TOP = 1067.0
ROOF = (1040.4, TOP)
LOW_SILL = 213.4                     # east arch sill
HIGH_SILL = 426.8                    # centre and west arch sill
GRADE = 10.0

def box(name, x, y, z):
    return {"name": name,
            "origin": [round((x[0] + x[1]) / 2.0, 1), round((y[0] + y[1]) / 2.0, 1), round((z[0] + z[1]) / 2.0, 1)],
            "extents": [round(x[1] - x[0], 1), round(y[1] - y[0], 1), round(z[1] - z[0], 1)],
            "angles": [0.0, 0.0, 0.0], "material": MAT}

def yawed(name, cx, cy, cz, length, width, height, yaw):
    return {"name": name,
            "origin": [round(cx, 1), round(cy, 1), round(cz, 1)],
            "extents": [round(length, 1), round(width, 1), round(height, 1)],
            "angles": [0.0, round(yaw, 3), 0.0], "material": MAT}

def build():
    out = []

    # ---- hexagon floor: central rectangle plus two stepped wedges ----------
    out.append(box("hex_floor_core", (CX - R / 2.0, CX + R / 2.0), (CY - A, CY + A), FLOOR))
    for k in range(STEPS):
        t = (k + 1) / float(STEPS)
        xo = (R / 2.0) * (2.0 - t)
        yb = A * t
        out.append(box("hex_floor_e%d" % k, (CX + R / 2.0, CX + xo), (CY - yb, CY + yb), FLOOR))
        out.append(box("hex_floor_w%d" % k, (CX - xo, CX - R / 2.0), (CY - yb, CY + yb), FLOOR))

    # ---- north tunnel: axis aligned ---------------------------------------
    ny = (CY + A, WALL_Y + 13.4)
    out.append(box("hex_tun_n_floor", (-BORE / 2.0, BORE / 2.0), ny, FLOOR))
    out.append(box("hex_tun_n_wall_w", (-BORE / 2.0 - WALL_T, -BORE / 2.0), ny, (FLOOR[1], TOP)))
    out.append(box("hex_tun_n_wall_e", (BORE / 2.0, BORE / 2.0 + WALL_T), ny, (FLOOR[1], TOP)))
    out.append(box("hex_tun_n_roof", (-BORE / 2.0 - WALL_T, BORE / 2.0 + WALL_T), ny, ROOF))

    # ---- flank tunnels ----------------------------------------------------
    for tag, sign, sill in (("ne", 1.0, LOW_SILL), ("nw", -1.0, HIGH_SILL)):
        ax, ay = sign * SPACING, WALL_Y                      # arch centre
        fx, fy = CX + sign * A * math.cos(math.radians(30)), CY + A * 0.5   # face midpoint
        dx, dy = fx - ax, fy - ay
        L = math.hypot(dx, dy)
        ux, uy = dx / L, dy / L
        yaw = math.degrees(math.atan2(uy, ux))
        px, py = -uy, ux
        mx, my = (ax + fx) / 2.0, (ay + fy) / 2.0
        base = min(sill, HIGH_SILL) - 26.8

        if sill == HIGH_SILL:
            out.append(yawed("hex_tun_%s_floor" % tag, mx, my, (FLOOR[0] + FLOOR[1]) / 2.0,
                             L, BORE, FLOOR[1] - FLOOR[0], yaw))
        else:
            rise = HIGH_SILL - sill
            run = rise / math.tan(math.radians(GRADE))       # 1210.8
            flat = L - run
            # flat pad off the arch
            fcx, fcy = ax + ux * flat / 2.0, ay + uy * flat / 2.0
            out.append(yawed("hex_tun_%s_pad" % tag, fcx, fcy, sill - 13.4,
                             flat, BORE, 26.8, yaw))
            # ramp, descending along local +x which points back at the arch
            rcx = ax + ux * (flat + run / 2.0)
            rcy = ay + uy * (flat + run / 2.0)
            slope_len = run / math.cos(math.radians(GRADE))
            cz = (HIGH_SILL + sill) / 2.0 - (53.3 / 2.0) / math.cos(math.radians(GRADE))
            ramp = yawed("hex_tun_%s_ramp" % tag, rcx, rcy, cz, slope_len, BORE, 53.3,
                         yaw + 180.0)
            ramp["angles"][0] = GRADE
            out.append(ramp)

        off = BORE / 2.0 + WALL_T / 2.0
        out.append(yawed("hex_tun_%s_wall_l" % tag, mx + px * off, my + py * off,
                         (base + TOP) / 2.0, L, WALL_T, TOP - base, yaw))
        out.append(yawed("hex_tun_%s_wall_r" % tag, mx - px * off, my - py * off,
                         (base + TOP) / 2.0, L, WALL_T, TOP - base, yaw))
        out.append(yawed("hex_tun_%s_roof" % tag, mx, my, (ROOF[0] + ROOF[1]) / 2.0,
                         L, BORE + 2 * WALL_T, ROOF[1] - ROOF[0], yaw))
    return out

def main(path):
    plan = json.load(open(path))
    boxes = plan["boxes"]
    idx = {b["name"]: i for i, b in enumerate(boxes)}
    log = []
    for nb in build():
        if nb["name"] in idx:
            log.append("skip add %s (present)" % nb["name"])
            continue
        boxes.append(nb)
        idx[nb["name"]] = len(boxes) - 1
        log.append("add %s" % nb["name"])
    json.dump(plan, open(path, "w"), indent=1)
    for line in log:
        print(line)
    print("boxes: %d" % len(boxes))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_half.json")
