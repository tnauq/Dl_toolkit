#!/usr/bin/env python3
"""Mirror the half-map into a full 180-degree rotationally symmetric plan.

Reads  docs/plans/dust2_half.json
Writes docs/plans/dust2_full.json   (half untouched, tail replay unaffected)

The two flip planes the user specified:

  Y plane  y = 6085.05   (northernmost geometry is 5494.5, plus 15 m,
                          giving a 30 m black gap between the halves)
  X plane  x = 460.1     (centre of the mid lane door near CT spawn:
                          axis_127 east face 280.1, axis_80 west face 640.1)

Mirror in Y then mirror in X is exactly a 180 degree yaw rotation about the
vertical line through (460.1, 6085.05), so it is applied as one PROPER
rotation.  Pitch and roll are therefore untouched and every ramp keeps its
gradient and its descent direction:

    x' = 920.2  - x
    y' = 12170.1 - y
    z' = z
    yaw' = yaw + 180        (pitch, roll unchanged)

Copies are named with a "m_" prefix so nothing collides with the name-keyed
manual tail.  Idempotent: rerunning just rewrites dust2_full.json.

    python3 mirror.py [docs/plans/dust2_half.json]
"""

import json
import sys

X_PLANE = 460.1
Y_PLANE = 6085.05
PREFIX = "m_"


def norm(a):
    while a > 180.0:
        a -= 360.0
    while a <= -180.0:
        a += 360.0
    return round(a, 4)


def mirror_box(b):
    o = b["origin"]
    a = b["angles"]
    c = json.loads(json.dumps(b))
    c["name"] = PREFIX + b["name"]
    c["origin"] = [
        round(2.0 * X_PLANE - o[0], 4),
        round(2.0 * Y_PLANE - o[1], 4),
        o[2],
    ]
    c["angles"] = [a[0], norm(a[1] + 180.0), a[2]]
    return c


def main(path):
    with open(path) as f:
        plan = json.load(f)

    have = {b["name"] for b in plan["boxes"]}
    src = list(plan["boxes"])

    out = list(src)
    for b in src:
        m = mirror_box(b)
        if m["name"] in have:
            print("SKIP %s (already present)" % m["name"])
            continue
        out.append(m)
        have.add(m["name"])

    plan["boxes"] = out
    plan["name"] = "dust2_full"

    dst = path.replace("dust2_half.json", "dust2_full.json")
    with open(dst, "w") as f:
        json.dump(plan, f, indent=1)
        f.write("\n")
    print("wrote %s: %d source + %d mirrored = %d boxes"
          % (dst, len(src), len(out) - len(src), len(out)))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_half.json")
