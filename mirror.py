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

ENTITIES AND PATHS ARE PRESERVED, not clobbered (changed 2026-08-22).  This
script only owns the BOXES.  It used to rewrite dust2_full.json wholesale from
the half, which silently deleted anything a later batch script had added to
the full plan -- an ordering trap with nothing to catch it: run mirror after
batch13 and the lanes just vanish.  Now the existing full plan's entities and
paths are carried over, so the two scripts can run in either order.

Carry-over is by NAME where a name exists, and by classname plus origin where
one does not (the two original spawns have no name).  A half-plan entity always
wins over a same-key one in the full plan, because the half is the source.

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


def key_of(x):
    """Identity for carry-over. Named things go by name; the unnamed spawns
    go by classname and origin, which is stable because this script never
    moves an entity."""
    if x.get("name"):
        return ("name", x["name"])
    return ("at", x.get("classname", ""),
            tuple(round(float(v), 4) for v in x.get("origin", [0, 0, 0])))


def carry_over(existing, from_half, label):
    """Everything in the half, plus anything the full plan has on top."""
    out = list(from_half)
    have = {key_of(x) for x in out}
    kept = 0
    for x in existing:
        k = key_of(x)
        if k in have:
            continue
        out.append(x)
        have.add(k)
        kept += 1
    if kept:
        print("carried over %d %s from the existing full plan" % (kept, label))
    return out


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

    # Read the plan we are about to overwrite, and keep the parts of it that
    # are not ours. Boxes ARE ours and are replaced outright.
    prev = {}
    try:
        with open(dst) as f:
            prev = json.load(f)
    except FileNotFoundError:
        pass
    except ValueError as ex:
        print("WARNING: %s did not parse (%s); nothing carried over" % (dst, ex))

    plan["entities"] = carry_over(prev.get("entities", []),
                                  plan.get("entities", []), "entities")
    plan["paths"] = carry_over(prev.get("paths", []),
                               plan.get("paths", []), "paths")
    with open(dst, "w") as f:
        json.dump(plan, f, indent=1)
        f.write("\n")
    print("wrote %s: %d source + %d mirrored = %d boxes"
          % (dst, len(src), len(out) - len(src), len(out)))
    print("  entities %d, paths %d, %d path nodes"
          % (len(plan["entities"]), len(plan["paths"]),
             sum(len(p.get("nodes", [])) for p in plan["paths"])))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_half.json")
