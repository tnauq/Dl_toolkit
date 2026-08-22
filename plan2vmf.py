#!/usr/bin/env python3
"""plan2vmf.py - emit a Source 1 VMF from a .mapplan.json.

This is hop one of the two-hop route into Deadlock: VMF here, then
Valve's source1import to turn it into a Source 2 vmap. Hop two is
Windows-only and cannot be run or verified from CI, so treat the output
of this script as unproven until someone compiles it.

WHY RECENTRED
Source 1's world limit is +/- 16384 on each axis. The plan spans
25182.00 on y and reaches y 18676.00, which is 2292.00 past the limit.
Everything is therefore shifted by RECENTRE below, which puts the map at
+/- 12170.00 on y and well inside on x and z. The shift is applied to
boxes AND entities so their relative positions are untouched, and it is
printed so it can be undone.

GEOMETRY
Each box becomes one six-sided solid. Rotated boxes are emitted as their
true oriented corners, not as an axis-aligned bounding box, so ramps keep
their pitch. Each side's plane is three of that face's corners, wound so
the plane normal points OUT of the solid; the winding is checked against
the box centre per face rather than assumed, because a wrong winding
gives an inside-out solid that vbsp will happily eat and then leak.

Texture axes are chosen from the dominant axis of each face normal. That
is correct for axis-aligned faces and approximate on the pitched ramps,
where it produces stretched alignment rather than broken geometry. Fixing
it properly means projecting along the true face normal, which matters
for looks, not for playability.

MATERIALS
The plan's Source 2 material paths do not exist in Source 1, so they are
mapped to the nearest Source 1 dev texture. Anything unrecognised falls
back to DEV/DEV_MEASUREGENERIC01B and is reported, since a missing
material is one of the things that makes source1import abort the whole
run rather than skip.

Usage: python3 plan2vmf.py docs/plans/dust2_full.json out/dust2.vmf
"""

import json
import math
import sys

# Applied to every box origin and entity origin. y only; x and z fit.
RECENTRE = [0.0, -6085.0, 0.0]

MAT_MAP = {
    "materials/dev/dev_measuregeneric01.vmat": "DEV/DEV_MEASUREGENERIC01B",
    "materials/dev/reflectivity_30.vmat": "DEV/REFLECTIVITY_30",
    "materials/dev/reflectivity_50.vmat": "DEV/REFLECTIVITY_50",
}
MAT_FALLBACK = "DEV/DEV_MEASUREGENERIC01B"

# Smallest extent that can still make a real face.
MIN_EXTENT = 0.1

# Face corner indices into the 8-corner list, and the axis each face
# faces. Corners are ordered by (sx, sy, sz) with sz fastest.
CORNER_SIGNS = [(sx, sy, sz)
                for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
FACES = [
    (2, [(-1, -1, 1), (-1, 1, 1), (1, 1, 1), (1, -1, 1)]),      # +z
    (2, [(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1)]),  # -z
    (0, [(1, -1, -1), (1, -1, 1), (1, 1, 1), (1, 1, -1)]),      # +x
    (0, [(-1, -1, -1), (-1, 1, -1), (-1, 1, 1), (-1, -1, 1)]),  # -x
    (1, [(-1, 1, -1), (1, 1, -1), (1, 1, 1), (-1, 1, 1)]),      # +y
    (1, [(-1, -1, -1), (-1, -1, 1), (1, -1, 1), (1, -1, -1)]),  # -y
]

UAXIS = {0: "[0 1 0 0]", 1: "[1 0 0 0]", 2: "[1 0 0 0]"}
VAXIS = {0: "[0 0 -1 0]", 1: "[0 0 -1 0]", 2: "[0 -1 0 0]"}


def rot(angles):
    p, y, r = [math.radians(v) for v in (angles or [0.0, 0.0, 0.0])]
    cy, sy = math.cos(y), math.sin(y)
    cp, sp = math.cos(p), math.sin(p)
    cr, sr = math.cos(r), math.sin(r)
    return [
        [cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
        [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
        [-sp, cp * sr, cp * cr],
    ]


def world(o, M, half, signs):
    v = [signs[i] * half[i] for i in range(3)]
    return [round(o[i] + sum(M[i][j] * v[j] for j in range(3)), 3)
            for i in range(3)]


def sub(a, b):
    return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]]


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def fmt(p):
    return "(%g %g %g)" % (p[0], p[1], p[2])


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_full.json"
    dst = sys.argv[2] if len(sys.argv) > 2 else "out/dust2.vmf"

    with open(src) as f:
        plan = json.load(f)

    ident = [1]
    def nid():
        ident[0] += 1
        return ident[0]

    out = []
    out.append('versioninfo\n{\n\t"editorversion" "400"\n'
               '\t"editorbuild" "8000"\n\t"mapversion" "1"\n'
               '\t"formatversion" "100"\n\t"prefab" "0"\n}\n')
    out.append("visgroups\n{\n}\n")
    out.append('viewsettings\n{\n\t"bSnapToGrid" "1"\n'
               '\t"bShowGrid" "1"\n\t"nGridSpacing" "64"\n}\n')

    unknown = {}
    flipped = 0

    out.append("world\n{\n")
    out.append('\t"id" "1"\n\t"mapversion" "1"\n\t"classname" "worldspawn"\n'
               '\t"skyname" "sky_dust"\n')

    degenerate = []
    for b in plan["boxes"]:
        e = b["extents"]
        # A box with a zero extent has four zero-area faces. vbsp treats
        # those as invalid planes, so it is skipped and reported rather
        # than written out as a solid that cannot compile.
        if min(e) <= MIN_EXTENT:
            degenerate.append((b["name"], list(e)))
            continue
        o = [b["origin"][i] + RECENTRE[i] for i in range(3)]
        half = [e[0] / 2.0, e[1] / 2.0, e[2] / 2.0]
        M = rot(b.get("angles"))

        mat = b.get("material")
        if mat in MAT_MAP:
            tex = MAT_MAP[mat]
        else:
            tex = MAT_FALLBACK
            unknown[mat] = unknown.get(mat, 0) + 1

        out.append('\tsolid\n\t{\n\t\t"id" "%d"\n' % nid())
        for axis, signs4 in FACES:
            pts = [world(o, M, half, s) for s in signs4]
            # Wind so the plane normal points away from the solid centre.
            n = cross(sub(pts[0], pts[1]), sub(pts[2], pts[1]))
            if dot(n, sub(pts[0], o)) < 0:
                pts = pts[::-1]
                flipped += 1
            out.append('\t\tside\n\t\t{\n\t\t\t"id" "%d"\n' % nid())
            out.append('\t\t\t"plane" "%s %s %s"\n'
                       % (fmt(pts[0]), fmt(pts[1]), fmt(pts[2])))
            out.append('\t\t\t"material" "%s"\n' % tex)
            out.append('\t\t\t"uaxis" "%s 0.25"\n' % UAXIS[axis])
            out.append('\t\t\t"vaxis" "%s 0.25"\n' % VAXIS[axis])
            out.append('\t\t\t"rotation" "0"\n\t\t\t"lightmapscale" "16"\n'
                       '\t\t\t"smoothing_groups" "0"\n\t\t}\n')
        out.append('\t\teditor\n\t\t{\n\t\t\t"color" "0 180 220"\n'
                   '\t\t\t"visgroupshown" "1"\n\t\t\t"visgroupautoshown" "1"\n'
                   '\t\t\t"comment" "%s"\n\t\t}\n' % b["name"])
        out.append("\t}\n")
    out.append("}\n")

    if degenerate:
        print("SKIPPED %d degenerate boxes (an extent at or under %g):"
              % (len(degenerate), MIN_EXTENT))
        for n, e in degenerate:
            print("  %s extents %s" % (n, e))

    for ent in plan.get("entities", []):
        o = [ent["origin"][i] + RECENTRE[i] for i in range(3)]
        a = ent.get("angles", [0, 0, 0])
        out.append('entity\n{\n\t"id" "%d"\n' % nid())
        out.append('\t"classname" "%s"\n' % ent["classname"])
        for k, v in (ent.get("properties") or {}).items():
            out.append('\t"%s" "%s"\n' % (k, v))
        out.append('\t"angles" "%g %g %g"\n' % (a[0], a[1], a[2]))
        out.append('\t"origin" "%g %g %g"\n' % (o[0], o[1], o[2]))
        out.append('\teditor\n\t{\n\t\t"color" "220 30 220"\n'
                   '\t\t"visgroupshown" "1"\n\t\t"visgroupautoshown" "1"\n\t}\n')
        out.append("}\n")

    import os
    d = os.path.dirname(dst)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(dst, "w") as f:
        f.write("".join(out))

    print("wrote %s" % dst)
    print("solids %d of %d boxes, recentre %s"
          % (len(plan["boxes"]) - len(degenerate), len(plan["boxes"]), RECENTRE))
    print("faces rewound %d" % flipped)
    if unknown:
        for m, n in sorted(unknown.items(), key=lambda kv: -kv[1]):
            print("UNMAPPED material %r on %d boxes -> %s" % (m, n, MAT_FALLBACK))


if __name__ == "__main__":
    main()
