#!/usr/bin/env python3
"""
Manual tail step: twentieth batch from the 2026-08-17 crosshair session.
Runs after apply_batch_20260817s.py. Name-keyed and idempotent.

Hexagon arena behind T spawn plus its approaches.

  - floor as three congruent rectangles at yaw 0 / 60 / 120. A regular
    hexagon is exactly their union, so this is not an approximation.
  - six perimeter walls, arch height, with the N / NE / NW faces split for
    arched exits cloned from the d468 assembly and rotated to sit flush in
    their face.
  - three tunnels from the arches in the y = -813.5 wall line, sized off the
    1600.25 entrance spacing. The east one carries a 10 degree ramp from
    the 213.4 sill up to the 426.8 floor.
  - platforms on the three southern walls, extending south by the wall
    height and lengthened so they meet at their outer corners.
  - short straight link between the axis_468_far arch and the axis_562 arch,
    which now share x 1600.25.

Usage:  python3 apply_batch_20260817t.py docs/plans/dust2_half.json
"""
import json, math, sys

MAT = "materials/dev/reflectivity_30.vmat"

SPACING = 1600.25                    # arch-to-arch spacing, drives everything
R = SPACING                          # hexagon side / circumradius
A = R * math.sqrt(3) / 2.0           # apothem
WALL_Y = -813.5
CX, CY = 0.0, WALL_Y - SPACING - A   # north face sits SPACING south of the wall

FLOOR = (400.0, 426.8)
SILL = FLOOR[1]
TOP = 1067.0                         # arch height
WALL_T = 26.7
ROOF = (1040.4, TOP)
BORE = 400.1
JAMB_OUT, JAMB_IN = 200.05, 165.2
SPRING = 911.8
LOW_SILL = 213.4
GRADE = 10.0

FACE_N, FACE_NE, FACE_SE, FACE_S, FACE_SW, FACE_NW = 90, 30, -30, -90, -150, 150
WALL_DIST = A + WALL_T / 2.0
PLAT_D = TOP - SILL                  # platform reach, equals wall height
PLAT_OUT = A + WALL_T / 2.0 + PLAT_D / 2.0
OUTER_SIDE = 2.0 * (A + WALL_T / 2.0 + PLAT_D) / math.sqrt(3)

SRC_TAG = "_d468"
SRC_CX, SRC_CY = 0.0, WALL_Y

def rad(d):
    return math.radians(d)

def yawbox(name, cx, cy, cz, length, width, height, yaw):
    return {"name": name,
            "origin": [round(cx, 1), round(cy, 1), round(cz, 1)],
            "extents": [round(length, 1), round(width, 1), round(height, 1)],
            "angles": [0.0, round(yaw, 3), 0.0], "material": MAT}

def facebox(name, normal, s0, s1, dist, thick, z0, z1):
    """Box lying in a hexagon face plane. s is the along-face coordinate."""
    n, t = rad(normal), rad(normal - 90)
    s = (s0 + s1) / 2.0
    cx = CX + dist * math.cos(n) + s * math.cos(t)
    cy = CY + dist * math.sin(n) + s * math.sin(t)
    return yawbox(name, cx, cy, (z0 + z1) / 2.0, s1 - s0, thick, z1 - z0, normal - 90)

def build(src):
    out = []
    TUN = {}

    # ---- floor: three rectangles, union is exactly the hexagon ------------
    for i, yaw in enumerate((0.0, 60.0, 120.0)):
        out.append(yawbox("hex_floor_%d" % i, CX, CY, (FLOOR[0] + FLOOR[1]) / 2.0,
                          R, 2 * A, FLOOR[1] - FLOOR[0], yaw))

    # ---- tunnels ----------------------------------------------------------
    def tunnel(tag, ax, ay, normal, sill):
        fx = CX + WALL_DIST * math.cos(rad(normal))
        fy = CY + WALL_DIST * math.sin(rad(normal))
        dx, dy = fx - ax, fy - ay
        L = math.hypot(dx, dy)
        ux, uy = dx / L, dy / L
        yaw = math.degrees(math.atan2(uy, ux))
        px, py = -uy, ux
        base = min(sill, SILL) - 26.8
        # A tunnel that meets a wall obliquely leaves a wedge at the mouth:
        # one corner stops short of the wall plane by (BORE/2)*tan(skew).
        # Run the shell past both wall planes by that much plus the wall
        # thickness so nothing stops short and no floor is missing.
        def skew(axis_yaw, wall_normal):
            d = abs(((axis_yaw - wall_normal + 180.0) % 360.0) - 180.0)
            return 180.0 - d if d > 90.0 else d
        skew_f = skew(yaw, normal)
        skew_a = skew(yaw, 90.0)
        ext_f = BORE / 2.0 * math.tan(rad(min(skew_f, 70.0))) + WALL_T / math.cos(rad(min(skew_f, 70.0)))
        ext_a = BORE / 2.0 * math.tan(rad(min(skew_a, 70.0))) + WALL_T / math.cos(rad(min(skew_a, 70.0)))
        L_ext = L + ext_f + ext_a
        mx = (ax + fx) / 2.0 + ux * (ext_f - ext_a) / 2.0
        my = (ay + fy) / 2.0 + uy * (ext_f - ext_a) / 2.0
        if sill == SILL:
            out.append(yawbox("hex_tun_%s_floor" % tag, mx, my, (FLOOR[0] + FLOOR[1]) / 2.0,
                              L_ext, BORE, FLOOR[1] - FLOOR[0], yaw))
        else:
            run = (SILL - sill) / math.tan(rad(GRADE))
            flat = L - run
            pad0 = -ext_a
            out.append(yawbox("hex_tun_%s_pad" % tag,
                              ax + ux * (pad0 + flat) / 2.0, ay + uy * (pad0 + flat) / 2.0,
                              sill - 13.4, flat - pad0, BORE, 26.8, yaw))
            out.append(yawbox("hex_tun_%s_mouth" % tag,
                              fx + ux * ext_f / 2.0, fy + uy * ext_f / 2.0,
                              (FLOOR[0] + FLOOR[1]) / 2.0, ext_f, BORE,
                              FLOOR[1] - FLOOR[0], yaw))
            cz = (SILL + sill) / 2.0 - (53.3 / 2.0) / math.cos(rad(GRADE))
            ramp = yawbox("hex_tun_%s_ramp" % tag, ax + ux * (flat + run / 2.0),
                          ay + uy * (flat + run / 2.0), cz,
                          run / math.cos(rad(GRADE)), BORE, 53.3, yaw + 180.0)
            ramp["angles"][0] = GRADE
            out.append(ramp)
        off = BORE / 2.0 + WALL_T / 2.0
        out.append(yawbox("hex_tun_%s_wall_l" % tag, mx + px * off, my + py * off,
                          (base + TOP) / 2.0, L_ext, WALL_T, TOP - base, yaw))
        out.append(yawbox("hex_tun_%s_wall_r" % tag, mx - px * off, my - py * off,
                          (base + TOP) / 2.0, L_ext, WALL_T, TOP - base, yaw))
        out.append(yawbox("hex_tun_%s_roof" % tag, mx, my, (ROOF[0] + ROOF[1]) / 2.0,
                          L_ext, BORE + 2 * WALL_T, ROOF[1] - ROOF[0], yaw))
        return {"yaw": yaw, "u": (ux, uy), "skew": skew_f,
                "arch": (fx + ux * ext_f, fy + uy * ext_f)}

    TUN["n"] = tunnel("n", 0.0, WALL_Y, FACE_N, SILL)
    TUN["ne"] = tunnel("ne", SPACING, WALL_Y, FACE_NE, LOW_SILL)
    TUN["nw"] = tunnel("nw", -SPACING, WALL_Y, FACE_NW, SILL)

    # ---- perimeter walls, built from the tunnel geometry -----------------
    half = R / 2.0 + WALL_T
    for normal, tag in ((FACE_N, "n"), (FACE_NE, "ne"), (FACE_SE, "se"),
                        (FACE_S, "s"), (FACE_SW, "sw"), (FACE_NW, "nw")):
        if tag in TUN:
            t = TUN[tag]
            # opening in the face plane is the bore stretched by the skew, so
            # the wall closes flush against the tunnel's inner faces
            oh = BORE / 2.0 / math.cos(rad(t["skew"]))
            out.append(facebox("hex_wall_%s_l" % tag, normal, -half, -oh, WALL_DIST, WALL_T, SILL, TOP))
            out.append(facebox("hex_wall_%s_r" % tag, normal, oh, half, WALL_DIST, WALL_T, SILL, TOP))
            # arch square to the tunnel, marking its end
            th = t["yaw"] - 90.0
            tx, ty = t["arch"]
            ux, uy = t["u"]
            px, py = -uy, ux
            for sgn in (-1.0, 1.0):
                so = sgn * (JAMB_IN + JAMB_OUT) / 2.0
                out.append(yawbox("hex_arch_%s_jamb%s" % (tag, "r" if sgn > 0 else "l"),
                                  tx + px * so, ty + py * so, (SILL + SPRING) / 2.0,
                                  WALL_T, JAMB_OUT - JAMB_IN, SPRING - SILL, t["yaw"]))
            for b in src:
                nb = json.loads(json.dumps(b))
                nb["name"] = b["name"][: -len(SRC_TAG)] + "_hex" + tag
                ox, oy = b["origin"][0] - SRC_CX, b["origin"][1] - SRC_CY
                nb["origin"] = [round(tx + ox * math.cos(rad(th)) - oy * math.sin(rad(th)), 1),
                                round(ty + ox * math.sin(rad(th)) + oy * math.cos(rad(th)), 1),
                                b["origin"][2]]
                nb["angles"] = [b["angles"][0], round(b["angles"][1] + th, 3), b["angles"][2]]
                out.append(nb)
        else:
            out.append(facebox("hex_wall_%s" % tag, normal, -half, half, WALL_DIST, WALL_T, SILL, TOP))
            s0, s1 = -OUTER_SIDE / 2.0, OUTER_SIDE / 2.0
            if normal == FACE_SE:
                s0 = -R / 2.0
            elif normal == FACE_SW:
                s1 = R / 2.0
            out.append(facebox("hex_plat_%s" % tag, normal, s0, s1,
                               PLAT_OUT, PLAT_D, ROOF[0], ROOF[1]))

    # ---- short link from the axis_468_far arch up to the axis_562 arch ----
    ly = (-800.1, -586.8)
    lx = (SPACING - BORE / 2.0, SPACING + BORE / 2.0)
    out.append({"name": "hex_link_wall_w",
                "origin": [round(lx[0] - WALL_T / 2.0, 1), round(sum(ly) / 2.0, 1), round((LOW_SILL + TOP) / 2.0, 1)],
                "extents": [WALL_T, round(ly[1] - ly[0], 1), round(TOP - LOW_SILL, 1)],
                "angles": [0.0, 0.0, 0.0], "material": MAT})
    out.append({"name": "hex_link_wall_e",
                "origin": [round(lx[1] + WALL_T / 2.0, 1), round(sum(ly) / 2.0, 1), round((LOW_SILL + TOP) / 2.0, 1)],
                "extents": [WALL_T, round(ly[1] - ly[0], 1), round(TOP - LOW_SILL, 1)],
                "angles": [0.0, 0.0, 0.0], "material": MAT})
    out.append({"name": "hex_link_roof",
                "origin": [round(SPACING, 1), round(sum(ly) / 2.0, 1), round(sum(ROOF) / 2.0, 1)],
                "extents": [round(BORE + 2 * WALL_T, 1), round(ly[1] - ly[0], 1), round(ROOF[1] - ROOF[0], 1)],
                "angles": [0.0, 0.0, 0.0], "material": MAT})
    return out

def main(path):
    plan = json.load(open(path))
    boxes = plan["boxes"]
    idx = {b["name"]: i for i, b in enumerate(boxes)}
    log = []
    src = [b for b in boxes if b["name"].endswith(SRC_TAG)]
    if not src:
        log.append("FAIL no %s arch pieces to clone" % SRC_TAG)
    for nb in build(src):
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
