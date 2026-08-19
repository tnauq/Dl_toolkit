#!/usr/bin/env python3
"""
Manual tail step: twenty-third batch from the 2026-08-17 crosshair session.
Runs after apply_batch_20260817v.py. Name-keyed and idempotent.

op 1: move the whole axis_377 opening up by its own height above the
      merged_721 floor. The arch band is raised rather than rebuilt and the
      axis_377 sill grows up to meet it, so the aperture keeps its original
      93.4 form and simply sits 240.1 higher.
op 2: parapet walls along the outer edge of the three southern hexagon
      platforms, height equal to the platform width, with two big arch
      doors at the two corners of the southernmost one.

Usage:  python3 apply_batch_20260817w.py docs/plans/dust2_half.json
"""
import json, math, sys, copy

MAT = "materials/dev/reflectivity_30.vmat"

# ---- op 1 -----------------------------------------------------------------
A377_X = (-1013.5, -960.2)
FLOOR_377 = 213.3            # merged_721 top
SILL_377 = 360.0             # axis_377 top
HEAD_377 = 453.4             # current arch cap
RISE_377 = (HEAD_377 - FLOOR_377)          # 240.1, the amount to grow by
NEW_HEAD = HEAD_377 + RISE_377             # 693.5
VOID_TOP = 893.6             # gapfill_378_366 underside
SILL_NEW = SILL_377 + RISE_377             # 600.1, sill grows to meet the arch
RAISE_377 = ["ramp-slab_380", "ramp-slab_381", "ramp-slab_383",
             "angled-wall_379", "angled-wall_384", "shallow_382"]
JAMBS_377 = [(4747.6, 4774.4), (4894.4, 4907.6)]
APERTURE_377 = (4747.6, 4907.6)

# ---- op 2 -----------------------------------------------------------------
R = 1600.25
A = R * math.sqrt(3) / 2.0
CX, CY = 0.0, -813.5 - R - A
WALL_T = 26.7
PLAT_TOP = 1067.0
PLAT_D = PLAT_TOP - 426.8                  # 640.2, platform width
PAR_TOP = PLAT_TOP + PLAT_D                # parapet height equals that width
PAR_DIST = A + WALL_T / 2.0 + PLAT_D + WALL_T / 2.0
OUTER_SIDE = 2.0 * (A + WALL_T / 2.0 + PLAT_D) / math.sqrt(3)
FACE_S, FACE_SE, FACE_SW = -90, -30, -150

BIG_W, BIG_H = 400.1, 586.8
JAMB_OUT, JAMB_IN = 200.05, 165.2
SPRING = PLAT_TOP + 485.0
HEAD_BIG = PLAT_TOP + BIG_H
SRC_TAG = "_d468"
SRC_CX, SRC_CY, SRC_SILL = 0.0, -813.5, 426.8

def box(name, x, y, z):
    return {"name": name,
            "origin": [round((x[0] + x[1]) / 2.0, 1), round((y[0] + y[1]) / 2.0, 1), round((z[0] + z[1]) / 2.0, 1)],
            "extents": [round(x[1] - x[0], 1), round(y[1] - y[0], 1), round(z[1] - z[0], 1)],
            "angles": [0.0, 0.0, 0.0], "material": MAT}

def rad(d):
    return math.radians(d)

def facebox(name, normal, s0, s1, dist, thick, z0, z1):
    n, t = rad(normal), rad(normal - 90)
    s = (s0 + s1) / 2.0
    return {"name": name,
            "origin": [round(CX + dist * math.cos(n) + s * math.cos(t), 1),
                       round(CY + dist * math.sin(n) + s * math.sin(t), 1),
                       round((z0 + z1) / 2.0, 1)],
            "extents": [round(s1 - s0, 1), round(thick, 1), round(z1 - z0, 1)],
            "angles": [0.0, float(normal - 90), 0.0], "material": MAT}

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
    for name in RAISE_377:
        if name not in idx:
            log.append("skip raise %s (absent)" % name)
            continue
        b = boxes[idx[name]]
        z = b["origin"][2]
        if z > SILL_377 + RISE_377 + 50:
            log.append("skip raise %s (already up)" % name)
            continue
        b["origin"][2] = round(z + RISE_377, 1)
        log.append("raise %s z %.1f -> %.1f" % (name, z, b["origin"][2]))
    if "axis_377" in idx:
        b = boxes[idx["axis_377"]]
        lo = b["origin"][2] - b["extents"][2] / 2.0
        hi = b["origin"][2] + b["extents"][2] / 2.0
        if abs(hi - SILL_NEW) < 0.1:
            log.append("skip grow axis_377 (already %.1f)" % SILL_NEW)
        elif abs(hi - SILL_377) > 0.1:
            log.append("FAIL grow axis_377: expected z max %.1f, found %.1f" % (SILL_377, hi))
        else:
            b["origin"][2] = round((lo + SILL_NEW) / 2.0, 1)
            b["extents"][2] = round(SILL_NEW - lo, 1)
            log.append("grow axis_377 z max %.1f -> %.1f" % (hi, SILL_NEW))
    else:
        log.append("FAIL axis_377 absent")

    # ---- op 2 -------------------------------------------------------------
    src = [b for b in boxes if b["name"].endswith(SRC_TAG)]
    if not src:
        log.append("FAIL no %s arch pieces" % SRC_TAG)

    for normal, tag in ((FACE_SE, "se"), (FACE_SW, "sw")):
        s0, s1 = -OUTER_SIDE / 2.0, OUTER_SIDE / 2.0
        if normal == FACE_SE:
            s0 = -R / 2.0
        else:
            s1 = R / 2.0
        add(facebox("hex_par_%s" % tag, normal, s0, s1, PAR_DIST, WALL_T, PLAT_TOP, PAR_TOP))

    # southern parapet, with a big arch tucked into each end
    half = OUTER_SIDE / 2.0
    for sgn in (-1.0, 1.0):
        c = sgn * (half - JAMB_OUT)
        side = "w" if sgn < 0 else "e"
        add(facebox("hex_par_s_jamb_%s0" % side, FACE_S, c - JAMB_OUT, c - JAMB_IN,
                    PAR_DIST, WALL_T, PLAT_TOP, SPRING))
        add(facebox("hex_par_s_jamb_%s1" % side, FACE_S, c + JAMB_IN, c + JAMB_OUT,
                    PAR_DIST, WALL_T, PLAT_TOP, SPRING))
        add(facebox("hex_par_s_hdr_%s" % side, FACE_S, c - JAMB_OUT, c + JAMB_OUT,
                    PAR_DIST, WALL_T, HEAD_BIG, PAR_TOP))
        th = FACE_S - 90.0
        n, t = rad(FACE_S), rad(FACE_S - 90)
        tx = CX + PAR_DIST * math.cos(n) + c * math.cos(t)
        ty = CY + PAR_DIST * math.sin(n) + c * math.sin(t)
        for b in src:
            nb = copy.deepcopy(b)
            nb["name"] = b["name"][: -len(SRC_TAG)] + "_hxpar" + side
            ox, oy = b["origin"][0] - SRC_CX, b["origin"][1] - SRC_CY
            nb["origin"] = [round(tx + ox * math.cos(rad(th)) - oy * math.sin(rad(th)), 1),
                            round(ty + ox * math.sin(rad(th)) + oy * math.cos(rad(th)), 1),
                            round(b["origin"][2] + PLAT_TOP - SRC_SILL, 1)]
            nb["angles"] = [b["angles"][0], round(b["angles"][1] + th, 3), b["angles"][2]]
            add(nb)
    # extend the southern platform to twice its reach and close in the strip
    # south of the two arches
    if "hex_plat_s" in idx:
        b = boxes[idx["hex_plat_s"]]
        w = b["extents"][1]
        if abs(w - 2 * PLAT_D) < 0.1:
            log.append("skip extend hex_plat_s (already %.1f)" % (2 * PLAT_D))
        elif abs(w - PLAT_D) > 0.1:
            log.append("FAIL extend hex_plat_s: expected width %.1f, found %.1f" % (PLAT_D, w))
        else:
            b["extents"][1] = round(2 * PLAT_D, 1)
            b["origin"][1] = round(b["origin"][1] - PLAT_D / 2.0, 1)
            log.append("extend hex_plat_s width %.1f -> %.1f" % (w, 2 * PLAT_D))
    PAR_Y = CY - (A + WALL_T / 2.0 + PLAT_D + WALL_T)      # parapet outer face
    SY = CY - (A + WALL_T / 2.0 + PLAT_D) - PLAT_D          # new platform south edge
    XE = OUTER_SIDE / 2.0
    add(box("hex_par_s_ext_w", (-XE - WALL_T, -XE), (SY - WALL_T, PAR_Y), (PLAT_TOP, PAR_TOP)))
    add(box("hex_par_s_ext_e", (XE, XE + WALL_T), (SY - WALL_T, PAR_Y), (PLAT_TOP, PAR_TOP)))
    add(box("hex_par_s_ext_s", (-XE - WALL_T, XE + WALL_T), (SY - WALL_T, SY), (PLAT_TOP, PAR_TOP)))
    add(box("hex_par_s_ext_roof", (-XE - WALL_T, XE + WALL_T), (SY - WALL_T, PAR_Y),
            (PAR_TOP - 26.6, PAR_TOP)))

    add(facebox("hex_par_s_mid", FACE_S,
                -(half - 2 * JAMB_OUT), (half - 2 * JAMB_OUT),
                PAR_DIST, WALL_T, PLAT_TOP, PAR_TOP))

    json.dump(plan, open(path, "w"), indent=1)
    for line in log:
        print(line)
    print("boxes: %d" % len(boxes))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_half.json")
