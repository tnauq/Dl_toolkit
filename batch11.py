#!/usr/bin/env python3
"""batch11.py - eighteenth build step, run after batch10.py.

Thickens ramp-slab_372 (and its m_ twin) downwards so its underside beds
into ramp-slab_367 instead of floating above it.

WHY THICKEN RATHER THAN EXTEND

ramp-slab_372 is pitch 12.0 and ramp-slab_367 is pitch 12.2, so they are
near parallel: the vertical gap between 372's top and 367's top is 136.6
at x -750, 137.1 at -650 and 137.4 at -550. Extending 372 along its own
run closes that at 0.0036 per unit and would need about 38000 units.
Making the slab deeper closes it immediately and leaves the walking
surface exactly where it is.

THE NUMBERS

372's underside currently sits 82.1 to 83.0 above 367's top surface
across the slab's length. Thickness goes 53.30 -> 143.30, an extra 90.00
measured perpendicular to the slab, which is 92.01 vertically, so the
underside ends up 9.0 to 9.9 INSIDE 367 along the whole length. That
bedding is deliberate: a flush underside on two slabs with different
pitches would show a wedge of daylight at one end.

The top surface is unchanged. The centre moves half the added thickness
along the slab's own -z, which is (cos yaw sin pitch, sin yaw sin pitch,
cos pitch), not along world z, so the top face plane and the local run
extent both stay exactly as they were:

  origin [-644.8, 4120.8, 278.1] -> [-654.156, 4120.8, 234.0834]
  extents [223.7, 133.4, 53.3]   -> [223.7, 133.4, 143.3]
  angles  [12.0, 0.0, 0.0]        unchanged

The m_ twin gets the same z and the mirrored x, per the plan transform.

Idempotent and name-keyed: the pre-edit origin/extents are recorded under
_batch11_pre and a rerun skips.

Usage: python3 batch11.py docs/plans/dust2_full.json
"""

import json
import math
import sys

TARGET = "ramp-slab_372"
ADD = 90.0


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_full.json"
    with open(path) as f:
        plan = json.load(f)

    by_name = {b["name"]: b for b in plan["boxes"]}

    for name in (TARGET, "m_" + TARGET):
        box = by_name.get(name)
        if box is None:
            print("MISSING %s" % name)
            continue
        if "_batch11_pre" in box:
            print("%s already done, skipping" % name)
            continue

        ox, oy, oz = box["origin"]
        ex, ey, ez = box["extents"]
        pitch, yaw, roll = box.get("angles", [0.0, 0.0, 0.0])

        p = math.radians(pitch)
        y = math.radians(yaw)
        # slab local +z in world
        nz = (math.cos(y) * math.sin(p), math.sin(y) * math.sin(p), math.cos(p))

        box["_batch11_pre"] = {"origin": [ox, oy, oz], "extents": [ex, ey, ez]}
        box["origin"] = [round(ox - ADD / 2 * nz[0], 4),
                         round(oy - ADD / 2 * nz[1], 4),
                         round(oz - ADD / 2 * nz[2], 4)]
        box["extents"] = [ex, ey, round(ez + ADD, 4)]

        print("%-16s thickness %.2f -> %.2f, origin %s -> %s"
              % (name, ez, ez + ADD, [ox, oy, oz], box["origin"]))

    with open(path, "w") as f:
        json.dump(plan, f, indent=1)

    print("boxes %d" % len(plan["boxes"]))


if __name__ == "__main__":
    main()
