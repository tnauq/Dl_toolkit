#!/usr/bin/env python3
"""Undo the roofs.py lift applied to the tree canopy near T spawn.

The trunk (angled-wall_488..506) is a stack of 53x53x40 blocks based at
213.4, the main floor. roofs.py read it as a wall, doubled it, and carried
the canopy resting on it up by one datum. One slab took the lift twice.

Runs LAST in the pipeline, after remove.py. Idempotent: each box is only
moved if it is still sitting at its lifted height.
"""

import json
import sys

DATUM = 213.4  # 128 CS units x 1.667

# name -> number of datums to undo
SHIFTS = {name: 1 for name in """
    ramp-slab_499 ramp-slab_501 ramp-slab_507 ramp-slab_510
    ramp-slab_512 ramp-slab_515 ramp-slab_526 ramp-slab_529
    ramp-slab_531 ramp-slab_534 ramp-slab_538 ramp-slab_539
    ramp-slab_540 ramp-slab_541 ramp-slab_542 ramp-slab_543
    ramp-slab_544 shallow_504 shallow_521 shallow_525 shallow_532
""".split()}
SHIFTS["ramp-slab_503"] = 2

# a box is only shifted if its z is within this of the expected lifted height
TOL = 1.0

# expected pre-fix z, recorded so a rerun cannot double-apply
LIFTED_Z = {
    "ramp-slab_499": 880.8, "ramp-slab_501": 890.0, "ramp-slab_503": 1129.6,
    "ramp-slab_507": 890.3, "ramp-slab_510": 890.3, "ramp-slab_512": 892.0,
    "ramp-slab_515": 893.8, "ramp-slab_526": 891.3, "ramp-slab_529": 868.8,
    "ramp-slab_531": 889.0, "ramp-slab_534": 892.0, "ramp-slab_538": 859.2,
    "ramp-slab_539": 843.7, "ramp-slab_540": 888.5, "ramp-slab_541": 855.2,
    "ramp-slab_542": 890.7, "ramp-slab_543": 871.2, "ramp-slab_544": 858.0,
    "shallow_504": 922.0, "shallow_521": 922.3, "shallow_525": 922.7,
    "shallow_532": 921.1,
}


def main(path):
    with open(path) as f:
        plan = json.load(f)

    by_name = {b["name"]: b for b in plan["boxes"]}
    moved, skipped, missing = 0, [], []

    for name, datums in SHIFTS.items():
        box = by_name.get(name)
        if box is None:
            missing.append(name)
            continue
        z = box["origin"][2]
        if abs(z - LIFTED_Z[name]) > TOL:
            skipped.append((name, z))
            continue
        box["origin"][2] = round(z - datums * DATUM, 1)
        moved += 1

    with open(path, "w") as f:
        json.dump(plan, f, indent=1)

    print("treefix: moved %d of %d" % (moved, len(SHIFTS)))
    for name, z in skipped:
        print("  skipped %s, z=%.1f, not at its lifted height" % (name, z))
    for name in missing:
        print("  missing %s" % name)
    if missing:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_half.json"))
